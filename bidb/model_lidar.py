"""3D views of English buildings from the Environment Agency's LiDAR (roadmap SH4d), for the local GUI.

For a catalogue record in England with a mapped footprint, `build(id)` takes the 1 m first-return surface model
(roofs, towers, walls, trees as the laser saw them) and the 1 m terrain model over a square round the footprint
(open web services, OGL), and classes each metre: the record's own building (inside its footprint and raised), other
buildings (OpenStreetMap), trees and other raised things, ground. The page draws the surface coloured by class under
the sun, moon and stars of any date with the real skyline (model_view.js, stonehenge_scene.js: `dtm.classes`). Cached
in `<cache>/lidar_models/`. It is a shell seen from the air: no interiors, and walls are blurred to the 1 m cells.
"""
import base64
import json
import math
import sqlite3
import struct

from . import model_geometry as G
from . import models3d, osgrid, sky_horizon
from .config import cache_dir, db_path
from .stonehenge_sources import _download, read_tiff

DTM = ("https://environment.data.gov.uk/spatialdata/lidar-composite-digital-terrain-model-dtm-1m/wcs",
       "13787b9a-26a4-4775-8523-806d13af58fc__Lidar_Composite_Elevation_DTM_1m")
DSM = ("https://environment.data.gov.uk/spatialdata/lidar-composite-digital-surface-model-first-return-dsm-1m/wcs",
       "df4e3ec3-315e-48aa-aaaf-b5ae74d7b2bb__Lidar_Composite_Elevation_FZ_DSM_1m")
GROUND, OWN, OTHER, RAISED = 0, 1, 2, 3
CREDIT = "Surface and ground: Environment Agency LiDAR Composite DSM (first return) and DTM 1 m (Open Government Licence)"


def wcs(service, e, n, size):
    """A size × size square of 1 m heights centred on (e, n), rows north to south; None where there is no data."""
    url, cov = service
    e0, n0, half = round(e), round(n), size // 2
    params = {"service": "WCS", "version": "2.0.1", "request": "GetCoverage", "CoverageId": cov, "format": "image/tiff",
              "subset": [f"E({e0 - half},{e0 + half})", f"N({n0 - half},{n0 + half})"]}
    rows = read_tiff(_download(url, f"{cov[:8]}_{e0}_{n0}_{size}.tif", params))
    return [[v if -100 < v < 2000 else None for v in row] for row in rows]


def polygons(geo, lat0, lon0):
    """Local outlines (metres) of a GeoJSON Polygon or MultiPolygon (outer rings)."""
    polys = geo["coordinates"] if geo["type"] == "MultiPolygon" else [geo["coordinates"]]
    return [[G.local(la, lo, lat0, lon0) for lo, la in poly[0]] for poly in polys]


def inside(pt, poly):
    x, y, hit = pt[0], pt[1], False
    for i in range(len(poly)):
        (x1, y1), (x2, y2) = poly[i - 1], poly[i]
        if (y1 > y) != (y2 > y) and x < x1 + (y - y1) * (x2 - x1) / (y2 - y1):
            hit = not hit
    return hit


def eligible(conn, eid):
    r = conn.execute("select name, lat, lon, footprint, nation from buildings where id = ?", (eid,)).fetchone()
    return r if r and r[4] == "England" and r[3] else None


def build(eid):
    """The model's data and surface grid (bytes) for an English record with a footprint, cached; None if not one."""
    conn = sqlite3.connect(db_path())
    row = eligible(conn, eid)
    if not row:
        return None
    folder = cache_dir() / "lidar_models"
    safe = "".join(ch if ch.isalnum() else "_" for ch in eid)
    jpath, bpath = folder / f"{safe}.json", folder / f"{safe}.bin"
    if jpath.exists() and bpath.exists():
        return json.loads(jpath.read_text()), bpath.read_bytes()
    name, lat0, lon0, fp, _ = row
    own = polygons(json.loads(fp), lat0, lon0)
    pts = [p for poly in own for p in poly]
    cx, cy = G.centroid(pts)
    lat = lat0 + cy / 110574
    lon = lon0 + cx / (111320 * math.cos(math.radians(lat0)))
    own = [[(x - cx, y - cy) for x, y in poly] for poly in own]
    extent = max(math.hypot(x, y) for poly in own for x, y in poly)
    size = int(min(400, max(160, 2 * extent + 120)) // 2 * 2)
    e, n = osgrid.to_en(lat, lon)
    dsm, dtm = wcs(DSM, e, n, size), wcs(DTM, e, n, size)
    k = min(len(dsm), len(dtm))
    others = []
    for el in G.osm(lat, lon, size * 0.75, ["[building]"]):
        if len(el["points"]) > 3:
            poly = [G.local(a, b, lat, lon) for a, b in el["points"]]
            if not any(inside(G.centroid(poly), o) for o in own):
                others.append((poly, min(p[0] for p in poly), max(p[0] for p in poly), min(p[1] for p in poly), max(p[1] for p in poly)))
    half = (k - 1) / 2
    heights, classes = [], bytearray()
    for i in range(k):
        for j in range(k):
            x, y = j - half, half - i
            g = dtm[i][j] if dtm[i][j] is not None else (dsm[i][j] if dsm[i][j] is not None else 0.0)
            s = dsm[i][j] if dsm[i][j] is not None else g
            fade = min(1.0, max(0.0, (half - 4 - math.hypot(x, y)) / 16))     # bare ground at the disc's edge,
            s = g + (s - g) * fade                                              # where the far land joins it
            up = s - g
            c = GROUND
            if up > 1.0 and any(inside((x, y), o) for o in own):
                c = OWN
            elif up > 1.5 and any(a <= x <= b and lo <= y <= hi and inside((x, y), p) for p, a, b, lo, hi in others):
                c = OTHER
            elif up > 1.5:
                c = RAISED
            heights.append(s)
            classes.append(c)
    low = min(heights)
    mid = heights[(k // 2) * k + k // 2]
    ground_c = dtm[k // 2][k // 2] if dtm[k // 2][k // 2] is not None else mid
    meta = {"n": k, "step": 1, "x0": -half, "y0": half, "min": round(low, 2), "scale": 0.01, "ground": round(ground_c, 2),
            "source": "ea-dsm", "classes": base64.b64encode(bytes(classes)).decode()}
    raw = struct.pack("<%dH" % (k * k), *[round((h - low) * 100) for h in heights])
    hz = sky_horizon.compact(sky_horizon.cached_profile(round(lat, 4), round(lon, 4)))
    hz["alt"] = models3d.despike(hz["alt"])
    tall = max((h for h, c in zip(heights, classes) if c == OWN), default=ground_c) - ground_c
    r = max(25.0, extent)
    data = {"id": eid, "name": name, "record": eid, "origin": {"lat": round(lat, 7), "lon": round(lon, 7)},
            "dtm": meta, "horizon": hz, "stars": models3d.stars(), "views": {"now": []},
            "shadow": {"half": size / 2, "centre": [0, 0]},
            "cams": {"overview": {"label": "From the south-west", "from": [-r * 1.5, -r * 1.9, r * 0.9 + tall], "to": [0, 0, tall / 3]},
                     "south": {"label": "Standing to the south", "from": [0, -r - 15], "to": [0, 0, tall / 2], "fov": 60, "standing": True},
                     "north": {"label": "Standing to the north", "from": [0, r + 15], "to": [0, 0, tall / 2], "fov": 60, "standing": True},
                     "above": {"label": "From above", "from": [0, -0.01, r * 3.5 + tall], "to": [0, 0, 0], "fov": 45}},
            "events": ["summer_rise", "summer_set", "winter_rise", "winter_set", "equinox_rise", "summer_moon", "winter_moon"],
            "start": {"m": 6, "d": 21, "t": 600, "note": "Midsummer morning. The surface is what the laser saw from the air: walls blur over a metre, and there are no interiors."},
            "facts": [{"text": f"The surface the Environment Agency's aircraft laser saw, every metre over {size} m square; "
                               f"the building's highest point about {tall:.0f} m above the ground at its centre.", "cites": []},
                      {"text": "Coloured by kind: the building itself (inside its mapped footprint), other mapped buildings, "
                               "trees and other raised things, and the ground.", "cites": []}],
            "credits": [CREDIT, "Footprints and buildings: © OpenStreetMap contributors (ODbL)", models3d.CREDITS_TILES.replace("Ground and skyline", "Skyline"),
                        "Stars: Yale Bright Star Catalogue (BSC5), via HEASARC", "three.js r160 (MIT)"]}
    folder.mkdir(parents=True, exist_ok=True)
    jpath.write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")))
    bpath.write_bytes(raw)
    return data, raw
