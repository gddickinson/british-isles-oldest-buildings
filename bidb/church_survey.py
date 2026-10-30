"""Roadmap SK5b2a: a private check of the church axes of bidb.church_orientation against a field survey.

Ian Hinton's survey of 1,926 medieval rural churches (Aspects of the Alignment and Location of Medieval Rural
Churches, PhD thesis, University of East Anglia 2010; spreadsheets with the thesis at
https://ueaeprints.uea.ac.uk/id/eprint/20521/) gives each church's nave and chancel alignment measured by compass
on site (true, local magnetic declination taken off), a grid reference to 100 m and, for some, the elevation of
the eastern horizon. Each survey church is matched to the nearest catalogue church with an outline within
`MATCH_M` (a shared saint, or a village name in the record's name, decides between several), and the axis from
the OSM outline and the skyline from the terrain model (`church_orientation.json`) set against the survey.

The spreadsheet's title sheet reserves copyright to the author: "no data from the spreadsheet, nor any information
derived therefrom, may be published without the author's prior, written consent". So nothing here is published:
the spreadsheet stays in the download cache (`<cache>/hinton/medieval.xls`, read with bidb.xls_read) and the
results go only to the git-ignored `runs/church_survey.json` (`python -m bidb.church_survey`).
"""
import json
import math
import re
import sqlite3
import statistics

from . import osgrid
from .church_orientation import OUT
from .config import ROOT, db_path
from .xls_read import sheets

URL = "https://ueaeprints.uea.ac.uk/20521/3/Medieval_church_data_-_thesis_-_Ian_Hinton.xls"
SHEET = "Survey data (all 1926 churches)"
RESULT = ROOT / "runs" / "church_survey.json"
MATCH_M = 250
SHUFFLES = 5000
COLS = {"village": 2, "dedication": 3, "sq": 4, "e": 5, "n": 6, "county": 7, "plan": 9, "tower": 10,
        "nave": 13, "chancel": 14, "aisles": 15, "nave_l": 20, "nave_w": 21, "horizon": 39}


def fetch(log=print):
    from .change_registers import _download
    return _download(URL, "medieval.xls", log, folder="hinton")


def survey():
    """The survey's churches with a grid reference and a true nave alignment."""
    out = []
    for row in sheets(fetch())[SHEET][4:]:
        row = row + [""] * (60 - len(row))
        r = {k: row[i] for k, i in COLS.items()}
        if not isinstance(r["nave"], float) or not r["sq"] or not isinstance(r["e"], float):
            continue
        try:
            lat, lon = osgrid.to_latlon("%s %03d %03d" % (r["sq"].strip(), r["e"], r["n"]))
        except (ValueError, KeyError):
            continue
        r.update(lat=lat, lon=lon, village=str(r["village"]).strip(), dedication=str(r["dedication"]).strip())
        out.append(r)
    return out


def _metres(a, b):
    k = math.cos(math.radians(a[0]))
    return math.hypot((a[0] - b[0]) * 111320, (a[1] - b[1]) * 111320 * k)


def _saint(text):
    return {w for w in re.findall(r"[a-z]+", text.lower()) if w not in ("st", "saint", "and", "the", "of", "church")}


def match(rows, records):
    """[(survey row, catalogue record)]: the one catalogue church within MATCH_M sharing the survey's saint or
    with the village in its name (a grid reference slip would otherwise pair churches of different places)."""
    cells = {}
    for rec in records:
        cells.setdefault((round(rec["lat"], 2), round(rec["lon"], 2)), []).append(rec)
    pairs = []
    for r in rows:
        near = [rec for dy in (-1, 0, 1) for dx in (-1, 0, 1)
                for rec in cells.get((round(round(r["lat"], 2) + dy / 100, 2), round(round(r["lon"], 2) + dx / 100, 2)), [])
                if _metres((r["lat"], r["lon"]), (rec["lat"], rec["lon"])) <= MATCH_M]
        named = [rec for rec in near if _saint(r["dedication"]) & _saint(rec["dedication"] + " " + rec["name"])
                 or r["village"].lower() in rec["name"].lower()]
        if len(named) == 1:
            pairs.append((r, named[0]))
    return pairs


def _diff(a, b):
    return (a - b + 90) % 180 - 90


def _stats(diffs):
    if not diffs:
        return None
    a = sorted(abs(d) for d in diffs)
    return {"n": len(a), "median_abs": round(statistics.median(a), 2), "mean": round(statistics.mean(diffs), 2),
            "within_2": round(sum(d <= 2 for d in a) / len(a), 3), "within_5": round(sum(d <= 5 for d in a) / len(a), 3),
            "p90_abs": round(a[int(0.9 * (len(a) - 1))], 1)}


def feast_test(pairs):
    """bidb.church_orientation's feast-day test on the matched medieval churches, with the OSM axes and again with
    the surveyed nave alignments: does axis error hide churches facing their saint's sunrise?"""
    from .church_orientation import _test, fixed_feasts, load, medieval
    feasts = load()["feasts"]
    con = sqlite3.connect(db_path())
    years = dict(con.execute("SELECT id, year_start FROM buildings WHERE category_group = 'Religious'"))
    osm, field = [], []
    for r, rec in pairs:
        entry = feasts.get(rec["dedication"])
        row = {"lat": rec["lat"], "year": years.get(rec["id"]), "dedication": rec["dedication"], "hz": rec["hz"] or 0.0}
        if not (entry and fixed_feasts(entry) and medieval(row) and 30 <= r["nave"] <= 150):
            continue
        osm.append(dict(row, axis=(rec["az"], rec["el"])))
        field.append(dict(row, axis=(r["nave"], rec["el"])))
    return {k: _test(rows, feasts, 1, horizon=hz, shuffles=SHUFFLES)
            for k, rows, hz in (("osm", osm, False), ("survey", field, False),
                                ("osm_skyline", osm, True), ("survey_skyline", field, True))}


def run(log=print):
    data = json.loads(OUT.read_text())
    fields = data["fields"]
    con = sqlite3.connect(db_path())
    records = []
    for rid, name, ded, lat, lon in con.execute(
            "SELECT id, name, dedication, lat, lon FROM buildings WHERE category_group = 'Religious' AND lat IS NOT NULL"):
        c = data["churches"].get(rid)
        if c and c[fields.index("el")] >= 1.4:
            records.append({"id": rid, "name": name or "", "dedication": ded or "", "lat": lat, "lon": lon,
                            "az": c[fields.index("az")], "el": c[fields.index("el")], "hz": c[fields.index("hz")]})
    rows = survey()
    pairs = match(rows, records)
    nave = [_diff(rec["az"], r["nave"]) for r, rec in pairs]
    from .church_orientation import axis
    fps = dict(con.execute("SELECT id, footprint FROM buildings WHERE category_group = 'Religious' AND footprint <> ''"))
    rect = [_diff(axis(json.loads(fps[rec["id"]]))[0], r["nave"]) for r, rec in pairs]
    out = {"survey": len(rows), "matched": len(pairs), "nave": _stats(nave),
           "nave_rectangle": _stats(rect),       # the axis before SK5b2b: smallest rectangle round the outline
           "chancel": _stats([_diff(rec["az"], r["chancel"]) for r, rec in pairs if isinstance(r["chancel"], float)])}
    # by plan and outline shape: do aisles, towers and short outlines skew the OSM axis?
    groups = {"aisles": lambda r, rec: str(r["aisles"]).strip().lower() not in ("", "none"),
              "no aisles": lambda r, rec: str(r["aisles"]).strip().lower() in ("", "none"),
              "elongation < 2": lambda r, rec: rec["el"] < 2, "elongation >= 2": lambda r, rec: rec["el"] >= 2,
              "nave-chancel bend >= 3": lambda r, rec: isinstance(r["chancel"], float) and abs(_diff(r["nave"], r["chancel"])) >= 3}
    out["by"] = {k: _stats([_diff(rec["az"], r["nave"]) for r, rec in pairs if f(r, rec)]) for k, f in groups.items()}
    out["feast_test"] = feast_test(pairs)
    hz = [(rec["hz"], r["horizon"]) for r, rec in pairs if rec["hz"] is not None and isinstance(r["horizon"], float)]
    if hz:
        d = [a - b for a, b in hz]
        out["horizon"] = {"n": len(d), "median_diff": round(statistics.median(d), 2),
                          "median_abs": round(statistics.median(abs(x) for x in d), 2),
                          "survey_median": round(statistics.median(b for _, b in hz), 2),
                          "model_median": round(statistics.median(a for a, _ in hz), 2)}
    out["worst"] = sorted(({"id": rec["id"], "name": rec["name"], "survey": r["village"], "osm": rec["az"],
                            "nave": r["nave"], "el": rec["el"]} for r, rec in pairs),
                          key=lambda x: -abs(_diff(x["osm"], x["nave"])))[:25]
    RESULT.parent.mkdir(exist_ok=True)
    RESULT.write_text(json.dumps(out, indent=1, ensure_ascii=False))
    log(json.dumps({k: v for k, v in out.items() if k != "worst"}, indent=1))
    return out


if __name__ == "__main__":
    run()
