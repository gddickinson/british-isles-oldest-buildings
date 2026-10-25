"""Wages and real wages for "Change over time" (roadmap C5d2): wage indexes of the time divided by prices (the ONS's
long-run RPI, bidb.change_prices), three stretches that cannot be joined (different measures, and no open index for
1913-1923 or 1939-1999 found):

- 1879-1912: the Board of Trade's "Index numbers showing general course of wages in the United Kingdom", wages in
  1900 = 100, Sixteenth Abstract of Labour Statistics (Cd. 7131, 1914), p. 82 (public domain; Internet Archive
  `op1256492-1001`, leaf 107): building, coal mining, engineering, textiles and agriculture, and the unweighted mean
  of the five (drawn) and of the four without agriculture, read from the page image into
  `data/curated/change/data/wages_bot_1879_1912.csv`; `check` recomputes both printed means (one slip, `KNOWN`).
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

BOT = DATA / "wages_bot_1879_1912.csv"
MOL = DATA / "wages_mol_1924_1938.csv"
GROUPS = ("building", "coal", "engineering", "textile", "agriculture")
KNOWN = {(1911, "mean_ex_agriculture"): 99.83}     # printed; the four groups give 99.80
AWE_URL = ("https://www.ons.gov.uk/generator?format=csv&uri=/employmentandlabourmarket/peopleinwork/"
           "earningsandworkinghours/timeseries/kab9/lms")


def load_bot(path=BOT):
    with open(path, newline="") as f:
        return [{k: (int(v) if k == "year" else float(v) if k in GROUPS or k.startswith("mean") else v)
                 for k, v in r.items()} for r in csv.DictReader(f)]


def check(rows=None):
    """Problems: a printed mean the printed groups do not give within 0.01 (the groups are rounded), `KNOWN` apart."""
    bad = []
    for r in rows or load_bot():
        v = [r[g] for g in GROUPS]
        for col, mean in (("mean_all", sum(v) / 5), ("mean_ex_agriculture", sum(v[:4]) / 4)):
            if abs(mean - r[col]) > 0.011 and KNOWN.get((r["year"], col)) != r[col]:
                bad.append(f"{r['year']} {col}: printed {r[col]}, groups give {mean:.3f}")
    return bad


def load_mol(path=MOL):
    """{year: mean of the four quarters, 1924 = 100}."""
    with open(path, newline="") as f:
        return {int(r["year"]): sum(float(r[q]) for q in ("q1", "q2", "q3", "q4")) / 4 for r in csv.DictReader(f)}


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


NOTE_RATES = ("Wage rates divided by prices (the ONS's long-run Retail Prices Index): what a week's wage at the "
              "standard rates would buy. 1879-1912: the Board of Trade's index of the general course of wages "
              "(unweighted mean of building, coal mining, engineering, textiles and agriculture), 1900 = 100; "
              "1924-1938: the Ministry of Labour's index of weekly full-time rates of wages in a representative "
              "selection of industries, 1924 = 100. Rates, not earnings: neither counts short time, unemployment, "
              "overtime or the move of workers into better-paid trades, and the two cannot be joined (no index of the "
              "same kind for 1913-1923 is open). Real wage rates rose {r1:.0f}% from 1879 to 1900 as prices fell "
              "({w1879:.1f} to 100), then fell to {w1912:.1f} in 1912 as prices rose; between the wars money rates "
              "fell ({m1933:.1f} in 1933) but prices fell faster, so real rates rose to {w1933:.1f} in 1933 and "
              "{w1938:.1f} in 1938.")
NOTE_AWE = ("Average weekly earnings, whole economy, total pay (ONS series KAB9), yearly, at {y1} prices (divided by "
            "the Retail Prices Index). Earnings, not rates: they include bonuses and overtime and change with the mix "
            "of jobs. The RPI rises faster than the official CPI and CPIH (the ONS no longer counts it a national statistic), "
            "so the fall since 2007 is larger here than on those measures. £{a2000:.0f} a week in 2000 was £{r2000:.0f} at {y1} prices; earnings peaked at £{peak:.0f} in "
            "{ypeak}, fell to £{low:.0f} in {ylow} and were £{r1:.0f} in {y1}.")


def series(bot, mol, pounds, prices):
    w1 = real({r["year"]: r["mean_all"] for r in bot}, prices, 1900)
    w2 = real(mol, prices, 1924)
    y1 = max(y for y in pounds if y in prices)
    a = at_prices({y: v for y, v in pounds.items() if y in prices}, prices, y1)
    ypeak = max((y for y in a if y < 2014), key=a.get)
    ylow = min((y for y in a if y > ypeak), key=a.get)
    rows = [
        _row("wages_real_uk", "Real wage rates, 1879-1912 and 1924-1938", "1879-1912 (1900 = 100)",
             "index of wage rates over prices", ["bot_labour_abstract_16", "stat_abstract_wages_uk", "ons_cdko"],
             "United Kingdom", NOTE_RATES.format(r1=w1[1900] / w1[1879] * 100 - 100, w1879=w1[1879], w1912=w1[1912],
                                                 m1933=mol[1933], w1933=w2[1933], w1938=w2[1938]),
             ["wages_real_1924_uk"], unit=""),
        _row("wages_real_1924_uk", "Real wage rates, 1924-1938", "1924-1938 (1924 = 100)",
             "index of wage rates over prices", ["stat_abstract_wages_uk", "ons_cdko"], "United Kingdom", unit=""),
        _row("wages_awe_real_uk", f"Average weekly earnings at {y1} prices, 2000-{y1}", "Average weekly earnings",
             f"£ a week at {y1} prices", ["ons_kab9", "ons_cdko"], "United Kingdom",
             NOTE_AWE.format(y1=y1, a2000=pounds[2000], r2000=a[2000], peak=a[ypeak], ypeak=ypeak, low=a[ylow],
                             ylow=ylow, r1=a[y1]), unit="£"),
    ]
    rows[0]["zero"] = rows[1]["zero"] = False
    rows[2]["zero"] = False
    return {"wages_real_uk": w1, "wages_real_1924_uk": w2, "wages_awe_real_uk": a}, rows


def write(points, rows):
    for sid, p in points.items():
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
    points, rows = series(bot, load_mol(), awe(log), change_prices.rpi(log))
    write(points, rows)
    for r in rows:
        log(f"{r['id']}: {(r.get('note') or '')[-220:]}")


if __name__ == "__main__":
    run(lambda m: print(m, file=sys.stderr, flush=True))
