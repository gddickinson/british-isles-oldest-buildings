"""Street detail saved for offline use (app/street_tiles.py): POST /api/street_tiles {name, bbox},
GET /api/street_tiles (areas + progress), DELETE /api/street_tiles, GET /tiles/<z>/<x>/<y>.mvt;
GET /historic_tiles/<layer>/<z>/<x>/<y>.webp: bundled historic map tiles (app.historic_build), the fallback
when a historic map's own server does not respond."""
from flask import Blueprint, Response, jsonify, request

from . import street_tiles

bp = Blueprint("street", __name__)


@bp.route("/api/street_tiles", methods=["GET", "POST", "DELETE"])
def street_tiles_api():
    if request.method == "POST":
        body = request.get_json(force=True) or {}
        bbox = [float(v) for v in body.get("bbox", [])][:4]
        if len(bbox) != 4:
            return jsonify({"error": "bbox [south, west, north, east] needed"}), 400
        return jsonify(street_tiles.save_area(body.get("name") or "Saved area", bbox))
    if request.method == "DELETE":
        street_tiles.clear()
    return jsonify({"areas": street_tiles.areas(), "job": street_tiles.JOB, "attribution": street_tiles.ATTRIBUTION,
                    "max_zoom": street_tiles.MAX_ZOOM})


@bp.route("/tiles/<int:z>/<int:x>/<int:y>.mvt")
def tile(z, x, y):
    got = street_tiles.tile(z, x, y)
    if not got:
        return Response(status=204)
    data, gz = got
    headers = {"Cache-Control": "public, max-age=604800"}
    if gz:
        headers["Content-Encoding"] = "gzip"
    return Response(data, mimetype="application/vnd.mapbox-vector-tile", headers=headers)


@bp.route("/historic_tiles/<layer>/<int:z>/<int:x>/<int:y>.webp")
def historic_tile(layer, z, x, y):
    from flask import abort, send_from_directory
    from bidb.config import cache_dir
    folder = cache_dir() / "historic_tiles" / layer / str(z) / str(x)
    if "/" in layer or ".." in layer or not (folder / f"{y}.webp").exists():
        abort(404)
    resp = send_from_directory(folder, f"{y}.webp", mimetype="image/webp")
    resp.headers["Cache-Control"] = "public, max-age=604800"
    return resp
