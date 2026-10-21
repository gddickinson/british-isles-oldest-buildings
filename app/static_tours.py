"""Static export of stories, tours and "on this day" (used by app.static_export): data/stories.json
(static/stories.js), data/tours.json (static_api.js routes), data/on_this_day.json (on_this_day.js)."""
import json

from bidb import stories_db

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
    if conn.execute("SELECT 1 FROM sqlite_master WHERE name = 'depictions'").fetchone():
        arts = {}                                    # {record id: [[title, creator, year, Commons file], …]}
        for rid, title, creator, year, image in conn.execute(
                "SELECT entity_id, title, creator, year, image FROM depictions ORDER BY year IS NULL, year"):
            arts.setdefault(rid, []).append([title, creator, year, image])
        (out_dir / "depictions.json").write_text(json.dumps(arts, ensure_ascii=False, separators=(",", ":")))
    if conn.execute("SELECT 1 FROM sqlite_master WHERE name = 'domesday'").fetchone():
        # {settlement qid: [name, Open Domesday id]} and {record id: settlement qid (prefixed "=" when itself)}
        places, marks = {}, {}
        for rid, sid, name, od, itself in conn.execute("SELECT entity_id, settlement_id, settlement, od_id, itself FROM domesday"):
            places[sid] = [name, od]
            marks[rid] = ("=" if itself else "") + sid
        (out_dir / "domesday.json").write_text(json.dumps({"s": places, "r": marks}, ensure_ascii=False,
                                                          separators=(",", ":")))
    return kinds
