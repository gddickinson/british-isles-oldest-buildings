"""Small pure-Python geometry helpers for the offline map: Douglas–Peucker simplification,
coordinate rounding and label points. Coordinates are GeoJSON [lon, lat] pairs in degrees."""


def _perp(p, a, b):
    (x, y), (x1, y1), (x2, y2) = p, a, b
    dx, dy = x2 - x1, y2 - y1
    if dx == 0 and dy == 0:
        return ((x - x1) ** 2 + (y - y1) ** 2) ** 0.5
    t = max(0.0, min(1.0, ((x - x1) * dx + (y - y1) * dy) / (dx * dx + dy * dy)))
    return ((x - x1 - t * dx) ** 2 + (y - y1 - t * dy) ** 2) ** 0.5


def douglas_peucker(points, tol):
    """Simplify a line (list of [x, y]) keeping points further than `tol` from the chord."""
    if len(points) < 3:
        return list(points)
    keep = [False] * len(points)
    keep[0] = keep[-1] = True
    stack = [(0, len(points) - 1)]
    while stack:
        i, j = stack.pop()
        best, idx = 0.0, None
        for k in range(i + 1, j):
            d = _perp(points[k], points[i], points[j])
            if d > best:
                best, idx = d, k
        if idx is not None and best > tol:
            keep[idx] = True
            stack += [(i, idx), (idx, j)]
    return [p for p, k in zip(points, keep) if k]


def _round(points, nd):
    out = []
    for x, y in points:
        p = [round(x, nd), round(y, nd)]
        if not out or out[-1] != p:
            out.append(p)
    return out


def simplify(geom, tol, nd=4, min_ring=4):
    """Simplified copy of a (Multi)LineString / (Multi)Polygon; None if nothing survives."""
    t = geom["type"]
    line = lambda pts: _round(douglas_peucker(pts, tol), nd)
    if t == "LineString":
        c = line(geom["coordinates"])
        return {"type": t, "coordinates": c} if len(c) > 1 else None
    if t == "MultiLineString":
        cs = [c for c in (line(p) for p in geom["coordinates"]) if len(c) > 1]
        return {"type": t, "coordinates": cs} if cs else None
    if t == "Polygon":
        rings = [r for r in (line(r) for r in geom["coordinates"]) if len(r) >= min_ring]
        return {"type": t, "coordinates": rings} if rings else None
    if t == "MultiPolygon":
        polys = []
        for poly in geom["coordinates"]:
            rings = [r for r in (line(r) for r in poly) if len(r) >= min_ring]
            if rings:
                polys.append(rings)
        return {"type": t, "coordinates": polys} if polys else None
    return geom


def bbox_centre(geom):
    xs, ys, stack = [], [], [geom["coordinates"]]
    while stack:
        c = stack.pop()
        if c and isinstance(c[0], (int, float)):
            xs.append(c[0])
            ys.append(c[1])
        else:
            stack.extend(c)
    return [round((min(xs) + max(xs)) / 2, 4), round((min(ys) + max(ys)) / 2, 4)]


def line_length_km(coords):
    import math
    total = 0.0
    for (x1, y1), (x2, y2) in zip(coords, coords[1:]):
        kx = 111.3 * math.cos(math.radians((y1 + y2) / 2))
        total += math.hypot((x2 - x1) * kx, (y2 - y1) * 111.3)
    return total


def feature(geom, **props):
    return {"type": "Feature", "properties": {k: v for k, v in props.items() if v not in (None, "")},
            "geometry": geom}


def collection(features):
    return {"type": "FeatureCollection", "features": [f for f in features if f["geometry"]]}


def join_rings(ways):
    """Join way segments ([[x, y], ...]) end-to-end into closed rings; leftovers are dropped."""
    pending = [list(w) for w in ways if len(w) > 1]
    rings = []
    while pending:
        ring = pending.pop()
        changed = True
        while ring[0] != ring[-1] and changed:
            changed = False
            for i, w in enumerate(pending):
                if w[0] == ring[-1]:
                    ring += w[1:]
                elif w[-1] == ring[-1]:
                    ring += w[-2::-1]
                elif w[-1] == ring[0]:
                    ring = w[:-1] + ring
                elif w[0] == ring[0]:
                    ring = w[:0:-1] + ring
                else:
                    continue
                pending.pop(i)
                changed = True
                break
        if ring[0] == ring[-1] and len(ring) >= 4:
            rings.append(ring)
    return rings
