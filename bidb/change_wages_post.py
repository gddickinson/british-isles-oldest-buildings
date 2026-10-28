"""Wage rates 1935-1975 (roadmap C5d2b1): the Ministry of Labour's (from 1968 the Department of Employment's) index of
weekly wage rates, all workers, all industries and services, read from the page images of the Annual Abstract of
Statistics Nos. 84 (1935-1946), 88, 90, 92, 93, 94, 100, 104, 108 and 112 (1975) into
`data/curated/change/data/wages_mol_1935_1975.csv` (one printed figure per line with edition, leaf, page, table; a
printed range such as "99-100" kept as low and high). Four bases, each figure at the end of the month:

- 1 September 1939 = 100, monthly 1935-1947 (No. 84 table 140);
- 30 June 1947 = 100, June 1948-1955 and January 1956 (Nos. 88, 90, 92, 93, 94);
- 31 January 1956 = 100, June 1956-1972 and July 1972 (Nos. 94, 100, 104, 108, 112);
- 31 July 1972 = 100, June 1973-1975 (No. 112).

Rows of kind `link` give the level of the new base date on the old base, as printed: June 1947 "between 166 and 167,
taking September 1939 = 100" (Nos. 84, 90), revised to "between 167 and 168" (No. 94); January 1956 from No. 94's
factor for all workers, 1.561 ("the new series can be linked with the old series on a broad basis"); July 1972 249.5
(No. 112, printed on both bases). `chain` takes each year's June figure on the newest base, from the latest edition
that prints it, and puts it on the 1939 base by the latest links; `check` tests the editions' overlaps and that the
links agree with the old series' own figures.
"""
import csv

from .change_firms import DATA

PATH = DATA / "wages_mol_1935_1975.csv"
BASES = ("1939-09-01", "1947-06-30", "1956-01-31", "1972-07-31")
REVISED = {(1966, "1956-01-31"): 0.1, (1967, "1956-01-31"): 0.1, (1971, "1956-01-31"): 0.3,   # later editions revised
           (1947, "1939-09-01"): 1.0}                       # the June 1947 link, revised by No. 94
EDITION_NO = lambda e: int(e.rsplit("_", 1)[1])


def load(path=PATH):
    with open(path, newline="") as f:
        return [{**r, "year": int(r["year"]), "low": float(r["low"]), "high": float(r["high"]),
                 "value": (float(r["low"]) + float(r["high"])) / 2} for r in csv.DictReader(f)]


def latest(rows, kind="rate", month="June"):
    """{(year, base): row} from the latest edition printing it."""
    out = {}
    for r in sorted(rows, key=lambda r: EDITION_NO(r["edition"])):
        if r["kind"] == kind and r["month"] == month:
            out[(r["year"], r["base"])] = r
    return out


def links(rows):
    """{base: its base date's level on the 1939 base}, from the latest printed links."""
    lk = {}
    for r in sorted((r for r in rows if r["kind"] == "link"), key=lambda r: EDITION_NO(r["edition"])):
        lk[BASES[BASES.index(r["base"]) + 1]] = r["value"]
    out = {BASES[0]: 100.0}
    for old, new in zip(BASES, BASES[1:]):
        out[new] = out[old] * lk[new] / 100
    return out


def chain(rows):
    """{year: (index on 1 September 1939 = 100, base read)}: each June on the newest base printed for that year."""
    rates, lk = latest(rows), links(rows)
    out = {}
    for (year, base), r in sorted(rates.items(), key=lambda kv: (kv[0][0], BASES.index(kv[0][1]))):
        out[year] = (round(r["value"] * lk[base] / 100, 2), base)
    return dict(sorted(out.items()))


def check(rows=None):
    """Problems: one figure printed differently by two editions (beyond the known revisions), a link that does not
    meet the old series' own figure (June 1956: 105.4 on the new base against 164 on the old), a year missing."""
    rows = rows if rows is not None else load()
    bad, seen = [], {}
    for r in rows:
        k = (r["year"], r["month"], r["base"], r["kind"])
        if k in seen and abs(seen[k]["value"] - r["value"]) > REVISED.get((r["year"], r["base"]), 0) + 1e-9:
            bad.append(f"{k}: {seen[k]['value']} in {seen[k]['edition']}, {r['value']} in {r['edition']}")
        seen.setdefault(k, r)
    rates = {(r["year"], r["month"], r["base"]): r["value"] for r in rows if r["kind"] == "rate"}
    lk = {BASES[BASES.index(r["base"]) + 1]: r["value"] for r in sorted(
        (r for r in rows if r["kind"] == "link"), key=lambda r: EDITION_NO(r["edition"]))}
    b39, b47, b56, _ = BASES
    for y, m, new, old, on_new in ((1947, "June", b47, b39, 100.0), (1956, "January", b56, b47, 100.0),
                                   (1956, "June", b56, b47, rates.get((1956, "June", b56)))):
        printed = rates.get((y, m, old))
        if printed is None or on_new is None or abs(on_new * lk[new] / 100 - printed) > 1:
            bad.append(f"{m} {y}: the link gives {on_new} on the {new} base = "
                       f"{on_new * lk[new] / 100 if on_new else '?'} on the old, which prints {printed}")
    years = sorted(chain(rows))
    if years != list(range(years[0], years[-1] + 1)):
        bad.append(f"years missing: {sorted(set(range(years[0], years[-1] + 1)) - set(years))}")
    return bad
