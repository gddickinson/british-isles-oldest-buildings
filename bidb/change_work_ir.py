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

The occupation lines (roadmap C5c2c2c2, C5c2c2c3): Table 20 of the same report (1901; males pp. 119-124, females pp.
125-130) and Table 19 of the 1891 General Report (C. 6780, 1892; Internet Archive `op1252985-1001`; males pp. 116-121,
females pp. 123-128), the "Total" column, read into `data/curated/change/data/work_census_ir_lines.csv` for every
sub-order that mixes sectors: orders 8 (about animals) and 9-23 (the industrial class) and the students of 3.5. (The
1901 report's page views `n<N>` crop the left-hand pages at the gutter; the uncropped scans are file N+1 of the item's
`_images.zip`.) Every sub-order's lines add to its Table 91 figure for each sex and year (`check_lines`).

Grouped as Scotland's census lines (bidb.change_work_sc, change_work_sc_1891), each line given a kind (`KINDS`): every
dealer to services, as are grooms, gamekeepers, coalheavers, platelayers, hairdressers, undertakers, chimney sweeps and
scavengers; quarriers, stone cutters, limeburners and peat cutters to mining; knackers and the undefined artisans,
engine drivers, factory hands and machinists to making. Four lines that join makers and dealers (tobacco
manufacturers and tobacconists, provision curers and dealers, bakers, confectioners) are shared out as their lines
were in Scotland in 1901 (`x:` kinds, change_work_sc_1891.split). Sub-orders not read line by line are whole
(`whole_kind`): classes I-III services, order 7 farming, board and lodging (16.1) services, miners (21.1) mining, the
rest of the industrial class making. Left out: students (not occupied; 1891 counts "persons aged 15 years and upwards
returned as Scholar" among them, 92,492 against 7,409 in 1901) and the general labourers (as Booth), most of whom, the
reports say, were farm labourers.
"""
import csv

from .change_firms import DATA

READINGS = DATA / "work_census_ir_t91.csv"
LINES = DATA / "work_census_ir_lines.csv"
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



KINDS = {"p": "farming, fishing and mining", "m": "making and building", "s": "services", "d": "dealers (services)",
         "o": "left out (general labourers)", "n": "left out (students, not occupied)",
         "x": "shared out as Scotland's 1901 lines (services lines / all lines)"}
SECTOR = {"p": 0, "m": 1, "s": 2, "d": 2, "o": 3, "n": 4}


YEARS = (1891, 1901, 1911)


def load_lines(path=LINES):
    """[{year, province, sex, sub_order, line, value, kind, ...}] as read (1891 and 1901 for all Ireland, 1911 by
    province)."""
    with open(path, newline="") as f:
        return [dict(r, year=int(r["year"]), value=int(r["value"])) for r in csv.DictReader(f)]


def check_lines(lines=None, rows=None):
    """Problems: a sub-order whose lines (students apart) do not add to its printed figure for a sex and year (Table
    91 for 1891 and 1901, each province's Table XIX for 1911)."""
    from . import change_work_ir_1911 as ir11
    lines, subs, prov = lines or load_lines(), _by(corrected(rows), "sub_order"), ir11.province_sub_orders()
    added = {}
    for r in lines:
        if r["sub_order"] != "3.5":
            k = (r["year"], r["province"], r["sex"], r["sub_order"])
            added[k] = added.get(k, 0) + r["value"]
    bad = []
    for (y, p, sex, so), v in added.items():
        printed = prov[(p, sex, so)] if y == 1911 else subs[so][sex + str(y)]
        if v != printed:
            bad.append(f"{so} {p} {sex}{y}: lines add to {v}, printed {printed}")
    return bad


def whole_kind(code):
    """The kind of a sub-order (or, for 1911, a class I-III) not read line by line."""
    if code in ("I", "II", "III"):
        return "s"
    order = int(code.split(".")[0])
    if order <= 6 or code == "16.1":
        return "s"
    return "p" if order == 7 or code == "21.1" else "m"


def sectors(year, lines=None, rows=None):
    """[primary, secondary, tertiary, general labourers, students] persons in a census year."""
    from . import change_work_sc as sc, change_work_sc_1891 as sc91
    lines = [r for r in (lines or load_lines()) if r["year"] == year]
    d1, out, lined = sc.load(), [0.0] * 5, set()
    for r in lines:
        k, v = r["kind"], r["value"]
        if r["sub_order"] != "3.5":
            lined.add(r["sub_order"])
        if k.startswith("x:"):
            share = sc91.split(k, d1)
            out[2] += v * share
            out[1] += v * (1 - share)
        else:
            out[SECTOR[k]] += v
    if year == 1911:
        from . import change_work_ir_1911 as ir11
        whole = ir11.sub_orders()
    else:
        whole = sub_orders(rows, year)
    for code, v in whole.items():
        if code not in lined and code != "24.1":
            out[SECTOR[whole_kind(code)]] += v
    out[2] -= out[4]                     # the students were counted in 3.5 (1891, 1901) or class I (1911), taken whole
    return out


def shares(lines=None, rows=None):
    """{year: (primary, secondary, tertiary) % of those occupied, students and general labourers apart}."""
    out = {}
    for y in YEARS:
        s = sectors(y, lines, rows)
        total = sum(s[:3])
        out[y] = tuple(round(v / total * 100, 2) for v in s[:3])
    return out


def left_out(lines=None, rows=None):
    """{year: general labourers, % of those occupied (students apart)}."""
    out = {}
    for y in YEARS:
        s = sectors(y, lines, rows)
        out[y] = round(s[3] / sum(s[:4]) * 100, 1)
    return out


if __name__ == "__main__":
    r = load()
    print(check(r) or "every row, order, class and total agrees (KNOWN apart)")
    print(check_lines(rows=r) or "every sub-order's lines add to Table 91")
    print("occupied", occupied(r))
    print("shares", shares(rows=r), "general labourers left out", left_out(rows=r))
