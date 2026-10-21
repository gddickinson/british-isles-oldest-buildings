"""Wikidata access: discover candidate buildings and fetch their full entity records."""
import re

from .config import (COUNTRIES, CUTOFF_YEAR, NATIONS, Q_ARCH_STRUCTURE, Q_BUILDING,
                     Q_IRISH_COUNTY, UNDATED_DESIGNATIONS, WIKIDATA_API)

_COUNTRY_VALUES = " ".join(f"wd:{q}" for q in COUNTRIES)
from .http import request_json, sparql


def _qid(uri):
    return uri.rsplit("/", 1)[-1]


def _chunks(seq, n):
    seq = list(seq)
    for i in range(0, len(seq), n):
        yield seq[i:i + n]


def find_candidates(cutoff_year=CUTOFF_YEAR):
    """British Isles items with an inception before the cutoff -> {qid: set(class qids)}."""
    rows = sparql(f"""
        SELECT ?item ?c WHERE {{
          VALUES ?country {{ {_COUNTRY_VALUES} }}
          ?item wdt:P17 ?country; wdt:P571 ?inc; wdt:P31 ?c .
          FILTER(?inc < "{cutoff_year:04d}-01-01T00:00:00Z"^^xsd:dateTime)
        }}""")
    out = {}
    for r in rows:
        out.setdefault(_qid(r["item"]["value"]), set()).add(_qid(r["c"]["value"]))
    return out


def find_designated():
    """Items carrying an UNDATED_DESIGNATIONS designation -> {qid: set(class qids)}."""
    values = " ".join(f"wd:{q}" for q in UNDATED_DESIGNATIONS)
    rows = sparql(f"""
        SELECT ?item ?c WHERE {{
          VALUES ?d {{ {values} }}
          ?item wdt:P1435 ?d; wdt:P31 ?c .
        }}""")
    out = {}
    for r in rows:
        out.setdefault(_qid(r["item"]["value"]), set()).add(_qid(r["c"]["value"]))
    return out


def irish_counties_for(qids):
    """{qid: county name} for items inside a county of Ireland (P131 chain)."""
    out = {}
    for chunk in _chunks(sorted(qids), 250):
        values = " ".join(f"wd:{q}" for q in chunk)
        rows = sparql(f"""
            SELECT DISTINCT ?item ?countyLabel WHERE {{
              VALUES ?item {{ {values} }}
              ?item wdt:P131+ ?county . ?county wdt:P31 wd:{Q_IRISH_COUNTY} .
              SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en". }}
            }}""")
        for r in rows:
            out[_qid(r["item"]["value"])] = r["countyLabel"]["value"]
    return out


def classes_under(class_qids, root_qid):
    """Subset of class_qids that are (transitive) subclasses of root_qid."""
    found = set()
    for chunk in _chunks(sorted(class_qids), 300):
        values = " ".join(f"wd:{q}" for q in chunk)
        rows = sparql(f"""
            SELECT DISTINCT ?c WHERE {{
              VALUES ?c {{ {values} }}
              ?c wdt:P279* wd:{root_qid} .
            }}""")
        found.update(_qid(r["c"]["value"]) for r in rows)
    return found


def structure_classes(class_qids):
    """Return (classes that are architectural structures, classes that are buildings)."""
    return classes_under(class_qids, Q_ARCH_STRUCTURE), classes_under(class_qids, Q_BUILDING)


def nations_for(qids):
    """{qid: nation name} using the located-in-admin-territory (P131) chain."""
    values_n = " ".join(f"wd:{q}" for q in NATIONS)
    out = {}
    for chunk in _chunks(sorted(qids), 250):
        values = " ".join(f"wd:{q}" for q in chunk)
        rows = sparql(f"""
            SELECT DISTINCT ?item ?n WHERE {{
              VALUES ?item {{ {values} }}
              VALUES ?n {{ {values_n} }}
              ?item wdt:P131+ ?n .
            }}""")
        for r in rows:
            out[_qid(r["item"]["value"])] = NATIONS[_qid(r["n"]["value"])]
    return out


def get_entities(qids, props="labels|descriptions|claims|sitelinks", label_only=False):
    """Fetch entities via wbgetentities in batches of 50 -> {qid: entity json}."""
    out = {}
    if label_only:
        props = "labels"
    for chunk in _chunks(sorted(set(qids)), 50):
        res = request_json(WIKIDATA_API, params={
            "action": "wbgetentities", "ids": "|".join(chunk), "props": props,
            "languages": "en", "sitefilter": "enwiki", "format": "json"}, min_interval=0.3)
        out.update(res.get("entities", {}))
    return out


def label(entity):
    return entity.get("labels", {}).get("en", {}).get("value", "")


# ---- claim helpers --------------------------------------------------------------

def claim_values(entity, prop):
    """Raw datavalue 'value' objects for a property, best rank first, deprecated dropped."""
    claims = [c for c in entity.get("claims", {}).get(prop, []) if c.get("rank") != "deprecated"]
    claims.sort(key=lambda c: c.get("rank") != "preferred")
    vals = []
    for c in claims:
        snak = c.get("mainsnak", {})
        if snak.get("snaktype") == "value":
            vals.append(snak["datavalue"]["value"])
    return vals


def item_ids(entity, prop):
    return [v["id"] for v in claim_values(entity, prop) if isinstance(v, dict) and "id" in v]


def strings(entity, prop):
    out = []
    for v in claim_values(entity, prop):
        if isinstance(v, str):
            out.append(v)
        elif isinstance(v, dict) and "text" in v:
            out.append(v["text"])
    return out


def first_string(entity, prop):
    vals = strings(entity, prop)
    return vals[0] if vals else None


def coords(entity):
    for v in claim_values(entity, "P625"):
        if isinstance(v, dict) and "latitude" in v:
            return v["latitude"], v["longitude"]
    return None, None


def times(entity, prop):
    """[(time string, precision)] for a time-valued property."""
    return [(v["time"], v.get("precision", 9)) for v in claim_values(entity, prop)
            if isinstance(v, dict) and "time" in v]


def quantity(entity, prop):
    for v in claim_values(entity, prop):
        if isinstance(v, dict) and "amount" in v:
            return float(v["amount"])
    return None


def enwiki_title(entity):
    return entity.get("sitelinks", {}).get("enwiki", {}).get("title")


LABEL_FALLBACK = ["en-gb", "ga", "cy", "gd", "gv", "kw", "fr", "de", "nl", "mul"]
# German labels (common for Irish megaliths) rewritten as "<place> <English type>"
GERMAN_TYPES = {"Court Tomb": "court tomb", "Clyde Tomb": "Clyde tomb", "Portal Tomb": "portal tomb",
                "Wedge Tomb": "wedge tomb", "Steinkreis": "stone circle", "Steinkreise": "stone circles",
                "Menhir": "standing stone", "Souterrain": "souterrain", "Felsritzungen": "rock art",
                "Steinmonumente": "stone monuments", "Steinreihe": "stone row", "Dolmen": "dolmen",
                "Ringfort": "ringfort", "Cairn": "cairn", "Kloster": "monastery", "Burg": "castle",
                "Kirche": "church", "Ruine": "ruin"}
GERMAN_WORDS = [(r"^Porträt des ", "Portrait of "), (r"\bPorträt des ", "portrait of "),
                (r"^Stolperstein für ", "Stolperstein for ")]


def english_form(label):
    """Rewrite a German fallback label ("Court Tomb von Doon") in English ("Doon court tomb")."""
    m = re.match(r"^(.+?) von (.+)$", label or "")
    if m and m.group(1) in GERMAN_TYPES:
        return f"{m.group(2)} {GERMAN_TYPES[m.group(1)]}"
    if m and m.group(1) == "Doon":
        return f"Doon of {m.group(2)}"
    for pat, rep in GERMAN_WORDS:
        label = re.sub(pat, rep, label)
    return label


def labels_any_language(qids):
    """{qid: label} for items without an English label, from the first other language present."""
    out = {}
    for chunk in _chunks(sorted(set(qids)), 50):
        res = request_json(WIKIDATA_API, params={
            "action": "wbgetentities", "ids": "|".join(chunk), "props": "labels",
            "format": "json"}, min_interval=0.3)
        for q, e in res.get("entities", {}).items():
            labels = e.get("labels", {})
            for lang in LABEL_FALLBACK + sorted(labels):
                if lang in labels:
                    value = labels[lang]["value"]
                    out[q] = english_form(value)
                    break
    return out
