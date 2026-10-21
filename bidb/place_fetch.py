"""Fetch places of interest from Wikidata with small SPARQL queries.

1. One "base" query per kind (or per class for large kinds): item, class, coordinates, country.
2. Detail queries in chunks of item ids: label, description, image, article, admin area,
   designations; then dates and kind-specific extras (war, museum, inscription, ...).
"""
import re
from urllib.parse import unquote

from .config import COUNTRIES
from .dates import format_year, parse_year, sort_year
from .http import sparql
from .place_kinds import ARCH_ROOTS, BOX, FIND_EXCLUDE_ROOTS, in_box

_COUNTRY_VALUES = " ".join(f"wd:{q}" for q in COUNTRIES)
LABEL_SERVICE = 'SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }'
EXTRA_PROPS = [("P361", "part_of"), ("P195", "now_in"), ("P189", "found_at"),
               ("P547", "commemorates"), ("P1684", "inscription"), ("P276", "location")]


def _qid(uri):
    return uri.rsplit("/", 1)[-1]


def _chunks(seq, n):
    seq = list(seq)
    for i in range(0, len(seq), n):
        yield seq[i:i + n]


def _point(wkt):
    m = re.match(r"Point\(([-\d.eE]+) ([-\d.eE]+)\)", wkt or "")
    return (float(m.group(2)), float(m.group(1))) if m else (None, None)


def _geo(kind):
    geo = kind["geo"]
    if geo == "located":
        return ("{ ?i wdt:P17 ?country } UNION { ?i wdt:P276 ?loc . ?loc wdt:P17 ?country }"
                " OPTIONAL { ?i wdt:P276 ?loc2 . ?loc2 wdt:P625 ?lcoord }")
    if geo == "discovered":
        return "?i wdt:P189 ?loc . ?loc wdt:P17 ?country . OPTIONAL { ?loc wdt:P625 ?lcoord }"
    if geo == "box":
        s, w, n, e = BOX
        return ("SERVICE wikibase:box { ?i wdt:P625 ?coord . "
                f'bd:serviceParam wikibase:cornerSouthWest "Point({w} {s})"^^geo:wktLiteral . '
                f'bd:serviceParam wikibase:cornerNorthEast "Point({e} {n})"^^geo:wktLiteral . }}')
    return "?i wdt:P17 ?country ."


def _selector(kind, root=None):
    if kind.get("designations"):
        return f"VALUES ?d {{ {' '.join('wd:' + d for d in kind['designations'])} }} ?i wdt:P1435 ?d ."
    if kind.get("classes") is None:          # finds: anything discovered here except non-artefacts
        ex = " ".join("wd:" + q for q in FIND_EXCLUDE_ROOTS)
        return f"?i wdt:P31 ?c0 . FILTER NOT EXISTS {{ VALUES ?ex {{ {ex} }} ?c0 wdt:P279* ?ex }}"
    path = "wdt:P31/wdt:P279*" if kind.get("subclasses") else "wdt:P31"
    roots = [root] if root else kind["classes"]
    return f"VALUES ?root {{ {' '.join('wd:' + r for r in roots)} }} ?i {path} ?root ."


def base_items(kind, log=print):
    """{qid: {"lat", "lon", "country", "type"}} for one kind."""
    roots = kind["classes"] if kind.get("per_class") else [None]
    out = {}
    for root in roots:
        geo = _geo(kind)
        country = "" if kind["geo"] == "box" else f"VALUES ?country {{ {_COUNTRY_VALUES} }}"
        coord = "" if kind["geo"] == "box" else "OPTIONAL { ?i wdt:P625 ?coord }"
        rows = sparql(f"""SELECT DISTINCT ?i ?coord ?lcoord ?country WHERE {{
            {country} {_selector(kind, root)} {geo} {coord} }}""")
        for r in rows:
            q = _qid(r["i"]["value"])
            lat, lon = _point((r.get("coord") or r.get("lcoord") or {}).get("value"))
            rec = out.setdefault(q, {"lat": None, "lon": None, "country": None,
                                     "type": ARCH_ROOTS.get(root) if root else None})
            if rec["lat"] is None and lat is not None:
                rec["lat"], rec["lon"] = lat, lon
            if r.get("country") and not rec["country"]:
                rec["country"] = _qid(r["country"]["value"])
        log(f"  {kind['key']}{' ' + root if root else ''}: {len(rows)} rows")
    return {q: r for q, r in out.items() if in_box(r["lat"], r["lon"])}


def details(qids):
    """{qid: {...}} label, description, image, article title, admin areas, designations, classes."""
    out = {}
    for chunk in _chunks(sorted(qids), 200):
        values = " ".join("wd:" + q for q in chunk)
        rows = sparql(f"""SELECT ?i ?iLabel ?iDescription ?img ?article ?adminLabel ?desLabel ?clsLabel WHERE {{
            VALUES ?i {{ {values} }}
            OPTIONAL {{ ?i wdt:P18 ?img }}
            OPTIONAL {{ ?article schema:about ?i; schema:isPartOf <https://en.wikipedia.org/> }}
            OPTIONAL {{ ?i wdt:P131 ?admin }}
            OPTIONAL {{ ?i wdt:P1435 ?des }}
            OPTIONAL {{ ?i wdt:P31 ?cls }}
            {LABEL_SERVICE} }}""")
        for r in rows:
            q = _qid(r["i"]["value"])
            d = out.setdefault(q, {"name": None, "description": None, "image": None, "title": None,
                                   "admin": [], "designations": [], "classes": []})
            val = lambda k: (r.get(k) or {}).get("value")
            d["name"] = d["name"] or val("iLabel")
            d["description"] = d["description"] or val("iDescription")
            if val("img") and not d["image"]:
                d["image"] = unquote(val("img").rsplit("/", 1)[-1])
            if val("article") and not d["title"]:
                d["title"] = unquote(val("article").rsplit("/", 1)[-1]).replace("_", " ")
            for k, key in (("adminLabel", "admin"), ("desLabel", "designations"), ("clsLabel", "classes")):
                v = val(k)
                if v and v not in d[key] and not re.fullmatch(r"Q\d+", v):
                    d[key].append(v)
    return out


def dates(qids, props):
    """{qid: (sort year, text)} from the first listed time property that has a value."""
    out = {}
    unions = " UNION ".join(f'{{ ?i p:{p}/psv:{p} [ wikibase:timeValue ?t; wikibase:timePrecision ?prec ] . '
                         f'BIND("{p}" AS ?prop) }}' for p in props)
    for chunk in _chunks(sorted(qids), 150):
        values = " ".join("wd:" + q for q in chunk)
        rows = sparql(f"""SELECT ?i ?prop ?t ?prec WHERE {{ VALUES ?i {{ {values} }}
            {unions} }}""")
        best = {}
        for r in rows:
            q, p = _qid(r["i"]["value"]), r["prop"]["value"]
            y, prec = parse_year(r["t"]["value"]), int(r["prec"]["value"])
            if y is None:
                continue
            key = (props.index(p), sort_year(y, prec))
            if q not in best or key < best[q][0]:
                best[q] = (key, sort_year(y, prec), format_year(y, prec))
        out.update({q: (v[1], v[2]) for q, v in best.items()})
    return out


def extras(qids):
    """{qid: {"part_of": [...], "now_in": [...], ...}} for the EXTRA_PROPS that are present."""
    out = {}
    unions = " UNION ".join(f'{{ ?i wdt:{p} ?v . BIND("{name}" AS ?k) }}' for p, name in EXTRA_PROPS)
    for chunk in _chunks(sorted(qids), 300):
        values = " ".join("wd:" + q for q in chunk)
        rows = sparql(f"""SELECT ?i ?k ?v ?vLabel WHERE {{ VALUES ?i {{ {values} }} {unions}
            {LABEL_SERVICE} }}""")
        for r in rows:
            v = (r.get("vLabel") or r["v"])["value"]
            if re.fullmatch(r"Q\d+", v) or v.startswith("http"):
                continue
            lst = out.setdefault(_qid(r["i"]["value"]), {}).setdefault(r["k"]["value"], [])
            if v not in lst:
                lst.append(v)
    return out
