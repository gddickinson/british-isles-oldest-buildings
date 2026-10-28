"""Bank clearing 1935-1974 (roadmap C5e2b2b2b3b2a), read by bidb.change_clearing: the Annual Abstract of Statistics'
tables of bank clearing, read from the page images of Nos. 84 (1935-1946, table 282 p. 236), 88 (1938, 1941-1950,
table 300 p. 281), 92 (table 312 p. 270), 96 (table 316 p. 273), 99 (table 329 p. 275), 104 (table 358 p. 307), 108
(table 368 p. 347), 111 (table 384 p. 369) and 112 (1964-1974, table 396 p. 387) →

- `clearing_london_annual_uk.csv`: one printed row per edition and year, £ million: the debit clearing in all
  (`debit_total`: the London Bankers' Clearing House and the provincial houses), the credit clearing (from 1 May 1960),
  the Clearing House's total and its town, metropolitan and country clearings (to 26 August 1939) and the general
  clearing (from 28 August 1939: the clearing banks' emergency operations, kept after them), and the provincial
  houses' total;
- `clearing_provincial_annual_uk.csv`: the provincial houses one by one (Southampton from 1945) and their printed total,
  to one decimal in Nos. 84 and 88, whole millions from No. 92. All the provincial clearings but Liverpool's afternoon
  clearing were abolished and transferred to the general clearing from 12 January 1968.

`check`: the Clearing House's clearings add to its total, the debit clearing is the Clearing House plus the provincial
houses, the towns add to their printed total within the rounding of their parts, and every figure printed by two
editions is equal but the `REVISED` (1968-1969 debit totals: No. 108 left out the Liverpool afternoon clearing; the
1970 credit clearing, "not comparable with earlier figures owing to mergers among the London Clearing banks"); every
year 1939-1974 is printed (1974 by No. 112 only: No. 113 is still in Crown copyright).
"""
import csv

from .change_firms import DATA

LONDON = DATA / "clearing_london_annual_uk.csv"
PROVINCIAL = DATA / "clearing_provincial_annual_uk.csv"
L_COLS = ("debit_total", "credit", "total", "town", "metropolitan", "country", "general", "provincial")
TOWNS = ("birmingham", "bradford", "bristol", "hull", "leeds", "leicester", "liverpool", "manchester", "newcastle",
         "nottingham", "sheffield", "southampton")
FIRST, LAST, ABOLISHED = 1939, 1974, 1968
# (column, year): the edition that revised the figure printed before
REVISED = {("debit_total", 1968): 111, ("debit_total", 1969): 111, ("credit", 1970): 111}


def _num(v):
    return float(v) if v != "" else None


def load():
    """(london rows, provincial rows): dicts with edition (int), page, table, year and figures (None where blank)."""
    with open(LONDON, newline="") as f:
        lon = [dict(r, edition=int(r["edition"]), year=int(r["year"]), **{c: _num(r[c]) for c in L_COLS})
               for r in csv.DictReader(f)]
    with open(PROVINCIAL, newline="") as f:
        pro = [dict(r, edition=int(r["edition"]), year=int(r["year"]), **{c: _num(r[c]) for c in TOWNS + ("total",)})
               for r in csv.DictReader(f)]
    return lon, pro


def town_sum(r):
    return sum(r[t] for t in TOWNS if r[t] is not None)


def sum_problems(lon, pro):
    bad = []
    for r in lon:
        s = sum(r[c] or 0 for c in ("town", "metropolitan", "country", "general"))
        if abs(s - r["total"]) > 1:
            bad.append(f"London No. {r['edition']} {r['year']}: clearings add to {s:,.0f}, total {r['total']:,.0f}")
        if r["debit_total"] is not None:
            want = r["total"] + (r["provincial"] or 0)
            if abs(want - r["debit_total"]) > 1:
                bad.append(f"debit No. {r['edition']} {r['year']}: {want:,.0f} against {r['debit_total']:,.0f}")
    for r in pro:
        if r["total"] is None:
            continue
        parts = sum(1 for t in TOWNS if r[t] is not None)
        allowed = 0.25 if r["edition"] < 92 else parts * 0.5       # whole millions from No. 92
        if abs(town_sum(r) - r["total"]) > allowed:
            bad.append(f"provincial No. {r['edition']} {r['year']}: towns add to {town_sum(r):.1f}, total {r['total']}")
    return bad


def _by_year(rows):
    out = {}
    for r in sorted(rows, key=lambda r: r["edition"]):
        out.setdefault(r["year"], []).append(r)
    return out


def overlap_problems(lon, pro):
    """A figure printed by two editions must agree (to the rounding of the later one for the provincial houses)."""
    bad = []
    for y, rs in _by_year(lon).items():
        for c in L_COLS:
            have = [r for r in rs if r[c] is not None]
            for a, b in zip(have, have[1:]):
                if a[c] != b[c] and REVISED.get((c, y)) != b["edition"]:
                    bad.append(f"London {c} {y}: Nos. {a['edition']} {a[c]:,.0f} and {b['edition']} {b[c]:,.0f}")
    for y, rs in _by_year(pro).items():
        for c in TOWNS + ("total",):
            have = [r for r in rs if r[c] is not None]
            for a, b in zip(have, have[1:]):
                if abs(a[c] - b[c]) > 0.5:
                    bad.append(f"provincial {c} {y}: Nos. {a['edition']} {a[c]} and {b['edition']} {b[c]}")
    return bad


def check(rows=None):
    lon, pro = rows or load()
    bad = sum_problems(lon, pro) + overlap_problems(lon, pro)
    have = _by_year(lon)
    bad += [f"London {y}: not printed" for y in range(FIRST, LAST + 1) if y not in have]
    bad += [f"provincial {y}: not printed" for y in range(FIRST, ABOLISHED) if y not in _by_year(pro)]
    return bad


def latest(rows):
    """{year: row} from the latest edition that prints the year."""
    return {y: rs[-1] for y, rs in _by_year(rows).items()}


def values(rows, col):
    return {y: r[col] for y, r in sorted(latest(rows).items()) if r[col] is not None}


def provincial_total(pro):
    """{year: £ million} to 1967: the latest printed total, or for 1939-1940 (no total printed) the towns' sum."""
    out = {}
    for y, r in sorted(latest(pro).items()):
        out[y] = r["total"] if r["total"] is not None else round(town_sum(r), 1)
    return out


def facts(rows=None):
    lon, pro = rows or load()
    best = latest(lon)
    return {"total": values(lon, "total"), "town": values(lon, "town"), "general": values(lon, "general"),
            "country": values(lon, "country"), "credit": values(lon, "credit"), "debit": values(lon, "debit_total"),
            "afternoon": {y: r["provincial"] for y, r in best.items() if y >= ABOLISHED},
            "provincial": provincial_total(pro), "man": values(pro, "manchester"), "liv": values(pro, "liverpool"),
            "first_edition": {y: rs[0]["edition"] for y, rs in _by_year(lon).items()}}


if __name__ == "__main__":
    print("\n".join(check()) or "all checks pass")
