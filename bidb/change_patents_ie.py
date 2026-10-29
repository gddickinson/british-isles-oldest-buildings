"""Patents in Ireland (roadmap C5e2b2b2c): graphs "Patents in Ireland, 2000-2025", "Patents with effect in Ireland,
2001-2025" (European patents beside the Office's) and "Irish patent applications by term, 2001-2025", from the Intellectual Property Office of Ireland's annual reports (the Patents Office's to 2018).

- Every report 2002-2025 prints the national applications received and patents granted by the Office for the year and
  the two before it (full 20-year term, short 10-year term, total; the 2002 report totals only), the applications from
  applicants in the State against the year before, and the European patents granted for Ireland by the EPO (a table
  "Patents granted in <year> having effect in the State" from 2007, a sentence before).
- `data/curated/change/data/patents_ipoi_reports_ie.csv`: one printed figure per row (report year, PDF page, year, measure,
  form: table or text), read from the reports' own text (born-digital PDFs), Irish-language pages included where they
  repeat a table. The site states "All rights, including copyright, in the content and design of these web pages are
  owned or controlled" by the IPOI and no reuse licence, so the figures are cited one by one as facts.
- `check`: each table's totals against its full- and short-term parts; every figure printed twice equal but `KNOWN`;
  every year present. `latest`: each year from the latest report (a table before a sentence, the English page first).
- No counts before 2000: the Controller's reports since 1928 (the Patents Office opened under the Industrial and
  Commercial Property (Protection) Act 1927) are not online, nor the Statistical Abstract of Ireland's earlier
  editions, and WIPO's statistics may not be republished.

    python -m bidb.change_patents_ie    check, write the CSVs and series.json rows, then run bidb.change_series
"""
import csv
from collections import defaultdict

from .change_firms import DATA
from .change_registers import _row
from .change_wages import write

FILE = DATA / "patents_ipoi_reports_ie.csv"
PARTS = (("apps_full", "apps_short", "apps_total"), ("grants_full", "grants_short", "grants_total"))
MEASURES = ("apps_full", "apps_short", "apps_total", "grants_full", "grants_short", "grants_total", "apps_state",
            "ep_granted")
FIRST = {"apps_total": 2000, "grants_total": 2000}       # the 2002 report's table; the rest from 2001
LAST = 2025
# (measure, year): {(report, form, page): value} printed differently from the figure kept
KNOWN = {
    ("apps_state", 2014): {(2014, "text", 13): 263},     # 262 in the 2015 report
    ("apps_state", 2015): {(2015, "text", 15): 289},     # 250 in the 2016 report (and the 2015 report's own chart)
    ("apps_state", 2017): {(2017, "text", 15): 182},     # 183 in the 2018 report
    ("ep_granted", 2010): {(2010, "text", 15): 39538},   # 39,539 in the report's table
    ("ep_granted", 2019): {(2019, "text", 22): 135313},  # 135,374 in the table
    ("ep_granted", 2024): {(2024, "text", 31): 109371},  # 109,390 in the table
    ("grants_full", 2014): {(2014, "table", 41): 79},    # the Irish-language page swaps full and short term
    ("grants_short", 2014): {(2014, "table", 41): 69},
}


def load(path=FILE):
    with open(path, newline="") as f:
        rows = list(csv.DictReader(f))
    for r in rows:
        for k in ("report", "pdf_page", "year", "value"):
            r[k] = int(r[k])
    return rows


def _key(r):
    return r["report"], r["form"], r["pdf_page"]


def _rank(r):
    """Later reports first; within a report a table before a sentence, the lower (English) page first."""
    return -r["report"], r["form"] != "table", r["pdf_page"]


def latest(rows=None):
    """{measure: {year: value}} from the latest report printing each figure."""
    out = defaultdict(dict)
    for r in sorted(rows or load(), key=_rank, reverse=True):
        if r["value"] != KNOWN.get((r["measure"], r["year"]), {}).get(_key(r)):
            out[r["measure"]][r["year"]] = r["value"]
    return dict(out)


def check(rows=None):
    """Problems: totals unlike their parts, figures printed differently (beyond `KNOWN`), years missing."""
    rows = rows or load()
    bad = []
    printed = defaultdict(dict)
    for r in rows:
        if r["measure"] not in MEASURES:
            bad.append(f"unknown measure {r['measure']}")
        printed[(r["report"], r["pdf_page"], r["year"])][r["measure"]] = r["value"]
    for (rep, page, y), m in sorted(printed.items()):
        for full, short, total in PARTS:
            if full in m and m[full] + m[short] != m[total]:
                bad.append(f"report {rep} p{page} {y}: {full} {m[full]} + {short} {m[short]} != {m[total]}")
    kept = latest(rows)
    seen = set()
    for r in rows:
        k = (r["measure"], r["year"])
        known = KNOWN.get(k, {})
        if _key(r) in known:
            seen.add((k, _key(r)))
            if r["value"] != known[_key(r)]:
                bad.append(f"{k} report {r['report']}: {r['value']}, KNOWN says {known[_key(r)]}")
        elif r["value"] != kept[r["measure"]][r["year"]]:
            bad.append(f"{k}: report {r['report']} p{r['pdf_page']} prints {r['value']}, kept "
                       f"{kept[r['measure']][r['year']]}")
    bad += [f"KNOWN {k} {rk} not in the file" for k, v in KNOWN.items() for rk in v if (k, rk) not in seen]
    for m in MEASURES:
        missing = sorted(set(range(FIRST.get(m, 2001), LAST + 1)) - set(kept.get(m, {})))
        if missing:
            bad.append(f"{m}: years missing {missing}")
    return bad


NOTE = ("National patent applications received and patents granted each year by the Patents Office in Kilkenny (\"In "
        "December 2019, the Patents Office changed its name to the 'Intellectual Property Office of Ireland'\", 2019 "
        "report), with the applications from applicants in the State, from the Office's annual reports 2002-2025 "
        "(each prints its year and the two before; the latest report is kept where they differ). Ireland joined "
        "the European Patent Convention in 1992, and \"there was a drop in the annual volume of patent applications "
        "being filed at the Office. The number of applications being received appears to have stabilised at around "
        "25% of the pre - 1992 level\" (2002 report); applications fell from {a2001:,} in 2001 to {a_min} in "
        "{a_min_y}, and those from the State from {s2001:,} to {s_min} in {s_min_y}. In {n_short} of the "
        "{n_years} years more than half of the applications were for short-term patents (see the graph by term). The rises from 2023 are \"due to a "
        "significant rise in applications received from China\" (2023 report): {a2024} applications in 2024, "
        "{s2024} of them from the State. No counts are drawn before 2000: the Controller's reports since the "
        "Office opened under the Industrial and Commercial Property (Protection) Act 1927 (the 2002 report is the "
        "seventy-fifth) are not online. Figures cited from the reports (all rights reserved).")
EP_NOTE = ("European patents granted by the European Patent Office that take effect in Ireland, against the patents "
           "granted by the Irish Office (annual reports 2002-2025), on a scale of powers of ten: \"They have the "
           "same legal status in Ireland as if they had been granted by my Office\" (Controller's report 2002). "
           "They were {ep2001:,} in 2001 and {ep_max:,} at their height in {ep_max_y}; in {last} the Office "
           "granted {g_last} patents against {ep_last:,} European ones. Three reports print a slightly different "
           "figure in the text than in their table (2010, 2019, 2024); the table's is drawn.")
TERM_NOTE = ("National patent applications to the Irish Office by term: full-term patents (20 years) and short-term "
             "patents (10 years) \"under Part II of the 1992 Act, which came into force on 1 August 1992\" (2002 "
             "report). Short-term applications were {short2001} of {a2001:,} in 2001 and {short2024} of "
             "{a2024} in 2024; full-term applications fell from {full2001} in 2001 to "
             "{full_min} in {full_min_y}. The 2018 report gives no reason for that year's {short2018} short-term "
             "applications (from {short2017} in 2017); the rise of 2023 was \"due to a significant rise in "
             "applications received from China\" (2023 report). Of "
             "the patents granted, {gs2002} of {g2002} were short-term in 2002 and {gs_last} of {g_last} in {last}.")


def series(kept=None):
    """({series id: {year: value}}, series.json rows)."""
    k = kept or latest()
    apps, grants, state, ep = k["apps_total"], k["grants_total"], k["apps_state"], k["ep_granted"]
    full, short = k["apps_full"], k["apps_short"]
    lo = lambda d, since=2001: min((v, y) for y, v in d.items() if y >= since)
    ep_max, ep_max_y = max((v, y) for y, v in ep.items())
    a_min, a_min_y = lo(apps)
    s_min, s_min_y = lo(state)
    full_min, full_min_y = lo(full)
    note = NOTE.format(a2001=apps[2001], a_min=a_min, a_min_y=a_min_y, s2001=state[2001], s_min=s_min,
                       s_min_y=s_min_y, a2024=apps[2024], s2024=state[2024],
                       n_short=sum(short[y] * 2 > apps[y] for y in short), n_years=len(short))
    ep_note = EP_NOTE.format(ep2001=ep[2001], ep_max=ep_max, ep_max_y=ep_max_y, last=LAST, g_last=grants[LAST],
                             ep_last=ep[LAST])
    term = TERM_NOTE.format(short2001=short[2001], a2001=apps[2001], short2024=short[2024], a2024=apps[2024],
                            full2001=full[2001],
                            full_min=full_min, full_min_y=full_min_y, short2018=short[2018], short2017=short[2017],
                            gs2002=k["grants_short"][2002], g2002=grants[2002], gs_last=k["grants_short"][LAST],
                            g_last=grants[LAST], last=LAST)
    src, region = ["ipoi_annual_reports"], "Ireland (the state)"
    rows = [_row("ie_patents_applications", "Patents in Ireland, 2000-2025", "Applications (Irish Office)",
                 "national patent applications received in the year", src, region, note,
                 ["ie_patents_granted", "ie_patents_state"], unit="patents"),
            _row("ie_patents_granted", "Patents granted by the Irish Office", "Granted (Irish Office)",
                 "patents granted by the Office in the year", src, region, unit="patents"),
            _row("ie_patents_state", "Patent applications from the State", "Applications from the State",
                 "national patent applications from applicants in the State", src, region, unit="patents"),
            _row("ie_patents_ep", "Patents with effect in Ireland, 2001-2025", "European patents for Ireland (EPO)",
                 "European patents granted by the EPO with effect in Ireland", src, region, ep_note,
                 ["ie_patents_granted"], unit="patents"),
            _row("ie_patents_short", "Irish patent applications by term, 2001-2025", "Short term (10 years)",
                 "short-term patent applications received in the year", src, region, term, ["ie_patents_full"],
                 unit="patents"),
            _row("ie_patents_full", "Full-term patent applications", "Full term (20 years)",
                 "full-term patent applications received in the year", src, region, unit="patents")]
    rows[3]["log"] = True
    points = {"ie_patents_applications": apps, "ie_patents_granted": grants, "ie_patents_state": state,
              "ie_patents_ep": ep, "ie_patents_short": short, "ie_patents_full": full}
    return points, rows


def run(log=print):
    rows = load()
    bad = check(rows)
    if bad:
        raise ValueError("; ".join(bad))
    points, srows = series(latest(rows))
    write(points, srows)
    log(f"{len(rows)} printed figures from {len({r['report'] for r in rows})} reports; {len(srows)} series")
    log(srows[0]["note"][:500])


if __name__ == "__main__":
    run()
