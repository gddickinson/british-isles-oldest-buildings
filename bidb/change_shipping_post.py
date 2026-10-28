"""Shipping 1935-1974 for "Change over time" (roadmap C5e2b2a), read by bidb.change_shipping: the merchant fleet on
the United Kingdom register and merchant ships built, from the page images of the Annual Abstract of Statistics
(public domain: published 1947-1975; Internet Archive, collection pub_annual-abstract-of-statistics-gb):

- registered (`data/curated/change/data/shipping_registered_annual_uk.csv`, end of year, steam and motor vessels
  only): No. 84 (1935-1946, table 244, p. 207), No. 88 (1938, 1941-1950, table 254, p. 243), No. 94 (1938, 1947-1956,
  table 247, p. 208), No. 100 (1952-1962, table 253, p. 199), No. 104 (1956-1966, table 259, p. 211), No. 108
  (1960-1970, table 263, p. 234; 1970 estimated); number, gross tons by size and net tons. No. 109 has no such table
  (only ships of 500 gross tons and over), so the line ends in 1970;
- built (`shipping_completed_annual_uk.csv`, thousand gross tons, vessels of 100 gross tons and over): No. 84 (table
  184, p. 157: launched in the UK and Eire 1935-1939 from Lloyd's Register, completed from 1940), No. 88 (table 187,
  p. 180), No. 90 (table 178, p. 172), No. 94 (table 192, p. 166), No. 100 (table 198, p. 160), No. 104 (table 201,
  p. 171), No. 108 (table 207, p. 191), No. 112 (table 219, p. 214): completions by kind (tankers, passenger and
  cargo, other, non-propelled from No. 108) and those for export (from No. 100).

`check` tests every row's parts against its printed total (within the rounding of the parts) and the editions'
overlaps (`overlaps` must equal `REVISED`); No. 84 prints 12,524 vessels for 1944, whose parts give 12,525 as in No. 88,
and No. 108 1,384 thousand tons completed in 1961, whose parts give 1,390 as in Nos. 100 and 104 (`MISPRINTS`: the
sum is used). Each year comes from the latest edition that prints it.
"""
import csv

from .change_firms import DATA

FILES = {"registered": DATA / "shipping_registered_annual_uk.csv", "built": DATA / "shipping_completed_annual_uk.csv"}
FIRST_BUILT, LAST_BUILT, LAST_REG = 1940, 1974, 1970
MISPRINTS = {("registered", 84, 1944): "number 12,524 printed; parts 12,525 (No. 88)",
             ("built", 108, 1961): "total 1,384 printed; parts 1,390 (Nos. 100, 104)"}
# editions that print a different figure for the same year: the later one is used
REVISED = {("built", 84, 88): [1941], ("built", 84, 90): [], ("built", 88, 90): [], ("built", 90, 94): [],
           ("built", 100, 104): [], ("built", 104, 108): [], ("built", 108, 112): [],
           ("built", 88, 94): [], ("built", 84, 94): [], ("built", 100, 108): [],
           ("registered", 84, 88): [], ("registered", 88, 94): [], ("registered", 94, 100): [],
           ("registered", 100, 104): [], ("registered", 104, 108): [], ("registered", 94, 104): [],
           ("registered", 100, 108): [], ("built", 104, 112): [], ("registered", 84, 94): []}
REG_PARTS = (("number", ("n_under500", "n_500_1599", "n_1600"), ("n_under500", "n_500plus")),
             ("gross", ("g_under500", "g_500_1599", "g_1600"), ("g_under500", "g_500plus")))
BUILT_PARTS = ("tankers", "passenger_cargo", "other", "non_propelled")


def rows(which, data=None):
    if data is not None:
        return data
    with open(FILES[which], newline="") as f:
        out = list(csv.DictReader(f))
    for r in out:
        r["year"], r["no"] = int(r["year"]), int(r["no"])
    return out


def _int(r, k):
    return int(r[k]) if r.get(k) else 0


def check(which, data=None):
    """Problems: rows whose parts do not add to the printed total (beyond rounding), unless a known misprint."""
    bad = []
    for r in rows(which, data):
        if (which, r["no"], r["year"]) in MISPRINTS:
            continue
        if which == "registered":
            for total, three, two in REG_PARTS:
                parts = three if r[three[1]] else two
                s = sum(_int(r, k) for k in parts)
                if abs(s - _int(r, total)) > (len(parts) - 1 if total == "gross" else 0):
                    bad.append(f"registered No. {r['no']} {r['year']}: {total} parts {s}, printed {r[total]}")
        elif r["tankers"]:
            s = sum(_int(r, k) for k in BUILT_PARTS)
            n = sum(1 for k in BUILT_PARTS if r[k])
            if abs(s - _int(r, "total")) > n - 1:
                bad.append(f"built No. {r['no']} {r['year']}: parts {s}, printed {r['total']}")
    return bad


def value(which, r, key):
    """A printed figure, the sum of its parts where the printed total is a known misprint."""
    if (which, r["no"], r["year"]) in MISPRINTS:
        if which == "built" and key == "total":
            return sum(_int(r, k) for k in BUILT_PARTS)
        if which == "registered" and key == "number":
            return sum(_int(r, k) for k in REG_PARTS[0][1] if r[k]) or sum(_int(r, k) for k in REG_PARTS[0][2])
    return _int(r, key)


def overlaps(data=None):
    """{(which, earlier No., later No.): [years printed differently]} for the editions that share years."""
    out = {}
    for which in FILES:
        rs = rows(which, data and data.get(which))
        keys = ("number", "gross", "net") if which == "registered" else ("total", "tankers", "export")
        by = {}
        for r in rs:
            if which == "built" and r["basis"] != "completed":
                continue
            by.setdefault(r["year"], []).append(r)
        for y, ys in sorted(by.items()):
            for a in ys:
                for b in ys:
                    if a["no"] < b["no"]:
                        k = (which, a["no"], b["no"])
                        out.setdefault(k, [])
                        if any(a[c] and b[c] and value(which, a, c) != value(which, b, c) for c in keys):
                            out[k].append(y)
    return out


def latest(which, basis="completed", data=None):
    """{year: row} from the latest edition printing the year."""
    out = {}
    for r in sorted(rows(which, data), key=lambda r: r["no"]):
        if which == "registered" or r["basis"] == basis:
            out[r["year"]] = r
    return out


def registered():
    """{year: million net tons} 1939-1970, steam and motor vessels (Annual Abstract)."""
    return {y: round(value("registered", r, "net") / 1000, 3) for y, r in latest("registered").items() if y >= 1939}


def built():
    """{series id: {year: thousand gross tons}}: completions, tankers, for export."""
    late = latest("built")
    out = {"shipping_completed_uk": {y: value("built", r, "total") for y, r in late.items()},
           "shipping_completed_tankers_uk": {y: _int(r, "tankers") for y, r in late.items() if r["tankers"]},
           "shipping_completed_export_uk": {y: _int(r, "export") for y, r in late.items() if r["export"]}}
    return out


def facts():
    """Figures quoted in the notes."""
    reg, late = latest("registered"), latest("built")
    launched = {y: int(r["total"]) for y, r in latest("built", "launched").items()}
    lloyds = int(latest("built", "lloyds")[1938]["total"])
    gross = {y: _int(r, "gross") for y, r in reg.items()}
    net = {y: value("registered", r, "net") for y, r in reg.items()}
    small = {y: value("registered", r, "number") - _int(r, "n_500plus") - _int(r, "n_500_1599") - _int(r, "n_1600")
             for y, r in reg.items()}
    tot = {y: value("built", r, "total") for y, r in late.items()}
    exp = {y: _int(r, "export") for y, r in late.items() if r["export"]}
    peak = max((y for y in tot if y >= 1946), key=tot.get)
    return {"launched": launched, "lloyds1938": lloyds, "gross": gross, "net": net, "small": small, "total": tot,
            "export": exp, "peak": peak, "low": min(tot, key=tot.get),
            "export_peak": max(exp, key=exp.get), "net_min_war": min((y for y in net if 1939 <= y <= 1945), key=net.get)}
