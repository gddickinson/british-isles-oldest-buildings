"""Country banks (roadmap C5e2b2b2b1): graphs "Country banks in England and Wales, 1809-1832" and "Country bank
failures, 1809-1830", from J. W. Gilbart, The History and Principles of Banking (3rd edition, London: Longman, 1837;
Gilbart died in 1863, public domain), read from the page images (Internet Archive `historyprinciple00gilb`):

- Table I, p. 110 (leaf 125): licences issued to country bankers and commissions of bankruptcy issued against country
  banks, 1809-1832 (bankruptcies printed as dashes for 1831-1832) → `banks_gilbart_1837_table1.csv`;
- Table II, p. 111 (leaf 126): country banks in England and Wales licensed to issue promissory notes, and their
  partners, by county, for the licence years 1811-12 to 1818-19 (Stamp Office return of 1 May 1819) →
  `banks_gilbart_1837_table2.csv` (dashes as 0), drawn at the first year of each.

`check` tests every county column against the printed total: the banks of 1815-16 add to 644 against 643 printed
(`KNOWN`; the column read twice from a zoomed crop, its partners add exactly).

    python -m bidb.change_banks      check, write the CSVs and series.json rows, then run bidb.change_series
"""
import csv

from .change_firms import DATA
from .change_registers import _row
from .change_wages import write

LICENCES = DATA / "banks_gilbart_1837_table1.csv"
COUNTIES = DATA / "banks_gilbart_1837_table2.csv"
TOTAL = "Total"
# (year, column): (sum of the counties, printed total)
KNOWN = {(1815, "banks"): (644, 643)}


def licences():
    """[(year, licences, bankruptcies or None)] from Table I."""
    with open(LICENCES, newline="") as f:
        return [(int(r["year"]), int(r["licences"]), int(r["bankrupts"]) if r["bankrupts"] else None)
                for r in csv.DictReader(f)]


def counties():
    """{county: {year: (banks, partners)}} from Table II, with the printed `Total`."""
    out = {}
    with open(COUNTIES, newline="") as f:
        for r in csv.DictReader(f):
            out.setdefault(r["county"], {})[int(r["year"])] = (int(r["banks"]), int(r["partners"]))
    return out


def check(c=None, lic=None):
    """Problems: a county column that does not add to its printed total (but `KNOWN`), a county or year missing,
    a year with more banks than partners, or more banks licensed than licences issued."""
    c = c or counties()
    bad = []
    years = sorted(c[TOTAL])
    for county, by_year in c.items():
        if sorted(by_year) != years:
            bad.append(f"{county}: years {sorted(by_year)}")
    for y in years:
        for i, col in enumerate(("banks", "partners")):
            parts = sum(v[y][i] for k, v in c.items() if k != TOTAL)
            printed = c[TOTAL][y][i]
            if parts != printed and KNOWN.get((y, col)) != (parts, printed):
                bad.append(f"{y} {col}: counties add to {parts:,}, printed {printed:,}")
        banks, partners = c[TOTAL][y]
        if banks > partners:
            bad.append(f"{y}: more banks than partners")
    issued = {y: n for y, n, _ in (lic or licences())}
    bad += [f"{y}: {c[TOTAL][y][0]} banks licensed, {issued[y]} licences" for y in years if c[TOTAL][y][0] > issued[y]]
    return bad


NOTE = ("Country banks (outside London) in England and Wales, from J. W. Gilbart's History and Principles of Banking "
        "(3rd edition, 1837, pp. 110-111). From 1808 a bank issuing its own notes had to take out a yearly licence, so "
        "the licences count only banks of issue, and not exactly: \"a bank that issues notes in several places, must "
        "take out a licence for each place\" (up to four), and \"banks that do not issue notes do not take out a "
        "licence\". Licences rose from {l1809} in 1809 to {lmax} in {ymax}, fell to {l1817} in 1817, "
        "stayed between 765 and 809 until 1826, dropped to {l1827} in 1827 and were {l1832} in 1832. The second line is the Stamp Office's own "
        "count of banks licensed, by county, for the licence years 1811-12 to 1818-19 (drawn at the first year): "
        "{b1811} banks with {p1811:,} partners in 1811-12, {b1812} in 1812-13, {b1817} in 1817-18, about three "
        "partners a bank throughout; Yorkshire had the most ({york} in 1811-12), Devon {devon}, Gloucestershire "
        "{glos} and Somerset {som}; Carnarvonshire and Anglesey none. The printed total for 1815-16 is 643, one fewer "
        "than its counties (644). Gilbart on the years before: \"very few country banks existed previous to the "
        "American war ... they received a severe check in the year 1793, when twenty-two became bankrupt\"; and after: "
        "\"According to the Post-office Directory for 1834, the number of private country banks, and branches of "
        "private banks in England and Wales is 638; and the number of joint-stock banks and their branches is 106.\"")
FAIL_NOTE = ("Commissions of bankruptcy issued against country banks in England and Wales each year, from the same "
             "table of Gilbart's (1837, p. 110; none given for 1831-1832). {total} in 1809-1830: {war} in 1814-1816 and "
             "{crisis} in the crisis of 1825-1826; {y1810} in 1810. Gilbart counts 22 country banks bankrupt in 1793.")


def series(lic=None, c=None):
    """({series id: {year: value}}, series.json rows)."""
    lic, c = lic or licences(), c or counties()
    issued = {y: n for y, n, _ in lic}
    failed = {y: b for y, _, b in lic if b is not None}
    banks = {y: v[0] for y, v in c[TOTAL].items()}
    ymax = max(issued, key=issued.get)
    first = min(banks)
    note = NOTE.format(l1809=issued[1809], lmax=issued[ymax], ymax=ymax, l1817=issued[1817], l1827=issued[1827], l1832=issued[1832],
                       b1811=banks[1811], p1811=c[TOTAL][1811][1], b1812=banks[1812], b1817=banks[1817],
                       york=c["Yorkshire"][first][0], devon=c["Devonshire"][first][0],
                       glos=c["Gloucestershire"][first][0], som=c["Somersetshire"][first][0])
    fail_note = FAIL_NOTE.format(total=sum(failed.values()), war=sum(failed[y] for y in (1814, 1815, 1816)),
                                 crisis=failed[1825] + failed[1826], y1810=failed[1810])
    src = ["gilbart_1837_banks"]
    rows = [_row("banks_country_licences_ew", "Country banks in England and Wales, 1809-1832", "licences issued",
                 "licences to issue notes", src, "England and Wales", note, ["banks_country_banks_ew"],
                 unit="licences"),
            _row("banks_country_banks_ew", "Country banks licensed (Stamp Office)", "banks licensed",
                 "banks licensed to issue notes", src, "England and Wales", unit="banks"),
            _row("banks_country_failures_ew", "Country bank failures, 1809-1830", "commissions of bankruptcy",
                 "commissions of bankruptcy against country banks", src, "England and Wales", fail_note,
                 unit="banks")]
    return {"banks_country_licences_ew": issued, "banks_country_banks_ew": banks,
            "banks_country_failures_ew": failed}, rows


def run(log=print):
    bad = check()
    if bad:
        raise ValueError("; ".join(bad))
    pts, rows = series()
    write(pts, rows)
    for r in rows:
        log(f"{r['id']}: {(r.get('note') or '')[:300]}")


if __name__ == "__main__":
    run()
