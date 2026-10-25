"""The main imports by quantity, 1854-1938, for "Change over time" (roadmap C5b2b3c1, C5b2b3c2, C5b2b3c3).

The Statistical Abstract prints, beside the table of values (`change_trade_imports`), a table of the quantities of the
principal articles imported. The rows for corn (grain and flour), raw cotton, wool, sugar, tea and timber were read
from the page images of No. 16 (table 10, 1854-55) and No. 18 (table 15, 1856-67; rows `qe_*`), No. 19 (table 15,
1857-67, the first edition with other kinds of corn and meal and a total of corn), No. 30 (table 21, 1868-1882), No. 45 (table 27, its 1883 column), No. 46 (table 27,
1884-1898) and No. 59 (table 40, 1897-1911, the Board's new classification; rows `q59_*`, its 1904 grain column, lost
in the binding, from No. 62's table 38), No. 70 (table 206, 1911-25) and No. 83 (table 285, 1924-38; rows `q70_*`, `q83_*`,
the classification of 1920) into `data/curated/change/data/trade_quantities_abstract_uk.csv` (one printed
figure per line, with edition, leaf, page and table). The printed totals (corn in Nos. 19-46, raw sugar and hewn and
sawn timber in Nos. 16 and 18) are checked against their parts (`check`; one known slip, `SLIPS`); every figure was found printed the same in another edition's OCR text, or read
on another edition's page (noted per figure). `new_goods` brings No. 59's rows to the old tables' definitions, the
same as the values'; 1897-98, given in both, differ only as `KNOWN` says (`overlap`). Nos. 16 and 18 give no other
kinds of corn, and less timber than No. 19 for every year both print (`early_overlap`), so grain and timber begin in
1857; raw cotton, wool, sugar and tea are taken from them for 1854-56. Nos. 70 and 83 print no totals; `c20_goods` gives
their goods, 1911 (No. 70 against No. 59) differs only by the definitions in `C20_KNOWN`, 1924-25 only by No. 83's
rounding to thousand lb (`c20_overlap`). From 1912 they give quantities of sawn softwood and pit props alone, drawn
as a line of their own ("softwood", 1911-34, before the Abstract's change to standards and fathoms).

Each good's average value per unit (the value of `change_trade_imports` over the quantity, same rows) is drawn as an
index (1900 = 100), so the graphs separate prices from quantities; to 1867 with the quantities of the values' own
editions, Nos. 16 and 18 (`price_goods`; grain from No. 19); timber from 1912 is softwood's, linked at 1911.

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
EARLY = "qe_"  # Nos. 16 (1854-55) and 18 (1856-67)
TOTALS = {"q_corn_total": CORN, EARLY + "sugar_rawtotal": [EARLY + "sugar_rawbp", EARLY + "sugar_rawforeign"],
          EARLY + "wood_hewntotal": [EARLY + "wood_hewnforeign", EARLY + "wood_hewnbp"],
          EARLY + "wood_sawntotal": [EARLY + "wood_sawnforeign", EARLY + "wood_sawnbp"]}
# printed totals their parts do not make, with the sum: No. 16's 1854 hewn timber, printed 1,216,920 in Nos. 10-16
# too (one edition of the 1846-65 volume prints 1,216,209)
SLIPS = {("qe_wood_hewntotal", 1854): 1216209}
EARLY_WOOD = ["wood_" + k for k in ("hewnforeign", "hewnbp", "teak", "sawnforeign", "sawnbp", "staves")]
COTTON_GAP = 0.001  # No. 19 revises No. 18's raw cotton by up to 0.06%
GRAIN59 = ["q59_g_" + k[len("n59_g_"):] for k in values.GRAIN59]
# printed units: grain, cotton and sugar in cwt (raw cotton in centals of 100 lb from 1911), wool and tea in lb,
# timber in loads; graphs in thousand tons (2,240 lb) and million loads
CWT, LB, CENTAL = 112, 1, 100
UNIT = {"grain": CWT, "cotton": CWT, "sugar": CWT, "wool": LB, "tea": LB}
CENTALS = 1911  # first year of raw cotton in centals
LOADS = ("timber", "softwood")
BASE = 1900
# 1897-98 in No. 59 less No. 46: lentils (counted with seeds in No. 59 until April 1902, with "other kinds" of corn
# before), and 1898's sheep's wool, revised (No. 48 prints the revised figure too).
KNOWN = {1897: {"grain": -170264}, 1898: {"grain": -189780, "wool": 5255315}}
C20 = {70: "q70_", 83: "q83_"}
SOFTWOOD = ["wood_sawnsoft", "wood_pitprops"]
SOFTWOOD_END = 1934  # pit props without other pitwood from 1935; standards and fathoms from 1936
# pounds in a printed unit of Nos. 70 and 83: wool in centals (No. 70) or thousand lb (No. 83), tea in lb or thousand
# lb; unmanufactured cotton waste (from 1920) in cwt, raw cotton in centals
C20_LB = {70: {"wool": CENTAL, "tea": LB}, 83: {"wool": 1000, "tea": 1000}}
WASTE = CWT / CENTAL
# 1911 in No. 70 less No. 59 on the old definitions (softwood against all timber): peas, beans, rye, lentils and the
# meals other than wheat meal (cwt); alpaca, vicuna, llama and flocks (lb); hewn timber, other sawn wood and staves
# (loads). 1924-25 (No. 83 against No. 70) agree, within the rounding of thousand lb and centals (`ROUNDING`).
C20_KNOWN = {"grain": -7692616, "wool": -8835533, "timber": -1183128}
ROUNDING = {"tea": 500, "wool": 550}


def load(path=READINGS):
    """{row: {year: value}} of the printed figures."""
    return values.load(path)


def check(rows):
    """Problems: a printed total that its parts do not make."""
    bad = []
    for total, parts in TOTALS.items():
        for y, t in sorted(rows.get(total, {}).items()):
            diff = sum(rows.get(p, {}).get(y, 0) for p in parts) - SLIPS.get((total, y), t)
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


def c20_goods(rows, ed, y):
    """The goods of one year from No. 70 or No. 83 (`ed`) in the old tables' units, raw cotton in centals: grain is
    wheat, barley, oats, maize, and wheat meal and flour; raw cotton includes linters and unmanufactured waste to 1919,
    from 1920 it is raw cotton without linters, with the waste added; wool is sheep's and lambs'; softwood (loads, to
    1934) is sawn softwood (with planed or dressed softwood and sleepers to 1914) and pit props."""
    p = C20[ed]
    n = lambda k: rows[p + k][y]
    out = {"grain": sum(n(k) for k in values.C20_GRAIN),
           "cotton": n("cotton") + rows.get(p + "cotton_waste", {}).get(y, 0) * WASTE,
           "wool": n("wool") * C20_LB[ed]["wool"], "sugar": n("sugar_refined") + n("sugar_raw"),
           "tea": n("tea") * C20_LB[ed]["tea"]}
    if y <= SOFTWOOD_END:
        out["softwood"] = sum(n(k) for k in SOFTWOOD)
    return out


def early_goods(rows, y):
    """The goods of one year from Nos. 16 and 18 (1854-1867), which give no grain: wheat, barley, oats, maize and
    wheat flour only. Timber is hewn (with teak, a row of its own in No. 18), sawn and staves, from the parts."""
    e = lambda k: rows.get(EARLY + k, {}).get(y, 0)
    return {"cotton": e("cotton_raw"), "wool": e("wool"), "sugar": e("sugar_refined") + e("sugar_rawtotal"),
            "tea": e("tea"), "timber": sum(e(k) for k in EARLY_WOOD)}


def goods(rows):
    """{year: {good: printed units}}: 1854-56 from Nos. 16 and 18 without grain and timber, 1857-67 from No. 19;
    1897-98 from No. 59, the later edition (as for the values); 1912-23 from No. 70, 1924-38 from No. 83; 1911 from
    No. 59, with No. 70's softwood."""
    out = {y: {k: v for k, v in early_goods(rows, y).items() if k != "timber"}
           for y in rows.get(EARLY + "tea", {}) if y not in rows["q_corn_total"]}
    out.update({y: old_goods(rows, y) for y in rows["q_corn_total"]})
    out.update({y: new_goods(rows, y) for y in rows["q59_cotton_raw"]})
    c20 = {y: c20_goods(rows, 70, y) for y in rows.get("q70_tea", {})}
    c20.update({y: c20_goods(rows, 83, y) for y in rows.get("q83_tea", {})})
    if 1911 in c20:
        out[1911]["softwood"] = c20.pop(1911)["softwood"]
    out.update(c20)
    return dict(sorted(out.items()))


def price_goods(rows):
    """The quantities for the price index: to 1867 those of the values' editions (Nos. 16 and 18), with No. 19's
    grain, which they do not give; later as `goods`."""
    out = goods(rows)
    for y in rows.get(EARLY + "tea", {}):
        out[y] = early_goods(rows, y) | {k: v for k, v in out[y].items() if k == "grain"}
    return out


def early_overlap(rows):
    """Years given by No. 18 and No. 19 where they differ other than in timber or by more than COTTON_GAP in raw
    cotton; and {year: No. 19 less No. 18's timber}."""
    bad, timber = {}, {}
    for y in sorted(set(rows.get(EARLY + "tea", {})) & set(rows["q_corn_total"])):
        a, b = early_goods(rows, y), old_goods(rows, y)
        timber[y] = b["timber"] - a["timber"]
        d = {k: b[k] - a[k] for k in a if k != "timber" and b[k] != a[k]}
        if set(d) - {"cotton"} or abs(d.get("cotton", 0)) > COTTON_GAP * a["cotton"]:
            bad[y] = d
    return bad, timber


def overlap(rows):
    """Years given by No. 46 and No. 59 whose differences (No. 59 - No. 46) are not the known ones."""
    out = {}
    for y in sorted(set(rows["q_corn_total"]) & set(rows["q59_cotton_raw"])):
        a, b = old_goods(rows, y), new_goods(rows, y)
        d = {k: b[k] - v for k, v in a.items() if b[k] != v}
        if d != KNOWN.get(y, {}):
            out[y] = d
    return out


def c20_overlap(rows):
    """Years given by two editions whose differences are not the known ones (beyond `ROUNDING`): 1911, No. 70 less
    No. 59 on the old definitions, and 1924-25, No. 83 less No. 70."""
    pairs = {}
    if "q70_tea" in rows:
        new = c20_goods(rows, 70, 1911)
        new["timber"] = new.pop("softwood")
        pairs[1911] = (new_goods(rows, 1911), new, C20_KNOWN)
    pairs.update({y: (c20_goods(rows, 70, y), c20_goods(rows, 83, y), {})
                  for y in set(rows.get("q70_tea", {})) & set(rows.get("q83_tea", {}))})
    out = {}
    for y, (a, b, known) in sorted(pairs.items()):
        d = {k: b[k] - v for k, v in a.items() if abs(b[k] - v - known.get(k, 0)) > ROUNDING.get(k, 0)}
        if d:
            out[y] = d
    return out


def softwood_values(vrows):
    """{year: £} of the softwood rows in the tables of values (Nos. 70 and 83, as `goods`), 1911-1934."""
    ed = lambda y: 70 if y < 1924 else 83
    return {y: sum(vrows[f"n{ed(y)}_{k}"][y] for k in SOFTWOOD) for y in range(1911, SOFTWOOD_END + 1)}


def tons(good, y, q):
    """Thousand tons (timber, softwood: million loads) from the printed quantity."""
    if good in LOADS:
        return q / 1e6
    lb = q * (CENTAL if good == "cotton" and y >= CENTALS else UNIT[good])
    return lb / 2240 / 1e3


def series(by_year, by_value, by_price=None):
    """{series id: [[year, value]]}: weights (thousand tons; timber million loads) and the average value per unit as
    an index, BASE = 100 (value and quantity in the same rows; quantities `by_price`, default `by_year`). Timber's
    index goes on with softwood's from its first year, linked there."""
    keys = GOODS + ("softwood",)
    weigh = lambda q: {g: {y: tons(g, y, v[g]) for y, v in q.items() if g in v} for g in keys}
    w, wp = weigh(by_year), weigh(by_price or by_year)
    out = {f"{PREFIX}{g}_uk": [[y, round(x, 2 if g in LOADS else 1)] for y, x in w[g].items()] for g in keys if w[g]}
    for g in GOODS:
        unit = {y: by_value[y][g] / x for y, x in wp[g].items()}
        soft = {y: by_value[y]["softwood"] / x for y, x in wp["softwood"].items()} if g == "timber" else {}
        if soft:
            link = unit[min(soft)] / soft[min(soft)]
            unit.update({y: u * link for y, u in soft.items() if y not in unit})
        out[f"{PREFIX}{g}_price_uk"] = [[y, round(u / unit[BASE] * 100, 1)] for y, u in unit.items()]
    return out


COMMON = (
    "from the Board of Trade's Statistical Abstracts, read from the page images of Nos. 16, 18, 19, 30, 45, 46, 59, 70 "
    "and 83 (and No. 62 for 1904's grain; edition, page and table per figure in the data file). The printed totals "
    "were checked against their parts, and every figure was found printed the same in another edition or read again "
    "on an enlarged crop. Where No. 59 (the Board's new classification) and No. 46 both give a year, 1897 and 1898, "
    "they agree except as stated; No. 59 is used for them, as for the values. From 1912 the goods are those of the "
    "classification of 1920 (Nos. 70 and 83, which agree for 1924-25 within No. 83's rounding to thousand lb); 1911, "
    "given by Nos. 59 and 70, is taken from No. 59; the breaks between them are stated here. From April 1923 the imports are "
    "those of Great Britain and Northern Ireland, with their trade with the Irish Free State.")
EARLY_NOTE = (
    " Nos. 16 and 18 (1854-56 here) print only wheat, barley, oats, maize and wheat flour, not the other kinds of corn "
    "and meal ({other:.1f}% of the total in {y57}), so grain and flour begins in 1857 with No. 19's full table; No. 19's 1868 "
    "equals No. 30's in every row.")
FOOD_NOTE = (
    "The weight of the grain and flour, sugar and tea brought into the United Kingdom each year, in thousand tons "
    "(the Abstract gives hundredweights and pounds), " + COMMON + EARLY_NOTE + " Grain and flour is the same as in "
    "\"Food imports\": wheat, barley, oats, maize, peas, beans, rye (and lentils from 1902), wheat flour and other "
    "meal, without rice; No. 59 counts lentils with seeds until April 1902 (0.17 million cwt in 1897). Sugar is "
    "refined and raw sugar, without molasses and glucose; Nos. 16 and 18 give the same sugar and tea as No. 19 "
    "for 1857-67. From 1912 grain and flour is wheat, barley, oats, maize, and wheat meal and flour: peas, beans, "
    "rye, lentils and the other meals are no longer shown ({gdrop:.1f}% of 1911's grain and flour by weight). No. 83 "
    "gives tea in thousand lb. Grain and flour was {g0:,.0f} thousand tons in {yg0}, {g13:,.0f} in 1913, {g1:,.0f} in "
    "{y1} (most: {gmax:,.0f} in {ygmax}); sugar {s0:,.0f} in {y0}, {s13:,.0f} in 1913 and {s1:,.0f}; tea {t0:,.0f}, "
    "{t13:,.0f} and {t1:,.0f}. Quantities, not values: see \"Food import prices\" for what each cost.")
MATERIALS_NOTE = (
    "The weight of the raw cotton and wool brought into the United Kingdom each year, in thousand tons (the "
    "Abstract gives hundredweights of cotton, from 1911 centals of 100 lb, and pounds of wool, in Nos. 70 and 83 "
    "centals and thousand lb), " + COMMON + " Wool is "
    "sheep's and lambs' wool with alpaca, vicuna and llama, and from 1883 \"other kinds and flocks\" (No. 44 "
    "gives 1882 so as 490.1 million lb, No. 30, used here, 489.0 million), not goats' hair or mohair; No. 59 (and "
    "No. 48) give 1898's sheep's wool 5.26 million lb above No. 46. 1854-56 are from Nos. 16 and 18, which give the "
    "same wool as No. 19 for 1857-67 and raw cotton up to {cgap:.2f}% below it. From 1912 wool is sheep's and "
    "lambs' wool alone (alpaca, vicuna, llama and flocks were {wdrop:.1f}% of 1911's wool), with noils until 1919. "
    "Raw cotton includes linters and unmanufactured waste to 1919; from 1920 it is raw cotton without linters, with "
    "the waste added (in cwt: No. 70 heads the waste row \"centals of 100 lbs.\", Nos. 73-83 \"cwts.\" for the same "
    "figures). Raw cotton was {c0:,.0f} thousand tons in {y0}, {c13:,.0f} in 1913, {c1:,.0f} in {y1} (most: "
    "{cmax:,.0f} in {ycmax}); wool {w0:,.0f}, {w13:,.0f} and {w1:,.0f} (most: {wmax:,.0f} in {ywmax}).")
TIMBER_NOTE = (
    "The timber brought into the United Kingdom each year, in million loads (the Abstract's measure), " + COMMON
    + " Timber is hewn (with pit props), sawn or split, and staves, as in \"Timber imports\"; mahogany and the other "
    "furniture woods, counted in tons, are left out. It begins in 1857 with No. 19: No. 18 (with No. 16, the only "
    "tables for 1854-56) gives {kgap0:.1f}-{kgap1:.1f}% less timber than No. 19 for each year 1857-67 (mostly "
    "sawn or split; staves are the same); the Abstract does not say why. Timber was {k0:,.2f} million loads in "
    "{yk0}, {k1:,.2f} in {yk1} (most: {kmax:,.2f} in {ykmax}). From 1912 (the classification of 1920) the Abstract "
    "gives quantities only of sawn softwood and pit props; hewn timber, the other sawn wood, staves and the furniture "
    "woods are given by value alone. They are the second line, from 1911 ({o11:,.2f} million loads, against "
    "{k1:,.2f} for all timber in No. 59) to {yo1}: sawn softwood includes planed or dressed softwood and sleepers to "
    "1914, and from 1915 they are counted elsewhere (No. 83 gives planed softwood as a row of its own from 1924, "
    "{pl24:,.2f} million loads that year, not added here). The line ends in {yo1}: from 1935 pit props leave out other pitwood, and from "
    "1936 the Abstract counts softwood in standards of 165 cubic feet and pit props in fathoms of 216 cubic feet, "
    "without saying how many loads they make. Sawn softwood and pit props were {o13:,.2f} million loads in 1913, "
    "{omin:,.2f} in {yomin} (the fewest) and {o1:,.2f} in {yo1}.")
PRICE_NOTE = (
    "The average value of a unit of each import (the value in \"{graph}\" divided by the quantity in the same rows "
    "of the Abstract's tables), as an index with {base} = 100. To 1870 the values are computed from average prices, "
    "from 1871 declared by the importers; an average over many kinds and qualities moves when the mix changes, so it "
    "is a rough guide to prices. To 1867 the quantities are those of the values' own editions, Nos. 16 and 18 "
    "(grain from No. 19, from 1857: they give no other kinds of corn); No. 16 gives no quantity of teak, which its "
    "timber values for 1854-55 include. {text} The quantities are " + COMMON)
FOOD_PRICES = ("Grain and flour stood at {g0:.0f} in {yg0}, {gmin:.0f} in {ygmin} (the lowest) and {g1:.0f} in {y1}; "
               "sugar at {s0:.0f} in {y0}, {smin:.0f} (in {ysmin}) and {s1:.0f}; tea at {t0:.0f}, {tmin:.0f} (in "
               "{ytmin}) and {t1:.0f}. From 1912 grain and flour leaves out peas, beans, rye, lentils and the "
               "meals other than wheat meal; on that definition its value per cwt in 1911 differs by {grain11:+.1f}%.")
MATERIAL_PRICES = ("Raw cotton stood at {c0:.0f} in {y0}, {cmin:.0f} in {ycmin} (the lowest) and {c1:.0f} in {y1}; "
                   "wool at {w0:.0f}, {wmin:.0f} (in {ywmin}) and {w1:.0f}; timber at {k0:.0f}, {kmin:.0f} (in "
                   "{ykmin}) and {k1:.0f} in {yk1}. From 1912 timber is sawn softwood and pit props alone (see "
                   "\"Timber imported\"), linked at 1911, when their value per load was {soft11:.0f}% of all timber's; "
                   "it ends in {yk1}.")


def _fields(v, y1, suffix=""):
    """The notes' fields of each good (letters gcwstk, o for softwood): first year and value, 1913, last, highest and
    lowest."""
    f = {"y1": y1}
    for x, k in zip(GOODS + ("softwood",), "gcwstko"):
        d = v.get(x + suffix)
        if not d:
            continue
        hi, lo, first, last = max(d, key=d.get), min(d, key=d.get), min(d), max(d)
        f.update({k + "0": d[first], f"y{k}0": first, k + "13": d.get(1913), k + "1": d[last], f"y{k}1": last,
                  k + "max": d[hi], f"y{k}max": hi, k + "min": d[lo], f"y{k}min": lo})
    f["y0"] = f["yc0"]
    return f


def prices(v, y1, title, region, links):
    """The two graphs of the price index: food (grain, sugar, tea) and raw materials (cotton, wool, timber); `links`:
    the 1911 comparisons of the definitions (soft11, grain11)."""
    unit, src = f"index, {BASE} = 100", SOURCES + ["stat_abstract_imports_uk"]
    f = _fields(v, y1, "_price") | links
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
    bad, timber = early_overlap(rows)
    if bad:
        raise ValueError(f"Nos. 18 and 19 differ: {bad}")
    diff = c20_overlap(rows)
    if diff:
        raise ValueError(f"Nos. 59, 70 and 83 differ: {diff}")
    by_year = goods(rows)
    for g in GOODS + ("softwood",):
        ys = [y for y, v in by_year.items() if g in v]
        if ys != list(range(min(ys), max(ys) + 1)):
            raise ValueError(f"years missing in {g}")
    vrows = values.load()
    by_value = values.goods(vrows)
    for y, x in softwood_values(vrows).items():
        by_value[y]["softwood"] = x
    pts = series(by_year, by_value, price_goods(rows))
    for sid, p in pts.items():
        _csv(sid, p)
    v = {k[len(PREFIX):-3]: dict(p) for k, p in pts.items()}
    y0, y1 = min(by_year), max(by_year)
    f = _fields(v, y1)
    early = lambda y: early_goods(rows, y)
    gap = [timber[y] / early(y)["timber"] * 100 for y in timber]
    cgap = max(abs(old_goods(rows, y)["cotton"] - early(y)["cotton"]) / early(y)["cotton"] * 100 for y in timber)
    y57 = min(timber)
    other = (rows["q_corn_other"][y57] + rows["q_corn_flourother"][y57]) / rows["q_corn_total"][y57] * 100
    old11, new11 = by_year[1911], c20_goods(rows, 70, 1911)
    drop = lambda g: -C20_KNOWN[g] / old11[g] * 100
    per = lambda vals, qty, g: vals[g] / qty[g]
    v11 = values.c20_goods(vrows, 70, 1911)
    links = {"soft11": per(by_value[1911], old11, "softwood") / per(by_value[1911], old11, "timber") * 100,
             "grain11": (per(v11, new11, "grain") / per(by_value[1911], old11, "grain") - 1) * 100}
    title = f"{y0}-{y1}"
    region = "United Kingdom (all Ireland to March 1923)"
    kt = "thousand tons a year"
    out = [
        _row(PREFIX + "grain_uk", f"Food imports by weight, {title}", "Grain and flour", kt, SOURCES, region,
             FOOD_NOTE.format(other=other, y57=y57, gdrop=drop("grain"), **f), [PREFIX + "sugar_uk", PREFIX + "tea_uk"], unit="kt"),
        _row(PREFIX + "sugar_uk", "Sugar imported", "Sugar", kt, SOURCES, region, unit="kt"),
        _row(PREFIX + "tea_uk", "Tea imported", "Tea", kt, SOURCES, region, unit="kt"),
        _row(PREFIX + "cotton_uk", f"Raw cotton and wool imported by weight, {title}", "Raw cotton", kt, SOURCES,
             region, MATERIALS_NOTE.format(cgap=cgap, wdrop=drop("wool"), **f), [PREFIX + "wool_uk"], unit="kt"),
        _row(PREFIX + "wool_uk", "Wool imported", "Wool", kt, SOURCES, region, unit="kt"),
        _row(PREFIX + "timber_uk", f"Timber imported, {f['yk0']}-{f['yo1']}", "Timber", "million loads a year",
             SOURCES, region, TIMBER_NOTE.format(kgap0=min(gap), kgap1=max(gap), o11=by_year[1911]["softwood"] / 1e6,
                                                 pl24=rows["q83_wood_planed"][1924] / 1e6, **f),
             [PREFIX + "softwood_uk"], unit="m loads"),
        _row(PREFIX + "softwood_uk", "Sawn softwood and pit props imported", "Sawn softwood and pit props",
             "million loads a year", SOURCES, region, unit="m loads"),
    ] + prices(v, y1, title, region, links)
    for r in out:
        r["zero"] = True
    path = DATA.parent / "series.json"
    keep = [x for x in json.loads(path.read_text()) if not x["id"].startswith(PREFIX)]
    path.write_text(json.dumps(keep + out, ensure_ascii=False, indent=1))
    g, c, gp = v["grain"], v["cotton"], v["grain_price"]
    log(f"{len(by_year)} years {y0}-{y1} (grain and timber from {min(g)}), totals checked; grain {g[min(g)]:,.0f} -> "
        f"{g[y1]:,.0f}, raw cotton {c[y0]:,.0f} -> {c[y1]:,.0f} thousand tons; No. 19 above No. 18's timber by "
        f"{min(gap):.1f}-{max(gap):.1f}%; grain price index {gp[min(gp)]:.0f} -> {gp[y1]:.0f} ({BASE} = 100)")


def run(log=print):
    write(load(), log)


if __name__ == "__main__":
    run(lambda m: print(m, file=sys.stderr, flush=True))
