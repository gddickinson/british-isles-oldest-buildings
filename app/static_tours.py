"""Static export of stories, tours and "on this day" (used by app.static_export): data/stories.json
(static/stories.js), data/tours.json (static_api.js routes), data/on_this_day.json (on_this_day.js)."""
import json

from bidb import stories_db
from bidb.tour_elevation import decode, encode

from .geo_simplify import douglas_peucker

ROUTE_TOL = 0.00004         # degrees (about 4 m): route lines simplified, 3.2 MB → 1.1 MB, not visible on the map

STORY_FIELDS = ["entity_kind", "entity_id", "kind", "heading", "text", "source_url", "name", "nation", "locality",
                "lat", "lon", "date_text", "licence"]


def export(conn, out_dir):
    """Write both files; returns {record id: [story kinds]} for the catalogue rows."""
    kinds = stories_db.kinds_by_record(conn)
    if stories_db.has_tables(conn):
        rows = stories_db.search(conn, limit=10**6)["rows"]
        packed = [[r.get(f) if r.get(f) is not None else "" for f in STORY_FIELDS] for r in rows]
        path = out_dir / "stories.json"
        path.write_text(json.dumps({"rows": packed}, ensure_ascii=False, separators=(",", ":")))
        print(f"exported {len(packed)} stories ({path.stat().st_size / 1e6:.1f} MB)")
    if conn.execute("SELECT 1 FROM sqlite_master WHERE name = 'tours'").fetchone():
        tours = []
        for r in conn.execute("SELECT * FROM tours ORDER BY mode, theme, title"):
            t = dict(r)
            t["stops"] = json.loads(t["stops"] or "[]")
            t["elevation"] = json.loads(t["elevation"]) if t.get("elevation") else None
            t["stages"] = json.loads(t["stages"]) if t.get("stages") else None
            if t.get("geometry"):
                t["geometry"] = encode(douglas_peucker(decode(t["geometry"]), ROUTE_TOL))
            tours.append(t)
        (out_dir / "tours.json").write_text(json.dumps(tours, ensure_ascii=False, separators=(",", ":")))
        print(f"exported {len(tours)} tours")
    if conn.execute("SELECT 1 FROM sqlite_master WHERE name = 'on_this_day'").fetchone():
        days = {}
        for m, d, y, what, kind, rid, name in conn.execute(
                "SELECT month, day, year, what, entity_kind, entity_id, name FROM on_this_day ORDER BY year"):
            days.setdefault(f"{m}-{d}", []).append([y, what, kind, rid, name])
        (out_dir / "on_this_day.json").write_text(json.dumps(days, ensure_ascii=False, separators=(",", ":")))
    if conn.execute("SELECT 1 FROM sqlite_master WHERE name = 'visiting'").fetchone():
        from bidb.visiting import COLUMNS as VC
        visits = {r[0]: dict(zip(VC[1:], r[1:])) for r in conn.execute(f"SELECT {', '.join(VC)} FROM visiting")}
        (out_dir / "visiting.json").write_text(json.dumps(visits, ensure_ascii=False, separators=(",", ":")))
    if conn.execute("SELECT 1 FROM sqlite_master WHERE name = 'old_name_links'").fetchone():
        from bidb.welsh_names import for_record as names
        links = dict(conn.execute("SELECT record_id, headname FROM old_name_links"))
        heads = {}                                   # {headname: [[form, year, date text, source], …] (shown ones), total}
        for rid, head in links.items():
            if head not in heads:
                n = names(conn, rid)
                heads[head] = [[f["form"], f["year"], f["date_text"], f["source"]] for f in n["forms"]] + [n["total"]]
        (out_dir / "old_names.json").write_text(json.dumps({"h": heads, "r": links}, ensure_ascii=False, separators=(",", ":")))
    if conn.execute("SELECT 1 FROM sqlite_master WHERE name = 'stops'").fetchone():
        from bidb.naptan import near                 # catalogue buildings only: every bus stop is too much to host
        stops = {}                                   # {record id: [[bus stop, locality, km], …, ferry or null]}
        for rid, lat, lon in conn.execute("SELECT id, lat, lon FROM buildings WHERE lat IS NOT NULL"):
            n = near(conn, lat, lon)
            if n["bus"] or n["ferry"]:
                stops[rid] = [[s["name"], s["locality"], s["km"]] for s in n["bus"]] + \
                    [[n["ferry"][0]["name"], n["ferry"][0]["locality"], n["ferry"][0]["km"]] if n["ferry"] else None]
        (out_dir / "stops.json").write_text(json.dumps(stops, ensure_ascii=False, separators=(",", ":")))
    if conn.execute("SELECT 1 FROM sqlite_master WHERE name = 'depictions'").fetchone():
        arts = {}                                    # {record id: [[title, creator, year, Commons file], …]}
        for rid, title, creator, year, image in conn.execute(
                "SELECT entity_id, title, creator, year, image FROM depictions ORDER BY year IS NULL, year"):
            arts.setdefault(rid, []).append([title, creator, year, image])
        (out_dir / "depictions.json").write_text(json.dumps(arts, ensure_ascii=False, separators=(",", ":")))
    if conn.execute("SELECT 1 FROM sqlite_master WHERE name = 'excavations'").fetchone():
        digs = {}                                    # {record id: [[what, years, who], …]}
        for rid, what, years, who in conn.execute("SELECT entity_id, what, years, who FROM excavations"):
            digs.setdefault(rid, []).append([what, years, who])
        (out_dir / "excavations.json").write_text(json.dumps(digs, ensure_ascii=False, separators=(",", ":")))
    from bidb.oldest_lists import lists
    from .quiz_api import pool
    (out_dir / "quiz.json").write_text(json.dumps(pool(conn), ensure_ascii=False, separators=(",", ":")))
    (out_dir / "oldest_lists.json").write_text(json.dumps(lists(conn), ensure_ascii=False, separators=(",", ":")))
    from bidb.oldest_things import index as things
    (out_dir / "things.json").write_text(json.dumps(things(), ensure_ascii=False, separators=(",", ":")))
    from bidb.glossary import entries as glossary
    (out_dir / "glossary.json").write_text(json.dumps(glossary(), ensure_ascii=False, separators=(",", ":")))
    from bidb.trade_stories import export as trades
    (out_dir / "trades.json").write_text(json.dumps(trades(conn), ensure_ascii=False, separators=(",", ":")))
    if conn.execute("SELECT 1 FROM sqlite_master WHERE name = 'dendro'").fetchone():
        tree = {}                                    # {record id: [[location, date text, method, reference], …]}
        for rid, loc, text, method, ref in conn.execute(
                "SELECT record_id, location, date_text, method, reference FROM dendro ORDER BY felled_from"):
            tree.setdefault(rid, []).append([loc, text, method, ref])
        (out_dir / "dendro.json").write_text(json.dumps(tree, ensure_ascii=False, separators=(",", ":")))
    if conn.execute("SELECT 1 FROM sqlite_master WHERE name = 'domesday'").fetchone():
        # {settlement qid: [name, Open Domesday id, (churches, priests, households, Phillimore ref)]}
        # and {record id: settlement qid (prefixed "=" when itself)}
        from bidb.domesday_entries import entry
        places, marks = {}, {}
        for rid, sid, name, od, itself in conn.execute("SELECT entity_id, settlement_id, settlement, od_id, itself FROM domesday"):
            if sid not in places:
                e = entry(conn, od)
                places[sid] = [name, od] + ([e["churches"], e["priests"], e["households"], e["phillimore"]] if e else [])
            marks[rid] = ("=" if itself else "") + sid
        (out_dir / "domesday.json").write_text(json.dumps({"s": places, "r": marks}, ensure_ascii=False,
                                                          separators=(",", ":")))
    return kinds
