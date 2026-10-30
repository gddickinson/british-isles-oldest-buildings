"""Geometry shared by the builders of the 3D models (bidb.model_<id>, roadmap SH3): OpenStreetMap features round a
site (Overpass, cached), points along an azimuth, an outline's radius in each direction, slabs laid along an
outline (kerbs), regular polygons and the facts list of a model page from its research file."""
import math

from .http import request_json

OVERPASS = "https://overpass-api.de/api/interpreter"
R = math.pi / 180


def osm(lat, lon, radius, filters):
    """OSM elements within `radius` m matching any of `filters` (Overpass filter strings such as
    '[historic=stone]'), each {id, tags, points: [(lat, lon)]} (cached by bidb.http)."""
    body = "".join(f"nwr(around:{radius},{lat},{lon}){f};" for f in filters)
    res = request_json(OVERPASS, data={"data": f"[out:json][timeout:60];({body});out tags geom;"}, method="POST",
                       min_interval=2)
    out = []
    for e in res["elements"]:
        geom = e.get("geometry") or ([{"lat": e["lat"], "lon": e["lon"]}] if "lat" in e else [])
        if e["type"] == "relation":
            geom = [p for m in e.get("members", []) if m.get("role") == "outer" for p in m.get("geometry", [])]
        out.append({"id": f"{e['type']}/{e['id']}", "tags": e.get("tags", {}), "points": [(p["lat"], p["lon"]) for p in geom]})
    return out


def local(lat, lon, lat0, lon0):
    """Metres east and north of (lat0, lon0)."""
    return ((lon - lon0) * 111320 * math.cos(math.radians(lat0)), (lat - lat0) * 110574)


def centroid(pts):
    return (sum(p[0] for p in pts) / len(pts), sum(p[1] for p in pts) / len(pts))


def toward(c, az, d):
    """The point d metres from c towards azimuth az."""
    return (c[0] + d * math.sin(az * R), c[1] + d * math.cos(az * R))


def bearing(a, b):
    return math.degrees(math.atan2(b[0] - a[0], b[1] - a[1])) % 360


def radius_at(outline, c, az):
    """Distance from c to the outline along azimuth az (the farthest crossing)."""
    d = (math.sin(az * R), math.cos(az * R))
    best = 0.0
    n = len(outline)
    for i in range(n):
        p, q = outline[i], outline[(i + 1) % n]
        ex, ey = q[0] - p[0], q[1] - p[1]
        den = d[0] * ey - d[1] * ex
        if abs(den) < 1e-12:
            continue
        wx, wy = p[0] - c[0], p[1] - c[1]
        t = (wx * ey - wy * ex) / den                  # along the ray
        u = (wx * d[1] - wy * d[0]) / den              # along the edge
        if t > 0 and 0 <= u <= 1:
            best = max(best, t)
    return best


def radii(outline, c, step=2):
    """The outline's radius from c every `step` degrees from north."""
    return [round(radius_at(outline, c, a), 2) for a in range(0, 360, step)]


def along(outline, count, inset=0.0):
    """`count` points spaced evenly round a closed outline (and the azimuth of the outline there), moved `inset` m
    towards its centroid: [(x, y, az)]."""
    n, c = len(outline), centroid(outline)
    seg = [math.dist(outline[i], outline[(i + 1) % n]) for i in range(n)]
    total, out, i, run = sum(seg), [], 0, 0.0
    for k in range(count):
        target = (k + 0.5) * total / count
        while run + seg[i] < target:
            run += seg[i]
            i += 1
        t = (target - run) / seg[i]
        p, q = outline[i], outline[(i + 1) % n]
        x, y = p[0] + (q[0] - p[0]) * t, p[1] + (q[1] - p[1]) * t
        if inset:
            d = math.dist((x, y), c) or 1
            x, y = x + (c[0] - x) / d * inset, y + (c[1] - y) / d * inset
        out.append((round(x, 2), round(y, 2), round(bearing(p, q), 1)))
    return out


def polygon(c, r, n, start=0.0):
    """Regular polygon round c, first corner at azimuth `start`."""
    return [[round(v, 2) for v in toward(c, start + 360 * k / n, r)] for k in range(n)]


def facts(research, keys, cite):
    """Facts listed on a model's page: [(key, text)] → [{text, cites}] from the research file's `facts`."""
    out = []
    for key, text in keys:
        f = research["facts"][key]
        out.append({"text": text, "cites": cite(research, f.get("cites"))})
    return out
