"""Floor plans from Wikimedia Commons "Plans of <building>" categories.

Used for buildings whose Wikidata item has no plan view image (P3311). The category is found by
name from the item's Commons category (P373): "Bamburgh Castle" -> "Plans of Bamburgh Castle".
Whole-category listing (allcategories) keeps this to a few hundred requests.
"""
import re
from urllib.parse import unquote

from .http import request_json, sparql

COMMONS_API = "https://commons.wikimedia.org/w/api.php"
PREFIXES = ("Plans of ", "Floor plans of ", "Ground plans of ")
GOOD = re.compile(r"\b(ground|floor|plan|grundriss|plattegrond)\b", re.I)
BAD = re.compile(r"\b(elevation|section|sections|façade|facade|perspective|detail|site plan|"
                 r"location|map|photo|aerial|comparative)\b", re.I)
IMAGE_EXT = (".jpg", ".jpeg", ".png", ".gif", ".svg", ".tif", ".tiff", ".webp")


def plan_categories():
    """{building category name: plans category name} for every 'Plans of ...' category."""
    out = {}
    for prefix in PREFIXES:
        params = {"action": "query", "list": "allcategories", "acprefix": prefix.strip(),
                  "aclimit": 500, "acmin": 1, "format": "json"}
        while True:
            res = request_json(COMMONS_API, params=params, min_interval=1.0)
            for c in res.get("query", {}).get("allcategories", []):
                name = c["*"]
                if name.startswith(prefix):
                    out.setdefault(name[len(prefix):], name)
            cont = res.get("continue", {}).get("accontinue")
            if not cont:
                break
            params = {**params, "accontinue": cont}
    return out


def commons_categories(qids):
    """{qid: Commons category (P373)}"""
    out = {}
    ids = sorted(q for q in qids if q.startswith("Q"))
    for n in range(0, len(ids), 300):
        values = " ".join("wd:" + q for q in ids[n:n + 300])
        for r in sparql(f"SELECT ?i ?c WHERE {{ VALUES ?i {{ {values} }} ?i wdt:P373 ?c . }}"):
            out.setdefault(r["i"]["value"].rsplit("/", 1)[1], r["c"]["value"])
    return out


def best_file(category):
    """The file in a plans category that looks most like a ground/floor plan, or None."""
    res = request_json(COMMONS_API, params={
        "action": "query", "list": "categorymembers", "cmtitle": "Category:" + category,
        "cmtype": "file", "cmlimit": 50, "format": "json"}, min_interval=1.0)
    files = [m["title"][5:] for m in res.get("query", {}).get("categorymembers", [])
             if m["title"].lower().endswith(IMAGE_EXT)]
    # only files named as a plan: book-page scans and photos also turn up in these categories
    files = [f for f in files if GOOD.search(f.replace("_", " ")) and not BAD.search(f.replace("_", " "))]
    return unquote(min(files, key=len)) if files else None


def plans(qids, log=print):
    """{qid: Commons file name} for items with a 'Plans of <their Commons category>' category."""
    cats = plan_categories()
    log(f"  commons plan categories: {len(cats)}")
    out = {}
    for q, cat in commons_categories(qids).items():
        plan_cat = cats.get(cat)
        if plan_cat:
            f = best_file(plan_cat)
            if f:
                out[q] = f
    return out
