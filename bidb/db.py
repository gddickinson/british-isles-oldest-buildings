"""SQLite storage: schema, bulk write, filters and the core read queries used by the GUI."""
import math
import sqlite3

from .config import db_path

COLUMNS = [
    ("id", "TEXT PRIMARY KEY"), ("name", "TEXT"), ("description", "TEXT"),
    ("category", "TEXT"), ("category_group", "TEXT"), ("classes", "TEXT"),
    ("is_building", "INTEGER"), ("oldest_of_type", "TEXT"), ("type_claim", "TEXT"),
    ("status", "TEXT"), ("period", "TEXT"), ("year_start", "INTEGER"),
    ("date_text", "TEXT"), ("date_source", "TEXT"),
    ("date_confidence", "TEXT"), ("date_evidence", "TEXT"),
    ("nation", "TEXT"), ("county", "TEXT"), ("district", "TEXT"), ("locality", "TEXT"),
    ("located_in", "TEXT"), ("street_address", "TEXT"), ("postcode", "TEXT"),
    ("lat", "REAL"), ("lon", "REAL"),
    ("heritage_grade", "TEXT"), ("designations", "TEXT"),
    ("nhle_id", "TEXT"), ("hes_id", "TEXT"), ("cadw_id", "TEXT"),
    ("ie_smr_id", "TEXT"), ("ie_niah_id", "TEXT"), ("ie_nm_id", "TEXT"),
    ("style", "TEXT"), ("materials", "TEXT"), ("architect", "TEXT"),
    ("religion", "TEXT"), ("dedication", "TEXT"), ("condition", "TEXT"),
    ("height_m", "REAL"), ("website", "TEXT"),
    ("image_file", "TEXT"), ("image_thumb", "TEXT"), ("image_page", "TEXT"),
    ("wikipedia_title", "TEXT"), ("wikipedia_extract", "TEXT"),
    ("wikidata_id", "TEXT"), ("curated", "INTEGER"), ("curated_notes", "TEXT"),
    ("user_notes", "TEXT"), ("edited", "INTEGER"), ("landmark", "TEXT"),
    ("register_notes", "TEXT"), ("register_url", "TEXT"), ("register_source", "TEXT"),
    ("refs", "TEXT"), ("sources", "TEXT"), ("date_check", "TEXT"), ("date_check_note", "TEXT"),
    ("image_note", "TEXT"), ("plan_image", "TEXT"), ("footprint", "TEXT"),
]
COLUMN_NAMES = [c for c, _ in COLUMNS]
FTS_FIELDS = ["name", "description", "locality", "located_in", "county", "classes",
              "wikipedia_extract", "curated_notes", "style", "dedication", "type_claim",
              "people_text", "other_names"]
# people_text: names of linked people (set_people_text); other_names: the name in Welsh, Gaelic,
# Irish … from the pronunciations stage (set_other_names)

# Filterable columns exposed to the GUI (column -> label)
FACETS = {"category_group": "Group", "category": "Category", "period": "Period",
          "nation": "Nation",
          "heritage_grade": "Heritage grade", "date_confidence": "Date basis",
          "date_check": "Date check",
          "status": "Status", "county": "County"}
SORTS = {"oldest": "year_start IS NULL, year_start ASC",
         "newest": "year_start IS NULL, year_start DESC",
         "name": "name COLLATE NOCASE", "nation": "nation IS NULL, nation, year_start",
         "distance": "dist IS NULL, dist"}


def name_rank(q, sort):
    """ORDER BY prefix and args putting name matches first when searching: exact name, name containing
    the whole phrase, name containing every word, then the rest (the chosen sort applies within each).
    Not for name or distance order."""
    import re
    words = [w for w in re.findall(r"\w+", (q or "").lower()) if len(w) > 1]
    if not words or sort in ("name", "distance"):
        return "", []
    phrase = " ".join(words)
    every = " AND ".join("lower(name) LIKE ?" for _ in words)
    return (f"CASE WHEN lower(name) = ? THEN 0 WHEN lower(name) LIKE ? THEN 1 WHEN {every} THEN 2 ELSE 3 END, ",
            [phrase, f"%{phrase}%"] + [f"%{w}%" for w in words])


def dist_km(lat1, lon1, lat2, lon2):
    """Great-circle distance in km (registered as SQL function DIST)."""
    if None in (lat1, lon1, lat2, lon2):
        return None
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = p2 - p1, math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 6371.0 * 2 * math.asin(math.sqrt(min(1.0, a)))


def connect(path=None, readonly=False):
    path = path or db_path()
    if readonly:
        conn = sqlite3.connect(f"file:{path}?mode=ro", uri=True, check_same_thread=False)
    else:
        path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.create_function("DIST", 4, dist_km, deterministic=True)
    return conn


def write_all(records, path=None):
    """Replace the database contents with the given list of record dicts."""
    conn = connect(path)
    cols_sql = ", ".join(f"{c} {t}" for c, t in COLUMNS)
    conn.executescript(f"""
        DROP TABLE IF EXISTS buildings_fts;
        DROP TABLE IF EXISTS buildings;
        CREATE TABLE buildings ({cols_sql});
        CREATE INDEX idx_year ON buildings(year_start);
        CREATE INDEX idx_cat ON buildings(category);
        CREATE INDEX idx_nation ON buildings(nation);
        CREATE VIRTUAL TABLE buildings_fts USING fts5(id UNINDEXED, {", ".join(FTS_FIELDS)});
    """)
    placeholders = ", ".join("?" for _ in COLUMN_NAMES)
    conn.executemany(f"INSERT INTO buildings ({', '.join(COLUMN_NAMES)}) VALUES ({placeholders})",
                     [[r.get(c) for c in COLUMN_NAMES] for r in records])
    conn.executemany(
        f"INSERT INTO buildings_fts (id, {', '.join(FTS_FIELDS)}) VALUES "
        f"(?, {', '.join('?' for _ in FTS_FIELDS)})",
        [[r["id"]] + [r.get(f) or "" for f in FTS_FIELDS] for r in records])
    conn.commit()
    conn.close()


def set_people_text(conn, names_by_id):
    """Make buildings findable by the names of people linked to them ({building id: text})."""
    conn.executemany("UPDATE buildings_fts SET people_text = ? WHERE id = ?",
                     [(text, bid) for bid, text in names_by_id.items()])
    conn.commit()


def _ensure_fts_columns(conn):
    """Older databases lack newer FTS columns; FTS5 cannot add one, so rebuild the index."""
    have = [r[1] for r in conn.execute("PRAGMA table_info(buildings_fts)")]
    missing = [f for f in FTS_FIELDS if f not in have]
    if not missing:
        return
    keep = [f for f in FTS_FIELDS if f in have]
    rows = conn.execute(f"SELECT id, {', '.join(keep)} FROM buildings_fts").fetchall()
    conn.executescript(f"""DROP TABLE buildings_fts;
        CREATE VIRTUAL TABLE buildings_fts USING fts5(id UNINDEXED, {", ".join(FTS_FIELDS)});""")
    conn.executemany(f"INSERT INTO buildings_fts (id, {', '.join(keep)}) VALUES "
                     f"(?, {', '.join('?' for _ in keep)})", rows)
    conn.commit()


def set_other_names(conn, names_by_id):
    """Make buildings findable by their names in other languages ({building id: text})."""
    _ensure_fts_columns(conn)
    conn.execute("UPDATE buildings_fts SET other_names = '' WHERE other_names != ''")
    conn.executemany("UPDATE buildings_fts SET other_names = ? WHERE id = ?",
                     [(text, bid) for bid, text in names_by_id.items()])
    conn.commit()


def _fts_query(text):
    """Turn free text into a safe FTS5 prefix query."""
    words = ["".join(ch for ch in w if ch.isalnum()) for w in text.split()]
    return " ".join(f'"{w}"*' for w in words if w)


def build_where(filters):
    """filters: q, facet lists, year_min/max, has_image, curated, buildings_only, oldest_only,
    bbox=(south, west, north, east), near=(lat, lon, radius_km or None), ids=[...]."""
    where, args = [], []
    q = _fts_query(filters.get("q") or "")
    if q:
        where.append("id IN (SELECT id FROM buildings_fts WHERE buildings_fts MATCH ?)")
        args.append(q)
    for col in FACETS:
        vals = filters.get(col) or []
        if vals:
            where.append(f"COALESCE({col}, 'Unknown') IN ({', '.join('?' for _ in vals)})")
            args.extend(vals)
    if filters.get("year_min") is not None:
        where.append("year_start >= ?")
        args.append(filters["year_min"])
    if filters.get("year_max") is not None:
        where.append("year_start <= ?")
        args.append(filters["year_max"])
    for flag, sql in (("has_image", "image_thumb IS NOT NULL"), ("curated", "curated = 1"),
                      ("buildings_only", "is_building = 1"),
                      ("oldest_only", "oldest_of_type IS NOT NULL"), ("edited", "edited = 1"),
                      ("landmarks_only", "landmark IS NOT NULL"), ("early_only", "year_start < 1500")):
        if filters.get(flag):
            where.append(sql)
    if filters.get("bbox"):
        s, w, n, e = filters["bbox"]
        where.append("lat BETWEEN ? AND ? AND lon BETWEEN ? AND ?")
        args.extend([s, n, w, e])
    near = filters.get("near")
    if near and near[2]:
        where.append("DIST(lat, lon, ?, ?) <= ?")
        args.extend([near[0], near[1], near[2]])
    story = filters.get("story")
    if story:                               # legends, ghosts … (table stories, bidb.stories)
        where.append("id IN (SELECT entity_id FROM stories" + ("" if story == "any" else " WHERE kind = ?") + ")")
        args.extend([] if story == "any" else [story])
    if filters.get("ids"):
        ids = filters["ids"]
        where.append(f"id IN ({', '.join('?' for _ in ids)})")
        args.extend(ids)
    return (" WHERE " + " AND ".join(where)) if where else "", args


def _dist_select(filters):
    near = filters.get("near")
    if near:
        return "DIST(lat, lon, ?, ?) AS dist", [near[0], near[1]]
    return "NULL AS dist", []


LIST_FIELDS = ["id", "name", "category", "category_group", "period", "year_start", "date_text",
               "date_confidence", "oldest_of_type", "landmark", "nation",
               "county", "locality", "heritage_grade", "status", "image_thumb", "lat", "lon",
               "curated"]


def search(conn, filters, sort="oldest", limit=50, offset=0):
    where, args = build_where(filters)
    if sort == "distance" and not filters.get("near"):
        sort = "oldest"
    order = SORTS.get(sort, SORTS["oldest"])
    dsel, dargs = _dist_select(filters)
    rank, rargs = name_rank(filters.get("q"), sort)
    total = conn.execute(f"SELECT COUNT(*) FROM buildings{where}", args).fetchone()[0]
    rows = conn.execute(
        f"SELECT {', '.join(LIST_FIELDS)}, {dsel} FROM buildings{where} "
        f"ORDER BY {rank}{order}, name LIMIT ? OFFSET ?", dargs + args + rargs + [limit, offset]).fetchall()
    return total, [dict(r) for r in rows]


def map_points(conn, filters):
    where, args = build_where(filters)
    extra = " AND " if where else " WHERE "
    rows = conn.execute(
        f"SELECT id, name, lat, lon, category, category_group, period, date_text, year_start"
        f" FROM buildings{where}"
        f"{extra}lat IS NOT NULL", args).fetchall()
    return [dict(r) for r in rows]


def facet_counts(conn, filters):
    """Counts per facet value, each computed with that facet's own filter removed."""
    out = {}
    for col in FACETS:
        f = dict(filters)
        f[col] = []
        where, args = build_where(f)
        rows = conn.execute(
            f"SELECT COALESCE({col}, 'Unknown') AS v, COUNT(*) AS n FROM buildings{where} "
            f"GROUP BY v ORDER BY n DESC", args).fetchall()
        out[col] = [[r["v"], r["n"]] for r in rows]
    return out


def get_building(conn, bid):
    row = conn.execute("SELECT * FROM buildings WHERE id = ?", (bid,)).fetchone()
    return dict(row) if row else None


def stats(conn):
    c = conn.execute
    return {
        "total": c("SELECT COUNT(*) FROM buildings").fetchone()[0],
        "with_images": c("SELECT COUNT(*) FROM buildings WHERE image_thumb IS NOT NULL").fetchone()[0],
        "oldest": dict(c("SELECT id, name, date_text FROM buildings WHERE year_start IS NOT NULL "
                         "ORDER BY year_start LIMIT 1").fetchone() or {}),
        "by_period": [list(r) for r in c("SELECT period, COUNT(*) FROM buildings GROUP BY period")],
    }


def all_rows(conn, filters, sort="oldest"):
    where, args = build_where(filters)
    order = SORTS.get(sort if sort != "distance" else "oldest", SORTS["oldest"])
    return [dict(r) for r in conn.execute(
        f"SELECT * FROM buildings{where} ORDER BY {order}, name", args)]
