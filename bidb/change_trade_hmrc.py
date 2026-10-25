"""The main goods traded since 2000, from HMRC's Overseas Trade Statistics, for "Change over time" (roadmap C5b2c).

HMRC's uktradeinfo API (OGL) gives the United Kingdom's trade by month, commodity (CN8) and partner, EU and non-EU
flows apart; its data begin in January 2000. One request per year sums value and net mass by HS heading for the
headings of the goods graphed from the Statistical Abstract for 1846-1938 (`GOODS`: the nearest modern headings,
stated in the notes), and one more sums all goods by month, to check that every month is there and for the shares.
Requests are paced (the API rejects quick ones) and cached.

    python -m bidb.change_trade_hmrc   → data/curated/change/data/hmrc_*.csv + series.json entries
                                         (then python -m bidb.change_series)
"""
import json
import sys

from .change_firms import DATA
from .change_registers import _csv, _row
from .http import request_json

URL = "https://api.uktradeinfo.com/OTS"
FIRST = 2000
GAP = 6.0                                  # seconds between requests
IMPORTS, EXPORTS = (1, 3), (2, 4)          # EU and non-EU flows
GOLD = ["7108"]                            # non-monetary gold, left out of the totals for the shares
SOURCES = ["hmrc_ots"]
PREFIX = "hmrc_"
_r = lambda a, b: [str(h) for h in range(a, b + 1)]
# HS headings (4 digits) of each good; exports first, then imports.
GOODS = {
    "cotton": _r(5204, 5212),                              # thread, yarn and woven fabrics of cotton
    "wool": ["5106", "5107", "5109", "5111", "5112"],      # yarn and woven fabrics of wool (not tops, waste, hair)
    "linen": ["5306", "5309"],                             # flax yarn and woven fabrics
    "coal": ["2701", "2702", "2704"],                      # coal, briquettes, lignite, coke
    "iron": [h for h in _r(7201, 7229) + _r(7301, 7326) if h != "7204"],   # iron, steel and their articles, not scrap
    "machinery": [h for h in _r(8401, 8487) if h != "8452"] + _r(8501, 8504) + ["8601", "8602"],
    "grain": [h for h in _r(1001, 1008) if h != "1006"] + ["1101", "1102"],   # cereals but rice, and their flours
    "raw_cotton": ["5201", "5203"],                        # raw cotton, carded or combed (not waste)
    "raw_wool": ["5101"],                                  # wool, not carded or combed
    "sugar": ["1701"],                                     # cane or beet sugar
    "tea": ["0902"],
    "timber": ["4403", "4406", "4407"],                    # wood in the rough, sleepers, sawn
}
EXPORT_GOODS = ("cotton", "wool", "linen", "coal", "iron", "machinery")
IMPORT_GOODS = ("grain", "raw_cotton", "raw_wool", "sugar", "tea", "timber")
# CommodityId (the CN8 code as a number) ranges holding the headings above, in one filter.
RANGES = [(902, 902), (1001, 1102), (1701, 1701), (2701, 2704), (4403, 4407), (5101, 5112), (5201, 5212),
          (5306, 5309), (7108, 7108), (7201, 7326), (8401, 8504), (8601, 8602)]


def _get(apply):
    return request_json(URL, params={"$apply": apply}, min_interval=GAP)["value"]


def _months(y):
    return f"MonthId ge {y}01 and MonthId le {y}12"


def headings(y):
    """{(flow, HS4): (value £, net mass kg)} for year y."""
    ids = " or ".join(f"(CommodityId ge {a * 10000} and CommodityId le {b * 10000 + 9999})" for a, b in RANGES)
    rows = _get(f"filter({_months(y)} and ({ids}))/groupby((FlowTypeId,Commodity/Hs4Code),"
                "aggregate(Value with sum as V,NetMass with sum as M))")
    return {(r["FlowTypeId"], r["Commodity"]["Hs4Code"]): (r["V"], r["M"]) for r in rows}


def totals(y):
    """{(flow, month): value £} of all goods in year y."""
    rows = _get(f"filter({_months(y)})/groupby((MonthId,FlowTypeId),aggregate(Value with sum as V))")
    return {(r["FlowTypeId"], r["MonthId"] % 100): r["V"] for r in rows}


def complete(tot):
    """True when all four flows have all twelve months."""
    return all((f, m) in tot for f in IMPORTS + EXPORTS for m in range(1, 13))


def goods(heads, tot):
    """{good: (value £, net mass kg)}, plus "exports" and "imports" (all goods but non-monetary gold) and "gold"."""
    out = {}
    for g, hs in GOODS.items():
        flows = EXPORTS if g in EXPORT_GOODS else IMPORTS
        v = [heads.get((f, h), (0, 0)) for f in flows for h in hs]
        out[g] = (sum(a for a, _ in v), sum(b for _, b in v))
    side = lambda flows: sum(v for (f, _), v in tot.items() if f in flows)
    gold = lambda flows: sum(heads.get((f, h), (0, 0))[0] for f in flows for h in GOLD)
    out["exports"] = (side(EXPORTS) - gold(EXPORTS), None)
    out["imports"] = (side(IMPORTS) - gold(IMPORTS), None)
    out["gold"] = (gold(EXPORTS), gold(IMPORTS))
    return out


def fetch(last, log=print):
    """{year: goods(...)} for every complete year from FIRST to `last`."""
    out = {}
    for y in range(FIRST, last + 1):
        tot = totals(y)
        if not complete(tot):
            log(f"{y}: incomplete ({len(tot)} flow-months), stopped")
            break
        out[y] = goods(headings(y), tot)
        log(f"{y}: exports {out[y]['exports'][0] / 1e9:,.1f} bn, imports {out[y]['imports'][0] / 1e9:,.1f} bn")
    return out


def series(by_year):
    """{series id: [[year, value]]}: £ million, thousand tonnes and shares of all exports or imports (%)."""
    m = lambda g: [[y, round(v[g][0] / 1e6, 2)] for y, v in by_year.items()]
    kt = lambda g: [[y, round(v[g][1] / 1e6, 2)] for y, v in by_year.items()]
    pct = lambda side, gs: [[y, round(sum(v[g][0] for g in gs) / v[side][0] * 100, 3)] for y, v in by_year.items()]
    out = {f"{PREFIX}{g}_uk": m(g) for g in EXPORT_GOODS + IMPORT_GOODS}
    out.update({f"{PREFIX}{g}_kt_uk": kt(g) for g in ("grain", "sugar", "tea", "raw_cotton", "raw_wool")})
    out[PREFIX + "textiles_share_uk"] = pct("exports", ("cotton", "wool", "linen"))
    out[PREFIX + "metal_share_uk"] = pct("exports", ("coal", "iron", "machinery"))
    out[PREFIX + "food_share_uk"] = pct("imports", ("grain", "sugar", "tea"))
    out[PREFIX + "materials_share_uk"] = pct("imports", ("raw_cotton", "raw_wool", "timber"))
    return out


def _then(sid, y):
    """A value of a Statistical Abstract series (1846-1938) for comparison in the notes."""
    rows = (DATA / f"{sid}.csv").read_text().splitlines()[1:]
    return dict((int(a), float(b)) for a, b, *_ in (r.split(",") for r in rows))[y]


COMMON = (
    "Summed from HM Revenue & Customs' Overseas Trade Statistics (uktradeinfo API), all partners, EU and non-EU, by "
    "Harmonized System heading, at the prices of the time. HMRC counts re-exports with exports (it does not separate "
    "goods made in the United Kingdom, as the Statistical Abstract did for 1846-1938), and from January 2021 Great "
    "Britain's trade with the EU is taken from customs declarations instead of the Intrastat survey, so the years "
    "from 2021 are not strictly comparable with those before. ")
TEXTILES_NOTE = (
    "The cotton, woollen and linen yarns and woven fabrics sent abroad each year. " + COMMON +
    "Cotton is headings 5204-5212 (sewing thread, yarn, woven fabrics), wool 5106, 5107, 5109, 5111 and 5112 (yarn and "
    "woven fabrics of wool, not tops, waste or the yarn of other animal hair), linen 5306 and 5309 (flax yarn and "
    "woven fabrics). Unlike the Abstract's totals these leave out made-up goods (clothing, household linen, lace, "
    "carpets), which HMRC classifies by article rather than by fibre. Cotton was {c0:,.1f} million pounds in {y0} and "
    "{c1:,.1f} million in {y1}; wool {w0:,.1f} and {w1:,.1f} million; linen {l0:,.1f} and {l1:,.1f} million. In 1913 "
    "the Abstract gives {c13:,.1f} million for cotton and {w13:,.1f} million for wool, at the prices of that time: the "
    "share graph compares them better.")
METALS_NOTE = (
    "The coal, iron and steel, and machinery sent abroad each year. " + COMMON +
    "Coal is headings 2701, 2702 and 2704 (coal and briquettes, lignite, coke); iron and steel chapters 72 and 73 "
    "(iron, steel and articles of them) without ferrous waste and scrap (7204), as the Abstract left out old iron; "
    "machinery chapter 84 without sewing machines (8452), with electric motors, generators and transformers "
    "(8501-8504) and rail locomotives (8601-8602), which the Abstract counted as machinery. Chapter 84 now holds "
    "computers, aircraft engines and turbines, far from the steam engines and textile machinery of 1913. Coal was "
    "{k0:,.1f} million pounds in {y0} and {k1:,.1f} million in {y1}; iron and steel {i0:,.0f} and {i1:,.0f} million; "
    "machinery {m0:,.0f} and {m1:,.0f} million (1913: coal {k13:,.1f}, iron and steel {i13:,.1f}, machinery "
    "{m13:,.1f} million).")
EXPORT_SHARE_NOTE = (
    "The main goods of the Statistical Abstract graphs as a share of all goods exported. " + COMMON +
    "All goods leave out non-monetary gold (heading 7108), whose flows through London's bullion market are large and "
    "erratic ({g1:,.1f} billion pounds exported in {y1}). Cotton, wool and linen yarns and fabrics were {t0:.2f}% of "
    "exports in {y0} and {t1:.2f}% in {y1} (in 1913 cotton, wool and linen goods were {t13:.1f}% of exports of UK "
    "produce, in 1938 {t38:.1f}%); coal, iron and steel and machinery {m0:.1f}% and {m1:.1f}% (1913: {m13:.1f}%, "
    "1938: {m38:.1f}%), almost all of it machinery.")
FOOD_NOTE = (
    "Grain and flour, sugar and tea brought into the United Kingdom each year. " + COMMON +
    "Grain is chapter 10 without rice (1006) and the flours of 1101 and 1102; sugar is heading 1701 (cane or beet "
    "sugar, raw or refined; not syrups or sugar confectionery); tea heading 0902 (not mate or tea extracts). Grain "
    "and flour cost {g0:,.0f} million pounds in {y0} and {g1:,.0f} million in {y1}; sugar {s0:,.0f} and {s1:,.0f} "
    "million; tea {t0:,.0f} and {t1:,.0f} million.")
MATERIALS_NOTE = (
    "Raw cotton, raw wool and timber brought into the United Kingdom each year. " + COMMON +
    "Raw cotton is headings 5201 and 5203 (not waste, 5202); wool heading 5101 (wool not carded or combed); timber "
    "headings 4403, 4406 and 4407 (wood in the rough, sleepers and sawn wood; not planed wood, panels or pulp). Raw "
    "cotton cost {c0:,.1f} million pounds in {y0} and {c1:,.1f} million in {y1}; wool {w0:,.1f} and {w1:,.1f} million; "
    "timber {k0:,.0f} and {k1:,.0f} million. In 1913 raw cotton cost {c13:,.1f} million pounds, more than any of the "
    "Abstract's main imports but grain and flour.")
IMPORT_SHARE_NOTE = (
    "The main goods of the Statistical Abstract graphs as a share of all goods imported (less non-monetary gold, "
    "heading 7108: {g1:,.1f} billion pounds imported in {y1}). " + COMMON +
    "Grain and flour, sugar and tea were {f0:.2f}% of imports in {y0} and {f1:.2f}% in {y1} (1913: {f13:.1f}%); raw "
    "cotton, wool and timber {m0:.2f}% and {m1:.2f}% (1913: {m13:.1f}%).")
WEIGHT_NOTE = (
    "Net mass of the same goods as \"Food imports\" and \"Raw material imports, {y0}-{y1}\" (HMRC Overseas Trade "
    "Statistics), in thousand tonnes; a tonne is 0.984 of the long ton used for 1854-1938. Grain and flour weighed "
    "{g0:,.0f} thousand tonnes in {y0} and {g1:,.0f} in {y1} (1913: {g13:,.0f} thousand tons); sugar {s0:,.0f} and "
    "{s1:,.0f}; tea {t0:,.0f} and {t1:,.0f} (1938: {t38:,.0f}).")
FIBRE_WEIGHT_NOTE = (
    "Net mass of raw cotton (headings 5201, 5203) and raw wool (5101) imported, thousand tonnes (HMRC Overseas Trade "
    "Statistics). Raw cotton weighed {c0:,.1f} thousand tonnes in {y0} and {c1:,.2f} in {y1}, against {c13:,.0f} "
    "thousand tons in 1913; wool {w0:,.1f} and {w1:,.1f} (1913: {w13:,.0f} thousand tons).")


def write(by_year, log=print):
    if list(by_year) != list(range(FIRST, max(by_year) + 1)):
        raise ValueError("years missing")
    pts = series(by_year)
    for sid, p in pts.items():
        _csv(sid, p)
    v = {k[len(PREFIX):-3]: dict(p) for k, p in pts.items()}
    y0, y1 = FIRST, max(by_year)
    a = lambda g: {"0": v[g][y0], "1": v[g][y1]}
    f = lambda **kw: {k + n: x for k, g in kw.items() for n, x in a(g).items()}
    gold = lambda i: by_year[y1]["gold"][i] / 1e9
    gbp, kt, pct = "million pounds (prices of the time)", "thousand tonnes", "%"
    region = "United Kingdom"
    row = lambda sid, title, label, unit_long, unit, note=None, models=None: _row(
        PREFIX + sid + "_uk", title, label, unit_long, SOURCES, region, note, models and [PREFIX + m + "_uk" for m in models],
        unit=unit)
    span = f"{y0}-{y1}"
    out = [
        row("cotton", f"Textile exports, {span}", "Cotton yarn and fabrics", gbp, "£m", TEXTILES_NOTE.format(
            y0=y0, y1=y1, c13=_then("sa_goods_cotton_uk", 1913), w13=_then("sa_goods_wool_uk", 1913),
            **f(c="cotton", w="wool", l="linen")), ["wool", "linen"]),
        row("wool", "Woollen exports since 2000", "Wool yarn and fabrics", gbp, "£m"),
        row("linen", "Linen exports since 2000", "Flax yarn and fabrics", gbp, "£m"),
        row("coal", f"Coal, iron and machinery exports, {span}", "Coal and coke", gbp, "£m", METALS_NOTE.format(
            y0=y0, y1=y1, k13=_then("sa_goods_coal_uk", 1913), i13=_then("sa_goods_iron_uk", 1913),
            m13=_then("sa_goods_machinery_uk", 1913), **f(k="coal", i="iron", m="machinery")), ["iron", "machinery"]),
        row("iron", "Iron and steel exports since 2000", "Iron and steel", gbp, "£m"),
        row("machinery", "Machinery exports since 2000", "Machinery", gbp, "£m"),
        row("textiles_share", f"Main exports, share of all UK exports, {span}", "Cotton, wool and linen",
            "% of goods exported", pct, EXPORT_SHARE_NOTE.format(
                y0=y0, y1=y1, g1=gold(0), t13=_then("sa_goods_textiles_share_uk", 1913),
                t38=_then("sa_goods_textiles_share_uk", 1938), m13=_then("sa_goods_metal_share_uk", 1913),
                m38=_then("sa_goods_metal_share_uk", 1938), **f(t="textiles_share", m="metal_share")),
            ["metal_share"]),
        row("metal_share", "Coal, iron and machinery, share of exports since 2000", "Coal, iron and machinery",
            "% of goods exported", pct),
        row("grain", f"Food imports, {span}", "Grain and flour", gbp, "£m", FOOD_NOTE.format(
            y0=y0, y1=y1, **f(g="grain", s="sugar", t="tea")), ["sugar", "tea"]),
        row("sugar", "Sugar imports since 2000", "Sugar", gbp, "£m"),
        row("tea", "Tea imports since 2000", "Tea", gbp, "£m"),
        row("raw_cotton", f"Raw material imports, {span}", "Raw cotton", gbp, "£m", MATERIALS_NOTE.format(
            y0=y0, y1=y1, c13=_then("sa_imports_cotton_uk", 1913), **f(c="raw_cotton", w="raw_wool", k="timber")),
            ["raw_wool", "timber"]),
        row("raw_wool", "Wool imports since 2000", "Wool", gbp, "£m"),
        row("timber", "Timber imports since 2000", "Timber", gbp, "£m"),
        row("food_share", f"Main imports, share of all imports, {span}", "Grain and flour, sugar and tea",
            "% of goods imported", pct, IMPORT_SHARE_NOTE.format(
                y0=y0, y1=y1, g1=gold(1), f13=_then("sa_imports_food_share_uk", 1913),
                m13=_then("sa_imports_materials_share_uk", 1913), **f(f="food_share", m="materials_share")),
            ["materials_share"]),
        row("materials_share", "Raw cotton, wool and timber, share of imports since 2000",
            "Raw cotton, wool and timber", "% of goods imported", pct),
        row("grain_kt", f"Food imports by weight, {span}", "Grain and flour", kt, "kt", WEIGHT_NOTE.format(
            y0=y0, y1=y1, g13=_then("sa_qty_grain_uk", 1913), t38=_then("sa_qty_tea_uk", 1938),
            **f(g="grain_kt", s="sugar_kt", t="tea_kt")), ["sugar_kt", "tea_kt"]),
        row("sugar_kt", "Sugar imported since 2000", "Sugar", kt, "kt"),
        row("tea_kt", "Tea imported since 2000", "Tea", kt, "kt"),
        row("raw_cotton_kt", f"Raw cotton and wool imported by weight, {span}", "Raw cotton", kt, "kt",
            FIBRE_WEIGHT_NOTE.format(y0=y0, y1=y1, c13=_then("sa_qty_cotton_uk", 1913),
                                     w13=_then("sa_qty_wool_uk", 1913), **f(c="raw_cotton_kt", w="raw_wool_kt")),
            ["raw_wool_kt"]),
        row("raw_wool_kt", "Wool imported since 2000", "Wool", kt, "kt"),
    ]
    for r in out:
        r["zero"] = True
    path = DATA.parent / "series.json"
    keep = [s for s in json.loads(path.read_text()) if not s["id"].startswith(PREFIX)]
    path.write_text(json.dumps(keep + out, ensure_ascii=False, indent=1))
    log(f"{len(by_year)} years {y0}-{y1}; machinery {v['machinery'][y0]:,.0f} -> {v['machinery'][y1]:,.0f} million; "
        f"textiles {v['textiles_share'][y0]:.2f}% -> {v['textiles_share'][y1]:.2f}% of exports")


def run(last=None, log=print):
    import datetime
    write(fetch(last or datetime.date.today().year, log), log)


if __name__ == "__main__":
    run(log=lambda m: print(m, file=sys.stderr, flush=True))
