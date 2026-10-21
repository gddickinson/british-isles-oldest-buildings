"""Notable objects kept in catalogue buildings (P276 location = building): bells, clocks,
windows, manuscripts, artworks, relics. Events (dated) and structures (with coordinates) are
excluded; the best-known MAX_PER_BUILDING objects per building are kept."""
import re
from urllib.parse import unquote

from .http import sparql
from .wikidata import english_form

MAX_PER_BUILDING = 15
# types that are events, organisations, places or abstractions rather than objects
NOT_OBJECT = re.compile(r"event|festival|concert|exhibition|season|competition|match|tournament|"
                        r"contest|lecture|league|club|business|organi[sz]ation|company|shipping line|"
                        r"military unit|squadron|flight|pub|hotel|restaurant|room|chapel|museum|"
                        r"estate|tree|station|legal case|pattern|literary work|version|round|"
                        r"collection|school|society|service|award|position|office", re.I)


def _qid(uri):
    return uri.rsplit("/", 1)[-1]


def objects_in(building_ids, log=print):
    """[{id, name, description, type, building_id, image, title, sitelinks}]"""
    found, classes = {}, {}
    ids = sorted(b for b in building_ids if b and b.startswith("Q"))
    for i in range(0, len(ids), 300):
        values = " ".join("wd:" + q for q in ids[i:i + 300])
        rows = sparql(f"""SELECT ?o ?oLabel ?oDescription ?b ?clsLabel ?img ?article ?n WHERE {{
            VALUES ?b {{ {values} }} ?o wdt:P276 ?b .
            FILTER NOT EXISTS {{ ?o wdt:P625 [] }} FILTER NOT EXISTS {{ ?o wdt:P585 [] }}
            FILTER NOT EXISTS {{ ?o wdt:P580 [] }} FILTER NOT EXISTS {{ ?o wdt:P31 wd:Q5 }}
            OPTIONAL {{ ?o wdt:P31 ?cls }} OPTIONAL {{ ?o wdt:P18 ?img }}
            OPTIONAL {{ ?article schema:about ?o; schema:isPartOf <https://en.wikipedia.org/> }}
            OPTIONAL {{ ?o wikibase:sitelinks ?n }}
            SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en". }} }}""")
        for r in rows:
            val = lambda k: (r.get(k) or {}).get("value")
            q = _qid(val("o"))
            if val("clsLabel"):
                classes.setdefault(q, set()).add(val("clsLabel"))
            if q in found or (val("oLabel") or "").startswith("Q"):
                continue
            found[q] = {"id": q, "name": english_form(val("oLabel")), "description": val("oDescription"),
                        "type": val("clsLabel"), "building_id": _qid(val("b")),
                        "image": unquote(val("img").rsplit("/", 1)[-1]) if val("img") else None,
                        "title": unquote(val("article").rsplit("/", 1)[-1]).replace("_", " ")
                        if val("article") else None, "sitelinks": int(val("n") or 0)}
    found = {q: o for q, o in found.items()
             if not any(NOT_OBJECT.search(c) for c in classes.get(q, ()))}
    per = {}
    for o in found.values():
        per.setdefault(o["building_id"], []).append(o)
    kept = []
    for objs in per.values():
        objs.sort(key=lambda o: -o["sitelinks"])
        kept.extend(objs[:MAX_PER_BUILDING])
    log(f"  objects in buildings: {len(found)} found, {len(kept)} kept")
    return kept
