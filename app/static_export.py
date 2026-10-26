"""Export a self-contained static copy of the GUI to dist/ (for hosting): python -m app.static_export

Pages are rendered with the Flask test client in STATIC_MODE; the browser then answers API calls
from dist/data/*.json via static/static_api.js. Editing and rebuilding are disabled.
"""
import base64
import json
import re
import shutil

from bidb import db, pron_db
from bidb.categories import CATEGORY_GROUPS, CATEGORY_ORDER, GROUP_ORDER
from bidb.classify import PERIOD_ORDER
from bidb.config import DATA_DIR, ROOT, cache_dir

from . import pages, static_places, static_pron, static_thumbs, static_tours, static_types
from .server import app

DIST = ROOT / "dist"
PAGES = {"/": "index.html", "/map": "map.html", "/places": "places.html", "/people": "people.html", "/pronunciation": "pronunciation.html",
         "/history": "history.html", "/change": "change.html", "/trades": "trades.html", "/oldest": "oldest.html",
         "/stats": "stats.html", "/tours": "tours.html", "/stories": "stories.html", "/quiz": "quiz.html", "/compare": "compare.html", "/data": "data.html", "/glossary": "glossary.html",
         "/types": "types.html",
         "/settings": "settings.html", "/help": "help.html"}
EXTRACT_CHARS = 900          # keep the data file small enough to host
SHARD_BYTES = 9_000_000      # each data file stays well under the host's 16 MB per-file limit


def _pack_historic_tiles():
    """Bundled historic map tiles (app.historic_build), one JSON pack per layer {"z/x/y": base64 WebP}:
    an artifact version holds at most 511 files, far fewer than the tiles."""
    tiles = cache_dir() / "historic_tiles"
    out = DIST / "static" / "data" / "historic" / "packs"
    out.mkdir(parents=True, exist_ok=True)
    for layer in sorted(tiles.iterdir()) if tiles.exists() else []:
        pack = {f"{t.parent.parent.name}/{t.parent.name}/{t.stem}": base64.b64encode(t.read_bytes()).decode()
                for t in layer.rglob("*.webp")}
        (out / f"{layer.name}.json").write_text(json.dumps(pack, separators=(",", ":")))


def _strip_document(html):
    """The artifact host wraps the main page in its own <html>/<head>/<body> skeleton."""
    head = html.split("<head>", 1)[1].split("</head>", 1)[0]
    body = html.split("<body", 1)[1].split(">", 1)[1].rsplit("</body>", 1)[0]
    head = head.replace('<meta charset="utf-8">', "").replace(
        '<meta name="viewport" content="width=device-width, initial-scale=1">', "")
    return head.strip() + "\n" + body.strip() + "\n"


def _rewrite(html):
    for route, fname in PAGES.items():
        html = html.replace(f'href="{route}"', f'href="{fname}"')
    html = re.sub(r'href="/building/([^"]+)"', r'href="index.html#\1"', html)
    return html.replace('"/static/', '"static/')


def export(thumb_limit=850):           # 1,100 until the change layers pushed the copy past 256 MiB
    if DIST.exists():
        shutil.rmtree(DIST)
    (DIST / "data").mkdir(parents=True)
    shutil.copytree(ROOT / "app" / "static", DIST / "static")
    if (ROOT / "docs" / "img").is_dir():                 # help page screenshots (shared with the README)
        shutil.copytree(ROOT / "docs" / "img", DIST / "static" / "help")
    _pack_historic_tiles()
    _pack_map_tiles()
    pages.STATIC_MODE = True
    try:
        client = app.test_client()
        for route, fname in PAGES.items():
            resp = client.get(route)
            assert resp.status_code == 200, (route, resp.status_code)
            html = _rewrite(resp.get_data(as_text=True))
            (DIST / fname).write_text(_strip_document(html) if fname == "index.html" else html)
    finally:
        pages.STATIC_MODE = False
    conn = db.connect(readonly=True)
    rows = db.all_rows(conn, {})
    drop = {"date_source", "district", "image_file", "edited", "user_notes"}
    people = {}                 # names of linked people, so the search box finds "Shakespeare"
    if conn.execute("SELECT 1 FROM sqlite_master WHERE name = 'person_links'").fetchone():
        for bid, name in conn.execute("SELECT l.target_id, p.name FROM person_links l JOIN persons p "
                                      "ON p.id = l.person_id WHERE l.target_type = 'building'"):
            people.setdefault(bid, set()).add(name)
    other = pron_db.other_names(conn, "building")      # names in Welsh, Gaelic, Irish …
    story_kinds = static_tours.export(conn, DIST / "data")
    for r in rows:
        if r["id"] in people:
            r["people_text"] = " ".join(sorted(people[r["id"]]))
        if r["id"] in other:
            r["other_names"] = other[r["id"]]
        if r["id"] in story_kinds:
            r["sk"] = story_kinds[r["id"]]
        for k in drop:
            r.pop(k, None)
        for k in ("wikipedia_extract", "register_notes"):
            if r.get(k) and len(r[k]) > EXTRACT_CHARS:
                r[k] = r[k][:EXTRACT_CHARS].rsplit(" ", 1)[0] + " …"
        for k in [k for k, v in r.items() if v in (None, "")]:
            del r[k]
    thumbs = static_thumbs.fetch_all(rows, limit=thumb_limit)
    plan_index = {}             # plans are fetched one small shard at a time, when a detail view opens
    plan_shards = static_thumbs.write_shards(static_thumbs.fetch_plans(rows), DIST / "data", "plans",
                                             max_bytes=3_000_000, index=plan_index)
    if conn.execute("SELECT 1 FROM sqlite_master WHERE name = 'timeline'").fetchone():
        events = {}
        for rid, y, label, text in conn.execute("SELECT entity_id, year, label, text FROM timeline ORDER BY year"):
            events.setdefault(rid, []).append([y, label, text])
        for r in rows:
            if r["id"] in events:
                r["timeline"] = events[r["id"]]
    lazy = _split_lazy(rows, thumbs)
    info = json.loads((DATA_DIR / "build_info.json").read_text())
    meta = {"facets": list(db.FACETS), "periods": PERIOD_ORDER, "categories": CATEGORY_ORDER,
            "groups": GROUP_ORDER, "group_of": {c: g for g, cats in CATEGORY_GROUPS for c in cats},
            "build_info": info, "plan_shards": plan_shards, "plan_index": plan_index, **lazy,
            "row_shards": write_json_shards(rows, "buildings_rows"),
            "place_shards": static_places.export(conn, DIST / "data", write_json_shards),
            "place_kinds": static_places.KIND_DEFAULTS, "url_prefixes": static_places.URL_PREFIXES}
    (DIST / "data" / "buildings.json").write_text(
        json.dumps({"meta": meta, "rows": []}, ensure_ascii=False, separators=(",", ":")))
    static_pron.export(conn, DIST / "data")
    static_types.export(conn, DIST / "data")
    from bidb import evidence
    (DIST / "data" / "evidence.json").write_text(json.dumps(evidence.export(), ensure_ascii=False, separators=(",", ":")))
    ver = DATA_DIR / "verification.json"
    if ver.exists():
        shutil.copy(ver, DIST / "data" / "verification.json")
    with app.app_context():
        from .api import history_with_places
        (DIST / "data" / "history.json").write_text(json.dumps(history_with_places(), ensure_ascii=False))
    size = sum(p.stat().st_size for p in DIST.rglob("*") if p.is_file())
    print(f"exported {len(rows)} records to {DIST} ({size / 1e6:.1f} MB)")


# shown only in a record's detail view: loaded per record (row "d" = details shard number)
DETAIL_FIELDS = ("sources", "refs", "image_page", "date_evidence", "register_notes", "register_url",
                 "register_source", "street_address", "website", "plan_image", "timeline")
LAZY_SHARD_BYTES = 600_000


def _split_lazy(rows, thumbs):
    """Move thumbnails, detail-only fields and outlines out of the rows into small files loaded on
    demand, so the first load holds only what lists, filters and search need. Thumbnails are
    ordered oldest first (the default sort) so a gallery page needs one or two files."""
    by_age = sorted(rows, key=lambda r: (r.get("year_start") is None, r.get("year_start") or 0, r["name"]))
    thumb_index, detail_index, details, outlines = {}, {}, {}, {}
    ordered = {r["id"]: thumbs[r["id"]] for r in by_age if r["id"] in thumbs}
    thumb_shards = static_thumbs.write_shards(ordered, DIST / "data", "thumbs",
                                              max_bytes=LAZY_SHARD_BYTES, index=thumb_index)
    for r in rows:
        r.pop("image_thumb", None)              # external images are blocked when hosted
        if r["id"] in thumb_index:
            r["t"] = thumb_index[r["id"]]
        d = {k: r.pop(k) for k in DETAIL_FIELDS if k in r}
        if d:
            details[r["id"]] = d
        if r.get("footprint"):
            outlines[r["id"]] = {k: r.get(k) for k in ("name", "category_group", "lat", "lon")} | {"footprint": r.pop("footprint")}
    detail_shards = static_thumbs.write_shards(details, DIST / "data", "details",
                                               max_bytes=LAZY_SHARD_BYTES, index=detail_index)
    by_id = {r["id"]: r for r in rows}
    for bid, i in detail_index.items():
        by_id[bid]["d"] = i
    outline_shards = static_thumbs.write_shards(outlines, DIST / "data", "outlines", max_bytes=3_000_000)
    return {"thumb_shards": thumb_shards, "detail_shards": detail_shards, "outline_shards": outline_shards}


TILE_PACK_BYTES = 3_000_000


def _pack_map_tiles():
    """The hosted copy may hold only ~500 files: bundle each tiled map layer (basemap/<layer>/<tile>.json)
    into packs of ≤ 3 MB (pack_<n>.json = {tile: data}) with pack_index.json = {tile: n}."""
    base = DIST / "static" / "data" / "basemap"
    for layer in sorted(p.parent for p in base.glob("*/index.json")):
        index = json.loads((layer / "index.json").read_text())
        packs, cur, size, where = [], {}, 0, {}
        for key in sorted(index):
            text = (layer / f"{key}.json").read_text()
            if cur and size + len(text) > TILE_PACK_BYTES:
                packs.append(cur)
                cur, size = {}, 0
            cur[key] = json.loads(text)
            size += len(text)
            where[key] = len(packs)
        if cur:
            packs.append(cur)
        for f in layer.glob("*.json"):
            f.unlink()
        for n, pack in enumerate(packs):
            (layer / f"pack_{n}.json").write_text(json.dumps(pack, ensure_ascii=False, separators=(",", ":")))
        (layer / "pack_index.json").write_text(json.dumps(where, separators=(",", ":")))


def write_json_shards(items, stem, key=None):
    """Write a list as JSON files of at most SHARD_BYTES each -> list of file names; with `key`, one file per
    key value instead (items sorted by it)."""
    names, chunk, size = [], [], 0
    if key is not None:
        from itertools import groupby
        for k, part in groupby(items, key):
            name = f"{stem}_{k}.json"
            (DIST / "data" / name).write_text(json.dumps(list(part), ensure_ascii=False, separators=(",", ":")))
            names.append(name)
        return names
    def flush():
        name = f"{stem}_{len(names)}.json"
        (DIST / "data" / name).write_text(json.dumps(chunk, ensure_ascii=False, separators=(",", ":")))
        names.append(name)
    for it in items:
        n = len(json.dumps(it, ensure_ascii=False))
        if chunk and size + n > SHARD_BYTES:
            flush()
            chunk, size = [], 0
        chunk.append(it)
        size += n
    if chunk:
        flush()
    return names


if __name__ == "__main__":
    export()
