"""Build stage / CLI: the Mapping Museums database (Birkbeck, CC BY 4.0) -> museums (run after bidb.museums).

    python -m bidb.mapping_museums            merge (download cached)
    python -m bidb.mapping_museums --report   counts

4,191 UK museums open at some time between 1960 and 2021, with subject, governance, accreditation,
size, and opening and closing years (given as ranges when uncertain). Each is matched to a Wikidata
museum place within MATCH_KM with a similar name: matches gain those details (`extra.mapping_museums`)
and are marked closed when the database says so; the rest become new museum places (kind
"mm_museum", labelled by subject like the Wikidata museums). Museums that are catalogue buildings
are matched too and left as they are.

Data downloaded from the Mapping Museums website at www.mappingmuseums.org (Mapping Museums Data,
September 2021, doi:10.18743/DATA.00171), accessed 2026-10-21.
"""
import argparse
import csv
import io
import json
import re
import time

from . import place_stage
from .db import connect, dist_km
from .http import request_json
from .place_records import blank

URL = "https://researchdata.bbk.ac.uk/id/eprint/171/1/MappingMuseumsData2021_09_30.csv"
DOI = "https://doi.org/10.18743/DATA.00171"
SOURCE = "Mapping Museums (Birkbeck)"
KINDS = ("mm_museum",)
MATCH_KM = 0.5
FIELDS = ["museum_id", "Name_of_museum", "Village,_Town_or_City", "Latitude", "Longitude", "Admin_area",
          "Accreditation", "Governance", "Size", "Subject_Matter", "Year_opened", "Year_closed", "Notes"]
# subject (first part) -> the museum label used for Wikidata museums (bidb/museums.py)
SUBJECT_LABEL = {
    "Arts": "Art museum or gallery", "Personality": "Historic house museum", "Buildings": "Historic house museum",
    "War_and_conflict": "Military museum", "Transport": "Transport or maritime museum",
    "Sea_and_seafaring": "Transport or maritime museum", "Science_and_technology": "Science, natural history or industry museum",
    "Natural_world": "Science, natural history or industry museum", "Industry_and_manufacture":
    "Science, natural history or industry museum", "Mining_and_quarrying": "Science, natural history or industry museum",
    "Medicine_and_health": "Science, natural history or industry museum",
    "Rural_Industry": "Science, natural history or industry museum", "Utilities": "Science, natural history or industry museum"}
NATIONS = ("England", "Scotland", "Wales", "Northern Ireland")
STOP = {"the", "museum", "museums", "of", "and", "gallery", "art", "&", "trust", "centre", "heritage", "collection"}


def rows():
    """The CSV as a list of dicts (only FIELDS), downloaded once and cached."""
    def parse(text):
        return [{k: r.get(k, "") for k in FIELDS} for r in csv.DictReader(io.StringIO(text.lstrip("﻿")))]
    return request_json(URL, extract=parse)


def years(value):
    """'1971:1971' -> (1971, 1971); '2007:2017' -> (2007, 2017); '9999:9999' -> None (still open)."""
    try:
        a, b = (int(x) for x in value.split(":"))
    except ValueError:
        return None
    return None if a == 9999 else (a, b)


def span_text(y):
    return None if not y else str(y[0]) if y[0] == y[1] else f"{y[0]}–{y[1]}"


def words(name):
    return {w for w in re.findall(r"[a-z0-9]+", (name or "").lower().replace("'s", "")) if w not in STOP}


def similar(a, b):
    """Names that share most of their distinctive words (or both have none left: "The Museum")."""
    wa, wb = words(a), words(b)
    if not wa or not wb:
        return (a or "").lower() == (b or "").lower()
    return len(wa & wb) / min(len(wa), len(wb)) >= 0.6


def details(r):
    opened, closed = years(r["Year_opened"]), years(r["Year_closed"])
    return {"subject": r["Subject_Matter"].replace("_", " ").replace("-", ": "),
            "governance": r["Governance"].replace("_", " ").replace("-", ": "),
            "accreditation": r["Accreditation"], "size": r["Size"], "opened": span_text(opened),
            "closed": span_text(closed), "id": r["museum_id"]}


def _candidates(conn):
    """Wikidata museum places and catalogue buildings, by 0.1-degree cell, for matching."""
    from .museums import KINDS as MUSEUM_KINDS
    out = {}
    q = ",".join("?" for _ in MUSEUM_KINDS)
    for row in conn.execute(f"SELECT id, name, lat, lon, 'place' FROM places WHERE kind IN ({q}) AND lat IS NOT NULL",
                            MUSEUM_KINDS):
        out.setdefault((round(row[2], 1), round(row[3], 1)), []).append(row)
    for row in conn.execute("SELECT id, name, lat, lon, 'building' FROM buildings WHERE lat IS NOT NULL"):
        out.setdefault((round(row[2], 1), round(row[3], 1)), []).append(row)
    return out


def match(cells, name, lat, lon):
    near = [c for dy in (-0.1, 0, 0.1) for dx in (-0.1, 0, 0.1)
            for c in cells.get((round(lat + dy, 1), round(lon + dx, 1)), [])]
    hits = [(dist_km(lat, lon, c[2], c[3]), c) for c in near if similar(name, c[1])]
    hits = [h for h in hits if h[0] <= MATCH_KM]
    return min(hits, key=lambda h: h[0])[1] if hits else None


def run(log=print):
    t0 = time.time()
    conn = connect()
    conn.execute("PRAGMA busy_timeout = 120000")
    data = rows()
    conn.execute("DELETE FROM places_fts WHERE id IN (SELECT id FROM places WHERE kind = 'mm_museum')")
    conn.execute("DELETE FROM places WHERE kind = 'mm_museum'")
    cells = _candidates(conn)
    new, enriched, in_catalogue = [], 0, 0
    for r in data:
        try:
            lat, lon = float(r["Latitude"]), float(r["Longitude"])
        except ValueError:
            continue
        d = details(r)
        hit = match(cells, r["Name_of_museum"], lat, lon)
        if hit and hit[4] == "building":
            in_catalogue += 1
        elif hit:
            (extra, typ, label) = conn.execute("SELECT extra, type, kind_label FROM places WHERE id = ?", (hit[0],)).fetchone()
            e = json.loads(extra) if extra else {}
            e["mapping_museums"] = d
            closed = f"{label} (closed)" if d["closed"] and "(closed)" not in (typ or "") else typ
            conn.execute("UPDATE places SET extra = ?, type = ? WHERE id = ?", (json.dumps(e, ensure_ascii=False), closed, hit[0]))
            enriched += 1
        else:
            label = SUBJECT_LABEL.get(r["Subject_Matter"].split("-")[0], "Museum")
            opened = years(r["Year_opened"])
            nation = next((n for n in NATIONS if f"/{n}/" in r["Admin_area"] + "/"), None)
            rec = blank(f"mm-{r['museum_id']}", "mm_museum", r["Name_of_museum"], lat=lat, lon=lon, nation=nation,
                        kind_label=label, kind_group="Museums & collections",
                        type=f"{label} (closed)" if d["closed"] else label, locality=r["Village,_Town_or_City"] or None,
                        description=r["Notes"] or None, year_start=opened[0] if opened else None,
                        date_text=(f"{span_text(opened)}–{d['closed']}" if d["closed"] else
                                   f"opened {span_text(opened)}") if opened else None,
                        source=SOURCE, url=DOI, extra=json.dumps({"mapping_museums": d}, ensure_ascii=False))
            new.append(rec)
    place_stage.insert(conn, new)
    conn.commit()
    log(f"[{time.time() - t0:5.0f}s] Mapping Museums: {len(data)} museums; {enriched} matched Wikidata museums, "
        f"{in_catalogue} catalogue buildings, {len(new)} new ({sum(1 for r in new if '(closed)' in r['type'])} closed)")


def report(log=print):
    conn = connect()
    log(json.dumps(dict(conn.execute("SELECT type, COUNT(*) FROM places WHERE kind = 'mm_museum' GROUP BY 1")
                        .fetchall()), indent=1))


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--report", action="store_true")
    a = ap.parse_args()
    report() if a.report else run()


if __name__ == "__main__":
    main()
