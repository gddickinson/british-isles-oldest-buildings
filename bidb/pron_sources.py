"""Where pronunciations come from: Wikipedia article openings (wikitext) and Wikidata.

Only the opening paragraph of each article is cached (via request_json's extract=), so ~20,000
articles take a few tens of MB rather than the full wikitext.
"""
import json
import time
from urllib.parse import unquote

from . import refresh
from .config import WIKIPEDIA_API, cache_dir
from .http import request_json, sparql
from .pron_parse import clean_lead

COMMONS_FILE = "https://commons.wikimedia.org/wiki/Special:FilePath/"


def _leads_from_response(text):
    """Revisions API response -> {"pages": {title: lead}, "back": {to: from}, "partial": [titles]}."""
    if not text:
        return {"pages": {}, "back": {}, "partial": []}
    q = json.loads(text).get("query", {})
    back = {}
    for kind in ("normalized", "redirects"):
        for m in q.get(kind, []):
            back[m["to"]] = back.get(m["from"], m["from"])
    pages, partial = {}, []
    for page in q.get("pages", []):
        revs = page.get("revisions")
        if revs:
            pages[page["title"]] = clean_lead(revs[0]["slots"]["main"].get("content", ""))[:3000]
        elif not page.get("missing") and not page.get("invalid"):
            partial.append(page["title"])     # content held back by the size limit: ask again
    return {"pages": pages, "back": back, "partial": partial}


_restarted = set()        # stores begun again by a refresh (bidb.refresh); marked when first saved


def _begun(name):
    """When a store was begun (<name>.begun, written when it is first saved), or None."""
    try:
        return float((cache_dir() / f"{name}.begun").read_text())
    except (OSError, ValueError):
        return None


def load_store(name="wiki_leads"):
    """Per-title results kept in <cache>/<name>.json, so reruns only fetch new titles. A refresh of
    Wikipedia (bidb.refresh) starts the store again."""
    path = cache_dir() / f"{name}.json"
    begun = _begun(name)
    if begun is not None and refresh.stale(path, "en.wikipedia.org", saved_at=begun):
        _restarted.add(name)
        return {}
    try:
        return json.loads(path.read_text())
    except (OSError, ValueError):
        return {}


def save_store(store, name="wiki_leads"):
    path = cache_dir() / f"{name}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(store, ensure_ascii=False))
    tmp.replace(path)
    marker = cache_dir() / f"{name}.begun"
    if name in _restarted or not marker.exists():     # stores older than markers count from their first save
        marker.write_text(f"{time.time():.0f}")
        _restarted.discard(name)


def wikipedia_leads(titles, log=print, batch=20, use_batch_cache=False):
    """{requested title: cleaned opening wikitext} for English Wikipedia titles.

    Openings are kept per title in <cache>/wiki_leads.json, so a later run with a different
    set of titles only fetches the new ones (use_batch_cache also reads older batch responses)."""
    titles = sorted({t for t in titles if t})
    store = load_store()
    todo = [t for t in titles if t not in store]
    log(f"  article openings: {len(titles) - len(todo)} stored, {len(todo)} to fetch")
    queue = [todo[i:i + batch] for i in range(0, len(todo), batch)]
    done = 0
    while queue:
        chunk = queue.pop(0)
        res = request_json(WIKIPEDIA_API, params={
            "action": "query", "prop": "revisions", "rvprop": "content", "rvslots": "main",
            "titles": "|".join(chunk), "redirects": 1, "format": "json", "formatversion": 2},
            min_interval=0.5, extract=_leads_from_response, use_cache=use_batch_cache)
        for title, lead in res["pages"].items():
            t = title
            store[t] = lead
            while t in res["back"]:
                t = res["back"][t]
                store[t] = lead
        if res["partial"] and len(chunk) > 1:
            queue += [[t] for t in res["partial"]]
        for t in chunk:
            if t not in res["partial"]:
                store.setdefault(t, "")              # missing page: remember, do not ask again
        done += len(chunk)
        if done % 1000 < batch:
            log(f"  article openings: {done}/{len(todo)}")
            save_store(store)
    if todo:
        save_store(store)
    return {t: store.get(t, "") for t in titles}


def wikidata_pronunciations(qids, log=print, chunk=300):
    """Audio recordings (P443) and IPA (P898) on Wikidata items, with their language and the
    item's label in that language -> {qid: [row]} (rows as in pron_parse)."""
    qids = sorted({q for q in qids if q and q.startswith("Q")})
    out = {}
    for i in range(0, len(qids), chunk):
        values = " ".join(f"wd:{q}" for q in qids[i:i + chunk])
        rows = sparql(f"""SELECT ?i ?audio ?ipa ?lang ?label WHERE {{
          VALUES ?i {{ {values} }}
          {{ ?i p:P443 ?s. ?s ps:P443 ?audio. OPTIONAL {{ ?s pq:P407 ?l. ?l wdt:P424 ?lang }} }}
          UNION {{ ?i p:P898 ?s. ?s ps:P898 ?ipa. OPTIONAL {{ ?s pq:P407 ?l. ?l wdt:P424 ?lang }} }}
          OPTIONAL {{ ?i rdfs:label ?label FILTER(LANG(?label) = COALESCE(?lang, "en")) }}
        }}""")
        for b in rows:
            qid = b["i"]["value"].rsplit("/", 1)[-1]
            audio = b.get("audio", {}).get("value", "")
            out.setdefault(qid, []).append({
                "name": b.get("label", {}).get("value", ""), "lang": b.get("lang", {}).get("value", "en"),
                "ipa": b.get("ipa", {}).get("value", ""), "respell": "",
                "audio": unquote(audio.rsplit("Special:FilePath/", 1)[-1]) if audio else ""})
        if (i // chunk) % 20 == 0:
            log(f"  wikidata pronunciations: {min(i + chunk, len(qids))}/{len(qids)} items, "
                f"{len(out)} with data")
    return out
