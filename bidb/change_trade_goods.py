"""The main exports of United Kingdom produce by value, 1868-1911, for "Change over time" (roadmap C5b2b1).

The Board of Trade's Statistical Abstract prints the declared value of each principal article of British (and Irish)
produce exported. The rows for coal, cotton, wool, linen, iron and steel and machinery were read from the page images
of four editions (`data/curated/change/data/trade_goods_abstract_uk.csv`: one printed figure per line, with edition,
leaf, page and table): No. 30 (1868-1882), No. 45 (its 1883 column only), No. 46 (1884-1898) and No. 59 (1897-1911,
the Board's new classification). Where the table prints a total, the parts read are checked against it (`check`);
the figures without one were found printed the same in at least two other editions' OCR text when they were read.

    python -m bidb.change_trade_goods   → data/curated/change/data/sa_goods_*.csv + series.json entries
                                          (then python -m bidb.change_series)
"""
import csv
import json
import sys
from collections import defaultdict

from .change_firms import DATA
from .change_registers import _csv, _row
from . import change_trade_values

READINGS = DATA / "trade_goods_abstract_uk.csv"
SOURCES = ["stat_abstract_goods_uk"]
PREFIX = "sa_goods_"

# Printed totals and the rows that make them up, per edition's row names.
TOTALS = {
    "cotton_total": ["cotton_white", "cotton_printed", "cotton_mixed", "cotton_other", "cotton_pieces",
                     "cotton_unbl", "cotton_bl", "cotton_prdy", "cotton_dyed", "cotton_stockings", "cotton_thread",
                     "cotton_lace", "cotton_unenum"],
    "linen_total": ["linen_white", "linen_printed", "linen_sail", "linen_thread", "linen_other"],
    "wool_total": ["wool_cloths", "wool_flannels", "wool_blankets", "wool_stuffs", "wool_stuffs2", "wool_carpets",
                   "wool_hosiery", "wool_other"] + [f"wool_c{i}" for i in range(1, 13)],
    "iron_total": ["iron_old", "iron_pig", "iron_bar", "iron_rail", "iron_rails", "iron_railother", "iron_wire",
                   "iron_hoops", "iron_tinned", "iron_cast", "iron_steelunw", "iron_steelman", "iron_galv",
                   "iron_sheets", "iron_black", "iron_tubes", "iron_castother", "iron_steelingots",
                   "iron_steelsheets"],
    "coalt_total": ["coalt_coal", "coalt_coke", "coalt_fuel"],
    "macht_total": ["macht_steamagri", "macht_loco", "macht_steamother", "macht_electrical", "macht_sewing",
                    "macht_agri", "macht_mining", "macht_textile", "macht_other"],
    "cottont_total": ["cottont_piece", "cottont_other", "cottont_yarn", "cottont_waste"],
    "otex_total": ["otex_haber", "otex_juteyarn", "otex_jutepiece", "otex_juteother", "otex_linenyarn",
                   "otex_linenplain", "otex_linenprinted", "otex_linensail", "otex_linenthread", "otex_linenother"],
}
# Known differences between a printed total and its printed parts (parts - total), explained in the readings file.
KNOWN = {("wool_total", 1883): -10}
MACH_OLD = ["mach_steam", "mach_other", "mach_loco", "mach_steamagri", "mach_steamother", "mach_agri",
            "mach_textother", "mach_textile", "mach_mother"]
WOOL_NOT_MANUF = ["woolt_flocks", "woolt_waste", "woolt_tops", "woolt_yarn", "woolt_alpaca"]
LINEN_NEW = ["otex_linenplain", "otex_linenprinted", "otex_linensail", "otex_linenthread", "otex_linenother"]
GOODS = ("coal", "cotton_yarn", "cotton_manuf", "wool_yarn", "wool_manuf", "linen_yarn", "linen_manuf", "iron",
         "machinery")


def load(path=READINGS):
    """{row: {year: value}} of the printed figures (pounds)."""
    out = defaultdict(dict)
    with open(path, newline="") as f:
        for r in csv.DictReader(f):
            out[r["row"]][int(r["year"])] = int(r["value"])
    return out


def check(rows):
    """Problems: a printed total that its parts do not make (beyond the known differences). Years where only the
    total (and one part) was read, such as machinery 1905-1911, are not checked."""
    bad = []
    for total, parts in TOTALS.items():
        for y, t in sorted(rows.get(total, {}).items()):
            if sum(y in rows.get(p, {}) for p in parts) < 2:
                continue
            diff = sum(rows.get(p, {}).get(y, 0) for p in parts) - t
            if diff != KNOWN.get((total, y), 0):
                bad.append(f"{total} {y}: parts - total = {diff:,}")
    return bad


def _sum(rows, keys, y):
    vals = [rows[k][y] for k in keys if y in rows.get(k, {})]
    return sum(vals) if vals else None


def old_goods(rows, y):
    """The goods of one year from the tables of Nos. 30, 45 and 46 (1868-1898)."""
    g = rows.get
    yarn = g("cotton_yarn", {}).get(y) or g("cyarn_all", {}).get(y) or _sum(rows, ["cyarn_grey", "cyarn_bl"], y)
    return {"coal": rows["coal"][y], "cotton_yarn": yarn, "cotton_manuf": rows["cotton_total"][y],
            "wool_yarn": rows["wool_yarn"][y], "wool_manuf": rows["wool_total"][y],
            "linen_yarn": rows["linen_yarn"][y], "linen_manuf": rows["linen_total"][y],
            "iron": rows["iron_total"][y] - rows["iron_old"][y], "machinery": _sum(rows, MACH_OLD, y)}


def new_goods(rows, y):
    """The goods of one year from No. 59's classification (1897-1911), on the old tables' definitions."""
    return {"coal": rows["coalt_total"][y], "cotton_yarn": rows["cottont_yarn"][y],
            "cotton_manuf": rows["cottont_piece"][y] + rows["cottont_other"][y],
            "wool_yarn": rows["woolt_yarn"][y],
            "wool_manuf": rows["woolt_total"][y] - _sum(rows, WOOL_NOT_MANUF, y),
            "linen_yarn": rows["otex_linenyarn"][y], "linen_manuf": _sum(rows, LINEN_NEW, y),
            "iron": rows["ironm_total"][y], "machinery": rows["macht_total"][y] - rows["macht_sewing"][y]}


def goods(rows):
    """{year: {good: pounds}}; where two editions give a year, the later one (No. 59) is used."""
    out = {y: old_goods(rows, y) for y in rows["coal"]}
    out.update({y: new_goods(rows, y) for y in rows["coalt_total"]})
    return dict(sorted(out.items()))


def overlap(rows):
    """Years given by both the old and the new tables, with the goods that differ (should be none)."""
    both = sorted(set(rows["coal"]) & set(rows["coalt_total"]))
    return {y: {k: (a, b) for k, a in old_goods(rows, y).items() if a != (b := new_goods(rows, y)[k])}
            for y in both}


def series(by_year, all_exports):
    """{series id: [[year, value]]}: £ million (two decimals) and shares of all UK produce exported (%)."""
    m = lambda f: [[y, round(f(v) / 1e6, 2)] for y, v in by_year.items()]
    pct = lambda f: [[y, round(f(v) / all_exports[y] * 100, 2)] for y, v in by_year.items()]
    cotton = lambda v: v["cotton_yarn"] + v["cotton_manuf"]
    wool = lambda v: v["wool_yarn"] + v["wool_manuf"]
    linen = lambda v: v["linen_yarn"] + v["linen_manuf"]
    textiles = lambda v: cotton(v) + wool(v) + linen(v)
    metal = lambda v: v["coal"] + v["iron"] + v["machinery"]
    return {PREFIX + "cotton_uk": m(cotton), PREFIX + "wool_uk": m(wool), PREFIX + "linen_uk": m(linen),
            PREFIX + "coal_uk": m(lambda v: v["coal"]), PREFIX + "iron_uk": m(lambda v: v["iron"]),
            PREFIX + "machinery_uk": m(lambda v: v["machinery"]),
            PREFIX + "textiles_share_uk": pct(textiles), PREFIX + "cotton_share_uk": pct(cotton),
            PREFIX + "metal_share_uk": pct(metal)}


TEXTILES_NOTE = (
    "The value of the cotton, woollen and worsted, and linen goods made in the United Kingdom and sent abroad each "
    "year, at the prices of the time (\"declared value\", as loaded on board), yarn and manufactures together, from "
    "the Board of Trade's Statistical Abstracts, read from the page images of Nos. 30, 45, 46 and 59 (edition, page "
    "and table per figure in the data file). Every total the tables print was checked against its printed parts; "
    "the figures without a printed total were found printed the same in at least two other editions. The "
    "sub-headings changed over the years but the totals are the Abstract's own; from 1897 the Board's new "
    "classification was brought back to the old totals (they agree exactly for 1897 and 1898, given in both "
    "tables): waste from worked cotton is counted with cotton manufactures to 1907 and left out from 1908, and "
    "tops, noils, waste, flocks and alpaca and mohair yarn are left out of wool. Cotton was {c0:,.1f} million in "
    "{y0}, {cmin:,.1f} million in {ymin} (its lowest) and {c1:,.1f} million in {y1}; woollen and worsted goods "
    "{w0:,.1f}, {wmax:,.1f} (in {ywmax}) and {w1:,.1f} million; linen {l0:,.1f} and {l1:,.1f} million. Jute, silk "
    "and apparel are not included.")
METALS_NOTE = (
    "The value of the coal, iron and steel, and machinery made in the United Kingdom and sent abroad each year, at "
    "the prices of the time, from the same Statistical Abstract tables as \"Textile exports\". Coal is coal, cinders "
    "(coke) and manufactured fuel, not bunker coal for ships and not the products of coal; iron and steel leaves out "
    "old iron for re-manufacture, though old rails are counted from 1907; machinery leaves out sewing machines, "
    "which the old tables did not count as machinery (electrical machinery, shown on its own from 1903, was "
    "counted with other machinery before). "
    "Coal was {k0:,.1f} million in {y0}, {kmax:,.1f} million in {ykmax} and {k1:,.1f} million in {y1}; iron and steel "
    "{i0:,.1f}, {imax:,.1f} (in {yimax}) and {i1:,.1f} million; machinery {m0:,.1f} and {m1:,.1f} million. New "
    "ships were not recorded as exports before 1899 and are not included.")
SHARE_NOTE = (
    "The main goods as a share of all exports of United Kingdom produce (\"UK exports of UK produce\", the "
    "Abstract's summary table, which counts the parcel post from 1885: 2.1 of 233.4 million in 1898). Cotton, wool and "
    "linen together were {t0:.1f}% in {y0} and {t1:.1f}% in {y1}; cotton alone {c0:.1f}% and {c1:.1f}%; coal, iron "
    "and steel and machinery together {k0:.1f}% and {k1:.1f}%. Values at the prices of the time: a falling share "
    "can mean lower prices as well as smaller quantities.")


def write(rows, log=print):
    bad = check(rows)
    if bad:
        raise ValueError("; ".join(bad))
    diff = {y: d for y, d in overlap(rows).items() if d}
    if diff:
        raise ValueError(f"old and new tables differ: {diff}")
    by_year = goods(rows)
    if list(by_year) != list(range(min(by_year), max(by_year) + 1)):
        raise ValueError("years missing")
    uk = dict(map(tuple, change_trade_values.series(change_trade_values.load())["sa_trade_exports_uk"]))
    pts = series(by_year, {y: v * 1e6 for y, v in uk.items()})
    for sid, p in pts.items():
        _csv(sid, p)
    v = {k[len(PREFIX):-3]: dict(p) for k, p in pts.items()}
    c, w, l, k, i, m = (v[x] for x in ("cotton", "wool", "linen", "coal", "iron", "machinery"))
    y0, y1 = min(c), max(c)
    arg = lambda d, f: f(d, key=d.get)
    ymin, ywmax, ykmax, yimax = arg(c, min), arg(w, max), arg(k, max), arg(i, max)
    gbp = "million pounds (prices of the time)"
    region = "United Kingdom (with all Ireland)"
    t, cs, ms = v["textiles_share"], v["cotton_share"], v["metal_share"]
    out = [
        _row(PREFIX + "cotton_uk", "Textile exports, 1868-1911", "Cotton yarn and manufactures", gbp, SOURCES, region,
             TEXTILES_NOTE.format(c0=c[y0], y0=y0, cmin=c[ymin], ymin=ymin, c1=c[y1], y1=y1, w0=w[y0],
                                  wmax=w[ywmax], ywmax=ywmax, w1=w[y1], l0=l[y0], l1=l[y1]),
             [PREFIX + "wool_uk", PREFIX + "linen_uk"], unit="£m"),
        _row(PREFIX + "wool_uk", "Woollen exports", "Woollen and worsted yarn and manufactures", gbp, SOURCES, region,
             unit="£m"),
        _row(PREFIX + "linen_uk", "Linen exports", "Linen yarn and manufactures", gbp, SOURCES, region, unit="£m"),
        _row(PREFIX + "coal_uk", "Coal, iron and machinery exports, 1868-1911", "Coal, coke and manufactured fuel",
             gbp, SOURCES, region,
             METALS_NOTE.format(k0=k[y0], y0=y0, kmax=k[ykmax], ykmax=ykmax, k1=k[y1], y1=y1, i0=i[y0],
                                imax=i[yimax], yimax=yimax, i1=i[y1], m0=m[y0], m1=m[y1]),
             [PREFIX + "iron_uk", PREFIX + "machinery_uk"], unit="£m"),
        _row(PREFIX + "iron_uk", "Iron and steel exports", "Iron and steel", gbp, SOURCES, region, unit="£m"),
        _row(PREFIX + "machinery_uk", "Machinery exports", "Machinery", gbp, SOURCES, region, unit="£m"),
        _row(PREFIX + "textiles_share_uk", "Main exports, share of all UK exports, 1868-1911",
             "Cotton, wool and linen", "% of exports of UK produce", SOURCES + ["stat_abstract_trade_uk"], region,
             SHARE_NOTE.format(t0=t[y0], y0=y0, t1=t[y1], y1=y1, c0=cs[y0], c1=cs[y1], k0=ms[y0], k1=ms[y1]),
             [PREFIX + "cotton_share_uk", PREFIX + "metal_share_uk"], unit="%"),
        _row(PREFIX + "cotton_share_uk", "Cotton, share of exports", "Cotton", "% of exports of UK produce",
             SOURCES, region, unit="%"),
        _row(PREFIX + "metal_share_uk", "Coal, iron and machinery, share of exports", "Coal, iron and machinery",
             "% of exports of UK produce", SOURCES, region, unit="%"),
    ]
    for r in out:
        r["zero"] = True
    path = DATA.parent / "series.json"
    keep = [s for s in json.loads(path.read_text()) if not s["id"].startswith(PREFIX)]
    path.write_text(json.dumps(keep + out, ensure_ascii=False, indent=1))
    log(f"{len(by_year)} years {y0}-{y1}, every printed total checked; cotton {c[y0]:,.1f} -> {c[y1]:,.1f}, "
        f"coal {k[y0]:,.1f} -> {k[y1]:,.1f} million; textiles {t[y0]:.1f}% -> {t[y1]:.1f}% of exports")


def run(log=print):
    write(load(), log)


if __name__ == "__main__":
    run(lambda m: print(m, file=sys.stderr, flush=True))
