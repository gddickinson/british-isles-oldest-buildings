"""The main imports by quantity, 1868-1911, for "Change over time" (roadmap C5b2b3c1).

The Statistical Abstract prints, beside the table of values (`change_trade_imports`), a table of the quantities of the
principal articles imported. The rows for corn (grain and flour), raw cotton, wool, sugar, tea and timber were read
from the page images of No. 30 (table 21, 1868-1882), No. 45 (table 27, its 1883 column), No. 46 (table 27,
1884-1898) and No. 59 (table 40, 1897-1911, the Board's new classification; rows `q59_*`, its 1904 grain column, lost
in the binding, from No. 62's table 38) into `data/curated/change/data/trade_quantities_abstract_uk.csv` (one printed
figure per line, with edition, leaf, page and table). The only printed totals, the totals of corn in Nos. 30-46, are
checked against their parts (`check`); every figure was found printed the same in another edition's OCR text, or read
on another edition's page (noted per figure). `new_goods` brings No. 59's rows to the old tables' definitions, the
same as the values'; 1897-98, given in both, differ only as `KNOWN` says (`overlap`).

Each good's average value per unit (the value of `change_trade_imports` over the quantity, same rows) is drawn as an
index (1900 = 100), so the graphs separate prices from quantities.

    python -m bidb.change_trade_quantities   → data/curated/change/data/sa_qty_*.csv + series.json entries
                                               (then python -m bidb.change_series)
"""
import json
import sys

from .change_firms import DATA
from .change_registers import _csv, _row
from . import change_trade_imports as values

READINGS = DATA / "trade_quantities_abstract_uk.csv"
SOURCES = ["stat_abstract_qty_uk"]
PREFIX = "sa_qty_"
GOODS = values.GOODS
CORN = ["q_corn_" + k for k in ("wheat", "barley", "oats", "maize", "other", "flourwheat", "flourother")]
TOTALS = {"q_corn_total": CORN}
GRAIN59 = ["q59_g_" + k[len("n59_g_"):] for k in values.GRAIN59]
# printed units: grain, cotton and sugar in cwt (raw cotton in centals of 100 lb in 1911), wool and tea in lb,
# timber in loads; graphs in thousand tons (2,240 lb) and million loads
CWT, LB, CENTAL = 112, 1, 100
UNIT = {"grain": CWT, "cotton": CWT, "sugar": CWT, "wool": LB, "tea": LB}
CENTALS = {1911}  # years of raw cotton in centals
BASE = 1900
# 1897-98 in No. 59 less No. 46: lentils (counted with seeds in No. 59 until April 1902, with "other kinds" of corn
# before), and 1898's sheep's wool, revised (No. 48 prints the revised figure too).
KNOWN = {1897: {"grain": -170264}, 1898: {"grain": -189780, "wool": 5255315}}


def load(path=READINGS):
    """{row: {year: value}} of the printed figures."""
    return values.load(path)


def check(rows):
    """Problems: a printed total that its parts do not make."""
    bad = []
    for total, parts in TOTALS.items():
        for y, t in sorted(rows.get(total, {}).items()):
            diff = sum(rows.get(p, {}).get(y, 0) for p in parts) - t
            if diff:
                bad.append(f"{total} {y}: parts - total = {diff:,}")
    return bad


def old_goods(rows, y):
    """The goods of one year from the tables of Nos. 30, 45 and 46 (1868-1898), in printed units."""
    s = lambda keys: values._sum(rows, ["q_" + k for k in keys], y)
    hewn = rows.get("q_wood_hewn", {}).get(y) or s(["wood_hewnfir", "wood_hewnoak", "wood_hewnteak",
                                                     "wood_hewnother"])
    sawn = rows.get("q_wood_sawn", {}).get(y) or s(["wood_sawnfir", "wood_sawnother"])
    return {"grain": rows["q_corn_total"][y], "cotton": rows["q_cotton_raw"][y],
            "wool": rows.get("q_wool", {}).get(y) or s(["wool_sheep", "wool_other"]),
            "sugar": s(["sugar_refined", "sugar_raw"]) if y in rows.get("q_sugar_raw", {})
            else s(["sugar_reflumps", "sugar_refother", "sugar_beet", "sugar_cane"]),
            "tea": rows["q_tea"][y], "timber": hewn + sawn + rows["q_wood_staves"][y]}


def new_goods(rows, y):
    """The goods of one year from No. 59 (1897-1911) on the old definitions: grain without rice, rice meal and other
    farinaceous substances; wool is sheep's and lambs', alpaca, vicuna and llama, and flocks and waste; timber is
    hewn (with pit props), sawn and staves, in loads (the furniture woods are in tons)."""
    n = lambda k: rows["q59_" + k][y]
    s = lambda keys: values._sum(rows, ["q59_" + k for k in keys], y)
    return {"grain": values._sum(rows, GRAIN59, y), "cotton": n("cotton_raw"),
            "wool": n("wool_sheep") + n("wool_alpaca") + n("wool_flocks"),
            "sugar": n("sugar_refined") + n("sugar_beet") + n("sugar_cane"), "tea": n("tea"),
            "timber": s(["wood_pitprops", "wood_hewnfir", "wood_hewnoak", "wood_hewnteak", "wood_hewnother",
                         "wood_sawnfir", "wood_sawnother", "wood_staves"])}


def goods(rows):
    """{year: {good: printed units}}; 1897-98 from No. 59, the later edition (as for the values)."""
    out = {y: old_goods(rows, y) for y in rows["q_corn_total"]}
    out.update({y: new_goods(rows, y) for y in rows["q59_cotton_raw"]})
    return dict(sorted(out.items()))


def overlap(rows):
    """Years given by No. 46 and No. 59 whose differences (No. 59 - No. 46) are not the known ones."""
    out = {}
    for y in sorted(set(rows["q_corn_total"]) & set(rows["q59_cotton_raw"])):
        a, b = old_goods(rows, y), new_goods(rows, y)
        d = {k: b[k] - v for k, v in a.items() if b[k] != v}
        if d != KNOWN.get(y, {}):
            out[y] = d
    return out


def tons(good, y, q):
    """Thousand tons (timber: million loads) from the printed quantity."""
    if good == "timber":
        return q / 1e6
    lb = q * (CENTAL if good == "cotton" and y in CENTALS else UNIT[good])
    return lb / 2240 / 1e3


def series(by_year, by_value):
    """{series id: [[year, value]]}: weights (thousand tons; timber million loads) and the average value per unit as
    an index, BASE = 100 (both value and quantity in the same rows)."""
    w = {g: {y: tons(g, y, v[g]) for y, v in by_year.items()} for g in GOODS}
    out = {f"{PREFIX}{g}_uk": [[y, round(x, 2 if g == "timber" else 1)] for y, x in w[g].items()] for g in GOODS}
    for g in GOODS:
        unit = {y: by_value[y][g] / x for y, x in w[g].items()}
        out[f"{PREFIX}{g}_price_uk"] = [[y, round(u / unit[BASE] * 100, 1)] for y, u in unit.items()]
    return out


COMMON = (
    "from the Board of Trade's Statistical Abstracts, read from the page images of Nos. 30, 45, 46 and 59 (and No. "
    "62 for 1904's grain; edition, page and table per figure in the data file). The totals of corn were checked "
    "against their parts, and every figure was found printed the same in another edition. Where No. 59 (the Board's "
    "new classification) and No. 46 both give a year, 1897 and 1898, they agree except as stated; No. 59 is used for "
    "them, as for the values.")
FOOD_NOTE = (
    "The weight of the grain and flour, sugar and tea brought into the United Kingdom each year, in thousand tons "
    "(the Abstract gives hundredweights and pounds), " + COMMON + " Grain and flour is the same as in \"Food "
    "imports\": wheat, barley, oats, maize, peas, beans, rye (and lentils from 1902), wheat flour and other meal, "
    "without rice; No. 59 counts lentils with seeds until April 1902 (0.17 million cwt in 1897). Sugar is refined and "
    "raw sugar, without molasses and glucose. Grain and flour was {g0:,.0f} thousand tons in {y0}, {g1:,.0f} in "
    "{y1} (most: {gmax:,.0f} in {ygmax}); sugar {s0:,.0f} and {s1:,.0f}; tea {t0:,.0f} and {t1:,.0f}. Quantities, "
    "not values: see \"Food import prices\" for what each cost.")
MATERIALS_NOTE = (
    "The weight of the raw cotton and wool brought into the United Kingdom each year, in thousand tons (the "
    "Abstract gives hundredweights of cotton, 1911 in centals of 100 lb, and pounds of wool), " + COMMON + " Wool is "
    "sheep's and lambs' wool with alpaca, vicuna and llama, and from 1883 \"other kinds and flocks\" (No. 44 "
    "gives 1882 so as 490.1 million lb, No. 30, used here, 489.0 million), not goats' hair or mohair; No. 59 (and "
    "No. 48) give 1898's sheep's wool 5.26 million lb above No. 46. Raw "
    "cotton was {c0:,.0f} thousand tons in {y0}, {c1:,.0f} in {y1} (most: {cmax:,.0f} in "
    "{ycmax}); wool {w0:,.0f} and {w1:,.0f} (most: {wmax:,.0f} in {ywmax}).")
TIMBER_NOTE = (
    "The timber brought into the United Kingdom each year, in million loads (the Abstract's measure), " + COMMON
    + " Timber is hewn (with pit props), sawn or split, and staves, as in \"Timber "
    "imports\"; mahogany and the other furniture woods, counted in tons, are left out. It was {k0:,.2f} million "
    "loads in {y0}, {k1:,.2f} in {y1} (most: {kmax:,.2f} in {ykmax}).")
PRICE_NOTE = (
    "The average value of a unit of each import (the value in \"{graph}\" divided by the quantity in the same rows "
    "of the Abstract's tables), as an index with {base} = 100. To 1870 the values are computed from average prices, "
    "from 1871 declared by the importers; an average over many kinds and qualities moves when the mix changes, so it "
    "is a rough guide to prices. {text} The quantities are " + COMMON)
FOOD_PRICES = ("Grain and flour stood at {g0:.0f} in {y0}, {gmin:.0f} in {ygmin} (the lowest) and {g1:.0f} in {y1}; "
               "sugar at {s0:.0f}, {smin:.0f} (in {ysmin}) and {s1:.0f}; tea at {t0:.0f}, {tmin:.0f} (in {ytmin}) "
               "and {t1:.0f}.")
MATERIAL_PRICES = ("Raw cotton stood at {c0:.0f} in {y0}, {cmin:.0f} in {ycmin} (the lowest) and {c1:.0f} in {y1}; "
                   "wool at {w0:.0f}, {wmin:.0f} (in {ywmin}) and {w1:.0f}; timber at {k0:.0f}, {kmin:.0f} (in "
                   "{ykmin}) and {k1:.0f}.")


def prices(v, y0, y1, title, region):
    """The two graphs of the price index: food (grain, sugar, tea) and raw materials (cotton, wool, timber)."""
    unit, src = f"index, {BASE} = 100", SOURCES + ["stat_abstract_imports_uk"]
    f = {"y0": y0, "y1": y1}
    for x, k in zip(GOODS, "gcwstk"):  # the letters of the note's fields
        d = v[x + "_price"]
        lo = min(d, key=d.get)
        f.update({k + "0": d[y0], k + "1": d[y1], k + "min": d[lo], f"y{k}min": lo})
    row = lambda x, label, **kw: _row(PREFIX + x + "_price_uk", label + " import prices", label, unit, src, region,
                                      unit="index", **kw)
    return [
        row("grain", "Grain and flour", note=PRICE_NOTE.format(graph="Food imports", base=BASE,
                                                               text=FOOD_PRICES.format(**f)),
            models=[PREFIX + "sugar_price_uk", PREFIX + "tea_price_uk"]) | {"title": f"Food import prices, {title}"},
        row("sugar", "Sugar"), row("tea", "Tea"),
        row("cotton", "Raw cotton", note=PRICE_NOTE.format(graph="Raw material imports", base=BASE,
                                                           text=MATERIAL_PRICES.format(**f)),
            models=[PREFIX + "wool_price_uk", PREFIX + "timber_price_uk"])
        | {"title": f"Raw material import prices, {title}"},
        row("wool", "Wool"), row("timber", "Timber")]


def write(rows, log=print):
    bad = check(rows)
    if bad:
        raise ValueError("; ".join(bad))
    diff = overlap(rows)
    if diff:
        raise ValueError(f"old and new tables differ: {diff}")
    by_year = goods(rows)
    if list(by_year) != list(range(min(by_year), max(by_year) + 1)):
        raise ValueError("years missing")
    by_value = values.goods(values.load())
    pts = series(by_year, by_value)
    for sid, p in pts.items():
        _csv(sid, p)
    v = {k[len(PREFIX):-3]: dict(p) for k, p in pts.items()}
    y0, y1 = min(by_year), max(by_year)
    arg = lambda d, f: f(d, key=d.get)
    g, c, w, s, t, k = (v[x] for x in GOODS)
    gp = v["grain_price"]
    title = f"{y0}-{y1}"
    region = "United Kingdom"
    kt = "thousand tons a year"
    out = [
        _row(PREFIX + "grain_uk", f"Food imports by weight, {title}", "Grain and flour", kt, SOURCES, region,
             FOOD_NOTE.format(g0=g[y0], y0=y0, g1=g[y1], y1=y1, gmax=g[arg(g, max)], ygmax=arg(g, max), s0=s[y0],
                              s1=s[y1], t0=t[y0], t1=t[y1]),
             [PREFIX + "sugar_uk", PREFIX + "tea_uk"], unit="kt"),
        _row(PREFIX + "sugar_uk", "Sugar imported", "Sugar", kt, SOURCES, region, unit="kt"),
        _row(PREFIX + "tea_uk", "Tea imported", "Tea", kt, SOURCES, region, unit="kt"),
        _row(PREFIX + "cotton_uk", f"Raw cotton and wool imported by weight, {title}", "Raw cotton", kt, SOURCES,
             region, MATERIALS_NOTE.format(c0=c[y0], y0=y0, c1=c[y1], y1=y1, cmax=c[arg(c, max)],
                                           ycmax=arg(c, max), w0=w[y0], w1=w[y1], wmax=w[arg(w, max)],
                                           ywmax=arg(w, max)),
             [PREFIX + "wool_uk"], unit="kt"),
        _row(PREFIX + "wool_uk", "Wool imported", "Wool", kt, SOURCES, region, unit="kt"),
        _row(PREFIX + "timber_uk", f"Timber imported, {title}", "Timber", "million loads a year", SOURCES, region,
             TIMBER_NOTE.format(k0=k[y0], y0=y0, k1=k[y1], y1=y1, kmax=k[arg(k, max)], ykmax=arg(k, max)),
             unit="m loads"),
    ] + prices(v, y0, y1, title, region)
    for r in out:
        r["zero"] = True
    path = DATA.parent / "series.json"
    keep = [x for x in json.loads(path.read_text()) if not x["id"].startswith(PREFIX)]
    path.write_text(json.dumps(keep + out, ensure_ascii=False, indent=1))
    log(f"{len(by_year)} years {y0}-{y1}, totals of corn checked; grain {g[y0]:,.0f} -> {g[y1]:,.0f}, raw cotton "
        f"{c[y0]:,.0f} -> {c[y1]:,.0f} thousand tons; grain price index {gp[y0]:.0f} -> {gp[y1]:.0f} ({BASE} = 100)")


def run(log=print):
    write(load(), log)


if __name__ == "__main__":
    run(lambda m: print(m, file=sys.stderr, flush=True))
