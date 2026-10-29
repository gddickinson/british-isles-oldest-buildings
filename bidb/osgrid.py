"""Ordnance Survey (GB) and Irish grid references <-> WGS84 latitude/longitude (mirrored in static/osgrid.js).

    to_latlon("SP 536 027")        -> (51.72…, -1.22…)   British National Grid (OSGB36, Helmert to WGS84)
    to_latlon("C 799 348", irish=True)                    Irish Grid (TM65)
    from_latlon(51.1789, -1.8262)  -> "SU 12236 42189"   and back (roadmap LD2)
    for_point(54.6, -5.9)          -> ("J 34xx 74xx", "Irish")   the grid in use there; None in the Channel Islands

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


def _arc(lat, p):
    """Meridional arc from the true origin, scaled by F0."""
    a, b, F0 = p["a"], p["b"], p["F0"]
    lat0 = math.radians(p["lat0"])
    n = (a - b) / (a + b)
    return b * F0 * ((1 + n + 5 / 4 * n ** 2 + 5 / 4 * n ** 3) * (lat - lat0)
                     - (3 * n + 3 * n ** 2 + 21 / 8 * n ** 3) * math.sin(lat - lat0) * math.cos(lat + lat0)
                     + (15 / 8 * n ** 2 + 15 / 8 * n ** 3) * math.sin(2 * (lat - lat0)) * math.cos(2 * (lat + lat0))
                     - 35 / 24 * n ** 3 * math.sin(3 * (lat - lat0)) * math.cos(3 * (lat + lat0)))


def _radii(lat, p):
    a, b, F0 = p["a"], p["b"], p["F0"]
    e2 = 1 - b * b / (a * a)
    s = math.sin(lat)
    nu = a * F0 / math.sqrt(1 - e2 * s * s)
    rho = a * F0 * (1 - e2) / (1 - e2 * s * s) ** 1.5
    return nu, rho, nu / rho - 1


def _tm_inverse(E, N, p):
    a, F0 = p["a"], p["F0"]
    lat0, lon0 = math.radians(p["lat0"]), math.radians(p["lon0"])
    lat, M = lat0, 0.0
    while True:
        lat = (N - p["N0"] - M) / (a * F0) + lat
        M = _arc(lat, p)
        if abs(N - p["N0"] - M) < 0.00001:
            break
    c, t = math.cos(lat), math.tan(lat)
    nu, rho, eta2 = _radii(lat, p)
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


def _tm_forward(lat, lon, p):
    """Local datum lat/lon (radians) -> (easting, northing) in metres."""
    s, c, t = math.sin(lat), math.cos(lat), math.tan(lat)
    nu, rho, eta2 = _radii(lat, p)
    dl = lon - math.radians(p["lon0"])
    I = _arc(lat, p) + p["N0"]
    II = nu / 2 * s * c
    III = nu / 24 * s * c ** 3 * (5 - t * t + 9 * eta2)
    IIIA = nu / 720 * s * c ** 5 * (61 - 58 * t * t + t ** 4)
    IV = nu * c
    V = nu / 6 * c ** 3 * (nu / rho - t * t)
    VI = nu / 120 * c ** 5 * (5 - 18 * t * t + t ** 4 + 14 * eta2 - 58 * t * t * eta2)
    return (p["E0"] + IV * dl + V * dl ** 3 + VI * dl ** 5,
            I + II * dl ** 2 + III * dl ** 4 + IIIA * dl ** 6)


def _to_cart(lat, lon, a, b):
    e2 = 1 - b * b / (a * a)
    nu = a / math.sqrt(1 - e2 * math.sin(lat) ** 2)
    return (nu * math.cos(lat) * math.cos(lon), nu * math.cos(lat) * math.sin(lon), (1 - e2) * nu * math.sin(lat))


def _shift(xyz, helmert, sign=1):
    """Seven-parameter Helmert transform, WGS84 -> local datum (the parameters' direction); sign -1: the reverse,
    by negated parameters."""
    x, y, z = xyz
    tx, ty, tz, s, rx, ry, rz = (sign * v for v in helmert)
    s = s * 1e-6
    rx, ry, rz = (math.radians(r / 3600) for r in (rx, ry, rz))
    return (tx + (1 + s) * x - rz * y + ry * z, ty + rz * x + (1 + s) * y - rx * z, tz - ry * x + rx * y + (1 + s) * z)


def _from_cart(xyz, a, b):
    x, y, z = xyz
    e2 = 1 - b * b / (a * a)
    pp = math.hypot(x, y)
    lat = math.atan2(z, pp * (1 - e2))
    for _ in range(10):
        nu = a / math.sqrt(1 - e2 * math.sin(lat) ** 2)
        lat = math.atan2(z + e2 * nu * math.sin(lat), pp)
    return lat, math.atan2(y, x)


def _helmert(lat, lon, p):
    """Local datum lat/lon (radians) -> WGS84 degrees."""
    lat2, lon2 = _from_cart(_shift(_to_cart(lat, lon, p["a"], p["b"]), p["helmert"], -1), *_WGS)
    return math.degrees(lat2), math.degrees(lon2)


def to_latlon(ref, irish=False):
    """Grid reference -> (lat, lon) WGS84, or None when it cannot be read."""
    en = parse(ref, irish)
    if not en:
        return None
    p = _IE if irish else _GB
    return _helmert(*_tm_inverse(*en, p), p)


def to_en(lat, lon, irish=False):
    """WGS84 degrees -> (easting, northing) on the national grid, in metres."""
    p = _IE if irish else _GB
    local = _from_cart(_shift(_to_cart(math.radians(lat), math.radians(lon), *_WGS), p["helmert"]), p["a"], p["b"])
    return _tm_forward(*local, p)


def _letter(i):
    return chr(ord("A") + i + (i > 7))           # no I


def format_en(E, N, irish=False, digits=10):
    """(easting, northing) -> "SU 12236 42189" (digits 2-10, truncated as the OS does), or None off the grid."""
    e100, n100 = int(E // 100000), int(N // 100000)
    if irish:
        if not (0 <= e100 < 5 and 0 <= n100 < 5):
            return None
        letters = _letter((4 - n100) * 5 + e100)
    else:
        if not (0 <= e100 < 7 and 0 <= n100 < 13):
            return None
        l1 = (19 - n100) - (19 - n100) % 5 + (e100 + 10) // 5
        l2 = (19 - n100) * 5 % 25 + e100 % 5
        letters = _letter(l1) + _letter(l2)
    half = digits // 2
    unit = 10 ** (5 - half)
    e, n = int(E % 100000 // unit), int(N % 100000 // unit)
    return f"{letters} {e:0{half}d} {n:0{half}d}"


def from_latlon(lat, lon, irish=False, digits=10):
    """WGS84 degrees -> grid reference string, or None off the grid."""
    return format_en(*to_en(lat, lon, irish), irish, digits)


# The island of Ireland, coarsely, with the North Channel and the Irish Sea between it and Kintyre, Galloway,
# Man and Wales (lon, lat); Rathlin and Inishtrahull inside, Islay and the Smalls outside
_IRELAND = [(-11.0, 51.2), (-6.1, 51.2), (-6.05, 52.5), (-5.85, 53.3), (-5.3, 54.2), (-5.3, 54.85),
            (-6.0, 55.2), (-6.05, 55.36), (-7.0, 55.5), (-11.0, 55.5)]


def in_ireland(lat, lon):
    inside, j = False, len(_IRELAND) - 1
    for i, (x, y) in enumerate(_IRELAND):
        xj, yj = _IRELAND[j]
        if (y > lat) != (yj > lat) and lon < (xj - x) * (lat - y) / (yj - y) + x:
            inside = not inside
        j = i
    return inside


def for_point(lat, lon, digits=10):
    """(grid reference, "OS" or "Irish") of the grid in use at a point (at sea off the other grid's squares, that
    one); None off both (the Channel Islands, abroad)."""
    irish = in_ireland(lat, lon)
    for grid in (irish, not irish):
        ref = from_latlon(lat, lon, grid, digits)
        if ref:
            return ref, "Irish" if grid else "OS"
    return None
