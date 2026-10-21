"""Find photos for records that have none: python -m bidb.images_extra

Wikimedia Commons geosearch (geotagged files, which include the large Geograph Britain and
Ireland collection) within 150 m of the record. A file whose title shares a distinctive word
with the record's name is preferred ("Photo matched by name"); otherwise the nearest file within
60 m is used and labelled "Photo taken nearby" so readers know it may show the surroundings.
"""
import re
import sqlite3
import time
from urllib.parse import quote

from .config import COMMONS_FILE_PAGE, DB_PATH, require_locations
from . import progress
from .http import request_json
from .records import commons_thumb

COMMONS_API = "https://commons.wikimedia.org/w/api.php"
GENERIC = {"church", "chapel", "castle", "house", "hall", "abbey", "priory", "tower", "bridge",
           "farm", "cottage", "street", "road", "saint", "the", "and", "with", "near", "of", "old",
           "barrow", "stone", "well", "cross", "parish", "mary", "john", "peter", "michael", "all",
           "saints", "holy", "trinity", "site", "remains", "ruins", "monument", "listed", "building"}
IMAGE_EXT = (".jpg", ".jpeg", ".png", ".webp", ".tif", ".tiff")


def _words(name):
    return {w for w in re.findall(r"[a-z]{4,}", (name or "").lower()) if w not in GENERIC}


def find_photo(name, lat, lon):
    """-> (filename, note) or None"""
    res = request_json(COMMONS_API, params={
        "action": "query", "list": "geosearch", "gscoord": f"{lat:.6f}|{lon:.6f}", "gsradius": 150,
        "gslimit": 30, "gsnamespace": 6, "format": "json"}, min_interval=1.0)
    hits = [h for h in res.get("query", {}).get("geosearch", [])
            if h["title"].lower().endswith(IMAGE_EXT)]
    words = _words(name)
    for h in hits:
        if words & _words(h["title"]):
            return h["title"][5:], f"Photo matched by name ({h['dist']:.0f} m away)"
    near = [h for h in hits if h["dist"] <= 60]
    if near:
        return near[0]["title"][5:], f"Photo taken nearby ({near[0]['dist']:.0f} m away); may show the surroundings"
    return None


# places: Wikidata items and Open Plaques only (the ~32k register monuments are left for later)
PLACE_SOURCES = ("Wikidata", "Open Plaques")


def run(table="buildings", limit=None):
    require_locations()
    conn = sqlite3.connect(DB_PATH, timeout=300)
    where = ""
    if table == "places":
        where = f" AND source IN ({', '.join(repr(s) for s in PLACE_SOURCES)})"
        if "image_note" not in [c[1] for c in conn.execute("PRAGMA table_info(places)")]:
            conn.execute("ALTER TABLE places ADD COLUMN image_note TEXT")    # databases built before it existed
    rows = conn.execute(f"SELECT id, name, lat, lon FROM {table} WHERE image_thumb IS NULL "
                        f"AND lat IS NOT NULL{where}").fetchall()[:limit]
    found, t0 = 0, time.time()
    for n, (rid, name, lat, lon) in enumerate(rows):
        hit = find_photo(name, lat, lon)
        if hit:
            fname, note = hit
            page = COMMONS_FILE_PAGE + quote(fname.replace(" ", "_"))
            conn.execute(f"UPDATE {table} SET image_thumb=?, image_page=?, image_note=? WHERE id=?",
                         [commons_thumb(fname), page, note, rid])
            found += 1
        if n % 20 == 0:
            progress.items(n, len(rows))
            conn.commit()
            print(f"[{time.time() - t0:5.0f}s] {n}/{len(rows)} checked, {found} photos found", flush=True)
    conn.commit()
    print(f"{table}: {found} photos found for {len(rows)} records without one", flush=True)


if __name__ == "__main__":
    import sys
    run(sys.argv[1] if len(sys.argv) > 1 else "buildings")
