"""Pronunciations: /api/pron/<record id> (the record's own and its town's), /api/pronunciations
(the guide: search, variety and kind filters) and /api/pronunciations/varieties."""
from flask import Blueprint, jsonify, request

from bidb import pron_db

from .common import conn

bp = Blueprint("pron", __name__)


@bp.route("/api/pron/<path:rid>")
def for_record(rid):
    return jsonify(pron_db.for_record(conn(), rid))


@bp.route("/api/pronunciations")
def guide():
    a = request.args
    res = pron_db.search(conn(), a.get("q", ""), a.get("variety", ""), a.get("kind", ""),
                         min(int(a.get("limit", 60)), 500), int(a.get("offset", 0)))
    return jsonify(res)


@bp.route("/api/pronunciations/varieties")
def varieties():
    return jsonify([{"variety": v, "count": n} for v, n in pron_db.varieties(conn())])


@bp.route("/api/pronunciations/coverage")
def coverage():
    c = conn()
    return jsonify({**pron_db.coverage(c), "missing": pron_db.missing_tricky(c)})
