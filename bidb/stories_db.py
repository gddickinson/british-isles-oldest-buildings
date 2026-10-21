"""Table `stories`: legends, ghosts, folklore and curious history per building or place.

    entity_kind ('building' | 'place'), entity_id, kind (stories_parse.KINDS), heading, text,
    source_url, licence
"""
from .stories_parse import KINDS

COLUMNS = ["entity_kind", "entity_id", "kind", "heading", "text", "source_url", "licence"]
LICENCE = "CC BY-SA 4.0 (Wikipedia)"


def write(conn, rows):
    conn.executescript(f"""DROP TABLE IF EXISTS stories;
        CREATE TABLE stories ({", ".join(c + " TEXT" for c in COLUMNS)});
        CREATE INDEX idx_story_entity ON stories(entity_id);
        CREATE INDEX idx_story_kind ON stories(kind);""")
    conn.executemany(f"INSERT INTO stories VALUES ({', '.join('?' for _ in COLUMNS)})",
                     [[r.get(c) for c in COLUMNS] for r in rows])
    conn.commit()


def has_tables(conn):
    return bool(conn.execute("SELECT 1 FROM sqlite_master WHERE name = 'stories'").fetchone())


def for_record(conn, record_id):
    if not has_tables(conn):
        return []
    return [dict(zip(COLUMNS, r)) | {"kind_label": KINDS.get(r[2], r[2])} for r in conn.execute(
        f"SELECT {', '.join(COLUMNS)} FROM stories WHERE entity_id = ? ORDER BY rowid", (record_id,))]


def kinds_by_record(conn):
    """{record id: [kinds]} for every record with a story."""
    out = {}
    if has_tables(conn):
        for eid, kind in conn.execute("SELECT DISTINCT entity_id, kind FROM stories"):
            out.setdefault(eid, []).append(kind)
    return out


def search(conn, q="", kind="", nation="", limit=60, offset=0):
    """Stories with the record they belong to (name, nation, place, coordinates, thumbnail)."""
    if not has_tables(conn):
        return {"total": 0, "rows": []}
    rec = """SELECT 'building' AS k, id, name, nation, locality, lat, lon, image_thumb, date_text FROM buildings
             UNION ALL SELECT 'place', id, name, nation, locality, lat, lon, image_thumb, date_text FROM places"""
    where, args = [], []
    if kind:
        where.append("s.kind = ?")
        args.append(kind)
    if nation:
        where.append("r.nation = ?")
        args.append(nation)
    for w in (q or "").split():
        where.append("(s.text LIKE ? OR r.name LIKE ? OR r.locality LIKE ?)")
        args += [f"%{w}%"] * 3
    sql = f"FROM stories s JOIN ({rec}) r ON r.id = s.entity_id {'WHERE ' + ' AND '.join(where) if where else ''}"
    total = conn.execute(f"SELECT COUNT(*) {sql}", args).fetchone()[0]
    cols = ["entity_kind", "entity_id", "kind", "heading", "text", "source_url", "name", "nation", "locality",
            "lat", "lon", "image_thumb", "date_text", "licence"]
    rows = conn.execute(f"""SELECT s.entity_kind, s.entity_id, s.kind, s.heading, s.text, s.source_url, r.name,
        r.nation, r.locality, r.lat, r.lon, r.image_thumb, r.date_text, s.licence {sql}
        ORDER BY (s.heading = '' AND s.text LIKE 'Wikipedia lists%'), length(s.text) DESC LIMIT ? OFFSET ?""",
        args + [limit, offset]).fetchall()
    return {"total": total, "rows": [dict(zip(cols, r)) | {"kind_label": KINDS.get(r[2], r[2])} for r in rows]}


def counts(conn):
    if not has_tables(conn):
        return {}
    return {k: n for k, n in conn.execute("SELECT kind, COUNT(DISTINCT entity_id) FROM stories GROUP BY kind")}
