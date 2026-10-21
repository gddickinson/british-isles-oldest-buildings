"""Routes along real paths and roads for tours: OSRM servers of FOSSGIS at routing.openstreetmap.de
(OpenStreetMap data, ODbL; foot, bike and car profiles). Responses are cached on disk.

Fair use: one request per tour, at most one a second (bidb.http rate limit).
"""
from .http import request_json

PROFILES = {"walk": "foot", "cycle": "bike", "drive": "car"}
SERVER = "https://routing.openstreetmap.de/routed-{}/route/v1/driving/{}"
ATTRIBUTION = "Routes: OSRM on routing.openstreetmap.de (FOSSGIS), © OpenStreetMap contributors"


def route(mode, points):
    """points [(lat, lon), …] (≤ 25) -> {"distance_km", "duration_min", "geometry" (polyline6),
    "legs_km": […]} or None when no route is found."""
    if len(points) < 2:
        return None
    coords = ";".join(f"{lon:.5f},{lat:.5f}" for lat, lon in points)
    try:
        res = request_json(SERVER.format(PROFILES[mode], coords),
                           params={"overview": "full", "geometries": "polyline6"}, min_interval=1.0)
    except Exception:                          # noqa: BLE001 - routing is optional; tours fall back to lines
        return None
    if not res or res.get("code") != "Ok" or not res.get("routes"):
        return None
    r = res["routes"][0]
    return {"distance_km": round(r["distance"] / 1000, 2), "duration_min": round(r["duration"] / 60, 1),
            "geometry": r["geometry"], "legs_km": [round(l["distance"] / 1000, 2) for l in r.get("legs", [])]}
