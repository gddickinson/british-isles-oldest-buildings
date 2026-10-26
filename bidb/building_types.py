"""Building types BT1b, BT1c: a family tree of building types, with sourced links between types.

Curated input `data/curated/building_types/lineage*.json` (lineage.json: houses and defence; lineage_religious.json,
lineage_agricultural.json, lineage_commercial.json, lineage_industrial.json, lineage_transport.json: one or two
domains each; read together, links may cross files):
    types: [{id, name, family, domain, fish (FISH concept id or null), abroad?, period? {text, from?, to?},
             note?, sources?}]
    links: [{id "from>to", from, to, kind, confidence, claim, sources, views? (disputed), region?}]
    Sources as in the evidence file: {title, author, kind, url, locator, quote}.

The types' place in the thesaurus comes from bidb.fish_types (FISH Thesaurus of Monument Types, OGL v3.0);
the links ("grew out of", "a form of", "shaped by"...) are not in the thesaurus and each cites its sources.

    python -m bidb.building_types              check the file and the FISH ids, print the families and links
    python -m bidb.building_types --quotes     also fetch every source and look for its quote
                                               (→ data/building_types_check.json)
"""
import json
import sys
from collections import Counter, defaultdict

from .config import DATA_DIR

PATH = DATA_DIR / "curated" / "building_types" / "lineage.json"
CHECK = DATA_DIR / "building_types_check.json"
KINDS = ("descent", "variant", "influence", "replacement", "revival", "convergence")
CONFIDENCE = ("documented", "probable", "disputed")
SOURCE_KINDS = ("primary", "listing", "secondary", "reference")


def files():
    """The curated files, lineage.json first."""
    return sorted(PATH.parent.glob("lineage*.json"))


def load(path=None):
    """One file, or every curated file merged into one {types, links}."""
    if path:
        return json.loads(path.read_text())
    data = {"types": [], "links": []}
    for p in files():
        d = json.loads(p.read_text())
        data["types"] += d["types"]
        data["links"] += d["links"]
    return data


def _source_problems(where, sources):
    bad = []
    for s in sources:
        if s.get("kind") not in SOURCE_KINDS:
            bad.append(f"{where}: source kind {s.get('kind')!r}")
        if not s.get("title") or not s.get("quote") or not (s.get("url") or s.get("locator")):
            bad.append(f"{where}: source without title, quote, or url/locator")
    return bad


def validate(data):
    """Problems in the file: missing fields, duplicate or unknown ids, unknown kinds, links without sources,
    disputed links without both views, a type with no link, a link that loops."""
    bad, ids = [], Counter(t.get("id") for t in data["types"])
    bad += [f"type {i}: duplicate id" for i, n in ids.items() if n > 1]
    for t in data["types"]:
        bad += [f"type {t.get('id')}: no {k}" for k in ("id", "name", "family", "domain") if not t.get(k)]
        if not t.get("abroad") and not t.get("fish") and not t.get("sources"):
            bad.append(f"type {t['id']}: neither a FISH concept nor sources")
        bad += _source_problems(f"type {t.get('id')}", t.get("sources", []))
    seen, linked = set(), set()
    for link in data["links"]:
        lid = link.get("id")
        if lid in seen:
            bad.append(f"link {lid}: duplicate id")
        seen.add(lid)
        if lid != f"{link.get('from')}>{link.get('to')}":
            bad.append(f"link {lid}: id is not from>to")
        for end in ("from", "to"):
            if link.get(end) not in ids:
                bad.append(f"link {lid}: unknown type {link.get(end)!r}")
            linked.add(link.get(end))
        if link.get("from") == link.get("to"):
            bad.append(f"link {lid}: links a type to itself")
        if link.get("kind") not in KINDS:
            bad.append(f"link {lid}: kind {link.get('kind')!r}")
        if link.get("confidence") not in CONFIDENCE:
            bad.append(f"link {lid}: confidence {link.get('confidence')!r}")
        if not link.get("claim") or not link.get("sources"):
            bad.append(f"link {lid}: no claim or sources")
        if link.get("confidence") == "disputed" and len(link.get("views", [])) < 2:
            bad.append(f"link {lid}: disputed without two views")
        bad += _source_problems(f"link {lid}", link.get("sources", []))
    bad += [f"type {i}: not in any link" for i in ids if i not in linked]
    bad += [f"descent loop through {c}" for c in _loops(data)]
    return bad


def _loops(data):
    """Types on a cycle of descent/variant links (a type cannot be its own ancestor)."""
    nxt = defaultdict(list)
    for link in data["links"]:
        if link.get("kind") in ("descent", "variant"):
            nxt[link["from"]].append(link["to"])
    loops, state = [], {}

    def visit(n):
        state[n] = 1
        for m in nxt[n]:
            if state.get(m) == 1:
                loops.append(m)
            elif m not in state:
                visit(m)
        state[n] = 2

    for n in list(nxt):
        if n not in state:
            visit(n)
    return loops


def fish_problems(data):
    """FISH ids that are not concepts of the thesaurus (needs the cached thesaurus)."""
    from . import fish_types
    concepts = fish_types.concepts()
    return [f"type {t['id']}: FISH {t['fish']} not in the thesaurus" for t in data["types"]
            if t.get("fish") and t["fish"] not in concepts]


def claims(data=None):
    """Evidence-style claims (id, sources) of every type and link, for bidb.evidence.check."""
    data = data or load()
    out = [{"id": f"type:{t['id']}", "sources": t["sources"]} for t in data["types"] if t.get("sources")]
    return out + [{"id": f"link:{link['id']}", "sources": link["sources"]} for link in data["links"]]


def family_tree(data):
    """{domain: {family: [type ids]}} in file order."""
    out = {}
    for t in data["types"]:
        out.setdefault(t["domain"], {}).setdefault(t["family"], []).append(t["id"])
    return out


def summary(data):
    names = {t["id"]: t["name"] for t in data["types"]}
    lines = [f"{len(data['types'])} types, {len(data['links'])} links "
             f"({', '.join(f'{k} {n}' for k, n in Counter(x['kind'] for x in data['links']).most_common())}; "
             f"{', '.join(f'{k} {n}' for k, n in Counter(x['confidence'] for x in data['links']).most_common())})"]
    for domain, families in family_tree(data).items():
        lines.append(domain)
        for family, ids in families.items():
            lines.append(f"  {family}: {', '.join(names[i] for i in ids)}")
    lines.append("Links")
    for link in data["links"]:
        where = f" [{link['region']}]" if link.get("region") else ""
        lines.append(f"  {names[link['from']]} → {names[link['to']]}: {link['kind']}, {link['confidence']}{where}")
    return lines


def main():
    from .evidence import check
    data = load()
    bad = validate(data) + fish_problems(data)
    print("\n".join(bad or summary(data)))
    if not bad and "--quotes" in sys.argv:
        check(claims=claims(data), path=CHECK)
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
