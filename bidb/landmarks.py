"""Important buildings of any date ("landmarks"): top heritage grades, World Heritage Sites and
structures that are widely known (articles in many Wikipedia languages).

These join the catalogue whatever their age; each carries the reason it was included.
"""
import re

from .config import COUNTRIES
from .http import sparql

_COUNTRY_VALUES = " ".join(f"wd:{q}" for q in COUNTRIES)
# designation QID -> reason (QIDs checked against Wikidata labels, October 2026)
TOP_GRADES = {"Q15700818": "Grade I listed", "Q10729054": "Category A listed",
              "Q71055272": "Grade A listed (Northern Ireland)", "Q9259": "World Heritage Site"}
FAMOUS_SITELINKS = 20      # articles in at least this many Wikipedia language editions


def _qid(uri):
    return uri.rsplit("/", 1)[-1]


def find_landmarks(log=print):
    """{qid: (set of class qids, reason)}"""
    out = {}
    for des, reason in TOP_GRADES.items():
        rows = sparql(f"""SELECT ?i ?c WHERE {{ VALUES ?country {{ {_COUNTRY_VALUES} }}
            ?i wdt:P1435 wd:{des}; wdt:P17 ?country; wdt:P31 ?c . }}""")
        for r in rows:
            q = _qid(r["i"]["value"])
            cls, _ = out.setdefault(q, (set(), reason))
            cls.add(_qid(r["c"]["value"]))
        log(f"  landmarks: {reason}: {len({_qid(r['i']['value']) for r in rows})}")
    rows = sparql(f"""SELECT ?i ?c ?s WHERE {{ VALUES ?country {{ {_COUNTRY_VALUES} }}
        ?i wdt:P17 ?country; wikibase:sitelinks ?s; wdt:P625 [] . FILTER(?s >= {FAMOUS_SITELINKS})
        ?i wdt:P31 ?c . }}""")
    for r in rows:
        q = _qid(r["i"]["value"])
        reason = f"Widely known (Wikipedia in {r['s']['value']} languages)"
        cls, old = out.get(q, (set(), reason))
        cls.add(_qid(r["c"]["value"]))
        out[q] = (cls, old if q in out else reason)
    # Crown Dependencies: their registers are not openly published, so take every designated or
    # documented structure Wikidata has for the Isle of Man, Jersey and Guernsey
    for country, name in CROWN_DEPENDENCIES.items():
        rows = sparql(f"""SELECT DISTINCT ?i ?c WHERE {{ ?i wdt:P17 wd:{country}; wdt:P625 []; wdt:P31 ?c .
            {{ ?i wdt:P1435 [] }} UNION {{ ?i wdt:P18 [] }}
            UNION {{ ?a schema:about ?i; schema:isPartOf <https://en.wikipedia.org/> }} }}""")
        for r in rows:
            q = _qid(r["i"]["value"])
            cls, _ = out.setdefault(q, (set(), f"Heritage of {name}"))
            cls.add(_qid(r["c"]["value"]))
    log(f"  landmarks: {len(out)} candidates in all")
    return out


# "Widely known" items of these kinds are places, not buildings (towns, streets, lochs...)
NOT_BUILDING = re.compile(r"\b(town|village|human settlement|city|big city|civil parish|community|"
                          r"unparished area|burgh|large burgh|seaside resort|port|seaport|fishing port|"
                          r"street|shopping street|road|road junction|square|garden square|area of london|"
                          r"district|lake|reservoir|water reservoir|island|micronation|waterfront|market town|"
                          r"restaurant district|ethnic enclave|motorway|international e-road network|"
                          r"kontor|human settlement in the isle of man|district of the isle of man|"
                          r"resort town|spa town|harbour|cathedral city|county town|suburb|"
                          r"neighbourhood|holiday village|new town|beach)\b")


def not_a_building(record):
    """True for a record included only as 'widely known' whose every type is a settlement, street
    or water body (a mixed item such as an estate that is also a skyscraper is kept)."""
    if not (record.get("landmark") or "").startswith("Widely known"):
        return False
    classes = [c.strip().lower() for c in (record.get("classes") or "").split(";") if c.strip()]
    return bool(classes) and all(NOT_BUILDING.fullmatch(c) for c in classes)


CROWN_DEPENDENCIES = {"Q9676": "the Isle of Man", "Q785": "Jersey", "Q25230": "Guernsey"}
