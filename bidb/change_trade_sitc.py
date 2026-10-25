"""The main goods traded 1958-1974, by the divisions of the Standard International Trade Classification, Revised,
for "Change over time" (roadmap C5b2d2a).

From No. 91 (1954) the Annual Abstract of Statistics prints imports and exports by the sections and divisions of the
Standard International Trade Classification, and from No. 101 by its revised form, SITC (R). Every division of every
section is printed (or an "other" line), so each figure was checked twice: the divisions against their section's
total, and the ten sections (and the subtotal of manufactures, sections 5-8) against the grand total (`check`). The
figures were read from the page images of Nos. 104 (1958-1966), 108 (1962-1970) and 112 (1966-1974)
(`data/curated/change/data/trade_sitc_abstract_uk.csv`: edition, leaf, page and table per figure); each year comes from
the latest of these editions (`LATEST`). The overlap years agree figure for figure (`overlap`): imports 1962-1965 in
Nos. 104 and 108, both sides 1966-1969 in Nos. 108 and 112 (No. 108 counts furniture imports with the other
miscellaneous articles); only an edition's last year, a first estimate, is revised by the next. From 1965 precious stones are in the trade
accounts, and Nos. 104 onwards add estimates for every earlier year; No. 102 and earlier editions leave them out, so
1953-1957 is a separate task (C5b2d2b). From 1970 re-exports are counted with exports, and Nos. 108 and 112 restate
1962-1969 so; No. 104 gives exports of United Kingdom produce alone, used for 1958-1961.

    python -m bidb.change_trade_sitc   → data/curated/change/data/aas_*.csv + series.json entries
                                         (then python -m bidb.change_series)
"""
import csv
import json
import re
import sys
from collections import defaultdict

from .change_firms import DATA
from .change_registers import _csv, _row

READINGS = DATA / "trade_sitc_abstract_uk.csv"
SOURCES = ["annual_abstract_sitc_uk"]
PREFIX = "aas_"
LATEST = (112, 108, 104)                    # editions, latest first
EXPORT_GOODS = {"textiles": ("65",), "coal": ("32",), "iron": ("67",), "machinery": ("71", "72")}
IMPORT_GOODS = {"cereals": ("04",), "sugar": ("06",), "beverages": ("07",), "wood": ("24",), "fibres": ("26",)}
# Printed totals that differ from their parts by more than the rounding, in every edition that prints them
KNOWN = {(108, "i", 1969, "s3"), (112, "i", 1969, "s3")}    # fuels 906.5, parts 1.3 + 885.5 + 19.4 = 906.2


def load(path=READINGS):
    """{edition number: {row: {year: £ million}}}; rows are side (x exports, i imports) + "_" + code: "total",
    section totals "s0"-"s9", divisions "00"-"89", "o<section>" for a section's other divisions, "mf" for sections
    5-8 together, "9pp" and "9o" for section 9's post parcels and other."""
    out = defaultdict(lambda: defaultdict(dict))
    with open(path, newline="") as f:
        for r in csv.DictReader(f):
            out[int(r["number"])][r["row"]][int(r["year"])] = float(r["value"])
    return out


def _parts(ed, side, s, y):
    """The printed parts of section s in year y."""
    pat = re.compile(rf"{side}_({s}\d|o{s})" + (rf"|{side}_9pp|{side}_9o" if s == 9 else ""))
    return [v[y] for r, v in ed.items() if pat.fullmatch(r) and y in v]


def check(rows):
    """Problems: a section whose divisions, or a total whose sections, do not add up within the rounding (half a unit
    of the last digit for each part and the total)."""
    bad = []
    near = lambda a, b, k: abs(a - b) <= 0.05 * (k + 1) + 0.01
    for n, ed in sorted(rows.items()):
        for side in "xi":
            for y, total in sorted(ed[f"{side}_total"].items()):
                secs = [ed[f"{side}_s{s}"][y] for s in range(10)]
                if not near(sum(secs), total, 10):
                    bad.append(f"No. {n} {y} {side}: sections {sum(secs):.1f} != total {total}")
                if not near(sum(secs[5:9]), ed[f"{side}_mf"][y], 4):
                    bad.append(f"No. {n} {y} {side}: sections 5-8 {sum(secs[5:9]):.1f} != {ed[f'{side}_mf'][y]}")
                for s in range(10):
                    p = _parts(ed, side, s, y)
                    if p and not near(sum(p), secs[s], len(p)) and (n, side, y, f"s{s}") not in KNOWN:
                        bad.append(f"No. {n} {y} {side}: section {s} parts {sum(p):.1f} != {secs[s]}")
    return bad


def overlap(rows, a, b):
    """Rows and years printed in editions a and b with different figures: [(row, year, in a, in b)]."""
    return sorted((r, y, v, rows[b][r][y]) for r, ys in rows[a].items() for y, v in ys.items()
                  if y in rows[b].get(r, {}) and v != rows[b][r][y])


def goods(rows):
    """{year: {good: £ million, "exports": ..., "imports": ..., "edition": n}} from the latest edition per year."""
    out = {}
    for n in reversed(LATEST):
        ed = rows[n]
        for y in ed["x_total"]:
            g = {k: round(sum(ed["x_" + d][y] for d in ds), 1) for k, ds in EXPORT_GOODS.items()}
            g.update({k: round(sum(ed["i_" + d][y] for d in ds), 1) for k, ds in IMPORT_GOODS.items()})
            g.update(exports=ed["x_total"][y], imports=ed["i_total"][y], edition=n)
            out[y] = g
    return dict(sorted(out.items()))


def series(by_year):
    """{series id: [[year, value]]}: £ million and shares of all exports or imports (%)."""
    m = lambda g: [[y, v[g]] for y, v in by_year.items()]
    pct = lambda side, gs: [[y, round(sum(v[g] for g in gs) / v[side] * 100, 2)] for y, v in by_year.items()]
    out = {f"{PREFIX}{g}_uk": m(g) for g in list(EXPORT_GOODS) + list(IMPORT_GOODS)}
    out[PREFIX + "exports_uk"] = m("exports")
    out[PREFIX + "imports_uk"] = m("imports")
    out[PREFIX + "textiles_share_uk"] = pct("exports", ("textiles",))
    out[PREFIX + "metal_share_uk"] = pct("exports", ("coal", "iron", "machinery"))
    out[PREFIX + "food_share_uk"] = pct("imports", ("cereals", "sugar", "beverages"))
    out[PREFIX + "materials_share_uk"] = pct("imports", ("wood", "fibres"))
    return out


def _then(sid, y):
    """A value of another series (the 1938-1952 groups), for the notes."""
    rows = (DATA / f"{sid}.csv").read_text().splitlines()[1:]
    return dict((int(a), float(b)) for a, b, *_ in (r.split(",") for r in rows))[y]


def reexports(rows, codes, y):
    """Exports of the divisions in year y with re-exports (No. 108) and without them (No. 104)."""
    return tuple(round(sum(rows[n]["x_" + c][y] for c in codes), 1) for n in (108, 104))


COMMON = (
    "From the Annual Abstract of Statistics (Central Statistical Office; figures of the Board of Trade, later the "
    "Department of Trade), which prints imports and exports by the sections and divisions of the Standard "
    "International Trade Classification, Revised, read from the page images of Nos. 104, 108 and 112; each year is "
    "taken from the latest of these that prints it, and every division was checked against its section's total and "
    "every section against the grand total. Imports are valued c.i.f., exports f.o.b. Up to 1961 exports are of United "
    "Kingdom produce; from 1962 they include re-exports (not distinguished in the statistics from 1970, and restated so "
    "for the earlier years). Precious stones are included throughout (in the trade accounts from 1965, estimated for "
    "the years before). From 1970 consignments of low value are counted only in the total, so the divisions are slightly "
    "short. The divisions are wider than the groups of 1938-1952 and the articles before. ")
TEXTILES_NOTE = (
    "Textile yarn, fabrics and made-up articles (division 65) exported each year, million pounds at the prices of the "
    "time; clothing is a division of its own (84) and is left out. " + COMMON +
    "With re-exports in 1962 it was {t62:,.1f} million, without them {t62u:,.1f}. Textiles were {t58:,.1f} million in "
    "1958 and {t1:,.1f} in {y1}; the cotton and woollen groups of the earlier classification, which leave out the other fibres, "
    "came to {c52:,.1f} million in 1952.")
METALS_NOTE = (
    "Coal, coke and briquettes (division 32), iron and steel (67) and machinery, electrical and other (71 and 72; "
    "transport equipment, 73, left out) exported each year, million pounds at the prices of the time. " + COMMON +
    "Re-exports hardly touch coal and iron (1962: coal {k62:,.1f} million either way, iron and steel {i62:,.1f} against "
    "{i62u:,.1f}) but are more in machinery ({m62:,.1f} against {m62u:,.1f}). Coal fell from {k58:,.1f} million in 1958 "
    "to {kmin:,.1f} in {ykmin}; machinery rose from {m58:,.1f} million to {m1:,.1f} in {y1}.")
EXPORT_SHARE_NOTE = (
    "Textile yarn and fabrics, and coal, iron and steel and machinery, as a share of all exports. " + COMMON +
    "Textiles were {t58:,.1f}% of exports in 1958 and {t1:,.1f}% in {y1}; coal, iron and steel and machinery "
    "{m58:,.1f}% and {m1:,.1f}%.")
IMPORTS_NOTE = (
    "Cereals and cereal preparations (division 04), sugar, sugar preparations and honey (06), coffee, tea, cocoa, "
    "spices and their manufactures (07; tea is not shown apart), wood, lumber and cork (24) and textile fibres and "
    "their waste (26: raw cotton, wool and the other fibres together) imported each year, million pounds at the prices "
    "of the time. " + COMMON +
    "Cereals cost {g58:,.1f} million in 1958 and {g1:,.1f} in {y1}; sugar {s58:,.1f} million in 1958, {s63:,.1f} in "
    "1963 and {s1:,.1f} in {y1}; textile fibres {f58:,.1f} million in 1958 and {f1:,.1f} in {y1}. In 1952 the grain and "
    "flour group of the earlier classification cost {g52:,.1f} million.")
IMPORT_SHARE_NOTE = (
    "Cereals, sugar and coffee, tea and cocoa, and wood and textile fibres, as a share of all imports. " + COMMON +
    "The foods were {f58:,.1f}% of imports in 1958 and {f1:,.1f}% in {y1}; wood and textile fibres {m58:,.1f}% and "
    "{m1:,.1f}%.")
TOTALS_NOTE = (
    "All imports and all exports, million pounds at the prices of the time, as printed in the tables by division. "
    + COMMON + "Re-exports added {r62:,.1f} million to the exports of 1962 ({x62u:,.1f} of United Kingdom produce, "
    "{x62:,.1f} with re-exports). Imports were {i58:,.1f} million in 1958 and {i1:,.1f} in {y1}, exports {x58:,.1f} and "
    "{x1:,.1f}; oil imports (division 33) rose from {o73:,.1f} million in 1973 to {o74:,.1f} in 1974.")


def write(by_year, rows, log=print):
    years = list(by_year)
    if years != list(range(years[0], years[-1] + 1)):
        raise ValueError("years missing")
    pts = series(by_year)
    for sid, p in pts.items():
        _csv(sid, p)
    v = {k[len(PREFIX):-3]: dict(p) for k, p in pts.items()}
    y1 = years[-1]
    low = lambda g: min(v[g], key=v[g].get)
    gbp, pct = "million pounds (prices of the time)", "%"
    row = lambda sid, title, label, unit_long, unit, note=None, models=None: _row(
        PREFIX + sid + "_uk", title, label, unit_long, SOURCES, "United Kingdom", note,
        models and [PREFIX + m + "_uk" for m in models], unit=unit)
    span = f"{years[0]}-{y1}"
    t62, t62u = reexports(rows, ("65",), 1962)
    k62, _ = reexports(rows, ("32",), 1962)
    i62, i62u = reexports(rows, ("67",), 1962)
    m62, m62u = reexports(rows, ("71", "72"), 1962)
    x62, x62u = reexports(rows, ("total",), 1962)
    out = [
        row("textiles", f"Textile exports by division, {span}", "Textile yarn, fabrics and made-up articles", gbp,
            "£m", TEXTILES_NOTE.format(t62=t62, t62u=t62u, t58=v["textiles"][years[0]], t1=v["textiles"][y1], y1=y1,
                                       c52=_then("aa_cotton_uk", 1952) + _then("aa_wool_uk", 1952))),
        row("coal", f"Coal, iron and machinery exports by division, {span}", "Coal, coke and briquettes", gbp, "£m",
            METALS_NOTE.format(k62=k62, i62=i62, i62u=i62u, m62=m62, m62u=m62u, k58=v["coal"][years[0]],
                               kmin=v["coal"][low("coal")], ykmin=low("coal"), m58=v["machinery"][years[0]],
                               m1=v["machinery"][y1], y1=y1), ["iron", "machinery"]),
        row("iron", "Iron and steel exports by division", "Iron and steel", gbp, "£m"),
        row("machinery", "Machinery exports by division", "Machinery, electrical and other", gbp, "£m"),
        row("textiles_share", f"Main exports by division, share of all UK exports, {span}", "Textile yarn and fabrics",
            "% of exports", pct, EXPORT_SHARE_NOTE.format(
                t58=v["textiles_share"][years[0]], t1=v["textiles_share"][y1], y1=y1,
                m58=v["metal_share"][years[0]], m1=v["metal_share"][y1]), ["metal_share"]),
        row("metal_share", "Coal, iron and machinery by division, share of exports", "Coal, iron and machinery",
            "% of exports", pct),
        row("cereals", f"Main imports by division, {span}", "Cereals and cereal preparations", gbp, "£m",
            IMPORTS_NOTE.format(g58=v["cereals"][years[0]], g1=v["cereals"][y1], s58=v["sugar"][years[0]],
                                s63=v["sugar"][1963], s1=v["sugar"][y1], f58=v["fibres"][years[0]],
                                f1=v["fibres"][y1], y1=y1, g52=_then("aa_grain_uk", 1952)),
            ["sugar", "beverages", "wood", "fibres"]),
        row("sugar", "Sugar imports by division", "Sugar, sugar preparations and honey", gbp, "£m"),
        row("beverages", "Coffee, tea and cocoa imports by division", "Coffee, tea, cocoa and spices", gbp, "£m"),
        row("wood", "Wood imports by division", "Wood, lumber and cork", gbp, "£m"),
        row("fibres", "Textile fibre imports by division", "Textile fibres and waste", gbp, "£m"),
        row("food_share", f"Main imports by division, share of all imports, {span}", "Cereals, sugar, coffee and tea",
            "% of all imports", pct, IMPORT_SHARE_NOTE.format(
                f58=v["food_share"][years[0]], f1=v["food_share"][y1], y1=y1,
                m58=v["materials_share"][years[0]], m1=v["materials_share"][y1]), ["materials_share"]),
        row("materials_share", "Wood and textile fibres by division, share of imports", "Wood and textile fibres",
            "% of all imports", pct),
        row("imports", f"Overseas trade at the prices of the time, {span}", "Imports", gbp, "£m", TOTALS_NOTE.format(
            r62=round(x62 - x62u, 1), x62u=x62u, x62=x62, i58=v["imports"][years[0]], i1=v["imports"][y1],
            x58=v["exports"][years[0]], x1=v["exports"][y1], y1=y1, o73=rows[112]["i_33"][1973],
            o74=rows[112]["i_33"][1974]), ["exports"]),
        row("exports", f"UK exports, {span}", "Exports", gbp, "£m"),
    ]
    for r in out:
        r["zero"] = True
    path = DATA.parent / "series.json"
    keep = [s for s in json.loads(path.read_text()) if not s["id"].startswith(PREFIX)]
    path.write_text(json.dumps(keep + out, ensure_ascii=False, indent=1))
    log(f"{len(years)} years {span}; machinery {v['machinery'][years[0]]:.1f} -> {v['machinery'][y1]:.1f} million; "
        f"textiles {v['textiles_share'][years[0]]:.1f}% -> {v['textiles_share'][y1]:.1f}% of exports")


def run(log=print):
    rows = load()
    bad = check(rows)
    if bad:
        raise ValueError("; ".join(bad))
    write(goods(rows), rows, log)


if __name__ == "__main__":
    run(lambda m: print(m, file=sys.stderr, flush=True))
