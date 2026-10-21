"""Build stage / CLI: places of legend, haunting and literature -> extra rows in table `places`
(group "Legends & literature"), run after bidb.places_build.

    python -m bidb.lore_places            fetch (cached) and add / replace these places
    python -m bidb.lore_places --report   counts

  haunted   pages in Wikipedia's "Reportedly haunted locations" categories (UK, its nations, Ireland)
  legend    Wikidata "mythical location" and fairy forts with coordinates; Wikipedia's "Locations
            associated with Arthurian legend"; data/curated/legendary_places.json (claims placed
            where tradition puts them)
  holywell  Wikidata holy wells
  literary  places that are the narrative location (P840) of notable literary works on Wikidata;
            the works are listed with each place
Records already in the catalogue (buildings or places, by Wikidata id) are left out: their own
stories carry the legend or ghost.
"""
import argparse
import json
import time

from .config import DATA_DIR, WIKIPEDIA_API
from .db import connect
from .enrich import wikipedia_intros
from .http import request_json, sparql
from .place_kinds import BOX
from .place_records import PLACE_COLUMN_NAMES, blank

KINDS = ("haunted", "legend", "holywell", "literary")
HAUNTED_CATS = ["Category:Reportedly haunted locations in the United Kingdom",
                "Category:Reportedly haunted locations in Ireland",
                "Category:Reportedly haunted locations in the Isle of Man"]
LEGEND_CATS = ["Category:Locations associated with Arthurian legend"]
ISLES = "wd:Q145 wd:Q27 wd:Q9676 wd:Q785 wd:Q25230 wd:Q21 wd:Q22 wd:Q25 wd:Q26"
LITERARY_MIN_SITELINKS = 3


def point(value):
    """WKT "Point(lon lat)" -> (lat, lon), or None (unknown values are blank nodes)."""
    try:
        lon, lat = (float(x) for x in value[6:-1].split())
        return lat, lon
    except ValueError:
        return None


def in_box(lat, lon):
    s, w, n, e = BOX
    return lat is not None and s <= lat <= n and w <= lon <= e


def category_pages(cat, depth=2, seen=None):
    """{title: {"qid", "lat", "lon", "desc"}} for articles in a category and its subcategories."""
    seen = seen if seen is not None else set()
    out, cont = {}, {}
    if cat in seen:
        return out
    seen.add(cat)
    while True:
        res = request_json(WIKIPEDIA_API, params={
            "action": "query", "generator": "categorymembers", "gcmtitle": cat, "gcmlimit": "max",
            "gcmtype": "page|subcat", "prop": "coordinates|pageprops|description", "ppprop": "wikibase_item",
            "colimit": "max", "format": "json", "formatversion": 2, **cont}, min_interval=0.5)
        for p in res.get("query", {}).get("pages", []):
            if p.get("ns") == 14:
                if depth > 0:
                    out.update(category_pages(p["title"], depth - 1, seen))
                continue
            if p.get("ns") != 0 or p["title"].startswith("List of"):
                continue
            co = (p.get("coordinates") or [{}])[0]
            out[p["title"]] = {"qid": (p.get("pageprops") or {}).get("wikibase_item"), "lat": co.get("lat"),
                               "lon": co.get("lon"), "desc": p.get("description")}
        if "continue" not in res:
            return out
        cont = {k: v for k, v in res["continue"].items()}


def wikidata_class(classes, label, subclasses=False):
    """Items of these classes (subclasses too when asked: slow for big classes) in the isles -> {qid: {...}}."""
    values = " ".join("wd:" + c for c in classes)
    path = "wdt:P31/wdt:P279*" if subclasses else "wdt:P31"
    rows = sparql(f"""SELECT ?i ?iLabel ?coord ?article ?desc WHERE {{
        VALUES ?cls {{ {values} }} ?i {path} ?cls ; wdt:P625 ?coord ; wdt:P17 ?c .
        VALUES ?c {{ {ISLES} }}
        OPTIONAL {{ ?article schema:about ?i ; schema:isPartOf <https://en.wikipedia.org/> }}
        OPTIONAL {{ ?i schema:description ?desc FILTER(lang(?desc) = "en") }}
        SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en,ga,cy,gd". }} }}""")
    out = {}
    for r in rows:
        pt = point(r["coord"]["value"])
        if not pt:
            continue
        lat, lon = pt
        qid = r["i"]["value"].rsplit("/", 1)[-1]
        title = r.get("article", {}).get("value", "").rsplit("/", 1)[-1].replace("_", " ")
        from urllib.parse import unquote
        out[qid] = {"name": r["iLabel"]["value"], "lat": lat, "lon": lon, "desc": r.get("desc", {}).get("value"),
                    "title": unquote(title) or None, "label": label}
    return out


WORK_CLASSES = {"Q8261": "novel", "Q25379": "play", "Q5185279": "poem", "Q49084": "short story",
                "Q7725634": "literary work", "Q37484": "epic poem", "Q1279564": "short story collection"}


def literary():
    """{place qid: {"name", "lat", "lon", "works": [[title, author, year, sitelinks], …]}} for notable works
    (one query per kind of work: novels, plays, poems …) set in the isles (P840)."""
    out = {}
    for cls in WORK_CLASSES:
        rows = sparql(f"""SELECT ?loc ?locLabel ?coord ?work ?workLabel ?authorLabel ?year ?sl WHERE {{
            ?work wdt:P31 wd:{cls} ; wdt:P840 ?loc ; wikibase:sitelinks ?sl . FILTER(?sl >= {LITERARY_MIN_SITELINKS})
            ?loc wdt:P625 ?coord ; wdt:P17 ?c . VALUES ?c {{ {ISLES} }}
            OPTIONAL {{ ?work wdt:P50 ?author }} OPTIONAL {{ ?work wdt:P577 ?date BIND(YEAR(?date) AS ?year) }}
            SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en". }} }}""")
        for r in rows:
            qid = r["loc"]["value"].rsplit("/", 1)[-1]
            pt = point(r["coord"]["value"])
            if not pt:
                continue
            lat, lon = pt
            p = out.setdefault(qid, {"name": r["locLabel"]["value"], "lat": lat, "lon": lon, "works": {}})
            w = r["workLabel"]["value"]
            if w not in p["works"] or not p["works"][w][1]:
                p["works"][w] = [w, r.get("authorLabel", {}).get("value"), r.get("year", {}).get("value"),
                                 int(r["sl"]["value"])]
    for p in out.values():
        p["works"] = sorted(p["works"].values(), key=lambda x: -x[3])
    return out


def build(conn, log=print):
    known = {q for (q,) in conn.execute("SELECT wikidata_id FROM buildings WHERE wikidata_id IS NOT NULL")}
    known |= {q for (q,) in conn.execute(f"SELECT wikidata_id FROM places WHERE wikidata_id IS NOT NULL "
                                         f"AND kind NOT IN ({','.join('?' for _ in KINDS)})", KINDS)}
    recs, seen = [], set()

    def add(qid, kind, name, lat, lon, **f):
        key = f.get("id") or qid or f.get("url") or name
        if (qid and qid in known) or key in seen or not in_box(lat, lon):
            return
        seen.add(key)
        recs.append(blank(qid or key, kind, name, lat=lat, lon=lon, wikidata_id=qid, **f))

    haunted = {}
    for cat in HAUNTED_CATS:
        haunted.update(category_pages(cat))
    log(f"  haunted: {len(haunted)} articles")
    legend_pages = {}
    for cat in LEGEND_CATS:
        legend_pages.update(category_pages(cat, depth=1))
    titles = [t for t, p in {**haunted, **legend_pages}.items() if p["lat"] is not None]
    intros = wikipedia_intros(titles)
    for kind, pages, label in (("haunted", haunted, "Reportedly haunted place"),
                               ("legend", legend_pages, "Place in Arthurian legend")):
        for t, p in pages.items():
            if p["lat"] is None:
                continue
            add(p["qid"], kind, t, p["lat"], p["lon"], description=p["desc"], type=label,
                wikipedia_title=t, wikipedia_extract=(intros.get(t) or {}).get("extract", "")[:900],
                image_thumb=(intros.get(t) or {}).get("image"), source="Wikipedia",
                url="https://en.wikipedia.org/wiki/" + t.replace(" ", "_"))
    for kind, classes, label, sub in (("legend", ["Q3238337"], "Place of legend", True),
                                      ("legend", ["Q3078277"], "Fairy fort", False),
                                      ("holywell", ["Q1371047"], "Holy well", False)):
        items = wikidata_class(classes, label, sub)
        log(f"  {kind}: {len(items)} Wikidata items")
        for qid, it in items.items():
            add(qid, kind, it["name"], it["lat"], it["lon"], description=it["desc"], type=it["label"],
                wikipedia_title=it["title"], source="Wikidata", url=f"https://www.wikidata.org/wiki/{qid}")
    for c in json.loads((DATA_DIR / "curated" / "legendary_places.json").read_text())["places"]:
        add(None, "legend", c["name"], c["lat"], c["lon"], description=c["claim"], type="Place of legend (claimed)",
            nation=c.get("nation"), source="Wikipedia (curated)", url=c["source"], id=c["id"])
    lit = literary()
    log(f"  literary: {len(lit)} places")
    for qid, p in lit.items():
        works = p["works"][:12]
        text = "; ".join(f"{w[0]}" + (f" ({w[1]}" + (f", {w[2]}" if w[2] else "") + ")" if w[1] else "") for w in works)
        add(qid, "literary", p["name"], p["lat"], p["lon"], type="Setting of literary works",
            description=f"Setting of {len(p['works'])} notable work{'s' if len(p['works']) > 1 else ''}: {text}",
            extra=json.dumps({"works": [w[:3] for w in works]}, ensure_ascii=False), source="Wikidata",
            url=f"https://www.wikidata.org/wiki/{qid}")
    return recs


def write(conn, recs):
    from . import places_db
    ph = ", ".join("?" for _ in PLACE_COLUMN_NAMES)
    conn.execute(f"DELETE FROM places_fts WHERE id IN (SELECT id FROM places WHERE kind IN ({','.join('?' for _ in KINDS)}))", KINDS)
    conn.execute(f"DELETE FROM places WHERE kind IN ({','.join('?' for _ in KINDS)})", KINDS)
    conn.executemany(f"INSERT OR REPLACE INTO places VALUES ({ph})", [[r.get(c) for c in PLACE_COLUMN_NAMES] for r in recs])
    cols = places_db.PLACE_FTS
    conn.executemany(f"INSERT INTO places_fts (id, {', '.join(cols)}) VALUES (?, {', '.join('?' for _ in cols)})",
                     [[r["id"]] + [r.get(c) or "" for c in cols] for r in recs])
    conn.commit()


def run(log=print):
    t0 = time.time()
    conn = connect()
    conn.execute("PRAGMA busy_timeout = 120000")
    recs = build(conn, log)
    write(conn, recs)
    report(conn, lambda m: log(f"[{time.time() - t0:5.0f}s] {m}"))


def report(conn=None, log=print):
    conn = conn or connect()
    log("places of legend, haunting and literature: " + ", ".join(
        f"{k} {n}" for k, n in conn.execute(f"SELECT kind, COUNT(*) FROM places WHERE kind IN "
                                            f"({','.join('?' for _ in KINDS)}) GROUP BY kind", KINDS)))


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--report", action="store_true")
    a = ap.parse_args()
    report() if a.report else run()


if __name__ == "__main__":
    main()
