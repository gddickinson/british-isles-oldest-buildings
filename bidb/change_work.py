"""Occupations by sector for "Change over time" (roadmap C5c): the share of people in work in farming, fishing and
mining (primary), making and building (secondary) and services (tertiary), on one definition throughout (mining with
farming, as the ONS and Keibek count it).

- ONS, Long-term trends in UK employment 1861-2018 (OGL), Figure 2a: UK shares 1920-1938 and 1948-2016 (from the Bank
  of England's Millennium of Macroeconomic Data); used to 1977.
- ONS workforce jobs by SIC 2007 section (OGL; LMS series, also JOBS02), June each year 1978-2026: A-B, C-F, G-T.
  Over 1978-2016 they differ from Figure 2a by at most `compare` points (a later vintage of the same figures).
- CSO CNNL1 (CC BY 4.0): Ireland (the state) at each census 1926-1996; mining moved from industry to the primary sector.
  Then CNA26 (censuses 2002-2016, by industrial group) and F7040 (2011-2022, by detailed NACE group; usually resident
  and present only), the industry not stated left out; the two agree within `compare_ie` points in 2011 and 2016.
- Keibek 2017 (quoted per figure in estimates.json): England and Wales 1601-1851, men and women (Table 20), and the
  male estimates for 1381 and c.1525 (Tables 22-23), drawn as estimate dots.

    python -m bidb.change_work   → data/curated/change/data/work_*.csv + series.json entries
                                   (then python -m bidb.change_series)
"""
import csv
import json
import re
import time

from .change_firms import DATA
from .change_registers import _csv, _download, _row

ONS_FIG = ("https://www.ons.gov.uk/generator?uri=/economy/nationalaccounts/uksectoraccounts/compendium/economicreview/"
           "april2019/longtermtrendsinukemployment1861to2018/a6452817&format=csv")
LMS_URL = ("https://www.ons.gov.uk/generator?format=csv&uri=/employmentandlabourmarket/peopleinwork/"
           "employmentandemployeetypes/timeseries/{cdid}/lms")
CSO_URL = "https://ws.cso.ie/public/api.restful/PxStat.Data.Cube_API.ReadDataset/{table}/CSV/1.0/en"
CNA26_PRIMARY = {"Agriculture, forestry and fishing", "Mining, quarrying and turf production"}
CNA26_SECONDARY = {"Manufacturing industries", "Electricity, gas and water supply", "Construction"}
NOT_STATED = "Industry not stated"
SECTORS = ["primary", "secondary", "tertiary"]
LMS = {"primary": ["jwr5", "jwr6"], "secondary": ["jwr7", "jwr8", "jwr9", "jws2"], "tertiary": ["jwt8"]}
LMS_TOTAL = "dydc"
FIRST_LMS = 1978
ESTIMATES = DATA.parent / "estimates.json"


def ons_figure(path):
    """{year: (primary, secondary, tertiary)} from the Figure 2a CSV; the war years (blank) are left out."""
    out = {}
    with open(path, newline="", encoding="utf-8-sig") as f:
        for r in csv.reader(f):
            if len(r) == 4 and re.fullmatch(r"\d{4}", r[0]) and all(x.strip() for x in r[1:]):
                out[int(r[0])] = tuple(float(x) for x in r[1:])
    return out


def lms(path):
    """{year: thousands} from the yearly rows of an ONS time-series CSV (for workforce jobs, the June figure)."""
    with open(path, newline="", encoding="utf-8-sig") as f:
        return {int(r[0]): float(r[1]) for r in csv.reader(f)
                if len(r) == 2 and re.fullmatch(r"\d{4}", r[0]) and r[1].strip()}


def lms_shares(series):
    """{year: (primary, secondary, tertiary) % of all workforce jobs} from {cdid: {year: thousands}}."""
    total = series[LMS_TOTAL]
    years = sorted(set(total).intersection(*(series[c] for cs in LMS.values() for c in cs)))
    return {y: tuple(round(sum(series[c][y] for c in LMS[s]) / total[y] * 100, 2) for s in SECTORS) for y in years}


def cso(path):
    """{year: (primary, secondary, tertiary) % of the population at work}, Ireland (the state), all persons."""
    n = {}
    with open(path, newline="", encoding="utf-8-sig") as f:
        for r in csv.DictReader(f):
            if r["County"] == "State" and r["Sex"] == "All Persons" and r["VALUE"].strip():
                n.setdefault(int(r["Year"]), {})[r["Industrial Group"]] = int(r["VALUE"])
    out = {}
    for y, g in sorted(n.items()):
        prim = g["Agriculture"] + g["Mining"]
        sec = g["Industry"] - g["Mining"]
        assert g["Agriculture"] + g["Industry"] + g["Services"] == g["All Industries"], y
        out[y] = tuple(round(v / g["All Industries"] * 100, 2) for v in (prim, sec, g["Services"]))
    return out


def _shares(prim, sec, ter):
    total = prim + sec + ter
    return tuple(round(v / total * 100, 2) for v in (prim, sec, ter))


def cso_cna26(path):
    """{year: shares} from CNA26 (censuses 2002-2016, all aged 15 and over at work), industry not stated left out."""
    n = {}
    with open(path, newline="", encoding="utf-8-sig") as f:
        for r in csv.DictReader(f):
            if r["Age Group"] == "15 years and over" and r["Sex"] == "Both sexes":
                n.setdefault(int(r["Year"]), {})[r["Industrial Group"]] = int(r["VALUE"])
    out = {}
    for y, g in sorted(n.items()):
        stated = g["All industries"] - g[NOT_STATED]
        prim = sum(g[k] for k in CNA26_PRIMARY)
        sec = sum(g[k] for k in CNA26_SECONDARY)
        out[y] = _shares(prim, sec, stated - prim - sec)
    return out


def cso_f7040(path):
    """{year: shares} from F7040's detailed groups, in NACE order: primary to 09, making and building to 43."""
    rows = {}
    with open(path, newline="", encoding="utf-8-sig") as f:
        for r in csv.DictReader(f):
            if r["Means of Travel"] == "All means of travel":
                rows.setdefault(int(r["Census Year"]), []).append((r["Detailed Industrial Group"], int(r["VALUE"])))
    out = {}
    for y, g in sorted(rows.items()):
        names = [n for n, _ in g]
        i1 = names.index("Mining support service activities (09)") + 1
        i2 = names.index("Other specialised construction activities (439)") + 1
        i3 = names.index(NOT_STATED)
        parts = [sum(v for _, v in g[a:b]) for a, b in ((0, i1), (i1, i2), (i2, i3))]
        assert sum(parts) + g[i3][1] == g[-1][1], y               # the groups add up to the total at work
        out[y] = _shares(*parts)
    return out


def compare_ie(cna, det):
    """The largest difference (points) between CNA26 and F7040 in the census years both give."""
    both = sorted(set(cna) & set(det))
    return max(abs(cna[y][i] - det[y][i]) for y in both for i in range(3)), both


def compare(fig, now):
    """The largest difference (points) between Figure 2a and the workforce jobs shares in the years both give."""
    both = [y for y in fig if y in now]
    return max(abs(fig[y][i] - now[y][i]) for y in both for i in range(3)), min(both), max(both)


def joined(fig, now):
    """The UK line: Figure 2a before 1978, workforce jobs from 1978."""
    return {**{y: v for y, v in fig.items() if y < FIRST_LMS}, **{y: v for y, v in now.items() if y >= FIRST_LMS}}


def estimates():
    """{sector: [(year, value, low, high, label)]} from Keibek's figures in estimates.json."""
    out = {}
    for m in json.loads(ESTIMATES.read_text())["models"]:
        if m["id"].startswith("work_") and m["id"].endswith("_keibek2017"):
            sec = m["id"].split("_")[1]
            out[sec] = [(p["year"], p["value"], p["low"], p["high"], f"{m['short']}, {p['note']}") for p in m["points"]]
    return out


def _est_csv(sid, rows):
    with open(DATA / f"{sid}.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["year", "value", "low", "high", "label"])
        w.writerows(["" if x is None else x for x in r] for r in rows)


TITLES = {"primary": ("Working in farming, fishing and mining", "farming, fishing, forestry and mining"),
          "secondary": ("Working in making and building", "manufacturing, construction and the utilities"),
          "tertiary": ("Working in services", "services (trade, transport, finance, public services and the rest)")}
NOTE = ("Share of people in work in {what}. United Kingdom: the ONS's yearly shares 1920-1977 (from the Bank of "
        "England's Millennium of Macroeconomic Data; none for 1939-47), then workforce jobs by industry from {first} "
        "(June each year), which differ from the earlier figures by at most {diff} points over {c0}-{c1}. Ireland (the "
        "state): the CSO's census counts 1926-{ie_last} (from 2002 those whose industry was not stated left out; 2022 "
        "from the table of those usually resident and present, within {ie_diff} points of the full count in 2011 and "
        "2016). Dots: Keibek's estimates for England and Wales, men and women "
        "1601-1851, and men only for 1381 (Smith's range from the poll tax) and c.1525 (between the muster lists and "
        "coroners' reports). Mining counts with farming throughout. Northern Ireland is in the UK line. {facts}")


def _facts(sec, uk, ie, est):
    i = SECTORS.index(sec)
    e = {r[0]: r[1] for r in est}
    if sec == "primary":
        return (f"In 1601 about {e[1601]:.0f}% of the adult labour force of England and Wales worked on the land or in "
                f"mines, {e[1851]:.1f}% in 1851; {uk[1920][i]:.1f}% of the UK's in 1920 and {uk[max(uk)][i]:.1f}% in "
                f"{max(uk)}. Ireland: {ie[1926][i]:.1f}% in 1926, {ie[1996][i]:.1f}% in 1996, "
                f"{ie[max(ie)][i]:.1f}% in {max(ie)}.")
    if sec == "secondary":
        peak = max((y for y in uk), key=lambda y: uk[y][i])
        return (f"Keibek puts making and building at {e[1601]:.1f}% in 1601 and {e[1701]:.1f}% in 1701, above "
                f"farming and mining from the 1670s, before the factories. The UK's share peaked at {uk[peak][i]:.1f}% in {peak} and was "
                f"{uk[max(uk)][i]:.1f}% in {max(uk)}. Ireland: {ie[1926][i]:.1f}% in 1926, {ie[1996][i]:.1f}% in "
                f"1996, {ie[max(ie)][i]:.1f}% in {max(ie)}.")
    return (f"Services grew almost without a break: {e[1601]:.1f}% in 1601 and {e[1851]:.1f}% in 1851 (England and "
            f"Wales), {uk[1920][i]:.1f}% of UK workers in 1920 and {uk[max(uk)][i]:.1f}% in {max(uk)}. Ireland: "
            f"{ie[1926][i]:.1f}% in 1926, {ie[1996][i]:.1f}% in 1996, {ie[max(ie)][i]:.1f}% in {max(ie)}.")


def write(uk, ie, est, diff, c0, c1, ie_diff=0.0, log=print):
    rows = []
    for i, sec in enumerate(SECTORS):
        _csv(f"work_{sec}_uk", [(y, v[i]) for y, v in sorted(uk.items())])
        _csv(f"work_{sec}_ie", [(y, v[i]) for y, v in sorted(ie.items())])
        _est_csv(f"work_{sec}_est", est[sec])
        title, what = TITLES[sec]
        main = _row(f"work_{sec}_uk", title, "United Kingdom", "% of people in work",
                    ["ons_longterm_employment", "ons_workforce_jobs", "cso_cnnl1", "cso_census_industry",
                     "est_work_keibek2017"],
                    "United Kingdom; Ireland; England and Wales (estimates)",
                    NOTE.format(what=what, first=FIRST_LMS, diff=f"{diff:.2f}", c0=c0, c1=c1, ie_last=max(ie),
                                ie_diff=f"{ie_diff:.2f}",
                                facts=_facts(sec, uk, ie, est[sec])),
                    [f"work_{sec}_ie", f"work_{sec}_est"], unit="%")
        main["gap"] = 5                                       # 1939-47 dotted
        ire = _row(f"work_{sec}_ie", f"{title}: Ireland", "Ireland (census)", "% of people at work", ["cso_cnnl1", "cso_census_industry"],
                   "Ireland (the state)", unit="%")
        dots = _row(f"work_{sec}_est", f"{title}: estimates", "England and Wales (Keibek)", "% of the labour force",
                    ["est_work_keibek2017"], "England and Wales", unit="%")
        dots["style"] = "estimates"
        for r in (main, ire, dots):
            r["zero"] = True
        rows += [main, ire, dots]
    path = DATA.parent / "series.json"
    keep = [s for s in json.loads(path.read_text()) if not s["id"].startswith("work_")]
    path.write_text(json.dumps(keep + rows, ensure_ascii=False, indent=1))
    log(f"graphs: 3 ({len(rows)} series); UK {min(uk)}-{max(uk)}, Ireland {min(ie)}-{max(ie)}; Figure 2a and "
        f"workforce jobs differ by at most {diff:.2f} points over {c0}-{c1}")


def _ons(url, name, log):
    for attempt in range(4):                     # the ONS answers 429 to quick requests
        try:
            return _download(url, name, log, "work")
        except Exception as e:
            if "429" not in str(e) or attempt == 3:
                raise
            time.sleep(20)


def run(log=print):
    fig = ons_figure(_ons(ONS_FIG, "ons_fig2a.csv", log))
    cdids = [c for cs in LMS.values() for c in cs] + [LMS_TOTAL]
    now = lms_shares({c: lms(_ons(LMS_URL.format(cdid=c), f"lms_{c}.csv", log)) for c in cdids})
    ie = cso(_download(CSO_URL.format(table="CNNL1"), "cso_cnnl1.csv", log, "work"))
    cna = cso_cna26(_download(CSO_URL.format(table="CNA26"), "cso_cna26.csv", log, "work"))
    det = cso_f7040(_download(CSO_URL.format(table="F7040"), "cso_f7040.csv", log, "work"))
    ie_diff, both = compare_ie(cna, det)
    ie.update(cna)
    ie.update({y: v for y, v in det.items() if y > max(cna)})
    diff, c0, c1 = compare(fig, now)
    write(joined(fig, now), ie, estimates(), diff, c0, c1, ie_diff, log)
    log(f"Ireland: CNA26 and F7040 differ by at most {ie_diff:.2f} points in {both}")


if __name__ == "__main__":
    run()
