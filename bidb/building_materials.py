"""Building types BT3a: materials and techniques of building in the isles, with periods, regions, the technology
that made each possible, geology, the building types that used it and sourced links between them.

Curated input `data/curated/building_types/materials_*.json` (one group or two per file, read together; links may
cross files):
    materials: [{id, name, group (GROUPS), kind ("material" | "technique"),
                 fish {scheme ("mat" building materials, "com" components, "mon" monument types), id} or null,
                 period {text, from, flourish? [from, to], to | ongoing, earlier?} (as the building types; earlier:
                 true when `from` is only the earliest example a source names and the use is surely older),
                 regions? {text, nations? [NATIONS]}, technology? (what made it possible, cheaper or ended it),
                 geology? [bedrock periods of bidb.change_geology], rock? [kinds of building rock of
                 change_geology.ROCKS: where the BGS map has its rock, within the geology periods unless igneous; []
                 when it was not quarried in the isles] (BT3c2), types? [building type ids],
                 examples? [{name, wikidata?, year?, note?}], note?, general? (true: a generic stone, as limestone,
                 that gives way in bidb.material_map to the named stones it has variant links to), sources}]
    A material's sources say what they support: about ["period", "region", "technology", "geology", "example"]
    (none: the material itself).
    links: [{id "from>to", from, to, kind, confidence, claim, sources, views? (disputed)}] as bidb.building_types.

Definitions come from the FISH Building Materials and Components thesauri (Historic England, OGL v3.0;
bidb.fish_types); dates, regions and links each cite their sources with an exact quote.

    python -m bidb.building_materials              check the files, print the groups and links
    python -m bidb.building_materials --file materials_x.json   one file only
    python -m bidb.building_materials --quotes     also fetch every source and look for its quote
                                                   (→ data/building_materials_check.json)
"""
import json
import sys
from collections import Counter
from pathlib import Path

from . import building_types as bt
from .config import DATA_DIR

FOLDER = DATA_DIR / "curated" / "building_types"
CHECK = DATA_DIR / "building_materials_check.json"
GROUPS = ("Stone", "Earth", "Timber", "Brick and tile", "Roofs", "Mortar and render", "Glass", "Iron and steel",
          "Concrete")
KINDS = ("material", "technique")
ABOUT = ("period", "region", "technology", "geology", "example")
NATIONS = ("England", "Scotland", "Wales", "Northern Ireland", "Republic of Ireland", "Isle of Man", "Jersey",
           "Guernsey")
SCHEMES = ("mat", "com", "mon")
GEOLOGY = ("Precambrian", "Cambrian", "Ordovician", "Silurian", "Devonian", "Carboniferous", "Permian", "Triassic",
           "Jurassic", "Cretaceous", "Palaeogene", "Neogene", "Intrusions and undivided")   # change_geology.NAMES
ROCKS = ("limestone", "chalk", "sandstone", "mudstone", "felsic", "mafic")       # change_geology.ROCKS (BT3c2)


def files():
    return sorted(FOLDER.glob("materials_*.json"))


def load(path=None):
    """One file, or every file merged into one {materials, links}."""
    data = {"materials": [], "links": []}
    for p in [path] if path else files():
        d = json.loads(Path(p).read_text())
        data["materials"] += d.get("materials", [])
        data["links"] += d.get("links", [])
    return data


def validate(data, type_ids=None, partial=False):
    """Problems: missing or unknown fields, duplicate ids, claims without a source about them, unknown building
    types, link problems as bidb.building_types (partial: one file, so link ends may be in another)."""
    type_ids = set(type_ids if type_ids is not None else (t["id"] for t in bt.load()["types"]))
    bad, ids = [], Counter(m.get("id") for m in data["materials"])
    bad += [f"material {i}: duplicate id" for i, n in ids.items() if n > 1]
    for m in data["materials"]:
        where = f"material {m.get('id')}"
        bad += [f"{where}: no {k}" for k in ("id", "name", "group", "kind", "sources") if not m.get(k)]
        if m.get("group") not in GROUPS:
            bad.append(f"{where}: group {m.get('group')!r}")
        if m.get("kind") not in KINDS:
            bad.append(f"{where}: kind {m.get('kind')!r}")
        fish = m.get("fish")
        if fish is not None and (fish.get("scheme") not in SCHEMES or not str(fish.get("id", "")).isdigit()):
            bad.append(f"{where}: fish {fish!r}")
        bad += bt._source_problems(where, m.get("sources", []), ABOUT)
        bad += bt.period_errors(where, m.get("period"))
        if "general" in m and m["general"] is not True:
            bad.append(f"{where}: general is not true")
        if "earlier" in (m.get("period") or {}) and m["period"]["earlier"] is not True:
            bad.append(f"{where}: period earlier is not true")
        about = {a for s in m.get("sources", []) for a in s.get("about", [])}
        needs = {"period": True, "region": m.get("regions"), "technology": m.get("technology"),
                 "geology": m.get("geology"), "example": m.get("examples")}
        bad += [f"{where}: no source about its {k}" for k, v in needs.items() if v and k not in about]
        regions = m.get("regions")
        if regions is not None and (not regions.get("text") or any(n not in NATIONS for n in regions.get("nations", []))):
            bad.append(f"{where}: regions {regions!r}")
        bad += [f"{where}: geology {g!r}" for g in m.get("geology", []) if g not in GEOLOGY]
        rock = m.get("rock")
        if rock is not None and (not isinstance(rock, list) or any(r not in ROCKS for r in rock)):
            bad.append(f"{where}: rock {rock!r}")
        bad += [f"{where}: unknown building type {t!r}" for t in m.get("types", []) if t not in type_ids]
        for e in m.get("examples", []):
            if not e.get("name") or (e.get("wikidata") and not str(e["wikidata"]).startswith("Q")):
                bad.append(f"{where}: example {e!r}")
    bad += [b.replace("type ", "material ", 1) for b in _link_problems(data, set(ids), partial)]
    return bad


def _link_problems(data, ids, partial):
    """The link rules of bidb.building_types (ends known, kinds, confidence, views, no descent loops)."""
    probe = {"types": [{"id": i, "name": i, "family": "-", "domain": "-", "fish": "1"} for i in ids],
             "links": data["links"]}
    out = [b for b in bt.validate(probe) if "not in any link" not in b]   # a material need not be linked
    return [b for b in out if not (partial and "unknown type" in b)]


def fish_problems(data):
    """FISH ids that are not concepts of their thesaurus (needs the cached thesauri)."""
    from . import fish_types
    return [f"material {m['id']}: FISH {m['fish']['scheme']} {m['fish']['id']} not in the thesaurus"
            for m in data["materials"] if m.get("fish")
            and str(m["fish"]["id"]) not in fish_types.concepts(m["fish"]["scheme"])]


def claims(data=None):
    """Evidence-style claims of every material and link, for bidb.evidence.check."""
    data = data or load()
    return ([{"id": f"material:{m['id']}", "sources": m["sources"]} for m in data["materials"]]
            + [{"id": f"mlink:{x['id']}", "sources": x["sources"]} for x in data["links"]])


def by_group(data):
    """{group: [materials]} in GROUPS order, then file order."""
    out = {g: [] for g in GROUPS}
    for m in data["materials"]:
        out.setdefault(m["group"], []).append(m)
    return {g: ms for g, ms in out.items() if ms}


def for_type(type_id, data=None):
    """Materials and techniques that list a building type."""
    return [m for m in (data or load())["materials"] if type_id in m.get("types", [])]


def summary(data):
    names = {m["id"]: m["name"] for m in data["materials"]}
    n_quotes = sum(len(x["sources"]) for x in data["materials"] + data["links"])
    lines = [f"{len(data['materials'])} materials and techniques, {len(data['links'])} links, {n_quotes} quotes"]
    for group, ms in by_group(data).items():
        lines.append(group)
        for m in ms:
            p = m["period"]
            end = "now" if p.get("ongoing") else p["to"]
            lines.append(f"  {m['name']} ({m['kind']}, {p['from']}-{end})")
    if data["links"]:
        lines.append("Links")
    for x in data["links"]:
        lines.append(f"  {names.get(x['from'], x['from'])} → {names.get(x['to'], x['to'])}: "
                     f"{x['kind']}, {x['confidence']}")
    return lines


def main():
    from .evidence import check
    one = bt._arg("--file")
    data = load(FOLDER / one) if one else load()
    bad = validate(data, partial=bool(one)) + fish_problems(data)
    print("\n".join(bad or summary(data)))
    if not bad and "--quotes" in sys.argv:
        out = bt._arg("--quotes")
        check(claims=claims(data), path=CHECK if not out or out.startswith("--") else Path(out))
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
