"""Enrichment from Wikipedia (intro text, lead image) and postcodes.io (addresses)."""
from .config import POSTCODES_API, WIKIPEDIA_API
from .http import request_json


def wikipedia_intros(titles):
    """{title: {'extract': str, 'image': url or None}} for enwiki titles, 20 per request."""
    out = {}
    titles = sorted(set(t for t in titles if t))
    for i in range(0, len(titles), 20):
        chunk = titles[i:i + 20]
        params = {"action": "query", "titles": "|".join(chunk),
                  "prop": "extracts|pageimages", "exintro": 1, "explaintext": 1,
                  "exlimit": 20, "piprop": "thumbnail", "pithumbsize": 800,
                  "pilimit": 20, "redirects": 1, "format": "json", "formatversion": 2}
        res = request_json(WIKIPEDIA_API, params=params, min_interval=0.3)
        q = res.get("query", {})
        back = {}
        for kind in ("normalized", "redirects"):
            for m in q.get(kind, []):
                back[m["to"]] = back.get(m["from"], m["from"])
        for page in q.get("pages", []):
            info = {"extract": (page.get("extract") or "").strip(),
                    "image": page.get("thumbnail", {}).get("source")}
            t = page.get("title")
            out[t] = info
            while t in back:
                t = back[t]
                out[t] = info
    return out


def reverse_geocode(points):
    """points: {key: (lat, lon)} -> {key: postcodes.io result dict} (nearest postcode)."""
    out = {}
    items = [(k, lat, lon) for k, (lat, lon) in points.items() if lat is not None]
    for i in range(0, len(items), 100):
        chunk = items[i:i + 100]
        body = {"geolocations": [{"latitude": round(lat, 6), "longitude": round(lon, 6),
                                  "radius": 2000, "limit": 1} for _, lat, lon in chunk]}
        res = request_json(f"{POSTCODES_API}/postcodes", json_body=body, method="POST",
                           min_interval=0.3)
        for (key, _, _), r in zip(chunk, res.get("result", [])):
            hits = r.get("result") or []
            if hits:
                out[key] = hits[0]
    return out


def address_from_postcode(pc):
    """Compose a readable locality line from a postcodes.io record."""
    if not pc:
        return {}
    parts = [pc.get("parish"), pc.get("admin_ward"), pc.get("admin_district"),
             pc.get("admin_county")]
    seen, line = set(), []
    for p in parts:
        if p and "unparished" not in p.lower() and p not in seen:
            seen.add(p)
            line.append(p)
    return {
        "postcode": pc.get("postcode"),
        "locality": ", ".join(line),
        "district": pc.get("admin_district"),
        "county": pc.get("admin_county"),
        "region": pc.get("region"),
        "nation": pc.get("country"),
    }


def wikipedia_articles(titles):
    """{title: {'text': full plain text, 'lead_wikitext': wikitext of section 0}}, one per request."""
    out = {}
    for title in sorted(set(t for t in titles if t)):
        res = request_json(WIKIPEDIA_API, params={
            "action": "query", "titles": title, "prop": "extracts|revisions",
            "explaintext": 1, "rvprop": "content", "rvslots": "main", "rvsection": 0,
            "redirects": 1, "format": "json", "formatversion": 2}, min_interval=0.3)
        pages = res.get("query", {}).get("pages", [])
        if not pages or pages[0].get("missing"):
            continue
        page = pages[0]
        revs = page.get("revisions") or [{}]
        out[title] = {"text": page.get("extract") or "",
                      "lead_wikitext": revs[0].get("slots", {}).get("main", {}).get("content", "")}
    return out
