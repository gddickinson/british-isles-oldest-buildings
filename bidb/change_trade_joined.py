"""The main goods traded 1846-2024 as shares of all UK trade, one line across the eras, with the breaks of definition
marked, for "Change over time" (roadmap C5b2d4).

Each era's graphs stay as they are; these join them into four long lines: textiles and coal, iron and machinery as
shares of exports, grain and raw materials (cotton, wool, wood) as shares of imports. Each year comes from one era:
the Statistical Abstract to 1938 (bidb.change_trade_goods, bidb.change_trade_imports), the Annual Abstract's groups
1939-1952 (bidb.change_trade_groups), its SITC divisions 1953-1974 (bidb.change_trade_classes, bidb.change_trade_sitc)
and the Growth Lab's SITC Rev. 2 shares 1975-2024 (bidb.change_trade_atlas), which keep the same divisions to the
end. HMRC's graphs since 2000 (bidb.change_trade_hmrc) use the nearest headings of the old articles, much narrower
than the divisions (textiles 0.29% of exports in 2000 against the Growth Lab's 1.6%), so they are not joined.

Shares are the only measure that can be joined: values are at the prices of the time, and the Growth Lab's are in
US dollars. Where two eras give a year (1938, 1962-1974), the breaks' notes give it on both definitions.

    python -m bidb.change_trade_joined   → data/curated/change/data/tj_*.csv + series.json entries
                                           (then python -m bidb.change_series)
"""
import csv
import json
import sys

from .change_firms import DATA
from .change_registers import _row

PREFIX = "tj_"
GL_FROM = 1975                       # first year from the Growth Lab; the Annual Abstract before
# first year on each new definition: (year, text); {a} and {b} are the share on the old and the new definition in the
# year before, where both eras give it
BREAKS = {
    1912: "From 1912 the Board of Trade's classification of 1920 (Statistical Abstract Nos. 70 and 83); 1911 on "
          "both definitions: {a} and {b}",
    1923: "From April 1923 trade with the Irish Free State counts as overseas trade and the Free State's own trade "
          "is left out",
    1939: "From 1939 the groups of the Annual Abstract of Statistics, wider than the Statistical Abstract's "
          "articles; 1938 on both: {a} and {b}",
    1953: "From 1953 the divisions of the Standard International Trade Classification (Annual Abstract), wider "
          "again",
    1958: "From 1958 the revised classification, SITC (R), with precious stones",
    1962: "From 1962 exports include re-exports",
    1975: "From 1975 the Growth Lab's shares (UN Comtrade reconciled with partners' reports, SITC Rev. 2, gold left "
          "out); 1974 on both: {a} (Annual Abstract) and {b}",
}
# (id, label, eras: [(first year, last year, csv ids summed, or (numerators, denominator) for a share to compute)])
JOINED = [
    ("textiles_x", "Textiles", "exports", [
        (1846, 1938, ["sa_goods_textiles_share_uk"]), (1939, 1952, ["aa_textiles_share_uk"]),
        (1953, 1974, ["aas_textiles_share_uk"]), (GL_FROM, 2024, ["gl_textiles_uk"])],
     "cotton, woollen and linen goods to 1938 (yarn and manufactures), the cotton and woollen groups 1939-1952, "
     "textile yarn, fabrics and made-up articles (division 65) from 1953"),
    ("metal_x", "Coal, iron and steel, and machinery", "exports", [
        (1846, 1938, ["sa_goods_metal_share_uk"]), (1939, 1952, ["aa_metal_share_uk"]),
        (1953, 1974, ["aas_metal_share_uk"]), (GL_FROM, 2024, ["gl_coal_uk", "gl_iron_uk", "gl_machinery_uk"])],
     "coal, iron and steel and machinery; from 1953 coal (division 32), iron and steel (67) and machinery (71-72 of "
     "SITC (R), 71-77 of Rev. 2: electrical and other machinery, not road vehicles, ships or aircraft)"),
    ("grain_i", "Grain and flour (cereals)", "imports", [
        (1854, 1938, ["sa_imports_grain_share_uk"]), (1939, 1952, ["aa_grain_share_uk"]),
        (1953, 1974, (["aas_cereals_uk"], "aas_imports_uk")), (GL_FROM, 2024, ["gl_cereals_uk"])],
     "grain and flour to 1952, cereals and cereal preparations (division 04) from 1953"),
    ("materials_i", "Raw cotton, wool and wood", "imports", [
        (1854, 1938, ["sa_imports_materials_share_uk"]), (1939, 1952, ["aa_materials_share_uk"]),
        (1953, 1974, ["aas_materials_share_uk"]), (GL_FROM, 2024, ["gl_wood_uk", "gl_fibres_uk"])],
     "raw cotton, wool and timber to 1952, cork and wood (division 24) and all textile fibres (26) from 1953"),
]
SOURCES = {"sa_goods": "stat_abstract_goods_uk", "sa_imports": "stat_abstract_imports_uk",
           "aa_": "annual_abstract_groups_uk", "aas_": "annual_abstract_sitc_uk", "gl_": "growth_lab_sitc2"}


def read(sid):
    with open(DATA / f"{sid}.csv", newline="") as f:
        return {int(r["year"]): float(r["value"]) for r in csv.DictReader(f) if r["value"]}


def era_values(spec):
    """{year: share} of one era's series: the sum of shares, or 100 * sum / total."""
    if isinstance(spec, tuple):
        nums, den = [read(s) for s in spec[0]], read(spec[1])
        return {y: 100 * sum(n[y] for n in nums) / den[y] for y in den if all(y in n for n in nums)}
    parts = [read(s) for s in spec]
    return {y: sum(p[y] for p in parts) for y in parts[0] if all(y in p for p in parts)}


def join(eras):
    """([[year, share, era index]], {break year: (old, new) in the year before, where both eras give it}): each year
    from one era, which must give every year of its span."""
    pts, both = [], {}
    vals = [era_values(spec) for _, _, spec in eras]
    for i, ((y0, y1, _), v) in enumerate(zip(eras, vals)):
        missing = [y for y in range(y0, y1 + 1) if y not in v]
        if missing:
            raise ValueError(f"era {y0}-{y1}: no value for {missing[:5]}")
        pts += [[y, round(v[y], 3), i] for y in range(y0, y1 + 1)]
        if i and y0 - 1 in v and y0 - 1 in vals[i - 1]:
            both[y0] = (vals[i - 1][y0 - 1], v[y0 - 1])
    if [p[0] for p in pts] != list(range(pts[0][0], pts[-1][0] + 1)):
        raise ValueError("eras overlap or leave a gap")
    return pts, both


EXPORTS_ONLY = {1962}


def breaks(pts, both, flow="exports"):
    """[[year, text]] of the breaks inside the line's years, with the year before on both definitions where known."""
    out = []
    for y, text in BREAKS.items():
        if pts[0][0] < y <= pts[-1][0] and (flow == "exports" or y not in EXPORTS_ONLY):
            a, b = both.get(y, (None, None))
            out.append([y, text.format(a=f"{a:.1f}%", b=f"{b:.1f}%") if a is not None else text.split("; ")[0]])
    return out


def sources_of(eras):
    ids = [s for _, _, spec in eras for s in (spec[0] + [spec[1]] if isinstance(spec, tuple) else spec)]
    out = []
    for sid in ids:
        src = next(v for k, v in sorted(SOURCES.items(), key=lambda kv: -len(kv[0])) if sid.startswith(k))
        out += [src] if src not in out else []
    if "annual_abstract_sitc_uk" in out:
        out.insert(out.index("annual_abstract_sitc_uk") + 1, "annual_abstract_classes_uk")
    return out


NOTE = ("{what} as a share of all {flow}, {y0}-{y1}, joined from the era graphs: the Statistical Abstract to 1938, the "
        "Annual Abstract of Statistics 1939-1974 and the Growth Lab's SITC Rev. 2 shares from 1975 (gold left out). "
        "The goods are {defs}; each definition differs a little from the one before (mostly it is wider), so the "
        "line may step at the marked breaks without anything changing there. Values at the prices of the time (a falling share can mean lower prices "
        "as well as smaller quantities); {basis}. {at}. HMRC's graphs since 2000 take the nearest headings of the old "
        "articles and are much narrower, so they are not joined.")
BASIS = {"exports": "exports of United Kingdom produce to 1961, with re-exports from 1962",
         "imports": "imports valued at the port of arrival (c.i.f.)"}


def write(log=print):
    out, label = [], {}
    for gid, name, flow, eras, defs in JOINED:
        pts, both = join(eras)
        sid = f"{PREFIX}{gid}_uk"
        with open(DATA / f"{sid}.csv", "w", newline="") as f:
            w = csv.writer(f)
            w.writerow(["year", "value", "era"])
            w.writerows([y, v, f"{eras[e][0]}-{eras[e][1]}"] for y, v, e in pts)
        v = {p[0]: p[1] for p in pts}
        years = [y for y in (pts[0][0], 1913, 1938, 1974, 1999, pts[-1][0]) if y in v]
        label[sid] = name
        row = _row(sid, "", name, f"% of {flow}", sources_of(eras), "United Kingdom", unit="%")
        del row["hidden"]
        row.update(breaks=breaks(pts, both, flow), zero=True,
                   note=NOTE.format(what=name, flow=flow, y0=pts[0][0], y1=pts[-1][0], defs=defs, basis=BASIS[flow],
                                    at=f"{name}: " + ", ".join(f"{v[y]:.1f}% in {y}" for y in years)))
        out.append(row)
        log(f"{sid}: {len(pts)} years, breaks " + ", ".join(str(b[0]) for b in row["breaks"]))
    x, m, g, r = out
    x.update(title="Main exports, share of all UK exports, 1846-2024", models=[m["id"]])
    g.update(title="Main imports, share of all UK imports, 1854-2024", models=[r["id"]])
    for s, t in ((m, x["title"]), (r, g["title"])):          # drawn on the graph above, not on their own
        s.update(title=f"{s['label']}, share of UK {s['unit_long'][5:]} ({t[-9:]})", hidden=True,
                 note=s["note"][s["note"].index("The goods are"):].split("; each definition")[0] + ", joined and "
                      "with the breaks as in the note above. " + s["note"].split(". ")[-2] + ".")
    path = DATA.parent / "series.json"
    keep = [s for s in json.loads(path.read_text()) if not s["id"].startswith(PREFIX)]
    path.write_text(json.dumps(keep + out, ensure_ascii=False, indent=1))
    return out


if __name__ == "__main__":
    write(lambda m: print(m, file=sys.stderr, flush=True))
