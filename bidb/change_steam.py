"""Steam power (roadmap C5e2b2b2a): graph "Power in British industry, 1760-1907".

- Kanefsky's horsepower of steam, water and wind in Great Britain at 1760, 1800, 1830, 1870 and 1907 (his 1979 Exeter
  thesis, p. 338, not open), as summarised in Crafts (2004), Economic Journal 114, Table 3 p. 342; quoted per figure in
  estimates.json (model `power_kanefsky1979`) and drawn as estimate dots on a log axis. `check`: each year's three
  sources add to the printed total (the 2003 working paper's 160,000 for steam and water in 1830 do not; the journal's
  165,000 do).
- Nuvolari, Verspagen and von Tunzelmann (2011, Cliometrica 5, open access, CC BY-NC) counted from Kanefsky's updated
  list of engines erected in the 18th century: quoted in the note only (three totals, no yearly figures).

    python -m bidb.change_steam      check, write the CSVs and series.json rows, then run bidb.change_series
"""
import json

from .change_firms import DATA
from .change_registers import _row
from .change_wages import write

ESTIMATES = DATA.parent / "estimates.json"
KINDS = ("steam", "water", "wind")


def model():
    return next(m for m in json.loads(ESTIMATES.read_text())["models"] if m["id"] == "power_kanefsky1979")


def table(m=None):
    """{kind: {year: horsepower}} for steam, water, wind and the printed total."""
    out = {}
    for p in (m or model())["points"]:
        out.setdefault(p["kind"], {})[p["year"]] = p["value"]
    return out


def check(t=None):
    """Problems: a year whose steam, water and wind do not add to the printed total, or a figure missing."""
    t = t or table()
    bad = [f"{k}: years {sorted(t[k])}" for k in KINDS if sorted(t[k]) != sorted(t["total"])]
    for y, total in sorted(t["total"].items()):
        parts = sum(t[k].get(y, 0) for k in KINDS)
        if parts != total:
            bad.append(f"{y}: steam + water + wind = {parts:,}, printed total {total:,}")
    return bad


def points(t=None):
    """{series id: [(year, value, None, None, label)]} for the three sources."""
    t = t or table()
    return {f"power_{k}_gb": [(y, v, None, None, f"Kanefsky 1979 (Crafts 2004, Table 3): {k} {v:,} hp of {t['total'][y]:,}")
                              for y, v in sorted(t[k].items())] for k in KINDS}


NOTE = ("Horsepower of the engines, water wheels and windmills at work in Great Britain, as reckoned by John Kanefsky "
        "(The Diffusion of Power Technology in British Industry, 1760-1870, Exeter thesis 1979, p. 338) and summarised "
        "by Nicholas Crafts (Economic Journal 2004, Table 3; internal combustion engines not included). These are "
        "estimates for five years, not counts: the dots are joined only to guide the eye, on a scale of powers of ten. "
        "Steam had {s1760:,} horsepower in 1760 against {w1760:,} from water, drew level with water in 1830 "
        "({s1830:,} each) and had {s1907:,} in 1907, {share1907:.0f}% of the total; water power grew until 1870 "
        "({w1870:,}) and wind's was never more than {wind_max:,}. Crafts: \"it was only in 1830 that steam reached "
        "parity with water as a source of power in the economy at which point only 165,000 steam horsepower had been "
        "installed representing about 1.5% of the total capital stock\"; Kanefsky's data are thinnest between the end "
        "of Watt's patent in 1800 and the Factory Act returns of 1838, and after 1870. Engines burned less coal as they "
        "improved: \"about 30 lb. with the Newcomen engines prior to James Watt, to 12.5 lb. with the Watt engine, 5 "
        "lb. with the move to high pressure in the mid 19th century and 2 lb with very high pressure in the early 20th "
        "century\" per horsepower an hour. Engines, not horsepower, in the 18th century (Nuvolari, Verspagen and von "
        "Tunzelmann 2011, from Kanefsky's updated list): \"From 1710 to 1733, 95 Savery-Newcomen engines were "
        "constructed\", \"In the period 1734-1774, instead, 442 engines were built\", and the list holds 2,279 "
        "engines erected by 1800, 479 of them Watt's (Jennifer Tann's count from the Boulton and Watt papers is 449). "
        "The 2003 working paper of Crafts' article prints 160,000 for steam and for water in 1830, which do not add to "
        "its total of 350,000; the journal's 165,000 do.")


def series(t=None):
    """({series id: points}, series.json rows)."""
    t = t or table()
    s, w = t["steam"], t["water"]
    note = NOTE.format(s1760=s[1760], w1760=w[1760], s1830=s[1830], s1907=s[1907],
                       share1907=s[1907] / t["total"][1907] * 100, w1870=w[1870], wind_max=max(t["wind"].values()))
    src = ["est_power_kanefsky1979", "nuvolari_2011_steam"]
    rows = [_row("power_steam_gb", "Power in British industry, 1760-1907", "steam", "horsepower (estimates)",
                 src, "Great Britain", note, ["power_water_gb", "power_wind_gb"], unit="hp"),
            _row("power_water_gb", "Water power (Kanefsky)", "water", "horsepower (estimates)", src[:1], "Great Britain",
                 unit="hp"),
            _row("power_wind_gb", "Wind power (Kanefsky)", "wind", "horsepower (estimates)", src[:1], "Great Britain",
                 unit="hp")]
    for r in rows:
        r.update(theme="Industry and energy", style="estimates", zero=False)
    rows[0]["log"] = True
    return points(t), rows


def run(log=print):
    bad = check()
    if bad:
        raise ValueError("; ".join(bad))
    pts, rows = series()
    write(pts, rows)
    log(rows[0]["note"][:400])


if __name__ == "__main__":
    run()
