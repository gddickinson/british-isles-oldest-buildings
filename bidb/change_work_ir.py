"""Occupations in Ireland at the censuses of 1891 and 1901 by class, order and sub-order (roadmap C5c2c2c1), read from
page images.

Census of Ireland, 1901, Part II, General Report (Cd. 1190, 1902; public domain; Internet Archive `op1254515-1001`),
Table 91, "Showing the occupations of males and females, in Ireland in 1891, and 1901, ... in classes, orders, and
sub-orders": the "All ages" columns (persons, males, females, 1891 and 1901) of pp. 398 and 400 (images n443, n445),
read into `data/curated/change/data/work_census_ir_t91.csv`. The facing pages 399 and 401 (n444, n446) split the same
figures by age (under 20, 20 and over) and settle any figure in doubt.

Ireland kept the classification of 1881 to 1911: six classes, the industrial class (V) in orders of people "working and
dealing" in a material, so makers and dealers share sub-orders and the three sectors need the occupation lines
(C5c2c2c2, C5c2c2c3). These figures are the frame the lines are checked against: `check` tests every row (persons =
males + females), every order against its sub-orders, every class against its orders, the classes I-V against the
"persons of specified occupations and conditions", and those with class VI against all persons, in each of the six
columns. One printed figure does not agree (`KNOWN`): the women in board and lodging in 1901, printed 5,570, are 5,572
by the age columns (240 under 20, 5,332 over), by the persons column and by the order total.

Changes of practice to watch when the lines are grouped: 93,280 "literary and scientific persons" in 1891 (8,378 in
1901) are mostly students (sub-order 3.5); farmers' sons and other relatives are in class IV; the general labourers are
sub-order 22.2 (left out, as in Booth's figures).
"""
import csv

from .change_firms import DATA

READINGS = DATA / "work_census_ir_t91.csv"
COLUMNS = ["p1891", "p1901", "m1891", "m1901", "f1891", "f1901"]
CLASS_ORDERS = {"I": (1, 2, 3), "II": (4,), "III": (5, 6), "IV": (7, 8), "V": tuple(range(9, 24)), "VI": (24,)}
OCCUPIED = ("I", "II", "III", "IV", "V")
KNOWN = {("16.1", "f1901"): 5572}                 # printed 5,570; the age columns, persons and order 16 give 5,572


def load(path=READINGS):
    """[{level, code, name, p1891, ..., f1901, image, page}] as printed."""
    with open(path, newline="") as f:
        return [dict(r, **{c: int(r[c]) for c in COLUMNS}) for r in csv.DictReader(f)]


def corrected(rows=None):
    """The rows with the misprints of `KNOWN` put right."""
    rows = [dict(r) for r in (rows or load())]
    for r in rows:
        for c in COLUMNS:
            r[c] = KNOWN.get((r["code"], c), r[c])
    return rows


def _by(rows, level):
    return {r["code"]: r for r in rows if r["level"] == level}


def check(rows=None):
    """Problems, after `KNOWN`: rows where persons are not males + females, orders, classes and totals that do not add."""
    rows = corrected(rows)
    bad = [f"{r['code']} {y}: persons {r['p' + y]}, males + females {r['m' + y] + r['f' + y]}"
           for r in rows for y in ("1891", "1901") if r["p" + y] != r["m" + y] + r["f" + y]]
    orders, classes, totals = _by(rows, "order"), _by(rows, "class"), _by(rows, "total")
    for c in COLUMNS:
        for code, o in orders.items():
            s = sum(r[c] for r in rows if r["level"] == "sub_order" and r["code"].split(".")[0] == code)
            if s != o[c]:
                bad.append(f"order {code} {c}: sub-orders add to {s}, printed {o[c]}")
        for name, nums in CLASS_ORDERS.items():
            s = sum(orders[str(n)][c] for n in nums)
            if s != classes[name][c]:
                bad.append(f"class {name} {c}: orders add to {s}, printed {classes[name][c]}")
        occupied = sum(classes[k][c] for k in OCCUPIED)
        if occupied != totals["specified"][c]:
            bad.append(f"classes I-V {c}: {occupied}, printed {totals['specified'][c]}")
        if occupied + classes["VI"][c] != totals["all"][c]:
            bad.append(f"all persons {c}: classes add to {occupied + classes['VI'][c]}, printed {totals['all'][c]}")
    return bad


def sub_orders(rows=None, year=1891):
    """{sub-order code: persons} in a census year (misprints corrected)."""
    return {code: r[f"p{year}"] for code, r in _by(corrected(rows), "sub_order").items()}


def occupied(rows=None):
    """{year: persons in classes I-V} (of specified occupations)."""
    t = _by(corrected(rows), "total")["specified"]
    return {1891: t["p1891"], 1901: t["p1901"]}


if __name__ == "__main__":
    r = load()
    print(check(r) or "every row, order, class and total agrees (KNOWN apart)")
    print("occupied", occupied(r))
