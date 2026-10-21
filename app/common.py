"""Shared request helpers: per-request DB connection and filter parsing."""
import json

from flask import abort, g, request

from bidb import db
from bidb.config import DATA_DIR, db_path


def conn():
    if "conn" not in g:
        path = db_path()          # resolved per request: the Settings page can move the database
        if not path.exists():
            abort(503, f"Database not found at {path} - run: python -m bidb.build, or check the "
                       "data location on the Settings page (is the drive plugged in?)")
        g.conn = db.connect(path, readonly=True)
    return g.conn


def close_conn(_exc=None):
    c = g.pop("conn", None)
    if c is not None:
        c.close()


def arg_num(name, cast=int):
    v = request.args.get(name, "").strip()
    try:
        return cast(v)
    except ValueError:
        return None


def filters_from_request():
    f = {"q": request.args.get("q", ""), "story": request.args.get("story", ""),
         "year_min": arg_num("year_min"), "year_max": arg_num("year_max")}
    for flag in ("has_image", "curated", "buildings_only", "oldest_only", "edited", "landmarks_only",
                 "early_only"):
        f[flag] = request.args.get(flag) == "1"
    for col in db.FACETS:
        f[col] = [v for v in request.args.getlist(col) if v]
    bbox = request.args.get("bbox", "")
    if bbox:
        try:
            f["bbox"] = [float(x) for x in bbox.split(",")][:4]
        except ValueError:
            pass
    lat, lon = arg_num("lat", float), arg_num("lon", float)
    if lat is not None and lon is not None:
        f["near"] = (lat, lon, arg_num("radius", float))
    ids = request.args.get("ids", "")
    if ids:
        f["ids"] = [i for i in ids.split(",") if i][:500]
    return f


def build_info():
    p = DATA_DIR / "build_info.json"
    return json.loads(p.read_text()) if p.exists() else {}
