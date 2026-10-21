"""Is a point on (or just off) the land of the British Isles jurisdictions?

Uses the bundled Natural Earth outline (app/static/data/british_isles.geojson: Ireland, United
Kingdom, Jersey, Guernsey, Isle of Man). Points at sea within `km` of a coast vertex also count, so
naval battles and wrecks close inshore are kept.
"""
import json
import math

from .config import ROOT

_RINGS = None


def _rings():
    global _RINGS
    if _RINGS is None:
        gj = json.loads((ROOT / "app" / "static" / "data" / "british_isles.geojson").read_text())
        _RINGS = []
        for f in gj["features"]:
            g = f["geometry"]
            polys = g["coordinates"] if g["type"] == "MultiPolygon" else [g["coordinates"]]
            for poly in polys:
                _RINGS.append(poly[0])
    return _RINGS


def _inside(lat, lon, ring):
    inside, j = False, len(ring) - 1
    for i in range(len(ring)):
        xi, yi = ring[i]
        xj, yj = ring[j]
        if (yi > lat) != (yj > lat) and lon < (xj - xi) * (lat - yi) / (yj - yi) + xi:
            inside = not inside
        j = i
    return inside


def near_land(lat, lon, km=15):
    if lat is None or lon is None:
        return False
    rings = _rings()
    if any(_inside(lat, lon, r) for r in rings):
        return True
    kx = 111.0 * math.cos(math.radians(lat))
    return any(math.hypot((x - lon) * kx, (y - lat) * 111.0) <= km for r in rings for x, y in r)
