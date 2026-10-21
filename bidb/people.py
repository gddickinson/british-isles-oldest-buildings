"""People linked to buildings and places (Wikidata), for the People page and detail views.

Links in both directions:
  person -> place : buried (P119), lived (P551), died (P20), born (P19), worked (P937)
  place -> person : architect (P84), commissioned (P88), founded (P112), occupant (P466),
                    owner (P127), commemorated (P547, plaques), named after (P138),
                    participant (P710, battles)
"""
import json

from .http import sparql

PERSON_TO_PLACE = {"P119": "Buried here", "P551": "Lived here", "P20": "Died here",
                   "P19": "Born here", "P937": "Worked here"}
PLACE_TO_PERSON = {"P84": "Architect", "P88": "Commissioned it", "P112": "Founded it",
                   "P466": "Occupant", "P127": "Owner", "P547": "Commemorated here",
                   "P138": "Named after them", "P710": "Took part"}
NAMED_AFTER, NAMED_AFTER_FROM = "Named after them", 1000   # only for people born after AD 1000
MAX_PER_ROLE = 40          # e.g. Westminster Abbey has thousands of burials: keep the best known
PERSON_COLUMNS = [("id", "TEXT PRIMARY KEY"), ("name", "TEXT"), ("description", "TEXT"),
                  ("birth", "INTEGER"), ("death", "INTEGER"), ("sitelinks", "INTEGER"),
                  ("image_thumb", "TEXT"), ("wikipedia_title", "TEXT"), ("summary", "TEXT")]
LINK_COLUMNS = [("person_id", "TEXT"), ("target_id", "TEXT"), ("target_type", "TEXT"),
                ("role", "TEXT"), ("ref", "TEXT")]     # ref: JSON {"s": stated in, "u": url} or NULL


def _qid(uri):
    return uri.rsplit("/", 1)[-1]


def _chunks(seq, n):
    seq = list(seq)
    for i in range(0, len(seq), n):
        yield seq[i:i + n]


def find_links(target_ids, log=print):
    """[(person qid, target qid, role)] for Wikidata target ids."""
    links = set()
    p2t = " ".join("wdt:" + p for p in PERSON_TO_PLACE)
    t2p = " ".join("wdt:" + p for p in PLACE_TO_PERSON)
    targets = sorted(t for t in target_ids if t and t.startswith("Q"))
    for n, chunk in enumerate(_chunks(targets, 300)):
        values = " ".join("wd:" + q for q in chunk)
        for r in sparql(f"""SELECT ?p ?t ?prop WHERE {{ VALUES ?t {{ {values} }} VALUES ?prop {{ {p2t} }}
                ?p ?prop ?t . ?p wdt:P31 wd:Q5 . }}"""):
            links.add((_qid(r["p"]["value"]), _qid(r["t"]["value"]),
                       PERSON_TO_PLACE[_qid(r["prop"]["value"])]))
        for r in sparql(f"""SELECT ?p ?t ?prop WHERE {{ VALUES ?t {{ {values} }} VALUES ?prop {{ {t2p} }}
                ?t ?prop ?p . ?p wdt:P31 wd:Q5 . }}"""):
            links.add((_qid(r["p"]["value"]), _qid(r["t"]["value"]),
                       PLACE_TO_PERSON[_qid(r["prop"]["value"])]))
        if n % 20 == 0:
            log(f"  people links: {n * 300}/{len(targets)} targets, {len(links)} links")
    return sorted(links)


def link_references(links, log=print):
    """{(person, target, role): '{"s": stated in, "u": url}'} for links whose Wikidata statement
    carries a reference (stated in / reference URL)."""
    prop_of = {**{v: k for k, v in PERSON_TO_PLACE.items()}, **{v: k for k, v in PLACE_TO_PERSON.items()}}
    rows = []
    for p, t, role in links:
        prop = prop_of[role]
        subj, obj = (p, t) if prop in PERSON_TO_PLACE else (t, p)
        rows.append((subj, prop, obj, (p, t, role)))
    out = {}
    for n, chunk in enumerate(_chunks(rows, 200)):
        values = " ".join(f"(wd:{s} p:{pr} ps:{pr} wd:{o})" for s, pr, o, _ in chunk)
        key = {(s, pr, o): k for s, pr, o, k in chunk}
        for r in sparql(f"""SELECT ?s ?p ?o ?statedLabel ?url WHERE {{
                VALUES (?s ?p ?ps ?o) {{ {values} }}
                ?s ?p ?st . ?st ?ps ?o ; prov:wasDerivedFrom ?ref .
                OPTIONAL {{ ?ref pr:P248 ?stated }} OPTIONAL {{ ?ref pr:P854 ?url }}
                SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en". }} }}"""):
            val = lambda k: (r.get(k) or {}).get("value")
            if not (val("statedLabel") or val("url")):
                continue
            k = key.get((_qid(val("s")), _qid(val("p")), _qid(val("o"))))
            if k and k not in out:
                out[k] = json.dumps({"s": val("statedLabel"), "u": val("url")}, ensure_ascii=False)
        if n % 20 == 0:
            log(f"  link references: {n * 200}/{len(rows)} links, {len(out)} referenced")
    return out


def person_details(qids):
    """{qid: person dict} with label, description, life years, sitelinks, image, article."""
    out = {}
    for chunk in _chunks(sorted(qids), 200):
        values = " ".join("wd:" + q for q in chunk)
        rows = sparql(f"""SELECT ?p ?pLabel ?pDescription ?b ?d ?n ?img ?article WHERE {{
            VALUES ?p {{ {values} }}
            OPTIONAL {{ ?p wdt:P569 ?b }} OPTIONAL {{ ?p wdt:P570 ?d }}
            OPTIONAL {{ ?p wikibase:sitelinks ?n }} OPTIONAL {{ ?p wdt:P18 ?img }}
            OPTIONAL {{ ?article schema:about ?p; schema:isPartOf <https://en.wikipedia.org/> }}
            SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en". }} }}""")
        for r in rows:
            q = _qid(r["p"]["value"])
            if q in out:
                continue
            val = lambda k: (r.get(k) or {}).get("value")
            out[q] = {"id": q, "name": val("pLabel"), "description": val("pDescription"),
                      "birth": _year(val("b")), "death": _year(val("d")),
                      "sitelinks": int(val("n") or 0), "image": val("img"),
                      "wikipedia_title": (val("article") or "").rsplit("/", 1)[-1].replace("_", " ") or None}
    return out


def _year(t):
    if not t or t.startswith("http"):
        return None
    neg = t.startswith("-")
    try:
        y = int(t.lstrip("+-").split("-", 1)[0])
    except ValueError:
        return None
    return -y if neg else y


def trim_links(links, persons):
    """Keep the MAX_PER_ROLE best-known people per (target, role)."""
    groups = {}
    for p, t, role in links:
        if p in persons:
            groups.setdefault((t, role), []).append(p)
    kept = []
    for (t, role), ps in groups.items():
        ps.sort(key=lambda p: -persons[p]["sitelinks"])
        kept.extend((p, t, role) for p in ps[:MAX_PER_ROLE])
    return kept
