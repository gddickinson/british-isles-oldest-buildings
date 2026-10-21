"""Place history events on the map.

Coordinates come from the Wikidata item of the event's source article, or, when that has none,
from the place named for it in data/curated/history_places.json. National or diffuse events
(wars, famines) stay unplaced.
"""
import json
import re
from urllib.parse import unquote

from .config import DATA_DIR, WIKIPEDIA_API
from .http import request_json
from .place_kinds import in_box
from .wikidata import coords, get_entities

HISTORY = DATA_DIR / "curated" / "history.json"
PLACES = DATA_DIR / "curated" / "history_places.json"
GEO_OUT = DATA_DIR / "history_geo.json"


def _title(url):
    if "wikipedia.org/wiki/" not in (url or ""):
        return None
    return unquote(url.split("/wiki/", 1)[1].split("#")[0]).replace("_", " ")


def _items_for(titles):
    """{title: wikidata qid} via pageprops."""
    out, titles = {}, sorted(set(t for t in titles if t))
    for i in range(0, len(titles), 50):
        res = request_json(WIKIPEDIA_API, params={
            "action": "query", "titles": "|".join(titles[i:i + 50]), "prop": "pageprops",
            "ppprop": "wikibase_item", "redirects": 1, "format": "json", "formatversion": 2})
        q = res.get("query", {})
        back = {}
        for kind in ("normalized", "redirects"):
            for m in q.get(kind, []):
                back[m["to"]] = back.get(m["from"], m["from"])
        for page in q.get("pages", []):
            item = page.get("pageprops", {}).get("wikibase_item")
            t = page.get("title")
            while item and t:
                out[t] = item
                t = back.get(t)
    return out


def locate_events(log=print):
    """{event title: {"place", "lat", "lon", "wikidata_id"}}; also written to data/history_geo.json."""
    events = json.loads(HISTORY.read_text())["events"]
    raw = json.loads(PLACES.read_text())
    skip = set(raw.get("_skip", []))
    curated = {k: v for k, v in raw.items() if not k.startswith("_")}
    src = {e["title"]: _title(e.get("source")) for e in events}
    items = _items_for(list(src.values()) + list(curated.values()))
    ents = get_entities(set(items.values()))
    out = {}
    for e in events:
        t = e["title"]
        if t in skip:
            continue
        for title, how in ((src.get(t), "source"), (curated.get(t), "curated")):
            q = items.get(title)
            lat, lon = coords(ents.get(q, {})) if q else (None, None)
            if in_box(lat, lon):
                out[t] = {"place": title, "lat": lat, "lon": lon, "wikidata_id": q, "how": how}
                break
    GEO_OUT.write_text(json.dumps(out, indent=1, ensure_ascii=False))
    log(f"history events placed: {len(out)} of {len(events)}")
    return out


def slug(text):
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")[:70]
