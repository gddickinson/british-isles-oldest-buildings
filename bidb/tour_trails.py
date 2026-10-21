"""Long-distance and pilgrim walks as multi-day tours (part of bidb.tours).

National trails / Scotland's Great Trails / Irish National Waymarked Ways (the map's trails layer)
and pilgrim ways from OpenStreetMap (route relations named after saints or pilgrims). For each
route of 40 km or more: the path as one line, the best sights within 1.5 km of it in order along
the way, and day stages of about 20 km.
"""
import json
import re

from bidb.config import ROOT

from .tour_plan import km

TRAILS = ROOT / "app" / "static" / "data" / "basemap" / "trails.json"
NEAR_KM, STAGE_KM, MIN_KM, MAX_STOPS = 1.5, 20, 40, 24
PILGRIM = r"Pilgrim|Pererin|Camino|Cuthbert|Columba|Kevin|Patrick|Oswald|Hilda|Bede|Augustine|Winefride|Wenefrede|" \
          r"Thomas Becket|Brendan|Ninian|Andrew|David|Brigid|Declan|Finbarr|Fursey|Swithun|Margaret|Kentigern|Mungo"


def _pilgrim_routes():
    from app.basemap_sources import overpass
    q = (f'[out:json][timeout:300];relation[route~"^(hiking|foot)$"][name~"{PILGRIM}"](49,-11,61.2,2.2);out geom;')
    out = []
    for rel in overpass(q, "pilgrim_routes").get("elements", []):
        lines = [[[g["lon"], g["lat"]] for g in m["geometry"]] for m in rel.get("members", [])
                 if m.get("type") == "way" and m.get("geometry")]
        if lines:
            out.append((rel["tags"].get("name:en") or rel["tags"]["name"], lines))
    return out


def _chain(lines):
    """The longest end-to-end chain of a route's ways, as [[lat, lon], …]."""
    from app.basemap_tiled import _join
    rounded = [[[round(x, 4), round(y, 4)] for x, y in l] for l in lines]
    chains = _join(rounded)
    best = max(chains, key=lambda c: sum(km((a[1], a[0]), (b[1], b[0])) for a, b in zip(c, c[1:])))
    return [[y, x] for x, y in best]


def routes():
    """[(name, kind, line)] kind: "trail" | "pilgrim"."""
    out, seen = [], set()
    for f in json.loads(TRAILS.read_text())["features"]:
        name = f["properties"].get("n") or ""
        if re.search(r"\bspur\b|link\b|loop\b", name, re.I):
            continue
        out.append((name, "pilgrim" if re.search(PILGRIM, name) else "trail", _chain(f["geometry"]["coordinates"])))
        seen.add(name)
    for name, lines in _pilgrim_routes():
        if name not in seen:
            out.append((name, "pilgrim", _chain(lines)))
            seen.add(name)
    return [(n, k, l) for n, k, l in out if len(l) > 1]


def along(line):
    """Cumulative km at each vertex."""
    acc = [0.0]
    for a, b in zip(line, line[1:]):
        acc.append(acc[-1] + km(a, b))
    return acc


def sights(line, cands):
    """Best candidates within NEAR_KM of the line -> [(km along, cand)], spread out, in order."""
    acc = along(line)
    step = max(1, len(line) // 600)
    pts = [(line[i], acc[i]) for i in range(0, len(line), step)]
    lat0 = min(p[0] for p, _ in pts) - 0.05
    lat1 = max(p[0] for p, _ in pts) + 0.05
    lon0 = min(p[1] for p, _ in pts) - 0.08
    lon1 = max(p[1] for p, _ in pts) + 0.08
    hits = []
    for c in cands:
        if not (lat0 <= c["lat"] <= lat1 and lon0 <= c["lon"] <= lon1):
            continue
        d, pos = min((km(p, (c["lat"], c["lon"])), a) for p, a in pts)
        if d <= NEAR_KM:
            hits.append((pos, c))
    # the best sight in each stretch of the route, then fill with the next best
    window = max(acc[-1] / MAX_STOPS, 3)
    best = {}
    for pos, c in hits:
        k = int(pos // window)
        if k not in best or c["score"] > best[k][1]["score"]:
            best[k] = (pos, c)
    return sorted(best.values(), key=lambda x: x[0])


def stages(total_km, stops):
    """Day stages of about STAGE_KM: [{"day", "from_km", "to_km", "stops": [names]}]."""
    days = max(1, round(total_km / STAGE_KM))
    size = total_km / days
    return [{"day": d + 1, "from_km": round(d * size, 1), "to_km": round((d + 1) * size, 1),
             "stops": [c["name"] for pos, c in stops if d * size <= pos < (d + 1) * size or (d == days - 1 and pos >= total_km)]}
            for d in range(days)]
