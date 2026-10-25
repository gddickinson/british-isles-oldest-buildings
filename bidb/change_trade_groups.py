"""The main goods traded 1938-1952, by the Board of Trade's groups, for "Change over time" (roadmap C5b2d1).

After 1938 the Statistical Abstract gave way to the Central Statistical Office's Annual Abstract of Statistics, which
prints the values of imports and of exports of United Kingdom produce by the classes and groups of the 1920
classification (£ million, one decimal) until No. 90 (1953); from No. 91 the tables follow the Standard International
Trade Classification. The figures were read from the page images of Nos. 84 (1935-1946), 88 (1938-1950), 89 (1938,
1942-1951) and 90 (1935-1938, 1946-1952) (`data/curated/change/data/trade_groups_abstract_uk.csv`: edition, leaf, page
and table per figure). Each edition revises earlier years, so each year comes from the latest edition that prints it
(`LATEST`); every edition's five class totals are checked against its printed total (`check`), and the goods used were
found the same in another edition (1939-1940: No. 85's and No. 86's tables) or read again from an enlarged crop (No.
90). Groups are wider than the articles of the 1846-1938 graphs (1938 compared in the notes); linen, sugar and tea
have no group of their own.

    python -m bidb.change_trade_groups   → data/curated/change/data/aa_*.csv + series.json entries
                                           (then python -m bidb.change_series)
"""
import csv
import json
import sys
from collections import defaultdict

from .change_firms import DATA
from .change_registers import _csv, _row

READINGS = DATA / "trade_groups_abstract_uk.csv"
SOURCES = ["annual_abstract_groups_uk"]
PREFIX = "aa_"
EXPORT_GOODS = ("cotton", "wool", "coal", "iron", "machinery")      # coal: group II.A coal + III.A coke and fuel
IMPORT_GOODS = ("grain", "raw_cotton", "raw_wool", "timber")
CLASSES = ("food", "raw", "manuf", "animals", "parcel")             # classes I-V
ROUNDED = {84: 0.55}                                                # No. 84 prints its totals to the nearest £1m
LATEST = (90, 89, 88, 84)                                           # editions, latest first


def load(path=READINGS):
    """{edition number: {row: {year: £ million}}}."""
    out = defaultdict(lambda: defaultdict(dict))
    with open(path, newline="") as f:
        for r in csv.DictReader(f):
            out[int(r["number"])][r["row"]][int(r["year"])] = float(r["value"])
    return out


def check(rows):
    """Problems: an edition's year whose five class totals do not add up to its printed total (within rounding)."""
    bad = []
    for n, ed in sorted(rows.items()):
        for side in "ix":
            for y, total in sorted(ed[f"{side}_total"].items()):
                s = sum(ed[f"{side}_{c}"][y] for c in CLASSES)
                if abs(s - total) > ROUNDED.get(n, 0.25):
                    bad.append(f"No. {n} {y} {side}: classes {s:.1f} != total {total}")
    return bad


def total(ed, n, side, y):
    """All imports or exports of United Kingdom produce: the printed total, or the sum of the classes where the
    edition prints only whole millions."""
    return round(sum(ed[f"{side}_{c}"][y] for c in CLASSES), 1) if n in ROUNDED else ed[f"{side}_total"][y]


def goods(rows):
    """{year: {good: £ million, "exports": ..., "imports": ..., "edition": n}} from the latest edition per year."""
    out = {}
    for n in reversed(LATEST):
        ed = rows[n]
        for y in ed["x_total"]:
            g = {k: ed[k][y] for k in EXPORT_GOODS + IMPORT_GOODS if k != "coal"}
            g["coal"] = round(ed["coal"][y] + ed["coke"][y], 1)
            g.update(exports=total(ed, n, "x", y), imports=total(ed, n, "i", y), edition=n)
            out[y] = g
    return dict(sorted(out.items()))


def revisions(rows, row, y):
    """{edition: value} of one row and year, in every edition that prints it."""
    return {n: rows[n][row][y] for n in sorted(rows) if y in rows[n][row]}


def series(by_year):
    """{series id: [[year, value]]}: £ million and shares of all exports or imports (%)."""
    m = lambda g: [[y, v[g]] for y, v in by_year.items()]
    pct = lambda side, gs: [[y, round(sum(v[g] for g in gs) / v[side] * 100, 2)] for y, v in by_year.items()]
    out = {f"{PREFIX}{g}_uk": m(g) for g in EXPORT_GOODS + IMPORT_GOODS}
    out[PREFIX + "exports_uk"] = m("exports")
    out[PREFIX + "imports_uk"] = m("imports")
    out[PREFIX + "textiles_share_uk"] = pct("exports", ("cotton", "wool"))
    out[PREFIX + "metal_share_uk"] = pct("exports", ("coal", "iron", "machinery"))
    out[PREFIX + "grain_share_uk"] = pct("imports", ("grain",))
    out[PREFIX + "materials_share_uk"] = pct("imports", ("raw_cotton", "raw_wool", "timber"))
    return out


def _then(sid, y=1938):
    """A value of a Statistical Abstract series (1846-1938), to compare 1938 on both definitions."""
    rows = (DATA / f"{sid}.csv").read_text().splitlines()[1:]
    return dict((int(a), float(b)) for a, b, *_ in (r.split(",") for r in rows))[y]


COMMON = (
    "From the Annual Abstract of Statistics (Central Statistical Office, figures of the Board of Trade), which prints "
    "the value of imports and of exports of United Kingdom produce by the groups of the Board of Trade's 1920 "
    "classification until 1952, read from the page images of Nos. 84, 88, 89 and 90; each year is taken from the "
    "latest of these editions that prints it (they revise the years before), and the class totals of every edition "
    "were checked against its printed totals. Imports are valued at the port of arrival (cost, insurance and "
    "freight), exports free on board. Figures for 1942-1945 leave out the munitions imported and exported by "
    "government departments. The groups are wider than the articles of the 1846-1938 graphs, so 1938 is given on both "
    "definitions. ")
TEXTILES_NOTE = (
    "Cotton yarns and manufactures (group III.I) and woollen and worsted yarns and manufactures (III.J) exported each "
    "year, million pounds at the prices of the time. " + COMMON +
    "1938: cotton {c38:.1f} million here against {c38s:.1f} in the Statistical Abstract's articles, wool {w38:.1f} "
    "against {w38s:.1f}. Linen has no group of its own (it is inside the manufactures of other textile materials). "
    "Cotton was {c40:.1f} million in 1940, {c43:.1f} in 1943, {cmax:.1f} in {ycmax} and {c1:.1f} in {y1}; wool "
    "{w43:.1f} in 1943 and {w1:.1f} in {y1}. Later editions moved a little between the groups: No. 90 gives 1946-1951 "
    "wool 0.5 to 1.8 million higher than No. 89.")
METALS_NOTE = (
    "Coal (group II.A, with coke and manufactured fuel, III.A, as the 1846-1938 graphs counted them), iron and steel "
    "and manufactures thereof (III.C) and machinery (III.G) exported each year, million pounds at the prices of the "
    "time. " + COMMON +
    "1938: coal {k38:.1f} million here and {k38s:.1f} in the Statistical Abstract; iron and steel {i38:.1f} against "
    "{i38s:.1f}; machinery {m38:.1f} against {m38s:.1f} (the group leaves out locomotives, which are with vehicles). "
    "No. 88 moved part of machinery to other groups ({m38old:.1f} million in 1938 in No. 84, {m38:.1f} in No. 88), and "
    "No. 90 moved a little more (1951: {m51a:.1f} in No. 89, {m51b:.1f} in No. 90); 1939 and 1940 are only in No. 84, on "
    "the earlier basis. Coal exports fell from {k39:.1f} million in 1939 to {kmin:.1f} in {ykmin}; machinery rose from "
    "{m43:.1f} million in 1943 to {m1:.1f} in {y1}.")
EXPORT_SHARE_NOTE = (
    "Cotton and woollen goods, and coal, iron and steel and machinery, as a share of all exports of United Kingdom "
    "produce. " + COMMON +
    "Cotton and wool were {t38:.1f}% of exports in 1938 ({t38s:.1f}% with linen in the Statistical Abstract), "
    "{tmax:.1f}% in {ytmax} and {t1:.1f}% in {y1}; coal, iron and machinery {m38:.1f}% in 1938 and {m1:.1f}% in {y1}.")
IMPORTS_NOTE = (
    "Grain and flour (group I.A), raw cotton and cotton waste (II.F), wool, raw and waste, and woollen rags (II.G) "
    "and wood and timber (II.E) imported each year, million pounds at the prices of the time. " + COMMON +
    "1938: grain and flour {g38:.1f} million here against {g38s:.1f} for the wheat, barley, oats, maize and flour of "
    "the Statistical Abstract graphs; raw cotton {c38:.1f} against {c38s:.1f}; wool {w38:.1f} against {w38s:.1f}; "
    "timber {k38:.1f} against {k38s:.1f}. Sugar and tea have no group of their own (they are inside other food and "
    "beverages). Raw cotton cost {cmax:.1f} million in {ycmax} and {c1:.1f} in {y1}; wool {wmax:.1f} million in "
    "{ywmax}.")
IMPORT_SHARE_NOTE = (
    "Grain and flour, and raw cotton, wool and timber, as a share of all imports. " + COMMON +
    "Grain and flour were {g38:.1f}% of imports in 1938 ({g38s:.1f}% for the Statistical Abstract's grains), "
    "{gmax:.1f}% in {ygmax} and {g1:.1f}% in {y1}; raw cotton, wool and timber {m38:.1f}% in 1938 ({m38s:.1f}%) and "
    "{m1:.1f}% in {y1}.")
TOTALS_NOTE = (
    "All imports and all exports of United Kingdom produce, million pounds at the prices of the time (the sum of the "
    "five classes, as printed in each edition's summary table; No. 84 prints it to the nearest million, so 1939 and "
    "1940 are the sum of its classes). " + COMMON +
    "1938: imports {i38:.1f} million and exports {x38:.1f} (the Statistical Abstract: {i38s:.1f} and {x38s:.1f}). "
    "Exports fell to {xmin:.1f} million in {yxmin} and were {x1:.1f} in {y1}; imports {i1:.1f} million in {y1}.")


def write(by_year, rows, log=print):
    years = list(by_year)
    if years != list(range(years[0], years[-1] + 1)):
        raise ValueError("years missing")
    pts = series(by_year)
    for sid, p in pts.items():
        _csv(sid, p)
    v = {k[len(PREFIX):-3]: dict(p) for k, p in pts.items()}
    y1 = years[-1]
    top = lambda g: max(v[g], key=v[g].get)
    low = lambda g: min(v[g], key=v[g].get)
    gbp, pct = "million pounds (prices of the time)", "%"
    row = lambda sid, title, label, unit_long, unit, note=None, models=None: _row(
        PREFIX + sid + "_uk", title, label, unit_long, SOURCES, "United Kingdom", note,
        models and [PREFIX + m + "_uk" for m in models], unit=unit)
    span = f"{years[0]}-{y1}"
    mach = lambda n, y: rows[n]["machinery"][y]
    out = [
        row("cotton", f"Textile exports by group, {span}", "Cotton yarns and manufactures", gbp, "£m",
            TEXTILES_NOTE.format(c38=v["cotton"][1938], c38s=_then("sa_goods_cotton_uk"), w38=v["wool"][1938],
                                 w38s=_then("sa_goods_wool_uk"), c40=v["cotton"][1940], c43=v["cotton"][1943],
                                 cmax=v["cotton"][top("cotton")], ycmax=top("cotton"), c1=v["cotton"][y1], y1=y1,
                                 w43=v["wool"][1943], w1=v["wool"][y1]), ["wool"]),
        row("wool", "Woollen exports by group", "Woollen and worsted yarns and manufactures", gbp, "£m"),
        row("coal", f"Coal, iron and machinery exports by group, {span}", "Coal, coke and manufactured fuel", gbp,
            "£m", METALS_NOTE.format(
                k38=v["coal"][1938], k38s=_then("sa_goods_coal_uk"), i38=v["iron"][1938],
                i38s=_then("sa_goods_iron_uk"), m38=v["machinery"][1938], m38s=_then("sa_goods_machinery_uk"),
                m38old=mach(84, 1938), m51a=mach(89, 1951), m51b=mach(90, 1951), k39=v["coal"][1939],
                kmin=v["coal"][low("coal")], ykmin=low("coal"), m43=v["machinery"][1943], m1=v["machinery"][y1],
                y1=y1), ["iron", "machinery"]),
        row("iron", "Iron and steel exports by group", "Iron and steel and manufactures", gbp, "£m"),
        row("machinery", "Machinery exports by group", "Machinery", gbp, "£m"),
        row("textiles_share", f"Main exports by group, share of all UK exports, {span}", "Cotton and wool",
            "% of exports of UK produce", pct, EXPORT_SHARE_NOTE.format(
                t38=v["textiles_share"][1938], t38s=_then("sa_goods_textiles_share_uk"),
                tmax=v["textiles_share"][top("textiles_share")], ytmax=top("textiles_share"),
                t1=v["textiles_share"][y1], y1=y1, m38=v["metal_share"][1938], m1=v["metal_share"][y1]),
            ["metal_share"]),
        row("metal_share", "Coal, iron and machinery by group, share of exports", "Coal, iron and machinery",
            "% of exports of UK produce", pct),
        row("grain", f"Main imports by group, {span}", "Grain and flour", gbp, "£m", IMPORTS_NOTE.format(
            g38=v["grain"][1938], g38s=_then("sa_imports_grain_uk"), c38=v["raw_cotton"][1938],
            c38s=_then("sa_imports_cotton_uk"), w38=v["raw_wool"][1938], w38s=_then("sa_imports_wool_uk"),
            k38=v["timber"][1938], k38s=_then("sa_imports_timber_uk"), c1=v["raw_cotton"][y1], y1=y1,
            cmax=v["raw_cotton"][top("raw_cotton")], ycmax=top("raw_cotton"), wmax=v["raw_wool"][top("raw_wool")],
            ywmax=top("raw_wool")), ["raw_cotton", "raw_wool", "timber"]),
        row("raw_cotton", "Raw cotton imports by group", "Raw cotton and cotton waste", gbp, "£m"),
        row("raw_wool", "Wool imports by group", "Wool, raw and waste", gbp, "£m"),
        row("timber", "Timber imports by group", "Wood and timber", gbp, "£m"),
        row("grain_share", f"Main imports by group, share of all imports, {span}", "Grain and flour",
            "% of all imports", pct, IMPORT_SHARE_NOTE.format(
                g38=v["grain_share"][1938], g38s=_then("sa_imports_grain_share_uk"),
                gmax=v["grain_share"][top("grain_share")], ygmax=top("grain_share"), g1=v["grain_share"][y1], y1=y1,
                m38=v["materials_share"][1938], m38s=_then("sa_imports_materials_share_uk"),
                m1=v["materials_share"][y1]), ["materials_share"]),
        row("materials_share", "Raw cotton, wool and timber by group, share of imports", "Raw cotton, wool and timber",
            "% of all imports", pct),
        row("imports", f"Overseas trade at the prices of the time, {span}", "Imports", gbp, "£m", TOTALS_NOTE.format(
            i38=v["imports"][1938], x38=v["exports"][1938], i38s=_then("sa_trade_imports_uk"),
            x38s=_then("sa_trade_exports_uk"), xmin=v["exports"][low("exports")], yxmin=low("exports"),
            x1=v["exports"][y1], i1=v["imports"][y1], y1=y1), ["exports"]),
        row("exports", "UK exports of UK produce, 1938-1952", "Exports of United Kingdom produce", gbp, "£m"),
    ]
    for r in out:
        r["zero"] = True
    path = DATA.parent / "series.json"
    keep = [s for s in json.loads(path.read_text()) if not s["id"].startswith(PREFIX)]
    path.write_text(json.dumps(keep + out, ensure_ascii=False, indent=1))
    log(f"{len(years)} years {span}; machinery {v['machinery'][1938]:.1f} -> {v['machinery'][y1]:.1f} million; "
        f"cotton and wool {v['textiles_share'][1938]:.1f}% -> {v['textiles_share'][y1]:.1f}% of exports")


def run(log=print):
    rows = load()
    bad = check(rows)
    if bad:
        raise ValueError("; ".join(bad))
    write(goods(rows), rows, log)


if __name__ == "__main__":
    run(lambda m: print(m, file=sys.stderr, flush=True))
