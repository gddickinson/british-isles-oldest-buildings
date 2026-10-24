"""The main imports by value, 1854-1911, for "Change over time" (roadmap C5b2b3a).

The Board of Trade's Statistical Abstract prints the value of each principal article imported. The rows for corn
(grain and flour), raw cotton, wool, sugar, tea and timber were read from the page images of six editions
(`data/curated/change/data/trade_imports_abstract_uk.csv`: one printed figure per line, with edition, leaf, page and
table), the editions used for the summary table (`change_trade_values`), so the shares use the same totals: No. 16
(1854-1855), No. 18 (1856-1867), No. 30 (1868-1882), No. 45 (its 1883 column), No. 46 (1884-1898) and No. 59
(1897-1911, the Board's new classification; rows `n59_*`, its 1904 grain column, lost in the binding, from No. 62).
Every printed total is checked against its parts (`check`: the total of corn, Nos. 16 and 18's raw sugar and timber,
No. 59's grain and flour, wood and timber, and wool); the figures with no printed total were found printed the same
in another edition's OCR text, or read again from an enlarged crop. `new_goods` brings No. 59's rows back to the old
tables' definitions; 1897-98, given in both, differ only as `KNOWN` says (`overlap`).

    python -m bidb.change_trade_imports   → data/curated/change/data/sa_imports_*.csv + series.json entries
                                            (then python -m bidb.change_series)
"""
import csv
import json
import sys
from collections import defaultdict

from .change_firms import DATA
from .change_registers import _csv, _row
from . import change_trade_values

READINGS = DATA / "trade_imports_abstract_uk.csv"
SOURCES = ["stat_abstract_imports_uk"]
PREFIX = "sa_imports_"
CORN = ["corn_wheat", "corn_barley", "corn_oats", "corn_maize", "corn_other", "corn_flourwheat", "corn_flourother"]
# No. 59's grain: the old "Total of Corn" is everything but rice, rice meal and other farinaceous substances.
GRAIN59 = ["n59_g_" + k for k in ("wheat", "barley", "oats", "maize", "peas", "beans", "lentils", "rye", "wheatmeal",
                                  "oatmeal", "maizemeal", "mealother")]
TOTALS = {
    "corn_total": CORN,
    "sugar_rawtotal": ["sugar_rawbp", "sugar_rawforeign"],
    "wood_hewntotal": ["wood_hewnforeign", "wood_hewnbp"],
    "wood_sawntotal": ["wood_sawnforeign", "wood_sawnbp"],
    "n59_g_total": GRAIN59 + ["n59_g_rice", "n59_g_ricemeal", "n59_g_farin"],
    "n59_wood_total": ["n59_wood_" + k for k in ("pitprops", "hewnfir", "hewnoak", "hewnteak", "hewnother", "sawnfir",
                                                 "sawnother", "staves", "mahogany", "furnother")],
    "n59_wool_total": ["n59_wool_" + k for k in ("alpaca", "camel", "mohair", "sheep", "flocks", "rags")],
}
# 1897-98 in No. 59 less No. 46 (pounds): lentils, counted with seeds in No. 59 until 15 April 1902 and with "other
# kinds" of corn before; sheep's wool of 1898, revised.
KNOWN = {1897: {"grain": -46919}, 1898: {"grain": -57855, "wool": 149713}}
GOODS = ("grain", "cotton", "wool", "sugar", "tea", "timber")


def load(path=READINGS):
    """{row: {year: value}} of the printed figures (pounds)."""
    out = defaultdict(dict)
    with open(path, newline="") as f:
        for r in csv.DictReader(f):
            out[r["row"]][int(r["year"])] = int(r["value"])
    return out


def check(rows):
    """Problems: a printed total that its parts do not make."""
    bad = []
    for total, parts in TOTALS.items():
        for y, t in sorted(rows.get(total, {}).items()):
            diff = sum(rows.get(p, {}).get(y, 0) for p in parts) - t
            if diff:
                bad.append(f"{total} {y}: parts - total = {diff:,}")
    return bad


def _sum(rows, keys, y):
    vals = [rows[k][y] for k in keys if y in rows.get(k, {})]
    return sum(vals) if vals else None


def _first(rows, keys, y):
    """The first of `keys` printed for year `y` (each edition names its rows differently)."""
    return next(rows[k][y] for k in keys if y in rows.get(k, {}))


def old_goods(rows, y):
    """The goods of one year from the tables of Nos. 16, 18, 30, 45 and 46 (1854-1898)."""
    s = lambda keys: _sum(rows, keys, y)
    hewn = rows.get("wood_hewn", {}).get(y) or s(["wood_hewntotal", "wood_teak"]) or s(
        ["wood_hewnfir", "wood_hewnoak", "wood_hewnteak", "wood_hewnother"])
    sawn = rows.get("wood_sawn", {}).get(y) or s(["wood_sawntotal"]) or s(["wood_sawnfir", "wood_sawnother"])
    return {"grain": rows["corn_total"][y], "cotton": rows["cotton_raw"][y],
            "wool": rows.get("wool_all", {}).get(y) or s(["wool_sheep", "wool_other"]),
            "sugar": (rows.get("sugar_refined", {}).get(y) or s(["sugar_reflumps", "sugar_refother"]))
            + _first(rows, ["sugar_raw", "sugar_rawtotal"], y) if y not in rows.get("sugar_beet", {})
            else s(["sugar_reflumps", "sugar_refother", "sugar_beet", "sugar_cane"]),
            "tea": rows["tea"][y], "timber": hewn + sawn + rows["wood_staves"][y]}


def new_goods(rows, y):
    """The goods of one year from No. 59's classification (1897-1911), on the old tables' definitions: wool is
    sheep's and lambs', alpaca, vicuna and llama, and flocks and waste (not camels' hair, mohair or rags); timber
    leaves out mahogany and the other furniture woods."""
    n = lambda k: rows["n59_" + k][y]
    return {"grain": _sum(rows, GRAIN59, y), "cotton": n("cotton_raw"),
            "wool": n("wool_sheep") + n("wool_alpaca") + n("wool_flocks"),
            "sugar": n("sugar_refined") + n("sugar_beet") + n("sugar_cane"), "tea": n("tea"),
            "timber": n("wood_total") - n("wood_mahogany") - n("wood_furnother")}


def goods(rows):
    """{year: {good: pounds}}; No. 59 is used for 1897-98, given in both."""
    out = {y: old_goods(rows, y) for y in rows["corn_total"]}
    out.update({y: new_goods(rows, y) for y in rows["n59_cotton_raw"]})
    return dict(sorted(out.items()))


def overlap(rows):
    """Years given by both the old and the new tables whose differences (new - old) are not the known ones."""
    out = {}
    for y in sorted(set(rows["corn_total"]) & set(rows["n59_cotton_raw"])):
        a, b = old_goods(rows, y), new_goods(rows, y)
        d = {k: b[k] - v for k, v in a.items() if b[k] != v}
        if d != KNOWN.get(y, {}):
            out[y] = d
    return out


def series(by_year, all_imports):
    """{series id: [[year, value]]}: £ million (two decimals) and shares of all imports (%)."""
    m = lambda k: [[y, round(v[k] / 1e6, 2)] for y, v in by_year.items()]
    pct = lambda f: [[y, round(f(v) / all_imports[y] * 100, 2)] for y, v in by_year.items()]
    out = {f"{PREFIX}{k}_uk": m(k) for k in GOODS}
    out[PREFIX + "food_share_uk"] = pct(lambda v: v["grain"] + v["sugar"] + v["tea"])
    out[PREFIX + "materials_share_uk"] = pct(lambda v: v["cotton"] + v["wool"] + v["timber"])
    out[PREFIX + "grain_share_uk"] = pct(lambda v: v["grain"])
    return out


COMMON = (
    "from the Board of Trade's Statistical Abstracts, read from the page images of Nos. 16, 18, 30, 45, 46 and 59 "
    "(edition, page and table per figure in the data file). Imports are valued as they arrived (cost, insurance and "
    "freight); to 1870 the Abstract gives a value computed from average prices, from 1871 the value declared by the "
    "importers. Every total the tables print was checked against its printed parts, and the other figures were "
    "found printed the same in another edition. Where the Board's new classification of 1897 (No. 59) and the old "
    "tables (No. 46) both give a year, 1897 and 1898, they agree except as stated; No. 59 is used for them.")
FOOD_NOTE = (
    "The value of the grain and flour, sugar and tea brought into the United Kingdom each year, at the prices of the "
    "time, " + COMMON + " Grain and flour is the Abstract's \"Total of Corn\": wheat, barley, oats, maize, other "
    "kinds (peas, beans, rye, lentils), wheat flour and other meal, without rice; No. 59 counts lentils with seeds "
    "until 15 April 1902, so 1897-1901 lack them (0.05 million in 1897), and from 1902 its other meal includes sharps, "
    "middlings and some offals. Sugar is refined and raw (unrefined, cane and beet) sugar, without molasses and "
    "glucose. Grain and flour was {g0:,.1f} million in {y0}, {g67:,.1f} million in 1867, {gmax:,.1f} million in "
    "{ygmax} and {g1:,.1f} million in {y1}; sugar {s0:,.1f}, {smax:,.1f} (in {ysmax}) and {s1:,.1f} million; tea "
    "{t0:,.1f}, {tmax:,.1f} (in {ytmax}) and {t1:,.1f} million. Values at the prices of the time, not quantities.")
MATERIALS_NOTE = (
    "The value of the raw cotton, wool and timber brought into the United Kingdom each year, at the prices of the "
    "time, " + COMMON + " Wool is sheep's and lambs' wool with alpaca, vicuna and llama, and flocks (and waste) from "
    "1883 (about 0.06 million a year), not goats' hair or mohair; No. 59 revises 1898's sheep's wool by 0.15 million "
    "(23.59 against No. 46's 23.44 million). Timber is hewn (with teak and pit props), sawn or split, and staves, "
    "not mahogany or other furniture woods; for 1866-67 later editions (Nos. 19-22) give 0.03 million more hewn and "
    "about 0.33 million more sawn timber than No. 18, which is used, and No. 30's 1868 is 0.49 million above No. "
    "18's. Raw cotton was {c0:,.1f} million in {y0}, {c61:,.1f} million in 1861, {c64:,.1f} million in 1864 "
    "(the American Civil War was fought in 1861-65), {c85:,.1f} million in 1885 and {c1:,.1f} "
    "million in {y1} (highest {cmax:,.1f} million, in {ycmax}); wool {w0:,.1f}, {wmax:,.1f} (in {ywmax}) and {w1:,.1f} million; timber {k0:,.1f}, "
    "{kmax:,.1f} (in {ykmax}) and {k1:,.1f} million.")
SHARE_NOTE = (
    "The main imports as a share of all imports (the Abstract's summary table, as in \"Overseas trade at the prices "
    "of the time\"). Grain and flour, sugar and tea together were {f0:.1f}% of all imports in {y0}, {fmax:.1f}% in "
    "{yfmax} and {f1:.1f}% in {y1}; grain and flour alone {g0:.1f}%, {gmax:.1f}% (in {ygmax}) and {g1:.1f}%; raw "
    "cotton, wool and timber together {m0:.1f}%, {mmax:.1f}% (in {ymmax}) and {m1:.1f}%. Values at the prices of the "
    "time: a falling share can mean lower prices as well as smaller quantities.")


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
    imp = dict(map(tuple, change_trade_values.series(change_trade_values.load())["sa_trade_imports_uk"]))
    pts = series(by_year, {y: v * 1e6 for y, v in imp.items()})
    for sid, p in pts.items():
        _csv(sid, p)
    v = {k[len(PREFIX):-3]: dict(p) for k, p in pts.items()}
    y0, y1 = min(by_year), max(by_year)
    arg = lambda d, f: f(d, key=d.get)
    g, s, t, c, w, k = (v[x] for x in ("grain", "sugar", "tea", "cotton", "wool", "timber"))
    f, gs, ms = v["food_share"], v["grain_share"], v["materials_share"]
    ygmax, ysmax, ytmax, ycmax, ywmax, ykmax = (arg(d, max) for d in (g, s, t, c, w, k))
    yfmax, ygsmax, ymmax = arg(f, max), arg(gs, max), arg(ms, max)
    gbp = "million pounds (prices of the time)"
    region = "United Kingdom"
    title = f"{y0}-{y1}"
    out = [
        _row(PREFIX + "grain_uk", f"Food imports, {title}", "Grain and flour", gbp, SOURCES, region,
             FOOD_NOTE.format(g0=g[y0], y0=y0, g67=g[1867], gmax=g[ygmax], ygmax=ygmax, g1=g[y1], y1=y1, s0=s[y0],
                              smax=s[ysmax], ysmax=ysmax, s1=s[y1], t0=t[y0], tmax=t[ytmax], ytmax=ytmax, t1=t[y1]),
             [PREFIX + "sugar_uk", PREFIX + "tea_uk"], unit="£m"),
        _row(PREFIX + "sugar_uk", "Sugar imports", "Sugar", gbp, SOURCES, region, unit="£m"),
        _row(PREFIX + "tea_uk", "Tea imports", "Tea", gbp, SOURCES, region, unit="£m"),
        _row(PREFIX + "cotton_uk", f"Raw material imports, {title}", "Raw cotton", gbp, SOURCES, region,
             MATERIALS_NOTE.format(c0=c[y0], y0=y0, c61=c[1861], c64=c[1864], c85=c[1885], cmax=c[ycmax],
                                   ycmax=ycmax, c1=c[y1], y1=y1, w0=w[y0], wmax=w[ywmax], ywmax=ywmax, w1=w[y1],
                                   k0=k[y0], kmax=k[ykmax], ykmax=ykmax, k1=k[y1]),
             [PREFIX + "wool_uk", PREFIX + "timber_uk"], unit="£m"),
        _row(PREFIX + "wool_uk", "Wool imports", "Wool", gbp, SOURCES, region, unit="£m"),
        _row(PREFIX + "timber_uk", "Timber imports", "Timber", gbp, SOURCES, region, unit="£m"),
        _row(PREFIX + "food_share_uk", f"Main imports, share of all imports, {title}", "Grain and flour, sugar and tea",
             "% of all imports", SOURCES + ["stat_abstract_trade_uk"], region,
             SHARE_NOTE.format(f0=f[y0], y0=y0, fmax=f[yfmax], yfmax=yfmax, f1=f[y1], y1=y1, g0=gs[y0],
                               gmax=gs[ygsmax], ygmax=ygsmax, g1=gs[y1], m0=ms[y0], mmax=ms[ymmax], ymmax=ymmax,
                               m1=ms[y1]),
             [PREFIX + "grain_share_uk", PREFIX + "materials_share_uk"], unit="%"),
        _row(PREFIX + "grain_share_uk", "Grain and flour, share of imports", "Grain and flour", "% of all imports",
             SOURCES, region, unit="%"),
        _row(PREFIX + "materials_share_uk", "Raw cotton, wool and timber, share of imports",
             "Raw cotton, wool and timber", "% of all imports", SOURCES, region, unit="%"),
    ]
    for r in out:
        r["zero"] = True
    path = DATA.parent / "series.json"
    keep = [x for x in json.loads(path.read_text()) if not x["id"].startswith(PREFIX)]
    path.write_text(json.dumps(keep + out, ensure_ascii=False, indent=1))
    log(f"{len(by_year)} years {y0}-{y1}, every printed total checked; grain {g[y0]:,.1f} -> {g[y1]:,.1f}, "
        f"raw cotton {c[y0]:,.1f} -> {c[y1]:,.1f} million; food {f[y0]:.1f}% -> {f[y1]:.1f}% of imports")


def run(log=print):
    write(load(), log)


if __name__ == "__main__":
    run(lambda m: print(m, file=sys.stderr, flush=True))
