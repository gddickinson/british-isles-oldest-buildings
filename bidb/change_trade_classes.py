"""The main goods traded 1953-1957, by the Board of Trade's classes and divisions of the original Standard
International Trade Classification, for "Change over time" (roadmap C5b2d2b); read by bidb.change_trade_sitc, which
joins them to its 1958-1974 series.

Up to No. 100 (1963) the Annual Abstract of Statistics prints imports and exports by the Import and Export Lists of
the Board of Trade: five classes (A food, beverages and tobacco; B basic materials; C mineral fuels; D manufactured
goods; E miscellaneous) and their divisions, numbered within each class and regrouped from the original SITC. Every
division is printed (or an "other" line), so each figure was checked twice: the divisions against their class's
total, and the four class totals and the two divisions of class E against the grand total (`check`). The figures were
read from the page images of Nos. 99 (1953-1961) and 100 (1954-1962) (`data/curated/change/data/
trade_classes_abstract_uk.csv`: edition, leaf, page and table per figure); 1954-1960 agree figure for figure in the
two (`overlap`), so 1953 comes from No. 99 and 1954-1957 from No. 100. Precious stones are left out (No. 104 adds them
from 1958); exports are of United Kingdom produce and include repayments of Lend-Lease silver to the United States
(£22.4 million in 1956, £7.1 million in 1957, footnote to No. 100's table 258).
"""
import re

from .change_firms import DATA
from .change_trade_sitc import load as _load, near, overlap  # noqa: F401  (overlap re-exported for the tests)

READINGS = DATA / "trade_classes_abstract_uk.csv"
LATEST = (100, 99)                          # editions, latest first
YEARS = range(1953, 1958)                   # 1958 onwards from SITC (R), bidb.change_trade_sitc
# The goods of change_trade_sitc on the classes' divisions (exports: D6-D9 are the four textile yarn and fabric
# divisions, D15-D16 machinery; imports: B7, B8 and "other textile fibres" are division 26 of SITC (R))
EXPORT_GOODS = {"textiles": ("D6", "D7", "D8", "D9"), "coal": ("C1",), "iron": ("D12",), "machinery": ("D15", "D16")}
IMPORT_GOODS = {"cereals": ("A5",), "sugar": ("A7",), "beverages": ("A8",), "wood": ("B4",),
                "fibres": ("B7", "B8", "Bo")}


def load(path=READINGS):
    """{edition number: {row: {year: £ million}}}; rows are side (x exports, i imports) + "_" + code: "total", class
    totals "sA"-"sD", divisions "A1"-"D23", "E1", "E2", and "<class>o" for a class's other divisions."""
    return _load(path)


def check(rows):
    """Problems: a class whose divisions, or a total whose classes, do not add up within the rounding (`near`)."""
    bad = []
    for n, ed in sorted(rows.items()):
        for side in "xi":
            for y, total in sorted(ed[f"{side}_total"].items()):
                top = [ed[f"{side}_s{c}"][y] for c in "ABCD"] + [ed[f"{side}_E{k}"][y] for k in (1, 2)]
                if not near(sum(top), total, len(top)):
                    bad.append(f"No. {n} {y} {side}: classes {sum(top):.1f} != total {total}")
                for c in "ABCD":
                    pat = re.compile(rf"{side}_{c}(\d+|o)")
                    p = [v[y] for r, v in ed.items() if pat.fullmatch(r) and y in v]
                    if not near(sum(p), ed[f"{side}_s{c}"][y], len(p)):
                        bad.append(f"No. {n} {y} {side}: class {c} parts {sum(p):.1f} != {ed[f'{side}_s{c}'][y]}")
    return bad


def _goods(ed, y, n):
    g = {k: round(sum(ed["x_" + d][y] for d in ds), 1) for k, ds in EXPORT_GOODS.items()}
    g.update({k: round(sum(ed["i_" + d][y] for d in ds), 1) for k, ds in IMPORT_GOODS.items()})
    g.update(exports=ed["x_total"][y], imports=ed["i_total"][y], edition=n)
    return g


def goods(rows):
    """{year: {good: £ million, "exports", "imports", "edition"}} for 1953-1957 from the latest edition per year."""
    out = {}
    for n in reversed(LATEST):
        for y in rows[n]["x_total"]:
            if y in YEARS:
                out[y] = _goods(rows[n], y, n)
    return dict(sorted(out.items()))


def in_1958(rows):
    """1958 on this basis (No. 100), to set beside the SITC (R) figures of No. 104."""
    return _goods(rows[LATEST[0]], 1958, LATEST[0])
