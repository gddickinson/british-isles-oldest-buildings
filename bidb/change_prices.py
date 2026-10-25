"""Prices since 1800 for "Change over time" (roadmap C5d1): the ONS's long-run Retail Prices Index (CDKO, OGL), the
"composite price index" joined by the ONS from older indexes to the RPI, yearly 1800-2025, January 1974 = 100.

    python -m bidb.change_prices      → data/curated/change/data/prices_rpi_uk.csv + series.json entry
                                        (then python -m bidb.change_series)

Drawn on a logarithmic axis (`log`): over two centuries prices rose about 120 times, most of it after 1940, so equal
steps on the axis are equal ratios. `rpi` (the yearly values) is also read by bidb.change_wages to turn wage indexes
into real wages.
"""
import csv
import json
import sys

from .change_firms import DATA
from .change_registers import _csv, _row
from .change_work import _ons

URL = "https://www.ons.gov.uk/generator?format=csv&uri=/economy/inflationandpriceindices/timeseries/cdko/mm23"
SOURCE = "ons_cdko"
SID = "prices_rpi_uk"


def rpi(log=print):
    """{year: index, January 1974 = 100}, the yearly values of CDKO (months left out)."""
    with open(_ons(URL, "cdko.csv", log), newline="") as f:
        return {int(r[0]): float(r[1]) for r in csv.reader(f) if len(r) == 2 and r[0].isdigit()}


def ratio(p, a, b):
    """How many times prices rose from year a to year b."""
    return p[b] / p[a]


NOTE = ("The ONS's long-run Retail Prices Index (series CDKO), the 'composite price index' it joins from older indexes "
        "of the cost of living to the RPI (from 1947), yearly, January 1974 = 100, on a logarithmic axis: equal steps "
        "are equal ratios. Prices in {y1} were {r_all:.0f} times those of 1800. Prices fell after the Napoleonic wars "
        "({p1813:.1f} in 1813, {p1850:.1f} in 1850) and moved little for a century ({p1900:.1f} in 1900); they doubled "
        "in the First World War ({p1914:.1f} in 1914, {p1918:.1f} in 1918) and rose to {p1920:.1f} in 1920, fell back "
        "in the 1920s and early 1930s ({p1933:.1f} in 1933), and have risen in every year since {since} but {falls}: "
        "{r_70s:.1f} times between 1970 and 1980, {r_since:.1f} times between 1980 and {y1}.")


def not_rising(p, after=1934):
    """Years after `after` when prices did not rise."""
    return [y for y in sorted(p) if y > after and p[y] <= p[y - 1]]


def series(p):
    """The CSV points and the series.json row."""
    y1 = max(p)
    note = NOTE.format(y1=y1, r_all=ratio(p, 1800, y1), r_70s=ratio(p, 1970, 1980), r_since=ratio(p, 1980, y1),
                       since=1935, falls=", ".join(map(str, not_rising(p))) or "none",
                       **{f"p{y}": p[y] for y in (1813, 1850, 1900, 1914, 1918, 1920, 1933)})
    row = _row(SID, f"Prices since 1800 (Retail Prices Index, long run), 1800-{y1}", "Retail Prices Index",
               "index, January 1974 = 100", [SOURCE], "United Kingdom", note, unit="")
    row.update(log=True, zero=False)
    return [[y, v] for y, v in sorted(p.items())], row


def write(points, row):
    _csv(SID, points)
    path = DATA.parent / "series.json"
    keep = [s for s in json.loads(path.read_text()) if s["id"] != SID]
    path.write_text(json.dumps(keep + [row], ensure_ascii=False, indent=1))


def run(log=print):
    p = rpi(log)
    if list(p) != list(range(1800, max(p) + 1)):
        raise ValueError("CDKO: years missing")
    points, row = series(p)
    write(points, row)
    log(f"{len(points)} years 1800-{max(p)}; {row['note'][-160:]}")


if __name__ == "__main__":
    run(lambda m: print(m, file=sys.stderr, flush=True))
