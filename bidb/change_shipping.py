"""Shipping for "Change over time" (roadmap C5e1): the merchant fleet registered in the United Kingdom (with the
Channel Islands and the Isle of Man) at the end of each year, 1848-1938, and merchant ships built in the United
Kingdom, 1846-1938 (C5e2b1: before 1897 for British owners only), read from the page images of the Statistical Abstract for the United Kingdom (public
domain; Internet Archive, collection pub_annual-abstract-of-statistics-gb):

- registered (`data/curated/change/data/shipping_registered_abstract_uk.csv`): No. 10 (1848-1850, table 35, p. 69),
  No. 13 (1851-1863, table 36, p. 91), No. 26 (1864-1869, table 40, p. 100), No. 32 (1870-1882, table 54, p. 127),
  No. 45 (1883, table 60, p. 175), No. 46 (1884-1896, table 60, p. 177), No. 59
  (1897-1910, table 70, p. 312), No. 70 (1911-1923, table 191, p. 274), No. 83 (1924-1938, table 269, p. 360, in
  thousand tons); sailing, steam and (from 1924) motor;
- built (`shipping_built_abstract_uk.csv`): before 1897 for British owners only, bidb.change_shipping_built; No. 59 (table 71, p. 312), No. 70 (table 192, p. 275), No. 83 (table 270, p. 361):
  all merchant vessels built, those for foreign owners included (earlier editions leave those out: a break at 1897).

`check` tests every row's parts against its printed total. The editions overlap and agree (1851-1862 in Nos. 10 and
13, 1864-1865 in Nos. 13 and 26, 1870-1878 in Nos. 26 and 32, 1884 in Nos. 32 and 46, 1911 in Nos. 59 and 70,
1924-1925 in Nos. 70 and 83), except 1883's steam tonnage, 3,728,263 in Nos. 31 and 32 and 3,728,268 in No. 45, whose
figure adds to the printed total (`MISPRINTS`). Nos. 8 and 9 have no table of registered ships, so the line begins in
1848. From 1923 the Irish Free State's ships are left out; the net tonnage of steamers was
raised slightly in 1914 by the Merchant Shipping Act 1907 (both noted).

C5e2b2a: from 1939 the fleet line continues (after a break) with the Annual Abstract's steam and motor vessels
1939-1970, and a graph of merchant ships completed 1940-1974 in gross tons (bidb.change_shipping_post). C5e2b2b1: the
UK-registered trading fleet of 500 gross tons and over 1950-2025 (DfT FLE0301, bidb.change_shipping_fleet).

    python -m bidb.change_shipping      → shipping_*_uk series csv + series.json entries
"""
import csv
import json
import sys

from .change_firms import DATA
from .change_registers import _csv, _row
from . import change_shipping_built as early
from . import change_shipping_post as post
from . import change_shipping_fleet as fleet

FILES = {"registered": DATA / "shipping_registered_abstract_uk.csv", "built": DATA / "shipping_built_abstract_uk.csv"}
KINDS = ("steam", "motor", "sailing")
FIRST = 1848
MISPRINTS = {1883: "steam tonnage 3,728,263 in Nos. 31 and 32 (worn type?); 3,728,268 in No. 45, which adds to the total"}
SOURCE = "stat_abstract_shipping_uk"
POST_SOURCE = "annual_abstract_shipping_uk"
REG_BREAK = ("From 1939 the Annual Abstract (Nos. 84, 88, 94, 100, 104, 108): steam and motor vessels only (sail "
             "left out); 1939-1962 with Commonwealth and foreign vessels on bareboat charter to or requisitioned by "
             "the UK; {aa1938:.2f} million net tons in 1938 there, {sa1938:.2f} in the Statistical Abstract")


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
            "of each year, net tons, from the Statistical Abstract (Nos. 10, 13, 26, 32, 45, 46, 59, 70, 83): steam, "
            "motor (shown apart from 1924, with steam before) and sailing. {cross_text} The fleet grew from "
            "{t1848:.1f} million tons in 1848 ({st1848:.2f} million of them steam) to {t1865:.1f} million in 1865, "
            "{t1884:.1f} million in 1884 and {t1914:.1f} million in 1914, lost {loss:.1f} million in the First "
            "World War (to 1918), was {t1922:.1f} million in 1922, {t1930:.1f} million in 1930 and {t1938:.1f} million in 1938; sail peaked at "
            "{smax:.1f} million in {ysmax} and fell to {s1938:.1f} million in 1938. From 1923 ships registered in the Irish Free State are left out; "
            "steamers' net tonnage rose slightly in 1914 when the Merchant Shipping Act 1907 came fully into force. "
            "From 1939 the line comes from the Annual Abstract (Ministry of Transport, later the "
            "Board of Trade): steam and motor vessels only, as it no longer counts sail each year (sailing vessels and other craft without engines: "
            "414,000 net tons in 1935, 278,243 in 1966); its footnotes say that the figures for 1939-1962 include "
            "Commonwealth and foreign vessels on bareboat charter to or requisitioned by the United Kingdom. The fleet "
            "fell to {w_min:.1f} million net tons in {y_min} and was {n1946:.1f} million in 1946, {n1961:.1f} million "
            "in 1961, {n1962:.1f} million in 1962 (its gross tonnage hardly changed: {g1961:.2f} and {g1962:.2f} "
            "million) and {n1970:.1f} million in 1970 (an estimate in No. 108). Vessels under 500 gross tons rose "
            "from {s1935:,} in 1935 to {s1970:,} in 1970 (No. 104: \"including miscellaneous craft\"). After 1970 "
            "the Annual Abstract gives only ships of 500 gross tons and over: see \"UK-registered trading fleet\".")
NOTE_BUILT = ("Merchant ships built in the United Kingdom each year, thousand tons, from the Statistical Abstract: "
              "to 1896 ships for British owners only (Nos. 8, 9, 23, 26, 32, 33, 46; ships built and first registered "
              "to 1870, built whether registered or not from 1871), from 1897 all merchant ships, those for foreign "
              "owners included (Nos. 59, 70, 83, net tons); each year from the latest edition, which revised 1861, "
              "1867-1873 and 1877-1878. {t1846:.0f} thousand tons in 1846; steam first outweighed sail in "
              "{steam_first}, sail last in {sail_last}; {peak_tons:.0f} thousand in {peak}, the most for British "
              "owners before 1897; the second line counts the ships (war and merchant) built for foreigners "
              "1884-1898. {t1913:,.0f} thousand tons in 1913; {t1915:.0f} in 1915; {t1920:,.0f} in the post-war boom "
              "of 1920; {t1933:.0f} in 1933, the depth of the slump; {t1938:.0f} in 1938. Motor ships from 1924 "
              "(with steam before). From 1940 in gross tons: \"Merchant ships completed in the UK, 1940-1974\".")
NOTE_DONE = ("Merchant ships of 100 gross tons and over completed in the United Kingdom each year, thousand gross "
             "tons, from the Annual Abstract (Nos. 84, 88, 90, 94, 100, 104, 108, 112; figures of the Admiralty to No. 94, "
             "of the Ministry of Transport in No. 100 and the Ministry of Technology in No. 104), each year from the latest "
             "edition (No. 88 revised 1941 from 1,192 to 1,158). Gross tons are larger than the net tons of the graph "
             "to 1938 for the same ships: for 1938 the Statistical Abstract gives {net1938:.0f} thousand net tons "
             "built, No. 84 {l1938:,} thousand gross tons launched in the UK and Eire (Lloyd's Register: {l1935} in "
             "1935, {l1939} in 1939, not comparable with completions, it says) and Nos. 88 and 90 {lloyds} thousand "
             "from Lloyd's Register with Eire. {c1942:,} thousand gross tons were completed in 1942, the most of the "
             "war, {c1945} in 1945, {cpeak:,} in {peak}, the most of these years, {c1962:,} in 1962 and {c1964} in "
             "1964; {c1974:,} in 1974. Tankers were {t1951} thousand in 1951 and {t1969} in 1969. Ships for export "
             "(printed from 1957): {e1957} thousand in 1957, {epeak} in {eyear} ({eshare:.0f}% of all completed), "
             "{e1974} in 1974.")


def series(reg, built):
    cross = min(y for y, v in reg.items() if v["steam"] + v["motor"] > v["sailing"])
    cross_text = (f"Steam tonnage already exceeded sail in {cross}." if cross == min(reg)
                  else f"Steam (net) tonnage overtook sail in {cross}.")
    steam = {y: round((v["steam"] + v["motor"]) / 1000, 3) for y, v in reg.items()}
    pts = {"shipping_reg_steam_uk": steam,
           "shipping_reg_sail_uk": {y: round(v["sailing"] / 1000, 3) for y, v in reg.items()},
           "shipping_reg_total_uk": {**{y: round(v["total"] / 1000, 3) for y, v in reg.items()}, **post.registered()},
           "shipping_built_uk": early.joined(built),
           "shipping_built_foreign_uk": {y: round(int(r["total"]) / 1000, 1)
                                         for y, r in early.latest(foreign=True).items()},
           **post.built()}
    t, s = pts["shipping_reg_total_uk"], pts["shipping_reg_sail_uk"]
    b = pts["shipping_built_uk"]
    unit = "million net tons"
    f = post.facts()
    n, g, c, e = f["net"], f["gross"], f["total"], f["export"]
    w = {y: n[y] for y in range(1939, 1946)}
    tank = pts["shipping_completed_tankers_uk"]
    reg_extra = {"w_min": min(w.values()) / 1000, "y_min": min(w, key=w.get), "n1946": n[1946] / 1000,
                 "n1961": n[1961] / 1000, "n1962": n[1962] / 1000, "g1961": g[1961] / 1000, "g1962": g[1962] / 1000,
                 "n1970": n[1970] / 1000, "s1935": f["small"][1935], "s1970": f["small"][1970]}
    done = {"net1938": b[1938], "l1938": f["launched"][1938], "l1935": f["launched"][1935],
            "l1939": f["launched"][1939], "lloyds": f["lloyds1938"], "c1942": c[1942], "c1945": c[1945],
            "cpeak": c[f["peak"]], "peak": f["peak"], "c1962": c[1962], "c1964": c[1964], "c1974": c[1974],
            "t1951": tank[1951], "t1969": tank[1969], "e1957": e[1957], "epeak": e[f["export_peak"]],
            "eyear": f["export_peak"], "eshare": 100 * e[f["export_peak"]] / c[f["export_peak"]], "e1974": e[1974]}
    rows = [_row("shipping_reg_total_uk", "Merchant fleet registered in the UK, 1848-1970", "All ships (from 1939 steam and motor)", unit,
                 [SOURCE, POST_SOURCE],
                 "United Kingdom", NOTE_REG.format(**reg_extra, cross_text=cross_text, t1922=t[1922], t1930=t[1930], t1884=t[1884], t1914=t[1914], loss=t[1914] - t[1918],
                                                   t1938=t[1938], s1938=s[1938], t1848=t[1848], t1865=t[1865],
                                                   st1848=pts["shipping_reg_steam_uk"][1848], smax=max(s.values()),
                                                   ysmax=max(s, key=s.get)),
                 ["shipping_reg_steam_uk", "shipping_reg_sail_uk"], unit="m t"),
            _row("shipping_reg_steam_uk", "Merchant fleet: steam and motor", "Steam and motor", unit, [SOURCE],
                 "United Kingdom", unit="m t"),
            _row("shipping_reg_sail_uk", "Merchant fleet: sail", "Sail", unit, [SOURCE], "United Kingdom", unit="m t"),
            _row("shipping_built_uk", "Merchant ships built in the UK, 1846-1938", "Ships built", "thousand tons",
                 [SOURCE], "United Kingdom", NOTE_BUILT.format(**{f"t{y}": b[y] for y in (1913, 1915, 1920, 1933, 1938)},
                                                               **early.facts()),
                 ["shipping_built_foreign_uk"], unit="k t"),
            _row("shipping_built_foreign_uk", "Ships built for foreigners", "Built for foreigners (war and merchant)",
                 "thousand tons", [SOURCE], "United Kingdom", unit="k t"),
            _row("shipping_completed_uk", "Merchant ships completed in the UK, 1940-1974", "All ships completed",
                 "thousand gross tons", [POST_SOURCE], "United Kingdom", NOTE_DONE.format(**done),
                 ["shipping_completed_tankers_uk", "shipping_completed_export_uk"], unit="k gt"),
            _row("shipping_completed_tankers_uk", "Ships completed: tankers", "Tankers", "thousand gross tons",
                 [POST_SOURCE], "United Kingdom", unit="k gt"),
            _row("shipping_completed_export_uk", "Ships completed for export", "For export", "thousand gross tons",
                 [POST_SOURCE], "United Kingdom", unit="k gt")]
    rows[3]["breaks"] = early.breaks(built)
    br = [[1939, REG_BREAK.format(aa1938=n[1938] / 1000, sa1938=steam[1938])]]
    rows[0]["breaks"] = br
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
    bad = check("registered") + check("built") + early.check() + post.check("registered") + post.check("built")
    if post.overlaps() != post.REVISED:
        bad.append(f"Annual Abstract overlaps {post.overlaps()} not as REVISED")
    if early.revisions() != early.REVISED:
        bad.append(f"revisions {early.revisions()} not as REVISED")
    if bad:
        raise ValueError("; ".join(bad))
    reg, built = load("registered"), load("built")
    if sorted(reg) != list(range(FIRST, 1939)) or sorted(built) != list(range(1897, 1939)):
        raise ValueError("years missing")
    if sorted(post.registered()) != list(range(1939, post.LAST_REG + 1)) or \
            sorted(post.built()["shipping_completed_uk"]) != list(range(post.FIRST_BUILT, post.LAST_BUILT + 1)):
        raise ValueError("Annual Abstract years missing")
    fle, old = fleet.dft(log=log)
    bad = fleet.problems(fle)
    if bad:
        raise ValueError("; ".join(bad))
    pts, rows = series(reg, built)
    more, extra = fleet.series(fle, old, reg1961=int(post.latest("registered")[1961]["g_500plus"]) / 1000)
    write({**pts, **more}, rows + extra)
    for r in rows:
        if r.get("note"):
            log(r["note"][:400])


if __name__ == "__main__":
    run(lambda m: print(m, file=sys.stderr, flush=True))
