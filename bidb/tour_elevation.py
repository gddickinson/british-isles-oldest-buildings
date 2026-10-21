"""Elevation profiles for tour routes: 100 points along the route from OpenTopoData (EU-DEM 25 m,
public API: ≤ 100 points per request, 1 request a second, 1,000 a day; responses cached).

    profile(line)  [[lat, lon], …] -> {"climb_m", "descent_m", "min_m", "max_m", "profile": [m, …], "hilly"}
"""
import math

from .http import request_json
from .tour_plan import km

API = "https://api.opentopodata.org/v1/eudem25m"
POINTS = 100


def decode(poly, precision=6):
    """Google/OSRM polyline -> [[lat, lon]]."""
    out, i, lat, lon, f = [], 0, 0, 0, 10 ** precision
    while i < len(poly):
        for k in (0, 1):
            shift = result = 0
            while True:
                b = ord(poly[i]) - 63
                i += 1
                result |= (b & 0x1F) << shift
                shift += 5
                if b < 0x20:
                    break
            d = ~(result >> 1) if result & 1 else result >> 1
            if k == 0:
                lat += d
            else:
                lon += d
        out.append([lat / f, lon / f])
    return out


def encode(line, precision=6):
    """[[lat, lon]] -> Google/OSRM polyline."""
    out, prev, f = [], (0, 0), 10 ** precision
    for lat, lon in line:
        cur = (round(lat * f), round(lon * f))
        for d in (cur[0] - prev[0], cur[1] - prev[1]):
            v = ~(d << 1) if d < 0 else d << 1
            while v >= 0x20:
                out.append(chr((0x20 | (v & 0x1F)) + 63))
                v >>= 5
            out.append(chr(v + 63))
        prev = cur
    return "".join(out)


def sample(line, n=POINTS):
    """n points evenly spaced along a line (by distance)."""
    if len(line) < 2:
        return line
    seg = [km(a, b) for a, b in zip(line, line[1:])]
    total = sum(seg) or 1
    out, acc, j = [], 0.0, 0
    for i in range(n):
        target = total * i / (n - 1)
        while j < len(seg) - 1 and acc + seg[j] < target:
            acc += seg[j]
            j += 1
        t = 0 if seg[j] == 0 else min(1, (target - acc) / seg[j])
        a, b = line[j], line[j + 1]
        out.append([a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t])
    return out


def hilliness(climb_m, dist_km):
    """Words for metres climbed per km (under 20 m in all is flat, however short the route)."""
    if climb_m < 20:
        return "flat"
    rate = climb_m / max(dist_km, 0.1)
    return "flat" if rate < 5 else "gently rolling" if rate < 10 else "hilly" if rate < 20 else "very hilly"


def climb_descent(heights, step=3.0):
    """Metres up and down, counting a change only once it reaches `step` m (terrain-model noise on
    closely spaced samples would otherwise add up to a false climb on short, flat routes)."""
    up = down = 0.0
    ref = heights[0] if heights else 0
    for h in heights[1:]:
        if h - ref >= step:
            up, ref = up + h - ref, h
        elif ref - h >= step:
            down, ref = down + ref - h, h
    return up, down


def profile(line, dist_km):
    """Heights every ~500 m (100–600 points, 100 per request); the profile drawn has 100 points."""
    n = int(min(600, max(POINTS, dist_km * 2)))
    n -= n % POINTS
    pts, elev = sample(line, n), []
    try:
        for i in range(0, len(pts), POINTS):
            res = request_json(API, params={"locations": "|".join(f"{a:.5f},{b:.5f}" for a, b in pts[i:i + POINTS])},
                               min_interval=1.1)
            elev += [r.get("elevation") for r in (res or {}).get("results", [])]
    except Exception:                          # noqa: BLE001 - elevation is optional
        return None
    if not elev or any(e is None or (isinstance(e, float) and math.isnan(e)) for e in elev):
        elev = [e if e is not None else 0 for e in elev]
        if not any(elev):
            return None
    smooth = [sum(elev[max(0, i - 1):i + 2]) / len(elev[max(0, i - 1):i + 2]) for i in range(len(elev))]
    climb, descent = climb_descent(smooth)
    return {"climb_m": round(climb), "descent_m": round(descent), "min_m": round(min(elev)), "max_m": round(max(elev)),
            "profile": [round(elev[round(i * (len(elev) - 1) / (POINTS - 1))]) for i in range(POINTS)],
            "hilly": hilliness(climb, dist_km)}
