"""Occupations by sector in Scotland at the census of 1891 (roadmap C5c2c2b), read from page images.

Tenth Decennial Census of the Population of Scotland, 1891, Vol. II, Part II (C. 7134, 1893; public domain; Internet
Archive `tenthdecennialce0002vari`), "Summary of the occupations of the inhabitants of Scotland, distinguishing the sexes":
classes and orders (p. 2, leaf 41), sub-orders (p. 3, leaf 42) and the occupations (pp. 4-9, leaves 43-48), all ages,
both sexes, read into `data/curated/change/data/work_census_sc_1891.csv`.

The 1891 classification puts people in six classes; its industrial class (V) has orders of "working and dealing" in a
material, so makers and dealers share sub-orders. Classes I-IV and the sub-orders of class V with no dealers are taken
whole from p. 3 (`(whole sub-order)`); the others line by line, each line given a kind (`KINDS`). Every one of those
sub-orders adds up to its printed total, and the sub-orders add up to the printed totals of the classes (`check`).

Grouped as the censuses of 1901 and 1911 (bidb.change_work_sc), line for line where the classifications differ: cattle
dealers, drovers and gamekeepers to services, knackers to making; mineral oil workers and gas works to making;
coalheavers to services (transport in 1911); coke burners, limeburners, quarriers and stone cutters to mining. A line
that joins makers and dealers (tobacco manufacture and tobacconists, bakers and confectioners, furniture makers and
dealers, provision curers and dealers, platelayers and navvies) is shared out as its lines were in 1901 (`x:` kinds,
`split`). Gardeners are one line in 1891, all in farming (the 1901-1911 tables put domestic gardeners in services).
"""
import csv

from . import change_work_sc as sc
from .change_firms import DATA

READINGS = DATA / "work_census_sc_1891.csv"
KINDS = {"p": "farming, fishing and mining", "m": "making and building", "s": "services", "d": "dealers (services)",
         "o": "left out (general labourers)", "x": "shared out as the 1901 lines (services lines / all lines)",
         "total": "printed sub-order total (check only)"}
CLASSES = {"I": (111319, ("1", "2", "3")), "II": (203153, ("4",)), "III": (180952, ("5", "6")),
           "IV": (249124, ("7", "8", "8a")), "V": (1032404, tuple(str(n) for n in range(9, 24)))}
OCCUPIED = 1776952                                # classes I-V, p. 2 and the report (1,220,388 males, 556,564 females)


def load(path=READINGS):
    """[{sub_order, line, value, kind, ...}] as read."""
    with open(path, newline="") as f:
        return [dict(r, value=int(r["value"])) for r in csv.DictReader(f)]


def check(rows=None):
    """Problems: a sub-order whose lines do not add to its printed total; classes not adding to theirs."""
    rows = rows or load()
    bad = []
    totals = {r["sub_order"]: r["value"] for r in rows if r["kind"] == "total"}
    counted = {}
    for r in rows:
        if r["kind"] != "total":
            counted[r["sub_order"]] = counted.get(r["sub_order"], 0) + r["value"]
    bad += [f"{so}: lines add to {counted.get(so)}, printed {v}" for so, v in totals.items() if counted.get(so) != v]
    for name, (printed, orders) in CLASSES.items():
        s = sum(v for so, v in totals.items() if so.split(".")[0] in orders)
        if s != printed:
            bad.append(f"class {name}: sub-orders add to {s}, printed {printed}")
    if sum(v for _, (v, _) in CLASSES.items()) != OCCUPIED:
        bad.append("classes I-V do not add to the occupied")
    return bad


def _persons_1901(lines, d1):
    return sum((r["m1901"] or 0) + (r["f1901"] or 0) for r in d1 if r["line"] in lines)


def split(kind, d1=None):
    """The services share of a line joining makers and dealers: its 1901 services lines over all its lines."""
    d1 = d1 or sc.load()
    serv, every = (set(int(n) for n in part.split("+")) for part in kind[2:].split("/"))
    bad = [r["line"] for r in d1 if r["line"] in every and r["bracket"] and r["m1901"] is None]
    if bad:
        raise ValueError(f"{kind}: 1901 figure in a brace ({bad})")
    return _persons_1901(serv, d1) / _persons_1901(every, d1)


def sectors(rows=None):
    """(primary, secondary, tertiary, left out) persons in 1891."""
    rows = rows or load()
    d1 = sc.load()
    out = [0.0, 0.0, 0.0, 0.0]
    for r in rows:
        k, v = r["kind"], r["value"]
        if k == "total":
            continue
        if k.startswith("x:"):
            share = split(k, d1)
            out[2] += v * share
            out[1] += v * (1 - share)
        else:
            out[{"p": 0, "m": 1, "s": 2, "d": 2, "o": 3}[k]] += v
    return tuple(out)


def shares(rows=None):
    """{1891: (primary, secondary, tertiary) % of those occupied whose industry is known}."""
    prim, sec, ter, _ = sectors(rows)
    total = prim + sec + ter
    return {1891: tuple(round(v / total * 100, 2) for v in (prim, sec, ter))}


def left_out(rows=None):
    """{1891: % of those occupied left out} (general labourers)."""
    s = sectors(rows)
    return {1891: round(s[3] / sum(s) * 100, 1)}


if __name__ == "__main__":
    r = load()
    print(check(r) or "every sub-order and class agrees")
    print({k: round(split(k), 3) for k in sorted({x["kind"] for x in r if x["kind"].startswith("x:")})})
    print(shares(r), "left out", left_out(r))
