"""Occupations by sector in England and Wales at the censuses of 1881-1911 (roadmap C5c2b1), read from the page images of
the 1911 Census Summary Tables (Cd. 7929, 1915; Internet Archive `censusofenglandw1911grea`, public domain):

- Table 65 (leaves 283, 285, 287; printed pp. 274-278): persons aged 10 and over engaged in occupations by order, on the
  1911 classification carried back to 1881, with the lines that show dealers on their own.
- Table 64 (leaf 281, p. 272): the food, tobacco and drink lines by sex, which the condensed list joins makers and dealers
  in; where 1881 and 1891 print two or three lines as one figure (millers with corn dealers, tobacco makers with
  tobacconists...), the figure is shared out as the lines were in 1901 (`split`).

`data/curated/change/data/work_census_ew.csv` has one printed figure per line (edition, leaf, page, table); `check`
tests every order against the total occupied and every split line against its order or line in Table 65.

The three sectors (`shares`), on the census's own makers and dealers:
- farming, fishing and mining: orders VII-IX (domestic gardeners are in VII, as the census puts them);
- making and building: orders X-XXI less the dealers the tables show apart (dealers in metals and machines, drapers, the
  dealers of food, tobacco and drink, inns and eating houses), plus the engine drivers of order XXII;
- services: orders I-VI, those dealers, and the general shopkeepers, pawnbrokers and costermongers of order XXII;
- left out, as no industry is stated: order XXII's general labourers and its "others" (5.0% to 1.8% and 1.1% to 1.0% of
  those occupied, 1881 to 1911). Dealers the condensed list does not show apart (coal, timber, clothes...) stay with
  their trade.
"""
import csv
from collections import defaultdict

from .change_firms import DATA

READINGS = DATA / "work_census_ew.csv"
YEARS = (1881, 1891, 1901, 1911)
PRIMARY = ["o07", "o08", "o09"]
MAKING = [f"o{n:02d}" for n in range(10, 22)]
SERVICES = [f"o{n:02d}" for n in range(1, 7)]
PARTS = {"o10": ["o10_dealers"], "o18": ["o18_drapers"],
         "o20": ["o20_food", "o20_tobacco", "o20_drinks", "o20_inn_service", "o20_lodging"],
         "o22": ["o22_shopkeepers", "o22_costermongers", "o22_labourers", "o22_engine", "o22_others"]}
# Table 64 lines of order XX: makers (the rest of each line are dealers); the line in Table 65 they add up to
FOOD = ["400", "401", "402", "403", "404", "405", "406", "407", "408", "409", "410", "411", "412", "413", "414",
        "415", "416", "417", "418", "419"]
TOBACCO = ["420", "421"]
DRINKS = ["422", "423", "424", "427", "433"]
MAKERS = {"400", "402", "404", "406", "408", "410", "412", "413", "414", "417", "418",   # creamery, curers, slaughterers,
          "420", "422", "423", "424"}                     # millers, bakers' makers, sugar, jam, cocoa, mineral water,
                                                          # mustard; tobacco makers; maltsters, brewers, distillers
NO_INDUSTRY = ["o22_labourers", "o22_others"]


def load(path=READINGS):
    """{row: {year: number}} as printed (Table 64 rows by sex: t64_m_401, a bracket t64_m_402+403)."""
    out = defaultdict(dict)
    with open(path, newline="") as f:
        for r in csv.DictReader(f):
            out[r["row"]][int(r["year"])] = int(r["value"])
    return out


def split(rows, sex, year):
    """{line: number} for one sex and year, a bracketed figure shared out as its lines were in 1901."""
    pre = f"t64_{sex}_"
    out = {}
    for key, vals in rows.items():
        if not key.startswith(pre) or year not in vals:
            continue
        lines = key[len(pre):].split("+")
        if len(lines) == 1:
            out[lines[0]] = vals[year]
            continue
        base = [rows[pre + ln][1901] for ln in lines]
        for ln, b in zip(lines, base):
            out[ln] = vals[year] * b / sum(base)
    return out


def persons(rows, year):
    """{Table 64 line: persons} for a year (makers and dealers of food, tobacco and drink)."""
    m, f = split(rows, "m", year), split(rows, "f", year)
    return {k: m.get(k, 0) + f.get(k, 0) for k in set(m) | set(f)}


def check(rows):
    """Problems: an order sum, a set of split lines, or Table 64's lines not adding up to their printed total."""
    bad = []
    t = {k[4:]: v for k, v in rows.items() if k.startswith("t65_")}
    for y in YEARS:
        orders = sum(t[f"o{n:02d}"][y] for n in range(1, 23))
        if orders != t["total_occupied"][y]:
            bad.append(f"{y}: orders I-XXII add to {orders}, total occupied {t['total_occupied'][y]}")
        for o in ("o20", "o22"):
            s = sum(t[p][y] for p in PARTS[o])
            if s != t[o][y]:
                bad.append(f"{y}: the lines of {o} add to {s}, printed {t[o][y]}")
        p = persons(rows, y)
        for line, codes in (("o20_food", FOOD), ("o20_tobacco", TOBACCO), ("o20_drinks", DRINKS)):
            s = round(sum(p.get(c, 0) for c in codes))
            if s != t[line][y]:
                bad.append(f"{y}: Table 64 lines of {line} add to {s}, Table 65 prints {t[line][y]}")
    return bad


def sectors(rows, year):
    """(primary, secondary, tertiary, no industry stated) persons in a census year."""
    t = {k[4:]: v[year] for k, v in rows.items() if k.startswith("t65_")}
    p = persons(rows, year)
    makers = sum(v for k, v in p.items() if k in MAKERS)
    xx_dealers = t["o20"] - makers
    prim = sum(t[o] for o in PRIMARY)
    sec = (sum(t[o] for o in MAKING) - t["o10_dealers"] - t["o18_drapers"] - xx_dealers + t["o22_engine"])
    ter = (sum(t[o] for o in SERVICES) + t["o10_dealers"] + t["o18_drapers"] + xx_dealers
           + t["o22_shopkeepers"] + t["o22_costermongers"])
    return prim, sec, ter, sum(t[o] for o in NO_INDUSTRY)


def shares(rows=None):
    """{year: (primary, secondary, tertiary) % of those occupied whose industry is known}."""
    rows = rows or load()
    out = {}
    for y in YEARS:
        prim, sec, ter, _ = sectors(rows, y)
        total = prim + sec + ter
        out[y] = tuple(round(v / total * 100, 2) for v in (prim, sec, ter))
    return out


LABEL = ("Census of England and Wales {year} (1911 Summary Tables, Tables 64-65): all occupied aged 10 and over, "
         "dealers moved to services, general labourers left out")


def points(rows=None):
    """{sector index: [(year, value, None, None, label)]} for the England and Wales dots."""
    s = shares(rows)
    return {i: [(y, v[i], None, None, LABEL.format(year=y)) for y, v in sorted(s.items())] for i in range(3)}


if __name__ == "__main__":
    r = load()
    print(check(r) or "all sums agree")
    for y in YEARS:
        prim, sec, ter, no = sectors(r, y)
        print(y, shares(r)[y], f"left out {no / (prim + sec + ter + no) * 100:.1f}%")
