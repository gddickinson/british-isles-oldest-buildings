"""One-off preparation of the yearly temperature series for each country of the isles and the globe
(data/curated/change/data/temp_*.csv). Run from the repo root with the project's Python:
    .venv/bin/python data/curated/change/prepare_temperatures.py <download folder>

Measured: Met Office HadUK-Grid country series (England, Wales, Scotland, Northern Ireland; 1884–), CRU CY 4.10 for
Ireland (1901–), CRU TS 4.10 cells for the Isle of Man and the Channel Islands (1901–; from layers/cru_years.json.gz),
HadCRUT5 for the globe (1850–).
Reconstructed by others: Luterbacher et al. 2004 / Xoplaki et al. 2005 European seasonal grids (1500–1900), averaged
over each country's land cells; PAGES 2k Consortium 2019 (global, AD 1–2000); Temp12k (Kaufman et al. 2020).
Estimated here: each country's yearly mean from the Central England Temperature for 1659 onwards, by a straight-line
fit over the years both are measured, with a band of ±1.96 × the fit's residual standard deviation.
"""
import csv
import gzip
import json
import math
import os
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
OUT = ROOT / "data" / "curated" / "change" / "data"
LAYERS = ROOT / "data" / "curated" / "change" / "layers"
HADUK = "https://www.metoffice.gov.uk/pub/data/weather/uk/climate/datasets/Tmean/date/{}.txt"
CRUCY = "https://crudata.uea.ac.uk/cru/data/hrg/cru_ts_4.10/crucy.2606161920.v4.10/countries/tmp/crucy.v4.10.1901.2025.{}.tmp.per"
HADCRUT = ("https://www.metoffice.gov.uk/hadobs/hadcrut5/data/HadCRUT.5.1.0.0/analysis/diagnostics/"
           "HadCRUT.5.1.0.0.analysis.summary_series.global.annual.csv")
PAGES2K = "https://www.ncei.noaa.gov/pub/data/paleo/pages2k/neukom2019temp/recons/Full_ensemble_median_and_95pct_range.txt"
LUT = "https://www.ncei.noaa.gov/pub/data/paleo/historical/europe-seasonal-files/{}-{}.txt"
NATIONS = {"England": "eng", "Wales": "wal", "Scotland": "scot", "Northern Ireland": "ni", "Republic of Ireland": "ie",
           "Isle of Man": "iom", "Jersey": "jer", "Guernsey": "gsy"}
ISLANDS = {"iom": (54.23, -4.55), "jer": (49.21, -2.13), "gsy": (49.46, -2.58)}     # nearest land cell for small islands


def get(url, dest):
    if not dest.exists():
        req = urllib.request.Request(url, headers={"User-Agent": "british-isles-oldest-buildings (research)"})
        dest.write_bytes(urllib.request.urlopen(req, timeout=120).read())
    return dest.read_text(errors="replace")


def write(name, pts):
    with open(OUT / name, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["year", "value", "low", "high"])
        for y in sorted(pts):
            v = pts[y]
            w.writerow([y, *(round(x, 2) if x is not None else "" for x in (v if isinstance(v, tuple) else (v, None, None)))])


def haduk(dl, region):
    out = {}
    for line in get(HADUK.format(region), dl / f"haduk_{region}.txt").splitlines():
        p = line.split()
        if len(p) == 18 and p[0].isdigit() and p[-1] != "---":
            out[int(p[0])] = float(p[-1])
    return out


def crucy(dl, country):
    out = {}
    for line in get(CRUCY.format(country), dl / f"crucy_{country}.per").splitlines():
        p = line.split()
        if len(p) == 18 and p[0].isdigit() and float(p[-1]) > -900:
            out[int(p[0])] = float(p[-1])
    return out


def cet():
    with open(OUT / "cet.csv") as f:
        return {int(r["year"]): float(r["value"]) for r in csv.DictReader(f)}


def fit_from_cet(measured, c):
    """Straight-line fit of a country's yearly mean on CET over the common years → estimates with a band, for the
    CET years before the country's record starts."""
    both = sorted(set(measured) & set(c))
    x, y = [c[k] for k in both], [measured[k] for k in both]
    mx, my = sum(x) / len(x), sum(y) / len(y)
    b = sum((a - mx) * (d - my) for a, d in zip(x, y)) / sum((a - mx) ** 2 for a in x)
    a = my - b * mx
    sd = math.sqrt(sum((d - (a + b * q)) ** 2 for q, d in zip(x, y)) / (len(x) - 2))
    r = sum((p - mx) * (d - my) for p, d in zip(x, y)) / math.sqrt(sum((p - mx) ** 2 for p in x) * sum((d - my) ** 2 for d in y))
    start = min(measured)
    est = {k: (a + b * v, a + b * v - 1.96 * sd, a + b * v + 1.96 * sd) for k, v in c.items() if k < start}
    return est, {"slope": round(b, 3), "intercept": round(a, 3), "sd": round(sd, 3), "r": round(r, 3), "years": [both[0], both[-1]]}


def luterbacher(dl):
    """Country yearly means 1500–1900 from the seasonal grids (0.5°, 25W–40E, 70N–35N; rows north → south)."""
    from bidb.db import connect
    from bidb.nation_geo import NationFinder
    cache = dl / "lut"
    cache.mkdir(exist_ok=True)
    grids = {}
    for y in range(1500, 1901):
        seas = []
        for s in ("wi", "sp", "su", "au"):
            vals = [float(v) for v in get(LUT.format(y, s), cache / f"{y}-{s}.txt").split()]
            seas.append(vals)
        grids[y] = [None if any(v[i] < -900 for v in seas) else sum(v[i] for v in seas) / 4 for i in range(len(seas[0]))]
    cell = lambda i: (69.75 - (i // 130) * 0.5, -24.75 + (i % 130) * 0.5)
    land = [i for i, v in enumerate(grids[1900]) if v is not None and 49 <= cell(i)[0] <= 61 and -11 <= cell(i)[1] <= 2]
    finder = NationFinder(connect())
    cells = {}
    for i in land:
        n = NATIONS.get(finder.nation(*cell(i)))
        if n:
            cells.setdefault(n, []).append(i)
    for n, (lat, lon) in ISLANDS.items():
        cells[n] = [min(land, key=lambda i: (cell(i)[0] - lat) ** 2 + ((cell(i)[1] - lon) * 0.63) ** 2)]
    print({k: len(v) for k, v in cells.items()})
    return {n: {y: sum(g[i] for i in ids) / len(ids) for y, g in grids.items()} for n, ids in cells.items()}


def cru_cells():
    """Isle of Man and Channel Islands yearly means 1901– from the nearest CRU TS land cell."""
    p = LAYERS / "cru_years.json.gz"
    if not p.exists():
        return {}
    with gzip.open(p, "rt") as f:
        d = json.load(f)
    out = {}
    for n, (lat, lon) in ISLANDS.items():
        grids = {int(k): v for k, v in d["tmp"].items()}
        first = grids[min(grids)]
        cand = [(r, c) for r in range(len(first)) for c in range(len(first[0])) if first[r][c] is not None]
        r, c = min(cand, key=lambda rc: (61 - (rc[0] + 0.5) / 2 - lat) ** 2 + ((-11 + (rc[1] + 0.5) / 2 - lon) * 0.63) ** 2)
        out[n] = {y: g[r][c] for y, g in grids.items() if g[r][c] is not None}
    return out


def main(dl):
    dl = Path(dl)
    dl.mkdir(parents=True, exist_ok=True)
    c = cet()
    measured = {"eng": haduk(dl, "England"), "wal": haduk(dl, "Wales"), "scot": haduk(dl, "Scotland"),
                "ni": haduk(dl, "Northern_Ireland"), "ie": crucy(dl, "Ireland"), **cru_cells()}
    lut = luterbacher(dl)
    fits = {}
    for n, m in measured.items():
        if not m:
            continue
        write(f"temp_{n}.csv", m)
        write(f"temp_{n}_lut.csv", {y: v for y, v in lut[n].items()})
        if n != "eng":
            est, fits[n] = fit_from_cet(m, c)
            write(f"temp_{n}_cet.csv", est)
        both = sorted(set(m) & set(lut[n]))
        fits.setdefault(n, {})["reconstruction_minus_measured"] = round(sum(lut[n][y] - m[y] for y in both) / len(both), 2) if both else None
    # the globe, as differences from 1850–1900 (HadCRUT5's own baseline is 1961–1990)
    had = {}
    for r in csv.DictReader(get(HADCRUT, dl / "hadcrut5.csv").splitlines()):
        had[int(r["Time"])] = tuple(float(r[k]) for k in ("Anomaly (deg C)", "Lower confidence limit (2.5%)", "Upper confidence limit (97.5%)"))
    base = sum(had[y][0] for y in range(1850, 1901)) / 51
    write("temp_global.csv", {y: tuple(v - base for v in t) for y, t in had.items()})
    pk = {}
    for line in get(PAGES2K, dl / "pages2k.txt").splitlines():
        p = line.split("\t")
        if p[0].strip().isdigit() and p[2] != "NA":
            pk[int(p[0])] = tuple(float(p[i]) for i in (2, 3, 4))
    pbase = sum(pk[y][0] for y in range(1850, 1901)) / 51
    write("temp_global_pages2k.csv", {y: tuple(v - pbase for v in t) for y, t in pk.items()})
    json.dump(fits, open(dl / "fits.json", "w"), indent=1)
    print(json.dumps(fits, indent=1))
    print("HadCRUT5 1850–1900 mean (1961–1990 base):", round(base, 3), "PAGES2k:", round(pbase, 3))


if __name__ == "__main__":
    main(sys.argv[1])
