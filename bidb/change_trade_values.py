"""Overseas trade at the prices of the time, 1854-1938, for "Change over time" (roadmap C5b2a).

The Board of Trade's Statistical Abstract for the United Kingdom prints a summary table of the value of imports,
exports of United Kingdom produce and re-exports ("foreign and colonial produce") each year. The figures were read
from the page images of eight editions (`data/curated/change/data/trade_abstract_uk.csv`: edition, leaf, page and
table per year, with the readings of other editions where they differ). Every row is checked by its own sums: United
Kingdom produce + re-exports = total exports, and total imports less re-exports = net imports (or imports + exports
= the total trade, in the editions that print that instead).

    python -m bidb.change_trade_values   → data/curated/change/data/sa_trade_*.csv + series.json entries
                                           (then python -m bidb.change_series)
"""
import csv
import json
import sys

from .change_firms import DATA
from .change_registers import _csv, _row

READINGS = DATA / "trade_abstract_uk.csv"
SOURCES = ["stat_abstract_trade_uk"]
FIELDS = ("imports", "net_imports", "uk_produce", "re_exports", "total_exports", "total_trade")

VALUES_NOTE = (
    "The value of goods imported into and exported from the United Kingdom each year at the prices of the time, in "
    "million pounds, from the Board of Trade's Statistical Abstracts, read from the page images of eight editions "
    "(Nos. 16, 18, 30, 33, 46, 59, 70 and 83; edition, page and table per year in the data file). Imports are valued "
    "as they arrived (cost, insurance and freight), exports as loaded on board (\"free on board\"); bullion and coin "
    "and goods transhipped under bond are left out. Re-exports are goods imported and sent on again (\"foreign and "
    "colonial produce\"), so imports less re-exports is what the country kept. Each row was checked by its own sums "
    "(United Kingdom produce + re-exports = all exports; imports less re-exports = net imports, or imports + exports "
    "= the total trade). Where editions overlap the latest edition read is used; they agree except 1870, 1885 and "
    "1898, revised later, and 1868, where No. 18 misprints the imports (294,460,214 for 294,693,608). The values of "
    "new ships exported were not recorded in 1897-98; manufactured tobacco moved from re-exports to United Kingdom "
    "produce in 1892; from August 1914 to June 1917 goods owned by the British or Allied governments were left out; "
    "and from 1 April 1923 trade with the Irish Free State is overseas trade and the Free State's own trade is left "
    "out. Imports rose from {i0:,.0f} million in {y0} to {i1913:,.0f} million in 1913 and {imax:,.0f} million in "
    "{ymax}, and were {i1:,.0f} million in {y1}; exports of United Kingdom produce were "
    "{u0:,.0f}, {u1913:,.0f} and {u1:,.0f} million. Imports were above exports in every year. These are values, not "
    "volumes: for the quantities traded see \"Overseas trade, 1800-1938 (at 1913 prices)\".")
SHARE_NOTE = (
    "Re-exports (imported goods sent on again: \"foreign and colonial produce\") as a share of all exports, from the "
    "same Statistical Abstract tables as \"Overseas trade at the prices of the time\". The share was {s0:.0f}% in "
    "{y0}, highest in {ymax} ({smax:.1f}%), "
    "{s1913:.1f}% in 1913, lowest in {ymin} ({smin:.1f}%) and {s1:.1f}% in {y1}. "
    "Manufactured tobacco counts as United Kingdom produce from 1892 (before, as re-exports).")


def load(path=READINGS):
    """{year: row} with the six values as ints (None where the edition does not print one) and the citation fields."""
    out = {}
    with open(path, newline="") as f:
        for r in csv.DictReader(f):
            row = dict(r)
            for k in FIELDS:
                row[k] = int(r[k]) if r[k] else None
            out[int(r["year"])] = row
    return out


def check(rows):
    """Problems: a row whose own sums do not agree, or that has neither net imports nor the total trade."""
    bad = []
    for y, r in sorted(rows.items()):
        if r["uk_produce"] + r["re_exports"] != r["total_exports"]:
            bad.append(f"{y}: United Kingdom produce + re-exports != total exports")
        if r["net_imports"] is not None:
            if r["imports"] - r["re_exports"] != r["net_imports"]:
                bad.append(f"{y}: imports - re-exports != net imports")
        elif r["total_trade"] is not None:
            if r["imports"] + r["total_exports"] != r["total_trade"]:
                bad.append(f"{y}: imports + exports != total trade")
        else:
            bad.append(f"{y}: no second sum to check")
    years = sorted(rows)
    if years != list(range(years[0], years[-1] + 1)):
        bad.append("years missing")
    return bad


def series(rows):
    """{series id: [[year, value]]}: £ million (two decimals) and re-exports' share of all exports (%)."""
    m = lambda k: [[y, round(r[k] / 1e6, 2)] for y, r in sorted(rows.items())]
    return {"sa_trade_imports_uk": m("imports"), "sa_trade_exports_uk": m("uk_produce"),
            "sa_trade_reexports_uk": m("re_exports"),
            "sa_trade_reexport_share_uk": [[y, round(r["re_exports"] / r["total_exports"] * 100, 2)]
                                           for y, r in sorted(rows.items())]}


def write(rows, log=print):
    bad = check(rows)
    if bad:
        raise ValueError("; ".join(bad))
    pts = series(rows)
    for sid, p in pts.items():
        _csv(sid, p)
    v = {k: dict(p) for k, p in pts.items()}
    imp, uk, sh = v["sa_trade_imports_uk"], v["sa_trade_exports_uk"], v["sa_trade_reexport_share_uk"]
    y0, y1 = min(imp), max(imp)
    ymax, ymin = max(imp, key=imp.get), min(sh, key=sh.get)
    shmax = max(sh, key=sh.get)
    assert all(imp[y] > v["sa_trade_exports_uk"][y] + v["sa_trade_reexports_uk"][y] for y in imp)
    gbp = "million pounds (prices of the time)"
    out = [
        _row("sa_trade_imports_uk", "Overseas trade at the prices of the time, 1854-1938", "Imports", gbp, SOURCES,
             "United Kingdom (all Ireland to March 1923)",
             VALUES_NOTE.format(i0=imp[y0], y0=y0, i1913=imp[1913], imax=imp[ymax], ymax=ymax, i1=imp[y1], y1=y1,
                                u0=uk[y0], u1913=uk[1913], u1=uk[y1]),
             ["sa_trade_exports_uk", "sa_trade_reexports_uk"], unit="£m"),
        _row("sa_trade_exports_uk", "UK exports of UK produce", "Exports of United Kingdom produce", gbp, SOURCES,
             "United Kingdom", unit="£m"),
        _row("sa_trade_reexports_uk", "UK re-exports", "Re-exports (foreign and colonial produce)", gbp, SOURCES,
             "United Kingdom", unit="£m"),
        _row("sa_trade_reexport_share_uk", "Re-exports, share of all exports", "Re-exports", "% of all exports",
             SOURCES, "United Kingdom (all Ireland to March 1923)",
             SHARE_NOTE.format(s0=sh[y0], y0=y0, ymax=shmax, smax=sh[shmax], s1913=sh[1913], ymin=ymin,
                               smin=sh[ymin], s1=sh[y1], y1=y1), unit="%"),
    ]
    for r in out:
        r["zero"] = True
    path = DATA.parent / "series.json"
    keep = [s for s in json.loads(path.read_text()) if not s["id"].startswith("sa_trade_")]
    path.write_text(json.dumps(keep + out, ensure_ascii=False, indent=1))
    log(f"{len(rows)} years {y0}-{y1} checked; imports {imp[y0]:,.1f} -> {imp[y1]:,.1f} million (peak {ymax}); "
        f"re-exports' share highest {shmax} ({sh[shmax]:.1f}%), lowest {ymin} ({sh[ymin]:.1f}%)")


def run(log=print):
    write(load(), log)


if __name__ == "__main__":
    run(lambda m: print(m, file=sys.stderr, flush=True))
