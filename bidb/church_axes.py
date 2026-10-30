"""Church axes from the walls and from mapped parts (roadmap SK5b2b), read by bidb.church_orientation.

The axis of bidb.church_orientation is the long side of the smallest rectangle round the whole outline, so a west
tower set askew, a porch or an aisle added on one side can turn it. Two other readings of the same church:

- `wall_axis`: the walls' own direction: every edge of the outline weighted by its length, folded onto 0-90° (the
  long walls and the end walls of a rectangular building agree), the busiest direction found in a window of
  `WINDOW` degrees and refined by the weighted mean of the edges inside it; of that direction and the one at right
  angles, the one along which the outline is longer is the axis. The long nave and chancel walls carry most of the
  length, so a tower or porch moves it little.
- `body_axis`: OpenStreetMap `building:part` ways tagged nave, chancel or church (the body without tower and porch)
  whose centre lies inside a church's outline (Overpass, cached; `parts_of`): few churches have them, so they check
  the two readings above rather than replace them (`compare`).

`python -m bidb.church_axes` prints how far the three readings differ.
"""
import json
import math
import sqlite3
import sys

from .config import CACHE_DIR, db_path

WINDOW = 6.0           # degrees: width of the window that finds the walls' busiest direction
BODY = ("nave", "chancel", "church")   # "church": the body without its tower or porch
PART_CACHE = CACHE_DIR / "church_parts.json"


def _rings(geom):
    polys = [geom["coordinates"]] if geom["type"] == "Polygon" else geom["coordinates"]
    return [poly[0] for poly in polys if poly and len(poly[0]) >= 4]


def _metres(rings):
    pts = [p for r in rings for p in r]
    lat0 = sum(p[1] for p in pts) / len(pts)
    k = math.cos(math.radians(lat0))
    return [[((lon * k) * 111320, lat * 111320) for lon, lat, *_ in r] for r in rings]


def _edges(rings_xy):
    """(direction in degrees from north folded onto 0-90, length in metres) of every edge."""
    out = []
    for r in rings_xy:
        for (x1, y1), (x2, y2) in zip(r, r[1:]):
            dx, dy = x2 - x1, y2 - y1
            n = math.hypot(dx, dy)
            if n > 0.05:
                out.append((math.degrees(math.atan2(dx, dy)) % 90, n))
    return out


def _fold(d, centre):
    """d moved by multiples of 90° to within 45° of centre."""
    return centre + (d - centre + 45) % 90 - 45


def dominant(edges):
    """The busiest edge direction (0-90°) and the share of the outline's length within WINDOW / 2 of it."""
    total = sum(n for _, n in edges)
    if not total:
        return None
    best = max((sum(n for d, n in edges if abs(_fold(d, c / 2) - c / 2) <= WINDOW / 2), c / 2) for c in range(180))
    c = best[1]
    near = [(_fold(d, c), n) for d, n in edges if abs(_fold(d, c) - c) <= WINDOW / 2]
    mean = sum(d * n for d, n in near) / sum(n for _, n in near)
    return mean % 90, best[0] / total


def _extent(rings_xy, az):
    a = math.radians(az)
    us = [x * math.sin(a) + y * math.cos(a) for r in rings_xy for x, y in r]
    return max(us) - min(us)


def wall_axis(geom):
    """(azimuth of the axis in 0-180°, length / width, share of the walls' length on the two directions), or None."""
    rings = _rings(geom)
    if not rings:
        return None
    xy = _metres(rings)
    dom = dominant(_edges(xy))
    if not dom:
        return None
    d, share = dom
    along, across = _extent(xy, d), _extent(xy, d + 90)
    if min(along, across) < 1:
        return None
    az, el = (d, along / across) if along >= across else (d + 90, across / along)
    return round(az % 180, 2), round(el, 2), round(share, 3)


def diff(a, b):
    """Smallest angle between two axes (each 0-180°)."""
    return abs((a - b + 90) % 180 - 90)


# Mapped parts ----------------------------------------------------------------------------------------------

def fetch_parts(log=print):
    """Ways tagged building:part nave, chancel or church in the isles (Overpass, cached): [{part, geom}]."""
    if PART_CACHE.exists():
        return json.loads(PART_CACHE.read_text())
    from .footprints import _overpass
    q = ('[out:json][timeout:300];way["building:part"~"^(%s)$"](49,-11,61.2,2.2);out tags geom;' % "|".join(BODY))
    out = []
    for el in _overpass(q, "church_body_parts").get("elements", []):
        pts = [[g["lon"], g["lat"]] for g in el.get("geometry", [])]
        if len(pts) >= 4 and pts[0] == pts[-1]:
            out.append({"part": el["tags"]["building:part"], "geom": {"type": "Polygon", "coordinates": [pts]}})
    PART_CACHE.parent.mkdir(parents=True, exist_ok=True)
    PART_CACHE.write_text(json.dumps(out))
    log(f"{len(out)} building:part ways tagged {', '.join(BODY)}")
    return out


def _inside(pt, geom):
    x, y = pt
    hit = False
    for ring in _rings(geom):
        for (x1, y1), (x2, y2) in zip(ring, ring[1:]):
            if (y1 > y) != (y2 > y) and x < x1 + (y - y1) * (x2 - x1) / (y2 - y1):
                hit = not hit
    return hit


def parts_of(outlines, parts):
    """{record id: [parts whose centre lies inside its outline]}."""
    boxes = {}
    for rid, g in outlines.items():
        pts = [p for r in _rings(g) for p in r]
        if pts:
            boxes[rid] = (min(p[0] for p in pts), min(p[1] for p in pts), max(p[0] for p in pts), max(p[1] for p in pts))
    out = {}
    for part in parts:
        ring = part["geom"]["coordinates"][0][:-1]
        c = (sum(p[0] for p in ring) / len(ring), sum(p[1] for p in ring) / len(ring))
        for rid, (x0, y0, x1, y1) in boxes.items():
            if x0 <= c[0] <= x1 and y0 <= c[1] <= y1 and _inside(c, outlines[rid]):
                out.setdefault(rid, []).append(part)
                break
    return out


def body_axis(parts):
    """Axis (wall_axis) of the largest part tagged nave, else chancel, else church; None when none is mapped or the
    part is too near square (length / width under MIN_ELONGATION) to have an axis."""
    from .church_orientation import MIN_ELONGATION
    for kind in BODY:
        geoms = [p["geom"] for p in parts if p["part"] == kind]
        if geoms:
            ax = wall_axis(max(geoms, key=lambda g: _area(_metres(_rings(g))[0])))
            return ax if ax and ax[1] >= MIN_ELONGATION else None
    return None


def _area(ring):
    return abs(sum(x1 * y2 - x2 * y1 for (x1, y1), (x2, y2) in zip(ring, ring[1:]))) / 2


def compare(log=print):
    """Rectangle axis and wall axis against each other, and against the nave or chancel where it is mapped."""
    from .church_orientation import axis, MIN_ELONGATION
    con = sqlite3.connect(db_path())
    outlines = {rid: json.loads(fp) for rid, fp in con.execute(
        "SELECT id, footprint FROM buildings WHERE category_group = 'Religious' AND footprint <> ''")}
    parts = parts_of(outlines, fetch_parts(log))
    rect_wall, body = [], []
    for rid, g in outlines.items():
        a, w = axis(g), wall_axis(g)
        if not a or not w or a[1] < MIN_ELONGATION or not 30 <= a[0] <= 150:
            continue
        rect_wall.append(diff(a[0], w[0]))
        b = body_axis(parts.get(rid, []))
        if b:
            body.append((rid, diff(a[0], b[0]), diff(w[0], b[0])))
    q = lambda xs, f: sorted(xs)[int(len(xs) * f)] if xs else None
    log(f"rectangle vs walls, {len(rect_wall)} east-facing churches: median {q(rect_wall, .5):.1f}°, "
        f"90% within {q(rect_wall, .9):.1f}°, {sum(d > 5 for d in rect_wall)} differ by more than 5°")
    if body:
        for i, what in ((1, "rectangle"), (2, "walls")):
            ds = [b[i] for b in body]
            log(f"{what} vs mapped nave/chancel, {len(ds)} churches: median {q(ds, .5):.1f}°, max {max(ds):.1f}°")
    return {"rect_wall": rect_wall, "body": body}


if __name__ == "__main__":
    compare()
