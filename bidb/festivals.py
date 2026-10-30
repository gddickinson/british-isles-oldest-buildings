"""Festivals and seasons (page /festivals): Christmas, Easter, Halloween, the saints' days and the old quarter days,
each with researched facts and places, and what the catalogue already holds for it.

    python -m bidb.festivals                  problems in the files, counts per festival
    python -m bidb.festivals --check [--new]  fetch every source and look for its quote → data/festivals_check.json
    python -m bidb.festivals --file PATH      problems and quote check of one file (for research rounds)

One file per festival, `data/curated/festivals/<id>.json`:
  id, title, also      the festival's names (`also`: other names, in the isles' languages too)
  season               winter / spring / summer / autumn
  when                 {"date": "MM-DD"} (fixed), {"easter": days from Easter Sunday}, {"sun": a bidb.sky event:
                       winter_solstice, summer_solstice, equinox}, or {"rule": "last Tuesday of January"}; `when_text`
                       says it in words ("25 December; the twelve days to 6 January")
  intro                two or three sentences in the researcher's own words
  facts                [{kind (FACT_KINDS), title, text (own words), year (optional, negative BC), where (optional:
                       {name, lat, lon, qid}), sources}]
  places               [{name, why, lat, lon, qid (catalogue record or Wikidata id, optional), sources}]: buildings,
                       monuments and sites tied to the festival
  sources              [{title, author, kind (evidence.KINDS), url, locator, quote}]: every quote exact
What the catalogue holds for each festival (bidb.festival_finds) is chosen by `find` (set in this repository, not
by research): church dedications, story words, sky events, place kinds and words, oldest things.
"""
import json
import re
import sys

from .config import DATA_DIR, ROOT

DIR = ROOT / "data" / "curated" / "festivals"
CHECK = DATA_DIR / "festivals_check.json"
SEASONS = ("winter", "spring", "summer", "autumn")
FACT_KINDS = ("history", "custom", "legend", "food", "oldest", "sky", "curiosity")
SUN_EVENTS = ("winter_solstice", "summer_solstice", "equinox")


def files():
    return sorted(DIR.glob("*.json"))


def load(file=None):
    """All festivals (or the one in `file`), as read."""
    return [json.loads(p.read_text()) for p in ([file] if file else files())]


def _sources(where, sources):
    from .evidence import KINDS
    out = []
    if not sources:
        out.append(f"{where}: no sources")
    for s in sources or []:
        if s.get("kind") not in KINDS or not s.get("title") or not s.get("quote") or not s.get("url"):
            out.append(f"{where}: source {s.get('title')!r} needs title, url, quote and kind in {KINDS}")
    return out


def _point(p):
    return isinstance(p.get("lat"), (int, float)) and isinstance(p.get("lon"), (int, float)) \
        and 49 < p["lat"] < 61.5 and -11 < p["lon"] < 2.5


def validate(f):
    """Problems in one festival."""
    fid, out = f.get("id") or "?", []
    for k in ("id", "title", "season", "when", "when_text", "intro", "facts", "places"):
        if not f.get(k):
            out.append(f"{fid}: no {k}")
    if f.get("season") and f["season"] not in SEASONS:
        out.append(f"{fid}: season {f['season']!r}")
    w = f.get("when") or {}
    if not (re.fullmatch(r"\d\d-\d\d", str(w.get("date", ""))) or isinstance(w.get("easter"), int)
            or w.get("sun") in SUN_EVENTS or w.get("rule")):
        out.append(f"{fid}: when {w!r}")
    for i, x in enumerate(f.get("facts") or []):
        n = f"{fid} fact {x.get('title') or i}"
        for k in ("kind", "title", "text"):
            if not x.get(k):
                out.append(f"{n}: no {k}")
        if x.get("kind") and x["kind"] not in FACT_KINDS:
            out.append(f"{n}: kind {x['kind']!r}")
        if "year" in x and not isinstance(x["year"], int):
            out.append(f"{n}: year {x['year']!r}")
        if x.get("where") and not (x["where"].get("name") and _point(x["where"])):
            out.append(f"{n}: where {x['where']!r}")
        out += _sources(n, x.get("sources"))
    for i, p in enumerate(f.get("places") or []):
        n = f"{fid} place {p.get('name') or i}"
        if not (p.get("name") and p.get("why")):
            out.append(f"{n}: needs name and why")
        if not _point(p):
            out.append(f"{n}: lat/lon")
        out += _sources(n, p.get("sources"))
    return out


def problems():
    out, seen = [], set()
    for f in load():
        out += validate(f)
        if f.get("id") in seen:
            out.append(f"{f.get('id')}: duplicate id")
        seen.add(f.get("id"))
    return out


def slug(text):
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def claims(file=None):
    """Evidence claims for every fact and place (checked by bidb.evidence.check into data/festivals_check.json)."""
    out = []
    for f in load(file):
        for x in f.get("facts", []):
            out.append({"id": f"fest-{f['id']}-{slug(x['title'])}", "record": f"festival:{f['id']}", "name": x["title"],
                        "field": "fact", "claim": x["text"], "verdict": "kept", "sources": x["sources"]})
        for p in f.get("places", []):
            out.append({"id": f"fest-{f['id']}-place-{slug(p['name'])}", "record": f"festival:{f['id']}",
                        "name": p["name"], "field": "place", "claim": p["why"], "verdict": "kept",
                        "sources": p["sources"]})
    return out


def checks():
    return json.loads(CHECK.read_text()) if CHECK.exists() else {}


def main():
    from . import evidence
    args = sys.argv[1:]
    if args[:1] == ["--file"]:
        from pathlib import Path
        p = Path(args[1])
        f = load(p)[0]
        for x in validate(f):
            print("problem:", x)
        tmp = DATA_DIR / f"festivals_check_{p.stem}.tmp.json"
        res = evidence.check(claims=claims(p), path=tmp, log=lambda m: None)
        for c in claims(p):
            for s, r in zip(c["sources"], res[c["id"]]["sources"]):
                if r != "quote-found":
                    print(f"{r}: {c['name']}: {s['url']} :: {s['quote'][:90]}")
        tmp.unlink(missing_ok=True)
        print(f"{len(f.get('facts', []))} facts, {len(f.get('places', []))} places, "
              f"{sum(r == 'quote-found' for v in res.values() for r in v['sources'])} of "
              f"{sum(len(v['sources']) for v in res.values())} quotes found")
        return
    for x in problems():
        print("problem:", x)
    if args[:1] == ["--check"]:
        evidence.check(claims=claims(), path=CHECK, only_new="--new" in args)
    else:
        for f in load():
            print(f"{f['id']:14} {len(f.get('facts', [])):3} facts {len(f.get('places', [])):3} places")


if __name__ == "__main__":
    main()
