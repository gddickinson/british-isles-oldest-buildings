"""Patents per year for "Change over time" (roadmap C5a), from the Intellectual Property Office (OGL) alone.

- "British patent numbers 1617-1852 (old series)": the first number of each decade (five years from 1800) in Bennet
  Woodcroft's numbering of the patents granted before the 1852 Act, so patents granted per year in each period
  (England and Wales; the Commonwealth's patents of 1649-60 were never numbered, none were granted in 1710).
- "Patent applications filed and patents granted each year 1852 to 1915": both, yearly.
- "British patent numbers 1916-1981" and "... 1979 to present day": the first number published in each year, so
  specifications published per year (from 1916 nearly all of them granted patents) and, under the 1977 Act,
  applications published per year.
- "Patents, trade marks and designs: monthly statistics 1995-2025": applications, grants by the IPO, and European
  patents granted by the EPO for the UK, summed by calendar year; "Facts and figures" 2019 and 2025 for the
  applications published 2011-2025 and the last year.

The IPO pages of 2011-13 are read from the Internet Archive. Bottomley's yearly counts for England, Scotland and Ireland
1700-1851 are copyright (no licence on Our World in Data's copy), so they are cited in the note, not drawn.

    python -m bidb.change_patents   → data/curated/change/data/patents_*.csv + series.json entries
                                      (then python -m bidb.change_series)
"""
import collections
import html
import json
import re
import sys

from .change_firms import DATA
from .change_registers import _csv, _download, _row, xlsx_rows

ARCHIVE = "https://web.archive.org/web/20130115203307/http://www.ipo.gov.uk/types/patent/p-about/p-whatis/p-oldnumbers/"
PAGES = {k: f"{ARCHIVE}p-oldnumbers-{k}.htm" for k in ("1617", "1852", "1916", "1979")}
MONTHLY_URL = "https://assets.publishing.service.gov.uk/media/68d115b2e65dc716bfb1dbb6/Monthly-Stats-1995-to-2025.xlsx"
FF2019_URL = "https://assets.publishing.service.gov.uk/media/5ed4ad3bd3bf7f4607b90adc/data-download-2019.xlsx"
FF2025_URL = ("https://assets.publishing.service.gov.uk/media/6a54db32a4890e65cce64dc5/"
              "ipo-facts-and-figures-data-download-2025.xlsx")
SPECS = (1917, 1978)     # years of the 1916 series counted: in 1916 the applications of 1915 and before were still
                         # published under their old numbers; from 1979 the 1977 Act's applications are published too


def cells(page):
    """The table cells of an archived IPO page as one list of strings."""
    t = re.sub(r"(?s)<script.*?</script>|<style.*?</style>", "", page)
    return [html.unescape(re.sub(r"<[^>]+>", "", c)).strip() for c in re.findall(r"(?s)<td[^>]*>(.*?)</td>", t)]


def old_series(page):
    """[(year, first patent number of that year, or None)] from the 1617-1852 page. The 1710 row gives the last patent
    of 1709 (none were granted in 1710) and 1852 the last under the old law, so both are returned as the number after."""
    out = []
    c = [x for x in cells(page) if x]
    for y, v in zip(c, c[1:]):
        if not re.fullmatch(r"1[678]\d\d", y) or not re.match(r"No \d|\*$", v):
            continue
        m = re.match(r"No (\d+)/", v)
        n = int(m.group(1)) if m else None
        out.append((int(y), n + 1 if n and v.endswith("*") else n))
    return sorted(out)


def per_period(rows):
    """[(middle year, patents a year)] between successive first numbers; a period with no number (the Commonwealth)
    is merged into the one before it."""
    rows = [r for r in rows if r[1] is not None]
    out = []
    for (a, n), (b, m) in zip(rows, rows[1:]):
        years = b - a if b != 1852 else b - a + 0.75          # the old law ran to 1 October 1852
        out.append((round((a + b - 1) / 2), round((m - n) / years, 1)))
    return out


def yearly_1852(page):
    """{year: (applications, granted)} 1853-1915; "1852/3" (1 October 1852 to the end of 1853) is given to 1853."""
    c = [x for x in cells(page) if x]
    out = {}
    for i, x in enumerate(c):
        if re.fullmatch(r"1852/3|18[5-9]\d|19(0\d|1[0-5])", x) and all(v.isdigit() for v in c[i + 1:i + 5]):
            out[1853 if x == "1852/3" else int(x)] = (int(c[i + 1]), int(c[i + 3]))
    return out


def first_numbers(page):
    """{year: first GB number published} from the 1916-1981 or 1979- page (its "20010" is 2010)."""
    c = [x for x in cells(page) if x]
    out = {}
    for y, v in zip(c, c[1:]):
        if re.fullmatch(r"\d{4,5}", y) and re.fullmatch(r"GB\d+", v):
            out[int(y[:2] + y[-2:])] = int(v[2:])
    return out


def published(firsts):
    """{year: numbers published in the year} from the first number of each year and the next."""
    ys = sorted(firsts)
    return {a: firsts[b] - firsts[a] for a, b in zip(ys, ys[1:]) if b == a + 1}


def monthly(path):
    """{year: [applications, grants by the IPO, EP(UK) grants by the EPO]} for whole years of the monthly tables."""
    out, months = collections.defaultdict(lambda: [0, 0, 0]), collections.Counter()
    for sheet, cols in (("Table 1 - Filings", [3]), ("Table 2 - Registrations", [3, 4])):
        for r in xlsx_rows(path, sheet, "ABCDE"):
            m = re.fullmatch(r"[A-Z][a-z]{2} (\d{4})", r[0].strip())
            if not m:
                continue
            y = int(m.group(1))
            for k, col in enumerate(cols):
                out[y][0 if sheet.startswith("Table 1") else 1 + k] += int(float(r[col]))
            months[y] += 1
    return {y: v for y, v in out.items() if months[y] == 24}      # 12 months in each table


def summary(path, sheet="Table 1", cols="ABCDEFGHIJK"):
    """{year: {"applications", "publications", "grants"}} from Table 1 of a Facts and figures workbook (2019 layout:
    right and kind in two columns; 2025 layout: "Patents applications2,3" in one)."""
    rows = xlsx_rows(path, sheet, cols)
    head = next(r for r in rows if sum(bool(re.fullmatch(r"20\d\d", x)) for x in r) >= 3)
    years = {i: int(x) for i, x in enumerate(head) if re.fullmatch(r"20\d\d", x)}
    out, right = collections.defaultdict(dict), ""
    for r in rows:
        right = r[0].strip() or right
        label = " ".join(x for x in r[:2] if x).lower()
        kind = next((k for k in ("applications", "publications", "grants") if k in label), None)
        if right.lower().startswith("patent") and kind:
            for i, y in years.items():
                if r[i].strip().isdigit():
                    out[y][kind] = int(r[i])
    return dict(out)


NOTE = ("Patents granted each year. To 1852 (England and Wales): the patents granted under the old law in each decade "
        "(five years from 1800), from the first number of each period in Woodcroft's numbering, as a yearly average "
        "drawn at the middle of the period; the Commonwealth's patents (1649-60) were never numbered, so the 1640s and "
        "1650s show almost none, and none were granted in 1710. From the 1852 Act (United Kingdom): the applications "
        "of each year that were granted (1852/3 is the fifteen months from 1 October 1852, drawn at 1853). {s0}-{s1}: "
        "patent specifications published in the year, from the first number of each year (after 1916 \"generally "
        "only granted patents were published\"; until the Second World War some foreign applications were laid open "
        "and numbered too; 1916 is left out, as earlier applications were still published under their old numbers). "
        "From 1995: patents granted by the IPO (2025, when a new patents system began, from Facts and figures), "
        "with the European patents granted for the UK by the European Patent Office, more than the IPO's in every "
        "year, as a third line. No counts are drawn for 1979-94 (see the graph of applications published). The applications line shows the jump of 1884, when the "
        "Patents, Designs and Trade Marks Act 1883 came into force: {a1883:,} applications in 1883, {a1884:,} in "
        "1884. Bottomley (2014) counts the English, Scottish and Irish patents separately for 1700-1851 (Scotland and "
        "Ireland had their own patents until 1852); his yearly figures are not open, so they are not drawn. The IPO "
        "says its statistics \"should not be used alone to describe the level of innovation in the UK\".")
PUB_NOTE = ("Patent applications published each year under the Patents Act 1977, eighteen months after their priority "
            "date: 1979-2010 from the first number published in each year (GB2000001 on 4 January 1979), 2011-15 from "
            "the IPO's Facts and figures 2019 and 2016-25 from Facts and figures 2025. Where the sources overlap they "
            "differ by under {diff}%. About half of the applications filed are published; the rest are withdrawn "
            "first.")
SOURCES = ["ipo_patent_numbers", "ipo_patents_1852_1915", "ipo_monthly_stats", "ipo_facts_figures"]


def series(old, early, specs, recent, ff, pub_numbers):
    """The points of each line: granted, applications, EP(UK) grants, applications published."""
    last = max(recent)
    granted = per_period(old) + [(y, g) for y, (_, g) in sorted(early.items())] \
        + [(y, n) for y, n in sorted(specs.items()) if SPECS[0] <= y <= SPECS[1]] + [(y, v[1]) for y, v in sorted(recent.items())]
    apps = [(y, a) for y, (a, _) in sorted(early.items())] + [(y, v[0]) for y, v in sorted(recent.items())]
    for y in sorted(ff):                                     # the whole year after the monthly tables end
        if y > last and {"applications", "grants"} <= set(ff[y]):
            granted.append((y, ff[y]["grants"]))
            apps.append((y, ff[y]["applications"]))
    ep = [(y, v[2]) for y, v in sorted(recent.items())]
    pub = sorted({**{y: n for y, n in pub_numbers.items() if y < min(ff)},
                  **{y: v["publications"] for y, v in ff.items() if "publications" in v}}.items())
    return granted, apps, ep, pub


def write(granted, apps, ep, pub, early, diff, log=print):
    for sid, pts in (("patents_granted_uk", granted), ("patents_applications_uk", apps), ("patents_ep_uk", ep),
                     ("patents_published_uk", pub)):
        _csv(sid, pts)
    region = "England and Wales to 1852, then the United Kingdom"
    rows = [
        _row("patents_granted_uk", "Patents granted per year", "Granted (IPO)", "patents granted in the year",
             SOURCES, region, NOTE.format(s0=SPECS[0], s1=SPECS[1], a1883=early[1883][0], a1884=early[1884][0]),
             ["patents_applications_uk", "patents_ep_uk"], unit="patents"),
        _row("patents_applications_uk", "Patent applications per year", "Applications filed", "patent applications filed in the year",
             SOURCES, region, unit="patents"),
        _row("patents_ep_uk", "European patents granted for the UK", "European patents for the UK (EPO)",
             "European patents granted for the UK by the EPO in the year", SOURCES[2:3], region, unit="patents"),
        _row("patents_published_uk", "Patent applications published per year", "Applications published (IPO)",
             "patent applications published in the year", ["ipo_patent_numbers", "ipo_facts_figures"], "United Kingdom",
             PUB_NOTE.format(diff=diff), unit="patents"),
    ]
    path = DATA.parent / "series.json"
    keep = [s for s in json.loads(path.read_text()) if not s["id"].startswith("patents_")]
    path.write_text(json.dumps(keep + rows, ensure_ascii=False, indent=1))
    log(f"graphs: 2 (4 series); granted {granted[0][0]}–{granted[-1][0]}, published {pub[0][0]}–{pub[-1][0]}")


def run(log=print):
    page = {k: _download(u, f"ipo_numbers_{k}.html", log).read_text(errors="replace") for k, u in PAGES.items()}
    old, early = old_series(page["1617"]), yearly_1852(page["1852"])
    specs = published(first_numbers(page["1916"]))
    pub_numbers = published(first_numbers(page["1979"]))
    recent = monthly(_download(MONTHLY_URL, "ipo_monthly_1995_2025.xlsx", log))
    ff19 = summary(_download(FF2019_URL, "ipo_facts_figures_2019.xlsx", log))
    ff25 = summary(_download(FF2025_URL, "ipo_facts_figures_2025.xlsx", log))
    ff = {**ff19, **ff25}
    log(f"old series {old[0][0]}–{old[-1][0]}, 1852 table {min(early)}–{max(early)}, specifications "
        f"{min(specs)}–{max(specs)}, published {min(pub_numbers)}–{max(pub_numbers)}, monthly {min(recent)}–{max(recent)}, "
        f"Facts and figures {min(ff)}–{max(ff)}")
    pubs = [(y, "numbers", pub_numbers[y], ff19[y]["publications"]) for y in pub_numbers if y in ff19]
    pubs += [(y, "2019 edition", ff19[y]["publications"], ff25[y]["publications"]) for y in ff19 if y in ff25]
    others = [(y, "monthly applications", recent[y][0], ff[y]["applications"]) for y in recent if y in ff]
    others += [(y, "monthly grants", recent[y][1], ff[y]["grants"]) for y in recent if y in ff]
    for y, what, a, b in pubs + others:
        log(f"  check {y} {what}: {a:,} against {b:,} in Facts and figures ({(a - b) / b * 100:+.1f}%)")
    diff = max(abs(a - b) / b * 100 for *_, a, b in pubs)
    write(*series(old, early, specs, recent, ff, pub_numbers), early, max(1, round(diff + 0.5)), log)


if __name__ == "__main__":
    run(lambda m: print(m, file=sys.stderr, flush=True))
