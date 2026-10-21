"""JSON API for places of interest, people and the links between them."""
from flask import Blueprint, abort, jsonify, request

from bidb import places_db
from bidb.classify import PERIOD_ORDER
from bidb.place_kinds import PLACE_GROUPS

from .common import arg_num, conn

bp = Blueprint("places_api", __name__)


def _ready():
    if not places_db.has_tables(conn()):
        abort(503, "Places not built yet - run: python -m bidb.places_build")
    return conn()


def place_filters():
    f = {"q": request.args.get("q", ""), "year_min": arg_num("year_min"),
         "year_max": arg_num("year_max"), "has_image": request.args.get("has_image") == "1"}
    for col in places_db.PLACE_FACETS:
        f[col] = [v for v in request.args.getlist(col) if v]
    bbox = request.args.get("bbox", "")
    if bbox:
        try:
            f["bbox"] = [float(x) for x in bbox.split(",")][:4]
        except ValueError:
            pass
    return f


@bp.route("/api/places")
def places():
    total, rows = places_db.search(_ready(), place_filters(), request.args.get("sort", "oldest"),
                                   min(arg_num("limit") or 48, 500), arg_num("offset") or 0)
    return jsonify(total=total, rows=rows)


@bp.route("/api/places/facets")
def place_facets():
    counts = places_db.facets(_ready(), place_filters())
    order = {"kind_group": PLACE_GROUPS, "period": PERIOD_ORDER + ["Unknown"]}
    for col, seq in order.items():
        counts[col].sort(key=lambda kv: seq.index(kv[0]) if kv[0] in seq else 99)
    return jsonify(counts)


@bp.route("/api/places/map")
def place_map():
    return jsonify(places_db.map_points(_ready(), place_filters()))


@bp.route("/api/place/<path:pid>")
def place(pid):
    p = places_db.get(_ready(), pid)
    if not p:
        abort(404)
    if p.get("lat") is not None:
        p["nearby_places"] = places_db.near(conn(), p["lat"], p["lon"], km=5, limit=8, exclude=pid)
    return jsonify(p)


@bp.route("/api/places/near")
def places_near():
    lat, lon = arg_num("lat", float), arg_num("lon", float)
    if lat is None or lon is None:
        abort(400)
    return jsonify(places_db.near(_ready(), lat, lon, km=arg_num("km", float) or 5,
                                  limit=arg_num("limit") or 12, exclude=request.args.get("exclude")))


@bp.route("/api/related/<path:bid>")
def related(bid):
    """People, objects and nearby places for a building's detail view."""
    c = conn()
    if not places_db.has_tables(c):
        return jsonify(people=[], objects=[], places=[])
    row = c.execute("SELECT lat, lon FROM buildings WHERE id = ?", (bid,)).fetchone()
    near = places_db.near(c, row["lat"], row["lon"], km=5, limit=12) if row and row["lat"] is not None else []
    return jsonify(people=places_db.people_for(c, bid), objects=places_db.objects_in(c, bid),
                   places=[p for p in near if p["id"] != bid])


@bp.route("/api/people")
def people():
    total, rows = places_db.people_search(_ready(), request.args.get("q", "").strip(),
                                          request.args.get("role", ""), request.args.get("sort", "known"),
                                          min(arg_num("limit") or 48, 200), arg_num("offset") or 0)
    return jsonify(total=total, rows=rows)


@bp.route("/api/people/roles")
def roles():
    return jsonify(places_db.roles(_ready()))


@bp.route("/api/person/<pid>")
def person(pid):
    p = places_db.person(_ready(), pid)
    if not p:
        abort(404)
    return jsonify(p)
