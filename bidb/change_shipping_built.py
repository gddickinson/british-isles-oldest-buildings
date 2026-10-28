"""Merchant ships built in the United Kingdom, 1846-1938, for "Change over time" (roadmap C5e2b1), read by
bidb.change_shipping. Before 1897 the Statistical Abstract counts only ships for British owners, on three
definitions, read from the page images into `data/curated/change/data/shipping_built_early_abstract_uk.csv` (one
printed row per line with edition, leaf, page, table and `basis`):

- `registered`: "built and registered" (No. 8 table 33 p. 52, 1846-1860; No. 9 table 34 p. 52, 1847-1861), "built
  and first registered" (No. 23 table 41 p. 94, 1861-1871; No. 26 table 41 p. 100, 1864-1870; No. 32 table 55
  p. 127, 1870);
- `built`: No. 23's starred years 1872-1875, "built in those years, whether registered or not";
- `british`: "built, whether registered or not (exclusive of vessels built for foreigners)" (No. 26, 1871-1878;
  No. 32, 1871-1884), "and of vessels built for Her Majesty's Navy" (No. 33 table 58 p. 133, 1871-1885; No. 46
  table 61 p. 178, 1884-1898);
- `foreign`: "built for foreigners, for war and mercantile purposes" (No. 46 table 62 p. 179, 1884-1898).

`check` tests every row's sail + steam against its printed total (tonnage always; counts but the two misprints in
`KNOWN`). Each year is taken from the latest edition that prints it (`latest`); the overlaps agree except the
revisions in `REVISED` (`revisions`). From 1897 the line is No. 59's onwards (all merchant ships, those for foreign
owners included; bidb.change_shipping), so the joined line has breaks at 1871 and 1897.
"""
import csv

from .change_firms import DATA

FILE = DATA / "shipping_built_early_abstract_uk.csv"
FIRST, JOIN = 1846, 1897
# printed vessel counts whose parts do not add up (the tonnages do)
KNOWN = {(8, 1847): "830 + 103 sailing and steam vessels printed as 936 (also in No. 9)",
         (9, 1847): "as No. 8",
         (46, 1887): "ships for foreigners: 14 + 142 printed as 56 (156)"}
# (earlier edition, later edition): years the later edition revised
REVISED = {(9, 23): [1861], (23, 26): [1867, 1868, 1869, 1870, 1871, 1872, 1873], (26, 32): [1877, 1878]}
BREAKS = [[1871, "From 1871 ships built whether registered or not, those built for foreigners left out (No. 26 "
                 "onwards); before, ships built and first registered in the UK. No. 23 had printed {y1871:,} tons for "
                 "1871 on the old definition, No. 26 {n1871:,} on the new"],
          [JOIN, "From 1897 all merchant ships built in the UK, those for foreign owners included (No. 59 onwards); "
                 "before, those for British owners only. 1897: {b1897:,} tons for British owners and {f1897:,} for "
                 "foreigners (war and merchant ships) in No. 46; {a1897:,} in all in No. 59"]]


def rows():
    with open(FILE, newline="") as f:
        return [dict(r, year=int(r["year"]), no=int(r["no"])) for r in csv.DictReader(f)]


def check(data=None):
    """Problems: rows whose sail + steam differ from the printed total (counts but the misprints in KNOWN)."""
    bad = []
    for r in data or rows():
        if int(r["sailing"]) + int(r["steam"]) != int(r["total"]):
            bad.append(f"No. {r['no']} {r['year']}: tons do not add up")
        if (r["no"], r["year"]) not in KNOWN and int(r["sailing_n"]) + int(r["steam_n"]) != int(r["total_n"]):
            bad.append(f"No. {r['no']} {r['year']}: vessels do not add up")
    return bad


def latest(data=None, foreign=False):
    """{year: row} from the latest edition printing it, ships for British owners (or, `foreign`, for foreigners)."""
    out = {}
    for r in sorted(data or rows(), key=lambda r: r["no"]):
        if (r["basis"] == "foreign") == foreign:
            out[r["year"]] = r
    return out


def revisions(data=None):
    """{(earlier, later): [years]} where consecutive editions printing a year give different tonnages."""
    by_year, out = {}, {}
    for r in sorted(data or rows(), key=lambda r: r["no"]):
        if r["basis"] != "foreign":
            by_year.setdefault(r["year"], []).append(r)
    for y, rs in sorted(by_year.items()):
        for a, b in zip(rs, rs[1:]):
            if (a["sailing"], a["steam"], a["total"]) != (b["sailing"], b["steam"], b["total"]):
                out.setdefault((a["no"], b["no"]), []).append(y)
    return out


def joined(built, data=None):
    """{year: thousand tons}: British owners' ships 1846-1896 (latest edition), all merchant ships from 1897."""
    early = latest(data)
    out = {y: round(int(r["total"]) / 1000, 1) for y, r in early.items() if y < JOIN}
    out.update({y: round(v["total"], 1) for y, v in built.items() if y >= JOIN})
    return out


def breaks(built, data=None):
    data = data or rows()
    early, foreign = latest(data), latest(data, foreign=True)
    n23 = next(int(r["total"]) for r in data if r["no"] == 23 and r["year"] == 1871)
    vals = {"y1871": n23, "n1871": int(early[1871]["total"]), "b1897": int(early[JOIN]["total"]),
            "f1897": int(foreign[JOIN]["total"]), "a1897": int(built[JOIN]["raw"]["total"])}
    return [[y, t.format(**vals)] for y, t in BREAKS]


def facts(data=None):
    """Figures quoted in the note: steam against sail among ships for British owners."""
    early = latest(data)
    steam_ahead = [y for y, r in sorted(early.items()) if int(r["steam"]) > int(r["sailing"])]
    sail_last = max(y for y, r in early.items() if int(r["sailing"]) > int(r["steam"]))
    peak = max((y for y in early if y < JOIN), key=lambda y: int(early[y]["total"]))
    return {"steam_first": steam_ahead[0], "sail_last": sail_last, "peak": peak,
            "peak_tons": int(early[peak]["total"]) / 1000, "t1846": int(early[FIRST]["total"]) / 1000}
