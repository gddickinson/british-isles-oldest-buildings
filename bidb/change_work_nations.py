"""Work by sector in Scotland and Ireland for "Change over time" (roadmap C5c2c): one graph per nation, the three sectors
as its lines.

- Booth (1886), Appendix B (2) Scotland and B (3) Ireland (pp. 418-419, 422-423; public domain): the self-supporting
  population 1841-1881 in thousands on Booth's classification (`data/curated/change/data/work_booth_sc.csv`,
  `work_booth_ir.csv`, read from the page images; every subtotal checked by change_work_ew.check_booth), grouped as for
  England and Wales (general labour, the independent and indefinite left out: `left_out`).
- Ireland goes on with the state's census shares 1926-2022 (the CSO tables read by change_work), after a break: the
  whole island to 1881, the 26 counties from 1926.

Written by change_work.run (`rows`), as series `work_sc_*` and `work_irl_*`.
"""
from . import change_work_ew as ew
from .change_firms import DATA
from .change_registers import _csv, _row

BOOTH = {"sc": DATA / "work_booth_sc.csv", "irl": DATA / "work_booth_ir.csv"}
SECTORS = ["primary", "secondary", "tertiary"]
LABELS = {"primary": "Farming, fishing and mining", "secondary": "Making and building", "tertiary": "Services"}
NAMES = {"sc": "Scotland", "irl": "Ireland"}
LEFT_OUT = ["general_labour", "property", "indefinite"]
BREAK = ("From 1926 the state (26 counties) at the CSO's censuses, by industry, those whose industry was not stated left "
         "out; to 1881 the whole island, Booth's regrouping of the censuses by occupation")


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


def series(b, ie=None):
    """{sector: [(year, %)]}: Booth's years, then the state's (Ireland) after them."""
    s = ew.booth_shares(b)
    out = {sec: [(y, v[i]) for y, v in sorted(s.items())] for i, sec in enumerate(SECTORS)}
    for i, sec in enumerate(SECTORS):
        out[sec] += [(y, v[i]) for y, v in sorted((ie or {}).items())]
    return out


NOTE = ("Share of the self-supporting population in farming, fishing and mining; making and building; and services "
        "(transport, dealing, commercial, public and professional, and domestic service), from Charles Booth's "
        "regrouping of the censuses of {place} 1841-1881 on one classification (1886), with dealers apart. General "
        "labour, people living on property and those of no stated occupation are left out ({lo} of the self-supporting, "
        "{years}). {extra}The same grouping as the England and Wales dots on the sector graphs. {facts}")
EXTRA = {"sc": "",
         "irl": ("General labourers, left out, were many in Ireland and most worked on the land, so farming is "
                 "understated there. From 1926 the line is the state's census shares by industry (as on the sector "
                 "graphs), after a break: the whole island to 1881, the 26 counties from 1926. ")}


def _facts(nation, s):
    v = {sec: dict(pts) for sec, pts in s.items()}
    p, t = v["primary"], v["tertiary"]
    text = (f"Farming, fishing and mining {p[1841]:.1f}% in 1841, {p[1881]:.1f}% in 1881; services {t[1841]:.1f}% and "
            f"{t[1881]:.1f}%.")
    if nation == "irl":
        last = max(p)
        text += f" The state: farming, fishing and mining {p[1926]:.1f}% in 1926, {p[last]:.1f}% in {last}."
    return text


def rows(ie, log=print):
    """Write the CSVs; the series.json rows of both graphs."""
    out = []
    for nation in ("sc", "irl"):
        b = load(nation)
        s = series(b, ie if nation == "irl" else None)
        lo = left_out(b)
        for sec in SECTORS:
            _csv(f"work_{nation}_{sec}", s[sec])
        last = max(y for y, _ in s["primary"])
        main = _row(f"work_{nation}_primary", f"Work by sector: {NAMES[nation]}, 1841-{last}", LABELS["primary"],
                    "% of the self-supporting" if nation == "sc" else "% of those in work",
                    ["booth_1886"] + (["cso_cnnl1", "cso_census_industry"] if nation == "irl" else []),
                    NAMES[nation] + (" (the whole island to 1881; the state from 1926)" if nation == "irl" else ""),
                    NOTE.format(place=NAMES[nation], lo=f"{min(lo.values())}-{max(lo.values())}%",
                                years="1841-1881", extra=EXTRA[nation], facts=_facts(nation, s)),
                    [f"work_{nation}_secondary", f"work_{nation}_tertiary"], unit="%")
        main["gap"] = 10                                       # censuses ten years apart; 1881-1926 dotted
        if nation == "irl":
            main["breaks"] = [[1926, BREAK]]
        lines = [_row(f"work_{nation}_{sec}", f"Work by sector: {NAMES[nation]}: {LABELS[sec].lower()}", LABELS[sec],
                      main["unit_long"], main["sources"], main["region"], unit="%") for sec in SECTORS[1:]]
        for r in [main] + lines:
            r["zero"] = True
            r["gap"] = 10
            if nation == "irl":
                r["breaks"] = [[1926, BREAK]]
        out += [main] + lines
        log(f"{NAMES[nation]}: {s['primary'][0][0]}-{last}, left out {lo}")
    return out
