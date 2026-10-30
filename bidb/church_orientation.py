"""Church orientation (roadmap SK5): do medieval churches face sunrise on their patron saint's day?

Each religious record's axis is taken from its OpenStreetMap outline (`footprint`): since SK5b2b the direction of its
walls, or the nave, chancel or church part where one is mapped (bidb.church_axes; towers, porches and aisles turn the
long side of the smallest rectangle round the outline, `axis`, kept for comparison); outlines less than 1.4 times as
long as wide have no clear axis. An outline that is not a church building (a precinct, churchyard or tower: SK5b2c,
bidb.church_sites) takes the axis of the largest church building mapped inside it, else is left out. The east end is the
end between north and south through east. For churches begun before 1540 with a dedication whose feast is fixed
(`data/curated/church_orientation.json`, researched with quoted sources), the sun's rising direction on the feast
day of the year begun, in the Julian calendar then in use, is compared with the axis (bidb.sky), over a flat
horizon and over the church's own skyline (SK5b: bidb.sky_horizon, bare ground: the altitude of the skyline on the
axis is the horizon for both the axis and the feast, so the sun's path is taken as straight across the few degrees
between them). The share of churches within `TOLERANCE` degrees of a feast is set against chance: the same churches
with their dedications shuffled (`SHUFFLES` times). A third test also counts the feast of the other saint an
ambiguous Wikidata dedication may mean (`if_other_saint`: St Oswald churches may be Oswald of Northumbria's). Written
to `app/static/data/church_orientation.json` for detail views and the Sky calendar page
(`python -m bidb.church_orientation [--flat]`; `--flat` skips the skylines; `--quotes` checks the sources' quotes).
"""
import json
import math
import random
import sqlite3
import sys

from . import sky
from .config import ROOT, db_path

FILE = ROOT / "data" / "curated" / "church_orientation.json"
OUT = ROOT / "app" / "static" / "data" / "church_orientation.json"
CHECK = ROOT / "data" / "church_orientation_check.json"
MIN_ELONGATION = 1.4
MEDIEVAL = 1540           # churches begun before the Reformation
TOLERANCE = 5.0           # degrees
SHUFFLES = 200


# Axis ------------------------------------------------------------------------------------------------------

def _points(geom):
    """Outer-ring points of a GeoJSON Polygon or MultiPolygon."""
    polys = [geom["coordinates"]] if geom["type"] == "Polygon" else geom["coordinates"]
    return [tuple(p[:2]) for poly in polys for p in poly[0]]


def _hull(pts):
    pts = sorted(set(pts))
    if len(pts) < 3:
        return pts
    cross = lambda o, a, b: (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])
    lower, upper = [], []
    for p in pts:
        while len(lower) >= 2 and cross(lower[-2], lower[-1], p) <= 0:
            lower.pop()
        lower.append(p)
    for p in reversed(pts):
        while len(upper) >= 2 and cross(upper[-2], upper[-1], p) <= 0:
            upper.pop()
        upper.append(p)
    return lower[:-1] + upper[:-1]


def axis(geom):
    """(azimuth of the long axis's eastern end in degrees, length / width), or None for a tiny or broken outline."""
    pts = _points(geom)
    if len(pts) < 3:
        return None
    lat0 = sum(p[1] for p in pts) / len(pts)
    k = math.cos(math.radians(lat0))
    xy = _hull([((lon * k) * 111320, lat * 111320) for lon, lat in pts])   # metres east, north
    if len(xy) < 3:
        return None
    best = None
    for i in range(len(xy)):
        (x1, y1), (x2, y2) = xy[i], xy[(i + 1) % len(xy)]
        a = math.atan2(y2 - y1, x2 - x1)
        c, s = math.cos(a), math.sin(a)
        us = [x * c + y * s for x, y in xy]
        vs = [-x * s + y * c for x, y in xy]
        w, h = max(us) - min(us), max(vs) - min(vs)
        if best is None or w * h < best[0]:
            best = (w * h, a if w >= h else a + math.pi / 2, max(w, h), min(w, h))
    _, a, long_, short = best
    if short < 1:
        return None
    az = (90 - math.degrees(a)) % 180          # from north, clockwise; an axis has two ends: keep 0-180
    return az, long_ / short


# Dates -----------------------------------------------------------------------------------------------------

def julian_calendar_day(y, m, d):
    """Julian day at 0h UT of a date in the Julian calendar."""
    if m <= 2:
        y, m = y - 1, m + 12
    return int(365.25 * (y + 4716)) + int(30.6001 * (m + 1)) + d - 1524.5


def feast_azimuth(lat, year, month_day, horizon=0.0):
    """Where the sun rose over a horizon of this altitude (degrees) on a Julian-calendar date of a year."""
    m, d = (int(x) for x in month_day.split("-"))
    jd = julian_calendar_day(year, m, d) + 0.25            # about sunrise in the isles
    return sky.azimuth(lat, sky.sun_declination(jd), "rise", "sun", horizon)


def axis_dates(lat, az, year, horizon=0.0):
    """Julian-calendar (month, day) dates of the year when the sun rose on this azimuth over a horizon."""
    dec = sky.declination_of(lat, az, "sun", horizon)
    start = julian_calendar_day(year, 1, 1) + 0.25
    out, prev = [], sky.sun_declination(start) - dec
    for i in range(1, 366):
        cur = sky.sun_declination(start + i) - dec
        if prev * cur <= 0 and prev != cur:
            jd = start + i - 1 + prev / (prev - cur)
            out.append(_julian_md(jd))
        prev = cur
    return out


def _julian_md(jd):
    """(month, day) in the Julian calendar of a Julian day."""
    c = int(jd + 0.5) + 1524
    d = int((c - 122.1) / 365.25)
    e = int((c - int(365.25 * d)) / 30.6001)
    day = c - int(365.25 * d) - int(30.6001 * e)
    return (e - 1 if e < 14 else e - 13), day


# Researched feasts and the test --------------------------------------------------------------------------

def load():
    return json.loads(FILE.read_text()) if FILE.exists() else {"feasts": {}, "studies": []}


def fixed_feasts(entry, other=False):
    """A dedication's fixed feasts; with `other`, also the feast of the other saint an ambiguous label may mean."""
    out = [f for f in entry.get("feasts", []) if not f.get("movable") and f.get("date")]
    alt = entry.get("if_other_saint")
    return out + [{"name": alt["name"], "date": alt["date"]}] if other and alt else out


def churches(con, parts=None, sites=None):
    """Religious records with an outline and their axis (SK5b2b): the mapped nave, chancel or church part where
    there is one (`parts`: bidb.church_axes.fetch_parts), else the direction of the outline's walls (`src`);
    `sites`: (outline tags, church buildings) of bidb.church_sites for outlines that are not the church."""
    from .church_axes import body_axis, parts_of, wall_axis
    rows = con.execute("SELECT id, lat, lon, year_start, dedication, footprint FROM buildings "
                       "WHERE category_group = 'Religious' AND footprint <> '' AND lat IS NOT NULL")
    out, outlines = [], {}
    for rid, lat, lon, year, ded, fp in rows:
        try:
            outlines[rid] = json.loads(fp)
            ax, src = wall_axis(outlines[rid]), "walls"
        except (ValueError, KeyError, TypeError, IndexError, ZeroDivisionError):
            ax, src = None, None
        out.append({"id": rid, "lat": lat, "lon": lon, "year": year, "dedication": ded or "",
                    "axis": ax[:2] if ax else None, "src": src})
    by_id = parts_of(outlines, parts or [])
    for r in out:
        b = body_axis(by_id.get(r["id"], []))
        if b:
            r["axis"], r["src"] = b[:2], "part"
    if sites:
        _site_axes(out, outlines, *sites)
    return out


def _site_axes(rows, outlines, tags, buildings):
    """SK5b2c: an outline that is not a church building (bidb.church_sites) takes the axis of the largest church
    building mapped inside it (`src` "building"), else has none (`src` "site")."""
    from .church_axes import wall_axis
    from .church_sites import inner_church, site_kind
    for r in rows:
        if r["src"] == "part" or r["id"] not in outlines or not site_kind(tags.get(r["id"])):
            continue
        inner = inner_church(outlines[r["id"]], buildings)
        ax = wall_axis(inner["geom"]) if inner else None
        r["axis"], r["src"] = (ax[:2], "building") if ax else (None, "site")


def east_facing(r):
    return bool(r["axis"]) and r["axis"][1] >= MIN_ELONGATION and 30 <= r["axis"][0] <= 150


def medieval(r):
    return r["year"] is not None and 600 <= r["year"] < MEDIEVAL


def add_skylines(rows, workers=8, log=print):
    """Each medieval east-facing church's skyline altitude on its axis (`hz`, degrees; bidb.sky_horizon)."""
    from .sky_horizon import altitude_at, many
    todo = [r for r in rows if east_facing(r) and medieval(r)]
    for r, p in zip(todo, many([(round(r["lat"], 5), round(r["lon"], 5)) for r in todo], workers, log)):
        r["hz"] = round(altitude_at(p["alt"], p["step"], r["axis"][0]), 2)


def best_diff(lat, year, az, feasts, horizon=0.0):
    """(smallest |axis - feast sunrise| in degrees, that feast) over a dedication's fixed feasts."""
    best = None
    for f in feasts:
        fa = feast_azimuth(lat, year, f["date"], horizon)
        if fa is None:
            continue
        diff = abs((az - fa + 90) % 180 - 90)
        if best is None or diff < best[0]:
            best = (diff, f)
    return best


def analyse(rows, feasts, seed=1):
    """Per church: axis, dates and its feast's difference, flat and over the skyline (rows with `hz`); the share
    within TOLERANCE against shuffled dedications: flat, over the skyline, and over the skyline with other saints."""
    out, tested = {}, []
    for r in rows:
        if not r["axis"]:
            if r.get("src") == "site":
                out[r["id"]] = {"az": None, "el": None, "src": "site"}
            continue
        az, el = r["axis"]
        rec = {"az": round(az, 1), "el": round(el, 2), "src": r.get("src")}
        if east_facing(r):
            year = r["year"] if medieval(r) else None
            rec["dates"] = ["%02d-%02d" % md for md in axis_dates(r["lat"], az, year or 1300)]
            rec["cal"] = year                   # None: not medieval or undated, dates for 1300
            if "hz" in r:
                rec["hz"] = r["hz"]
                rec["dates_hz"] = ["%02d-%02d" % md for md in axis_dates(r["lat"], az, year, r["hz"])]
            entry = feasts.get(r["dedication"])
            if year and entry and fixed_feasts(entry):
                best = best_diff(r["lat"], year, az, fixed_feasts(entry))
                if best:
                    rec["feast"], rec["diff"] = best[1]["name"], round(best[0], 1)
                    tested.append(r)
                    if "hz" in r:
                        best = best_diff(r["lat"], year, az, fixed_feasts(entry), r["hz"])
                        rec["feast_hz"], rec["diff_hz"] = best[1]["name"], round(best[0], 1)
        out[r["id"]] = rec
    summary = {"churches": len(rows), "from_parts": sum(1 for r in out.values() if r["src"] == "part"),
               "from_buildings": sum(1 for r in out.values() if r["src"] == "building"),
               "sites_left_out": sum(1 for r in out.values() if r["src"] == "site"),
               "with_axis": sum(1 for r in out.values() if (r["el"] or 0) >= MIN_ELONGATION),
               "east_facing": sum(1 for r in out.values() if "dates" in r), "tolerance": TOLERANCE, "shuffles": SHUFFLES}
    summary.update(_test(tested, feasts, seed))
    summary["by_dedication"] = _by_dedication(tested, out)
    with_hz = [r for r in tested if "hz" in r]
    if with_hz:
        summary["skyline"] = _test(with_hz, feasts, seed, horizon=True)
        summary["other_saints"] = _test(with_hz, feasts, seed, horizon=True, other=True)
        summary["other_saints"]["labels"] = sorted(k for k, v in feasts.items() if v.get("if_other_saint"))
    return out, summary


def _test(tested, feasts, seed, horizon=False, other=False, shuffles=SHUFFLES):
    """How many churches face within TOLERANCE of their own saint's feast sunrise, against shuffled dedications;
    `p`: the share of shuffles with as many or more."""
    def hit(r, ded):
        b = best_diff(r["lat"], r["year"], r["axis"][0], fixed_feasts(feasts[ded], other), r["hz"] if horizon else 0.0)
        return b is not None and b[0] <= TOLERANCE
    observed = sum(hit(r, r["dedication"]) for r in tested)
    rnd, chance = random.Random(seed), []
    for _ in range(shuffles if tested else 0):
        deds = [r["dedication"] for r in tested]
        rnd.shuffle(deds)
        chance.append(sum(hit(r, d) for r, d in zip(tested, deds)))
    chance.sort()
    return {"tested": len(tested), "observed": observed,
            "chance_mean": round(sum(chance) / len(chance), 1) if chance else None,
            "chance_95": [chance[int(len(chance) * 0.025)], chance[int(len(chance) * 0.975) - 1]] if chance else None,
            "p": round(sum(c >= observed for c in chance) / len(chance), 3) if chance else None}


def _by_dedication(tested, out):
    by = {}
    for r in tested:
        b = by.setdefault(r["dedication"], [0, 0])
        b[0] += 1
        b[1] += out[r["id"]]["diff"] <= TOLERANCE
    return sorted(([d, n, k] for d, (n, k) in by.items()), key=lambda x: -x[1])


FIELDS = ("az", "el", "dates", "cal", "feast", "diff", "hz", "dates_hz", "feast_hz", "diff_hz", "src")


def run(log=print, skylines=True):
    data = load()
    con = sqlite3.connect(db_path())
    from .church_axes import fetch_parts
    from .church_sites import fetch_buildings, outline_tags, site_kind
    tags, outlines = outline_tags(), {}
    for rid, fp in con.execute("SELECT id, footprint FROM buildings WHERE category_group = 'Religious' "
                               "AND footprint <> '' AND lat IS NOT NULL"):
        if site_kind(tags.get(rid)):
            outlines[rid] = json.loads(fp)
    rows = churches(con, fetch_parts(log), (tags, fetch_buildings(outlines, log)))
    if skylines:
        add_skylines(rows, log=log)
    per, summary = analyse(rows, data["feasts"])
    OUT.write_text(json.dumps({"summary": summary, "studies": data.get("studies", []), "fields": FIELDS,
                               "churches": {k: [v.get(f) for f in FIELDS] for k, v in per.items()}},
                              ensure_ascii=False, separators=(",", ":")))
    log(f"{summary['churches']} religious records with outlines; {summary['from_buildings']} outlines of a site or "
        f"another building read from the church inside, {summary['sites_left_out']} left out")
    log(f"{summary['with_axis']} with a clear axis, "
        f"{summary['east_facing']} facing between NNE and SSE; {summary['tested']} medieval with a fixed feast")
    if summary["tested"]:
        log(f"within {TOLERANCE}° of a feast-day sunrise: {summary['observed']} "
            f"({100 * summary['observed'] / summary['tested']:.1f}%); shuffled dedications: mean {summary['chance_mean']}, "
            f"95% range {summary['chance_95']}")
    for key, what in (("skyline", "over the skyline"), ("other_saints", "over the skyline, either saint")):
        t = summary.get(key)
        if t:
            log(f"{what}: {t['observed']} of {t['tested']}; shuffled mean {t['chance_mean']}, 95% {t['chance_95']}")
    return summary


def claims():
    """Feasts and studies as evidence claims (quotes checked by bidb.evidence.check)."""
    data = load()
    out = [{"id": "feast-" + k, "record": None, "name": k, "field": "feast", "claim": ", ".join(
        f"{f['name']} {f.get('date') or '(movable)'}" for f in v["feasts"]), "verdict": "kept", "sources": v["sources"]}
        for k, v in data["feasts"].items()]
    return out + [{"id": "study-" + s["id"], "record": None, "name": s["citation"], "field": "study",
                   "claim": s["finding"], "verdict": "kept", "sources": s["sources"]} for s in data.get("studies", [])]


if __name__ == "__main__":
    run(skylines="--flat" not in sys.argv)
    if "--quotes" in sys.argv:
        from .evidence import check
        check(claims=claims(), path=CHECK)
