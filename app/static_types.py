"""Static export of the page /types (BT4b, used by app.static_export), compact because the hosted copy is nearly full:

    types_tree.json      the tree, the materials by group, materials by century, every family link of types and of
                         materials once (pages name theirs by index; the tree's own links are rebuilt from them)
    types_index.json     which file holds each page, and type and material names for the detail views
    types_pages_<n>.json type pages ("t:<id>") and material pages ("m:<id>"), a few files of about 1 MB
    types_here_<n>.json  {record or place id: [types, materials]} by static_places.shard_of (one file per detail view)

A catalogue record is named by its id alone (the browser holds the catalogue rows); a place as
[id, name, year, date text, county, nation]. Places on the maps are delta-coded integers (1/1000 degree), without
pop-ups. Examples are cut to EXAMPLES (types) and MAT_EXAMPLES (materials), evidence sentences to EVIDENCE characters;
thumbnails are left out (external images are blocked when hosted). static/static_types.js expands all of this."""
import json

from bidb import building_materials, building_types, type_charts, type_pages

from .static_places import shard_of

EXAMPLES, MAT_EXAMPLES, EVIDENCE = 40, 25, 200
PAGE_BYTES = 1_200_000
HERE_SHARDS = 16
VIA = {"wikidata": 0, "wikipedia": 1, "register": 2}       # how a material was found (types_here)


def _dump(path, obj):
    path.write_text(json.dumps(obj, ensure_ascii=False, separators=(",", ":")))
    return path.stat().st_size


def ref(e):
    """A catalogue record by its id; a place with what the page shows of it."""
    if e["source"] == "building":
        return e["id"]
    return [e["id"], e["name"], e["year"], e.get("date_text"), e.get("county"), e.get("nation")]


def deltas(points):
    """[[lat, lon], …] → flat integers in 1/1000 degree, each the step from the one before."""
    out, plat, plon = [], 0, 0
    for lat, lon in points:
        a, b = round(lat * 1000), round(lon * 1000)
        out += [a - plat, b - plon]
        plat, plon = a, b
    return out


def _points(points, primary_at=None):
    """Split map points into catalogue ids and place deltas, main type and not ("b", "b2", "p", "p2")."""
    out = {"b": [], "b2": [], "p": [], "p2": []}
    for q in points:
        second = primary_at is not None and q[primary_at] == 0
        if q[3] == "building":
            out["b2" if second else "b"].append(q[2])
        else:
            out["p2" if second else "p"].append((q[0], q[1]))
    out["p"], out["p2"] = deltas(out["p"]), deltas(out["p2"])
    return {k: v for k, v in out.items() if v}


def _brief(e):
    return {k: v for k, v in e.items() if k != "thumb"} if e else None


def _link_index(links):
    return {id(link): i for i, link in enumerate(links)}


def type_entry(d, link_at, links):
    """One type page in the hosted form."""
    d = dict(d)
    d["links"] = [link_at[id(k)] for k in links if d["type"]["id"] in (k["from"], k["to"])]
    d["earliest"] = _brief(d.get("earliest"))
    ex = d.pop("examples", None) or []
    d["ex"] = [[ref(e), int(bool(e["too_early"]))] for e in ex[:EXAMPLES]]
    d["sp"] = [[s["county"], s["nation"], s["year"], ref(s)] for s in d.pop("spread", None) or []]
    d["pts"] = _points(d.pop("points", None) or [], primary_at=5)
    return d


def material_entry(d, link_at, links):
    d = dict(d)
    mid = d["material"]["id"]
    d["links"] = [link_at[id(k)] for k in links if mid in (k["from"], k["to"])]
    d["earliest"] = _brief(d.get("earliest"))
    ex = d.pop("examples", None) or []
    d["ex"] = [[ref(e), int(bool(e["too_early"])), _trim(e.get("evidence"))] for e in ex[:MAT_EXAMPLES]]
    d["pts"] = _points(d.pop("points", None) or [])
    return d


def _trim(text):
    if not text or len(text) <= EVIDENCE:
        return text
    return text[:EVIDENCE - 1] + "…"


def here(conn, types, mats):
    """{entity: [[type index, or -1 - index when not the main type], [material index * 3 + how found]]}."""
    tidx = {t["id"]: i for i, t in enumerate(types)}
    midx = {m["id"]: i for i, m in enumerate(mats)}
    out = {}
    for e, t, primary in conn.execute("SELECT entity_id, type_id, is_primary FROM type_map ORDER BY is_primary DESC"):
        if t in tidx:
            out.setdefault(e, [[], []])[0].append(tidx[t] if primary else -1 - tidx[t])
    seen = set()
    for e, m, via in conn.execute("SELECT entity_id, material_id, via FROM material_map ORDER BY rowid"):
        if m in midx and (e, m, via) not in seen:
            seen.add((e, m, via))
            out.setdefault(e, [[], []])[1].append(midx[m] * 3 + VIA.get(via, 2))
    return out


def export(conn, out_dir):
    """Write the files; returns the total size in bytes."""
    if not conn.execute("SELECT 1 FROM sqlite_master WHERE name = 'type_map'").fetchone():
        return 0
    data, mdata = building_types.load(), building_materials.load()
    tree = type_pages.tree(conn, data)
    for t in tree["types"]:
        t["earliest"] = _brief(t["earliest"])
    del tree["links"]
    tlinks, mlinks = data["links"], mdata["links"]
    tat, mat = _link_index(tlinks), _link_index(mlinks)
    size = _dump(out_dir / "types_tree.json", {
        "tree": tree, "materials": type_pages.materials(conn, mdata),
        "centuries": type_charts.centuries(conn, mdata), "type_links": tlinks, "mat_links": mlinks})
    pages = [("t:" + t["id"], type_entry(type_pages.type_page(conn, t["id"], data, mdata), tat, tlinks))
             for t in data["types"]]
    for m in mdata["materials"]:
        d = type_pages.material_page(conn, m["id"], data, mdata)
        if d:
            pages.append(("m:" + m["id"], material_entry(d, mat, mlinks)))
    files, index, cur, cur_size = [], {}, {}, 0
    for key, page in pages:
        n = len(json.dumps(page, ensure_ascii=False, separators=(",", ":")))
        if cur and cur_size + n > PAGE_BYTES:
            files.append(cur)
            cur, cur_size = {}, 0
        cur[key], cur_size, index[key] = page, cur_size + n, len(files)
    files.append(cur)
    for i, part in enumerate(files):
        size += _dump(out_dir / f"types_pages_{i}.json", part)
    shards = [{} for _ in range(HERE_SHARDS)]
    for e, v in here(conn, data["types"], mdata["materials"]).items():
        shards[shard_of(e) % HERE_SHARDS][e] = v
    for i, part in enumerate(shards):
        size += _dump(out_dir / f"types_here_{i}.json", part)
    size += _dump(out_dir / "types_index.json", {
        "pages": index, "here_shards": HERE_SHARDS, "types": [[t["id"], t["name"], t["family"]] for t in data["types"]],
        "mats": [[m["id"], m["name"], m["group"]] for m in mdata["materials"]]})
    print(f"exported /types: {len(pages)} pages in {len(files)} files, {size / 1e6:.1f} MB")
    return size
