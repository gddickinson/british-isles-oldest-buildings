"""3D views of stone circles built on request from their mapped stones (roadmap SH3h, bidb.model_circles):
`/api/circle_model/<id>` (the model's data) and `/api/circle_model_dtm/<id>` (its ground grid), and the page
`/model/circle/<id>` (model.html); English buildings from the Environment Agency's LiDAR surface (bidb.model_lidar):
`/api/lidar_model/<id>`, `/api/lidar_model_dtm/<id>`, `/model/lidar/<id>`. Local GUI only: the hosted copy has no server to build them."""
import json

from flask import Blueprint, Response, abort, render_template

from bidb import model_circles, model_lidar

bp = Blueprint("models_api", __name__)


def _built(eid):
    res = model_circles.build(eid)
    if res is None:
        abort(404)
    return res


@bp.route("/api/circle_model/<path:eid>")
def circle_model(eid):
    # Not jsonify: it sorts the keys, and the first camera is the opening view.
    return Response(json.dumps(_built(eid)[0], ensure_ascii=False), mimetype="application/json")


@bp.route("/api/circle_model_dtm/<path:eid>")
def circle_model_dtm(eid):
    return Response(_built(eid)[1], mimetype="application/octet-stream")


@bp.route("/model/circle/<path:eid>")
def circle_page(eid):
    info = model_circles.known().get(eid)
    if not info:
        abort(404)
    m = {"name": info["name"], "record": eid if info["source"] == "building" else None,
         "about": [f"Built from the {info['stones']} stones mapped on OpenStreetMap round {info['name']}: their "
                   "positions, with heights only where tagged. The first opening builds the ground and skyline, "
                   "which can take half a minute."], "labels_label": "Labels"}
    return render_template("model.html", page="models", m=m, mid=None,
                           src=f"/api/circle_model/{eid}", dtm=f"/api/circle_model_dtm/{eid}")


def _lidar(eid):
    res = model_lidar.build(eid)
    if res is None:
        abort(404)
    return res


@bp.route("/api/lidar_model/<path:eid>")
def lidar_model(eid):
    return Response(json.dumps(_lidar(eid)[0], ensure_ascii=False), mimetype="application/json")


@bp.route("/api/lidar_model_dtm/<path:eid>")
def lidar_model_dtm(eid):
    return Response(_lidar(eid)[1], mimetype="application/octet-stream")


@bp.route("/model/lidar/<path:eid>")
def lidar_page(eid):
    """Roadmap SH4d: any English record with a footprint, from the Environment Agency's LiDAR surface."""
    import sqlite3
    from bidb.config import db_path
    row = model_lidar.eligible(sqlite3.connect(db_path()), eid)
    if not row:
        abort(404)
    m = {"name": row[0], "record": eid, "labels_label": "Labels",
         "about": ["The building and its surroundings as the Environment Agency's survey aircraft saw them with its "
                   "laser, every metre: roofs, towers, walls and trees at their real heights, coloured by kind (the "
                   "building itself, other buildings, trees, ground). A shell seen from the air: no interiors, and "
                   "walls blur over a metre. The first opening fetches the survey and builds the skyline, which can "
                   "take half a minute."]}
    return render_template("model.html", page="models", m=m, mid=None,
                           src=f"/api/lidar_model/{eid}", dtm=f"/api/lidar_model_dtm/{eid}")
