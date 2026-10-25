"""Work by sector in Scotland and Ireland for "Change over time" (roadmap C5c2c): one graph per nation, the three sectors
as its lines.

- Booth (1886), Appendix B (2) Scotland and B (3) Ireland (pp. 418-419, 422-423; public domain): the self-supporting
  population 1841-1881 in thousands on Booth's classification (`data/curated/change/data/work_booth_sc.csv`,
  `work_booth_ir.csv`, read from the page images; every subtotal checked by change_work_ew.check_booth), grouped as for
  England and Wales (general labour, the independent and indefinite left out: `left_out`).
- Scotland goes on with the census of 1891 (change_work_sc_1891, on its own classification) and those of 1901 and
  1911 (change_work_sc: the 1911 report's Table D1), grouped line by line, every dealer in services, general labourers
  alone left out; a break at 1891 and another at 1901 (the classification of 1911).
- Ireland goes on with the censuses of 1891, 1901 and 1911 (change_work_ir: the 1881 classification, the lines of
  sub-orders that mix makers and dealers grouped as Scotland's, students and general labourers left out), after a
  break at 1891, then the state's census shares 1926-2022 (the CSO tables read by change_work), after a break: the
  whole island to 1911, the 26 counties from 1926.

Written by change_work.run (`rows`), as series `work_sc_*` and `work_irl_*`.
"""
from . import change_work_ew as ew, change_work_ir as ir, change_work_sc as sc, change_work_sc_1891 as sc91
from .change_firms import DATA
from .change_registers import _csv, _row

BOOTH = {"sc": DATA / "work_booth_sc.csv", "irl": DATA / "work_booth_ir.csv"}
SECTORS = ["primary", "secondary", "tertiary"]
LABELS = {"primary": "Farming, fishing and mining", "secondary": "Making and building", "tertiary": "Services"}
NAMES = {"sc": "Scotland", "irl": "Ireland"}
LEFT_OUT = ["general_labour", "property", "indefinite"]
BREAKS = {"sc": [[1891, "From 1891 the censuses' own lines grouped by the same rule, every dealer in services, general "
                        "labourers alone left out; to 1881 Booth's regrouping"],
                 [1901, "From 1901 the classification of 1911 (1901 regrouped by the census office); 1891 on its own "
                        "classification, gardeners all in farming"]],
          "irl": [[1891, "From 1891 the censuses' own lines grouped by the same rule, every dealer in services, students "
                         "and general labourers alone left out; to 1881 Booth's regrouping"],
                  [1926, "From 1926 the state (26 counties) at the CSO's censuses, by industry, those whose industry was "
                         "not stated left out; to 1911 the whole island, by occupation"]]}


def load(nation):
    """Booth's figures for a nation, checked."""
    b = ew.load_booth(BOOTH[nation])
    bad = ew.check_booth(b)
    if bad:
        raise ValueError(f"Booth, {NAMES[nation]}: " + "; ".join(bad))
    return b


def left_out(b):
    """{year: % of the self-supporting left out} (general labour, property owning and independent, indefinite)."""
    return {y: round(sum(b[k][y] for k in LEFT_OUT) / v * 100, 1) for y, v in sorted(b["self_supporting"].items())}


def series(b, after=None):
    """{sector: [(year, %)]}: Booth's years, then the later censuses (Scotland's, the state's) after them."""
    s = ew.booth_shares(b)
    out = {sec: [(y, v[i]) for y, v in sorted(s.items())] for i, sec in enumerate(SECTORS)}
    for i, sec in enumerate(SECTORS):
        out[sec] += [(y, v[i]) for y, v in sorted((after or {}).items())]
    return out


NOTE = ("Share of the self-supporting population in farming, fishing and mining; making and building; and services "
        "(transport, dealing, commercial, public and professional, and domestic service), from Charles Booth's "
        "regrouping of the censuses of {place} 1841-1881 on one classification (1886), with dealers apart. General "
        "labour, people living on property and those of no stated occupation are left out ({lo} of the self-supporting, "
        "{years}). {extra}The same grouping as the England and Wales dots on the sector graphs. {facts}")
EXTRA = {"sc": ("From 1891 the censuses' own tables, line by line: 1891 on its classification (lines that join makers "
                "and dealers shared out as in 1901), 1901 and 1911 from the 1911 report's Table D1; every dealer in "
                "services, only general labourers left out ({lo_census} of those occupied), so the line starts again "
                "after a break, and again at 1901, where the classification changes. "),
         "irl": ("General labourers, left out, were many in Ireland and most worked on the land, so farming is "
                 "understated there. From 1891 the censuses' own tables, line by line (1891 and 1901 from the 1901 "
                 "General Report, 1911 the four province volumes summed): every dealer in services, lines joining "
                 "makers and dealers shared out as Scotland's in 1901, students and general labourers left out "
                 "({lo_census} of those occupied). From 1926 the line is the state's census shares by industry (as on "
                 "the sector graphs), after a break: the whole island to 1911, the 26 counties from 1926. ")}


def _facts(nation, s):
    v = {sec: dict(pts) for sec, pts in s.items()}
    p, t = v["primary"], v["tertiary"]
    text = (f"Farming, fishing and mining {p[1841]:.1f}% in 1841, {p[1881]:.1f}% in 1881; services {t[1841]:.1f}% and "
            f"{t[1881]:.1f}%.")
    if nation == "sc":
        text += (f" Census: farming, fishing and mining {p[1891]:.1f}% in 1891, {p[1901]:.1f}% in 1901, "
                 f"{p[1911]:.1f}% in 1911; services {t[1891]:.1f}%, {t[1901]:.1f}%, {t[1911]:.1f}%.")
    if nation == "irl":
        last = max(p)
        text += (f" Census: farming, fishing and mining {p[1891]:.1f}% in 1891, {p[1901]:.1f}% in 1901, "
                 f"{p[1911]:.1f}% in 1911; services {t[1891]:.1f}%, {t[1901]:.1f}%, {t[1911]:.1f}%.")
        text += f" The state: farming, fishing and mining {p[1926]:.1f}% in 1926, {p[last]:.1f}% in {last}."
    return text


def rows(ie, log=print):
    """Write the CSVs; the series.json rows of both graphs."""
    from . import change_work_ir_1911 as ir11
    bad = ir.check() + ir.check_lines() + ir11.check()
    if bad:
        raise ValueError("census of Ireland: " + "; ".join(bad))
    out = []
    for nation in ("sc", "irl"):
        b = load(nation)
        s = series(b, {**ir.shares(), **ie} if nation == "irl" else {**sc91.shares(), **sc.shares()})
        lo = left_out(b)
        census_lo = ir.left_out() if nation == "irl" else {**sc91.left_out(), **sc.left_out()}
        lo_census = "-".join(f"{v}%" for v in sorted(census_lo.values(), reverse=True))
        for sec in SECTORS:
            _csv(f"work_{nation}_{sec}", s[sec])
        last = max(y for y, _ in s["primary"])
        main = _row(f"work_{nation}_primary", f"Work by sector: {NAMES[nation]}, 1841-{last}", LABELS["primary"],
                    "% of those in work",
                    ["booth_1886"] + (["census_ir_1891", "census_ir_1901_lines", "census_ir_1911", "cso_cnnl1",
                                       "cso_census_industry"] if nation == "irl"
                                      else ["census_sc_1891", "census_sc_1911"]),
                    NAMES[nation] + (" (the whole island to 1911; the state from 1926)" if nation == "irl" else ""),
                    NOTE.format(place=NAMES[nation], lo=f"{min(lo.values())}-{max(lo.values())}%",
                                years="1841-1881", extra=EXTRA[nation].format(lo_census=lo_census),
                                facts=_facts(nation, s)),
                    [f"work_{nation}_secondary", f"work_{nation}_tertiary"], unit="%")
        main["gap"] = 10                                       # censuses ten years apart; longer gaps dotted
        lines = [_row(f"work_{nation}_{sec}", f"Work by sector: {NAMES[nation]}: {LABELS[sec].lower()}", LABELS[sec],
                      main["unit_long"], main["sources"], main["region"], unit="%") for sec in SECTORS[1:]]
        for r in [main] + lines:
            r["zero"] = True
            r["gap"] = 10
            r["breaks"] = BREAKS[nation]
        out += [main] + lines
        log(f"{NAMES[nation]}: {s['primary'][0][0]}-{last}, left out {lo}")
    return out
