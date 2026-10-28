"""Bank notes in circulation (roadmap C5e2b2b2b2): graphs "Bank notes in circulation, 1846-1922" and "Country bank
notes in England and Wales, 1846-1921", from the Statistical Abstract's table of the average amount of promissory
notes payable to bearer on demand in circulation (returns of the Stamp Office, later the Inland Revenue), read from
the page images of Nos. 8, 13, 26, 41, 46, 59 and 68 → `banknotes_abstract_uk.csv` (one printed row per edition and
date: March, June, September and December of each year; pounds, No. 68 in thousands with the country banks in one
column and Ireland in one).

`check` tests every row by its printed sums (private + joint stock = country banks; Bank of England + country banks +
Scotland + Ireland = the United Kingdom; No. 68 within its rounding), every date 1846-1922 present, and the editions
against each other where they overlap. Three rows do not add up as printed (`KNOWN`): two Bank of England figures
that a later edition corrects, and June 1900, printed the same in Nos. 59 and 62.

    python -m bidb.change_banknotes      check, write the CSVs and series.json rows, then run bidb.change_series
"""
import csv

from .change_firms import DATA
from .change_registers import _row
from .change_wages import write

SOURCE = DATA / "banknotes_abstract_uk.csv"
MONTHS = ("March", "June", "September", "December")
PARTS = ("bank_of_england", "private", "joint_stock", "country", "scotland", "bank_of_ireland", "irish_joint_stock",
         "ireland", "united_kingdom")
FIRST, LAST = 1846, 1922
# (edition, year, month): (sum of the parts, printed total), rows whose printed figures do not add up
KNOWN = {("41", 1893, "December"): (40596269, 40596264),   # No. 46 prints the Bank of England 5 lower
         ("59", 1897, "December"): (42839281, 42839051),   # No. 46 prints the Bank of England 230 lower
         ("59", 1900, "June"): (45902258, 45884258)}       # the same in No. 62


def load():
    """[{edition, year, month, part: value in pounds or None, ...}] in file order (No. 68 multiplied to pounds)."""
    out = []
    with open(SOURCE, newline="") as f:
        for r in csv.DictReader(f):
            k = 1000 if r["unit"] == "thousand" else 1
            row = {"edition": r["edition"], "pages": r["pages"], "year": int(r["year"]), "month": r["month"],
                   "unit": r["unit"], "read": r["read"]}
            for p in PARTS:
                row[p] = int(r[p]) * k if r[p] != "" else None
            if row["ireland"] is None:
                row["ireland"] = row["bank_of_ireland"] + row["irish_joint_stock"]
            out.append(row)
    return out


def _sums(r):
    """(problems of the country column, (parts of the UK, printed UK)) for one row."""
    bad = []
    if r["private"] is not None and r["private"] + r["joint_stock"] != r["country"]:
        bad.append(f"private + joint stock {r['private'] + r['joint_stock']:,}, country printed {r['country']:,}")
    parts = r["bank_of_england"] + r["country"] + r["scotland"] + r["ireland"]
    return bad, (parts, r["united_kingdom"])


def check(rows=None):
    """Problems: a row that does not add up (but `KNOWN`), a date missing, or two editions that differ at a date
    (but where one of them is `KNOWN`; No. 68 against the others to its rounding)."""
    rows = rows or load()
    bad = []
    for r in rows:
        key = (r["edition"], r["year"], r["month"])
        cbad, (parts, printed) = _sums(r)
        bad += [f"{key}: {b}" for b in cbad]
        slack = 2000 if r["unit"] == "thousand" else 0
        if abs(parts - printed) > slack and KNOWN.get(key) != (parts, printed):
            bad.append(f"{key}: parts add to {parts:,}, United Kingdom printed {printed:,}")
    dates = {(r["year"], r["month"]) for r in rows}
    bad += [f"{y} {m}: missing" for y in range(FIRST, LAST + 1) for m in MONTHS if (y, m) not in dates]
    by_date = {}
    for r in rows:
        by_date.setdefault((r["year"], r["month"]), []).append(r)
    cols = ("bank_of_england", "country", "scotland", "ireland", "united_kingdom")
    for (y, m), rs in by_date.items():
        for a, b in zip(rs, rs[1:]):
            if (a["edition"], y, m) in KNOWN or (b["edition"], y, m) in KNOWN:
                continue
            # No. 68 rounds each figure to the thousand and prints the sum of its rounded parts as the total
            slack = 1000 if "thousand" in (a["unit"], b["unit"]) else 0
            diff = [c for c in cols if abs(a[c] - b[c]) > slack * (3 if c == "united_kingdom" else 1)]
            if diff:
                bad.append(f"{y} {m}: Nos. {a['edition']} and {b['edition']} differ in {', '.join(diff)}")
    return bad


def latest(rows=None):
    """{(year, month): row} from the latest edition that prints the date (a `KNOWN` row only when no other does)."""
    out = {}
    for r in sorted(rows or load(), key=lambda r: int(r["edition"])):
        key = (r["year"], r["month"])
        if key not in out or (r["edition"], *key) not in KNOWN:
            out[key] = r
    return out


def yearly(col, rows=None, pounds=False):
    """{year: mean of the four dates} in £ million (or pounds), from `latest` (or the latest edition that prints the
    column: No. 68 does not divide the country banks); years with a date missing left out."""
    rows = rows or load()
    best = latest(r for r in rows if r[col] is not None)
    out = {}
    for y in range(FIRST, LAST + 1):
        vals = [best[(y, m)][col] for m in MONTHS if (y, m) in best]
        if len(vals) == 4 and None not in vals:
            mean = sum(vals) / 4
            out[y] = round(mean) if pounds else round(mean / 1e6, 3)
    return out


NOTE = ("Bank notes in circulation, the mean of four dates a year (the months ended in March, June, September and "
        "December; four-weekly periods from 1908), from the Statistical Abstract's returns of notes payable to bearer "
        "on demand, read from the page images (Nos. 8, 13, 26, 41, 46, 59 and 68, each year from the latest edition; "
        "every row checked against its printed totals). The Bank Charter Act of 1844 barred new banks of issue, so "
        "the Bank of England's notes grew while the country banks' shrank: £{boe1846} million of Bank of England "
        "notes in 1846 against £{cty1846} million of country bank notes in England and Wales, £{boe1913} million and "
        "£{cty1913} million in 1913. Scottish banks issued £{sc1846} million in 1846 and £{sc1913} million in 1913, "
        "the Irish £{ir1846} million and £{ir1913} million. With the war the Bank of England's notes rose to "
        "£{boe1920} million in 1920 (the Treasury's currency notes are in another table of the Abstract, not drawn "
        "here); all notes in the United Kingdom came to £{uk1846} million in 1846, £{uk1913} million in 1913 and "
        "£{uk1920} million in 1920. Three printed rows do not add up: December 1893 and December 1897 (the Bank of "
        "England figure, corrected in the next edition) and June 1900 (parts £{jun1900:,}, total printed "
        "£45,884,258, the same in No. 62).")
COUNTRY_NOTE = ("Notes of the country banks of England and Wales in circulation (the mean of four dates a year), "
                "private and joint stock banks apart to 1911 (No. 68 prints them as one column). After the Act of "
                "1844 no new bank could issue notes and a bank lost its issue when it merged, so "
                "the issue shrank: £{c1846} million in 1846 (private {p1846}, joint stock {j1846}), "
                "£{c1866} million in 1866, £{c1890} million in 1890, £{c1900} million in 1900 and £{c1911} million in "
                "1911 (private {p1911}, joint stock {j1911}). £{m1921:,} remained in March 1921; from June 1921 the "
                "column is blank (the event \"Bank Charter Act and the end of country bank notes\" names the last bank "
                "of issue).")


def series(rows=None):
    """({series id: {year: value}}, series.json rows)."""
    rows = rows or load()
    best = latest(rows)
    boe, cty, sc, ir, uk = (yearly(c, rows) for c in ("bank_of_england", "country", "scotland", "ireland",
                                                      "united_kingdom"))
    priv, js = yearly("private", rows), yearly("joint_stock", rows)
    cty = {y: v for y, v in cty.items() if y <= 1921}
    r1900 = best[(1900, "June")]
    note = NOTE.format(boe1846=f"{boe[1846]:.1f}", cty1846=f"{cty[1846]:.1f}", boe1913=f"{boe[1913]:.1f}",
                       cty1913=f"{cty[1913]:.2f}", sc1846=f"{sc[1846]:.1f}", sc1913=f"{sc[1913]:.1f}",
                       ir1846=f"{ir[1846]:.1f}", ir1913=f"{ir[1913]:.1f}", boe1920=f"{boe[1920]:.0f}",
                       uk1846=f"{uk[1846]:.1f}", uk1913=f"{uk[1913]:.1f}", uk1920=f"{uk[1920]:.0f}",
                       jun1900=r1900["bank_of_england"] + r1900["country"] + r1900["scotland"] + r1900["ireland"])
    cnote = COUNTRY_NOTE.format(c1846=f"{cty[1846]:.2f}", p1846=f"{priv[1846]:.2f}", j1846=f"{js[1846]:.2f}",
                                c1866=f"{cty[1866]:.2f}", c1890=f"{cty[1890]:.2f}", c1900=f"{cty[1900]:.2f}",
                                c1911=f"{cty[1911]:.3f}", p1911=f"{priv[1911]:.3f}", j1911=f"{js[1911]:.3f}",
                                m1921=best[(1921, "March")]["country"])
    src = ["stat_abstract_banknotes_uk"]
    out = [_row("banknotes_boe_uk", "Bank notes in circulation, 1846-1922", "Bank of England", "£ million (yearly "
                "mean)", src, "United Kingdom", note, ["banknotes_scotland_uk", "banknotes_ireland_uk"],
                unit="£ million"),
           _row("banknotes_scotland_uk", "Scottish banks' notes", "Scottish banks", "£ million (yearly mean)", src,
                "Scotland", unit="£ million"),
           _row("banknotes_ireland_uk", "Irish banks' notes", "Irish banks", "£ million (yearly mean)", src,
                "Ireland", unit="£ million"),
           _row("banknotes_country_ew", "Country bank notes in England and Wales, 1846-1921", "all country banks",
                "£ million (yearly mean)", src, "England and Wales", cnote,
                ["banknotes_private_ew", "banknotes_jointstock_ew"], unit="£ million"),
           _row("banknotes_private_ew", "Private banks' notes", "private banks", "£ million (yearly mean)", src,
                "England and Wales", unit="£ million"),
           _row("banknotes_jointstock_ew", "Joint stock banks' notes", "joint stock banks", "£ million (yearly mean)",
                src, "England and Wales", unit="£ million")]
    return {"banknotes_boe_uk": boe, "banknotes_scotland_uk": sc, "banknotes_ireland_uk": ir,
            "banknotes_country_ew": cty, "banknotes_private_ew": priv, "banknotes_jointstock_ew": js}, out


def run(log=print):
    bad = check()
    if bad:
        raise ValueError("; ".join(bad))
    pts, rows = series()
    write(pts, rows)
    for r in rows:
        log(f"{r['id']}: {(r.get('note') or '')[:400]}")


if __name__ == "__main__":
    run()
