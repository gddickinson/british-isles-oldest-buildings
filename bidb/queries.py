"""Analytical read queries for the GUI: timeline, dashboard stats, nearby, gaps, oldest by type."""
from .categories import CATEGORY_ORDER, GROUP_ORDER, group_for
from .db import build_where


def timeline(conn, filters, bucket=100):
    """Counts per time bucket (default century) split by category group.

    Returns {"bucket": n, "groups": [...], "rows": [{"start": y, "counts": {group: n}}]}.
    """
    where, args = build_where(filters)
    extra = " AND " if where else " WHERE "
    rows = conn.execute(
        f"SELECT CAST((year_start - (CASE WHEN year_start < 0 THEN {bucket - 1} ELSE 0 END))"
        f" / {bucket} AS INTEGER) * {bucket} AS b, COALESCE(category_group, 'Other') AS g,"
        f" COUNT(*) AS n FROM buildings{where}{extra}year_start IS NOT NULL GROUP BY b, g",
        args).fetchall()
    buckets = {}
    for r in rows:
        buckets.setdefault(r["b"], {})[r["g"]] = r["n"]
    present = {g for c in buckets.values() for g in c}
    return {"bucket": bucket, "groups": [g for g in GROUP_ORDER if g in present],
            "rows": [{"start": b, "counts": buckets[b]} for b in sorted(buckets)]}


def _counts(conn, col, where, args, limit=None):
    sql = (f"SELECT COALESCE({col}, 'Unknown') AS v, COUNT(*) AS n FROM buildings{where} "
           f"GROUP BY v ORDER BY n DESC")
    if limit:
        sql += f" LIMIT {int(limit)}"
    return [[r["v"], r["n"]] for r in conn.execute(sql, args)]


def dashboard(conn, filters):
    """Everything the statistics page needs, for the current filter."""
    where, args = build_where(filters)
    total = conn.execute(f"SELECT COUNT(*) FROM buildings{where}", args).fetchone()[0]
    fields = {"image": "image_thumb IS NOT NULL", "coordinates": "lat IS NOT NULL",
              "recorded date": "date_confidence = 'Recorded'",
              "any date": "year_start IS NOT NULL", "heritage designation": "designations <> ''",
              "Wikipedia article": "wikipedia_title IS NOT NULL"}
    completeness = []
    for label, cond in fields.items():
        joiner = " AND " if where else " WHERE "
        n = conn.execute(f"SELECT COUNT(*) FROM buildings{where}{joiner}{cond}", args).fetchone()[0]
        completeness.append([label, n])
    category = _counts(conn, "category", where, args)
    category.sort(key=lambda kv: CATEGORY_ORDER.index(kv[0]) if kv[0] in CATEGORY_ORDER else 99)
    joiner = " AND " if where else " WHERE "
    oldest_county = [dict(r) for r in conn.execute(
        f"SELECT county, nation, id, name, date_text, MIN(year_start) AS year FROM buildings{where}"
        f"{joiner}year_start IS NOT NULL AND county IS NOT NULL GROUP BY county, nation "
        f"ORDER BY nation, county", args)]
    return {"total": total, "nation": _counts(conn, "nation", where, args),
            "category": category, "period": _counts(conn, "period", where, args),
            "heritage_grade": _counts(conn, "heritage_grade", where, args),
            "status": _counts(conn, "status", where, args),
            "county": _counts(conn, "county", where, args, limit=25),
            "completeness": completeness, "oldest_by_county": oldest_county}


def nearby(conn, bid, limit=10, max_km=15):
    b = conn.execute("SELECT lat, lon FROM buildings WHERE id = ?", (bid,)).fetchone()
    if not b or b["lat"] is None:
        return []
    rows = conn.execute(
        "SELECT id, name, category, date_text, image_thumb, DIST(lat, lon, ?, ?) AS dist "
        "FROM buildings WHERE id <> ? AND lat BETWEEN ? AND ? AND lon BETWEEN ? AND ? "
        "ORDER BY dist LIMIT ?",
        (b["lat"], b["lon"], bid, b["lat"] - 0.3, b["lat"] + 0.3, b["lon"] - 0.5, b["lon"] + 0.5,
         limit)).fetchall()
    return [dict(r) for r in rows if r["dist"] is not None and r["dist"] <= max_km]


def gaps(conn, limit=200):
    """Records missing key data, with counts, for the data-quality page."""
    checks = {"no_image": "image_thumb IS NULL", "no_coordinates": "lat IS NULL",
              "no_date": "year_start IS NULL",
              "estimated_date": "date_confidence = 'Estimate (building type)'",
              "no_nation": "nation IS NULL", "no_designation": "designations = '' OR designations IS NULL",
              "date_conflict": "date_check = 'Conflict'"}
    out = {}
    for key, cond in checks.items():
        n = conn.execute(f"SELECT COUNT(*) FROM buildings WHERE {cond}").fetchone()[0]
        rows = conn.execute(
            f"SELECT id, name, nation, county, date_text, wikidata_id, date_check_note FROM buildings WHERE {cond} "
            f"ORDER BY year_start IS NULL, year_start LIMIT ?", (limit,)).fetchall()
        out[key] = {"count": n, "rows": [dict(r) for r in rows]}
    return out


def oldest_by_category(conn, per=6):
    """The oldest dated records in each category (including researched 'oldest of type')."""
    out = []
    for cat in CATEGORY_ORDER:
        rows = conn.execute(
            "SELECT id, name, date_text, year_start, nation, locality, image_thumb, "
            "oldest_of_type, type_claim, date_confidence FROM buildings "
            "WHERE category = ? AND year_start IS NOT NULL ORDER BY year_start LIMIT ?",
            (cat, per)).fetchall()
        n = conn.execute("SELECT COUNT(*) FROM buildings WHERE category = ?", (cat,)).fetchone()[0]
        if rows:
            out.append({"category": cat, "group": group_for(cat), "count": n,
                        "examples": [dict(r) for r in rows]})
    return out
