"""Second pass for photos and floor plans that bidb.images_extra and bidb.footprints did not find.

    python -m bidb.photo_search photos [buildings|places]   photos for records still without one
    python -m bidb.photo_search plans                       floor plans for catalogue buildings without one

Photos, in order (each labelled in image_note so readers know how it was matched):
  1. the record's own Commons category (Wikidata P373): its first photograph   "Photo from its Commons category"
  2. the free lead image of its Wikipedia article (pageimages)                  "Photo from its Wikipedia article"
  3. a Commons search for the name: a geotagged file within 3 km whose title holds every distinctive word of
     the name                                                                   "Photo found by name on Commons"
     (titles such as "Road near X" or "X Farm" are labelled as showing the surroundings)
Plans: files titled as a plan ("plan", "floor plan", "ground plan", "Grundriss") inside the building's own Commons
category tree (Wikidata P373; `deepcat:`) whose title holds every distinctive word of the name, leaving out maps,
town or street plans, seating plans and "plans" in the sense of intentions. A search by name alone
matched namesakes (Villa Park in Denver) and street maps, so it is not used for plans.
"""
import math
import re
import sqlite3
import sys
import time
from urllib.parse import quote

from . import progress
from .config import COMMONS_FILE_PAGE, DB_PATH, require_locations
from .http import request_json
from .images_extra import COMMONS_API, IMAGE_EXT, _words
from .records import commons_thumb

WIKIPEDIA_API = "https://en.wikipedia.org/w/api.php"
PLAN_WORDS = re.compile(r"\b(plan|plans|floor ?plan|ground ?plan|grundriss|groundplan)\b", re.I)
MAP_LIKE = re.compile(r"\b(gros plan|seating plan|to the plan|plan with|engraving|future plans|marketing plans|plans and policy|plan du|plan von|"
                      r"map|maps|town plan|village plan|street|streets|environs|sheet|insurance|master ?plan|"
                      r"city|county|parish|survey|estate|district|ordnance|road|roads)\b", re.I)
NEAR = re.compile(r"\b(near|towards|beyond|behind|past|outside|road to|lane to|track to|drive to|entrance to|access to|"
                  r"view (from|to)|wood|woods|farm|field|fields)\b", re.I)
MUSEUM = re.compile(r"\b(museum|gallery|galleries|collection)\b", re.I)
SURROUNDINGS = "Photo found by name on Commons; taken near it, may show the surroundings"
NOT_PHOTO = re.compile(r"\b(map|plan|logo|coat of arms|flag|diagram|drawing|engraving|svg)\b", re.I)


def _commons(params):
    return request_json(COMMONS_API, params={**params, "format": "json"}, min_interval=0.5)


def category_photo(category):
    """The first photograph in a Commons category, or None."""
    res = _commons({"action": "query", "list": "categorymembers", "cmtitle": "Category:" + category,
                    "cmtype": "file", "cmlimit": 30})
    for m in res.get("query", {}).get("categorymembers", []):
        t = m["title"]
        if t.lower().endswith(IMAGE_EXT) and not NOT_PHOTO.search(t):
            return t[5:]
    return None


def categories(qids):
    """{qid: Commons category (P373)} via wbgetentities (the query service is not needed)."""
    from .wikidata import claim_values, get_entities
    out = {}
    for q, ent in get_entities([q for q in qids if q.startswith("Q")], props="claims").items():
        vals = claim_values(ent, "P373")
        if vals:
            out[q] = vals[0]
    return out


def lead_images(titles):
    """{Wikipedia title: free lead image file name} (pageimages, 50 titles per request)."""
    out, titles = {}, sorted(set(t for t in titles if t))
    for i in range(0, len(titles), 50):
        res = request_json(WIKIPEDIA_API, params={"action": "query", "prop": "pageimages", "piprop": "name",
                                                  "pilicense": "free", "redirects": 1, "format": "json",
                                                  "titles": "|".join(titles[i:i + 50])}, min_interval=0.5)
        q = res.get("query", {})
        back = {r["to"]: r["from"] for r in q.get("redirects", []) + q.get("normalized", [])}
        for p in q.get("pages", {}).values():
            if p.get("pageimage"):
                out[back.get(p["title"], p["title"])] = p["pageimage"]
    return out


def _km(a, b, c, d):
    return math.hypot((a - c) * 111.2, (b - d) * 111.2 * math.cos(math.radians(a)))


def search(text, words, lat, lon, reach_km=3.0):
    """A geotagged Commons photo within reach whose title holds every word in `words`, or None."""
    if not words:
        return None
    res = _commons({"action": "query", "list": "search", "srnamespace": 6, "srlimit": 20, "srsearch": f'"{text}"'})
    hits = [h["title"] for h in res.get("query", {}).get("search", [])
            if h["title"].lower().endswith(IMAGE_EXT)]
    hits = [t for t in hits if words <= _words(t) and not NOT_PHOTO.search(t)]
    if not hits:
        return None
    if lat is None:
        return None
    co = _commons({"action": "query", "prop": "coordinates", "titles": "|".join(hits[:20])})
    where = {p["title"]: p.get("coordinates", [{}])[0] for p in co.get("query", {}).get("pages", {}).values()}
    for t in hits:
        c = where.get(t) or {}
        if "lat" in c and _km(lat, lon, c["lat"], c["lon"]) <= reach_km:
            return t[5:]
    return None


def photos(table="buildings", log=print):
    require_locations()
    conn = sqlite3.connect(DB_PATH, timeout=300)
    thumb = "image_thumb" if table == "places" else "COALESCE(image_file, image_thumb)"
    rows = conn.execute(f"SELECT id, name, lat, lon, wikipedia_title, locality FROM {table} "
                        f"WHERE COALESCE({thumb}, '') = ''" + (" AND wikipedia_title IS NOT NULL" if table == "places" else "")
                        ).fetchall()
    log(f"{table}: {len(rows)} without a photo")
    cats = categories([r[0] for r in rows]) if table == "buildings" else {}
    leads = lead_images([r[4] for r in rows])
    found, t0 = 0, time.time()
    for n, (rid, name, lat, lon, wp, locality) in enumerate(rows):
        hit = None
        if rid in cats:
            f = category_photo(cats[rid])
            hit = f and (f, "Photo from its Commons category")
        if not hit and wp in leads:
            hit = (leads[wp], "Photo from its Wikipedia article")
        if not hit and table == "buildings":
            f = search(name, _words(name), lat, lon)
            hit = f and (f, SURROUNDINGS if NEAR.search(f) else "Photo found by name on Commons")
        if hit:
            fname, note = hit
            page = COMMONS_FILE_PAGE + quote(fname.replace(" ", "_"))
            conn.execute(f"UPDATE {table} SET image_thumb = ?, image_page = ?, image_note = ? WHERE id = ?",
                         (commons_thumb(fname), page, note, rid))
            found += 1
        if n % 25 == 0:
            progress.items(n, len(rows))
            conn.commit()
            log(f"[{time.time() - t0:5.0f}s] {n}/{len(rows)} checked, {found} photos found")
    conn.commit()
    log(f"{table}: {found} photos found for {len(rows)} records without one")


def category_plan(category, words):
    """A plan of the building among the files of its Commons category tree whose title holds every distinctive
    word of its name (`words`; a tree also holds the collections a college or museum keeps), or None."""
    for scope in (f'deepcat:"{category}"', f'incategory:"{category.replace(" ", "_")}"'):
        res = _commons({"action": "query", "list": "search", "srnamespace": 6, "srlimit": 30,
                        "srsearch": f"{scope} intitle:plan"})
        if "error" in res:
            continue                                   # deepcat refuses very large trees: the category itself
        for h in res.get("query", {}).get("search", []):
            t = h["title"]
            if (t.lower().endswith(IMAGE_EXT + (".svg", ".gif")) and PLAN_WORDS.search(t) and not MAP_LIKE.search(t)
                    and words and words <= _words(t)):
                return t[5:]
        return None
    return None


def plans(log=print):
    """Floor plans for catalogue buildings without one, from their own Commons category tree."""
    require_locations()
    conn = sqlite3.connect(DB_PATH, timeout=300)
    rows = conn.execute("SELECT id, name FROM buildings WHERE plan_image IS NULL AND id LIKE 'Q%' "
                        "ORDER BY landmark DESC, oldest_of_type DESC, year_start").fetchall()
    cats = categories([r[0] for r in rows])
    # museums and galleries: their category trees hold the collections ("Plan of Babylon ..., British Museum")
    rows = [r for r in rows if r[0] in cats and not MUSEUM.search(r[1])]
    log(f"{len(rows)} buildings without a plan have a Commons category")
    found, t0 = 0, time.time()
    for n, (rid, name) in enumerate(rows):
        f = category_plan(cats[rid], _words(name))
        if f:
            conn.execute("UPDATE buildings SET plan_image = ? WHERE id = ?", (f, rid))
            found += 1
            log(f"  {name}: {f}")
        if n % 50 == 0:
            progress.items(n, len(rows))
            conn.commit()
            log(f"[{time.time() - t0:5.0f}s] {n}/{len(rows)} checked, {found} plans found")
    conn.commit()
    log(f"plans: {found} found for {len(rows)} buildings without one")


if __name__ == "__main__":
    if sys.argv[1:2] == ["plans"]:
        plans()
    else:
        photos(sys.argv[2] if len(sys.argv) > 2 else "buildings")
