"""Build stage / CLI: paintings, prints and drawings of buildings and places -> table `depictions`.

    python -m bidb.depictions         write the table (run after the place stages)
    python -m bidb.depictions <id>    one record

Wikidata items that depict (P180) a catalogue building or a place and have an image (P18), with
title, artist (P170), year (P571/P577) and kind; made before NEWEST (older views of a place, "then"),
or undated. The images are on Wikimedia Commons, each file under its own licence (old works are
mostly public domain); the app shows a thumbnail and links to the file page.
"""
import json
import sys
import time
from urllib.parse import unquote

from .db import connect
from .http import sparql
from .records import commons_thumb

COLUMNS = ["entity_id", "artwork_id", "title", "creator", "year", "kind", "image", "thumb"]
NEWEST = 1950
PER_RECORD = 12


def find(qids, log=print, chunk=300):
    """{depicted qid: [row, …]} oldest first."""
    out = {}
    qids = sorted(q for q in qids if q and q.startswith("Q"))
    for i in range(0, len(qids), chunk):
        values = " ".join("wd:" + q for q in qids[i:i + chunk])
        rows = sparql(f"""SELECT ?a ?aLabel ?b ?img ?y ?cLabel ?kLabel WHERE {{
            VALUES ?b {{ {values} }} ?a wdt:P180 ?b ; wdt:P18 ?img .
            OPTIONAL {{ ?a wdt:P571 ?d }} OPTIONAL {{ ?a wdt:P577 ?p }} BIND(YEAR(COALESCE(?d, ?p)) AS ?y)
            OPTIONAL {{ ?a wdt:P170 ?c }} OPTIONAL {{ ?a wdt:P31 ?k }}
            SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en". }} }}""")
        for r in rows:
            val = lambda k: (r.get(k) or {}).get("value")
            year = int(val("y")) if val("y") else None
            if year is not None and year > NEWEST:
                continue
            art, depicted = val("a").rsplit("/", 1)[-1], val("b").rsplit("/", 1)[-1]
            title = val("aLabel") or ""
            creator = val("cLabel")
            if creator and creator.startswith("http"):          # an unknown-value creator
                creator = None
            items = out.setdefault(depicted, {})
            if art not in items and not (title.startswith("Q") and title[1:].isdigit()):
                image = unquote(val("img").rsplit("/", 1)[-1])
                items[art] = [art, title, creator, year, val("kLabel"), image, commons_thumb(image, 400)]
        if (i // chunk) % 20 == 0:
            log(f"  depictions: {min(i + chunk, len(qids))}/{len(qids)} items")
    return {q: distinct(sorted(v.values(), key=lambda x: (x[3] is None, x[3] or 0)))[:PER_RECORD] for q, v in out.items()}


def distinct(arts):
    """One of each work: impressions of the same print in several collections share title, artist and year."""
    seen, out = set(), []
    for a in arts:
        key = (a[1].lower().removeprefix(f"{(a[2] or '').lower()} - "), a[2], a[3])
        if key not in seen:
            seen.add(key)
            out.append(a)
    return out


def run(log=print):
    t0 = time.time()
    conn = connect()
    conn.execute("PRAGMA busy_timeout = 120000")
    ids = {}
    for rid, qid in list(conn.execute("SELECT id, wikidata_id FROM buildings WHERE wikidata_id IS NOT NULL")) + list(
            conn.execute("SELECT id, wikidata_id FROM places WHERE wikidata_id IS NOT NULL")):
        ids.setdefault(qid, rid)
    found = find(ids, log)
    rows = [[ids[q]] + art for q, arts in found.items() for art in arts]
    conn.execute("DROP TABLE IF EXISTS depictions")
    conn.execute(f"CREATE TABLE depictions ({', '.join(COLUMNS)})")
    conn.execute("CREATE INDEX depictions_entity ON depictions(entity_id)")
    conn.executemany(f"INSERT INTO depictions VALUES ({', '.join('?' for _ in COLUMNS)})", rows)
    conn.commit()
    log(f"[{time.time() - t0:5.0f}s] depictions: {len(rows)} artworks of {len(found)} buildings and places")


def for_record(conn, rid):
    if not conn.execute("SELECT 1 FROM sqlite_master WHERE name = 'depictions'").fetchone():
        return []
    return [dict(zip(COLUMNS, r)) for r in conn.execute(
        f"SELECT {', '.join(COLUMNS)} FROM depictions WHERE entity_id = ? ORDER BY year IS NULL, year", (rid,))]


if __name__ == "__main__":
    if len(sys.argv) > 1:
        print(json.dumps(for_record(connect(), sys.argv[1]), indent=1))
    else:
        run()
