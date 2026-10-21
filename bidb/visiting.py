"""Build stage / CLI: visiting information -> table `visiting`.

    python -m bidb.visiting            fetch (cached) and write the table
    python -m bidb.visiting Q816295    one record

OpenStreetMap objects that carry a wikidata=* tag and say something about visiting (opening_hours,
fee, operator, wheelchair, website) are matched to catalogue buildings and places by that QID.
Fetched in four regional boxes from the Overpass API (cached in <cache>/basemap/, ODbL).
"""
import json
import sys
import time

from .db import connect

COLUMNS = ["entity_id", "operator", "opening_hours", "fee", "wheelchair", "website", "osm"]
BOXES = {"south": (49, -11, 52.5, 2.2), "midlands": (52.5, -11, 54.5, 2.2), "north": (54.5, -11, 57, 2.2),
         "far_north": (57, -11, 61.2, 2.2)}
CARE = ("English Heritage", "National Trust", "Historic Environment Scotland", "Historic Scotland", "Cadw",
        "Office of Public Works", "OPW", "National Trust for Scotland", "Manx National Heritage",
        "Churches Conservation Trust", "Landmark Trust", "Friends of Friendless Churches")


def fetch(log=print):
    from app.basemap_sources import overpass
    out = {}
    for name, (s, w, n, e) in BOXES.items():
        q = (f'[out:json][timeout:600];nwr["wikidata"]["opening_hours"]({s},{w},{n},{e})->.a;'
             f'nwr["wikidata"]["fee"]({s},{w},{n},{e})->.b;'
             f'nwr["wikidata"]["operator"~"{"|".join(CARE)}"]({s},{w},{n},{e})->.c;(.a;.b;.c;);out tags;')
        els = overpass(q, f"visiting_{name}", pause=5).get("elements", [])
        for el in els:
            t = el.get("tags", {})
            qid = t.get("wikidata", "").split(";")[0].strip()
            if qid.startswith("Q"):
                prev = out.get(qid, {})
                out[qid] = {**{k: v for k, v in t.items() if k in ("operator", "opening_hours", "fee", "wheelchair",
                                                                     "website", "contact:website")}, **prev,
                            "osm": prev.get("osm") or f"{el['type']}/{el['id']}"}
        log(f"  {name}: {len(els)} OSM objects")
    return out


def run(log=print):
    t0 = time.time()
    conn = connect()
    conn.execute("PRAGMA busy_timeout = 120000")
    tags = fetch(log)
    ids = {w: i for i, w in conn.execute("SELECT id, wikidata_id FROM buildings WHERE wikidata_id IS NOT NULL")}
    ids.update({w: i for i, w in conn.execute("SELECT id, wikidata_id FROM places WHERE wikidata_id IS NOT NULL")})
    rows = []
    for qid, t in tags.items():
        if qid in ids:
            rows.append((ids[qid], t.get("operator"), t.get("opening_hours"), t.get("fee"), t.get("wheelchair"),
                         t.get("website") or t.get("contact:website"), t.get("osm")))
    conn.executescript(f"""DROP TABLE IF EXISTS visiting;
        CREATE TABLE visiting ({", ".join(c + " TEXT" for c in COLUMNS)});
        CREATE INDEX idx_visiting ON visiting(entity_id);""")
    conn.executemany(f"INSERT INTO visiting VALUES ({', '.join('?' for _ in COLUMNS)})", rows)
    conn.commit()
    ops = {}
    for r in rows:
        if r[1]:
            ops[r[1]] = ops.get(r[1], 0) + 1
    log(f"[{time.time() - t0:5.0f}s] visiting information for {len(rows)} records; top operators: "
        + ", ".join(f"{k} {v}" for k, v in sorted(ops.items(), key=lambda x: -x[1])[:6]))


def for_record(conn, rid):
    if not conn.execute("SELECT 1 FROM sqlite_master WHERE name = 'visiting'").fetchone():
        return None
    r = conn.execute(f"SELECT {', '.join(COLUMNS)} FROM visiting WHERE entity_id = ?", (rid,)).fetchone()
    return dict(zip(COLUMNS, r)) if r else None


if __name__ == "__main__":
    if len(sys.argv) > 1:
        print(json.dumps(for_record(connect(), sys.argv[1]), indent=1))
    else:
        run()
