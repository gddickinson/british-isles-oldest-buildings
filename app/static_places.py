"""Static export of places of interest and people (used by app.static_export)."""
import json

from bidb import places_db, pron_db
from bidb.place_kinds import KIND_GROUP, KIND_LABEL

TRIM = {"description": 400, "wikipedia_extract": 400}   # the hosted copy may hold at most 256 MiB
# external images are blocked in the hosted sandbox, so image fields are left out
DROP = {"image_thumb", "image_page"}
WIKIDATA = "https://www.wikidata.org/wiki/"
# {kind: [label, group]}: a place's label and group are left out when they are its kind's (meta.place_kinds)
KIND_DEFAULTS = {k: [KIND_LABEL.get(k, k), KIND_GROUP.get(k)] for k in set(KIND_LABEL) | set(KIND_GROUP)}


def _trim(text, n):
    return text if len(text) <= n else text[:n].rsplit(" ", 1)[0] + " …"


def export(conn, out_dir, write_shards):
    """Write place shards (via write_shards) and people.json; returns the place shard names."""
    if not places_db.has_tables(conn):
        return []
    rows, other = [], pron_db.other_names(conn, "place")    # names in Welsh, Gaelic, Irish …
    for r in conn.execute("SELECT * FROM places ORDER BY kind_group, id"):
        d = {k: v for k, v in dict(r).items() if v not in (None, "") and k not in DROP}
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
        rows.append(d)
    names = write_shards(rows, "places")
    # light index for building pages ("related": objects kept there, places nearby) without the 50 MB
    # rows [id, name, lat, lon, label index, group index, date_text, building_id] with trailing nulls dropped
    # (labels and groups once each, coordinates to ~1 m: an artifact file holds at most 16 MB)
    lab = lambda r: r.get("kind_label") or KIND_DEFAULTS.get(r.get("kind"), [None, None])[0] or ""
    grp = lambda r: r.get("kind_group") or KIND_DEFAULTS.get(r.get("kind"), [None, None])[1] or ""
    labels = sorted({lab(r) for r in rows})
    groups = sorted({grp(r) for r in rows})
    li, gi = {v: i for i, v in enumerate(labels)}, {v: i for i, v in enumerate(groups)}
    rnd = lambda v: round(v, 5) if v is not None else None
    geo = []
    for r in rows:
        row = [r["id"], r["name"], rnd(r.get("lat")), rnd(r.get("lon")), li[lab(r)], gi[grp(r)], r.get("date_text"),
               r.get("building_id")]
        while row[-1] is None:
            row.pop()
        geo.append(row)
    (out_dir / "places_geo.json").write_text(json.dumps({"labels": labels, "groups": groups, "rows": geo},
                                                        ensure_ascii=False, separators=(",", ":")))
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
