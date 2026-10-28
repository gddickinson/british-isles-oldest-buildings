"""Wages before the Board of Trade's index (roadmap C5d2b2b), read by bidb.change_wages:

- G. H. Wood, "The Course of Average Wages between 1790 and 1860", Economic Journal 9 (1899), 588-592: "Table showing
  course of average wages in towns, 1790-1860 (1840 = 100)", p. 591 (Internet Archive
  `sim_economic-journal_march-december-1899_9_33-36`, image n598): money wages in 24 towns and districts (all trades
  found, agriculture left out) and their unweighted average, read from the page image into
  `data/curated/change/data/wages_wood_1790_1860.csv` (Wood died in 1940: public domain). `check` tests each printed
  average against the mean of the towns printed for that year (`KNOWN`: 1860 printed 116, the towns give 117.4).
  Divided by the ONS long-run RPI from 1800 (`real`; to 1810 over the mean of the year and those beside it, since Wood
  reads each year to 1810 as "the middle year of a short period").
- Bowley's money-wage index numbers by decade, 1780-1899 (1890-99 = 100), "which our work indicates, but which are
  not yet established" (Wages in the United Kingdom in the Nineteenth Century, 1900, p. 126; quoted per figure in
  estimates.json, model `wages_bowley1900`), drawn as estimate dots at mid-decade, on 1840-50 = 100 (`bowley`).
"""
import csv
import json

from .change_firms import DATA
from .change_registers import _row

WOOD = DATA / "wages_wood_1790_1860.csv"
ESTIMATES = DATA.parent / "estimates.json"
KNOWN = {1860: 116}         # printed averages that the printed towns do not give within a point
WOOD_TOL = 1.0              # the average is rounded and Wood may have rounded the towns' ratios first
SHORT_PERIOD = 1810         # to this year each year stands for three


def load(path=WOOD):
    """{town: {year: index}}, the "Average" row included."""
    with open(path, newline="") as f:
        return {r["town"]: {int(k): int(v) for k, v in r.items() if k.isdigit() and v} for r in csv.DictReader(f)}


def check(table=None):
    """Problems: a printed average more than `WOOD_TOL` from the mean of that year's towns, `KNOWN` apart."""
    table = table or load()
    avg, bad = table["Average"], []
    for y, v in avg.items():
        mean = town_mean(y, table)
        if abs(mean - v) > WOOD_TOL and KNOWN.get(y) != v:
            bad.append(f"Wood {y}: printed {v}, the towns give {mean:.2f}")
    return bad


def town_mean(year, table=None):
    table = table or load()
    towns = [t[year] for name, t in table.items() if name != "Average" and year in t]
    return sum(towns) / len(towns)


def average(table=None):
    return dict(sorted((table or load())["Average"].items()))


def real(wood, prices):
    """{year: money wages over prices, 1840 = 100}, years with prices only."""
    def p(y):
        ys = [x for x in (y - 1, y, y + 1) if x in prices] if y <= SHORT_PERIOD else [y]
        return sum(prices[x] for x in ys) / len(ys)
    r = {y: w / p(y) for y, w in wood.items() if y in prices}
    return {y: round(v / r[1840] * 100, 1) for y, v in sorted(r.items())}


def model():
    return next(m for m in json.loads(ESTIMATES.read_text())["models"] if m["id"] == "wages_bowley1900")


def bowley(m=None):
    """[(mid-decade year, value, low, high, label)] on 1840-50 = 100 (Bowley's printed figures × 100/60)."""
    pts = (m or model())["points"]
    base = next(p["value"] for p in pts if p["year"] == 1845)
    k = 100 / base
    return [(p["year"], round(p["value"] * k, 1), p["low"] and round(p["low"] * k, 1), p["high"] and round(p["high"] * k, 1),
             f"Bowley 1900, {p['decade']}: {p['printed']} (1890-99 = 100)") for p in pts]


NOTE = ("Wages before the Board of Trade's index (drawn from 1879 in \"Real wage rates, 1879-1938\"), 1840 = 100. Money "
        "wages: G. H. Wood's index of average wages in towns (1899), the unweighted average of 24 towns and districts "
        "(London, Manchester, Glasgow, Dublin, Leeds, Sheffield, the Durham and Northumberland and the South of Scotland "
        "coalfields, Monimail in Fife and Glamorgan for rural artisans and labourers...), all trades for which he found "
        "figures, agriculture left out; a town's line is led by its staple trade. To 1810 \"each year stated may, "
        "therefore, best be considered as the middle year of a short period\". Real wages: the same over the ONS's "
        "long-run Retail Prices Index (to 1810 the mean of the year and those beside it), from 1800 when the RPI "
        "begins. Bowley warned in 1900 that \"it is unfortunate that we cannot with safety use index numbers of "
        "wholesale prices as a measure of the purchasing power of the workman's wages\"; the RPI before 1914 is "
        "itself joined from older estimates, and 1840 was a dear year (prices fell {p4050:.0f}% to 1850), so the "
        "real line rises sharply after it. Money wages rose {m1:.0f}% from 1790 to 1810 and fell {m2:.0f}% from 1810 "
        "to 1845 (Wood: \"the increase (69 per cent.) which took place between 1790 and 1810; the decrease (19 per "
        "cent.) between 1810 and 1845\"); real wages were {r1800:.0f} in 1800, {r1810:.0f} in 1810 and {r1860:.0f} in "
        "1860. Dots: Bowley's index numbers by decade (1900), \"which our work indicates, but which are not yet "
        "established\", printed on 1890-99 = 100 and drawn here on 1840-50 = 100 at mid-decade, ranges as bars: "
        "{b1785:.0f} in the 1780s, {b1815:.0f} in the 1810s, {b1895:.0f} in the 1890s. Wood's printed average for 1860 "
        "({a1860}, as Bowley's) is {gap:.1f} below the mean of the towns he prints for that year.")


def series(prices):
    """({series id: points}, series.json rows): the graph "Wages in towns, 1790-1860"."""
    wood = average()
    r = real(wood, prices)
    b = bowley()
    bv = {y: v for y, v, *_ in b}
    note = NOTE.format(p4050=(1 - prices[1850] / prices[1840]) * 100, m1=(wood[1810] / wood[1790] - 1) * 100,
                       m2=(1 - wood[1845] / wood[1810]) * 100, r1800=r[1800], r1810=r[1810], r1860=r[1860],
                       b1785=bv[1785], b1815=bv[1815], b1895=bv[1895], a1860=wood[1860], gap=town_mean(1860) - wood[1860])
    rows = [
        _row("wages_real_wood_uk", f"Wages in towns, {min(wood)}-{max(wood)}", f"real wages, {min(r)}-{max(r)}",
             "index, 1840 = 100", ["wood_1899_wages", "ons_cdko", "est_wages_bowley1900"], "United Kingdom", note,
             ["wages_money_wood_uk", "wages_bowley_est"], unit=""),
        _row("wages_money_wood_uk", "Money wages in towns (Wood 1899)", "money wages (Wood)", "index, 1840 = 100",
             ["wood_1899_wages"], "United Kingdom", unit=""),
        _row("wages_bowley_est", "Money wages by decade (Bowley 1900)", "money wages by decade (Bowley, estimates)",
             "index, 1840-50 = 100", ["est_wages_bowley1900"], "United Kingdom", unit=""),
    ]
    rows[2]["style"] = "estimates"
    for row in rows:
        row["zero"] = False
    return {"wages_real_wood_uk": r, "wages_money_wood_uk": wood, "wages_bowley_est": b}, rows
