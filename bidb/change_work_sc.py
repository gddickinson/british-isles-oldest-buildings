"""Occupations by sector in Scotland at the censuses of 1901 and 1911 (roadmap C5c2c2a), read from page images.

Census of Scotland 1911, Vol. II (Cd. 6896, 1913; public domain; Internet Archive `b32177264_0004`), Table D1,
"Intercensal change in the numbers returned under the various occupations" (leaves 86-97, pp. lxxv-lxxxvi): every one
of the 397 occupation lines of the 1911 classification, males and females, 1911 and 1901 (the 1901 figures regrouped
by the census office), with the increase or decrease printed beside them. The OCR of the tables is unusable, so they
were read from the page images into `data/curated/change/data/work_census_sc.csv`, one printed line per row; a 1901
figure that covers two or more lines (a brace) stands on the first line of its `bracket`.

`check` tests every line (or bracket) against its printed change, and the lines against the printed total occupied.
Every line agrees; the males add to the printed totals exactly; the females of 1901 add to 97 fewer than the printed
591,624 (`KNOWN`), though every female line agrees with its own printed change.

The three sectors (`sectors`), with every dealer apart as in Booth's regrouping, which this graph carries on:
- farming, fishing and mining: orders VII-IX (domestic gardeners are in order IV in Scotland's tables, so in services);
- making and building: orders X-XXI and the makers of order XXII, less the dealers (`DEALERS`);
- services: orders I-VI, every dealer line, the inns and lodging of order XX (`SERVICES`), and order XXII's shopkeepers,
  costermongers, cattle dealers, chimney sweeps... (`SERVICES`);
- left out, as no industry is stated: general labourers (line 393), as Booth leaves out general labour.
"""
import csv

from .change_firms import DATA

READINGS = DATA / "work_census_sc.csv"
YEARS = (1901, 1911)
TOTALS = {("m", 1911): 1473757, ("m", 1901): 1391188, ("f", 1911): 593210, ("f", 1901): 591624}
KNOWN = {("f", 1901): 97}                     # the female lines of 1901 add to 97 fewer than the printed total


def _lines(*spans):
    out = set()
    for s in spans:
        out |= set(range(s[0], s[1] + 1)) if isinstance(s, tuple) else {s}
    return out


PRIMARY = _lines((97, 130))                   # orders VII-IX less the dealers in coal and stone (131, 132)
DEALERS = _lines(131, 132, 188, 189, 199, 200, 229, 230, 238, 245, 246, 263, 271, 277, 311, 312, 316, 318, 324, 328,
                 332, 334, 336, 338, 340, 342, 344, 348, 349, 352, 354)
SERVICES = _lines((1, 96), (358, 360), (362, 363), (373, 375), 382, 383, (385, 390), 392) | DEALERS
NO_INDUSTRY = {393}
# order XXII's makers: billposters and sandwichmen (with paper and sundry workers in 1901), knackers, sundry industries,
# undefined contractors and manufacturers, engine drivers, artisans, factory hands, machinists
SECONDARY = _lines((133, 392), 394, 395, 396, 397) - PRIMARY - SERVICES - NO_INDUSTRY


def load(path=READINGS):
    """[{line, m1911, m1901, m_change, f1911, f1901, f_change, bracket, ...}] as read, blanks as None."""
    out = []
    with open(path, newline="") as f:
        for r in csv.DictReader(f):
            row = dict(r)
            for k in ("line", "m1911", "m1901", "m_change", "f1911", "f1901", "f_change"):
                row[k] = int(r[k]) if r[k] else None
            out.append(row)
    return out


def check(rows=None):
    """Problems: a line or bracket whose 1911 less 1901 is not its printed change; a sum not the printed total."""
    rows = rows or load()
    bad = []
    for sex in ("m", "f"):
        groups = {}
        for r in rows:
            g = groups.setdefault(r["bracket"] or f"line {r['line']}", [0, 0, 0])
            g[0] += r[f"{sex}1911"] or 0
            g[1] += r[f"{sex}1901"] or 0
            g[2] += r[f"{sex}_change"] or 0
        bad += [f"{sex} {k}: {a} - {b} is not {c}" for k, (a, b, c) in groups.items() if a - b != c]
        for y in YEARS:
            s = sum(r[f"{sex}{y}"] or 0 for r in rows)
            if TOTALS[sex, y] - s != KNOWN.get((sex, y), 0):
                bad.append(f"{sex} {y}: lines add to {s}, printed total {TOTALS[sex, y]}")
    return bad


def _brackets_in_one_sector(rows):
    """A 1901 brace must not span two sectors (its figure cannot be shared out)."""
    def sector(n):
        return next(i for i, s in enumerate((PRIMARY, SECONDARY, SERVICES, NO_INDUSTRY)) if n in s)
    by = {}
    for r in rows:
        if r["bracket"]:
            by.setdefault(r["bracket"], set()).add(sector(r["line"]))
    return [b for b, s in by.items() if len(s) > 1]


def sectors(rows, year):
    """(primary, secondary, tertiary, no industry stated) persons in a census year."""
    out = [0, 0, 0, 0]
    for r in rows:
        n = (r[f"m{year}"] or 0) + (r[f"f{year}"] or 0)
        for i, s in enumerate((PRIMARY, SECONDARY, SERVICES, NO_INDUSTRY)):
            if r["line"] in s:
                out[i] += n
    return tuple(out)


def shares(rows=None):
    """{year: (primary, secondary, tertiary) % of those occupied whose industry is known}."""
    rows = rows or load()
    out = {}
    for y in YEARS:
        prim, sec, ter, _ = sectors(rows, y)
        total = prim + sec + ter
        out[y] = tuple(round(v / total * 100, 2) for v in (prim, sec, ter))
    return out


def left_out(rows=None):
    """{year: % of those occupied left out} (general labourers)."""
    rows = rows or load()
    return {y: round(sectors(rows, y)[3] / sum(sectors(rows, y)) * 100, 1) for y in YEARS}


if __name__ == "__main__":
    r = load()
    print(check(r) or "every line and total agrees (KNOWN apart)")
    print("braces across sectors:", _brackets_in_one_sector(r) or "none")
    print(shares(r), "left out", left_out(r))
