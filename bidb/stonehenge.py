"""The 3D model of Stonehenge (page /stonehenge): writes `app/static/data/stonehenge.json` and the ground grid
`app/static/data/stonehenge_dtm.bin` (`python -m bidb.stonehenge`).

Inputs: the stones as they survive digitised from Anthony Johnson's numbered plan
(`data/curated/stonehenge/plan_stones.json`, made by prepare_plan.py there), placed on the ground by fitting it to
the OpenStreetMap stones (bidb.stonehenge_layout.register); the researched record of every stone, the dimensions and
the layout with quoted sources (`data/curated/stonehenge/stones.json`); the Environment Agency's 1 m LiDAR terrain
(800 m square, written at 2 m); the skyline round the centre (bidb.sky_horizon); the bright stars (BSC5, V ≤ 5.5).
"""
import json
import math
import os
import struct

from . import models3d, osgrid, sky_horizon
from . import stonehenge_layout as L
from . import stonehenge_sources as S
from .config import ROOT

HERE = os.path.join(ROOT, "data", "curated", "stonehenge")
OUT = os.path.join(ROOT, "app", "static", "data")
SIZE, STEP = 800, 2              # metres of LiDAR round the centre, metres between written heights
OUTLIERS = ("91", "92", "93", "94", "95", "96", "97")


def _round(pts):
    return [[round(x, 2), round(y, 2)] for x, y in pts]


def placed(lat0=S.CENTRE[0], lon0=S.CENTRE[1]):
    """Plan stones and OSM outliers in the model frame, the model's origin on the ground and the fit."""
    plan = json.load(open(os.path.join(HERE, "plan_stones.json")))["stones"]
    osm = S.osm_stones()
    big = [s for s in plan if s["area_m2"] > 0.4]
    fit = L.register(big, osm, lat0, lon0, turn=False)    # the plan has north up; OSM's outlines (traced from
    fit["free_theta"] = L.register(big, osm, lat0, lon0)["theta"]   # aerial photos) cannot settle a rotation
    th, (tx, ty) = fit["theta"], fit["shift"]
    stones = {s["id"]: _round([L.rotate(p, th) for p in s["outline"]]) for s in plan}
    outliers = {}
    for o in osm:
        if o["ref"] in OUTLIERS:
            pts = [L.local(a, b, lat0, lon0) for a, b in o["outline"]]
            outliers[o["ref"]] = _round([(x - tx, y - ty) for x, y in pts])
    lat = lat0 + ty / 110574
    lon = lon0 + tx / (111320 * math.cos(math.radians(lat0)))
    return stones, outliers, (lat, lon), fit


def terrain(lat, lon):
    """LiDAR heights round the origin every STEP m (means of STEP × STEP cells): (grid, metadata)."""
    e, n = osgrid.to_en(lat, lon)
    rows = S.lidar(e, n, SIZE)
    e0, n0 = round(e) - SIZE // 2, round(n) + SIZE // 2           # north-west corner of the coverage
    k = SIZE // STEP
    grid = [[sum(rows[i * STEP + a][j * STEP + b] for a in range(STEP) for b in range(STEP)) / STEP ** 2
             for j in range(k)] for i in range(k)]
    low = min(min(r) for r in grid)
    ci = int((n0 - n) / STEP)
    cj = int((e - e0) / STEP)
    meta = {"file": "stonehenge_dtm.bin", "n": k, "step": STEP, "x0": round(e0 + STEP / 2 - e, 2),
            "y0": round(n0 - STEP / 2 - n, 2), "min": round(low, 2), "scale": 0.01,
            "ground": round(grid[ci][cj], 2), "e": round(e, 1), "n_": round(n, 1),
            "about": "rows north to south, columns west to east; height = min + value × scale (metres OD)"}
    return grid, meta


def write():
    stones, outliers, (lat, lon), fit = placed()
    research = json.load(open(os.path.join(HERE, "stones.json")))
    record = {s["id"]: s for s in research["stones"]}
    now = L.now(stones, record, outliers)
    built, ring = L.built(stones, record, outliers, research["dimensions"])
    grid, dtm = terrain(lat, lon)
    with open(os.path.join(OUT, dtm["file"]), "wb") as f:
        f.write(struct.pack("<%dH" % (dtm["n"] ** 2), *[round((h - dtm["min"]) * 100) for r in grid for h in r]))
    hz = sky_horizon.compact(sky_horizon.cached_profile(round(lat, 4), round(lon, 4)))
    stars = models3d.stars()
    sources = research["sources"]
    info = {sid: {"group": r["group"], "state": r["state_now"], "notes": r.get("notes", ""),
                  "cites": [{"title": sources[c["source"]]["title"], "url": sources[c["source"]]["url"],
                             "quote": c["quote"]} for c in r.get("cites", []) if c.get("source") in sources]}
            for sid, r in record.items()}
    data = {
        "origin": {"lat": round(lat, 7), "lon": round(lon, 7), "fit": {"rotation_deg": round(math.degrees(fit["theta"]), 2),
                   "free_rotation_deg": round(math.degrees(fit["free_theta"]), 2),
                   "pairs": fit["pairs"], "rms_m": round(fit["rms"], 2)}},
        "axis": L.AXIS, "ring": ring, "now": now, "built": built, "stones": info, "dtm": dtm, "horizon": hz,
        "stars": stars, "debate": research.get("missing_debate", []),
        "credits": [
            "Stone plan: Anthony Johnson, Plan of the central Stone Structure at Stonehenge (2007), Wikimedia Commons "
            "File:Stone_Plan.jpg (CC BY 3.0); coloured by Nightdevil (2018), File:Stone_Plan_Coloured.jpg (CC BY-SA 4.0)",
            S.ATTRIBUTION["osm"], S.ATTRIBUTION["lidar"], S.ATTRIBUTION["stars"],
            "Skyline: " + "Terrain Tiles (Mapzen / AWS Open Data; Environment Agency LiDAR, SRTM, EU-DEM)",
            "three.js r160 (MIT)"],
    }
    with open(os.path.join(OUT, "stonehenge.json"), "w") as f:
        json.dump(data, f, separators=(",", ":"))
    return data


def report(data):
    o = data["origin"]
    print(f"origin {o['lat']}, {o['lon']}; plan fitted to {o['fit']['pairs']} OSM stones (shift only; a free fit "
          f"would rotate it {o['fit']['free_rotation_deg']}°), rms {o['fit']['rms_m']} m; ring centre {data['ring']['centre']} r {data['ring']['radius']} m,"
          f" {data['ring']['step']}° per upright")
    by = {}
    for s in data["built"]:
        by[s["status"]] = by.get(s["status"], 0) + 1
    print(f"now {len(data['now'])} stones; built {len(data['built'])} ({by}); {len(data['stars'])} stars; "
          f"ground {data['dtm']['n']}² at {data['dtm']['step']} m, centre {data['dtm']['ground']} m OD")


if __name__ == "__main__":
    report(write())
