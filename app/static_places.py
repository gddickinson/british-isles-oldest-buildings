"""Static export of places of interest and people (used by app.static_export)."""
import json

from bidb import places_db, pron_db
from bidb.place_kinds import KIND_GROUP, KIND_LABEL

TRIM = {"description": 300, "wikipedia_extract": 300}   # the hosted copy may hold at most 256 MiB
# external images are blocked in the hosted sandbox, so image fields are left out
DROP = {"image_thumb", "image_page"}
WIKIDATA = "https://www.wikidata.org/wiki/"
# {kind: [label, group]}: a place's label and group are left out when they are its kind's (meta.place_kinds)
# common starts of place links, written "~<n>:" + the rest (expanded in static_places.js; 3.7 MB less)
URL_PREFIXES = ["https://heritagedata.maps.arcgis.com/apps/webappviewer/index.html?id=0c9eb9575b544081b0d296436d8f60f8"
                "&query=18a4b61b268-layer-9%2CSMRS%2C",
                "https://historicengland.org.uk/listing/the-list/list-entry/", "https://openplaques.org/plaques/",
                "https://portal.historicenvironment.scot/designation/",
                "http://cadwpublic-api.azurewebsites.net/reports/sam/FullReport?lang=en&id=",
                "https://www.trove.scot/place/", "https://en.wikipedia.org/wiki/"]
# register texts that only say there is no description yet
NO_DESCRIPTION = ("We regret that we are unable to supply descriptive details",
                  "The Archaeological Survey of Ireland (ASI) is in the process of providing information")
KIND_DEFAULTS = {k: [KIND_LABEL.get(k, k), KIND_GROUP.get(k)] for k in set(KIND_LABEL) | set(KIND_GROUP)}


def _trim(text, n):
    return text if len(text) <= n else text[:n].rsplit(" ", 1)[0] + " …"


PLACE_SHARDS = 16        # a place's full row is in places_<shard_of(id)>.json (one file to open a place)
CELL_LAT, CELL_LON = 1, 2   # light rows by location: pcells/<lat>_<lon>.json (1° by 2° cells)


def shard_of(pid):
    """Stable hash of an id over UTF-16 code units, mirrored by shardOf in static_places.js."""
    h = 0
    units = pid.encode("utf-16-le")
    for i in range(0, len(units), 2):
        h = (h * 31 + int.from_bytes(units[i:i + 2], "little")) & 0xFFFFFFFF
    return h % PLACE_SHARDS


def cell_of(lat, lon):
    return f"{int(lat // CELL_LAT * CELL_LAT)}_{int(lon // CELL_LON * CELL_LON)}"


def write_index(rows, out_dir):
    """Light rows for building pages, place pages, the people pages and plain map layers, without the full
    places: [id, name, lat, lon, label index, group index, date_text, building_id, year_start] (trailing nulls dropped,
    coordinates to ~1 m) in location cells, plus places_index.json (labels, groups, cell sizes, objects kept
    in each building)."""
    import shutil
    lab = lambda r: r.get("kind_label") or KIND_DEFAULTS.get(r.get("kind"), [None, None])[0] or ""
    grp = lambda r: r.get("kind_group") or KIND_DEFAULTS.get(r.get("kind"), [None, None])[1] or ""
    labels = sorted({lab(r) for r in rows})
    groups = sorted({grp(r) for r in rows})
    li, gi = {v: i for i, v in enumerate(labels)}, {v: i for i, v in enumerate(groups)}
    rnd = lambda v: round(v, 5) if v is not None else None
    cells, objects, nowhere = {}, {}, []
    for r in rows:
        row = [r["id"], r["name"], rnd(r.get("lat")), rnd(r.get("lon")), li[lab(r)], gi[grp(r)], r.get("date_text"),
               r.get("building_id"), r.get("year_start")]
        while row[-1] is None:
            row.pop()
        if r.get("building_id"):
            objects.setdefault(r["building_id"], []).append(row)
        if r.get("lat") is None or r.get("lon") is None:
            nowhere.append(row)
        else:
            cells.setdefault(cell_of(r["lat"], r["lon"]), []).append(row)
    folder = out_dir / "pcells"
    shutil.rmtree(folder, ignore_errors=True)
    folder.mkdir()
    for key, part in cells.items():
        (folder / f"{key}.json").write_text(json.dumps(part, ensure_ascii=False, separators=(",", ":")))
    (out_dir / "places_geo.json").unlink(missing_ok=True)          # replaced by the cells (2026-10-22)
    (out_dir / "places_index.json").write_text(json.dumps(
        {"labels": labels, "groups": groups, "cell": [CELL_LAT, CELL_LON], "shards": PLACE_SHARDS,
         "cells": {k: len(v) for k, v in sorted(cells.items())}, "objects": objects, "nowhere": nowhere},
        ensure_ascii=False, separators=(",", ":")))


def export(conn, out_dir, write_shards):
    """Write place shards (via write_shards) and people.json; returns the place shard names."""
    if not places_db.has_tables(conn):
        return []
    rows, other = [], pron_db.other_names(conn, "place")    # names in Welsh, Gaelic, Irish …
    for r in conn.execute("SELECT * FROM places ORDER BY kind_group, id"):
        d = {k: v for k, v in dict(r).items() if v not in (None, "") and k not in DROP}
        if d.get("description", "").startswith(NO_DESCRIPTION):
            del d["description"]
        for k, n in TRIM.items():
            if d.get(k):
                d[k] = _trim(d[k], n)
        if d.get("extra"):
            d["extra"] = json.loads(d["extra"])
        if d["id"] in other:
            d["other_names"] = other[d["id"]]
        # Wikidata's address and id when they only repeat the record's id (rebuilt in static_places.js)
        if d.get("kind") in KIND_DEFAULTS:
            label, group = KIND_DEFAULTS[d["kind"]]
            if d.get("kind_label") == label:
                del d["kind_label"]
            if d.get("kind_group") == group:
                del d["kind_group"]
        if d.get("source") == "Wikidata":         # the commonest source: the default in static_places.js
            del d["source"]
        if d.get("wikidata_id") == d["id"]:
            del d["wikidata_id"]
            if d.get("url") == WIKIDATA + d["id"]:
                del d["url"]
        for i, start in enumerate(URL_PREFIXES):
            if d.get("url", "").startswith(start):
                d["url"] = f"~{i}:" + d["url"][len(start):]
                break
        rows.append(d)
    names = write_shards(sorted(rows, key=lambda r: shard_of(r["id"])), "places", key=lambda r: shard_of(r["id"]))
    write_index(rows, out_dir)
    persons = [{k: v for k, v in dict(r).items() if v not in (None, "") and k != "image_thumb"}
               for r in conn.execute("SELECT * FROM persons")]
    for p in persons:
        p.setdefault("sitelinks", 0)
    has_ref = "ref" in [c[1] for c in conn.execute("PRAGMA table_info(person_links)")]
    links = [list(r) for r in conn.execute(
        "SELECT person_id, target_id, target_type, role" + (", ref" if has_ref else "") + " FROM person_links")]
    for l in links:
        if len(l) > 4 and l[4]:
            l[4] = json.loads(l[4])
        elif len(l) > 4:
            l.pop()
    (out_dir / "people.json").write_text(json.dumps({"persons": persons, "links": links},
                                                    ensure_ascii=False, separators=(",", ":")))
    print(f"exported {len(rows)} places in {len(names)} files, {len(persons)} people")
    return names
