"""Data exports for the current filters: buildings, places and people as CSV / JSON / GeoJSON / KML.

    /export/buildings.<fmt>?<catalogue filters>     fmt: csv json geojson kml
    /export/places.<fmt>?<places filters>           fmt: csv json geojson kml
    /export/people.<fmt>?q=&role=                   fmt: csv json
    /export/pronunciations.<fmt>?q=&variety=&kind=   fmt: csv json
    /export.csv                                     (older link; same as /export/buildings.csv)

The hosted copy builds the same files in the browser (static/ui_export.js).
"""
import csv
import io
import json
from xml.sax.saxutils import escape

from flask import Blueprint, Response, abort, request

from bidb import db, places_db, pron_db

from .common import conn, filters_from_request
from .places_api import place_filters

bp = Blueprint("export_api", __name__)
MIME = {"csv": "text/csv", "json": "application/json", "geojson": "application/geo+json",
        "kml": "application/vnd.google-earth.kml+xml"}
# compact column sets for the map formats (the CSV/JSON keep every column)
GEO_FIELDS = {"buildings": ["id", "name", "category", "date_text", "year_start", "period", "nation",
                            "county", "locality", "heritage_grade", "status", "wikidata_id"],
              "places": ["id", "name", "kind_label", "kind_group", "type", "date_text", "year_start",
                         "period", "nation", "locality", "source", "url"]}


def _download(body, fmt, stem):
    return Response(body, mimetype=MIME[fmt], headers={
        "Content-Disposition": f"attachment; filename=british_isles_{stem}.{fmt}"})


def to_csv(rows, fields=None):
    fields = fields or (list(rows[0]) if rows else [])
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=fields, extrasaction="ignore")
    w.writeheader()
    w.writerows(rows)
    return buf.getvalue()


def to_geojson(rows, fields):
    feats = [{"type": "Feature", "geometry": {"type": "Point", "coordinates": [r["lon"], r["lat"]]},
              "properties": {k: r.get(k) for k in fields}}
             for r in rows if r.get("lat") is not None and r.get("lon") is not None]
    return json.dumps({"type": "FeatureCollection", "features": feats}, ensure_ascii=False)


def to_kml(rows, fields, title):
    marks = []
    for r in rows:
        if r.get("lat") is None:
            continue
        desc = "<br>".join(f"{escape(k)}: {escape(str(r[k]))}" for k in fields
                           if r.get(k) not in (None, "") and k not in ("id", "name"))
        marks.append(f"<Placemark><name>{escape(r.get('name') or r['id'])}</name>"
                     f"<description><![CDATA[{desc}]]></description>"
                     f"<Point><coordinates>{r['lon']},{r['lat']}</coordinates></Point></Placemark>")
    return ('<?xml version="1.0" encoding="UTF-8"?><kml xmlns="http://www.opengis.net/kml/2.2">'
            f"<Document><name>{escape(title)}</name>{''.join(marks)}</Document></kml>")


def _rows(kind):
    if kind == "buildings":
        return db.all_rows(conn(), filters_from_request(), request.args.get("sort", "oldest"))
    if kind == "places":
        if not places_db.has_tables(conn()):
            abort(503, "Places not built yet")
        w, args = places_db.where(place_filters())
        return [dict(r) for r in conn().execute(f"SELECT * FROM places{w} ORDER BY year_start IS NULL, "
                                                "year_start, name", args)]
    if kind == "pronunciations":
        a = request.args
        rows = pron_db.search(conn(), a.get("q", ""), a.get("variety", ""), a.get("kind", ""), 1000000, 0)["rows"]
        for r in rows:
            r["audio_file_page"] = r.pop("audio_urls", {}).get("page", "")
        return rows
    total, rows = places_db.people_search(conn(), request.args.get("q", ""), request.args.get("role", ""),
                                          request.args.get("sort", "known"), 100000, 0)
    return rows


@bp.route("/export/<kind>.<fmt>")
def export(kind, fmt):
    if kind not in ("buildings", "places", "people", "pronunciations") or fmt not in MIME or (
            kind in ("people", "pronunciations") and fmt in ("geojson", "kml")):
        abort(404)
    rows = _rows(kind)
    if fmt == "csv":
        fields = db.COLUMN_NAMES if kind == "buildings" else None
        return _download(to_csv(rows, fields), fmt, kind)
    if fmt == "json":
        return _download(json.dumps(rows, ensure_ascii=False), fmt, kind)
    if fmt == "geojson":
        return _download(to_geojson(rows, GEO_FIELDS[kind]), fmt, kind)
    return _download(to_kml(rows, GEO_FIELDS[kind], f"British Isles {kind}"), fmt, kind)


@bp.route("/export.csv")
def export_csv():
    return export("buildings", "csv")
