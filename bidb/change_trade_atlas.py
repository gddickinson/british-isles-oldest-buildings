"""The main goods traded 1962-2024 as shares of all UK trade, by the divisions of SITC Revision 2, from the Growth
Lab at Harvard University's International Trade Data (CC0), for "Change over time" (roadmap C5b2d3).

The Annual Abstract tables after 1974 (No. 113 onwards) are still in Crown copyright, so the years between the
Annual Abstract graphs (to 1974, bidb.change_trade_sitc) and HMRC's (from 2000, bidb.change_trade_hmrc) come from this
public-domain dataset instead. It starts from the reports of every country to the United Nations (Comtrade) and
reconciles each flow with the partner's report, in US dollars; only shares of all goods are drawn, leaving out
non-monetary gold (division 97), which is large in recent years. On 1962-1974 the shares are compared with the
Annual Abstract's own (`compare`), and the notes give the differences.

    python -m bidb.change_trade_atlas   → data/curated/change/data/gl_*.csv + series.json entries
                                          (then python -m bidb.change_series)
"""
import csv
import json
import sys
from collections import defaultdict
from statistics import mean

from .change_firms import DATA
from .change_registers import _csv, _download, _row

URL = "https://dataverse.harvard.edu/api/access/datafile/13685146"    # sitc_country_product_year_2.csv, 50 MB
NAME = "sitc_country_product_year_2.csv"
SOURCE = "growth_lab_sitc2"
PREFIX = "gl_"
GOLD = "97"
UNCLASSIFIED = ("91", "93", "94", "95", "96")
EXPORT_GOODS = {"textiles": ("65",), "coal": ("32",), "iron": ("67",),
                "machinery": ("71", "72", "73", "74", "75", "76", "77")}     # SITC (R) divisions 71 and 72
IMPORT_GOODS = {"cereals": ("04",), "sugar": ("06",), "beverages": ("07",), "wood": ("24",), "fibres": ("26",)}


def load(country="GBR", log=print):
    """{year: {division: (exports, imports)}} in US dollars for one country (ISO3 code)."""
    out = defaultdict(dict)
    with open(_download(URL, NAME, log, "growthlab"), newline="") as f:
        for r in csv.DictReader(f):
            if r["country_iso3_code"] == country:
                out[int(r["year"])][r["product_sitc_code"]] = (int(r["export_value"]), int(r["import_value"]))
    return dict(sorted(out.items()))


def shares(by_year):
    """{year: {good: % of all exports or imports but gold, "gold_x"/"gold_i": gold's % of all, "other_x": % of
    exports not classified by kind}}."""
    out = {}
    for y, divs in by_year.items():
        side = [sum(v[i] for c, v in divs.items() if c != GOLD) for i in (0, 1)]
        part = lambda cs, i: sum(divs.get(c, (0, 0))[i] for c in cs) / side[i] * 100
        g = {k: part(cs, 0) for k, cs in EXPORT_GOODS.items()}
        g.update({k: part(cs, 1) for k, cs in IMPORT_GOODS.items()})
        for i, s in enumerate("xi"):
            gold = divs.get(GOLD, (0, 0))[i]
            g["gold_" + s] = gold / (side[i] + gold) * 100
        g["other_x"] = part(UNCLASSIFIED, 0)
        out[y] = g
    return out


def official():
    """{year: {good: % of all exports or imports}} from the Annual Abstract, 1953-1974 (bidb.change_trade_sitc)."""
    from . import change_trade_classes as classes
    from . import change_trade_sitc as sitc
    by_year = {**classes.goods(classes.load()), **sitc.goods(sitc.load())}
    out = {}
    for y, v in by_year.items():
        out[y] = {g: v[g] / v["exports"] * 100 for g in EXPORT_GOODS}
        out[y].update({g: v[g] / v["imports"] * 100 for g in IMPORT_GOODS})
    return out


def compare(gl, off):
    """(first, last year both cover, {good: mean of this share less the Annual Abstract's, in points})."""
    years = sorted(set(gl) & set(off))
    return years[0], years[-1], {g: round(mean(gl[y][g] - off[y][g] for y in years), 2)
                                 for g in list(EXPORT_GOODS) + list(IMPORT_GOODS)}


COMMON = (
    "Shares of all goods traded by the United Kingdom, leaving out non-monetary gold (division 97: {gx:.1f}% of "
    "exports and {gi:.1f}% of imports in {y1}, at most {g79:.2f}% before 1980), by the divisions of the Standard International "
    "Trade Classification, Revision 2, from the Growth Lab at Harvard University's International Trade Data (SITC, "
    "Rev. 2). It starts from the countries' reports to the United Nations (Comtrade) and reconciles each flow with "
    "the partner country's report (the Bustos-Yildirim method), in US dollars, so only shares are drawn. These are "
    "estimates, not the United Kingdom's own statistics: on {c0}-{c1}, the years both cover, they differ from the "
    "Annual Abstract's shares on average by (points) {diffs}. They bridge the years between the Annual Abstract graphs "
    "(to 1974; the editions after it are still in Crown copyright) and HMRC's (from 2000, by narrower headings of the "
    "Harmonized System). Goods not classified by kind (divisions 91-96) were at most {om:.1f}% of exports, in {yo}.")
EXPORTS_NOTE = (
    "Textile yarn, fabrics and made-up articles (division 65), coal, coke and briquettes (32), iron and steel (67) "
    "and machinery (71-77, the machinery of the revised classification's divisions 71 and 72; transport equipment "
    "left out) as a share of all UK exports. " + COMMON + " Textiles were {t0:.1f}% of exports in {y0}, {t75:.1f}% "
    "in 1975, {t99:.1f}% in 1999 and {t1:.1f}% in {y1}; machinery {m0:.1f}%, {m75:.1f}%, {m99:.1f}% and {m1:.1f}%; "
    "coal {k0:.2f}% in {y0} and {k1:.2f}% in {y1}.")
IMPORTS_NOTE = (
    "Cereals and cereal preparations (division 04), sugar, sugar preparations and honey (06), coffee, tea, cocoa and "
    "spices (07), cork and wood (24) and textile fibres and their waste (26) as a share of all UK imports. "
    + COMMON + " Cereals were {g0:.1f}% of imports in {y0}, {g75:.1f}% in 1975, {g99:.1f}% in 1999 and {g1:.1f}% in "
    "{y1}; sugar {s75:.1f}% in 1975 and {s99:.1f}% in 1999; textile fibres "
    "{f0:.1f}% in {y0} and {f1:.2f}% in {y1}.")
LABELS = {"textiles": "Textile yarn and fabrics", "coal": "Coal, coke and briquettes", "iron": "Iron and steel",
          "machinery": "Machinery", "cereals": "Cereals", "sugar": "Sugar and honey",
          "beverages": "Coffee, tea, cocoa and spices", "wood": "Cork and wood", "fibres": "Textile fibres"}


def write(sh, cmp, log=print):
    years = list(sh)
    if years != list(range(years[0], years[-1] + 1)):
        raise ValueError("years missing")
    for g in LABELS:
        _csv(f"{PREFIX}{g}_uk", [[y, round(v[g], 3)] for y, v in sh.items()])
    y0, y1 = years[0], years[-1]
    c0, c1, d = cmp
    yo = max(sh, key=lambda y: sh[y]["other_x"])
    diffs = lambda gs: ", ".join(f"{LABELS[g].lower()} {d[g]:+.2f}" for g in gs)
    base = dict(y0=y0, y1=y1, c0=c0, c1=c1, gx=sh[y1]["gold_x"], gi=sh[y1]["gold_i"], om=sh[yo]["other_x"], yo=yo,
                g79=max(max(v["gold_x"], v["gold_i"]) for y, v in sh.items() if y < 1980))
    at = lambda p, g: {p + k: sh[y][g] for k, y in (("0", y0), ("75", 1975), ("99", 1999), ("1", y1))}
    span = f"{y0}-{y1}"
    row = lambda g, title=None, note=None, models=None: _row(
        f"{PREFIX}{g}_uk", title or f"{LABELS[g]}, share of UK trade (SITC Rev. 2)", LABELS[g], "% of all goods "
        "but gold", [SOURCE], "United Kingdom", note, models and [f"{PREFIX}{m}_uk" for m in models], unit="%")
    out = [row("textiles", f"Main exports by SITC division, share of all UK exports, {span}",
               EXPORTS_NOTE.format(**base, diffs=diffs(EXPORT_GOODS), **at("t", "textiles"),
                                   **at("m", "machinery"), **at("k", "coal")), ["coal", "iron"])]
    out += [row(g) for g in ("coal", "iron")]
    out.append(row("machinery", f"Machinery exports by SITC division, share of all UK exports, {span}",
                   f"Machinery (divisions 71-77) as a share of all UK exports but gold; the source and its comparison "
                   f"with the Annual Abstract are in the note to Main exports by SITC division, {span}. "
                   f"{sh[y0]['machinery']:.1f}% in {y0}, {sh[1975]['machinery']:.1f}% in 1975, "
                   f"{sh[1999]['machinery']:.1f}% in 1999 and {sh[y1]['machinery']:.1f}% in {y1}."))
    out.append(row("cereals", f"Main imports by SITC division, share of all UK imports, {span}",
                   IMPORTS_NOTE.format(**base, diffs=diffs(IMPORT_GOODS), **at("g", "cereals"), **at("s", "sugar"),
                                       **at("f", "fibres")), ["sugar", "beverages"]))
    out += [row(g) for g in ("sugar", "beverages")]
    out.append(row("wood", f"Wood and textile fibre imports by SITC division, share of all UK imports, {span}",
                   f"Cork and wood (division 24) and textile fibres (26) as a share of all UK imports but gold; the "
                   f"source and its comparison with the Annual Abstract are in the note to Main imports by SITC "
                   f"division, {span}. Wood {sh[y0]['wood']:.1f}% in {y0} and {sh[y1]['wood']:.1f}% in {y1}; "
                   f"textile fibres {sh[y0]['fibres']:.1f}% and {sh[y1]['fibres']:.2f}%.", ["fibres"]))
    out.append(row("fibres"))
    path = DATA.parent / "series.json"
    keep = [s for s in json.loads(path.read_text()) if not s["id"].startswith(PREFIX)]
    path.write_text(json.dumps(keep + out, ensure_ascii=False, indent=1))
    log(f"{len(years)} years {span}; against the Annual Abstract {c0}-{c1}: " + diffs(LABELS))


def run(log=print):
    sh = shares(load(log=log))
    write(sh, compare(sh, official()), log)


if __name__ == "__main__":
    run(lambda m: print(m, file=sys.stderr, flush=True))
