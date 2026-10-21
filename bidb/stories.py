"""Build stage / CLI: legends, ghosts, folklore and curious history from the full Wikipedia
articles of buildings and places ->  table `stories`.

    python -m bidb.stories            fetch (cached per title) and write the table
    python -m bidb.stories --report   counts and examples

Articles are fetched 20 at a time and kept as plain-text sections in <cache>/wiki_articles.json,
so reruns (e.g. after changing the story rules in stories_parse) need no downloads.
"""
import argparse
import json
import time
from urllib.parse import quote

from . import progress, stories_db
from .config import DATA_DIR, WIKIPEDIA_API, require_locations
from .db import connect
from .http import request_json
from .pron_sources import load_store, save_store
from .stories_parse import KINDS, find, sections

STORE = "wiki_articles"


def _articles_from_response(text):
    """Revisions API response -> {"pages": {title: sections}, "back": {to: from}, "partial": [titles]}."""
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
            pages[page["title"]] = sections(revs[0]["slots"]["main"].get("content", ""))
        elif not page.get("missing") and not page.get("invalid"):
            partial.append(page["title"])     # content held back by the size limit: ask again
    return {"pages": pages, "back": back, "partial": partial}


def articles(titles, log=print, batch=20):
    """{title: {"s": sections, "c": categories}} (per-title store; only new titles are fetched)."""
    titles = sorted({t for t in titles if t})
    store = load_store(STORE)
    todo = [t for t in titles if t not in store]
    log(f"  articles: {len(titles) - len(todo)} stored, {len(todo)} to fetch")
    queue, done = [todo[i:i + batch] for i in range(0, len(todo), batch)], 0
    while queue:
        chunk = queue.pop(0)
        res = request_json(WIKIPEDIA_API, params={
            "action": "query", "prop": "revisions", "rvprop": "content", "rvslots": "main",
            "titles": "|".join(chunk), "redirects": 1, "format": "json", "formatversion": 2},
            min_interval=0.5, extract=_articles_from_response, use_cache=False)
        for title, entry in res["pages"].items():
            t = title
            store[t] = entry
            while t in res["back"]:
                t = res["back"][t]
                store[t] = entry
        if res["partial"] and len(chunk) > 1:
            queue += [[t] for t in res["partial"]]
        for t in chunk:
            if t not in res["partial"]:
                store.setdefault(t, {})              # missing page: remember, do not ask again
        done += len(chunk)
        progress.items(done, len(todo))
        if done % 1000 < batch:
            log(f"  articles: {done}/{len(todo)}")
            save_store(store, STORE)
    if todo:
        save_store(store, STORE)
    return {t: store.get(t, {}) for t in titles}


def register_stories(conn, rejects):
    """Tales in the HES / Cadw register descriptions already downloaded for dating (no new requests)."""
    from .register_dates import cached_description
    rows = []
    for bid, hes, cadw in conn.execute("SELECT id, hes_id, cadw_id FROM buildings "
                                       "WHERE hes_id IS NOT NULL OR cadw_id IS NOT NULL"):
        got = cached_description({"hes_id": hes, "cadw_id": cadw})
        if not got:
            continue
        reg, url, text = got
        text = text if isinstance(text, str) else " ".join(text)
        for s in find({"s": [["", text]], "c": []}):
            if not any(frag in s["text"] for frag in rejects.get(bid, [])):
                rows.append({"entity_kind": "building", "entity_id": bid, **s, "source_url": url,
                             "licence": f"OGL ({'Historic Environment Scotland' if reg == 'HES' else 'Cadw'})"})
    return rows


def _rejects():
    """Reviewed false matches: data/curated/story_rejects.json {record id: [text fragment, …]}."""
    try:
        return json.loads((DATA_DIR / "curated" / "story_rejects.json").read_text())
    except (OSError, ValueError):
        return {}


def run(log=print):
    require_locations()
    t0 = time.time()
    say = lambda m: log(f"[{time.time() - t0:6.0f}s] {m}")
    conn = connect()
    conn.execute("PRAGMA busy_timeout = 120000")       # background jobs may be writing
    recs = [("building", i, t) for i, t in conn.execute(
        "SELECT id, wikipedia_title FROM buildings WHERE coalesce(wikipedia_title, '') != ''")]
    recs += [("place", i, t) for i, t in conn.execute(
        "SELECT id, wikipedia_title FROM places WHERE coalesce(wikipedia_title, '') != '' "
        "AND kind_group NOT IN ('Finds & treasures', 'Plaques & people')")]
    say(f"{len(recs)} records with a Wikipedia article")
    arts = articles([t for *_, t in recs], say)
    rejects = _rejects()
    rows = []
    for kind, eid, title in recs:
        url = "https://en.wikipedia.org/wiki/" + quote(title.replace(" ", "_"))
        for s in find(arts.get(title)):
            if any(frag in s["text"] for frag in rejects.get(eid, [])):
                continue                                 # reviewed: not a tale
            rows.append({"entity_kind": kind, "entity_id": eid, **s, "source_url": url,
                         "licence": stories_db.LICENCE})
    rows += register_stories(conn, rejects)
    stories_db.write(conn, rows)
    say(f"wrote {len(rows)} stories")
    report(conn, log)


def report(conn=None, log=print):
    conn = conn or connect()
    for kind, n in sorted(stories_db.counts(conn).items(), key=lambda x: -x[1]):
        log(f"  {KINDS.get(kind, kind)}: {n} records")


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--report", action="store_true")
    a = ap.parse_args()
    report() if a.report else run()


if __name__ == "__main__":
    main()
