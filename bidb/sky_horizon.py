"""Real horizons (roadmap SK7): the skyline round a place from the terrain tiles, and where the sun and moon
rise and set over it (mirrored in app/static/sky.js: `horizonAzimuth`).

    profile(lat, lon)          {"step": 0.5, "ground": m, "alt": [degrees per step from north], "km": [distance]}
    cached_profile(lat, lon)   the same, kept in `<cache>/horizons/` (downloads tiles the first time)
    altitude_at(alt, step, az) horizon altitude at an azimuth (linear between steps)
    horizon_azimuth(...)       first gleam over the skyline (rise) or last gleam (set); None if never

Bare ground only: the terrain model has no trees or buildings. Light bends over the ground (terrestrial
refraction, k = 0.13) and the earth curves away, so far hills sit lower than their height alone suggests.
"""
import json
import math

from .config import cache_dir
from .sky import event_azimuth
from .terrain_tiles import Terrain

STEP = 0.5             # degrees of azimuth
EYE = 1.6              # metres above the ground
EARTH = 6371000.0
K = 0.13               # terrestrial refraction coefficient
MAX_KM = 60
FIRST = 20.0           # first sample, metres
GROW = 1.02            # each sample this much further than the last
LOWEST = -2.0          # a horizon below this (sea from a high cliff) is taken as this
ZOOMS = ((1500, 13), (8000, 11), (MAX_KM * 1000, 9))   # finer tiles near the observer


def _zoom(d):
    return next(z for limit, z in ZOOMS if d <= limit)


def _distances():
    d, out = FIRST, []
    while d <= MAX_KM * 1000:
        out.append(d)
        d *= GROW
    return out


def profile(lat, lon, terrain=None, step=STEP):
    """Horizon altitude (degrees, apparent before refraction of the body's light) and its distance, every step."""
    t = terrain or Terrain()
    ground = t.height(lat, lon, 13)
    eye = ground + EYE
    dists = _distances()
    m_lat = 111320.0
    m_lon = 111320.0 * math.cos(math.radians(lat))
    alt, km = [], []
    for i in range(round(360 / step)):
        a = math.radians(i * step)
        sa, ca = math.sin(a), math.cos(a)
        best, at = -90.0, 0.0
        for d in dists:
            h = t.height(lat + d * ca / m_lat, lon + d * sa / m_lon, _zoom(d))
            e = math.degrees(math.atan2(h - eye - d * d * (1 - K) / (2 * EARTH), d))
            if e > best:
                best, at = e, d
        alt.append(round(max(best, LOWEST), 2))
        km.append(round(at / 1000, 2))
    return {"step": step, "ground": round(ground, 1), "alt": alt, "km": km}


def cached_profile(lat, lon, terrain=None):
    path = cache_dir() / "horizons" / f"{lat:.5f}_{lon:.5f}.json"
    if path.exists():
        return json.loads(path.read_text())
    p = profile(lat, lon, terrain)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(p, separators=(",", ":")))
    return p


def altitude_at(alt, step, az):
    x = (az % 360) / step
    i = int(math.floor(x)) % len(alt)
    f = x - math.floor(x)
    return alt[i] * (1 - f) + alt[(i + 1) % len(alt)] * f


def _above(lat, body, event, rise_set, year, alt, step, az):
    """Whether the body, on its path through the sky that day, stands above the skyline at azimuth az."""
    a = event_azimuth(lat, body, event, rise_set, year, altitude_at(alt, step, az))
    if a is None:
        return False
    return a <= az if rise_set == "rise" else a >= az


def horizon_azimuth(lat, body, event, rise_set, year, alt, step=STEP, fine=0.05, span=60):
    """Azimuth of the first gleam (rise) or last gleam (set) over the skyline: walking from where the body
    would cross a horizon at LOWEST, towards the south (a higher horizon always moves it south), the first
    azimuth at which its path is above the skyline."""
    start = event_azimuth(lat, body, event, rise_set, year, LOWEST)
    if start is None:
        return None
    sign = 1 if rise_set == "rise" else -1
    prev = start
    for k in range(1, round(span / fine) + 1):
        az = start + sign * k * fine
        if _above(lat, body, event, rise_set, year, alt, step, az):
            lo, hi = prev, az                       # refine between the last step below and this one
            for _ in range(12):
                mid = (lo + hi) / 2
                lo, hi = (lo, mid) if _above(lat, body, event, rise_set, year, alt, step, mid) else (mid, hi)
            return hi % 360
        prev = az
    return None


def compact(p):
    """The profile for sky.json: altitudes in hundredths of a degree, distances in whole km."""
    return {"step": p["step"], "ground": p["ground"], "alt": [round(a * 100) for a in p["alt"]],
            "km": [round(k) for k in p["km"]]}
