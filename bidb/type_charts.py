"""Building types BT5: the data of the charts of types and materials through time (the "Through time" tab of the
page /types and the type pages), from the curated types and materials and the records and places mapped to them.

    spread     one type's first dated example in each county (not too early, not dated from the type itself,
               not demolished): how it spread across the isles
    chains     "what came before and what came next": the lines of descent, replacement and revival through one
               type, followed back to the types it came from and forward to the last ones, each step with its
               link kind and confidence
    centuries  materials and techniques by the century their records were begun (too early ones left out), in
               the groups of bidb.building_materials
The types in use at each date are counted in the browser from the tree (/api/type_tree), which has every period.
"""
from collections import defaultdict

from . import building_materials, material_stats, type_stats

SUCCESSION = ("descent", "replacement", "revival")   # links that say what came next (variants are forms, not heirs)
MAX_CHAINS = 8                                       # lines shown before and after a type
MAX_STEPS = 8                                        # types in one line


def spread(conn, type_id, data=None):
    """[{county, nation, year, id, source, name, date_text}] oldest first, one per county; None for unknown types."""
    t = type_stats.types_by_id(data).get(type_id)
    if t is None:
        return None
    ok, first = type_stats.early_ok(), {}
    for r in type_stats._rows(conn, type_id):
        if not r["county"] or not type_stats._candidate(r, t, ok):
            continue
        key = (r["nation"] or "", r["county"])
        if key not in first or (r["year"], r["name"] or "") < (first[key]["year"], first[key]["name"] or ""):
            first[key] = r
    return sorted(({"county": r["county"], "nation": r["nation"], "year": r["year"], "id": r["id"],
                    "source": r["source"], "name": r["name"], "date_text": r["date_text"]} for r in first.values()),
                  key=lambda x: (x["year"], x["county"]))


def _paths(start, edges, limit=MAX_CHAINS):
    """Maximal paths from start along edges {id: [(next id, link)]}, no type twice, longest first."""
    out = []

    def walk(node, path, seen):
        nxt = [(m, k) for m, k in edges.get(node, []) if m not in seen]
        if not nxt or len(path) >= MAX_STEPS:
            if path:
                out.append(path)
            return
        for m, k in nxt:
            walk(m, path + [(m, k)], seen | {m})

    walk(start, [], {start})
    out.sort(key=lambda p: (-len(p), [m for m, _ in p]))
    return out[:limit]


def chains(type_id, data):
    """{before: [[step...]], after: [[step...]]}; a step is {id, name, from, kind, confidence, abroad}. Lines before
    run from the oldest ancestor to the type (the type itself left out); lines after from the type onwards."""
    types = {t["id"]: t for t in data["types"]}
    if type_id not in types:
        return None
    fwd, back = defaultdict(list), defaultdict(list)
    for link in data["links"]:
        if link["kind"] in SUCCESSION and link["from"] in types and link["to"] in types:
            fwd[link["from"]].append((link["to"], link))
            back[link["to"]].append((link["from"], link))

    def step(tid, link):
        t = types[tid]
        return {"id": tid, "name": t["name"], "from": (t.get("period") or {}).get("from"), "kind": link["kind"],
                "confidence": link["confidence"], "abroad": bool(t.get("abroad"))}

    after = [[step(m, k) for m, k in p] for p in _paths(type_id, fwd)]
    before = []
    for p in _paths(type_id, back):        # walked backwards: the link of each step joins it to the one after it
        before.append(list(reversed([step(m, k) for m, k in p])))
    out = {"before": before, "after": after, "form_of": None}
    if not before and not after:            # a form of another type (a Wealden house of the hall house): its lines
        parent = next((k["from"] for k in data["links"] if k["kind"] == "variant" and k["to"] == type_id
                       and k["from"] in types), None)      # variant links run from the general type to its form
        if parent:
            sub = chains(parent, dict(data, links=[k for k in data["links"] if type_id not in (k["from"], k["to"])]))
            if sub["before"] or sub["after"]:
                out["form_of"] = {"id": parent, "name": types[parent]["name"], "before": sub["before"],
                                  "after": sub["after"]}
    return out


def centuries(conn, mdata=None):
    """{groups: [[group, [material ids]]], names: {id: name}, first: {id: first year}, counts: {id: {century: n}}}."""
    mdata = mdata or building_materials.load()
    return {"groups": [[g, [m["id"] for m in ms]] for g, ms in building_materials.by_group(mdata).items()],
            "names": {m["id"]: m["name"] for m in mdata["materials"]},
            "first": {m["id"]: (m.get("period") or {}).get("from") for m in mdata["materials"]},
            "counts": material_stats.by_century(conn, mdata)}
