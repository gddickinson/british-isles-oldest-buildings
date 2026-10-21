"""SQLite storage and queries for places of interest, people and their links.

Tables (in the same database file as `buildings`):
  places (+ places_fts), persons, person_links(person_id, target_id, target_type, role)
"""
import json

from .db import _fts_query, set_people_text
from .people import LINK_COLUMNS, PERSON_COLUMNS
from .place_records import PLACE_COLUMN_NAMES, PLACE_COLUMNS

PLACE_FACETS = {"kind_group": "Layer", "kind_label": "Type", "nation": "Nation",
                "period": "Period", "source": "Source"}
PLACE_FTS = ["name", "description", "type", "locality", "designation", "wikipedia_extract", "extra", "other_names"]
PLACE_LIST = ["id", "kind", "kind_label", "kind_group", "type", "name", "date_text", "year_start",
              "period", "nation", "locality", "lat", "lon", "image_thumb", "source", "building_id"]


def write(conn, places, persons, links):
    cols = lambda spec: ", ".join(f"{c} {t}" for c, t in spec)
    conn.executescript(f"""
        DROP TABLE IF EXISTS places_fts; DROP TABLE IF EXISTS places;
        DROP TABLE IF EXISTS persons; DROP TABLE IF EXISTS person_links;
        CREATE TABLE places ({cols(PLACE_COLUMNS)});
        CREATE INDEX idx_pl_group ON places(kind_group);
        CREATE INDEX idx_pl_building ON places(building_id);
        CREATE VIRTUAL TABLE places_fts USING fts5(id UNINDEXED, {", ".join(PLACE_FTS)});
        CREATE TABLE persons ({cols(PERSON_COLUMNS)});
        CREATE TABLE person_links ({cols(LINK_COLUMNS)});
        CREATE INDEX idx_pk_target ON person_links(target_id);
        CREATE INDEX idx_pk_person ON person_links(person_id);
    """)
    ph = lambda n: ", ".join("?" for _ in range(n))
    conn.executemany(f"INSERT INTO places VALUES ({ph(len(PLACE_COLUMN_NAMES))})",
                     [[p.get(c) for c in PLACE_COLUMN_NAMES] for p in places])
    conn.executemany(f"INSERT INTO places_fts VALUES ({ph(len(PLACE_FTS) + 1)})",
                     [[p["id"]] + [p.get(f) or "" for f in PLACE_FTS] for p in places])
    pcols = [c for c, _ in PERSON_COLUMNS]
    conn.executemany(f"INSERT INTO persons VALUES ({ph(len(pcols))})",
                     [[p.get(c) for c in pcols] for p in persons])
    conn.executemany(f"INSERT INTO person_links VALUES ({ph(len(LINK_COLUMNS))})", links)
    conn.commit()
    names = {p["id"]: p["name"] for p in persons}
    by_building = {}
    for pid, target, ttype, *_ in links:
        if ttype == "building" and pid in names:
            by_building.setdefault(target, set()).add(names[pid])
    set_people_text(conn, {b: " ".join(sorted(n)) for b, n in by_building.items()})


def set_other_names(conn, names_by_id):
    """Make places findable by their names in other languages ({place id: text})."""
    have = [r[1] for r in conn.execute("PRAGMA table_info(places_fts)")]
    if "other_names" not in have:            # databases built before the column existed
        rows = conn.execute(f"SELECT id, {', '.join(have[1:])} FROM places_fts").fetchall()
        conn.executescript(f"""DROP TABLE places_fts;
            CREATE VIRTUAL TABLE places_fts USING fts5(id UNINDEXED, {", ".join(PLACE_FTS)});""")
        conn.executemany(f"INSERT INTO places_fts (id, {', '.join(have[1:])}) VALUES "
                         f"({', '.join('?' for _ in have)})", rows)
    conn.execute("UPDATE places_fts SET other_names = '' WHERE other_names != ''")
    conn.executemany("UPDATE places_fts SET other_names = ? WHERE id = ?",
                     [(text, pid) for pid, text in names_by_id.items()])
    conn.commit()


def has_tables(conn):
    return bool(conn.execute("SELECT 1 FROM sqlite_master WHERE name = 'places'").fetchone())


def where(filters):
    w, args = [], []
    q = _fts_query(filters.get("q") or "")
    if q:
        w.append("id IN (SELECT id FROM places_fts WHERE places_fts MATCH ?)")
        args.append(q)
    for col in PLACE_FACETS:
        vals = filters.get(col) or []
        if vals:
            w.append(f"COALESCE({col}, 'Unknown') IN ({', '.join('?' for _ in vals)})")
            args.extend(vals)
    for key, op in (("year_min", ">="), ("year_max", "<=")):
        if filters.get(key) is not None:
            w.append(f"year_start {op} ?")
            args.append(filters[key])
    if filters.get("has_image"):
        w.append("image_thumb IS NOT NULL")
    if filters.get("bbox"):
        s, west, n, e = filters["bbox"]
        w.append("lat BETWEEN ? AND ? AND lon BETWEEN ? AND ?")
        args.extend([s, n, west, e])
    return (" WHERE " + " AND ".join(w)) if w else "", args


SORTS = {"oldest": "year_start IS NULL, year_start", "newest": "year_start IS NULL, year_start DESC",
         "name": "name COLLATE NOCASE"}


def search(conn, filters, sort="oldest", limit=48, offset=0):
    from .db import name_rank
    w, args = where(filters)
    rank, rargs = name_rank(filters.get("q"), sort)
    total = conn.execute(f"SELECT COUNT(*) FROM places{w}", args).fetchone()[0]
    rows = conn.execute(f"SELECT {', '.join(PLACE_LIST)} FROM places{w} ORDER BY "
                        f"{rank}{SORTS.get(sort, SORTS['oldest'])}, name LIMIT ? OFFSET ?",
                        args + rargs + [limit, offset]).fetchall()
    return total, [dict(r) for r in rows]


def facets(conn, filters):
    out = {}
    for col in PLACE_FACETS:
        w, args = where({**filters, col: []})
        out[col] = [[r[0], r[1]] for r in conn.execute(
            f"SELECT COALESCE({col}, 'Unknown') AS v, COUNT(*) AS n FROM places{w} "
            f"GROUP BY v ORDER BY n DESC", args)]
    return out


def map_points(conn, filters):
    w, args = where(filters)
    return [dict(r) for r in conn.execute(
        f"SELECT id, name, lat, lon, kind_label, kind_group, date_text FROM places{w}"
        f"{' AND' if w else ' WHERE'} lat IS NOT NULL", args)]


def get(conn, pid):
    row = conn.execute("SELECT * FROM places WHERE id = ?", (pid,)).fetchone()
    if not row:
        return None
    p = dict(row)
    p["extra"] = json.loads(p["extra"]) if p.get("extra") else {}
    p["people"] = people_for(conn, pid)
    return p


def near(conn, lat, lon, km=5, limit=12, exclude=None):
    dlat, dlon = km / 111.0, km / 65.0
    rows = conn.execute(
        "SELECT id, name, kind_label, kind_group, date_text, DIST(lat, lon, ?, ?) AS dist FROM places "
        "WHERE lat BETWEEN ? AND ? AND lon BETWEEN ? AND ? AND id IS NOT ? ORDER BY dist LIMIT ?",
        (lat, lon, lat - dlat, lat + dlat, lon - dlon, lon + dlon, exclude, limit * 3)).fetchall()
    return [dict(r) for r in rows if r["dist"] is not None and r["dist"] <= km][:limit]


def objects_in(conn, building_id):
    return [dict(r) for r in conn.execute(
        "SELECT id, name, type, description, image_thumb FROM places WHERE building_id = ? "
        "ORDER BY name", (building_id,))]


def people_for(conn, target_id):
    return [dict(r) for r in conn.execute(
        "SELECT p.id, p.name, p.description, p.birth, p.death, l.role, l.ref FROM person_links l "
        "JOIN persons p ON p.id = l.person_id WHERE l.target_id = ? "
        "ORDER BY l.role, p.sitelinks DESC", (target_id,))]


def person(conn, pid):
    row = conn.execute("SELECT * FROM persons WHERE id = ?", (pid,)).fetchone()
    if not row:
        return None
    p = dict(row)
    p["links"] = [dict(r) for r in conn.execute(
        "SELECT l.role, l.ref, l.target_id, l.target_type, COALESCE(b.name, pl.name) AS name, "
        "COALESCE(b.date_text, pl.date_text) AS date_text, COALESCE(b.lat, pl.lat) AS lat, "
        "COALESCE(b.lon, pl.lon) AS lon, COALESCE(b.category, pl.kind_label) AS what "
        "FROM person_links l LEFT JOIN buildings b ON b.id = l.target_id "
        "LEFT JOIN places pl ON pl.id = l.target_id WHERE l.person_id = ? ORDER BY l.role, name",
        (pid,))]
    return p


def people_search(conn, q="", role="", sort="known", limit=48, offset=0):
    w, args = [], []
    if q:
        w.append("(p.name LIKE ? OR p.description LIKE ?)")
        args += [f"%{q}%", f"%{q}%"]
    if role:
        w.append("p.id IN (SELECT person_id FROM person_links WHERE role = ?)")
        args.append(role)
    ws = (" WHERE " + " AND ".join(w)) if w else ""
    order = {"known": "p.sitelinks DESC", "born": "p.birth IS NULL, p.birth",
             "name": "p.name COLLATE NOCASE"}.get(sort, "p.sitelinks DESC")
    total = conn.execute(f"SELECT COUNT(*) FROM persons p{ws}", args).fetchone()[0]
    rows = conn.execute(
        f"SELECT p.id, p.name, p.description, p.birth, p.death, p.image_thumb, p.summary, "
        f"(SELECT GROUP_CONCAT(l.role || '|' || l.target_id || '|' || COALESCE(b.name, pl.name), '\n') "
        f" FROM person_links l LEFT JOIN buildings b ON b.id = l.target_id "
        f" LEFT JOIN places pl ON pl.id = l.target_id WHERE l.person_id = p.id) AS links "
        f"FROM persons p{ws} ORDER BY {order} LIMIT ? OFFSET ?", args + [limit, offset]).fetchall()
    out = []
    for r in rows:
        d = dict(r)
        d["links"] = [dict(zip(("role", "target_id", "name"), x.split("|", 2)))
                      for x in (d["links"] or "").split("\n") if x][:12]
        out.append(d)
    return total, out


def roles(conn):
    return [[r[0], r[1]] for r in conn.execute(
        "SELECT role, COUNT(DISTINCT person_id) FROM person_links GROUP BY role ORDER BY 2 DESC")]
