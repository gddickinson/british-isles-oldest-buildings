"""Wages and real wages for "Change over time" (roadmap C5d2): wage indexes of the time divided by prices (the ONS's
long-run RPI, bidb.change_prices), stretches that cannot be joined (different measures, and no open index for
1939-1999 found):

- 1879-1913: the Board of Trade's "Index numbers showing general course of wages in the United Kingdom", wages in
  1900 = 100: 1879 from the Sixteenth Abstract of Labour Statistics (Cd. 7131, 1914), p. 82 (Internet Archive
  `op1256492-1001`, leaf 107), 1880-1913 from the Seventeenth (1915; `op1256333-1001`, leaf 90, p. 66), which revised
  agriculture (1912: 105.08 → 107.4) (public domain): building, coal mining, engineering, textiles and agriculture,
  and the unweighted mean of the five (drawn) and of the four without agriculture, read from the page images into
  `data/curated/change/data/wages_bot_1879_1913.csv`; `check` recomputes both printed means (one slip, `KNOWN`).
- 1914-1934 (C5d2a), July 1914 = 100, wage rates over the official cost-of-living index at the same date, the
  printed ranges as a band (`load_war`, `real_1914`): July 1914-1919 Bowley's "general rough average" of time rates
  and the Labour Gazette cost of living (Prices and Wages in the United Kingdom, 1914-1920, 1921, Table XXXIII,
  p. 106; quoted figures); 31 December 1920-1934 the Ministry of Labour's "estimated average percentage increase in
  weekly full-time rates of wages generally, compared with July, 1914" (Statistical Abstract No. 70 p. 93, No. 79
  pp. 140-141) over the cost of living at the beginning of the next January (No. 79 p. 137, No. 80 p. 137),
  `wages_mol_1914_1934.csv`.
- 1924-1938: the Ministry of Labour's "Index numbers showing the general course of weekly rates of wages" (average
  for 1924 = 100), by quarter, Statistical Abstract No. 83, table 138, p. 155 (leaf 176), `wages_mol_1924_1938.csv`;
  the year is the mean of its four quarters.
- 2000-2025: ONS Average Weekly Earnings, whole economy, total pay (KAB9, OGL), yearly £ a week, at 2025 prices.

    python -m bidb.change_wages      → data/curated/change/data/wages_*.csv + series.json entries
"""
import csv
import json
import sys

from . import change_prices
from .change_firms import DATA
from .change_registers import _csv, _row
from .change_work import _ons

BOT = DATA / "wages_bot_1879_1913.csv"
MOL = DATA / "wages_mol_1924_1938.csv"
WAR = DATA / "wages_mol_1914_1934.csv"
GROUPS = ("building", "coal", "engineering", "textile", "agriculture")
KNOWN = {}          # (year, column): a printed mean kept although its groups do not give it
AWE_URL = ("https://www.ons.gov.uk/generator?format=csv&uri=/employmentandlabourmarket/peopleinwork/"
           "earningsandworkinghours/timeseries/kab9/lms")


def load_bot(path=BOT):
    with open(path, newline="") as f:
        return [{k: (int(v) if k == "year" else float(v) if k in GROUPS or k.startswith("mean") else v)
                 for k, v in r.items()} for r in csv.DictReader(f)]


def check(rows=None):
    """Problems: a printed mean the printed groups do not give within their rounding (0.01 for the Sixteenth Abstract's
    two decimals, 0.1 for the Seventeenth's one), `KNOWN` apart."""
    bad = []
    for r in rows or load_bot():
        v = [r[g] for g in GROUPS]
        tol = 0.011 if r["edition"] == "op1256492-1001" else 0.1
        for col, mean in (("mean_all", sum(v) / 5), ("mean_ex_agriculture", sum(v[:4]) / 4)):
            if abs(mean - r[col]) > tol and KNOWN.get((r["year"], col)) != r[col]:
                bad.append(f"{r['year']} {col}: printed {r[col]}, groups give {mean:.3f}")
    return bad


def load_mol(path=MOL):
    """{year: mean of the four quarters, 1924 = 100}."""
    with open(path, newline="") as f:
        return {int(r["year"]): sum(float(r[q]) for q in ("q1", "q2", "q3", "q4")) / 4 for r in csv.DictReader(f)}


def load_war(path=WAR):
    """Rows of wages_mol_1914_1934.csv: wage rates (low, high) and cost of living, July 1914 = 100."""
    with open(path, newline="") as f:
        return [{k: (float(v) if k in ("wage_low", "wage_high", "cost_of_living") else int(v) if k == "year" else v)
                 for k, v in r.items()} for r in csv.DictReader(f)]


def real_1914(rows):
    """{year: (real, low, high)}: wage rates over the cost of living, July 1914 = 100; Bowley's July figures to 1919,
    the Ministry of Labour's end-of-year figures from 1920 (Bowley's July 1920 left out: the line has one point a year)."""
    out = {}
    for r in rows:
        if r["date"] == "July" and r["year"] >= 1920:
            continue
        c = r["cost_of_living"]
        lo, hi = r["wage_low"] / c * 100, r["wage_high"] / c * 100
        out[r["year"]] = (round((lo + hi) / 2, 1), round(lo, 1), round(hi, 1))
    return dict(sorted(out.items()))


def awe(log=print):
    """{year: £ a week}, KAB9's yearly values."""
    with open(_ons(AWE_URL, "kab9.csv", log), newline="") as f:
        return {int(r[0]): float(r[1]) for r in csv.reader(f) if len(r) == 2 and r[0].isdigit()}


def real(wages, prices, base):
    """Wages divided by prices, base year = 100."""
    r = {y: w / prices[y] for y, w in wages.items()}
    return {y: round(v / r[base] * 100, 2) for y, v in sorted(r.items())}


def at_prices(pounds, prices, year):
    """£ a week at the prices of `year`."""
    return {y: round(v * prices[year] / prices[y], 1) for y, v in sorted(pounds.items())}


NOTE_RATES = ("Wage rates divided by prices: what a week's wage at the standard rates would buy, three lines on "
              "their own bases. 1879-1913: the Board of Trade's index of the general course of wages (unweighted mean "
              "of building, coal mining, engineering, textiles and agriculture), 1900 = 100, over the ONS's long-run "
              "Retail Prices Index. 1914-1934: July 1914 = 100, wage rates over the official cost-of-living index at the "
              "same date, the band showing the range printed: to 1919 Bowley's rough average of time rates in July "
              "(1921), from 1920 the Ministry of Labour's estimate of the average increase in weekly full-time rates "
              "at the end of each year (the cost of living at the beginning of the next January). 1924-1938: the "
              "Ministry of Labour's index of weekly full-time rates in a representative selection of industries, "
              "1924 = 100, over the RPI. Rates, not earnings: none counts short time, unemployment, overtime or the "
              "move of workers into better-paid trades (war work raised earnings well above rates). Real wage rates "
              "rose {r1:.0f}% from 1879 to 1900 as prices fell ({w1879:.1f} to 100), then fell to {w1912:.1f} in 1912 "
              "as prices rose. In the war prices outran wages (real rates {war_low:.0f} in July {war_year}, July 1914 "
              "= 100); wages caught up in 1918-19 and stood at {w1920:.0f} at the end of 1920 and {w1921:.0f} a year "
              "later, as prices fell first; the wage cuts of 1922 took them back to {w1922:.0f}, and as prices then "
              "fell faster than money rates they reached {w1934:.0f} at the end of 1934. On the 1924 base, "
              "money rates fell to {m1933:.1f} in 1933 and real rates rose to {w1933:.1f} in 1933 and {w1938:.1f} in "
              "1938.")
NOTE_AWE = ("Average weekly earnings, whole economy, total pay (ONS series KAB9), yearly, at {y1} prices (divided by "
            "the Retail Prices Index). Earnings, not rates: they include bonuses and overtime and change with the mix "
            "of jobs. The RPI rises faster than the official CPI and CPIH (the ONS no longer counts it a national statistic), "
            "so the fall since 2007 is larger here than on those measures. £{a2000:.0f} a week in 2000 was £{r2000:.0f} at {y1} prices; earnings peaked at £{peak:.0f} in "
            "{ypeak}, fell to £{low:.0f} in {ylow} and were £{r1:.0f} in {y1}.")


def series(bot, mol, war, pounds, prices):
    w1 = real({r["year"]: r["mean_all"] for r in bot}, prices, 1900)
    w2 = real(mol, prices, 1924)
    w3 = real_1914(war)
    war_year = min((y for y in w3 if y <= 1919), key=lambda y: w3[y][0])
    y1 = max(y for y in pounds if y in prices)
    a = at_prices({y: v for y, v in pounds.items() if y in prices}, prices, y1)
    ypeak = max((y for y in a if y < 2014), key=a.get)
    ylow = min((y for y in a if y > ypeak), key=a.get)
    rows = [
        _row("wages_real_uk", "Real wage rates, 1879-1938", "1879-1913 (1900 = 100)",
             "index of wage rates over prices",
             ["bot_labour_abstract_16", "bot_labour_abstract_17", "bowley_1921_wages", "stat_abstract_wages_uk",
              "ons_cdko"], "United Kingdom",
             NOTE_RATES.format(r1=w1[1900] / w1[1879] * 100 - 100, w1879=w1[1879], w1912=w1[1912],
                               war_low=w3[war_year][0], war_year=war_year, w1920=w3[1920][0], w1921=w3[1921][0], w1922=w3[1922][0], w1934=w3[1934][0],
                               m1933=mol[1933], w1933=w2[1933], w1938=w2[1938]),
             ["wages_real_1914_uk", "wages_real_1924_uk"], unit=""),
        _row("wages_real_1914_uk", "Real wage rates, 1914-1934", "1914-1934 (July 1914 = 100)",
             "index of wage rates over the cost of living", ["bowley_1921_wages", "stat_abstract_wages_uk"],
             "United Kingdom", unit=""),
        _row("wages_real_1924_uk", "Real wage rates, 1924-1938", "1924-1938 (1924 = 100)",
             "index of wage rates over prices", ["stat_abstract_wages_uk", "ons_cdko"], "United Kingdom", unit=""),
        _row("wages_awe_real_uk", f"Average weekly earnings at {y1} prices, 2000-{y1}", "Average weekly earnings",
             f"£ a week at {y1} prices", ["ons_kab9", "ons_cdko"], "United Kingdom",
             NOTE_AWE.format(y1=y1, a2000=pounds[2000], r2000=a[2000], peak=a[ypeak], ypeak=ypeak, low=a[ylow],
                             ylow=ylow, r1=a[y1]), unit="£"),
    ]
    rows[1]["breaks"] = [[1920, "July figures (Bowley) to 1919; from 1920 the Ministry of Labour's, at the end of "
                                "each year"]]
    for r in rows:
        r["zero"] = False
    return {"wages_real_uk": w1, "wages_real_1914_uk": w3, "wages_real_1924_uk": w2, "wages_awe_real_uk": a}, rows


def write(points, rows):
    for sid, p in points.items():
        if any(isinstance(v, tuple) for v in p.values()):          # value, low, high
            with open(DATA / f"{sid}.csv", "w", newline="") as f:
                w = csv.writer(f)
                w.writerow(["year", "value", "low", "high"])
                w.writerows([y, *v] for y, v in sorted(p.items()))
        else:
            _csv(sid, sorted(p.items()))
    path = DATA.parent / "series.json"
    ids = {r["id"] for r in rows}
    keep = [s for s in json.loads(path.read_text()) if s["id"] not in ids]
    path.write_text(json.dumps(keep + rows, ensure_ascii=False, indent=1))


def run(log=print):
    bot = load_bot()
    bad = check(bot)
    if bad:
        raise ValueError("; ".join(bad))
    points, rows = series(bot, load_mol(), load_war(), awe(log), change_prices.rpi(log))
    write(points, rows)
    for r in rows:
        log(f"{r['id']}: {(r.get('note') or '')[-220:]}")


if __name__ == "__main__":
    run(lambda m: print(m, file=sys.stderr, flush=True))
