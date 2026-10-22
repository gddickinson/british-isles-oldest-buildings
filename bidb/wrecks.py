"""Build stage / CLI: shipwrecks and losses at sea from the official wreck inventories -> "Maritime heritage".

    python -m bidb.wrecks            fetch (cached) and write
    python -m bidb.wrecks --report   counts

Scotland: Canmore's maritime records (Historic Environment Scotland, OGL), those recorded as wrecks
(FORM 'WRK'); the year of loss is in the site type, e.g. "DUTCH EAST INDIAMAN (17TH CENTURY)-(1664)".
Ireland: the Wreck Inventory of Ireland (National Monuments Service, CC BY 4.0; data.gov.ie CSV), the wrecks with a
position; their nation is set later by bidb.nation_geo.
England's and Wales's protected wrecks come from bidb.registers; Wikidata's shipwrecks from the place kinds.
Each wreck is placed at its recorded position, dated by its year of loss (date text "lost 1664").
"""
import re
import sys
import time

from .place_records import blank
from .registers_client import arcgis

GROUP = "Maritime heritage"
KINDS = ("wreck",)
CANMORE = "https://inspire.hes.scot/arcgis/rest/services/CANMORE/Canmore_Points/MapServer/1"
IRELAND_CSV = "https://www.arcgis.com/sharing/rest/content/items/d4b084c880b546fabe38345461b563d2/data"
ATTRIBUTION = {
    "Canmore": "Canmore, Historic Environment Scotland (Open Government Licence).",
    "Wreck Inventory of Ireland": "Wreck Inventory of Ireland, National Monuments Service, Department of Housing, "
                                  "Local Government and Heritage (CC BY 4.0).",
}
_YEAR = re.compile(r"\((1[0-9]{3}|20[0-2][0-9])\)")
_CENTURY = re.compile(r"\((\d{1,2})(ST|ND|RD|TH) CENTURY\)")


def loss_year(site_type):
    """(year, text) from a Canmore site type: the year in brackets, else the century's start."""
    m = _YEAR.findall(site_type or "")
    if m:
        return int(m[-1]), f"lost {m[-1]}"
    c = _CENTURY.search(site_type or "")
    if c:
        n = int(c.group(1))
        return (n - 1) * 100 + 1, f"lost in the {n}{c.group(2).lower()} century"
    return None, None


def vessel(site_type):
    """'DUTCH EAST INDIAMAN (17TH CENTURY)-(1664)' -> 'Dutch East Indiaman'."""
    t = re.sub(r"\(.*?\)", "", (site_type or "").split("-(")[0]).strip(" -,")
    return t.capitalize() if t else None


def canmore(log=print):
    rows = arcgis(CANMORE, "CANMOREID,NMRSNAME,SITETYPE,COUNCIL,URL", where="FORM = 'WRK'", paging="fid", page=1000)
    out = []
    for a, lat, lon in rows:
        if lat is None or not a.get("NMRSNAME"):
            continue
        year, text = loss_year(a.get("SITETYPE"))
        kind = vessel(a.get("SITETYPE"))
        if kind and kind.lower().startswith(("obstruction", "debris", "fouling")):
            continue                                   # seabed obstructions, not identified wrecks
        name = a["NMRSNAME"].title().replace("'S ", "'s ")
        out.append(blank(f"canmore-{a['CANMOREID']}", "wreck", name, kind_label="Shipwreck or loss", kind_group=GROUP,
                         type=kind or "Wreck", description=f"{kind or 'Wreck'} recorded by Canmore" if kind else None,
                         year_start=year, date_text=text, lat=lat, lon=lon, nation="Scotland",
                         locality=(a.get("COUNCIL") or "").title() or None, url=a.get("URL"), source="Canmore"))
    log(f"  Canmore wrecks: {len(out)} of {len(rows)}")
    return out


def _csv(text):
    import csv
    import io
    return list(csv.DictReader(io.StringIO(text.lstrip("\ufeff"))))


def ireland(log=print):
    from .http import request_json
    rows = request_json(IRELAND_CSV, extract=_csv)
    out = []
    for a in rows:
        name = (a.get("Wreck Name") or "").strip()
        try:
            lat, lon = float(a.get("DD_Lat") or 0), float(a.get("DD_Long") or 0)
        except ValueError:
            continue
        if not name or abs(lat) < 1 or abs(lon) < 0.01:
            continue                                   # most of the inventory has no position (0, 0)
        year = (a.get("Date_of_Loss_Year_Only") or "").strip()
        year = int(year) if year.isdigit() and 500 < int(year) < 2030 else None
        kind = (a.get("Classification") or "").strip() or None
        desc = " ".join(x for x in ((a.get("Description") or "").strip(), ) if x) or None
        out.append(blank(f"iwi-{a.get('Wreck No') or name}", "wreck", name.title() if name.isupper() else name,
                         kind_label="Shipwreck or loss", kind_group=GROUP, type=kind or "Wreck",
                         description=desc, year_start=year,
                         date_text=f"lost {(a.get('Date of Loss') or '').strip() or year}" if year else None,
                         lat=lat, lon=lon, locality=(a.get("Place of Loss") or "").strip()[:120] or None,
                         source="Wreck Inventory of Ireland"))
    log(f"  Irish wrecks with a position: {len(out)} of {len(rows)}")
    return out


def nearest_nations(conn, cell=0.5):
    """Wrecks without a nation (the Irish inventory) take that of the nearest catalogue building (grid search in
    rings of `cell` degrees; wrecks lie off the coast, beyond bidb.nation_geo's reach)."""
    grid = {}
    for lat, lon, nation in conn.execute("SELECT lat, lon, nation FROM buildings WHERE lat IS NOT NULL AND nation IS NOT NULL"):
        grid.setdefault((int(lat // cell), int(lon // cell)), []).append((lat, lon, nation))
    rows = conn.execute("SELECT id, lat, lon FROM places WHERE kind = 'wreck' AND nation IS NULL").fetchall()
    updates = []
    for pid, lat, lon in rows:
        ci, cj = int(lat // cell), int(lon // cell)
        for ring in range(0, 8):
            near = [b for i in range(ci - ring, ci + ring + 1) for j in range(cj - ring, cj + ring + 1)
                    if max(abs(i - ci), abs(j - cj)) == ring for b in grid.get((i, j), ())]
            if near:
                best = min(near, key=lambda b: (b[0] - lat) ** 2 + ((b[1] - lon) * 0.6) ** 2)
                updates.append((best[2], pid))
                break
    conn.executemany("UPDATE places SET nation = ? WHERE id = ?", updates)
    # far out in the Atlantic (Ireland's inventory reaches 300 km and more offshore): Ireland's waters
    conn.execute("UPDATE places SET nation = 'Republic of Ireland' WHERE kind = 'wreck' AND nation IS NULL "
                 "AND source = 'Wreck Inventory of Ireland'")
    return len(updates)


def run(log=print):
    from . import place_stage
    from .classify import period_for
    from .db import connect
    t0 = time.time()
    lg = lambda m: log(f"[{time.time() - t0:5.0f}s] {m}")
    recs = canmore(lg) + ireland(lg)
    for r in recs:
        r["period"] = period_for(r["year_start"]) if r.get("year_start") is not None else "Unknown"
    conn = connect()
    conn.execute("PRAGMA busy_timeout = 120000")
    place_stage.write(conn, recs, KINDS, GROUP, lambda kind, r: False, lg)
    lg(f"{nearest_nations(conn)} wrecks without a nation given the nearest catalogue building's")
    conn.commit()
    lg(f"{len(recs)} wrecks written")


def report():
    from .db import connect
    conn = connect()
    print(dict(conn.execute("SELECT source, COUNT(*) FROM places WHERE kind = 'wreck' GROUP BY 1").fetchall()))


if __name__ == "__main__":
    report() if sys.argv[1:] == ["--report"] else run()
