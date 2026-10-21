"""Stories (legends, ghosts, folklore, curious history): /api/stories/<record id>, /api/stories
(search: q, kind, nation) and /api/stories/counts."""
from flask import Blueprint, jsonify, request

from bidb import stories_db
from bidb.stories_parse import KINDS

from .common import conn

bp = Blueprint("stories", __name__)


@bp.route("/api/stories/<path:rid>")
def for_record(rid):
    return jsonify(stories_db.for_record(conn(), rid))


@bp.route("/api/timeline/<path:rid>")
def timeline(rid):
    from bidb.timeline import for_record as events
    return jsonify(events(conn(), rid))


@bp.route("/api/visiting/<path:rid>")
def visiting(rid):
    from bidb.visiting import for_record as visit
    return jsonify(visit(conn(), rid))


@bp.route("/api/stories")
def search():
    a = request.args
    return jsonify(stories_db.search(conn(), a.get("q", ""), a.get("kind", ""), a.get("nation", ""),
                                     min(int(a.get("limit", 60)), 500), int(a.get("offset", 0))))


@bp.route("/api/stories_counts")
def counts():
    got = stories_db.counts(conn())
    return jsonify([{"kind": k, "label": label, "count": got.get(k, 0)} for k, label in KINDS.items()])
