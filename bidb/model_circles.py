"""3D views of any stone circle from its stones mapped on OpenStreetMap (roadmap SH3h), for the local GUI.

`python -m bidb.model_circles` counts, for every catalogue record and place typed as a stone circle (table type_map),
the stones mapped within `RADIUS` m (one query for every historic=standing_stone/menhir/stone or megalith_type=menhir
in the isles, and natural=stone) and writes those with at least `MIN_STONES` to `data/circle_models.json`; the model itself also takes
natural=stone. `build(entity)` makes the model's data
(bidb.models3d's format, parts from app/static/model_parts.js) on request, cached in `<cache>/circle_models/`:
each stone at its mapped position, its outline if mapped as an area, its height if tagged (else `DEFAULT_H`), the
ground from the terrain tiles and the skyline round the circle's centre, so the sun and moon rise where they would.
"""
import json
import math
import struct
import sys

from . import model_geometry as G
from . import models3d, sky_horizon
from .config import DATA_DIR, cache_dir

OUT = DATA_DIR / "circle_models.json"
RADIUS, MIN_STONES, DEFAULT_H = 45, 5, 1.5
FILTERS = ["[historic=standing_stone]", "[historic=menhir]", "[historic=stone]", "[natural=stone]", "[megalith_type=menhir]"]


def circles(conn):
    """Typed stone circles: (entity id, source, name, lat, lon)."""
    rows = []
    for eid, src in conn.execute("select entity_id, source from type_map where type_id = 'stone-circle'"):
        table = "buildings" if src == "building" else "places"
        r = conn.execute(f"select name, lat, lon from {table} where id = ?", (eid,)).fetchone()
        if r and r[1] is not None:
            rows.append((eid, src, r[0], r[1], r[2]))
    return rows


def stones(lat, lon):
    """Mapped stones round a point: [{id, c: (x, y) m from it, outline or None, height or None}]."""
    out = []
    for e in G.osm(lat, lon, RADIUS, FILTERS):
        if not e["points"]:
            continue
        pts = [G.local(a, b, lat, lon) for a, b in e["points"]]
        area = len(pts) > 3 and pts[0] == pts[-1]
        try:
            h = float(str(e["tags"].get("height", "")).replace("m", "").strip())
        except ValueError:
            h = None
        out.append({"id": e["id"], "c": G.centroid(pts[:-1] if area else pts), "outline": pts[:-1] if area else None,
                    "height": h if h and 0.2 < h < 8 else None})
    return out


def all_stones():
    """Every stone mapped in the isles (historic or megalith tags, or natural=stone), as (lat, lon): one query."""
    tags = '[historic~"^(standing_stone|menhir|stone)$"]'
    box = "(49.8,-11.0,61.0,2.2)"
    q = (f"[out:json][timeout:900];(nwr{tags}{box};nwr[megalith_type=menhir]{box};nwr[natural=stone]{box};);"
         "out center;")
    res = G.request_json(G.OVERPASS, data={"data": q}, method="POST", min_interval=2)
    return [(e["lat"], e["lon"]) if "lat" in e else (e["center"]["lat"], e["center"]["lon"])
            for e in res["elements"] if "lat" in e or "center" in e]


def survey(log=print):
    """Which typed stone circles have enough mapped stones (counted from one query of every mapped stone) →
    data/circle_models.json."""
    from .db import connect
    conn = connect(readonly=True)
    cells = {}
    pts = all_stones()
    for la, lo in pts:
        cells.setdefault((round(la * 200), round(lo * 100)), []).append((la, lo))
    found = {}
    for eid, src, name, lat, lon in circles(conn):
        near = 0
        for i in (-1, 0, 1):
            for j in (-1, 0, 1):
                for la, lo in cells.get((round(lat * 200) + i, round(lon * 100) + j), []):
                    near += math.dist(G.local(la, lo, lat, lon), (0, 0)) <= RADIUS
        if near >= MIN_STONES:
            found[eid] = {"name": name, "source": src, "stones": near, "lat": lat, "lon": lon}
    OUT.write_text(json.dumps(found, ensure_ascii=False, indent=0) + "\n")
    log(f"{len(pts)} stones mapped in the isles; {len(found)} stone circles with {MIN_STONES} or more within "
        f"{RADIUS} m → {OUT.name}")
    return found


def known():
    return json.loads(OUT.read_text()) if OUT.exists() else {}


def build(eid):
    """The model's data and ground grid (bytes) for a surveyed circle, cached; None if it is not one."""
    info = known().get(eid)
    if not info:
        return None
    folder = cache_dir() / "circle_models"
    safe = "".join(ch if ch.isalnum() else "_" for ch in eid)
    jpath, bpath = folder / f"{safe}.json", folder / f"{safe}.bin"
    if jpath.exists() and bpath.exists():
        return json.loads(jpath.read_text()), bpath.read_bytes()
    st = stones(info["lat"], info["lon"])
    cx, cy = G.centroid([s["c"] for s in st])
    lat = info["lat"] + cy / 110574
    lon = info["lon"] + cx / (111320 * math.cos(math.radians(info["lat"])))
    parts = []
    for s in st:
        x, y = s["c"][0] - cx, s["c"][1] - cy
        h = s["height"] or DEFAULT_H
        note = (f"Mapped on OpenStreetMap ({s['id']})" + (f", {h} m high (tagged)." if s["height"] else
                f"; no height mapped, drawn {DEFAULT_H} m."))
        if s["outline"]:
            parts.append({"kind": "stone", "outline": [[p[0] - cx, p[1] - cy] for p in s["outline"]], "h": h,
                          "rock": "sandstone", "title": "Stone", "note": note})
        else:
            parts.append({"kind": "stone", "c": [round(x, 2), round(y, 2)], "len": 0.9, "wid": 0.4,
                          "az": (G.bearing((0, 0), (x, y)) + 90) % 360, "h": h, "rock": "sandstone",
                          "title": "Stone", "note": note})
    span = max(math.hypot(s["c"][0] - cx, s["c"][1] - cy) for s in st)
    grid, dtm = models3d.ground(lat, lon, 300, 2, "tiles")
    dtm["file"] = None
    raw = struct.pack("<%dH" % (dtm["n"] ** 2), *[round((v - dtm["min"]) * 100) for row in grid for v in row])
    hz = sky_horizon.compact(sky_horizon.cached_profile(round(lat, 4), round(lon, 4)))
    hz["alt"] = models3d.despike(hz["alt"])
    r = max(8.0, span)
    data = {"id": eid, "name": info["name"], "record": eid, "origin": {"lat": round(lat, 7), "lon": round(lon, 7)},
            "dtm": dtm, "horizon": hz, "stars": models3d.stars(), "views": {"now": parts},
            "shadow": {"half": max(20, r * 1.6), "centre": [0, 0]},
            "cams": {"overview": {"label": "Overview", "from": [r * 1.6, -r * 2.2, r * 0.9 + 4], "to": [0, 0, 1]},
                     "centre_ne": {"label": "In the centre, facing north-east", "from": [0, 0], "to": [30, 30, 2], "fov": 60, "standing": True},
                     "centre_sw": {"label": "In the centre, facing south-west", "from": [0, 0], "to": [-30, -30, 2], "fov": 60, "standing": True},
                     "above": {"label": "From above", "from": [0, -0.01, r * 4 + 20], "to": [0, 0, 0], "fov": 45}},
            "events": ["summer_rise", "winter_set", "winter_rise", "summer_set", "equinox_rise", "summer_moon", "winter_moon"],
            "face": {"summer_rise": "centre_ne", "winter_set": "centre_sw"},
            "start": {"event": "summer_rise", "t": 600, "note": "Midsummer morning this year. Try the sky events and the views from the centre."},
            "facts": [{"text": f"{len(st)} stones mapped on OpenStreetMap within {RADIUS} m (positions; heights only where tagged).", "cites": []},
                      {"text": "A quick view built from the map, not a survey: stones may be missing, mis-placed or not part of the circle.", "cites": []}],
            "credits": ["Stones: © OpenStreetMap contributors (ODbL)", models3d.CREDITS_TILES,
                        "Stars: Yale Bright Star Catalogue (BSC5), via HEASARC", "three.js r160 (MIT)"],
            "about": [f"{info['name']}: a 3D view built from its stones mapped on OpenStreetMap, on the real ground and "
                      "under the sky of any date, with the real skyline."]}
    folder.mkdir(parents=True, exist_ok=True)
    jpath.write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")))
    bpath.write_bytes(raw)
    return data, raw


if __name__ == "__main__":
    survey()
    sys.exit(0)
