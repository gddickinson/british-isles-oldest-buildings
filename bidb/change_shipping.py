"""Shipping for "Change over time" (roadmap C5e1): the merchant fleet registered in the United Kingdom (with the
Channel Islands and the Isle of Man) at the end of each year, 1884-1938, and merchant ships built in the United
Kingdom, 1897-1938, net tons, read from the page images of the Statistical Abstract for the United Kingdom (public
domain; Internet Archive, collection pub_annual-abstract-of-statistics-gb):

- registered (`data/curated/change/data/shipping_registered_uk.csv`): No. 46 (1884-1896, table 60, p. 177), No. 59
  (1897-1910, table 70, p. 312), No. 70 (1911-1923, table 191, p. 274), No. 83 (1924-1938, table 269, p. 360, in
  thousand tons); sailing, steam and (from 1924) motor;
- built (`shipping_built_uk.csv`): No. 59 (table 71, p. 312), No. 70 (table 192, p. 275), No. 83 (table 270, p. 361):
  all merchant vessels built, those for foreign owners included (earlier editions leave those out, so the line starts
  in 1897).

`check` tests every row's parts against its printed total. The editions overlap and agree (1911 in Nos. 59 and 70,
1924-1925 in Nos. 70 and 83). From 1923 the Irish Free State's ships are left out; the net tonnage of steamers was
raised slightly in 1914 by the Merchant Shipping Act 1907 (both noted).

    python -m bidb.change_shipping      → shipping_*_uk series csv + series.json entries
"""
import csv
import json
import sys

from .change_firms import DATA
from .change_registers import _csv, _row

FILES = {"registered": DATA / "shipping_registered_uk.csv", "built": DATA / "shipping_built_uk.csv"}
KINDS = ("steam", "motor", "sailing")
SOURCE = "stat_abstract_shipping_uk"


def load(which):
    """{year: {steam, motor, sailing, total}} in thousand net tons."""
    out = {}
    with open(FILES[which], newline="") as f:
        for r in csv.DictReader(f):
            scale = 1 if r["unit"].startswith("thousand") else 1 / 1000
            out[int(r["year"])] = {k: (float(r[k]) * scale if r[k] else 0.0) for k in KINDS + ("total",)}
            out[int(r["year"])]["raw"] = r
    return out


def check(which):
    """Problems: rows whose parts do not add to the printed total (within rounding)."""
    bad = []
    with open(FILES[which], newline="") as f:
        for r in csv.DictReader(f):
            s = sum(int(r[k] or 0) for k in KINDS)
            if abs(s - int(r["total"])) > 1:
                bad.append(f"{which} {r['year']}: parts add to {s}, printed {r['total']}")
    return bad


NOTE_REG = ("Merchant ships registered in the United Kingdom (with the Channel Islands and the Isle of Man) at the end "
            "of each year, net tons, from the Statistical Abstract (Nos. 46, 59, 70, 83): steam, motor (shown apart "
            "from 1924, with steam before) and sailing. {cross_text} The fleet grew from "
            "{t1884:.1f} million tons in 1884 to {t1914:.1f} million in 1914, lost {loss:.1f} million in the First "
            "World War (to 1918), was {t1922:.1f} million in 1922, {t1930:.1f} million in 1930 and {t1938:.1f} million in 1938; sail fell from "
            "{s1884:.1f} to {s1938:.1f} million. From 1923 ships registered in the Irish Free State are left out; "
            "steamers' net tonnage rose slightly in 1914 when the Merchant Shipping Act 1907 came fully into force.")
NOTE_BUILT = ("Merchant ships built in the United Kingdom each year, thousand net tons, ships for foreign owners "
              "included, from the Statistical Abstract (Nos. 59, 70, 83). {t1913:.0f} thousand tons in 1913; "
              "{t1915:.0f} in 1915; {t1920:.0f} in the post-war boom of 1920; {t1933:.0f} in 1933, the depth of the "
              "slump; {t1938:.0f} in 1938. Motor ships from 1924 (with steam before).")


def series(reg, built):
    cross = min(y for y, v in reg.items() if v["steam"] + v["motor"] > v["sailing"])
    cross_text = (f"Steam tonnage already exceeded sail in {cross}." if cross == min(reg)
                  else f"Steam tonnage overtook sail in {cross}.")
    pts = {"shipping_reg_steam_uk": {y: round((v["steam"] + v["motor"]) / 1000, 3) for y, v in reg.items()},
           "shipping_reg_sail_uk": {y: round(v["sailing"] / 1000, 3) for y, v in reg.items()},
           "shipping_reg_total_uk": {y: round(v["total"] / 1000, 3) for y, v in reg.items()},
           "shipping_built_uk": {y: round(v["total"], 1) for y, v in built.items()}}
    t, s = pts["shipping_reg_total_uk"], pts["shipping_reg_sail_uk"]
    b = pts["shipping_built_uk"]
    unit = "million net tons"
    rows = [_row("shipping_reg_total_uk", "Merchant fleet registered in the UK, 1884-1938", "All ships", unit, [SOURCE],
                 "United Kingdom", NOTE_REG.format(cross_text=cross_text, t1922=t[1922], t1930=t[1930], t1884=t[1884], t1914=t[1914], loss=t[1914] - t[1918],
                                                   t1938=t[1938], s1884=s[1884], s1938=s[1938]),
                 ["shipping_reg_steam_uk", "shipping_reg_sail_uk"], unit="m t"),
            _row("shipping_reg_steam_uk", "Merchant fleet: steam and motor", "Steam and motor", unit, [SOURCE],
                 "United Kingdom", unit="m t"),
            _row("shipping_reg_sail_uk", "Merchant fleet: sail", "Sail", unit, [SOURCE], "United Kingdom", unit="m t"),
            _row("shipping_built_uk", "Merchant ships built in the UK, 1897-1938", "Ships built", "thousand net tons",
                 [SOURCE], "United Kingdom", NOTE_BUILT.format(**{f"t{y}": b[y] for y in (1913, 1915, 1920, 1933, 1938)}),
                 unit="k t")]
    for r in rows:
        r["theme"] = "Industry and energy"
    return pts, rows


def write(pts, rows):
    for sid, p in pts.items():
        _csv(sid, sorted(p.items()))
    path = DATA.parent / "series.json"
    ids = {r["id"] for r in rows}
    keep = [s for s in json.loads(path.read_text()) if s["id"] not in ids]
    path.write_text(json.dumps(keep + rows, ensure_ascii=False, indent=1))


def run(log=print):
    bad = check("registered") + check("built")
    if bad:
        raise ValueError("; ".join(bad))
    reg, built = load("registered"), load("built")
    if sorted(reg) != list(range(1884, 1939)) or sorted(built) != list(range(1897, 1939)):
        raise ValueError("years missing")
    pts, rows = series(reg, built)
    write(pts, rows)
    for r in rows:
        if r.get("note"):
            log(r["note"][:400])


if __name__ == "__main__":
    run(lambda m: print(m, file=sys.stderr, flush=True))
