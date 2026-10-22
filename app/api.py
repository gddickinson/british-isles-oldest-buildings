"""Read-only data API (JSON) and CSV export."""
import json

from flask import Blueprint, Response, abort, jsonify, request

from bidb import db, queries
from bidb.categories import CATEGORY_ORDER, GROUP_ORDER
from bidb.classify import PERIOD_ORDER
from bidb.config import DATA_DIR
from bidb.history_geo import slug

from .common import arg_num, conn, filters_from_request

bp = Blueprint("api", __name__)
FACET_ORDER = {"period": PERIOD_ORDER + ["Unknown"], "category": CATEGORY_ORDER,
               "category_group": GROUP_ORDER}


@bp.route("/api/search")
def search():
    total, rows = db.search(conn(), filters_from_request(), request.args.get("sort", "oldest"),
                            min(arg_num("limit") or 48, 500), arg_num("offset") or 0)
    return jsonify(total=total, rows=rows)


@bp.route("/api/facets")
def facets():
    counts = db.facet_counts(conn(), filters_from_request())
    for col, seq in FACET_ORDER.items():
        counts[col].sort(key=lambda kv: seq.index(kv[0]) if kv[0] in seq else 99)
    return jsonify(counts)


@bp.route("/api/map")
def map_points():
    return jsonify(db.map_points(conn(), filters_from_request()))


@bp.route("/api/building/<path:bid>")
def building(bid):
    b = db.get_building(conn(), bid)
    if not b:
        abort(404)
    return jsonify(b)


@bp.route("/api/buildings")
def buildings_by_ids():
    """Full records for a list of ids (favourites, compare)."""
    ids = [i for i in request.args.get("ids", "").split(",") if i][:50]
    found = {b["id"]: b for b in (db.get_building(conn(), i) for i in ids) if b}
    return jsonify([found[i] for i in ids if i in found])


@bp.route("/api/nearby/<path:bid>")
def nearby(bid):
    return jsonify(queries.nearby(conn(), bid, limit=arg_num("limit") or 10,
                                  max_km=arg_num("km", float) or 15))


@bp.route("/api/timeline")
def timeline():
    return jsonify(queries.timeline(conn(), filters_from_request(), arg_num("bucket") or 100))


@bp.route("/api/stats")
def stats():
    return jsonify(queries.dashboard(conn(), filters_from_request()))


@bp.route("/api/gaps")
def gaps():
    return jsonify(queries.gaps(conn()))


@bp.route("/api/oldest")
def oldest():
    return jsonify(queries.oldest_by_category(conn(), per=arg_num("per") or 6))


@bp.route("/api/on_this_day")
def on_this_day():
    """?month=&day= -> events, battles, openings, births and deaths on that day (bidb.on_this_day)."""
    from bidb.on_this_day import for_day
    return jsonify(for_day(conn(), int(request.args.get("month", 1)), int(request.args.get("day", 1))))


@bp.route("/api/quiz")
def quiz():
    """Random buildings with a photo and a well-supported date, for "Guess the period"."""
    n = min(int(request.args.get("n", 10)), 30)
    rows = conn().execute("""SELECT id, name, image_thumb, year_start, date_text, period, category, locality, nation
        FROM buildings WHERE image_thumb IS NOT NULL AND year_start IS NOT NULL AND period != 'Unknown'
        AND date_check IN ('Corroborated', 'Referenced', 'Reviewed') ORDER BY random() LIMIT ?""", (n,)).fetchall()
    return jsonify([dict(r) for r in rows])


@bp.route("/api/history")
def history():
    return jsonify(history_with_places())


def history_with_places():
    """The history file with each event's map location (from data/history_geo.json)."""
    p = DATA_DIR / "curated" / "history.json"
    if not p.exists():
        abort(404)
    hist = json.loads(p.read_text())
    geo_path = DATA_DIR / "history_geo.json"
    geo = json.loads(geo_path.read_text()) if geo_path.exists() else {}
    for e in hist["events"]:
        g = geo.get(e["title"])
        if g:
            e.update(place=g["place"], lat=g["lat"], lon=g["lon"], place_id="ev-" + slug(e["title"]))
    return hist


@bp.route("/api/footprints")
def footprints():
    """Building outlines inside bbox=south,west,north,east (for zoomed-in maps)."""
    try:
        s_, w, n, e = [float(x) for x in request.args.get("bbox", "").split(",")][:4]
    except ValueError:
        abort(400)
    rows = conn().execute(
        "SELECT id, name, category_group, footprint FROM buildings WHERE footprint IS NOT NULL "
        "AND lat BETWEEN ? AND ? AND lon BETWEEN ? AND ? LIMIT 800", (s_, n, w, e)).fetchall()
    return jsonify([dict(r) for r in rows])


@bp.route("/api/evidence")
def evidence():
    """Researched claims with their sources and check results, by record (data/curated/evidence.json)."""
    from bidb import evidence as ev
    return jsonify(ev.export())


@bp.route("/api/verification")
def verification():
    """Checks of the researched files against their cited sources (bidb.verify_research)."""
    p = DATA_DIR / "verification.json"
    return Response(p.read_text() if p.exists() else "{}", mimetype="application/json")


@bp.route("/api/build_info")
def build_info_api():
    out = {}
    for name in ("build_info.json", "build_diff.json"):
        p = DATA_DIR / name
        if p.exists():
            out[name.split(".")[0]] = json.loads(p.read_text())
    return jsonify(out)
