"""Tours: /api/tours (ready-made; mode, theme, nation, q), /api/tour/<id>, /api/route (a route
along real paths/roads for the tour builder, via bidb.tour_route) and /api/tour_candidates
(scored stops near a point, for "suggest a tour" and "add stops along the way")."""
import json

from flask import Blueprint, abort, jsonify, request

from bidb import tour_plan, tour_route
from bidb.tours import THEMES, candidates

from .common import conn

bp = Blueprint("tours", __name__)
_CANDS = {}                  # candidate stops, computed once per database file


def _has_tours(c):
    return bool(c.execute("SELECT 1 FROM sqlite_master WHERE name = 'tours'").fetchone())


def _tour(row):
    t = dict(row)
    t["stops"] = json.loads(t["stops"] or "[]")
    t["elevation"] = json.loads(t["elevation"]) if t.get("elevation") else None
    t["stages"] = json.loads(t["stages"]) if t.get("stages") else None
    return t


@bp.route("/api/tours")
def tours():
    c, a = conn(), request.args
    if not _has_tours(c):
        return jsonify([])
    rows = [_tour(r) for r in c.execute("SELECT * FROM tours ORDER BY mode, theme, title")]
    for key in ("mode", "theme", "nation"):
        if a.get(key):
            rows = [t for t in rows if t[key] == a[key]]
    for w in a.get("q", "").lower().split():
        rows = [t for t in rows if w in (t["title"] + " " + t["summary"] + " " + t["area"]).lower()]
    for t in rows:
        t.pop("geometry", None)
    return jsonify(rows)


@bp.route("/api/tour/<tid>")
def tour(tid):
    c = conn()
    row = c.execute("SELECT * FROM tours WHERE id = ?", (tid,)).fetchone() if _has_tours(c) else None
    if not row:
        abort(404)
    return jsonify(_tour(row))


@bp.route("/api/route")
def route():
    """?mode=walk|cycle|drive&points=lat,lon;lat,lon;… -> route or {"error"}."""
    mode = request.args.get("mode", "walk")
    try:
        pts = [tuple(float(x) for x in p.split(",")) for p in request.args.get("points", "").split(";") if p]
    except ValueError:
        abort(400)
    if mode not in tour_route.PROFILES or not 2 <= len(pts) <= 25:
        abort(400)
    got = tour_route.route(mode, pts)
    if got and mode != "drive":
        from bidb.tour_elevation import decode, profile
        got["elevation"] = profile(decode(got["geometry"]), got["distance_km"])
    return jsonify(got or {"error": "No route found (or the routing service is unreachable)"})


@bp.route("/api/tour_candidates")
def tour_candidates():
    """?lat&lon&km[&theme] -> scored records within km, best first (≤ 300)."""
    c = conn()
    key = c.execute("PRAGMA database_list").fetchone()[2]
    if key not in _CANDS:
        _CANDS.clear()
        _CANDS[key] = candidates(c)
    try:
        lat, lon = float(request.args["lat"]), float(request.args["lon"])
        radius = min(float(request.args.get("km", 10)), 80)
    except (KeyError, ValueError):
        abort(400)
    test = THEMES.get(request.args.get("theme") or "highlights", THEMES["highlights"])["test"]
    keep = ["id", "kind", "name", "lat", "lon", "date_text", "category", "locality", "story_kinds", "score",
            "image_thumb"]
    near = [r for r in _CANDS[key] if abs(r["lat"] - lat) < radius / 100 and test(r)
            and tour_plan.km((lat, lon), (r["lat"], r["lon"])) <= radius]
    near.sort(key=lambda r: -r["score"])
    return jsonify([{k: r.get(k) for k in keep} for r in near[:300]])
