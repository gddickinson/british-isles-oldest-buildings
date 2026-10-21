"""Build stage / CLI: ready-made tours -> table `tours`.

    python -m bidb.tours            generate, route (cached) and write the tours
    python -m bidb.tours --report   list them

Walks around historic towns, cycle rides and driving day trips, for all sights ("highlights")
and for themes (ghosts & legends, prehistoric, castles, early churches, Roman). Centres are
chosen greedily where the interesting records of a theme cluster; stops are the best records
within the mode's radius, ordered by nearest neighbour + 2-opt and routed along real paths
and roads (bidb.tour_route). Without a route the tour keeps straight lines and an estimate.
"""
import argparse
import json
import time

from . import stories_db, tour_plan, tour_route, tour_trails
from .config import ROOT, require_locations
from .db import connect

THEMES = {
    "highlights": {"title": "Highlights", "test": lambda r: True},
    "ghosts": {"title": "Ghosts & legends",
               "test": lambda r: bool({"supernatural", "legend", "folklore"} & set(r["story_kinds"]))
               or r.get("kind_label") in ("Reportedly haunted place", "Place of legend")},
    "maritime": {"title": "Maritime heritage", "test": lambda r: r.get("kind_group") == "Maritime heritage"
                 or any(w in (r.get("category") or "") for w in ("Lighthouse", "Harbour", "Dock"))},
    "industrial": {"title": "Industrial Revolution", "test": lambda r: r.get("kind_group") == "Industrial heritage"
                   or r.get("category_group") == "Industry & transport"},
    "victorian": {"title": "Victorian", "test": lambda r: r.get("kind_group") == "Victorian era"
                  or r.get("period") == "Victorian"},
    "coastal": {"title": "Coastal defences", "test": lambda r: r.get("kind_label") in COASTAL},
    "military": {"title": "Military heritage", "test": lambda r: r.get("kind_group") == "Military heritage"
                 or (r.get("category_group") == "Fortification" and (r.get("year_start") or 0) >= 1500)},
    "museums": {"title": "Museums & galleries", "test": lambda r: r.get("kind_group") == "Museums & collections"
                and r.get("kind_label") != "Library or archive" and "(closed)" not in (r.get("type") or "")},
    "bridges": {"title": "Bridges", "test": lambda r: r.get("kind_group") == "Bridges"
                or ("Bridge" in (r.get("category") or "")           # the category also holds wells and dams
                    and any(w in (r.get("name") or "").lower() for w in ("bridge", "viaduct", "aqueduct", "pont", "brig")))},
    "underground": {"title": "Underground", "test": lambda r: r.get("kind_group") == "Underground"},
    "literary": {"title": "Literary places", "test": lambda r: r.get("kind_label") == "Literary place" or r.get("writer")},
    "prehistoric": {"title": "Prehistoric", "test": lambda r: r.get("period") in ("Neolithic", "Bronze Age", "Iron Age")
                    or r.get("category_group") == "Prehistoric" or r.get("kind_group") == "Archaeological sites"},
    "castles": {"title": "Castles", "test": lambda r: r.get("category_group") == "Fortification"},
    "churches": {"title": "Early churches", "test": lambda r: r.get("category_group") == "Religious"
                 and r.get("year_start") is not None and r["year_start"] < 1300},
    # "Roman Britain" is only a period label in Ireland (by date): Roman sites are in Britain
    "trail": {"title": "Long-distance & pilgrim ways", "test": lambda r: True},
    "roman": {"title": "Roman", "test": lambda r: r.get("category_group") == "Roman" or (
        r.get("period") == "Roman Britain" and r.get("nation") in ("England", "Wales", "Scotland"))},
}
COASTAL = ("Martello or defensive tower", "Fort or fortification", "Gun or anti-aircraft battery",
           "Pillbox or anti-tank defence", "Radar station, sound mirror or signal station")
# how many tours per (theme, mode)
PLAN = {("highlights", "walk"): 45, ("highlights", "cycle"): 25, ("highlights", "drive"): 25,
        ("ghosts", "walk"): 10, ("ghosts", "cycle"): 6, ("ghosts", "drive"): 10,
        ("prehistoric", "cycle"): 6, ("prehistoric", "drive"): 10, ("castles", "cycle"): 5,
        ("castles", "drive"): 10, ("literary", "drive"): 6, ("maritime", "drive"): 8, ("maritime", "walk"): 6,
        ("industrial", "drive"): 8, ("industrial", "cycle"): 5, ("victorian", "walk"): 8, ("victorian", "drive"): 4, ("churches", "cycle"): 6, ("churches", "drive"): 4, ("roman", "drive"): 4,
        ("roman", "walk"): 3, ("underground", "walk"): 6, ("underground", "drive"): 4,
        ("coastal", "cycle"): 5, ("coastal", "drive"): 6, ("military", "drive"): 6, ("military", "walk"): 3,
        ("museums", "walk"): 10, ("museums", "drive"): 4,
        ("bridges", "walk"): 6, ("bridges", "cycle"): 5, ("bridges", "drive"): 6}
# keep tours of the same theme and mode this far apart (km)
APART = {"walk": 6, "cycle": 22, "drive": 60}
COLUMNS = ["id", "mode", "theme", "title", "area", "nation", "summary", "distance_km", "duration_min",
           "routed", "geometry", "stops", "elevation", "stages"]


def candidates(conn):
    """Buildings and visitable places with coordinates, scored by interest."""
    kinds = stories_db.kinds_by_record(conn)
    cols = ["id", "name", "lat", "lon", "date_text", "year_start", "period", "category", "category_group",
            "landmark", "oldest_of_type", "curated", "image_thumb", "wikipedia_title", "heritage_grade",
            "status", "nation", "county", "locality"]
    out = []
    for row in conn.execute(f"SELECT {', '.join(cols)} FROM buildings WHERE lat IS NOT NULL"):
        out.append(dict(zip(cols, row)) | {"kind": "building"})
    pcols = ["id", "name", "lat", "lon", "date_text", "year_start", "period", "kind_label", "kind_group", "type",
             "image_thumb", "wikipedia_title", "nation", "locality"]
    for row in conn.execute(f"""SELECT {', '.join(pcols)} FROM places WHERE lat IS NOT NULL
            AND (coalesce(wikipedia_title, '') != ''
                 OR kind_group IN ('Legends & literature', 'Maritime heritage', 'Victorian era', 'Industrial heritage', 'Underground', 'Museums & collections')
                 OR (kind_group = 'Military heritage' AND kind != 'memorial')) AND building_id IS NULL
            AND kind_group NOT IN ('Finds & treasures', 'Plaques & people', 'History events')"""):
        r = dict(zip(pcols, row))
        out.append(r | {"kind": "place", "category": r["kind_label"]})
    writers = {t for (t,) in conn.execute(
        """SELECT DISTINCT l.target_id FROM person_links l JOIN persons p ON p.id = l.person_id
           WHERE l.role IN ('Buried here', 'Died here', 'Born here', 'Lived here', 'Occupant', 'Owner', 'Worked here',
                            'Commemorated here')
           AND (p.description LIKE '%writer%' OR p.description LIKE '%poet%' OR p.description LIKE '%novelist%'
                OR p.description LIKE '%playwright%' OR p.description LIKE '%dramatist%')""")}
    for r in out:
        r["writer"] = r["id"] in writers               # home, grave or plaque of a writer
        r["story_kinds"] = kinds.get(r["id"], [])
        r["stories"] = len(r["story_kinds"])
        r["score"] = tour_plan.interest(r)
    return out


def _grid(cands, cell):
    g = {}
    for c in cands:
        g.setdefault((int(c["lat"] / cell), int(c["lon"] / cell)), []).append(c)
    return g


def _density(c, grid, cell, radius):
    i, j = int(c["lat"] / cell), int(c["lon"] / cell)
    n = int(radius / (cell * 111)) + 1
    return sum(o["score"] for di in range(-n, n + 1) for dj in range(-n * 2, n * 2 + 1)
               for o in grid.get((i + di, j + dj), []) if tour_plan.km((c["lat"], c["lon"]), (o["lat"], o["lon"])) <= radius)


def _towns():
    rows = json.loads((ROOT / "app" / "static" / "data" / "basemap" / "towns.json").read_text())
    return [r for r in rows if r[3] <= 1]


def area_name(stops, mode, towns):
    lat = sum(s["lat"] for s in stops) / len(stops)
    lon = sum(s["lon"] for s in stops) / len(stops)
    if mode == "drive":
        counties = [s.get("county") for s in stops if s.get("county")]
        if counties:
            return max(set(counties), key=counties.count)
    # the biggest town close to the middle of the tour (a city, not one of its suburbs)
    reach = {"walk": 2.5, "cycle": 8, "drive": 20}[mode]
    close = [t for t in towns if tour_plan.km((lat, lon), (t[1], t[2])) < reach]
    if close:
        return max(close, key=lambda t: (t[3] == 0, t[4] or 0))[0]
    near = min(towns, key=lambda t: tour_plan.km((lat, lon), (t[1], t[2])))
    if tour_plan.km((lat, lon), (near[1], near[2])) < 15:
        return near[0]
    locs = [(s.get("locality") or "").split(",")[0].strip() for s in stops if s.get("locality")]
    return max(set(locs), key=locs.count) if locs else near[0]


def title_for(theme, mode, area):
    noun = {"walk": "walk", "cycle": "bike ride", "drive": "drive"}[mode]
    return {"highlights": {"walk": f"Historic {area} on foot", "cycle": f"Around {area} by bike",
                           "drive": f"{area}: a day by car"}[mode],
            "ghosts": f"Ghosts & legends of {area} ({noun})",
            "literary": f"Literary {area} ({noun})",
            "maritime": f"Maritime {area} ({noun})",
            "industrial": f"Industrial {area} ({noun})",
            "victorian": f"Victorian {area} ({noun})",
            "underground": f"Underground {area} ({noun})",
            "coastal": f"Coastal defences of {area} ({noun})",
            "military": f"Military {area} ({noun})",
            "museums": f"Museums & galleries of {area} ({noun})",
            "bridges": f"Bridges of {area} ({noun})",
            "prehistoric": f"Prehistoric {area} ({noun})",
            "castles": f"Castles of {area} ({noun})",
            "churches": f"Early churches around {area} ({noun})",
            "roman": f"Roman {area} ({noun})"}[theme]


def _label(stop):
    return f"{stop['name']} ({stop['date_text']})" if stop.get("date_text") else stop["name"]


def summary(stops, mode, dist_km, minutes):
    best = sorted(stops, key=lambda s: -s["score"])[:3]
    tales = sum(1 for s in stops if s["stories"])
    hrs = f"{minutes / 60:.1f} h" if minutes >= 90 else f"{minutes:.0f} min"
    text = (f"{len(stops)} stops, {dist_km:.1f} km, about {hrs} with time at each stop. "
            f"Highlights: {', '.join(_label(b) for b in best)}.")
    return text + (f" {tales} stops come with a legend or story." if tales else "")


def _elevation(geom, pts, dist):
    from .tour_elevation import decode, profile
    line = decode(geom) if geom else [list(p) for p in pts]
    return profile(line, dist)


def make_tour(theme, mode, stops, towns, n):
    m = tour_plan.MODES[mode]
    path = tour_plan.order(stops, loop=m["loop"])
    pts = [(s["lat"], s["lon"]) for s in path] + ([(path[0]["lat"], path[0]["lon"])] if m["loop"] else [])
    routed = tour_route.route(mode, pts)
    if routed:
        dist, travel, geom = routed["distance_km"], routed["duration_min"], routed["geometry"]
        if mode == "walk":                       # OSRM foot speed is brisk; use a sightseeing pace
            travel = dist / m["kmh"] * 60
        ferry = travel > 3 * dist / m["kmh"] * 60     # waiting for ferries counted as travel time
        if ferry:
            travel = dist / m["kmh"] * 60
    else:
        dist = sum(tour_plan.km(a, b) for a, b in zip(pts, pts[1:])) * m["detour"]
        travel, geom = dist / m["kmh"] * 60, ""
        ferry = False
    minutes = travel + m["stop_min"] * len(path)
    area = area_name(path, mode, towns)
    nations = [s.get("nation") for s in path if s.get("nation")]
    keep = ["id", "kind", "name", "lat", "lon", "date_text", "category", "locality", "story_kinds"]
    return {"id": f"{mode}-{theme}-{n}", "mode": mode, "theme": theme, "title": title_for(theme, mode, area),
            "area": area, "nation": max(set(nations), key=nations.count) if nations else "",
            "summary": summary(path, mode, dist, minutes) + (" Includes ferry crossings: check the timetables."
                                                              if ferry else ""), "distance_km": round(dist, 1),
            "duration_min": round(minutes), "routed": 1 if routed else 0, "geometry": geom,
            "stops": json.dumps([{k: s.get(k) for k in keep} for s in path], ensure_ascii=False),
            "elevation": json.dumps(_elevation(geom, pts, dist)) if mode != "drive" else "", "stages": ""}


def generate(conn, log=print):
    cands = candidates(conn)
    towns = _towns()
    log(f"{len(cands)} candidate stops")
    tours = []
    for (theme, mode), want in PLAN.items():
        m = tour_plan.MODES[mode]
        pool = [c for c in cands if THEMES[theme]["test"](c)]
        cell = max(m["radius_km"] / 111, 0.01)
        grid = _grid(pool, cell)
        ranked = sorted(pool, key=lambda c: -c["score"])[:3000]
        dens = sorted(((_density(c, grid, cell, m["radius_km"]), c) for c in ranked), key=lambda x: -x[0])
        centres, made = [], 0
        for _, c in dens:
            if made >= want:
                break
            centre = (c["lat"], c["lon"])
            if any(tour_plan.km(centre, o) < APART[mode] for o in centres):
                continue
            stops = tour_plan.pick_stops(pool, centre, mode)
            if not stops:
                continue
            centres.append(centre)
            made += 1
            tours.append(make_tour(theme, mode, stops, towns, made))
        log(f"  {theme} / {mode}: {made} tours")
    trails = [trail_tour(name, kind, line, cands, n) for n, (name, kind, line) in enumerate(tour_trails.routes(), 1)]
    trails = [x for x in trails if x]
    log(f"  long-distance and pilgrim ways: {len(trails)} tours")
    return tours + trails


def trail_tour(name, kind, line, cands, n):
    """A national trail or pilgrim way as a multi-day walk with sights along it."""
    from .tour_elevation import encode, profile
    acc = tour_trails.along(line)
    total = acc[-1]
    if total < tour_trails.MIN_KM:
        return None
    stops = tour_trails.sights(line, cands)
    if len(stops) < 3:
        return None
    path = [c for _, c in stops]
    days = tour_trails.stages(total, stops)
    step = max(1, len(line) // 1500)                  # keep the drawn line light
    simple = line[::step] + ([line[-1]] if (len(line) - 1) % step else [])
    counties = [c.get("county") for c in path if c.get("county")]
    nations = [c.get("nation") for c in path if c.get("nation")]
    keep = ["id", "kind", "name", "lat", "lon", "date_text", "category", "locality", "story_kinds"]
    elev = profile(line, total)
    return {"id": f"walk-trail-{n}", "mode": "walk", "theme": "trail", "title": name,
            "area": max(set(counties), key=counties.count) if counties else "",
            "nation": max(set(nations), key=nations.count) if nations else "",
            "summary": (f"{'A pilgrim way' if kind == 'pilgrim' else 'A long-distance trail'} of {total:.0f} km, about "
                        f"{len(days)} day{'s' if len(days) > 1 else ''} on foot, past {len(path)} sights: "
                        + ", ".join(_label(c) for c in sorted(path, key=lambda c: -c["score"])[:3]) + "."),
            "distance_km": round(total, 1), "duration_min": round(len(days) * 7 * 60), "routed": 1,
            "geometry": encode(simple), "stops": json.dumps([{k: c.get(k) for k in keep} for c in path], ensure_ascii=False),
            "elevation": json.dumps(elev) if elev else "", "stages": json.dumps(days, ensure_ascii=False)}


def write(conn, tours):
    conn.executescript(f"""DROP TABLE IF EXISTS tours;
        CREATE TABLE tours ({", ".join(c + (" REAL" if c in ("distance_km", "duration_min") else " TEXT")
                                       for c in COLUMNS)});""")
    conn.executemany(f"INSERT INTO tours VALUES ({', '.join('?' for _ in COLUMNS)})",
                     [[t[c] for c in COLUMNS] for t in tours])
    conn.commit()


def run(log=print):
    require_locations()
    t0 = time.time()
    conn = connect()
    conn.execute("PRAGMA busy_timeout = 120000")
    tours = generate(conn, lambda m: log(f"[{time.time() - t0:6.0f}s] {m}"))
    write(conn, tours)
    log(f"wrote {len(tours)} tours ({sum(t['routed'] for t in tours)} routed)")


def report(log=print):
    conn = connect()
    for row in conn.execute("SELECT mode, theme, title, distance_km, duration_min, routed FROM tours ORDER BY mode, theme"):
        log(" | ".join(str(x) for x in row))


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--report", action="store_true")
    a = ap.parse_args()
    report() if a.report else run()


if __name__ == "__main__":
    main()
