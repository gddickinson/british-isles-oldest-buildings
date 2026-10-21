"""Index of georeferenced historic maps covering the British Isles, from the Allmaps bulk file
(files.allmaps.org/maps.geojson, CC0; ~200 MB worldwide, downloaded once and filtered).

Writes app/static/data/historic/allmaps.json: one row per map with its outline (simplified),
covered area, holding library and links, so a detail view can list "historic maps of this
place" (most detailed first). Run: python -m app.historic_allmaps
"""
import json
import math

import requests

from bidb.config import CACHE_DIR, USER_AGENT

from .geo_simplify import simplify
from .historic_build import OUT

BULK = "https://files.allmaps.org/maps.geojson"
CACHE = CACHE_DIR / "allmaps"
BOX = (-11.0, 49.0, 2.2, 61.2)        # west, south, east, north
MAX_KM2 = 400_000                      # larger outlines are maps of the whole of Britain: not "of this place"


def _ring(geom):
    return geom["coordinates"][0] if geom["type"] == "Polygon" else geom["coordinates"][0][0]


def british_isles_maps():
    """Features of the bulk file whose outline centre lies in the British Isles box (cached)."""
    path = CACHE / "bi.json"
    if path.exists():
        return json.loads(path.read_text())
    CACHE.mkdir(parents=True, exist_ok=True)
    tmp = CACHE / "maps.geojson"
    with requests.get(BULK, headers={"User-Agent": USER_AGENT}, stream=True, timeout=600) as r:
        r.raise_for_status()
        with open(tmp, "wb") as fh:
            for chunk in r.iter_content(1 << 20):
                fh.write(chunk)
    keep = []
    for f in json.loads(tmp.read_text())["features"]:
        if not f.get("geometry"):
            continue
        ring = _ring(f["geometry"])
        cx = (min(p[0] for p in ring) + max(p[0] for p in ring)) / 2
        cy = (min(p[1] for p in ring) + max(p[1] for p in ring)) / 2
        if BOX[0] < cx < BOX[2] and BOX[1] < cy < BOX[3]:
            keep.append(f)
    path.write_text(json.dumps(keep))
    tmp.unlink()                       # 200 MB: keep only the British Isles subset
    return keep


def _provider(res):
    prov = (res.get("provider") or [{}])[0]
    return ((prov.get("label") or {}).get("none") or [None])[0]


def _library_link(res):
    """The holding library's own page for the map, where it can be derived from the image id."""
    rid = res.get("id") or ""
    if "map-view.nls.uk/iiif" in rid:
        return "https://maps.nls.uk/view/" + rid.rsplit("%2F", 1)[-1].split("/")[0]
    return None


def _area_km2(ring):
    lat0 = math.radians(sum(p[1] for p in ring) / len(ring))
    xy = [(p[0] * 111.32 * math.cos(lat0), p[1] * 110.57) for p in ring]
    return abs(sum(x1 * y2 - x2 * y1 for (x1, y1), (x2, y2) in zip(xy, xy[1:] + xy[:1]))) / 2


def build():
    rows = []
    for f in british_isles_maps():
        props = f["properties"]
        ring = _ring(f["geometry"])
        km2 = _area_km2(ring)
        if km2 > MAX_KM2 or km2 <= 0:
            continue
        geom = simplify({"type": "Polygon", "coordinates": [ring]}, 0.002) or {"coordinates": [ring]}
        pts = [[round(x, 4), round(y, 4)] for x, y in geom["coordinates"][0]]
        rows.append({"id": props["id"].rsplit("/", 1)[-1], "p": _provider(props["resource"]),
                     "a": round(km2, 2), "l": _library_link(props["resource"]), "g": pts})
    rows.sort(key=lambda r: r["a"])
    (OUT / "allmaps.json").write_text(json.dumps(rows, ensure_ascii=False, separators=(",", ":")))
    print(f"allmaps: {len(rows)} British Isles maps -> {OUT / 'allmaps.json'} "
          f"({(OUT / 'allmaps.json').stat().st_size / 1e6:.1f} MB)")


if __name__ == "__main__":
    build()
