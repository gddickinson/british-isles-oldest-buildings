"""Building types (BT2b): `/api/types` (every isles type: counts, period, earliest surviving example),
`/api/type/<id>` (one type: curated entry, links, examples oldest first, by nation and century, map points) and
`/api/types_of/<record or place id>` (the types of one record, primary first), from bidb.type_stats."""
from flask import Blueprint, abort, jsonify

from bidb import building_types, type_stats

from .common import conn

bp = Blueprint("types", __name__)
_DATA = {}


def _data():
    """The curated lineage files, read once per server."""
    if "data" not in _DATA:
        _DATA["data"] = building_types.load()
    return _DATA["data"]


@bp.route("/api/types")
def types():
    return jsonify(type_stats.summary(conn(), _data()))


@bp.route("/api/type/<tid>")
def one_type(tid):
    d = type_stats.detail(conn(), tid, _data())
    if d is None:
        abort(404)
    d["links"] = [link for link in _data()["links"] if tid in (link["from"], link["to"])]
    return jsonify(d)


@bp.route("/api/types_of/<rid>")
def types_of(rid):
    return jsonify(type_stats.for_entity(conn(), rid, _data()))
