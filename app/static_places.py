"""Static export of places of interest and people (used by app.static_export)."""
import json

from bidb import places_db, pron_db

TRIM = {"description": 400, "wikipedia_extract": 600}
# external images are blocked in the hosted sandbox, so image fields are left out
DROP = {"image_thumb", "image_page"}


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
        rows.append(d)
    names = write_shards(rows, "places")
    # light index for building pages ("related": objects kept there, places nearby) without the 50 MB
    geo = [[r["id"], r["name"], r.get("lat"), r.get("lon"), r.get("kind_label"), r.get("kind_group"),
            r.get("date_text"), r.get("building_id")] for r in rows]
    (out_dir / "places_geo.json").write_text(json.dumps(geo, ensure_ascii=False, separators=(",", ":")))
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
