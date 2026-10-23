"""Surfaces of the ready-made bike rides (and walks): how much is on paved roads, quiet traffic-free paths and
unpaved tracks, from OpenStreetMap (ODbL) via Overpass. OSRM's routes carry no surface, so the ways along a route
are fetched (`way[highway](around:12, <points>)`), and every ~200 m of the route takes the nearest way's tags.

    python -m bidb.tour_surface [--mode cycle]   add "surface" to each tour's elevation JSON

Result per tour: {"paved": %, "unpaved": %, "traffic_free": %} (traffic-free = cycleways, paths, tracks and
bridleways, whatever their surface); shown with the elevation profile.
"""
import json
import math
import sys
import time

PAVED = {"asphalt", "paved", "concrete", "concrete:plates", "concrete:lanes", "paving_stones", "sett", "chipseal",
         "metal", "wood", "bricks"}
UNPAVED = {"unpaved", "gravel", "fine_gravel", "compacted", "dirt", "earth", "ground", "grass", "mud", "sand",
           "pebblestone", "rock", "woodchips", "grass_paver", "cobblestone", "unhewn_cobblestone"}
OFF_ROAD = {"cycleway", "path", "footway", "bridleway", "track", "pedestrian", "steps"}
STEP_KM = 0.2


def kind(tags):
    """'paved' | 'unpaved' for a way's tags (surface, else what its highway type usually is)."""
    s = (tags.get("surface") or "").split(";")[0]
    if s in PAVED:
        return "paved"
    if s in UNPAVED:
        return "unpaved"
    hw = tags.get("highway")
    if hw == "track":
        return "paved" if tags.get("tracktype") == "grade1" else "unpaved"
    if hw in ("path", "bridleway"):
        return "unpaved"
    return "paved"


def points(line, step_km=STEP_KM):
    """Points every `step_km` along a [(lat, lon)] line."""
    out, carry = [line[0]], 0.0
    for (a, b), (c, d) in zip(line, line[1:]):
        seg = math.hypot((c - a) * 111.2, (d - b) * 111.2 * math.cos(math.radians(a)))
        while seg > 0 and carry + seg >= step_km:
            t = (step_km - carry) / seg
            a, b = a + (c - a) * t, b + (d - b) * t
            seg -= step_km - carry
            carry = 0.0
            out.append((a, b))
        carry += seg
    return out


def _dist2(p, a, b):
    """Squared distance (in km²) from p to segment a-b, all (lat, lon)."""
    k = math.cos(math.radians(p[0]))
    ax, ay, bx, by, px, py = a[1] * k, a[0], b[1] * k, b[0], p[1] * k, p[0]
    dx, dy = bx - ax, by - ay
    t = 0 if dx == dy == 0 else max(0, min(1, ((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy)))
    return ((ax + t * dx - px) ** 2 + (ay + t * dy - py) ** 2) * 111.2 ** 2


def shares(samples, ways):
    """{"paved", "unpaved", "traffic_free"} percentages of the samples, each taking its nearest way."""
    counts = {"paved": 0, "unpaved": 0, "traffic_free": 0}
    n = 0
    for p in samples:
        best = None
        for tags, geom in ways:
            if abs(geom[0][0] - p[0]) > 0.2:
                continue
            d = min(_dist2(p, a, b) for a, b in zip(geom, geom[1:])) if len(geom) > 1 else 9e9
            if best is None or d < best[0]:
                best = (d, tags)
        if best is None or best[0] > 0.05 ** 2:
            continue                                    # no way within 50 m: leave the point out
        n += 1
        counts[kind(best[1])] += 1
        counts["traffic_free"] += best[1].get("highway") in OFF_ROAD
    return {k: round(100 * v / n) for k, v in counts.items()} if n else None


def fetch_ways(samples, name, chunk=40):
    """Ways along the route, asked for in pieces of `chunk` points (long lines come back empty); an empty
    answer is not kept, so a busy server's reply is tried again next time."""
    from app.basemap_sources import CACHE, overpass
    ways = {}
    for i in range(0, len(samples), chunk):
        part = samples[max(0, i - 1):i + chunk]
        coords = ",".join(f"{a:.5f},{b:.5f}" for a, b in part)
        key = f"tour_surface_{name}_{i // chunk}"
        res = overpass(f"[out:json][timeout:180];way[highway](around:12,{coords});out tags geom;", key, pause=2)
        if not res.get("elements"):
            (CACHE / f"osm_{key}.json").unlink(missing_ok=True)
        for e in res.get("elements", []):
            if e.get("geometry"):
                ways[e["id"]] = (e.get("tags", {}), [(g["lat"], g["lon"]) for g in e["geometry"]])
    return list(ways.values())


def run(mode="cycle", log=print):
    from .db import connect
    from .tour_elevation import decode
    t0 = time.time()
    conn = connect()
    conn.execute("PRAGMA busy_timeout = 120000")
    rows = [r for r in conn.execute("SELECT id, geometry, elevation FROM tours WHERE mode = ? AND routed = 1 "
                                    "AND geometry != ''", (mode,)) if '"surface"' not in (r[2] or "")]
    done = 0
    for tid, geom, elev in rows:
        line = decode(geom)
        if len(line) < 2:
            continue
        samples = points(line)
        try:
            ways = fetch_ways(samples, tid)
        except Exception as e:                      # a busy Overpass server: keep the rest
            log(f"  {tid}: {e}")
            continue
        s = shares(samples, ways)
        if s:
            e = json.loads(elev) if elev else {}
            e["surface"] = s
            conn.execute("UPDATE tours SET elevation = ? WHERE id = ?", (json.dumps(e), tid))
            conn.commit()
            done += 1
        log(f"[{time.time() - t0:5.0f}s] {tid}: {s}")
    log(f"surfaces for {done} of {len(rows)} {mode} tours")


if __name__ == "__main__":
    run(sys.argv[2] if sys.argv[1:2] == ["--mode"] else "cycle")
