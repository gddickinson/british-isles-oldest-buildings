"""Inventions and discoveries on Wikidata made at a known place in the isles (roadmap C6b), read by bidb.oldest_lists.

Items with an inventor or discoverer (P61) and a place of discovery (P189) or of creation (P1071) in the isles. The
narrow query (no class tree) finishes in seconds on QLever; the first try, with the subclasses of invention, did not.
Only places with their own coordinates count: an item placed only at "United Kingdom" or "England" is left out, and
so are finds, fossils and museum objects (other groups have them) and the researched innovations already listed.
The place becomes `made_at_qid`, so bidb.oldest_lists.link_made_at links it to its building or place.

    python -m bidb.innovations_wd   → prints what would be added
"""
import re
from urllib.parse import unquote

from .change_firms import COUNTRIES, QLEVER
from .dates import parse_year
from .http import request_json
from .place_kinds import in_box

KIND = "inv_wd"
LABEL = "Invention or discovery (Wikidata)"
# place items that are a whole nation or region (their coordinates are a centroid, not the place it was made)
TOO_WIDE = {"Q145", "Q21", "Q22", "Q25", "Q26", "Q27", "Q174193", "Q161885", "Q179876", "Q230791", "Q215530",
            "Q31747", "Q9676", "Q25230", "Q785", "Q3336843"}
# reviewed 2026-10-27: items left out, with the reason
SKIP = {"Q6591619": "mechanical computer: the general class, not one of Babbage's engines (they are listed)",
        "Q2891742": "Salter's duck: Wikidata places it at Coventry University; it was devised at Edinburgh"}
NOT_INVENTION = re.compile(r"fossil|archaeolog|hoard|\bcoin\b|artefact|artifact|taxon|mineral species|"
                           r"inscription|sculpture|statue|manuscript", re.I)


def fetch():
    """Wikidata bindings, one per item and place."""
    q = f"""PREFIX wd: <http://www.wikidata.org/entity/> PREFIX wdt: <http://www.wikidata.org/prop/direct/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#> PREFIX schema: <http://schema.org/>
SELECT ?i ?place (SAMPLE(?lab) AS ?name) (SAMPLE(?pl) AS ?pname) (SAMPLE(?co) AS ?coord) (SAMPLE(?d1) AS ?found)
  (SAMPLE(?d2) AS ?inception) (GROUP_CONCAT(DISTINCT ?invl; separator="|") AS ?by)
  (GROUP_CONCAT(DISTINCT ?cl; separator="|") AS ?classes) (SAMPLE(?art) AS ?article) WHERE {{
  VALUES ?c {{ {" ".join("wd:" + c for c in COUNTRIES.split())} }}
  ?i wdt:P61 ?inv . {{ ?i wdt:P189 ?place }} UNION {{ ?i wdt:P1071 ?place }}
  ?place wdt:P17 ?c ; wdt:P625 ?co .
  ?i rdfs:label ?lab FILTER(LANG(?lab)="en")
  OPTIONAL {{ ?place rdfs:label ?pl FILTER(LANG(?pl)="en") }}
  OPTIONAL {{ ?inv rdfs:label ?invl FILTER(LANG(?invl)="en") }}
  OPTIONAL {{ ?i wdt:P31|wdt:P279 ?cls . ?cls rdfs:label ?cl FILTER(LANG(?cl)="en") }}
  OPTIONAL {{ ?i wdt:P575 ?d1 }} OPTIONAL {{ ?i wdt:P571 ?d2 }}
  OPTIONAL {{ ?art schema:about ?i ; schema:isPartOf <https://en.wikipedia.org/> }}
}} GROUP BY ?i ?place"""
    res = request_json(QLEVER, params={"query": q}, headers={"Accept": "application/sparql-results+json"},
                       min_interval=1.0)
    return res["results"]["bindings"]


def _qid(b, key):
    return (b.get(key) or {}).get("value", "").rsplit("/", 1)[-1] or None


def _point(wkt):
    m = re.match(r"Point\(([-\d.eE]+) ([-\d.eE]+)\)", wkt or "", re.I)
    return (float(m.group(2)), float(m.group(1))) if m else (None, None)


def items(bindings, skip=(), names=()):
    """One dict per item kept: the first place with coordinates in the isles that is not a whole nation."""
    out = {}
    for b in bindings:
        qid, place = _qid(b, "i"), _qid(b, "place")
        if qid in out or qid in skip or qid in SKIP or place in TOO_WIDE:
            continue
        val = {k: (b.get(k) or {}).get("value") for k in ("name", "pname", "coord", "found", "inception", "by",
                                                             "classes", "article")}
        lat, lon = _point(val["coord"])
        classes = [c for c in (val["classes"] or "").split("|") if c]
        if not in_box(lat, lon) or any(NOT_INVENTION.search(c) for c in classes) or re.match(r"Q\d+$|discovery of ", val["name"], re.I) \
                or val["name"].lower() in names:
            continue
        year = parse_year(val["found"] or val["inception"] or "")
        by = [p for p in (val["by"] or "").split("|") if p]
        title = (val["article"] or "").rsplit("/wiki/", 1)[-1].replace("_", " ") or None
        out[qid] = {"qid": qid, "name": val["name"][:1].upper() + val["name"][1:], "place": place,
                    "place_name": val["pname"], "lat": lat, "lon": lon, "year": year, "by": by,
                    "classes": classes, "wikipedia_title": title and unquote(title)}
    return list(out.values())


def researched_qids():
    """Wikidata ids and names of the researched innovations (they keep their own entry)."""
    from .oldest_lists import entries
    from .wikipedia_list import titles_to_qids
    es = entries("innovations")
    got = titles_to_qids(sorted({e["wikipedia_title"] for e in es if e.get("wikipedia_title")}))
    return set(got.values()) | {e["qid"] for e in es if e.get("qid")}, {e["name"].lower() for e in es}


def records():
    """Place records (kind `inv_wd`) for bidb.oldest_lists.run."""
    from .place_records import blank
    out = []
    for it in items(fetch(), *researched_qids()):
        who = ", ".join(it["by"][:3])
        desc = f"{it['name']}: {'discovered' if _discovery(it) else 'invented or first made'} by {who or 'unknown'}" \
               f"{' in ' + str(it['year']) if it['year'] is not None else ''} at {it['place_name'] or 'this place'} " \
               f"(Wikidata statements, not checked against a source)"
        out.append(blank(it["qid"], KIND, it["name"], kind_label=LABEL, kind_group="Innovations & firsts",
                         type=", ".join(it["classes"][:3]) or None, description=desc, year_start=it["year"],
                         date_text=str(it["year"]) if it["year"] is not None else None, lat=it["lat"], lon=it["lon"],
                         locality=it["place_name"], wikipedia_title=it["wikipedia_title"], wikidata_id=it["qid"],
                         source="Wikidata (CC0)", url=f"https://www.wikidata.org/wiki/{it['qid']}",
                         extra={"made_at_qid": it["place"], "made_at": it["place_name"], "inventors": it["by"]}))
    return out


def _discovery(it):
    return any(re.search(r"element|particle|lepton|nucleon|boson|number|antibiotic|penam", c) for c in it["classes"])


if __name__ == "__main__":
    for r in sorted(records(), key=lambda r: (r["year_start"] is None, r["year_start"] or 0)):
        print(r["date_text"] or "    ", r["name"], "|", r["locality"], "|", r["description"][:90])
