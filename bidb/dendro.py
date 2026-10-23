"""Research track / CLI / build stage: tree-ring dates of catalogue buildings -> table `dendro`.

    python -m bidb.dendro             download the database (cached), match it to the catalogue, write the table
    python -m bidb.dendro --report    catalogue dates that the tree-ring dates contradict
    python -m bidb.dendro <id>        one record

Source: the Vernacular Architecture Group's Dendrochronology Database (tree-ring, isotope and
radiocarbon dates for over 4,900 UK and Irish buildings published in the journal Vernacular
Architecture; distributed by the Archaeology Data Service, https://doi.org/10.5284/1132568, ADS terms of
use). Each dated entry (a building or a part of one: "Horton, Horton Court; North Range") is placed by
its grid reference (bidb.osgrid) and matched to the catalogue building nearby whose name it shares.
"""
import csv
import io
import json
import re
import sys
import time
import zipfile
from collections import defaultdict

from .config import USER_AGENT, cache_dir
from .db import connect, dist_km
from .osgrid import to_latlon

ZIP_URL = "https://archaeologydataservice.ac.uk/catalogue/adsdata/arch-282-15/dissemination/VA55.zip"
MASTER = "VA55-IND_FULL_TO_55_MASTER.csv"
DOI = "https://doi.org/10.5284/1132568"
KINDS = {"D": "tree-ring", "I": "tree-ring (isotope)", "C": "radiocarbon"}
COLUMNS = ["record_id", "location", "felled_from", "felled_to", "date_text", "method", "building", "structure",
           "reference", "lab", "notes", "metres"]
# words that say what a building is rather than which one it is
GENERIC = set("""the of and at in on a an st saint saints church chapel parish house hall farm farmhouse manor court
    barn cottage cottages old new priory abbey cathedral castle tower street road lane high green no main range wing
    roof north south east west rear front cross great little lower upper building buildings former site our lady
    holy blessed virgin all mary's hotel public pub tavern""".split())


def _download():
    import requests
    path = cache_dir() / "vag_dendro" / "VA55.zip"
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        r = requests.get(ZIP_URL, headers={"User-Agent": USER_AGENT}, timeout=120)
        r.raise_for_status()
        path.write_bytes(r.content)
    return path


def entries():
    """Dated entries of the database: dicts with lat/lon (from the grid reference where it agrees)."""
    with zipfile.ZipFile(_download()) as z:
        raw = z.read(MASTER)
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:                     # the VA55 file is Windows-1252 ("1507±9")
        text = raw.decode("cp1252", errors="replace")
    out = []
    for r in csv.DictReader(io.StringIO(text)):
        if r["Type"] not in KINDS or not r["Felling_date:start"].strip():
            continue
        lat, lon = (float(r["Latitude"]), float(r["Longitude"])) if r["Latitude"] else (None, None)
        ll = to_latlon(r["Grid"], irish=r["Country"] == "IR")
        if ll and (lat is None or abs(ll[0] - lat) < 0.05 and abs(ll[1] - lon) < 0.05):
            lat, lon = ll
        if lat is None:
            continue
        out.append({"location": r["Location"].strip(), "felled_from": int(r["Felling_date:start"]),
                    "felled_to": int(r["Felling_date:end"] or r["Felling_date:start"]), "date_text": r["Date"].strip(),
                    "method": KINDS[r["Type"]], "building": r["Type_bld"].strip(), "structure": r["Type_str"].strip(),
                    "reference": f"Vernacular Architecture {r['Vol']}, p. {r['Page']}", "lab": r["Lab"],
                    "notes": (r["General Notes"] or "").strip()[:600], "lat": lat, "lon": lon})
    return out


KIND_WORDS = {"castle", "cathedral", "abbey", "priory", "church", "chapel", "guildhall", "barn", "tower", "palace",
              "college", "hospital", "almshouses", "court", "manor", "hall", "inn", "mill", "bridge", "gatehouse"}
SAINTS = set("mary peter paul john andrew michael james thomas nicholas margaret helen giles george lawrence laurence "
             "martin bartholomew leonard botolph edmund luke mark matthew stephen catherine baptist evangelist".split())


def _words(text):
    text = re.sub(r"\b\w+ (?:street|road|lane|place|close|gate|row|square|walk)\b", " ", (text or "").lower())
    return re.findall(r"[a-z]+", text.replace("'s", ""))


def tokens(name):
    return {t for t in _words(name) if len(t) > 2 and t not in GENERIC}


def _index(conn):
    grid = defaultdict(list)
    for rid, name, lat, lon, year in conn.execute(
            "SELECT id, name, lat, lon, year_start FROM buildings WHERE lat IS NOT NULL "
            "AND (year_start IS NULL OR year_start >= 400)"):    # hillforts and Roman sites have no roof timbers
        grid[round(lat * 20), round(lon * 20)].append((rid, name, lat, lon, tokens(name)))
    return grid


def match(entry, grid):
    """(record id, metres) of the catalogue building this entry describes, or None.

    Either every distinctive word of the record's name that is not the town's is in the entry (within 1.5 km;
    300 m for a church named only by its saint), or the name is the town and a kind of building ("Lincoln
    Cathedral") and the entry names that kind outside its town part (within 600 m)."""
    loc = tokens(entry["location"])
    parts = entry["location"].split(",", 1)
    town = tokens(parts[0]) if len(parts) > 1 else set()
    rest_words = set(_words(parts[-1]))
    best = None
    ci, cj = round(entry["lat"] * 20), round(entry["lon"] * 20)
    for di in (-1, 0, 1):
        for dj in (-1, 0, 1):
            for rid, name, lat, lon, tok in grid.get((ci + di, cj + dj), ()):
                km = dist_km(entry["lat"], entry["lon"], lat, lon)
                if not tok or km > 1.5 or not tok & loc:
                    continue
                own = tok - town
                if own and own <= loc:
                    if own <= SAINTS and km > 0.3:
                        continue
                    score = (2, len(own), -km)
                else:
                    kinds = set(_words(name)) & KIND_WORDS
                    if own or not (tok & town) or not kinds or not kinds <= rest_words or km > 0.6:
                        continue
                    score = (1, len(tok & loc), -km)
                if best is None or score > best[0]:
                    best = (score, rid, round(km * 1000))
    return (best[1], best[2]) if best else None


def run(log=print):
    t0 = time.time()
    conn = connect()
    conn.execute("PRAGMA busy_timeout = 120000")
    grid, rows = _index(conn), []
    es = entries()
    for e in es:
        m = match(e, grid)
        if m:
            rows.append((m[0], e["location"], e["felled_from"], e["felled_to"], e["date_text"], e["method"],
                         e["building"], e["structure"], e["reference"], e["lab"], e["notes"], m[1]))
    conn.execute("DROP TABLE IF EXISTS dendro")
    conn.execute(f"CREATE TABLE dendro ({', '.join(COLUMNS)})")
    conn.execute("CREATE INDEX dendro_record ON dendro(record_id)")
    conn.executemany(f"INSERT INTO dendro VALUES ({', '.join('?' for _ in COLUMNS)})", rows)
    conn.commit()
    log(f"[{time.time() - t0:5.0f}s] tree-ring dates: {len(es)} dated entries, {len(rows)} matched to "
        f"{len({r[0] for r in rows})} catalogue buildings")


def for_record(conn, rid):
    if not conn.execute("SELECT 1 FROM sqlite_master WHERE name = 'dendro'").fetchone():
        return []
    return [dict(zip(COLUMNS, r)) for r in conn.execute(
        f"SELECT {', '.join(COLUMNS)} FROM dendro WHERE record_id = ? ORDER BY felled_from", (rid,))]


def report(conn=None):
    """Records whose catalogue year is far from their earliest tree-ring date."""
    conn = conn or connect()
    rows = conn.execute("SELECT b.id, b.name, b.year_start, b.date_source, MIN(d.felled_from), MAX(d.felled_to), "
                        "COUNT(*) FROM dendro d JOIN buildings b ON b.id = d.record_id GROUP BY b.id").fetchall()
    later = [r for r in rows if r[2] is not None and r[2] > r[4] + 50]     # catalogue says later than the timbers
    earlier = [r for r in rows if r[2] is not None and r[2] < r[4] - 150]  # catalogue says much earlier
    print(f"{len(rows)} catalogue buildings with tree-ring dates; {len(later)} dated later than their earliest "
          f"timbers, {len(earlier)} dated over 150 years before them (earlier fabric or a wrong date)")
    for title, group in (("later than the timbers", later), ("much earlier than the timbers", earlier)):
        print(f"-- {title}")
        for r in sorted(group, key=lambda r: abs(r[2] - r[4]), reverse=True)[:40]:
            print(f"  {r[0]:14} {r[1][:40]:40} catalogue {r[2]:5} ({r[3][:22]}) | felled {r[4]}-{r[5]} ({r[6]})")
    return rows


if __name__ == "__main__":
    if sys.argv[1:] == ["--report"]:
        report()
    elif sys.argv[1:]:
        print(json.dumps(for_record(connect(), sys.argv[1]), indent=1, ensure_ascii=False))
    else:
        run()
