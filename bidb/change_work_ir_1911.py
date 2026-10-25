"""Occupations in Ireland at the census of 1911 (roadmap C5c2c2c4), read from the page images of the four province
volumes: Census of Ireland 1911, Area, houses and population ... Province of Leinster (Cd. 6049, 1912), Munster,
Ulster and Connaught (public domain; Internet Archive `op1256115-1001` to `op1256118-1001`). No General Report for
1911 is on the Internet Archive, so Ireland is the sum of the four provinces' Summary Tables.

- Table XIX (classes, orders and sub-orders, all ages, males and females): the totals, the six classes and the
  sub-orders the sectors need (3.5 and orders 7-23) → `data/curated/change/data/work_census_ir_1911.csv`.
- Table XX (every occupation line by sex, the "Total" column): the lines of the sub-orders that mix sectors, with the
  1891 and 1901 lines in `work_census_ir_lines.csv` (column `province`), grouped by change_work_ir.

`check` tests, in each province and for each sex, the classes I-V against the persons of specified occupations, those
with class VI against all persons, classes IV and V against their sub-orders, and the four provinces' persons
against the 4,390,219 of Ireland in 1911; change_work_ir.check_lines tests each sub-order's lines against Table XIX.
"""
import csv

from .change_firms import DATA

FRAME = DATA / "work_census_ir_1911.csv"
IRELAND = 4390219                               # persons in Ireland, 1911 (the four provinces)
PROVINCES = ("Leinster", "Munster", "Ulster", "Connaught")
CLASS_ORDERS = {"IV": (7, 8), "V": tuple(range(9, 24))}


def load(path=FRAME):
    """[{province, level, code, males, females, edition, image}] as read."""
    with open(path, newline="") as f:
        return [dict(r, males=int(r["males"]), females=int(r["females"])) for r in csv.DictReader(f)]


def _get(rows, province, level, code):
    return next(r for r in rows if (r["province"], r["level"], r["code"]) == (province, level, code))


def check(rows=None):
    """Problems: a province's classes or sub-orders not adding to its printed totals; provinces not adding to Ireland."""
    rows, bad = rows or load(), []
    for p in PROVINCES:
        for sex in ("males", "females"):
            cls = {c: _get(rows, p, "class", c)[sex] for c in ("I", "II", "III", "IV", "V", "VI")}
            occupied = sum(v for c, v in cls.items() if c != "VI")
            if occupied != _get(rows, p, "total", "specified")[sex]:
                bad.append(f"{p} {sex}: classes I-V add to {occupied}")
            if occupied + cls["VI"] != _get(rows, p, "total", "all")[sex]:
                bad.append(f"{p} {sex}: classes add to {occupied + cls['VI']}, not all persons")
            for c, orders in CLASS_ORDERS.items():
                s = sum(r[sex] for r in rows if r["province"] == p and r["level"] == "sub_order"
                        and int(r["code"].split(".")[0]) in orders)
                if s != cls[c]:
                    bad.append(f"{p} {sex} class {c}: sub-orders add to {s}, printed {cls[c]}")
    persons = sum(r["males"] + r["females"] for r in rows if r["level"] == "total" and r["code"] == "all")
    if persons != IRELAND:
        bad.append(f"the provinces add to {persons} persons, not {IRELAND}")
    return bad


def sub_orders(rows=None, sex=None):
    """{sub-order code, or class I-III: persons (or one sex) in Ireland}, the provinces summed."""
    out = {}
    for r in rows or load():
        if r["level"] == "sub_order" or (r["level"] == "class" and r["code"] in ("I", "II", "III")):
            out[r["code"]] = out.get(r["code"], 0) + (r[sex] if sex else r["males"] + r["females"])
    return out


def province_sub_orders(rows=None):
    """{(province, sex initial, sub-order): persons}."""
    return {(r["province"], s[0], r["code"]): r[s] for r in rows or load() if r["level"] == "sub_order"
            for s in ("males", "females")}


def occupied(rows=None):
    """Persons of specified occupations in Ireland, 1911."""
    return sum(r["males"] + r["females"] for r in rows or load() if r["level"] == "total" and r["code"] == "specified")


if __name__ == "__main__":
    print(check() or "every class, sub-order and province agrees")
    print("occupied", occupied())
