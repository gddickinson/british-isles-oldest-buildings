"""Trade stories (roadmap C8): `/api/trades` (the list) and `/api/trade/<id>` (one story: events, places, buildings,
people, graphs, innovations, notes), from bidb.trade_stories."""
from flask import Blueprint, abort, jsonify

from bidb import trade_stories

from .common import conn

bp = Blueprint("trades", __name__)


@bp.route("/api/trades")
def trades():
    return jsonify(trade_stories.index())


@bp.route("/api/trade/<sid>")
def trade(sid):
    s = trade_stories.story(conn(), sid)
    if s is None:
        abort(404)
    return jsonify(s)
