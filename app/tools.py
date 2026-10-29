"""Interactive tools: place search, Commons image galleries, skylines, user corrections (jobs: app/jobs_api.py)."""
import re

from flask import Blueprint, abort, jsonify, request

from bidb import db, overrides, sky_horizon
from bidb.config import POSTCODES_API, WIKIDATA_API
from bidb.http import request_json

from .common import conn

bp = Blueprint("tools", __name__)
COMMONS_API = "https://commons.wikimedia.org/w/api.php"
NOMINATIM = "https://nominatim.openstreetmap.org/search"
POSTCODE_RE = re.compile(r"^[A-Z]{1,2}\d[A-Z\d]?\s*\d[A-Z]{2}$", re.I)


@bp.route("/api/geocode")
def geocode():
    """Place or postcode -> [{name, lat, lon}] (postcodes.io for UK postcodes, else Nominatim)."""
    q = request.args.get("q", "").strip()
    if not q:
        return jsonify([])
    if POSTCODE_RE.match(q):
        try:
            r = request_json(f"{POSTCODES_API}/postcodes/{q.replace(' ', '')}")["result"]
            return jsonify([{"name": r["postcode"], "lat": r["latitude"], "lon": r["longitude"]}])
        except Exception:
            pass
    try:
        res = request_json(NOMINATIM, params={"q": q, "format": "json", "limit": 5,
                                              "countrycodes": "gb,ie,im,je,gg"}, min_interval=1.0)
    except Exception:
        return jsonify([])
    return jsonify([{"name": r["display_name"], "lat": float(r["lat"]), "lon": float(r["lon"])}
                    for r in res])


@bp.route("/api/horizon")
def horizon():
    """The skyline round a point (SK7): altitudes in hundredths of a degree every half degree from north, distances in
    km; terrain tiles downloaded the first time (a few seconds), then cached."""
    try:
        lat, lon = round(float(request.args["lat"]), 4), round(float(request.args["lon"]), 4)
    except (KeyError, ValueError):
        abort(400)
    if not (49 <= lat <= 61.5 and -11 <= lon <= 2.5):
        abort(404)
    try:
        return jsonify(sky_horizon.compact(sky_horizon.cached_profile(lat, lon)))
    except Exception:
        abort(503)


@bp.route("/api/images/<path:bid>")
def images(bid):
    """Up to 24 images from the building's Wikimedia Commons category (P373)."""
    if not bid.startswith("Q"):
        return jsonify([])
    ent = request_json(WIKIDATA_API, params={"action": "wbgetentities", "ids": bid,
                                             "props": "claims", "format": "json"})
    claims = ent.get("entities", {}).get(bid, {}).get("claims", {}).get("P373", [])
    if not claims:
        return jsonify([])
    cat = claims[0]["mainsnak"].get("datavalue", {}).get("value")
    res = request_json(COMMONS_API, params={
        "action": "query", "generator": "categorymembers", "gcmtitle": f"Category:{cat}",
        "gcmtype": "file", "gcmlimit": 24, "prop": "imageinfo",
        "iiprop": "url|extmetadata", "iiurlwidth": 480, "format": "json", "formatversion": 2})
    out = []
    for p in res.get("query", {}).get("pages", []):
        info = (p.get("imageinfo") or [{}])[0]
        meta = info.get("extmetadata", {})
        if not info.get("thumburl") or not re.search(r"\.(jpe?g|png|gif|tiff?|webp)$", p["title"], re.I):
            continue
        out.append({"title": p["title"].replace("File:", ""), "thumb": info["thumburl"],
                    "page": info.get("descriptionurl"),
                    "artist": re.sub(r"<[^>]+>", "", meta.get("Artist", {}).get("value", ""))[:80],
                    "license": meta.get("LicenseShortName", {}).get("value", "")})
    return jsonify({"category": cat, "images": out})


@bp.route("/api/override/<path:bid>", methods=["POST", "DELETE"])
def override(bid):
    """Save (POST {fields, note}) or remove (DELETE) a user correction."""
    if not db.get_building(conn(), bid):
        abort(404)
    if request.method == "DELETE":
        overrides.remove(bid)
        w = db.connect()
        w.execute("UPDATE buildings SET edited = NULL, user_notes = NULL WHERE id = ?", (bid,))
        w.commit()
        w.close()
        return jsonify(ok=True, note="Removed; other original values return at the next rebuild.")
    body = request.get_json(force=True, silent=True) or {}
    try:
        clean = overrides.save_one(bid, body.get("fields", {}), body.get("note", ""))
    except (TypeError, ValueError) as exc:
        return jsonify(ok=False, error=str(exc)), 400
    from bidb.classify import period_for
    from bidb.categories import group_for
    w = db.connect()
    sets = {k: v for k, v in clean.items() if k != "notes"}
    if "notes" in clean:
        sets["user_notes"] = clean["notes"]
    if "year_start" in sets:
        sets["period"] = period_for(sets["year_start"])
        sets["date_confidence"] = "Corrected by user"
    if "category" in sets:
        sets["category_group"] = group_for(sets["category"])
    sets["edited"] = 1
    w.execute(f"UPDATE buildings SET {', '.join(f'{k} = ?' for k in sets)} WHERE id = ?",
              [*sets.values(), bid])
    w.commit()
    w.close()
    return jsonify(ok=True, saved=clean)
