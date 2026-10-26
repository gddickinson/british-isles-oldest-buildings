"""Trade stories (roadmap C8): `/api/trades` (the list), `/api/trade/<id>` (one story: events, places, buildings,
people, graphs, innovations, notes) and `/api/trade_here/<record id>` (C9: "Trade and industry here" in detail
views), from bidb.trade_stories."""
from flask import Blueprint, abort, jsonify

from bidb import trade_stories

from .common import conn

bp = Blueprint("trades", __name__)


@bp.route("/api/trades")
def trades():
    return jsonify(trade_stories.index())


_HERE = {}


@bp.route("/api/trade_here/<rid>")
def trade_here(rid):
    """The trade stories a building or place belongs to and the innovations made there (computed once per server)."""
    if "map" not in _HERE:
        _HERE["map"] = trade_stories.here(conn())
    return jsonify(_HERE["map"].get(rid, {"trades": [], "made": []}))


@bp.route("/api/trade/<sid>")
def trade(sid):
    s = trade_stories.story(conn(), sid)
    if s is None:
        abort(404)
    return jsonify(s)
