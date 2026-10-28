"""Bankers' clearing houses (roadmap C5e2b2b2b3b1, C5e2b2b2b3b2a): graphs "London Bankers' Clearing House: amounts
cleared, 1868-1974" (the total, and from 1902 the town and country clearings, the general clearing from 1939), "London
Bankers' Clearing House at 1974 prices, 1868-1974" (the total over the ONS's long-run RPI) and "Provincial bankers'
clearing houses, 1897-1967" (their total, Manchester and Liverpool); from 1939 from bidb.change_clearing_post (the
Annual Abstract), to 1938 from the Statistical Abstract's tables of amounts cleared,
read from the page images of Nos. 31, 32, 33, 42, 46, 50, 59, 62, 66, 69, 71, 78, 82 and 83 →
`clearing_london_abstract_uk.csv` (one printed row per edition and year: total, six months to 30 June, Stock Exchange
settling or account days, consols settling days and the 4th of each month to No. 66, town, metropolitan and country
clearings from 1902; £ million) and `clearing_provincial_abstract_uk.csv` (the provincial houses and their printed
total; £ million to one decimal).

Nos. 29 and 30 print other totals for the same years (1873: 6,182 against 6,071) with no year end stated; No. 31 labels
its years "ended 31st Dec." and every later edition agrees with it, so the series starts there. `check` tests the
London rows by their parts (town + metropolitan + country = total), the provincial rows by their printed total, every
year printed twice or more against the other editions (London: equal but the `REVISED`; provincial: No. 69 recompiled
them from the London Clearing House's annual statements and revised most years by 0.1, which is allowed across No. 69,
other differences listed in `PROVINCIAL_REVISED`), and that no year is missing.

Each year 1868-1938 from this module's tables (1938's London total 39,611 as No. 83 prints it; the Annual Abstract
prints 39,610), 1939-1974 from the Annual Abstract.

    python -m bidb.change_clearing      check, write the CSVs and series.json rows, then run bidb.change_series
"""
import csv

from . import change_clearing_post as post
from .change_firms import DATA
from .change_prices import rpi
from .change_registers import _row
from .change_wages import write

LONDON = DATA / "clearing_london_abstract_uk.csv"
PROVINCIAL = DATA / "clearing_provincial_abstract_uk.csv"
L_COLS = ("total", "half_year", "stock_exchange", "consols", "fourth", "town", "metropolitan", "country")
TOWNS = ("birmingham", "bradford", "bristol", "hull", "leeds", "leicester", "liverpool", "manchester", "newcastle",
         "nottingham", "sheffield")
FIRST, FIRST_PROVINCIAL, LAST = 1868, 1897, 1938
SOURCE_CHANGE = 69     # provincial figures "compiled from the Annual Statements of the London Bankers' Clearing House"
# (column, year): (earlier edition, later edition) whose London figures differ
REVISED = {("fourth", 1883): ("31", "32")}
# (column, year): editions that differ from the one before, apart from the change of source at No. 69
PROVINCIAL_REVISED = {("birmingham", 1905): "62", ("total", 1905): "62", ("liverpool", 1910): "62",
                      ("total", 1910): "62", ("newcastle", 1910): "66", ("birmingham", 1924): "71",
                      ("total", 1927): "82", ("total", 1929): "82", ("total", 1932): "82"}
# No. 66's 1910 Newcastle 49.4 (total 744.2) is printed by no other edition: Nos. 59, 62 and 69 print 48.4


def _num(v, cast):
    return cast(v) if v != "" else None


def load():
    """(london rows, provincial rows): dicts with edition, page, table, year and the figures (None where blank)."""
    with open(LONDON, newline="") as f:
        lon = [dict(r, year=int(r["year"]), **{c: _num(r[c], int) for c in L_COLS}) for r in csv.DictReader(f)]
    with open(PROVINCIAL, newline="") as f:
        pro = [dict(r, year=int(r["year"]), **{c: _num(r[c], float) for c in TOWNS + ("total",)})
               for r in csv.DictReader(f)]
    return lon, pro


def sum_problems(lon, pro):
    bad = []
    for r in lon:
        if r["town"] is not None:
            s = r["town"] + (r["metropolitan"] or 0) + r["country"]
            if abs(s - r["total"]) > 1:
                bad.append(f"London No. {r['edition']} {r['year']}: parts add to {s:,}, total printed {r['total']:,}")
    for r in pro:
        s = sum(r[c] for c in TOWNS if r[c] is not None)
        if abs(s - r["total"]) > 0.25:
            bad.append(f"provincial No. {r['edition']} {r['year']}: towns add to {s:.1f}, total printed {r['total']}")
    return bad


def _by_year(rows):
    out = {}
    for r in sorted(rows, key=lambda r: int(r["edition"])):
        out.setdefault(r["year"], []).append(r)
    return out


def overlap_problems(lon, pro):
    """Editions printing the same year must agree (each figure against the edition before that prints it)."""
    bad = []
    for y, rs in _by_year(lon).items():
        for c in L_COLS:
            have = [r for r in rs if r[c] is not None]
            for a, b in zip(have, have[1:]):
                if a[c] != b[c] and REVISED.get((c, y)) != (a["edition"], b["edition"]):
                    bad.append(f"London {c} {y}: Nos. {a['edition']} {a[c]:,} and {b['edition']} {b[c]:,}")
    for y, rs in _by_year(pro).items():
        for c in TOWNS + ("total",):
            have = [r for r in rs if r[c] is not None]
            if c == "total":                    # a total covers the towns its edition prints
                have = [r for r in rs if {t for t in TOWNS if r[t] is not None} ==
                        {t for t in TOWNS if rs[-1][t] is not None}]
            for a, b in zip(have, have[1:]):
                across = int(a["edition"]) < SOURCE_CHANGE <= int(b["edition"])
                if abs(a[c] - b[c]) > 0.01 and not across and PROVINCIAL_REVISED.get((c, y)) not in (
                        a["edition"], b["edition"]):
                    bad.append(f"provincial {c} {y}: Nos. {a['edition']} {a[c]} and {b['edition']} {b[c]}")
    return bad


def check(rows=None):
    lon, pro = rows or load()
    bad = sum_problems(lon, pro) + overlap_problems(lon, pro)
    bad += [f"London {y}: not printed" for y in range(FIRST, LAST + 1) if y not in _by_year(lon)]
    bad += [f"provincial {y}: not printed" for y in range(FIRST_PROVINCIAL, LAST + 1) if y not in _by_year(pro)]
    return bad


def latest(rows):
    """{year: row} from the latest edition that prints the year."""
    return {y: rs[-1] for y, rs in _by_year(rows).items()}


def values(rows, col):
    return {y: r[col] for y, r in sorted(latest(rows).items()) if r[col] is not None}


def facts(rows=None):
    lon, pro = rows or load()
    tot = values(lon, "total")
    peak = max(tot, key=tot.get)
    low = min((y for y in tot if y > peak), key=tot.get)
    ptot = values(pro, "total")
    ppeak = max(ptot, key=ptot.get)
    best = latest(lon)
    share = {y: round(100 * best[y]["town"] / best[y]["total"], 1) for y in (1902, 1938)}
    return {"tot": tot, "peak": peak, "low": low, "ptot": ptot, "ppeak": ppeak, "share": share,
            "town": values(lon, "town"), "metro": values(lon, "metropolitan"), "country": values(lon, "country"),
            "man": values(pro, "manchester"), "liv": values(pro, "liverpool"), "best": best}


NOTE = ("Amounts cleared at the London Bankers' Clearing House in each calendar year, in pounds of the time, on a "
        "logarithmic axis: to 1938 from the Statistical Abstract read from the page images (Nos. 31, 32, 33, 42, 46, 50, "
        "59, 62, 66, 69, 71, 78, 82 and 83, each year from the latest edition; every year but 1868 printed by two "
        "editions or more and compared, and from 1902 the town, metropolitan and country clearings checked against "
        "the total), from 1939 from the Annual Abstract of Statistics (Nos. 84, 88, 92, 96, 99, 104, 108, 111 and 112, "
        "every row checked by its parts). The amounts cleared came to £{t1868:,} million in 1868, £{t1913:,} million "
        "in 1913 and, with the prices of the war, £{t1920:,} million in 1920; {peak} (£{tpeak:,} million) was not passed "
        "until {passed}, the slump having taken them down to £{tlow:,} million in {low}. Town clearings were {s1902}% "
        "of the total in 1902 and {s1938}% in 1938; metropolitan clearings (not drawn) are printed from 19 February "
        "1907 (£{m1907:,} million to the end of that year, £{m1938:,} million in 1938). From 28 August 1939, under the "
        "clearing banks' emergency operations, a general clearing took the country and metropolitan clearings and "
        "part of the town clearing (£{g1939:,} million to the end of 1939, £{g1944:,} million in 1944); it was kept "
        "after the operations ended in August 1946, and the town clearing came back to {s1974}% of the total by 1974. "
        "The figures then rose to £{t1960:,} million in 1960 and £{t1974:,} "
        "million in 1974. The credit clearing (established on 20 April 1960, figures from 1 May: £{c1961:,} million in 1961, "
        "£{c1974:,} million in 1974) is not included. The Stock Exchange account days of 1914 are eighteen "
        "settlements (twenty-five or twenty-six in 1922-1923) and its consols settling days seven, January to July. "
        "From 1936 the figures include the District Bank, whose admission 'accounts for part of the increase in "
        "Town and Metropolitan Clearings, but not in Country Clearing' (No. 82). The Annual Abstract warns that the "
        "figures 'are not strictly comparable throughout owing to changes in the composition of the clearings'. "
        "Nos. 29 and 30 print other totals for 1868-1882 with no year end stated; they are not used.")
REAL_NOTE = ("The amounts cleared at the London Bankers' Clearing House (the graph above) at the prices of 1974: each "
             "year's total times the ONS's long-run Retail Prices Index for 1974 over that year's. Prices moved little "
             "before 1914, so the line follows the amounts: £{r1868:,} million in 1868, £{r1913:,} million in 1913. "
             "The rise to 1920 was all prices: at 1974 prices the clearings were £{r1920:,} million, less than in "
             "1913. The clearings at 1974 prices were "
             "highest before the Second World War in {rpeak} (£{rp:,} million), lowest in {rlow} (£{rl:,} million), "
             "back above {rpeak}'s by {rback}, and grew {ratio:.1f} times from 1938 to "
             "1974 against {nominal:.0f} times in pounds of the time. Clearings measure payments between banks, not "
             "output, and the RPI measures what households buy, so the line is a rough guide to the volume of "
             "business, not a measure of it.")
PROVINCIAL_NOTE = ("Amounts cleared at the provincial bankers' clearing houses in each calendar year, £ million, from "
                   "the same tables (in the Statistical Abstract from No. 59, 1897, in the Annual Abstract from No. "
                   "84; each year from the latest edition, every row checked against its printed total; 1939 and "
                   "1940 the sum of the houses, no total being printed). From No. 69 the figures were compiled from "
                   "the London Bankers' Clearing House's annual statements instead of returns from the houses "
                   "themselves, and most years 1905-1924 were revised by about 0.1 (Leeds 1916 from 28.0 to 38.5). "
                   "The total covers more houses over time: Nottingham from 1909 ('no record kept' before), Bradford "
                   "from 1912 (added by No. 71, back to 1912), Hull from its opening on 1 February 1921, Southampton "
                   "from 1945; areas were restricted (Bristol July 1922, Nottingham 1931, Liverpool 1 April 1935, "
                   "Sheffield September 1939, Manchester July 1943) and extended again (Nottingham 5 May, Sheffield "
                   "9 June and Manchester 1 July 1947, Birmingham 1 June 1950); Sheffield's was discontinued from 12 "
                   "December 1940 to 5 January 1941 and Bristol's re-arranged in September 1942. Manchester was the "
                   "largest until 1943 (£{m1897} million in 1897, £{m1920:,} million in 1920, £{m1942} million in 1942, "
                   "£{m1944} million in 1944 after the restriction); Liverpool was the largest from 1944 (£{l1967} "
                   "million in 1967) in every year but {not_liv}. The total was £{p1897} million in 1897, £{p1913} million in 1913, £{p1938:,} "
                   "million in 1938, £{p1944:,} million in 1944 and £{ppeak:,} million at its height in {ppy}. 'All "
                   "provincial clearings, with the exception of the afternoon clearing at Liverpool were abolished and "
                   "transferred to General Clearing from 12 January 1968' (Annual Abstract No. 108); the afternoon "
                   "clearing at Liverpool, not drawn, came to £{a1968} million in 1968 and £{a1974} million in 1974.")


def joined(rows=None, post_rows=None):
    """{series id: {year: value}}: 1868-1938 from the Statistical Abstract, 1939-1974 from the Annual Abstract (the
    country clearings followed by the general clearing from 1939; the provincial houses to 1967)."""
    f, g = facts(rows or load()), post.facts(post_rows or post.load())
    after = lambda d: {y: v for y, v in d.items() if y > LAST}
    return {"clearing_london_uk": {**f["tot"], **after(g["total"])}, "clearing_town_uk": {**f["town"], **after(g["town"])},
            "clearing_country_uk": {**f["country"], **after(g["general"])},
            "clearing_provincial_uk": {**f["ptot"], **after(g["provincial"])},
            "clearing_manchester_uk": {**f["man"], **after(g["man"])},
            "clearing_liverpool_uk": {**f["liv"], **after(g["liv"])}}, f, g


def at_1974(tot, prices):
    return {y: round(v * prices[1974] / prices[y]) for y, v in sorted(tot.items())}


def series(rows=None, post_rows=None, prices=None):
    """({series id: {year: value}}, series.json rows)."""
    pts, f, g = joined(rows, post_rows)
    tot, ptot, man, liv = (pts[k] for k in ("clearing_london_uk", "clearing_provincial_uk", "clearing_manchester_uk",
                                             "clearing_liverpool_uk"))
    real = at_1974(tot, prices or rpi(lambda *a: None))
    pre = {y: v for y, v in real.items() if y < 1939}
    rpeak = max(pre, key=pre.get)
    rlow = min((y for y in real if rpeak < y < 1960), key=real.get)
    peak = max((y for y in tot if y <= LAST), key=tot.get)
    low = min((y for y in tot if peak < y <= LAST), key=tot.get)
    pp = max(ptot, key=ptot.get)
    note = NOTE.format(t1868=tot[1868], t1913=tot[1913], t1920=tot[1920], peak=peak, tpeak=tot[peak],
                       passed=min(y for y in tot if y > peak and tot[y] > tot[peak]), tlow=tot[low], low=low,
                       s1902=f["share"][1902], s1938=f["share"][1938], m1907=f["metro"][1907], m1938=f["metro"][1938],
                       g1939=round(g["general"][1939]), g1944=round(g["general"][1944]),
                       s1974=round(100 * g["town"][1974] / g["total"][1974], 1), t1960=round(tot[1960]),
                       t1974=round(tot[1974]), c1961=round(g["credit"][1961]), c1974=round(g["credit"][1974]))
    rnote = REAL_NOTE.format(r1868=real[1868], r1913=real[1913], r1920=real[1920], rpeak=rpeak, rp=real[rpeak],
                             rlow=rlow, rl=real[rlow], rback=min(y for y in real if y > rlow and real[y] > real[rpeak]),
                             ratio=real[1974] / real[1938], nominal=tot[1974] / tot[1938])
    pnote = PROVINCIAL_NOTE.format(m1897=man[1897], m1920=man[1920], m1942=man[1942], m1944=man[1944],
                                   l1967=round(liv[1967]), not_liv=", ".join(
                                       str(y) for y in sorted(liv) if y >= 1944 and man[y] > liv[y]) or "none", p1897=ptot[1897], p1913=ptot[1913], p1938=ptot[1938],
                                   p1944=ptot[1944], ppeak=round(ptot[pp]), ppy=pp, a1968=round(g["afternoon"][1968]),
                                   a1974=round(g["afternoon"][1974]))
    src = ["stat_abstract_clearing_uk", "annual_abstract_clearing_uk"]
    unit, ul = "£ million", "£ million cleared in the year"
    out = [_row("clearing_london_uk", "London Bankers' Clearing House: amounts cleared, 1868-1974", "total",
                ul, src, "London", note, ["clearing_town_uk", "clearing_country_uk"], unit=unit),
           _row("clearing_town_uk", "Town clearings", "town clearings", ul, src, "London", unit=unit),
           _row("clearing_country_uk", "Country clearings (general clearing from 1939)",
                "country clearings, general clearing from 1939", ul, src, "London", unit=unit),
           _row("clearing_london_real_uk", "London Bankers' Clearing House at 1974 prices, 1868-1974",
                "total at 1974 prices", "£ million cleared in the year, at 1974 prices", src + ["ons_cdko"], "London",
                rnote, unit=unit),
           _row("clearing_provincial_uk", "Provincial bankers' clearing houses, 1897-1967", "all provincial houses",
                ul, src, "England", pnote, ["clearing_manchester_uk", "clearing_liverpool_uk"], unit=unit),
           _row("clearing_manchester_uk", "Manchester clearing house", "Manchester", ul, src, "England", unit=unit),
           _row("clearing_liverpool_uk", "Liverpool clearing house", "Liverpool", ul, src, "England", unit=unit)]
    war = [1939, "From 28 August 1939 the general clearing (the clearing banks' emergency operations) takes the "
                 "country and metropolitan clearings and part of the town clearing"]
    out[0].update(log=True, zero=False)
    out[0]["breaks"] = [[1936, "From 1936 including the District Bank, newly admitted to the London Bankers' "
                               "Clearing House (part of the rise in town and metropolitan clearings)"], war]
    out[3].update(log=True, zero=False)
    out[3]["breaks"] = [war]
    out[4]["breaks"] = [[1909, "From 1909 including Nottingham (no record kept before)"],
                        [1912, "From 1912 including Bradford (added by Statistical Abstract No. 71)"],
                        [1921, "From 1921 including Hull, opened 1 February 1921"],
                        [1943, "Manchester's area restricted in July 1943 (extended again 1 July 1947)"],
                        [1945, "From 1945 including Southampton"]]
    return {**pts, "clearing_london_real_uk": real}, out


def run(log=print):
    bad = check() + post.check()
    if bad:
        raise ValueError("; ".join(bad))
    pts, rows = series()
    write(pts, rows)
    for r in rows:
        log(f"{r['id']}: {(r.get('note') or '')[:700]}")


if __name__ == "__main__":
    run()
