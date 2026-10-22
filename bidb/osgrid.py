"""Ordnance Survey (GB) and Irish grid references -> WGS84 latitude/longitude.

    to_latlon("SP 536 027")        -> (51.72…, -1.22…)   British National Grid (OSGB36, Helmert to WGS84)
    to_latlon("C 799 348", irish=True)                    Irish Grid (TM65)

Accuracy a few metres (a seven-parameter Helmert shift; no OSTN15), ample for grid references given
to 10 or 100 m.
"""
import math
import re

_GB = dict(a=6377563.396, b=6356256.909, F0=0.9996012717, lat0=49, lon0=-2, E0=400000, N0=-100000,
           helmert=(-446.448, 125.157, -542.060, 20.4894, -0.1502, -0.2470, -0.8421))
_IE = dict(a=6377340.189, b=6356034.447, F0=1.000035, lat0=53.5, lon0=-8, E0=200000, N0=250000,
           helmert=(-482.530, 130.596, -564.557, -8.150, 1.042, 0.214, 0.631))
_WGS = (6378137.0, 6356752.314245)


def _letters_gb(ref):
    """'SP' -> (east, north) offset of the 100 km square, in metres."""
    a, b = (ord(c) - ord("A") - (c > "I") for c in ref[:2])
    e = ((a - 2) % 5) * 5 + b % 5
    n = (19 - (a // 5) * 5) - b // 5
    return e * 100000, n * 100000


def _letter_ie(c):
    i = ord(c) - ord("A") - (c > "I")
    return (i % 5) * 100000, (4 - i // 5) * 100000


def parse(ref, irish=False):
    """Grid reference -> (easting, northing) in metres (the centre of the square it names), or None."""
    ref = re.sub(r"\s+", " ", (ref or "").replace("\xa0", " ")).strip().upper()
    ref = re.sub(r"^([A-Z])0(?=\s|\d)", r"\1O", ref)          # "S0 281 554": a zero typed for the letter O
    m = re.fullmatch(r"([A-HJ-Z]{1,2})\s*(\d+)\s*(\d*)", ref)
    if not m:
        return None
    letters, d1, d2 = m.groups()
    digits = d1 + d2
    if len(digits) % 2 or not digits or len(letters) != (1 if irish else 2):
        return None
    half = len(digits) // 2
    unit = 10 ** (5 - half)
    e0, n0 = _letter_ie(letters) if irish else _letters_gb(letters)
    return e0 + int(digits[:half]) * unit + unit / 2, n0 + int(digits[half:]) * unit + unit / 2


def _tm_inverse(E, N, p):
    a, b, F0 = p["a"], p["b"], p["F0"]
    lat0, lon0 = math.radians(p["lat0"]), math.radians(p["lon0"])
    e2 = 1 - b * b / (a * a)
    n = (a - b) / (a + b)
    lat, M = lat0, 0.0
    while True:
        lat = (N - p["N0"] - M) / (a * F0) + lat
        M = b * F0 * ((1 + n + 5 / 4 * n ** 2 + 5 / 4 * n ** 3) * (lat - lat0)
                      - (3 * n + 3 * n ** 2 + 21 / 8 * n ** 3) * math.sin(lat - lat0) * math.cos(lat + lat0)
                      + (15 / 8 * n ** 2 + 15 / 8 * n ** 3) * math.sin(2 * (lat - lat0)) * math.cos(2 * (lat + lat0))
                      - 35 / 24 * n ** 3 * math.sin(3 * (lat - lat0)) * math.cos(3 * (lat + lat0)))
        if abs(N - p["N0"] - M) < 0.00001:
            break
    s, c, t = math.sin(lat), math.cos(lat), math.tan(lat)
    nu = a * F0 / math.sqrt(1 - e2 * s * s)
    rho = a * F0 * (1 - e2) / (1 - e2 * s * s) ** 1.5
    eta2 = nu / rho - 1
    dE = E - p["E0"]
    VII = t / (2 * rho * nu)
    VIII = t / (24 * rho * nu ** 3) * (5 + 3 * t * t + eta2 - 9 * t * t * eta2)
    IX = t / (720 * rho * nu ** 5) * (61 + 90 * t * t + 45 * t ** 4)
    X = 1 / (c * nu)
    XI = 1 / (c * 6 * nu ** 3) * (nu / rho + 2 * t * t)
    XII = 1 / (c * 120 * nu ** 5) * (5 + 28 * t * t + 24 * t ** 4)
    XIIA = 1 / (c * 5040 * nu ** 7) * (61 + 662 * t * t + 1320 * t ** 4 + 720 * t ** 6)
    return (lat - VII * dE ** 2 + VIII * dE ** 4 - IX * dE ** 6,
            lon0 + X * dE - XI * dE ** 3 + XII * dE ** 5 - XIIA * dE ** 7)


def _helmert(lat, lon, p):
    """Local datum lat/lon (radians) -> WGS84 degrees."""
    a, b = p["a"], p["b"]
    e2 = 1 - b * b / (a * a)
    nu = a / math.sqrt(1 - e2 * math.sin(lat) ** 2)
    x, y, z = (nu * math.cos(lat) * math.cos(lon), nu * math.cos(lat) * math.sin(lon), (1 - e2) * nu * math.sin(lat))
    tx, ty, tz, s, rx, ry, rz = p["helmert"]
    s = s * 1e-6
    rx, ry, rz = (math.radians(r / 3600) for r in (rx, ry, rz))
    x2 = tx + (1 + s) * x - rz * y + ry * z
    y2 = ty + rz * x + (1 + s) * y - rx * z
    z2 = tz - ry * x + rx * y + (1 + s) * z
    a2, b2 = _WGS
    e22 = 1 - b2 * b2 / (a2 * a2)
    pp = math.hypot(x2, y2)
    lat2 = math.atan2(z2, pp * (1 - e22))
    for _ in range(10):
        nu2 = a2 / math.sqrt(1 - e22 * math.sin(lat2) ** 2)
        lat2 = math.atan2(z2 + e22 * nu2 * math.sin(lat2), pp)
    return math.degrees(lat2), math.degrees(math.atan2(y2, x2))


def to_latlon(ref, irish=False):
    """Grid reference -> (lat, lon) WGS84, or None when it cannot be read."""
    en = parse(ref, irish)
    if not en:
        return None
    p = _IE if irish else _GB
    return _helmert(*_tm_inverse(*en, p), p)
