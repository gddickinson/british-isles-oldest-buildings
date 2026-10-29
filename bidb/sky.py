"""Sun and moon on the horizon (roadmap SK1, SK2), mirrored in app/static/sky.js.

Where the sun and moon rise and set at a place for any declination, the declinations of the solstices,
equinoxes, cross-quarter days and lunar standstills for any year (the obliquity of the ecliptic changes: the
midwinter sun of 3000 BC rose about a degree further south), the dates of those events, and the researched
alignments of `data/curated/sky_alignments.json` checked and written with their computed azimuths to
`app/static/data/sky.json` (`python -m bidb.sky [--quotes]`; `--quotes` fetches every source and looks for its
quote, → `data/sky_check.json`).

Rising and setting mean the first and last gleam of the upper limb, with standard refraction; the horizon
altitude may be given in degrees (hills raise it).
"""
import json
import math
import sys

from .config import ROOT

FILE = ROOT / "data" / "curated" / "sky_alignments.json"
OUT = ROOT / "app" / "static" / "data" / "sky.json"
CHECK = ROOT / "data" / "sky_check.json"

SUN_RADIUS = 0.266        # degrees, semi-diameter
MOON_RADIUS = 0.259
MOON_PARALLAX = 0.951     # horizontal parallax, mean
MOON_INCLINATION = 5.145  # of the moon's orbit to the ecliptic

# Ecliptic longitude of the sun at each solar event; cross-quarter days half way between.
SUN_EVENTS = {"equinox": 0, "summer_solstice": 90, "winter_solstice": 270,
              "imbolc": 315, "beltane": 45, "lughnasa": 135, "samhain": 225}
MOON_EVENTS = ("major_north", "major_south", "minor_north", "minor_south")
VERDICTS = ("established", "probable", "disputed")
SOURCE_FIELDS = ("title", "url", "quote")


def rad(x):
    return math.radians(x)


def deg(x):
    return math.degrees(x)


def obliquity(year):
    """Mean obliquity of the ecliptic in degrees (Laskar 1986, good for 10,000 years either side of AD 2000)."""
    t = (year - 2000) / 10000
    c = (-4680.93, -1.55, 1999.25, -51.38, -249.67, -39.05, 7.12, 27.87, 5.79, 2.45)
    return (84381.448 + sum(k * t ** (i + 1) for i, k in enumerate(c))) / 3600


def declination(body, event, year=2000):
    """Declination in degrees of the sun at a solar event, or of the moon at a standstill limit, in a year."""
    eps = obliquity(year)
    if body == "sun":
        return deg(math.asin(math.sin(rad(eps)) * math.sin(rad(SUN_EVENTS[event]))))
    size, side = event.split("_")
    d = eps + MOON_INCLINATION if size == "major" else eps - MOON_INCLINATION
    return d if side == "north" else -d


def refraction(h):
    """Refraction in degrees for an apparent altitude h in degrees (Bennett)."""
    return 1 / math.tan(rad(h + 7.31 / (h + 4.4))) / 60


def centre_altitude(body, horizon=0.0):
    """True geocentric altitude of the body's centre when its upper limb touches a horizon of this altitude."""
    if body == "sun":
        return horizon - refraction(horizon) - SUN_RADIUS
    return horizon - refraction(horizon) - MOON_RADIUS + MOON_PARALLAX * math.cos(rad(horizon))


def azimuth(lat, dec, rise_set="rise", body="sun", horizon=0.0):
    """Azimuth in degrees from true north where a body of this declination rises or sets; None if it never does."""
    h = rad(centre_altitude(body, horizon))
    c = (math.sin(rad(dec)) - math.sin(rad(lat)) * math.sin(h)) / (math.cos(rad(lat)) * math.cos(h))
    if abs(c) > 1:
        return None
    a = deg(math.acos(c))
    return a if rise_set == "rise" else 360 - a


def declination_of(lat, az, body="sun", horizon=0.0):
    """Declination of a body rising or setting at azimuth az (the inverse of `azimuth`)."""
    h = rad(centre_altitude(body, horizon))
    return deg(math.asin(math.sin(rad(lat)) * math.sin(h) + math.cos(rad(lat)) * math.cos(h) * math.cos(rad(az))))


def event_azimuth(lat, body, event, rise_set, year=2000, horizon=0.0):
    return azimuth(lat, declination(body, event, year), rise_set, body, horizon)


# Dates ---------------------------------------------------------------------------------------------------

def julian_day(y, m, d):
    """Julian day at 0h UT of a Gregorian date."""
    if m <= 2:
        y, m = y - 1, m + 12
    a = y // 100
    return int(365.25 * (y + 4716)) + int(30.6001 * (m + 1)) + d + 2 - a + a // 4 - 1524.5


def calendar_date(jd):
    """Gregorian (year, month, day) of a Julian day."""
    z = int(jd + 0.5)
    a = int((z - 1867216.25) / 36524.25)
    b = z + 1 + a - a // 4 + 1524
    c = int((b - 122.1) / 365.25)
    d = int(365.25 * c)
    e = int((b - d) / 30.6001)
    day = b - d - int(30.6001 * e)
    month = e - 1 if e < 14 else e - 13
    return (c - 4716 if month > 2 else c - 4715), month, day


def sun_longitude(jd):
    """Apparent ecliptic longitude of the sun in degrees (low precision, about 0.01°)."""
    t = (jd - 2451545.0) / 36525
    l0 = 280.46646 + 36000.76983 * t
    m = rad(357.52911 + 35999.05029 * t)
    c = (1.914602 - 0.004817 * t) * math.sin(m) + 0.019993 * math.sin(2 * m) + 0.000289 * math.sin(3 * m)
    omega = rad(125.04 - 1934.136 * t)
    return (l0 + c - 0.00569 - 0.00478 * math.sin(omega)) % 360


def sun_declination(jd):
    t = (jd - 2451545.0) / 36525
    eps = obliquity(2000 + t * 100) + 0.00256 * math.cos(rad(125.04 - 1934.136 * t))
    return deg(math.asin(math.sin(rad(eps)) * math.sin(rad(sun_longitude(jd)))))


def next_sun_event(event, jd):
    """Julian day of the next time after jd that the sun reaches the longitude of an event."""
    target = SUN_EVENTS[event]
    guess = jd + ((target - sun_longitude(jd)) % 360) / 360 * 365.2422
    for _ in range(6):
        guess += ((target - sun_longitude(guess) + 180) % 360 - 180) / 360 * 365.2422
    return guess if guess > jd else next_sun_event(event, jd + 1)


def node_longitude(jd):
    """Mean longitude of the moon's ascending node in degrees."""
    return (125.04452 - 1934.136261 * (jd - 2451545.0) / 36525) % 360


def next_standstill(kind, jd):
    """Julian day of the next major (node at 0°) or minor (node at 180°) lunar standstill after jd."""
    target = 0 if kind == "major" else 180
    days = ((node_longitude(jd) - target) % 360) / 1934.136261 * 36525
    return jd + (days or 6798.38)


# Researched alignments -------------------------------------------------------------------------------------

def load():
    if not FILE.exists():
        return []
    return json.loads(FILE.read_text())["alignments"]


def problems(rows=None):
    """What is wrong with the researched alignments (empty when they are fine)."""
    rows = load() if rows is None else rows
    out, seen = [], set()
    for a in rows:
        name = a.get("id", "?")
        if name in seen:
            out.append(f"{name}: duplicate id")
        seen.add(name)
        events = SUN_EVENTS if a.get("body") == "sun" else MOON_EVENTS if a.get("body") == "moon" else ()
        unnamed = a.get("event") is None and a.get("rise_set") is None and a.get("verdict") == "disputed"
        if a.get("event") not in events and not unnamed:   # a disputed lunar site may name no event
            out.append(f"{name}: unknown event {a.get('body')}:{a.get('event')}")
        if a.get("rise_set") not in ("rise", "set") and not unnamed:
            out.append(f"{name}: rise_set must be rise or set")
        if a.get("verdict") not in VERDICTS:
            out.append(f"{name}: verdict {a.get('verdict')}")
        if a.get("verdict") == "disputed" and len(a.get("views") or []) < 2:
            out.append(f"{name}: disputed with fewer than two views")
        if not isinstance(a.get("lat"), (int, float)) or not isinstance(a.get("lon"), (int, float)):
            out.append(f"{name}: no position")
        if not a.get("sources"):
            out.append(f"{name}: no sources")
        for s in a.get("sources") or []:
            missing = [f for f in SOURCE_FIELDS if not s.get(f)]
            if missing:
                out.append(f"{name}: source without {', '.join(missing)}")
    return out


def computed(a):
    """The alignment with azimuths computed for today and for the year it was built (flat horizon)."""
    out = dict(a)
    if a["event"] is None:                         # sources name no event: nothing to compute
        return out
    args = (a["lat"], a["body"], a["event"], a["rise_set"])
    out["azimuth_now"] = round(event_azimuth(*args), 1)
    if a.get("built") is not None:
        out["azimuth_built"] = round(event_azimuth(*args, year=a["built"]), 1)
    if a.get("azimuth") is not None:
        ref = out.get("azimuth_built", out["azimuth_now"])
        out["difference"] = round((a["azimuth"] - ref + 180) % 360 - 180, 1)
    return out


def claims(rows=None):
    """Each alignment as an evidence claim (quotes checked by bidb.evidence.check)."""
    return [{"id": "sky-" + a["id"], "record": a.get("record"), "name": a["name"], "field": "alignment",
             "claim": a["claim"], "value": f"{a['body']} {(a['event'] or 'unnamed event').replace('_', ' ')} {a['rise_set'] or ''}".strip(),
             "verdict": a["verdict"], "sources": a["sources"]} for a in (load() if rows is None else rows)]


def write():
    """Every alignment with its computed azimuths and each source's last quote check → sky.json."""
    ck = json.loads(CHECK.read_text()) if CHECK.exists() else {}
    rows = []
    for a in load():
        res = ck.get("sky-" + a["id"], {}).get("sources", [])
        rows.append(computed({**a, "sources": [{**s, "check": res[i] if i < len(res) else None}
                                               for i, s in enumerate(a["sources"])]}))
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({"alignments": rows}, ensure_ascii=False, separators=(",", ":")))
    return rows


def main():
    bad = problems()
    for p in bad:
        print("problem:", p)
    rows = write()
    print(f"{len(rows)} alignments → {OUT.relative_to(ROOT)}")
    for a in rows:
        diff = a.get("difference")
        flag = "" if diff is None or abs(diff) <= 3 else "   ← published azimuth differs by more than 3°"
        if a["event"] is None:
            print(f"  {a['name'][:34]:34} {a['body']} (no event named)")
            continue
        print(f"  {a['name'][:34]:34} {a['body']} {a['event']:16} {a['rise_set']:4} computed "
              f"{a.get('azimuth_built', a['azimuth_now']):6.1f}  published {a.get('azimuth') or '-'}{flag}")
    if not bad and "--quotes" in sys.argv:
        from .evidence import check
        check(claims=claims(), path=CHECK)
        write()                                   # again, with the check results
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
