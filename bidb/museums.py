"""Build stage / CLI: museums, galleries and collections -> places group "Museums & collections".

    python -m bidb.museums            fetch (cached) and add / regroup (run after bidb.military)
    python -m bidb.museums --report   counts

Wikidata items in the isles with coordinates:
  museum       museums of every kind (any subclass of museum), closed ones shown as closed
  artmuseum    art museums, art galleries and sculpture gardens
  housemuseum  historic house, biographical and literary museums
  milmuseum    military, regimental and naval museums
  transmuseum  transport, railway, aviation, motor and maritime museums
  scimuseum    science, natural history, technology, medicine, industry and mining museums
  library      archives, national, research and academic libraries, and libraries with an article
Heritage railways, museum ships, visitor and nature centres are left to their own groups. Each
museum keeps its best-known objects (Wikidata P195 collection or P276 location; `extra.kept_here`);
finds whose "now kept at" names a museum here link to it (`extra.now_in_ids`), and the kept objects
not yet among the places become searchable "Object in a museum" places at the museum (attached to
it when the museum is a catalogue building, so they show under "Notable objects here"). Items already
in the building catalogue stay there; Victorian and industrial places that are museums move here.
"""
import argparse
import json
import time
from urllib.parse import unquote

from .db import connect
from .http import sparql
from .maritime import _record
from . import place_stage
from .place_stage import query as _query, rows_for, subclass_items

GROUP = "Museums & collections"
MUSEUM = "Q33506"
# kind: (label, classes that decide it); checked in this order, "museum" otherwise
KIND_CLASSES = {
    "artmuseum": ("Art museum or gallery", {"Q207694", "Q1007870", "Q1759852"}),
    "housemuseum": ("Historic house museum", {"Q2087181", "Q10624527", "Q1865249"}),
    "milmuseum": ("Military museum", {"Q2772772", "Q7308408", "Q26958661"}),
    "transmuseum": ("Transport or maritime museum", {"Q18704634", "Q2516357", "Q4828724", "Q1863818", "Q787934"}),
    "scimuseum": ("Science, natural history or industry museum", {"Q1970365", "Q588140", "Q2398990", "Q3329663",
                                                                  "Q1662089", "Q819426", "Q1093436"}),
    "library": ("Library or archive", {"Q166118", "Q22806", "Q1438040", "Q856234", "Q7075"}),
}
LABELS = {"museum": "Museum"} | {k: v[0] for k, v in KIND_CLASSES.items()}
KINDS = tuple(LABELS) + ("kept",)          # kept: an object a museum keeps (group "Finds & treasures")
NOT_MUSEUM = {"Q420962", "Q575727", "Q18411786", "Q16761700", "Q3499307"}   # left to their own groups
DEFUNCT = "Q123124127"
COUNTRIES = ["wd:Q145", "wd:Q27", "wd:Q9676", "wd:Q785", "wd:Q25230"]
OTHER_CLASSES = {"Q1007870": False, "Q166118": False, "Q22806": False, "Q1438040": False,   # False: all items
                 "Q856234": True, "Q7075": True}                                            # True: with an article
KEPT_MAX, KEPT_MIN_SITELINKS = 12, 2
REGROUP_FROM = ("industrial", "victorian_public", "victorian_leisure", "victorian_style", "railway", "engine",
                "warehouse", "mill", "mine", "ironworks", "kiln")


def _kind(classes):
    for kind, (_, cls) in KIND_CLASSES.items():
        if classes & cls:
            return kind
    return "museum"


def build(log=print):
    classes = subclass_items(MUSEUM)
    for cls, wp_only in OTHER_CLASSES.items():
        for r in _query(f"?i wdt:P31 wd:{cls} .", wp_only):
            classes.setdefault(r["i"]["value"].rsplit("/", 1)[-1], set()).add(cls)
    keep = {q: c for q, c in classes.items() if not c <= NOT_MUSEUM}
    recs = {}
    for r in rows_for(keep):
        qid = r["i"]["value"].rsplit("/", 1)[-1]
        kind = _kind(keep[qid])
        x = _record(kind, LABELS[kind], r)
        if not x or x["id"] in recs:
            continue
        if DEFUNCT in keep[qid] or (r.get("end") and r["end"]["value"]):
            x["type"] = f"{LABELS[kind]} (closed)"
        recs[x["id"]] = x
    for r in recs.values():
        r["kind_group"] = GROUP
    log(f"  museums and collections: {len(recs)} "
        + json.dumps({k: sum(r['kind'] == k for r in recs.values()) for k in KINDS}))
    return list(recs.values())


def kept_here(museum_ids, log=print):
    """{museum qid: [[name, wikipedia title, object qid, type], …]} best-known objects first."""
    found = {}
    ids = sorted(museum_ids)
    for i in range(0, len(ids), 200):
        values = " ".join("wd:" + q for q in ids[i:i + 200])
        rows = sparql(f"""SELECT ?o ?oLabel ?m ?clsLabel ?article ?n WHERE {{
            VALUES ?m {{ {values} }} {{ ?o wdt:P195 ?m }} UNION {{ ?o wdt:P276 ?m }}
            ?o wikibase:sitelinks ?n FILTER(?n >= {KEPT_MIN_SITELINKS})
            FILTER NOT EXISTS {{ ?o wdt:P625 [] }} FILTER NOT EXISTS {{ ?o wdt:P31 wd:Q5 }}
            FILTER NOT EXISTS {{ ?o wdt:P585 [] }}
            OPTIONAL {{ ?o wdt:P31 ?cls }}
            OPTIONAL {{ ?article schema:about ?o ; schema:isPartOf <https://en.wikipedia.org/> }}
            SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en". }} }}""")
        for r in rows:
            val = lambda k: (r.get(k) or {}).get("value")
            o, m = val("o").rsplit("/", 1)[-1], val("m").rsplit("/", 1)[-1]
            name = val("oLabel") or ""
            if name.startswith("Q") and name[1:].isdigit():
                continue
            title = unquote(val("article").rsplit("/", 1)[-1]).replace("_", " ") if val("article") else None
            found.setdefault(m, {}).setdefault(o, [int(val("n")), name, title, o, val("clsLabel")])
    out = {m: [x[1:] for x in sorted(objs.values(), key=lambda x: -x[0])[:KEPT_MAX]] for m, objs in found.items()}
    log(f"  kept here: {sum(len(v) for v in out.values())} objects in {len(out)} museums")
    return out


def run(log=print):
    t0 = time.time()
    conn = connect()
    conn.execute("PRAGMA busy_timeout = 120000")
    recs = build(log)
    kept = kept_here([r["id"] for r in recs], log)
    for r in recs:
        if kept.get(r["id"]):
            r["extra"] = {"kept_here": kept[r["id"]]}
    stamp = lambda m: log(f"[{time.time() - t0:5.0f}s] {m}")
    _, moved, in_catalogue = place_stage.write(conn, recs, KINDS, GROUP, lambda kind, r: kind in REGROUP_FROM, stamp)
    for pid, qid in conn.execute(f"SELECT id, wikidata_id FROM places WHERE id IN ({','.join('?' for _ in moved)})",
                                 moved).fetchall():
        if kept.get(qid):                              # regrouped places keep their extras and get these
            (extra,) = conn.execute("SELECT extra FROM places WHERE id = ?", (pid,)).fetchone()
            e = json.loads(extra) if extra else {}
            e["kept_here"] = kept[qid]
            conn.execute("UPDATE places SET extra = ? WHERE id = ?", (json.dumps(e, ensure_ascii=False), pid))
    objs = object_places(conn, kept, {r["id"]: r for r in recs}, in_catalogue)
    place_stage.insert(conn, objs)
    linked = link_finds(conn, recs)
    conn.commit()
    stamp(f"{len(objs)} objects kept in museums, {linked} finds linked to their museum")


def object_places(conn, kept, museums, in_catalogue):
    """Places for the kept objects not already among the places, at their museum."""
    from .place_records import blank
    have = {q for (q,) in conn.execute("SELECT wikidata_id FROM places WHERE wikidata_id IS NOT NULL")}
    out = {}
    for mid, objs in kept.items():
        if mid in in_catalogue:
            row = conn.execute("SELECT id, name, lat, lon, nation FROM buildings WHERE wikidata_id = ?", (mid,)).fetchone()
            m = dict(zip(("id", "name", "lat", "lon", "nation"), row)) if row else None
        else:
            m = museums.get(mid)
        if not m or m.get("lat") is None:
            continue
        for name, title, qid, typ in objs:
            if qid in have or qid in out:
                continue
            out[qid] = blank(qid, "kept", name, type=typ, lat=m["lat"], lon=m["lon"], nation=m.get("nation"),
                             locality=m["name"], wikipedia_title=title, wikidata_id=qid, source="Wikidata",
                             url=f"https://www.wikidata.org/wiki/{qid}",
                             building_id=m["id"] if mid in in_catalogue else None)
    return list(out.values())


def link_finds(conn, recs):
    """Finds and objects whose "now kept at" names a museum: extra.now_in_ids = {name: "place:<id>" or
    "building:<id>"} (museums that are catalogue buildings open as buildings)."""
    places = {i for (i,) in conn.execute("SELECT id FROM places WHERE kind_group = ?", (GROUP,))}
    buildings = {w: i for i, w in conn.execute("SELECT id, wikidata_id FROM buildings WHERE wikidata_id IS NOT NULL")}
    by_name = {}
    for r in recs:
        ref = f"place:{r['id']}" if r["id"] in places else f"building:{buildings[r['id']]}" if r["id"] in buildings else None
        if ref:
            by_name.setdefault(r["name"], ref)
    n = 0
    for pid, extra in conn.execute("SELECT id, extra FROM places WHERE extra LIKE '%now_in%'").fetchall():
        e = json.loads(extra)
        e.pop("now_in_ids", None)
        links = {name: by_name[name] for name in e.get("now_in") or [] if name in by_name}
        if links:
            e["now_in_ids"] = links
            n += 1
        conn.execute("UPDATE places SET extra = ? WHERE id = ?", (json.dumps(e, ensure_ascii=False), pid))
    return n


def report(log=print):
    log(json.dumps(place_stage.report(connect(), GROUP), indent=1))


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--report", action="store_true")
    a = ap.parse_args()
    report() if a.report else run()


if __name__ == "__main__":
    main()
