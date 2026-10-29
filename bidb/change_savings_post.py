"""Savings banks 1939-1975 (roadmap C5e2b2b2b3b2b), read by bidb.change_savings: the Annual Abstract of Statistics'
"National savings" tables read from the page images of Nos. 86 (1938-1949, table 286 p. 257, leaf 267), 88 (table 310
p. 291, leaf 303), 92 (table 320 p. 277, leaf 289), 96 (table 324 p. 280, leaf 292), 99 (table 340 p. 284, leaf 296), 104
(table 325 p. 281, leaf 295), 108 (table 335 pp. 316-317, leaves 332-333) and 112 (1964/65-1974/75, table 361 pp.
347-348, leaves 365-366) → `savings_banks_annual_uk.csv`: every printed figure, one row per edition, item and year,
£ million (a blank value is a printed dash). Receipts, repayments and interest are for years ended 31 March (1938/39 →
1939), amounts remaining invested at 31 March.

Items: `received_`, `paid_`, `interest_` and `due_` (amount remaining invested) followed by `total` (none for interest),
`po` (Post Office Savings Bank, from 1969 the National Savings Bank, ordinary accounts), `po_investment` (investment
accounts, from June 1966), `tsb` (trustee savings banks, ordinary and special investment departments together, to No.
92), `tsb_ord` and `tsb_special` (from No. 96), and the other national savings: `nsc` (certificates; `paid_nsc` is the
principal; from No. 96 `paid_nsc_principal`, `paid_nsc_interest`), `defence` (`paid_defence_before`/`_maturity`),
`premium` (premium savings bonds, from November 1956), `development` (national development bonds, from May 1964),
`bsb` (British savings bonds), `saye_dept`, `saye_tsb` (Save As You Earn, with `_interest`), `stock` / `other`
(securities on the Post Office register).

`check`: every printed total against its parts (within the rounding of the parts), each savings bank's amount at 31
March from the year before and the year's receipts, interest and repayments (within £1 million but `UNBALANCED`), the
savings-bank figures of overlapping editions equal but the `REVISED` (mostly the last year of an edition), every year
1939-1975 printed. Other items are not compared across editions: No. 96 redefined the certificates' interest and
repayments, No. 104 revised the certificates' accrued interest.
"""
import csv

from .change_firms import DATA

SOURCE = DATA / "savings_banks_annual_uk.csv"
FIRST, LAST = 1939, 1975
BANKS = ("po", "po_investment", "tsb", "tsb_ord", "tsb_special")
# (bank, year): why the amount does not follow from the year before and the year's movements within £1 million
SRB = "the flows exclude Service release benefits and withdrawals from Service release benefit accounts (to March 1949)"
UNBALANCED = {("tsb", 1942): "Eire banks left out from 1941/42 (£2.4 million at 31 March 1941)",
              **{("po", y): SRB for y in (1946, 1947, 1948, 1949)},
              **{("po", y): "not explained in the footnotes" for y in (1943, 1944, 1945, 1952, 1953, 1954, 1957,
                                                                          1969)},
              ("tsb", 1965): "not explained in the footnotes"}
# (item, year): (edition, the later edition that revised it)
REVISED = {("due_po", 1946): (88, 92), ("due_po", 1947): (88, 92), ("due_po", 1948): (88, 92),
           ("due_po", 1949): (86, 88), ("paid_po", 1949): (86, 88), ("received_po", 1949): (86, 88),
           ("paid_po", 1951): (88, 92), ("received_po", 1951): (88, 92),
           ("due_tsb_ord", 1959): (96, 99), ("received_tsb_ord", 1959): (96, 99),
           **{(i, 1971): (108, 112) for i in ("due_po", "due_po_investment", "interest_po_investment",
                                               "interest_tsb_ord", "interest_tsb_special", "paid_po",
                                               "paid_po_investment", "received_po", "received_po_investment",
                                               "received_tsb_ord")}}


def load():
    """[{edition (int), leaf, page, table, item, year (int), value (£ million; 0.0 for a printed dash)}]."""
    with open(SOURCE, newline="") as f:
        return [dict(r, edition=int(r["edition"]), year=int(r["year"]), value=float(r["value"] or 0))
                for r in csv.DictReader(f)]


def _cells(rows):
    """{(edition, year): {item: value}}."""
    out = {}
    for r in rows:
        out.setdefault((r["edition"], r["year"]), {})[r["item"]] = r["value"]
    return out


def sum_problems(rows):
    bad = []
    for (ed, y), items in sorted(_cells(rows).items()):
        for kind in ("received", "paid", "due"):
            if f"{kind}_total" not in items:
                continue
            parts = [v for i, v in items.items() if i.startswith(kind + "_") and i != f"{kind}_total"]
            if abs(sum(parts) - items[f"{kind}_total"]) > (len(parts) + 1) * 0.05 + 1e-6:
                bad.append(f"No. {ed} {y} {kind}: parts add to {sum(parts):.1f}, total {items[f'{kind}_total']}")
    return bad


def bank(items, kind, name):
    """A bank's figure in one edition and year; `tsb` is the two departments together where printed apart."""
    v = items.get(f"{kind}_{name}")
    if v is None and name == "tsb" and f"{kind}_tsb_ord" in items:
        v = items[f"{kind}_tsb_ord"] + items.get(f"{kind}_tsb_special", 0)
    return v


def balances(rows):
    """[(bank, edition, year, printed amount - computed amount)] for every year an edition prints with the year
    before."""
    cells, out = _cells(rows), []
    for (ed, y), items in sorted(cells.items()):
        prev = cells.get((ed, y - 1))
        if not prev:
            continue
        for b in BANKS:
            vals = [bank(prev, "due", b)] + [bank(items, k, b) for k in ("received", "interest", "paid", "due")]
            if None not in vals:
                out.append((b, ed, y, round(vals[4] - (vals[0] + vals[1] + vals[2] - vals[3]), 1)))
    return out


def balance_problems(rows):
    return [f"{b} No. {ed} {y}: amount differs by {d:+.1f} from the year before and the year's movements"
            for b, ed, y, d in balances(rows) if abs(d) > 1.0 and (b, y) not in UNBALANCED]


def overlap_problems(rows):
    by, bad = {}, []
    for r in sorted(rows, key=lambda r: r["edition"]):
        if r["item"].split("_", 1)[1] in BANKS:
            by.setdefault((r["item"], r["year"]), []).append(r)
    for key, rs in by.items():
        for a, b in zip(rs, rs[1:]):
            if a["value"] != b["value"] and REVISED.get(key) != (a["edition"], b["edition"]):
                bad.append(f"{key}: No. {a['edition']} {a['value']}, No. {b['edition']} {b['value']}")
    return bad


def check(rows=None):
    rows = rows or load()
    have = {r["year"] for r in rows if r["item"] == "due_po"}
    return (sum_problems(rows) + balance_problems(rows) + overlap_problems(rows)
            + [f"{y}: no amount printed" for y in range(FIRST, LAST + 1) if y not in have])


def latest(rows=None):
    """{(item, year): value} from the latest edition that prints it."""
    return {(r["item"], r["year"]): r["value"] for r in sorted(rows or load(), key=lambda r: r["edition"])}


def values(item, rows=None, first=FIRST):
    """{year: £ million} of one item from `latest`, from `first` (31 March 1938 is printed only by No. 86)."""
    return {y: v for (i, y), v in sorted(latest(rows).items()) if i == item and y >= first}


def tsb_both(rows=None):
    """{year: £ million}: the trustee banks' two departments together at 31 March."""
    best = latest(rows)
    return {y: round(best[("due_tsb_ord", y)] + best[("due_tsb_special", y)], 1) if ("due_tsb_ord", y) in best
            else best[("due_tsb", y)] for y in range(FIRST, LAST + 1)}


if __name__ == "__main__":
    print("\n".join(check()) or "all checks pass")
