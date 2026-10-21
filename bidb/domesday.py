"""Build stage / CLI: "mentioned in Domesday Book (1086)" -> table `domesday` (run after bidb.pronunciations).

    python -m bidb.domesday         write the table
    python -m bidb.domesday <id>    one record

Settlements recorded in Domesday Book are the Wikidata items with an OpenDomesday settlement ID
(P3118, CC0; 13,000+). A building or place is marked when it is such a settlement itself, or when
its town or parish (Wikidata P131, the `pron_towns` links made by bidb.pronunciations) is one.
Open Domesday's own statistics (households, ploughs, mills, landholders; CC BY-SA) are not used:
its API no longer answers (checked 2026-10-21) and its place pages need a grid reference Wikidata
does not hold.
"""
import json
import sys
import time

from .db import connect
from .http import sparql

COLUMNS = ["entity_id", "settlement_id", "settlement", "od_id", "itself"]


def settlements():
    """{qid: (name, Open Domesday id)} for every settlement with an OpenDomesday settlement ID."""
    rows = sparql("""SELECT ?i ?iLabel ?od WHERE { ?i wdt:P3118 ?od .
        SERVICE wikibase:label { bd:serviceParam wikibase:language "en". } }""")
    return {r["i"]["value"].rsplit("/", 1)[-1]: (r["iLabel"]["value"], r["od"]["value"]) for r in rows}


def run(log=print):
    t0 = time.time()
    conn = connect()
    conn.execute("PRAGMA busy_timeout = 120000")
    dom = settlements()
    out = {}
    for rid, qid in list(conn.execute("SELECT id, wikidata_id FROM buildings")) + list(
            conn.execute("SELECT id, wikidata_id FROM places WHERE wikidata_id IS NOT NULL")):
        if qid in dom:
            out[rid] = (rid, qid, dom[qid][0], dom[qid][1], 1)
    for rid, town in conn.execute("SELECT record_id, town_id FROM pron_towns"):
        if rid not in out and town in dom:
            out[rid] = (rid, town, dom[town][0], dom[town][1], 0)
    conn.execute("DROP TABLE IF EXISTS domesday")
    conn.execute(f"CREATE TABLE domesday ({', '.join(COLUMNS)})")
    conn.execute("CREATE INDEX domesday_entity ON domesday(entity_id)")
    conn.executemany(f"INSERT INTO domesday VALUES ({', '.join('?' for _ in COLUMNS)})", out.values())
    conn.commit()
    log(f"[{time.time() - t0:5.0f}s] Domesday: {len(dom)} settlements; {len(out)} records marked "
        f"({sum(1 for r in out.values() if r[4])} are settlements themselves)")


def for_record(conn, rid):
    if not conn.execute("SELECT 1 FROM sqlite_master WHERE name = 'domesday'").fetchone():
        return None
    r = conn.execute(f"SELECT {', '.join(COLUMNS)} FROM domesday WHERE entity_id = ?", (rid,)).fetchone()
    return dict(zip(COLUMNS, r)) if r else None


if __name__ == "__main__":
    if len(sys.argv) > 1:
        print(json.dumps(for_record(connect(), sys.argv[1]), indent=1))
    else:
        run()
