"""The main exports of United Kingdom produce by value, 1846-1938, for "Change over time" (roadmap C5b2b1, C5b2b2,
C5b2b3d).

The Board of Trade's Statistical Abstract prints the declared value of each principal article of British (and Irish)
produce exported. The rows for coal, cotton, wool, linen, iron and steel and machinery were read from the page images
of the editions (`data/curated/change/data/trade_goods_abstract_uk.csv`: one printed figure per line, with edition,
leaf, page and table): No. 8 (1846-1853, table 18, every figure but 1846's printed the same in No. 9; the total of
all exports from table 15), No. 16 (1854-1855), No. 18 (1856-1867), No. 30 (1868-1882), No. 45 (its 1883 column only),
No. 46 (1884-1898) and No. 59 (1897-1911, the Board's new classification). Nos. 16 and 18 count tin plates under tin,
not iron, so they are added to iron and steel (`old_goods`); No. 8 prints them in one line with tin and pewter
ware, and old iron inside wrought iron, so tin plates come from Nos. 10, 11 and 13 (from 1848) and old iron from
Nos. 11 and 13 (from 1849); before then No. 8's wider lines are used (`EARLY`). Where the table prints a total, the parts read are checked against it (`check`);
the figures without one were found printed the same in at least two other editions' OCR text when they were read.
Nos. 70 (1911-1925, table 212) and 83 (1924-1938, table 288) follow the classification of 1920 and print no totals
(rows `n70_*`, `n83_*`); every figure was found in another edition's OCR or, where none prints it (mostly 1937-38),
read again from an enlarged crop. `c20_goods` brings their rows back to the old totals; the years given by two
editions (1911, 1924-25) differ only as `C20_KNOWN` says.

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
    "cotton_total": ["cotton_white", "cotton_printed", "cotton_cambric", "cotton_mixed", "cotton_other", "cotton_pieces",
                     "cotton_unbl", "cotton_bl", "cotton_prdy", "cotton_dyed", "cotton_stockings", "cotton_thread",
                     "cotton_lace", "cotton_unenum"],
    "linen_total": ["linen_white", "linen_printed", "linen_sail", "linen_thread", "linen_other"],
    "wool_total": ["wool_cloths", "wool_flannels", "wool_blankets", "wool_stuffs", "wool_stuffs2", "wool_carpets",
                   "wool_hosiery", "wool_other"] + [f"wool_c{i}" for i in range(1, 13)],
    "iron_total": ["iron_old", "iron_wroughtall", "iron_pig", "iron_bar", "iron_rail", "iron_barrail", "iron_wrought",
                   "iron_hoopswrought", "iron_rails", "iron_railother", "iron_wire",
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
# No. 8 (1846-1853) gives old iron only inside wrought iron of all kinds, and tin plates in one line with tin and
# pewter ware; Nos. 10, 11 and 13 separate tin plates from 1848 (`tin_plates`) and Nos. 11 and 13 old iron from 1849
# (`iron_oldin`). Before then iron and steel keeps old iron and takes the wider tin line.
EARLY = 1849
MACH_OLD = ["mach_steam", "mach_other", "mach_loco", "mach_steamagri", "mach_steamother", "mach_agri",
            "mach_textother", "mach_textile", "mach_mother"]
WOOL_NOT_MANUF = ["woolt_flocks", "woolt_waste", "woolt_tops", "woolt_yarn", "woolt_alpaca"]
LINEN_NEW = ["otex_linenplain", "otex_linenprinted", "otex_linensail", "otex_linenthread", "otex_linenother"]
# Classification of 1920 (Nos. 70 and 83): hollow-ware, sewing machines and cotton waste in Class II (from 1920) left
# out, as before; wool hosiery, moved to apparel, added back; railway axles, tyres and wheels (iron and steel's
# railway material in No. 70, a vehicles row in No. 83) and rail locomotives (vehicles) counted as before.
C20_IRON = ["ir_pig", "ir_bariron", "ir_barsteel", "ir_bars", "ir_girders", "ir_plates", "ir_galv", "ir_tinned",
            "ir_tubes", "ir_rails", "ir_railother", "ir_wire", "ir_nails", "ir_other", "v_axles"]
C20_MACH = ["m_boilers", "m_elec", "m_tools", "m_mining", "m_prime", "m_ice", "m_primeother", "m_textile", "m_other",
            "v_loco"]
C20_COTTON = ["cp_grey", "cp_white", "cp_printflags", "cp_printother", "cp_printed", "cp_dyed", "cp_coloured",
              "c_flags", "c_lace", "c_thread", "c_other"]
C20_WOOL = ["wt_woolall", "wt_woolmixed", "wt_worstedall", "wt_worstedmixed", "w_carpets", "w_other", "wh_stock",
            "wh_other"]
# Years given by two editions (later - earlier, pounds), explained in the notes: 1911 No. 70 against No. 59 (cotton
# hosiery and gloves moved to apparel while waste from worked cotton is in other manufactures; flocks in other
# woollen manufactures; old rails left out of rails; road locomotives not shown), 1924-25 No. 83 against No. 70
# (part of other iron and steel moved, with boilers and boiler-house plant gathered under machinery).
C20_KNOWN = {1911: {"cotton_manuf": 841010, "wool_manuf": 8570, "iron": -2196, "machinery": -469774},
             1924: {"iron": -411689, "machinery": 1981217}, 1925: {"iron": -381646, "machinery": 1841590}}
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
    """The goods of one year from the tables of Nos. 8, 16, 18, 30, 45 and 46 (1846-1898); tin plates, counted under
    tin before 1868, are added to iron and steel."""
    g = rows.get
    old = g("iron_old", {}).get(y, g("iron_oldin", {}).get(y))
    if old is None and y >= EARLY:
        raise KeyError(f"old iron {y}")
    tin = g("tin_plates", {}).get(y, g("tin_pewter", {}).get(y, 0))
    yarn = g("cotton_yarn", {}).get(y) or g("cyarn_all", {}).get(y) or _sum(rows, ["cyarn_grey", "cyarn_bl"], y)
    return {"coal": rows["coal"][y], "cotton_yarn": yarn, "cotton_manuf": rows["cotton_total"][y],
            "wool_yarn": rows["wool_yarn"][y], "wool_manuf": rows["wool_total"][y],
            "linen_yarn": rows["linen_yarn"][y], "linen_manuf": rows["linen_total"][y],
            "iron": rows["iron_total"][y] - (old or 0) + tin,
            "machinery": _sum(rows, MACH_OLD, y)}


def new_goods(rows, y):
    """The goods of one year from No. 59's classification (1897-1911), on the old tables' definitions."""
    return {"coal": rows["coalt_total"][y], "cotton_yarn": rows["cottont_yarn"][y],
            "cotton_manuf": rows["cottont_piece"][y] + rows["cottont_other"][y],
            "wool_yarn": rows["woolt_yarn"][y],
            "wool_manuf": rows["woolt_total"][y] - _sum(rows, WOOL_NOT_MANUF, y),
            "linen_yarn": rows["otex_linenyarn"][y], "linen_manuf": _sum(rows, LINEN_NEW, y),
            "iron": rows["ironm_total"][y], "machinery": rows["macht_total"][y] - rows["macht_sewing"][y]}


def c20_goods(rows, ed, y):
    """The goods of one year from No. 70 or No. 83 (`ed`), on the old tables' definitions."""
    s = lambda keys: _sum(rows, [f"n{ed}_{k}" for k in keys], y)
    return {"coal": s(["coal", "coke", "fuel"]), "cotton_yarn": s(["cy_grey", "cy_bl"]), "cotton_manuf": s(C20_COTTON),
            "wool_yarn": s(["wy_woollen", "wy_worsted"]), "wool_manuf": s(C20_WOOL), "linen_yarn": s(["l_yarn"]),
            "linen_manuf": s(["l_piece", "l_other"]), "iron": s(C20_IRON), "machinery": s(C20_MACH)}


def goods(rows):
    """{year: {good: pounds}}; where two editions give a year, the later one is used (No. 59 for 1897-98, No. 83
    for 1924-25), except 1911, kept from No. 59 so that the break in definitions falls between 1911 and 1912."""
    out = {y: old_goods(rows, y) for y in rows["coal"]}
    out.update({y: new_goods(rows, y) for y in rows["coalt_total"]})
    out.update({y: c20_goods(rows, 70, y) for y in rows.get("n70_coal", {}) if y > 1911})
    out.update({y: c20_goods(rows, 83, y) for y in rows.get("n83_coal", {})})
    return dict(sorted(out.items()))


def _diff(a, b):
    return {k: b[k] - v for k, v in a.items() if b[k] != v}


def overlap(rows):
    """Years given by both the old and the new tables, with the goods that differ (should be none), and the
    years given by two editions of the 1920 classification whose differences are not the known ones."""
    both = sorted(set(rows["coal"]) & set(rows["coalt_total"]))
    out = {y: {k: (a, b) for k, a in old_goods(rows, y).items() if a != (b := new_goods(rows, y)[k])}
           for y in both}
    pairs = {1911: (new_goods(rows, 1911), c20_goods(rows, 70, 1911))} if "n70_coal" in rows else {}
    pairs.update({y: (c20_goods(rows, 70, y), c20_goods(rows, 83, y))
                  for y in set(rows.get("n70_coal", {})) & set(rows.get("n83_coal", {}))})
    out.update({y: d for y, (a, b) in pairs.items() if (d := _diff(a, b)) != C20_KNOWN.get(y, {})})
    return out


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
    "the Board of Trade's Statistical Abstracts, read from the page images of Nos. 8, 16, 18, 30, 45, 46, 59, 70 and 83 "
    "(edition, page and table per figure in the data file). Every total the tables print was checked against its "
    "printed parts; the figures without a printed total were found printed the same in other editions (at least two "
    "from 1868, at least one before), and those found in no other edition's OCR text (mostly 1937-38) were read "
    "again from enlarged crops; 1846, given in No. 8 alone, was checked by its printed totals and an enlarged crop, and "
    "No. 8's 1854 column equals No. 16's in every good. For "
    "1868, given in both, No. 18 and No. 30 agree for cotton and linen; wool manufactures differ by 0.2% and wool "
    "yarn by 2.6% (No. 30's revised figures are used from 1868). The sub-headings changed over the years but the "
    "totals are the Abstract's own; from 1897 the Board's new classification was brought back to the old totals "
    "(they agree exactly for 1897 and 1898, given in both tables): waste from worked cotton is counted with cotton "
    "manufactures to 1907 and left out from 1908, and tops, noils, waste, flocks and alpaca and mohair yarn are "
    "left out of wool. From 1912 (Nos. 70 and 83, the classification of 1920, with no totals) the goods are the sum "
    "of their rows: cotton hosiery and gloves are counted with apparel and left out (0.62 million in 1911), waste "
    "from worked cotton is in other cotton manufactures until 1919 (1.46 million in 1911) and left out from 1920, "
    "and woollen hosiery, also moved to apparel, is added back; for 1911, given in both, No. 70's rows give cotton "
    "0.84 million and wool 0.01 million more than No. 59, whose figure is used. Cotton was {c0:,.1f} million in "
    "{y0}, fell from {c61:,.1f} million in 1861 to {c62:,.1f} million in 1862, was {c13:,.1f} million in 1913, "
    "{cmax:,.1f} million in {ycmax} and {c1:,.1f} million in {y1}; woollen and worsted goods {w0:,.1f}, "
    "{w13:,.1f} (1913), {wmax:,.1f} (in {ywmax}) and {w1:,.1f} million; linen {l0:,.1f}, {l13:,.1f} and "
    "{l1:,.1f} million. Jute, silk, artificial silk and apparel are not included.")
METALS_NOTE = (
    "The value of the coal, iron and steel, and machinery made in the United Kingdom and sent abroad each year, at "
    "the prices of the time, from the same Statistical Abstract tables as \"Textile exports\". Coal is coal, cinders "
    "(coke) and manufactured fuel, not bunker coal for ships and not the products of coal; iron and steel leaves out "
    "old iron for re-manufacture, though old rails are counted from 1907 to 1911, and hollow-ware from 1904; "
    "machinery leaves out sewing machines, which the old tables did not count as machinery (electrical machinery, "
    "shown on its own from 1903, was counted with other machinery before). Before 1868 (Nos. 8, 16 and 18) coal is "
    "coals, cinders and culm, without the patent fuel counted from then (for 1868 No. 18 gives 5.35 million, No. 30 "
    "5.44 million); tin plates, entered under tin, are added to iron and steel; manufactures of steel, entered with "
    "hardwares and cutlery before 1862 (No. 22) and not shown in No. 18, are counted only from 1868 (0.36 to 0.47 "
    "million a year in 1862-67, Nos. 22 and 24). No. 8 (1846-53) prints tin plates in one line with tin and pewter "
    "ware and counts old iron inside wrought iron; tin plates are taken from Nos. 10, 11 and 13 from 1848 and old "
    "iron left out from 1849 (Nos. 11 and 13), so iron and steel in 1846-47 is about 1% too high on the later "
    "definition (old iron 0.7% of iron and steel in 1849-53; pewter and tin ware 17,000 to 33,000 pounds a year) "
    "and in 1848 about 0.7%. From 1912 (Nos. 70 and 83) the goods are the sum of their rows, "
    "with rail locomotives (now under vehicles) counted as machinery and railway axles, tyres and wheels as iron "
    "and steel; road locomotives and steam rollers are not shown (0.47 million in 1911). From 1924 (No. 83) part of "
    "other iron and steel was moved and boilers and boiler-house plant gathered under machinery: for 1924 No. 83's "
    "rows give iron and steel 0.41 million less and machinery 1.98 million more than No. 70's (No. 83 is used). "
    "Coal was {k0:,.1f} million in {y0}, {k13:,.1f} million in 1913, {kmax:,.1f} million in {ykmax}, {k26:,.1f} "
    "million in 1926 and {k1:,.1f} million in {y1}; iron and steel {i0:,.1f}, {i13:,.1f} (1913), {imax:,.1f} (in "
    "{yimax}) and {i1:,.1f} million; machinery {m0:,.1f}, {m13:,.1f} (1913) and {m1:,.1f} million. New ships, "
    "recorded as exports from 1899, are not included.")
SHARE_NOTE = (
    "The main goods as a share of all exports of United Kingdom produce (\"UK exports of UK produce\", the "
    "Abstract's summary table; before 1854, when it begins, No. 8's total declared value of British and Irish produce "
    "exported; the summary table counts the parcel post from 1885: 2.1 of 233.4 million in 1898; from August 1914 "
    "to June 1917 goods taken from government stores or shipped on government vessels were left out, and from April 1923 exports "
    "to the Irish Free State are counted and the Free State's own exports are not). Cotton, wool and linen together "
    "were {t0:.1f}% in {y0}, {t13:.1f}% in 1913 and {t1:.1f}% in {y1}; cotton alone {c0:.1f}%, {c13:.1f}% and "
    "{c1:.1f}%; coal, iron and steel and machinery together {k0:.1f}%, {k13:.1f}% and {k1:.1f}%. Values at the "
    "prices of the time: a falling share can mean lower prices as well as smaller quantities.")


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
    printed = {y: v for y, v in rows.get("n70_all", {}).items() if abs(v / 1e6 - uk[y]) > 0.005}
    if printed:
        raise ValueError(f"No. 70's total exports differ from the summary table: {printed}")
    # Before 1854 the summary table has no imports at real values; all exports come from No. 8's own total
    # (table 15), printed the same as the total of No. 10's table of principal articles (1848-1853) and in No. 13.
    uk.update({y: v / 1e6 for y, v in rows.get("all", {}).items() if y < min(uk)})
    pts = series(by_year, {y: v * 1e6 for y, v in uk.items()})
    for sid, p in pts.items():
        _csv(sid, p)
    v = {k[len(PREFIX):-3]: dict(p) for k, p in pts.items()}
    c, w, l, k, i, m = (v[x] for x in ("cotton", "wool", "linen", "coal", "iron", "machinery"))
    y0, y1 = min(c), max(c)
    arg = lambda d, f: f(d, key=d.get)
    ycmax, ywmax, ykmax, yimax = arg(c, max), arg(w, max), arg(k, max), arg(i, max)
    gbp = "million pounds (prices of the time)"
    region = "United Kingdom (all Ireland to March 1923)"
    t, cs, ms = v["textiles_share"], v["cotton_share"], v["metal_share"]
    out = [
        _row(PREFIX + "cotton_uk", f"Textile exports, {y0}-{y1}", "Cotton yarn and manufactures", gbp, SOURCES, region,
             TEXTILES_NOTE.format(c0=c[y0], y0=y0, c61=c[1861], c62=c[1862], c13=c[1913], cmax=c[ycmax], ycmax=ycmax,
                                  c1=c[y1], y1=y1, w0=w[y0], w13=w[1913], wmax=w[ywmax], ywmax=ywmax, w1=w[y1],
                                  l0=l[y0], l13=l[1913], l1=l[y1]),
             [PREFIX + "wool_uk", PREFIX + "linen_uk"], unit="£m"),
        _row(PREFIX + "wool_uk", "Woollen exports", "Woollen and worsted yarn and manufactures", gbp, SOURCES, region,
             unit="£m"),
        _row(PREFIX + "linen_uk", "Linen exports", "Linen yarn and manufactures", gbp, SOURCES, region, unit="£m"),
        _row(PREFIX + "coal_uk", f"Coal, iron and machinery exports, {y0}-{y1}", "Coal, coke and manufactured fuel",
             gbp, SOURCES, region,
             METALS_NOTE.format(k0=k[y0], y0=y0, k13=k[1913], kmax=k[ykmax], ykmax=ykmax, k26=k[1926], k1=k[y1], y1=y1,
                                i0=i[y0], i13=i[1913], imax=i[yimax], yimax=yimax, i1=i[y1], m0=m[y0], m13=m[1913],
                                m1=m[y1]),
             [PREFIX + "iron_uk", PREFIX + "machinery_uk"], unit="£m"),
        _row(PREFIX + "iron_uk", "Iron and steel exports", "Iron and steel", gbp, SOURCES, region, unit="£m"),
        _row(PREFIX + "machinery_uk", "Machinery exports", "Machinery", gbp, SOURCES, region, unit="£m"),
        _row(PREFIX + "textiles_share_uk", f"Main exports, share of all UK exports, {y0}-{y1}",
             "Cotton, wool and linen", "% of exports of UK produce", SOURCES + ["stat_abstract_trade_uk"], region,
             SHARE_NOTE.format(t0=t[y0], y0=y0, t13=t[1913], t1=t[y1], y1=y1, c0=cs[y0], c13=cs[1913], c1=cs[y1],
                               k0=ms[y0], k13=ms[1913], k1=ms[y1]),
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
