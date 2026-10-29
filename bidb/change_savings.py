"""Savings banks (roadmap C5e2b2b2b3a, C5e2b2b2b3b2b): graphs "Savings banks: amount due to depositors, 1846-1975"
(trustee savings banks, the Post Office Savings Bank from 1863 and the trustee banks' special investment departments
from 1924; from 1939 at 31 March from the Annual Abstract, bidb.change_savings_post), "Savings banks by nation,
1846-1898" (England and Wales, Scotland, Ireland: trustee banks and, from 1863, the Post Office) and "Savings bank
accounts open, 1897-1938", to 1938 from the Statistical Abstract's tables of the amount received from, paid to
and due to depositors, read from the page images of Nos. 8, 13, 26, 41, 42, 46, 59, 70 and 83 →
`savings_banks_abstract_uk.csv` (one printed row per edition, bank, year and measure: received, interest, paid, due,
accounts, dormant, opened, closed, transferred; England and Wales or the four nations and the United Kingdom to 1898,
the United Kingdom alone from No. 59; No. 83 in thousands).

`check` tests every row by its nations (they add to the United Kingdom; Post Office capital "computed" to a pound or
two), each year's amount due against the year before (due = due before + received + interest - paid, exact wherever
interest is printed or included: the Post Office throughout, the trustee banks from 1877), the editions against each
other where they overlap, and No. 83's accounts by their movements (open = open before + opened - closed -
transferred). Printed rows that do not add up are `KNOWN`; figures an edition revised are `REVISED`.

    python -m bidb.change_savings      check, write the CSVs and series.json rows, then run bidb.change_series
"""
import csv

from . import change_savings_post as post
from .change_firms import DATA
from .change_registers import _row
from .change_wages import write

SOURCE = DATA / "savings_banks_abstract_uk.csv"
NATIONS = ("england_wales", "england", "wales", "scotland", "ireland")
FIRST = {"trustee": 1846, "post_office": 1863, "trustee_special": 1924}
LAST = 1938
# (edition, bank, year, measure): (sum of the nations, printed United Kingdom) for rows that do not add up as printed
KNOWN = {("8", "trustee", 1849, "due"): (28536910, 28537010),
         ("26", "post_office", 1864, "due"): (4993034, 4993124)}    # No. 13 prints England and Wales 4,687,893
# (bank, year, measure): editions whose figures differ, the later a revision
REVISED = {("trustee", 1860, "due"): ("8", "13"),          # No. 8: "The Capital for 1860 is an approximation only"
           ("trustee", 1865, "due"): ("13", "26"),
           ("post_office", 1924, "accounts"): ("70", "83"),  # No. 83 counts active accounts after transfers
           ("post_office", 1925, "accounts"): ("70", "83"),  # to the dormant ledgers
           ("trustee", 1924, "accounts"): ("70", "83"),
           ("trustee", 1925, "accounts"): ("70", "83")}
# (bank, year): accounts that do not follow from the movements: coupon accounts left out from 1933 (No. 83 note a)
ACCOUNTS_BREAK = {("post_office", 1933)}


def load():
    """[{edition, pages, table, bank, year, measure, nation: pounds or None, ..., united_kingdom, unit, read}] with
    figures in thousands multiplied to pounds (accounts stay a count)."""
    out = []
    with open(SOURCE, newline="") as f:
        for r in csv.DictReader(f):
            k = 1000 if r["unit"] == "thousand" and r["measure"] in ("received", "interest", "paid", "due") else 1
            row = {"edition": r["edition"], "pages": r["pages"], "table": r["table"], "bank": r["bank"],
                   "year": int(r["year"]), "measure": r["measure"], "unit": r["unit"], "read": r["read"]}
            for c in NATIONS + ("united_kingdom",):
                row[c] = int(r[c]) * k if r[c] != "" else None
            out.append(row)
    return out


def _slack(*rows):
    """Rounding allowed between figures: two pounds of a computed capital, two units of a thousand."""
    return 2000 if any(r["unit"] == "thousand" for r in rows) else 2


def nation_problems(rows):
    bad = []
    for r in rows:
        parts = [r[c] for c in NATIONS if r[c] is not None]
        if not parts:
            continue
        key = (r["edition"], r["bank"], r["year"], r["measure"])
        slack = 2 if r["bank"] == "post_office" else 0
        if abs(sum(parts) - r["united_kingdom"]) > slack and KNOWN.get(key) != (sum(parts), r["united_kingdom"]):
            bad.append(f"{key}: nations add to {sum(parts):,}, United Kingdom printed {r['united_kingdom']:,}")
    return bad


def latest(rows=None):
    """{(bank, year, measure): row} from the latest edition that prints it."""
    out = {}
    for r in sorted(rows or load(), key=lambda r: int(r["edition"])):
        out[(r["bank"], r["year"], r["measure"])] = r
    return out


def balance_problems(rows):
    """Each year's amount due from the year before, wherever interest is printed or included in the receipts."""
    best, bad = latest(rows), []
    for (bank, y, m), r in best.items():
        prev = best.get((bank, y - 1, "due"))
        if m != "due" or not prev:
            continue
        rec, paid = best[(bank, y, "received")], best[(bank, y, "paid")]
        interest = best.get((bank, y, "interest"))
        if bank != "post_office" and not interest:       # trustee banks before 1877: interest not printed
            continue
        calc = prev["united_kingdom"] + rec["united_kingdom"] - paid["united_kingdom"]
        calc += interest["united_kingdom"] if interest else 0
        if abs(calc - r["united_kingdom"]) > _slack(r, prev):
            bad.append(f"{bank} {y}: due {r['united_kingdom']:,}, the year before and the year's movements give {calc:,}")
    return bad


def overlap_problems(rows):
    """Editions that print the same figure must agree. Receipts are compared with the interest added, since the
    Post Office's receipts include interest to 1896 and No. 83 counts the trustee banks' dividends as receipts."""
    by, bad = {}, []
    for r in rows:
        m = "received" if r["measure"] == "interest" else r["measure"]
        eds = by.setdefault((r["bank"], r["year"], m), {})
        if r["edition"] not in eds:
            eds[r["edition"]] = dict(r, measure=m)
        else:                                              # received + interest of the same edition
            cell = eds[r["edition"]]
            for c in NATIONS + ("united_kingdom",):
                if r[c] is not None and cell[c] is not None:
                    cell[c] += r[c]
    for key, eds in by.items():
        rs = sorted(eds.values(), key=lambda r: int(r["edition"]))
        for a, b in zip(rs, rs[1:]):
            if REVISED.get(key) == (a["edition"], b["edition"]) or any(
                    (r["edition"], *key) in KNOWN for r in (a, b)):
                continue
            cols = [c for c in NATIONS + ("united_kingdom",) if a[c] is not None and b[c] is not None]
            slack = _slack(a, b) if a["measure"] != "accounts" else 0
            diff = [c for c in cols if abs(a[c] - b[c]) > slack]
            if diff:
                bad.append(f"{key}: Nos. {a['edition']} and {b['edition']} differ in {', '.join(diff)}")
    return bad


def account_problems(rows):
    """No. 83: accounts open from the year before and the year's openings, closings and transfers."""
    best, bad = latest(rows), []
    for (bank, y, m), r in best.items():
        prev, opened = best.get((bank, y - 1, "accounts")), best.get((bank, y, "opened"))
        if m != "accounts" or not prev or not opened or prev["edition"] != r["edition"] or (bank, y) in ACCOUNTS_BREAK:
            continue
        moved = opened["united_kingdom"] - best[(bank, y, "closed")]["united_kingdom"]
        tr = best.get((bank, y, "transferred"))
        calc = prev["united_kingdom"] + moved - (tr["united_kingdom"] if tr else 0)
        if calc != r["united_kingdom"]:
            bad.append(f"{bank} {y}: {r['united_kingdom']:,} accounts open, the movements give {calc:,}")
    return bad


def check(rows=None):
    """Problems: nations, balances, overlapping editions, account movements, and a year missing."""
    rows = rows or load()
    bad = nation_problems(rows) + balance_problems(rows) + overlap_problems(rows) + account_problems(rows)
    have = {(r["bank"], r["year"], r["measure"]) for r in rows}
    for bank, first in FIRST.items():
        bad += [f"{bank} {y}: no {m}" for y in range(first, LAST + 1) for m in ("received", "paid", "due")
                if (bank, y, m) not in have]
    return bad


def values(bank, measure, rows=None, scale=1e6, digits=3):
    """{year: value} from `latest` (£ million or million accounts by default)."""
    return {y: round(r["united_kingdom"] / scale, digits)
            for (b, y, m), r in sorted(latest(rows).items()) if b == bank and m == measure}


def by_nation(rows=None):
    """{"ew"|"sc"|"ir": {year: £ million}}: amount due in the trustee banks and, from 1863, the Post Office Savings
    Bank, from the latest edition that prints the nations (to 1898)."""
    best = {}
    for r in sorted(rows or load(), key=lambda r: int(r["edition"])):
        if r["measure"] == "due" and any(r[c] is not None for c in NATIONS):
            best[(r["bank"], r["year"])] = r
    out = {"ew": {}, "sc": {}, "ir": {}}
    for (b, y), t in sorted(best.items()):
        if b != "trustee":
            continue
        p = best.get(("post_office", y))
        parts = {"ew": t["england"] + t["wales"] + (p["england_wales"] if p else 0),
                 "sc": t["scotland"] + (p["scotland"] if p else 0), "ir": t["ireland"] + (p["ireland"] if p else 0)}
        for k, v in parts.items():
            out[k][y] = round(v / 1e6, 3)
    return out


def facts(rows=None):
    """Figures quoted in the notes."""
    rows = rows or load()
    tr, po, sp = (values(b, "due", rows) for b in ("trustee", "post_office", "trustee_special"))
    acc = values("post_office", "accounts", rows)
    over = min(y for y in po if po[y] > tr[y])
    low = min((y for y in tr if 1861 <= y <= 1880), key=tr.get)
    dormant = latest(rows)[("post_office", 1909, "dormant")]["united_kingdom"]
    return {"tr": tr, "po": po, "sp": sp, "acc": acc, "tacc": values("trustee", "accounts", rows),
            "over": over, "low": low, "dormant": dormant}


NOTE = ("Amount due to depositors at the end of each year (trustee savings banks on 20 November, the Post Office "
        "Savings Bank on 31 December), from the Statistical Abstract read from the page images (Nos. 8, 13, 26, 41, 42, "
        "46, 59, 70 and 83, each year from the latest edition; every row checked against its nations, and each year "
        "against the year before and the year's receipts, interest and payments wherever interest is printed). "
        "Government stock held for depositors is not included. The trustee banks held £{tr1846} million in 1846 and "
        "£{tr1861} million in 1861, then fell to £{trlow} million in {low} while the Post Office Savings Bank, opened "
        "in 1861 (see the event), grew; the Post Office passed them in {over} (£{poover} million against £{trover} million) "
        "and held £{po1913} million in 1913, the trustee banks £{tr1913} million. The Post Office "
        "held £{po1919} million in 1919, a year whose figures include the gratuities paid to demobilised men; the "
        "Irish Free State opened its own Post Office Savings Bank on 1 January 1923. In 1938 the Post Office held "
        "£{po1938} million, the trustee banks' ordinary departments £{tr1938} million and their special investment "
        "departments (open only to ordinary depositors, printed from 1924) £{sp1938} million. Printed as 'capital' "
        "to No. 42 (1894); the trustee banks' interest is printed from 1877 (the rate allowed to trustees fell from 3¼ to 3 "
        "per cent from 20 November 1880).")
POST_NOTE = (" From 1939 the amount at 31 March of each year, from the Annual Abstract of Statistics' tables of national "
             "savings read from the page images (Nos. 86, 88, 92, 96, 99, 104, 108 and 112; every printed total checked "
             "against its parts and each bank's amount against the year before and the year's movements); the Post "
             "Office line is its ordinary accounts (the National Savings Bank from 1969; investment accounts, opened "
             "in 1966, held £{inv1975} million in 1975). The Annual Abstract prints the trustee banks' two departments "
             "together to 1948 (£{both1939} million in 1939, £{both1948} million in 1948), so their lines start again "
             "in 1949. The Post Office Savings Bank held £{po1939} million at 31 March 1939 and £{popeak} million at "
             "its height in {peak}, then fell to £{polow} million in {low} while the "
             "trustee banks grew: their two departments together passed the Post Office's ordinary accounts in "
             "{over} (£{bothover} million against £{poover} million) and held £{both1975} million in 1975 (ordinary "
             "£{tr1975} million, special investment £{sp1975} million).")
NATION_NOTE = ("Amount due to depositors in the trustee savings banks (20 November) and, from 1863, the Post Office "
               "Savings Bank (31 December), by nation, from the same Statistical Abstract tables (printed by nation to "
               "1898; each row checked against the United Kingdom total). Log axis. In 1846 England and Wales held "
               "£{ew1846} million, Scotland £{sc1846} million and Ireland £{ir1846} million; Ireland's deposits fell "
               "to £{irlow} million in {irlowy}. In 1898 England and Wales held £{ew1898} million, Scotland "
               "£{sc1898} million and Ireland £{ir1898} million.")
ACCOUNTS_NOTE = ("Accounts open at the end of each year, from the same tables (printed from No. 59, 1897): "
                 "{po1897} million in the Post Office Savings Bank and {tr1897} million in the trustee banks in 1897, "
                 "{po1938} million and {tr1938} million in 1938. From 1909 the Post Office counts active accounts "
                 "only ({dormant:,} dormant accounts of under £1 untouched for five years in 1909, not distinguished "
                 "before); No. 83's count from 1924 is lower than No. 70's for the same years ({po1924} million against "
                 "{po1924old} million) and leaves out coupon accounts from 1933. The trustee line is the ordinary "
                 "departments.")


def series(rows=None):
    """({series id: {year: value}}, series.json rows)."""
    rows = rows or load()
    f = facts(rows)
    tr, po, sp, acc, tacc = f["tr"], f["po"], f["sp"], f["acc"], f["tacc"]
    old = next(r for r in rows if (r["edition"], r["bank"], r["year"], r["measure"]) == ("70", "post_office", 1924,
                                                                                         "accounts"))
    note = NOTE.format(tr1846=f"{tr[1846]:.1f}", tr1861=f"{tr[1861]:.1f}", trlow=f"{tr[f['low']]:.1f}", low=f["low"],
                       tr1913=f"{tr[1913]:.0f}", over=f["over"],
                       poover=f"{po[f['over']]:.1f}", trover=f"{tr[f['over']]:.1f}", po1913=f"{po[1913]:.0f}",
                       po1919=f"{po[1919]:.0f}", po1938=f"{po[1938]:.0f}", tr1938=f"{tr[1938]:.0f}",
                       sp1938=f"{sp[1938]:.0f}")
    anote = ACCOUNTS_NOTE.format(po1897=f"{acc[1897]:.2f}", tr1897=f"{tacc[1897]:.2f}", po1938=f"{acc[1938]:.2f}",
                                 tr1938=f"{tacc[1938]:.2f}", dormant=f["dormant"], po1924=f"{acc[1924]:.2f}",
                                 po1924old=f"{old['united_kingdom'] / 1e6:.2f}")
    note += post_note()
    nat = by_nation(rows)
    ir_low = min((y for y in nat["ir"] if y < 1863), key=nat["ir"].get)
    nnote = NATION_NOTE.format(**{f"{k}{y}": f"{nat[k][y]:.1f}" for k in nat for y in (1846, 1898)},
                               irlow=f"{nat['ir'][ir_low]:.1f}", irlowy=ir_low)
    src = ["stat_abstract_savings_uk"]
    breaks = [[1909, "From 1909 active accounts only (dormant accounts of under £1 untouched for five years left out: "
                     f"{f['dormant']:,} in 1909)"],
              [1924, "From 1924 Statistical Abstract No. 83's count of active accounts (No. 70 gives "
                     f"{old['united_kingdom']:,} for 1924)"],
              [1933, "From 1933 coupon accounts left out (the coupon system replaced by a stamp savings scheme)"]]
    psrc = src + ["annual_abstract_savings_uk"]
    out = [_row("savings_due_trustee_uk", "Savings banks: amount due to depositors, 1846-1975", "trustee savings banks",
                "£ million at the end of the year (from 1939 at 31 March)", psrc, "United Kingdom", note,
                ["savings_due_po_uk", "savings_due_special_uk"], unit="£ million"),
           _row("savings_due_po_uk", "Post Office Savings Bank", "Post Office Savings Bank",
                "£ million at the end of the year (from 1939 at 31 March)", psrc, "United Kingdom", unit="£ million"),
           _row("savings_due_special_uk", "Trustee banks' special investment departments", "trustee special "
                "investment departments", "£ million at the end of the year (from 1939 at 31 March)", psrc,
                "United Kingdom", unit="£ million"),
           _row("savings_nation_ew", "Savings banks by nation, 1846-1898", "England and Wales",
                "£ million due to depositors at the end of the year", src, "United Kingdom", nnote,
                ["savings_nation_sc", "savings_nation_ir"], unit="£ million"),
           _row("savings_nation_sc", "Savings banks: Scotland", "Scotland", "£ million due to depositors at the end of "
                "the year", src, "Scotland", unit="£ million"),
           _row("savings_nation_ir", "Savings banks: Ireland", "Ireland", "£ million due to depositors at the end of "
                "the year", src, "Ireland", unit="£ million"),
           _row("savings_accounts_po_uk", "Savings bank accounts open, 1897-1938", "Post Office Savings Bank",
                "million accounts open at the end of the year", src, "United Kingdom", anote,
                ["savings_accounts_trustee_uk"], unit="million accounts"),
           _row("savings_accounts_trustee_uk", "Trustee savings bank accounts", "trustee savings banks",
                "million accounts open at the end of the year", src, "United Kingdom", unit="million accounts")]
    out[0]["breaks"] = [[1939, "From 1939 at 31 March of each year (Annual Abstract of Statistics); to 1938 the "
                               "trustee banks at 20 November and the Post Office at 31 December"]]
    out[3]["breaks"] = [[1863, "From 1863 with the Post Office Savings Bank"]]
    out[3]["log"] = True
    out[6]["breaks"] = breaks
    pr = post.load()
    return {"savings_due_trustee_uk": {**tr, **post.values("due_tsb_ord", pr)},
            "savings_due_po_uk": {**po, **post.values("due_po", pr)},
            "savings_due_special_uk": {**sp, **post.values("due_tsb_special", pr)},
            "savings_nation_ew": nat["ew"], "savings_nation_sc": nat["sc"], "savings_nation_ir": nat["ir"],
            "savings_accounts_po_uk": acc, "savings_accounts_trustee_uk": tacc}, out


def post_note(rows=None):
    """The 1939-1975 part of the note, from bidb.change_savings_post."""
    rows = rows or post.load()
    po, both = post.values("due_po", rows), post.tsb_both(rows)
    peak = max(po, key=po.get)
    low = min((y for y in po if y > peak), key=po.get)
    over = min(y for y in both if both[y] > po[y])
    return POST_NOTE.format(inv1975=f"{post.values('due_po_investment', rows)[1975]:.0f}", both1939=f"{both[1939]:.1f}",
                            both1948=f"{both[1948]:.1f}", po1939=f"{po[1939]:.1f}", popeak=f"{po[peak]:,.1f}",
                            peak=peak, polow=f"{po[low]:,.1f}", low=low, over=over, bothover=f"{both[over]:,.1f}",
                            poover=f"{po[over]:,.1f}", both1975=f"{both[1975]:,.1f}",
                            tr1975=f"{post.values('due_tsb_ord', rows)[1975]:,.1f}",
                            sp1975=f"{post.values('due_tsb_special', rows)[1975]:,.1f}")


def run(log=print):
    bad = check() + post.check()
    if bad:
        raise ValueError("; ".join(bad))
    pts, rows = series()
    write(pts, rows)
    for r in rows:
        log(f"{r['id']}: {(r.get('note') or '')[:600]}")


if __name__ == "__main__":
    run()
