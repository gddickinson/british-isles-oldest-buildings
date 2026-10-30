"""Festivals and seasons (page /festivals): `/api/festivals` (every festival for the cards) and `/api/festival/<id>`
(one festival: researched facts and places with their quote checks, and what the catalogue holds for it), from
bidb.festival_finds."""
from flask import Blueprint, abort, jsonify

from bidb import festival_finds

from .common import conn

bp = Blueprint("festivals", __name__)


@bp.route("/api/festivals")
def festivals():
    return jsonify(festival_finds.index(conn()))


@bp.route("/api/festival/<fid>")
def festival(fid):
    page = festival_finds.page(conn(), fid)
    if page is None:
        abort(404)
    return jsonify(page)
