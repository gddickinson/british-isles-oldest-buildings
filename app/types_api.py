"""Building types (BT2b, BT4a) and materials (BT3c1): `/api/types` (every isles type: counts, period, earliest
surviving example), `/api/type/<id>` (one type, bidb.type_stats), `/api/types_of/<record or place id>` (the types of
one record, primary first); for the page /types (bidb.type_pages): `/api/type_tree`, `/api/type_page/<id>`,
`/api/materials`, `/api/material/<id>`, `/api/types_here/<record or place id>` (types and materials, detail views)."""
from flask import Blueprint, abort, jsonify

from bidb.config import db_path
from bidb import building_materials, building_types, type_pages, type_stats

from .common import conn

bp = Blueprint("types", __name__)
_DATA = {}


def _data():
    """The curated lineage files, read once per server."""
    if "data" not in _DATA:
        _DATA["data"] = building_types.load()
    return _DATA["data"]


def _mdata():
    if "mdata" not in _DATA:
        _DATA["mdata"] = building_materials.load()
    return _DATA["mdata"]


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


@bp.route("/api/type_tree")
def type_tree():
    key = db_path().stat().st_mtime         # 2 s of counting, kept until the database changes
    if _DATA.get("tree_key") != key:
        _DATA["tree"], _DATA["tree_key"] = type_pages.tree(conn(), _data()), key
    return jsonify(_DATA["tree"])


@bp.route("/api/type_page/<tid>")
def type_page(tid):
    d = type_pages.type_page(conn(), tid, _data(), _mdata())
    if d is None:
        abort(404)
    return jsonify(d)


@bp.route("/api/materials")
def materials():
    return jsonify(type_pages.materials(conn(), _mdata()))


@bp.route("/api/material/<mid>")
def material(mid):
    d = type_pages.material_page(conn(), mid, _data(), _mdata())
    if d is None:
        abort(404)
    return jsonify(d)


@bp.route("/api/types_here/<rid>")
def types_here(rid):
    return jsonify(type_pages.here(conn(), rid, _data(), _mdata()))
