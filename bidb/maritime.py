"""Build stage / CLI: maritime heritage -> places group "Maritime heritage" (run after bidb.places_build).

    python -m bidb.maritime            fetch (cached) and add / regroup
    python -m bidb.maritime --report   counts

Wikidata items in the isles with coordinates: harbours and ports, docks, dry docks and wharves,
shipyards, slipways and boatyards, ropewalks, custom houses, lighthouses, lifeboat stations, naval
bases and museum ships; and shipbuilding firms (industry: shipbuilding), placed at their yard or
headquarters, with founding and closing years. Items already in the building catalogue stay there;
places already in the database (e.g. a dock filed under industrial heritage) move to this group.
"""
import argparse
import json
import time

from .db import connect
from .http import sparql
from .lore_places import ISLES, in_box, point
from .place_records import PLACE_COLUMN_NAMES, blank

GROUP = "Maritime heritage"
# kind: (label, Wikidata classes)
CLASSES = {
    "harbour": ("Harbour or port", ["Q283202", "Q44782", "Q1420027"]),
    "dock": ("Dock or wharf", ["Q124282", "Q811177", "Q25958098", "Q828909"]),
    "shipyard": ("Shipyard or slipway", ["Q190928", "Q5478125", "Q20820202", "Q361945"]),
    "ropewalk": ("Ropewalk", ["Q1249556", "Q41085665"]),
    "customhouse": ("Custom house", ["Q218653"]),
    "lighthouse": ("Lighthouse", ["Q39715"]),
    "lifeboat": ("Lifeboat station", ["Q11997323"]),
    "naval": ("Naval base or dockyard", ["Q1324633"]),
    "museumship": ("Museum ship", ["Q575727"]),
}
KINDS = tuple(CLASSES) + ("shipbuilder",)


def _items(classes):
    values = " ".join("wd:" + c for c in classes)
    return sparql(f"""SELECT ?i ?iLabel ?coord ?article ?desc ?start ?end WHERE {{
        VALUES ?cls {{ {values} }} ?i wdt:P31 ?cls ; wdt:P625 ?coord ; wdt:P17 ?c . VALUES ?c {{ {ISLES} }}
        OPTIONAL {{ ?i wdt:P571 ?s }} OPTIONAL {{ ?i wdt:P1619 ?o }} BIND(YEAR(COALESCE(?s, ?o)) AS ?start)
        OPTIONAL {{ ?i wdt:P576 ?e BIND(YEAR(?e) AS ?end) }}
        OPTIONAL {{ ?article schema:about ?i ; schema:isPartOf <https://en.wikipedia.org/> }}
        OPTIONAL {{ ?i schema:description ?desc FILTER(lang(?desc) = "en") }}
        SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en,ga,cy,gd". }} }}""")


def _shipbuilders():
    """Firms whose industry is shipbuilding, at their own coordinates or their headquarters'."""
    return sparql(f"""SELECT ?i ?iLabel ?coord ?article ?desc ?start ?end WHERE {{
        ?i wdt:P452 wd:Q474200 .
        {{ ?i wdt:P625 ?coord ; wdt:P17 ?c . }} UNION {{ ?i wdt:P159 ?hq . ?hq wdt:P625 ?coord ; wdt:P17 ?c . }}
        VALUES ?c {{ {ISLES} }}
        OPTIONAL {{ ?i wdt:P571 ?s BIND(YEAR(?s) AS ?start) }} OPTIONAL {{ ?i wdt:P576 ?e BIND(YEAR(?e) AS ?end) }}
        OPTIONAL {{ ?article schema:about ?i ; schema:isPartOf <https://en.wikipedia.org/> }}
        OPTIONAL {{ ?i schema:description ?desc FILTER(lang(?desc) = "en") }}
        SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en". }} }}""")


def _record(kind, label, r):
    from urllib.parse import unquote
    pt = point(r["coord"]["value"])
    if not pt or not in_box(*pt):
        return None
    qid = r["i"]["value"].rsplit("/", 1)[-1]
    start = int(r["start"]["value"]) if r.get("start") else None
    end = int(r["end"]["value"]) if r.get("end") else None
    title = unquote(r.get("article", {}).get("value", "").rsplit("/", 1)[-1].replace("_", " ")) or None
    date = f"{start}–{end}" if start and end else (str(start) if start else (f"until {end}" if end else None))
    return blank(qid, kind, r["iLabel"]["value"], lat=pt[0], lon=pt[1], wikidata_id=qid, type=label,
                 description=r.get("desc", {}).get("value"), year_start=start, date_text=date,
                 wikipedia_title=title, source="Wikidata", url=f"https://www.wikidata.org/wiki/{qid}")


def build(log=print):
    recs = {}
    for kind, (label, classes) in CLASSES.items():
        got = [x for x in (_record(kind, label, r) for r in _items(classes)) if x]
        for x in got:
            recs.setdefault(x["id"], x)
        log(f"  {kind}: {len(got)}")
    got = [x for x in (_record("shipbuilder", "Shipbuilder", r) for r in _shipbuilders()) if x]
    for x in got:
        recs.setdefault(x["id"], x)
    log(f"  shipbuilder: {len(got)}")
    return list(recs.values())


def run(log=print):
    from . import places_db
    from .enrich import wikipedia_intros
    t0 = time.time()
    conn = connect()
    conn.execute("PRAGMA busy_timeout = 120000")
    recs = build(log)
    in_catalogue = {q for (q,) in conn.execute("SELECT wikidata_id FROM buildings WHERE wikidata_id IS NOT NULL")}
    from .lore_places import KINDS as LORE                      # legends and literature keep their group
    keep = KINDS + LORE
    existing = {q: i for i, q in conn.execute("SELECT id, wikidata_id FROM places WHERE wikidata_id IS NOT NULL "
                                              f"AND kind NOT IN ({','.join('?' for _ in keep)})", keep)}
    moved = [existing[r["id"]] for r in recs if r["id"] in existing and r["id"] not in in_catalogue]
    new = [r for r in recs if r["id"] not in in_catalogue and r["id"] not in existing]
    intros = wikipedia_intros([r["wikipedia_title"] for r in new if r.get("wikipedia_title")])
    for r in new:
        got = intros.get(r.get("wikipedia_title") or "") or {}
        r["wikipedia_extract"] = (got.get("extract") or "")[:900] or None
        r["image_thumb"] = got.get("image")
    conn.execute(f"DELETE FROM places_fts WHERE id IN (SELECT id FROM places WHERE kind IN ({','.join('?' for _ in KINDS)}))", KINDS)
    conn.execute(f"DELETE FROM places WHERE kind IN ({','.join('?' for _ in KINDS)})", KINDS)
    ph = ", ".join("?" for _ in PLACE_COLUMN_NAMES)
    conn.executemany(f"INSERT OR REPLACE INTO places VALUES ({ph})", [[r.get(c) for c in PLACE_COLUMN_NAMES] for r in new])
    cols = places_db.PLACE_FTS
    conn.executemany(f"INSERT INTO places_fts (id, {', '.join(cols)}) VALUES (?, {', '.join('?' for _ in cols)})",
                     [[r["id"]] + [r.get(c) or "" for c in cols] for r in new])
    conn.executemany("UPDATE places SET kind_group = ? WHERE id = ?", [(GROUP, i) for i in moved])
    conn.commit()
    log(f"[{time.time() - t0:5.0f}s] maritime heritage: {len(new)} new places, {len(moved)} existing places "
        f"regrouped, {sum(1 for r in recs if r['id'] in in_catalogue)} already catalogue buildings")


def report(log=print):
    conn = connect()
    log(json.dumps(dict(conn.execute("SELECT kind_label, COUNT(*) FROM places WHERE kind_group = ? GROUP BY 1", (GROUP,))
                        .fetchall()), indent=1))


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--report", action="store_true")
    a = ap.parse_args()
    report() if a.report else run()


if __name__ == "__main__":
    main()
