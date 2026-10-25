"""Companies from the official registers for "Change over time" (roadmap C4b), beside the Wikidata firms of C4a.

- Companies House, Table A8 of "Companies register activities" (OGL): companies incorporated and dissolved each year
  and the size of the register, Great Britain 1939 to 2008-09, United Kingdom from 2009-10.
- Companies House, Free Company Data Product (no re-use conditions): the companies on the register now, counted by
  the year (and decade, by industry from their SIC codes) they were incorporated. Only live companies are in it, so
  set against the incorporations of the same years it shows how few survive.
- Ireland's Companies Registration Office, Company Records (CC BY 4.0): every company registered, with the dissolved
  ones (from the 1960s; earlier dissolved companies are mostly missing), by year registered and dissolved.

The register counts are about a hundred times the Wikidata ones, so they have graphs of their own rather than more
lines on the C4a graphs. Downloads are kept in `<cache>/registers/`; only the yearly counts are written.

    python -m bidb.change_registers   → data/curated/change/data/companies_*.csv + series.json entries
                                        (then python -m bidb.change_series)
"""
import collections
import csv
import io
import json
import re
import sys
import xml.etree.ElementTree as ET
import zipfile

import requests

from .change_firms import DATA, SECTORS
from .config import USER_AGENT, cache_dir

A8_URL = ("https://assets.publishing.service.gov.uk/media/6a3d1a97eaee00074150f4df/"
          "Companies_register_activities_April_2025_to_March_2026.xlsx")
CH_URL = "https://download.companieshouse.gov.uk/BasicCompanyDataAsOneFile-2026-10-01.zip"
CRO_URL = ("https://opendata.cro.ie/dataset/bf6f837d-0946-4c14-9a99-82cd6980c121/resource/"
           "3fef41bc-b8f4-4b10-8434-ce51c29b1bba/download/companies.csv.zip")
LAST = 2025                                   # last whole year (the snapshots are of October 2026)

# Companies Act companies, as counted by Table A8: not partnerships, charitable incorporated organisations,
# registered societies, Royal Charter bodies (whose dates are charters, back to 1327) or overseas entities
COMPANY_TYPES = {"Private Limited Company", "Public Limited Company", "Private Unlimited Company", "Private Unlimited",
                 "Old Public Company", "Community Interest Company",
                 "PRI/LTD BY GUAR/NSC (Private, limited by guarantee, no share capital)",
                 "PRI/LBG/NSC (Private, Limited by guarantee, no share capital, use of 'Limited' exemption)",
                 "PRIV LTD SECT. 30 (Private limited company, section 30 of the Companies Act)"}
CRO_GONE = re.compile(r"dissolved|struck off|ceased|deleted|de-registered|conv\.", re.I)

# SIC 2007 divisions → SECTORS of bidb.change_firms (index); None = not stated (dormant, none given)
_SIC = [((1, 9), 4), ((10, 12), 0), ((13, 17), 5), ((18, 18), 3), ((19, 33), 5), ((35, 39), 2), ((41, 43), 5),
        ((45, 47), 6), ((49, 53), 2), ((55, 56), 0), ((58, 60), 3), ((61, 61), 2), ((62, 63), 7), ((64, 66), 1),
        ((68, 89), 7), ((90, 90), 3), ((91, 97), 7)]
NOT_TRADING = {"74990", "99999"}              # non-trading and dormant companies


def sic_sector(text):
    """SECTORS index for a SicText value such as "62020 - Information technology consultancy activities"."""
    code = text.split(" ", 1)[0]
    if not code.isdigit() or code in NOT_TRADING:
        return None
    div = int(code[:2])
    return next((k for (lo, hi), k in _SIC if lo <= div <= hi), None)


def _download(url, name, log, folder="registers"):
    path = cache_dir() / folder / name
    if path.exists():
        return path
    path.parent.mkdir(parents=True, exist_ok=True)
    log(f"downloading {name}")
    with requests.get(url, headers={"User-Agent": USER_AGENT}, stream=True, timeout=120) as r:
        r.raise_for_status()
        part = path.with_suffix(".part")
        with open(part, "wb") as f:
            for chunk in r.iter_content(1 << 20):
                f.write(chunk)
    part.rename(path)
    return path


def xlsx_rows(path, sheet_name, cols="ABCDEFG"):
    """Rows of one sheet of an .xlsx as lists of strings, one per column of `cols` (stdlib only)."""
    m = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
    rel = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id"
    z = zipfile.ZipFile(path)
    shared = [''.join(t.text or '' for t in si.iter(m + "t"))
              for si in ET.fromstring(z.read("xl/sharedStrings.xml"))]
    targets = {r.get("Id"): r.get("Target") for r in ET.fromstring(z.read("xl/_rels/workbook.xml.rels"))}
    sheet = next(s for s in ET.fromstring(z.read("xl/workbook.xml")).iter(m + "sheet") if s.get("name") == sheet_name)
    rows = []
    for row in ET.fromstring(z.read("xl/" + targets[sheet.get(rel)].lstrip("/").removeprefix("xl/"))).iter(m + "row"):
        cells = {}
        for c in row.iter(m + "c"):
            v = c.find(m + "v")
            text = (shared[int(v.text)] if c.get("t") == "s" else v.text) if v is not None else \
                ''.join(t.text or '' for t in c.iter(m + "t"))
            cells[re.match(r"[A-Z]+", c.get("r")).group()] = text or ""
        rows.append([cells.get(col, "") for col in cols])
    return rows


def a8(path):
    """{year: (register, effective register, incorporations, dissolved)} from Table A8. Financial years ("1986 - 87",
    April to March) are given the year they end in."""
    out = {}
    for r in xlsx_rows(path, "Table A8"):
        m = re.fullmatch(r"(\d{4})(?: - (\d\d))?", r[0].strip())
        if not m or not r[3].strip().isdigit():
            continue
        year = int(m.group(1)) + (1 if m.group(2) else 0)
        out[year] = tuple(int(x) for x in r[1:5])
    return out


def companies_house(path):
    """(live companies by year incorporated, {decade: [all, per sector…]}) from the basic data file."""
    years, decades = collections.Counter(), {}
    z = zipfile.ZipFile(path)
    with io.TextIOWrapper(z.open(z.namelist()[0]), encoding="utf-8", errors="replace", newline="") as f:
        rows = csv.reader(f)
        head = {k.strip(): i for i, k in enumerate(next(rows))}
        cat, inc, sic = head["CompanyCategory"], head["IncorporationDate"], head["SICCode.SicText_1"]
        for r in rows:
            if len(r) < len(head) or r[cat] not in COMPANY_TYPES or not re.fullmatch(r"\d\d/\d\d/\d{4}", r[inc]):
                continue
            year = int(r[inc][-4:])
            if not 1850 <= year <= LAST:
                continue
            years[year] += 1
            row = decades.setdefault(year // 10 * 10, [0] * (1 + len(SECTORS)))
            row[0] += 1
            k = sic_sector(r[sic])
            if k is not None:
                row[1 + k] += 1
    return years, decades


def cro(path):
    """({year: [registered, dissolved, registered that year and still on the register]}, records, records with no
    registration date) from the CRO records."""
    out, total, undated = collections.defaultdict(lambda: [0, 0, 0]), 0, 0
    z = zipfile.ZipFile(path)
    with io.TextIOWrapper(z.open(z.namelist()[0]), encoding="utf-8", newline="") as f:
        for r in csv.DictReader(f):
            reg, gone = r["company_reg_date"][:4], r["comp_dissolved_date"][:4]
            total += 1
            undated += not reg
            if reg.isdigit() and 1850 <= int(reg) <= LAST:      # placeholder dates (1753-01-01) left out
                out[int(reg)][0] += 1
                out[int(reg)][2] += not gone and not CRO_GONE.search(r["company_status"])
            if gone.isdigit() and 1850 <= int(gone) <= LAST:
                out[int(gone)][1] += 1
    return dict(out), total, undated


def _csv(sid, points):
    with open(DATA / f"{sid}.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["year", "value"])
        w.writerows(points)


def _row(sid, title, label, unit_long, sources, region, note=None, models=None, unit="companies"):
    row = {"id": sid, "theme": "Prosperity and work", "title": title, "region": region, "unit": unit,
           "unit_long": unit_long, "label": label, "sources": sources, "file": f"{sid}.csv", "default": False}
    if models:
        row["models"] = models
    if note:
        row["note"] = note
    else:
        row["hidden"] = True
    return row


GB_NOTE = ("Companies incorporated and dissolved each year from Companies House's Table A8: Great Britain to 2008-09, "
           "the United Kingdom from 2009-10 (when Northern Ireland's register joined); calendar years to 1986, then "
           "years ending in March (shown at the year they end in); figures before 2009-10 rounded to the nearest 100. "
           "The third line counts the companies on the register in October 2026 by the year they were incorporated "
           "(Companies House basic data; Companies Act companies only, as in Table A8): of the {inc:,} incorporated "
           "in {y}, {live:,} are still on the register. The Wikidata firms of the other graphs are a few thousand "
           "per decade, about a hundredth of these.")
REGISTER_NOTE = ("Companies on the register of Great Britain (from 2009-10 the United Kingdom) at the end of each "
                 "year, from Companies House's Table A8; the effective register leaves out companies being "
                 "dissolved or liquidated. {first:,} in 1939, {last:,} in 2025-26.")
IE_NOTE = ("Companies registered and dissolved each year in Ireland (the state; Northern Ireland's companies are on "
           "the UK register), from the Companies Registration Office's records of every company, with the dissolved "
           "ones: {all:,} companies. Companies dissolved before the 1960s are mostly missing, so the earlier years "
           "count chiefly the companies that lasted (dissolutions are recorded from {first_gone}; a handful earlier "
           "are not shown), and {undated:,} records have no registration date. The third line counts the companies of each year's "
           "registrations still on the register in October 2026. Contains Irish Public Sector Data licensed under a "
           "Creative Commons Attribution 4.0 International (CC BY 4.0) licence.")
LIVE_NOTE = ("Companies on the UK register in October 2026 by the decade they were incorporated and their industry "
             "(the first SIC code given, sorted into the industries of the Wikidata firms graphs; construction "
             "counts with making things, restaurants with food and drink). Only companies still alive are in the "
             "file, so the early decades show the survivors, not the companies founded then: set these against "
             "the incorporations per year. {none:,} of {all:,} companies are dormant, not trading or give no code "
             "and count in no industry. The 2020s are a part decade.")
LIVE_GRAPHS = [   # title, sector indexes (first is the main line), grouped as the C4a graphs
    ("Companies alive today by decade founded: making, food and drink, mining", [5, 0, 4]),
    ("Companies alive today by decade founded: finance, transport, shops", [1, 2, 6]),
    ("Companies alive today by decade founded: publishing and services", [3, 7]),
]
SOURCES = ["companies_house_a8", "companies_house_basic"]


def write_graphs(table, live_years, live_decades, ireland, ie_counts, log=print):
    """CSVs and series.json entries of the register graphs."""
    ch_years = range(1900, LAST + 1)
    _csv("companies_incorporated_gb", [[y, v[2]] for y, v in sorted(table.items())])
    _csv("companies_dissolved_gb", [[y, v[3]] for y, v in sorted(table.items())])
    _csv("companies_live_by_year_uk", [[y, live_years.get(y, 0)] for y in ch_years])
    _csv("companies_register_gb", [[y, v[0]] for y, v in sorted(table.items())])
    _csv("companies_register_effective_gb", [[y, v[1]] for y, v in sorted(table.items())])
    ie_years = range(1900, LAST + 1)
    first_gone = min(y for y, v in ireland.items() if v[1] >= 100)    # a stray handful before
    _csv("companies_registered_ie", [[y, ireland.get(y, [0])[0]] for y in ie_years])
    _csv("companies_dissolved_ie", [[y, ireland[y][1]] for y in ie_years if y >= first_gone and y in ireland])
    _csv("companies_live_by_year_ie", [[y, ireland.get(y, [0, 0, 0])[2]] for y in ie_years])
    decades = range(1900, LAST // 10 * 10 + 10, 10)
    zero = [0] * (1 + len(SECTORS))
    for _, ks in LIVE_GRAPHS:
        for k in ks:
            _csv(f"companies_live_{_slug(k)}", [[d, live_decades.get(d, zero)[1 + k]] for d in decades])

    y = 1980
    rows = [
        _row("companies_incorporated_gb", "Companies incorporated per year", "Incorporated (Table A8)",
             "companies incorporated in the year", SOURCES, "Great Britain, United Kingdom from 2009-10",
             GB_NOTE.format(inc=table[y][2], y=y, live=live_years[y]),
             ["companies_dissolved_gb", "companies_live_by_year_uk"]),
        _row("companies_dissolved_gb", "Companies dissolved per year", "Dissolved (Table A8)", "companies dissolved in the year", SOURCES, ""),
        _row("companies_live_by_year_uk", "Companies alive today by year incorporated", "Of each year's, still on the register in 2026",
             "companies incorporated in the year and on the register in October 2026", SOURCES, "United Kingdom"),
        _row("companies_register_gb", "Companies on the register", "Total register (Table A8)",
             "companies on the register", SOURCES[:1], "Great Britain, United Kingdom from 2009-10",
             REGISTER_NOTE.format(first=table[1939][0], last=table[max(table)][0]),
             ["companies_register_effective_gb"]),
        _row("companies_register_effective_gb", "Companies on the effective register", "Effective register", "companies on the effective register",
             SOURCES[:1], ""),
        _row("companies_registered_ie", "Companies registered per year: Ireland", "Registered (CRO)",
             "companies registered in the year", ["cro_companies"], "Ireland (the state)",
             IE_NOTE.format(all=ie_counts[0], first_gone=first_gone, undated=ie_counts[1]),
             ["companies_dissolved_ie", "companies_live_by_year_ie"]),
        _row("companies_dissolved_ie", "Companies dissolved per year: Ireland", "Dissolved (CRO)", "companies dissolved in the year", ["cro_companies"], ""),
        _row("companies_live_by_year_ie", "Companies alive today by year registered: Ireland", "Of each year's, still on the register in 2026",
             "companies registered in the year and on the register in October 2026", ["cro_companies"], ""),
    ]
    total = sum(v[0] for v in live_decades.values())
    stated = sum(sum(v[1:]) for v in live_decades.values())
    for title, ks in LIVE_GRAPHS:
        sids = [f"companies_live_{_slug(k)}" for k in ks]
        rows.append(_row(sids[0], title, SECTORS[ks[0]][0], "companies alive in 2026 founded in the decade",
                         SOURCES[1:], "United Kingdom", LIVE_NOTE.format(none=total - stated, all=total), sids[1:]))
        rows += [_row(s, f"Companies alive today: {SECTORS[k][0]}", SECTORS[k][0],
                      "companies alive in 2026 founded in the decade", SOURCES[1:], "United Kingdom")
                 for s, k in zip(sids[1:], ks[1:])]
    for r in rows:                                    # hidden lines share their graph's region
        r["region"] = r["region"] or next(g["region"] for g in rows if r["id"] in g.get("models", []))
    path = DATA.parent / "series.json"
    series = [s for s in json.loads(path.read_text()) if not s["id"].startswith("companies_")]
    path.write_text(json.dumps(series + rows, ensure_ascii=False, indent=1))
    log(f"graphs: {sum(1 for r in rows if not r.get('hidden'))} ({len(rows)} series)")


def _slug(k):
    return re.sub(r"[^a-z]+", "_", SECTORS[k][0].lower().split(",")[0].split(" and ")[0]).strip("_")


def run(log=print):
    table = a8(_download(A8_URL, "ch_activities_2026.xlsx", log))
    log(f"Table A8: {min(table)}–{max(table)}, {len(table)} years")
    live_years, live_decades = companies_house(_download(CH_URL, CH_URL.rsplit("/", 1)[1], log))
    log(f"Companies House: {sum(live_years.values()):,} live companies incorporated 1850–{LAST}")
    ireland, *ie_counts = cro(_download(CRO_URL, "companies.csv.zip", log))
    log(f"CRO: {sum(v[0] for v in ireland.values()):,} registered, {sum(v[1] for v in ireland.values()):,} dissolved")
    write_graphs(table, live_years, live_decades, ireland, ie_counts, log)


if __name__ == "__main__":
    run(lambda m: print(m, file=sys.stderr, flush=True))
