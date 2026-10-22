"""Shared helpers for the place stages that add a places group from Wikidata classes
(underground, military, museums, bridges).

    query(where)            items matching a SPARQL pattern, with coordinates, opening and closing years
    subclass_items(root)    {qid: set of classes} for every item of a class or its subclasses
    write(conn, recs, …)    replace the stage's places, regroup existing ones, keep catalogue buildings
"""
import json

from .http import sparql
from .lore_places import ISLES

COUNTRIES = ["wd:Q145", "wd:Q27", "wd:Q9676", "wd:Q785", "wd:Q25230"]   # UK, Ireland, Man, Jersey, Guernsey
DISUSED = "wd:Q11639308 wd:Q63065035 wd:Q56651571"   # state of use: decommissioned, abandoned, out of service
CANCELLED = "Q30108381"                                 # never built
# kinds that never move to another group (plus every kind made by a group stage: protected())
STAY = ("plaque", "find", "object", "event", "kept")


def protected():
    """Kinds made by the group stages (legends, maritime, underground, military, museums, bridges):
    a place one of them made is never taken by another."""
    from . import bridges, digs, hoards, lore_places, mapping_museums, maritime, military, museums, underground
    return set(STAY) | {k for m in (lore_places, maritime, underground, military, museums, mapping_museums, bridges,
                                    hoards, digs) for k in m.KINDS}


def query(where, wp_only=False):
    """Rows (i, iLabel, coord, article, desc, start, end, closed) for items matching `where`."""
    article = ("?article schema:about ?i ; schema:isPartOf <https://en.wikipedia.org/> ." if wp_only else
               "OPTIONAL { ?article schema:about ?i ; schema:isPartOf <https://en.wikipedia.org/> }")
    return sparql(f"""SELECT ?i ?iLabel ?coord ?article ?desc ?start ?end ?closed WHERE {{
        {where} ?i wdt:P625 ?coord ; wdt:P17 ?c . VALUES ?c {{ {ISLES} }}
        OPTIONAL {{ ?i wdt:P1619 ?o }} OPTIONAL {{ ?i wdt:P571 ?s }} BIND(YEAR(COALESCE(?o, ?s)) AS ?start)
        OPTIONAL {{ ?i wdt:P3999 ?x }} OPTIONAL {{ ?i wdt:P576 ?d }} BIND(YEAR(COALESCE(?x, ?d)) AS ?end)
        OPTIONAL {{ ?i wdt:P5817 ?st VALUES ?st {{ {DISUSED} }} }} BIND(BOUND(?st) AS ?closed)
        FILTER NOT EXISTS {{ ?i wdt:P5817 wd:{CANCELLED} }}
        {article}
        OPTIONAL {{ ?i schema:description ?desc FILTER(lang(?desc) = "en") }}
        SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en,ga,cy,gd". }} }}""")


def subclass_items(root):
    """{qid: set of P31 classes} for every item with coordinates in the isles whose class is `root` or
    one of its subclasses (one query per country keeps each one light)."""
    out = {}
    for c in COUNTRIES:
        for r in sparql(f"""SELECT DISTINCT ?i ?cls WHERE {{ ?i wdt:P31 ?cls ; wdt:P17 {c} ; wdt:P625 [] .
                ?cls wdt:P279* wd:{root} . }}"""):
            out.setdefault(r["i"]["value"].rsplit("/", 1)[-1], set()).add(r["cls"]["value"].rsplit("/", 1)[-1])
    return out


def rows_for(qids, size=300):
    """query() rows for a list of items, in batches."""
    ids = sorted(qids)
    for i in range(0, len(ids), size):
        yield from query(f"VALUES ?i {{ {' '.join('wd:' + q for q in ids[i:i + size])} }}")


def write(conn, recs, kinds, group, may_move, log=print):
    """Replace this stage's places (`kinds`) with `recs`, leaving catalogue buildings alone.

    Places already in the database from other stages move to `group` with the new label when
    may_move(their kind, new record) is true; their kind stays, so their own stage can rebuild them.
    Returns (new records, moved place ids, Wikidata ids in the catalogue)."""
    from .enrich import wikipedia_intros
    in_catalogue = {q for (q,) in conn.execute("SELECT wikidata_id FROM buildings WHERE wikidata_id IS NOT NULL")}
    keep = protected()
    q = ",".join("?" for _ in kinds)
    existing = {w: (i, k) for i, w, k in conn.execute(
        f"SELECT id, wikidata_id, kind FROM places WHERE wikidata_id IS NOT NULL AND kind NOT IN ({q})", kinds)}
    moved = [(r["kind_label"], existing[r["id"]][0]) for r in recs if r["id"] in existing
             and r["id"] not in in_catalogue and existing[r["id"]][1] not in keep
             and may_move(existing[r["id"]][1], r)]
    new = [r for r in recs if r["id"] not in in_catalogue and r["id"] not in existing]
    intros = wikipedia_intros([r["wikipedia_title"] for r in new if r.get("wikipedia_title")])
    for r in new:
        got = intros.get(r.get("wikipedia_title") or "") or {}
        r["wikipedia_extract"] = (got.get("extract") or "")[:900] or None
        r["image_thumb"] = got.get("image")
        if isinstance(r.get("extra"), dict):
            r["extra"] = json.dumps(r["extra"], ensure_ascii=False)
    conn.execute(f"DELETE FROM places_fts WHERE id IN (SELECT id FROM places WHERE kind IN ({q}))", kinds)
    conn.execute(f"DELETE FROM places WHERE kind IN ({q})", kinds)
    insert(conn, new)
    conn.executemany("UPDATE places SET kind_group = ?, kind_label = ? WHERE id = ?", [(group, lab, i) for lab, i in moved])
    log(f"{group}: {len(new)} new places, {len(moved)} existing places regrouped, "
        f"{sum(1 for r in recs if r['id'] in in_catalogue)} already catalogue buildings")
    return new, [i for _, i in moved], in_catalogue


def insert(conn, recs):
    """Insert place records and their full-text rows."""
    from . import places_db
    from .place_records import PLACE_COLUMN_NAMES
    ph = ", ".join("?" for _ in PLACE_COLUMN_NAMES)
    conn.executemany(f"INSERT OR REPLACE INTO places VALUES ({ph})", [[r.get(c) for c in PLACE_COLUMN_NAMES] for r in recs])
    cols = places_db.PLACE_FTS
    conn.executemany(f"INSERT INTO places_fts (id, {', '.join(cols)}) VALUES (?, {', '.join('?' for _ in cols)})",
                     [[r["id"]] + [r.get(c) or "" for c in cols] for r in recs])


def report(conn, group):
    return dict(conn.execute("SELECT kind_label, COUNT(*) FROM places WHERE kind_group = ? GROUP BY 1", (group,)).fetchall())
