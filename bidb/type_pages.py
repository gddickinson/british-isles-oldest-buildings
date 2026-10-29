"""Building types BT4a, BT3c1: the data of the page /types, from the curated types and materials (bidb.building_types,
bidb.building_materials), their FISH definitions (bidb.fish_types, OGL v3.0) and the catalogue records and places
mapped to them (bidb.type_stats, bidb.material_stats).

    tree      every type (isles types with their counts and earliest surviving example; types abroad that the
              links reach, flagged), domains and families in file order, and the links between types
    type      one type: definition, period, structure, plan, links in and out with their sources, the materials
              the curated file gives it and those found in its records, examples, by nation and century, map;
              what came before and after and its first example per county (bidb.type_charts, BT5); plans of
              real examples (catalogue records and places with a Commons plan, BT6b, BT6c2a); labelled diagrams (bidb.type_diagrams, BT6c)
    materials every material and technique by group, with counts
    material  one material: definition, period, regions, technology, geology, links, building types (curated and
              among its records), examples with the evidence sentence, by nation and century, map
    here      the types and materials of one record or place (detail views)
"""
from . import building_materials, building_types, material_stats, type_charts, type_diagrams, type_stats

FISH_URL = "https://www.heritagedata.org/live/schemes/{}/concepts/{}.html"
TOP = 12                    # materials of a type's records, types of a material's records
PLANS = 12                  # plans of real examples on a type page (BT6b)


def _definition(scheme, fish_id):
    """The FISH scope note of a concept, without the indexing advice, and its URL; None without the thesaurus."""
    from . import fish_types
    from .glossary import scope_note
    try:
        c = fish_types.concepts(scheme).get(str(fish_id))
    except (OSError, KeyError, ValueError):
        return None
    if not c:
        return None
    return {"term": c["term"], "text": scope_note(c), "url": FISH_URL.format(fish_types.SCHEMES[scheme][1], fish_id)}


def _links(links, item_id, names):
    """The links of one type or material, each with the other end's id and name and the direction."""
    out = []
    for link in links:
        if item_id not in (link["from"], link["to"]):
            continue
        other = link["to"] if link["from"] == item_id else link["from"]
        out.append(dict(link, other=other, other_name=names.get(other, other),
                        direction="out" if link["from"] == item_id else "in"))
    return out


def tree(conn, data=None):
    data = data or building_types.load()
    stats = {s["id"]: s for s in type_stats.summary(conn, data)}
    types = []
    for t in data["types"]:
        s = stats.get(t["id"], {})
        types.append({"id": t["id"], "name": t["name"], "domain": t["domain"], "family": t["family"],
                      "abroad": bool(t.get("abroad")), "period": type_stats._period(t),
                      "buildings": s.get("buildings", 0), "places": s.get("places", 0),
                      "earliest": s.get("earliest")})
    links = [{k: link.get(k) for k in ("id", "from", "to", "kind", "confidence", "claim", "region")}
             for link in data["links"]]
    # lists, not objects: JSON keys may come back sorted
    order = [[dom, list(fams.items())] for dom, fams in building_types.family_tree(data).items()]
    return {"tree": order, "types": types, "links": links}


def _materials_of_type(conn, type_id, mats):
    rows = conn.execute("""SELECT mm.material_id, COUNT(DISTINCT mm.entity_id) FROM type_map tm
                           JOIN material_map mm ON mm.entity_id = tm.entity_id
                           WHERE tm.type_id = ? GROUP BY mm.material_id ORDER BY 2 DESC""", (type_id,)).fetchall()
    return [{"id": mid, "name": mats[mid]["name"], "group": mats[mid]["group"], "count": n}
            for mid, n in rows if mid in mats][:TOP]


def plans(conn, type_id, t=None, limit=PLANS):
    """BT6b, BT6c2a: catalogue records of the type with a floor plan on Commons, then places with one
    (bidb.place_plans): those of this main type first, those begun too early for the type (bidb.type_stats) last,
    then oldest first: [{id, source, name, year, date_text, county, nation, plan}]. Real buildings, often drawn with
    their later phases."""
    rows = conn.execute("""SELECT b.id, 'building', b.name, b.year_start, b.date_text, b.county, b.nation,
                                  b.plan_image, tm.is_primary
                           FROM type_map tm JOIN buildings b ON b.id = tm.entity_id
                           WHERE tm.type_id = ? AND tm.source = 'building' AND b.plan_image IS NOT NULL
                             AND b.plan_image != ''""", (type_id,)).fetchall()
    if conn.execute("SELECT 1 FROM sqlite_master WHERE name = 'place_plans'").fetchone():
        rows += conn.execute("""SELECT p.id, 'place', p.name, p.year_start, p.date_text, p.county, p.nation,
                                       pp.file, tm.is_primary
                                FROM type_map tm JOIN places p ON p.id = tm.entity_id
                                JOIN place_plans pp ON pp.place_id = p.id
                                WHERE tm.type_id = ? AND tm.source = 'place'""", (type_id,)).fetchall()
    ok = type_stats.early_ok() if t else {}
    keys = ("id", "source", "name", "year", "date_text", "county", "nation", "plan")
    out = [dict(zip(keys + ("primary",), r)) for r in rows]
    for p in out:
        p["too_early"] = bool(t) and type_stats.too_early(p, t, ok)
    out.sort(key=lambda p: (not p["primary"], p["too_early"], p["source"] != "building", p["year"] is None,
                            p["year"] or 0, p["name"] or ""))
    return [{k: p[k] for k in keys} for p in out[:limit]]


def type_page(conn, type_id, data=None, mdata=None):
    """One type, or None. Types abroad (only reached by links) have no examples."""
    data, mdata = data or building_types.load(), mdata or building_materials.load()
    t = next((x for x in data["types"] if x["id"] == type_id), None)
    if t is None:
        return None
    d = type_stats.detail(conn, type_id, data) or {"type": t, "period": type_stats._period(t), "abroad": True}
    names = {x["id"]: x["name"] for x in data["types"]}
    mats = material_stats.materials_by_id(mdata)
    d["definition"] = _definition("mon", t["fish"]) if t.get("fish") else None
    d["links"] = _links(data["links"], type_id, names)
    d["materials"] = [{"id": m["id"], "name": m["name"], "group": m["group"], "kind": m["kind"]}
                      for m in building_materials.for_type(type_id, mdata)]
    d["record_materials"] = _materials_of_type(conn, type_id, mats) if not d.get("abroad") else []
    d["chains"] = type_charts.chains(type_id, data)                                  # BT5
    d["spread"] = [] if d.get("abroad") else type_charts.spread(conn, type_id, data)
    d["plans"] = [] if d.get("abroad") else plans(conn, type_id, t)                    # BT6b
    d["diagrams"] = type_diagrams.for_type(type_id, data)                                # BT6c
    return d


def materials(conn, mdata=None):
    mdata = mdata or building_materials.load()
    stats = material_stats.summary(conn, mdata)
    return {"groups": [[g, [m["id"] for m in ms]] for g, ms in building_materials.by_group(mdata).items()],
            "materials": stats}


def _types_of_material(conn, material_id, types):
    rows = conn.execute("""SELECT tm.type_id, COUNT(DISTINCT tm.entity_id) FROM material_map mm
                           JOIN type_map tm ON tm.entity_id = mm.entity_id
                           WHERE mm.material_id = ? AND tm.is_primary GROUP BY tm.type_id ORDER BY 2 DESC""",
                        (material_id,)).fetchall()
    return [{"id": tid, "name": types[tid]["name"], "count": n} for tid, n in rows if tid in types][:TOP]


def material_page(conn, material_id, data=None, mdata=None):
    data, mdata = data or building_types.load(), mdata or building_materials.load()
    d = material_stats.detail(conn, material_id, mdata)
    if d is None:
        return None
    m, types = d["material"], {t["id"]: t for t in data["types"]}
    names = {x["id"]: x["name"] for x in mdata["materials"]}
    fish = m.get("fish")
    d["definition"] = _definition(fish["scheme"], fish["id"]) if fish else None
    d["links"] = _links(mdata["links"], material_id, names)
    d["types"] = [{"id": tid, "name": types[tid]["name"]} for tid in m.get("types", []) if tid in types]
    d["record_types"] = _types_of_material(conn, material_id, types)
    d["period"] = material_stats._period(m)
    return d


def here(conn, entity_id, data=None, mdata=None):
    """{types: [...], materials: [...]} of one record or place."""
    return {"types": type_stats.for_entity(conn, entity_id, data),
            "materials": material_stats.for_entity(conn, entity_id, mdata)}
