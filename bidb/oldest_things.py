"""Research track: the oldest things of the isles that are not buildings or places: recipes, books, songs, laws,
games, customs, everyday objects, pictures (the page /things).

    python -m bidb.oldest_things                  problems in the files, counts per theme
    python -m bidb.oldest_things --check [--new]  fetch every source and look for its quote → data/things_check.json
    python -m bidb.oldest_things --file PATH      problems and quote check of one file (for research rounds)

One file per theme, `data/curated/things/<theme>.json`: {"about": ..., "entries": [...]}. An entry:
  category      one of its theme's CATEGORIES
  name          what it is ("The Forme of Cury")
  year          the year it stands at, negative for BC (int; the start of a range or "c.")
  age_text      the date as the sources give it ("c. 1390")
  claim         what it is the oldest of, as the sources allow ("the oldest known English cookery book")
  evidence      how well that is established: what is known, what is disputed, rivals
  verdict       kept (sources agree) / corrected (the popular claim is wrong; claim says the right one) / open
  nation        England, Scotland, Wales, Northern Ireland, Republic of Ireland, Isle of Man, Jersey, Guernsey
  where         {"name", "role": kept | made | held | found, "lat", "lon"}: where it is kept now, was made or
                found, or (customs, events) where it still takes place; optional
  wikipedia_title  its article, if any; qid  its Wikidata item, if any
  sources       [{title, author, kind (evidence.KINDS), url, locator, quote}]: every quote exact, as in the page
The sources are checked like the other researched claims (bidb.evidence.check with this module's claims).
"""
import json
import re
import sys

from .config import DATA_DIR, ROOT

DIR = ROOT / "data" / "curated" / "things"
CHECK = DATA_DIR / "things_check.json"
NATIONS = ("England", "Scotland", "Wales", "Northern Ireland", "Republic of Ireland", "Isle of Man", "Jersey",
           "Guernsey", "British Isles")
ROLES = ("kept", "made", "held", "found")
THEMES = {
    "food": {"title": "Food and drink",
             "intro": "The oldest recipes and cookery books, dishes still made, records of brewing and distilling, "
                      "and the oldest food brands.",
             "categories": ["Oldest recipe or cookery book", "Oldest dish or food still made",
                            "Oldest drink or brewing record", "Oldest food brand or packaging"]},
    "writing": {"title": "Writing, books and letters",
                "intro": "The first writing in the isles, the oldest books and manuscripts, poems and stories, "
                         "letters and diaries, printing and newspapers.",
                "categories": ["Oldest writing or inscription", "Oldest manuscript or book",
                               "Oldest poem, story or literature", "Oldest letter, diary or personal writing",
                               "Oldest printing, newspaper or library"]},
    "music": {"title": "Music, song and dance",
              "intro": "The oldest songs and written music, instruments, hymns, carols and anthems, recordings and "
                       "dances.",
              "categories": ["Oldest song or written music", "Oldest musical instrument",
                             "Oldest hymn, carol or anthem", "Oldest recording", "Oldest dance or performance"]},
    "law": {"title": "Laws, documents and maps",
            "intro": "The oldest law codes and laws still in force, charters and deeds, records of government and "
                     "the oldest maps.",
            "categories": ["Oldest law or law code", "Oldest charter or legal document",
                           "Oldest record of government", "Oldest map"]},
    "games": {"title": "Games, sport and pastimes",
              "intro": "The oldest games and game pieces, written rules of sports, balls, trophies and sporting "
                       "events still held.",
              "categories": ["Oldest game or game piece", "Oldest written rules of a sport",
                             "Oldest sporting object or trophy", "Oldest sporting event still held"]},
    "customs": {"title": "Customs and traditions",
                "intro": "Ceremonies, festivals, folk plays and dances, and charitable doles kept up for centuries.",
                "categories": ["Oldest ceremony or custom", "Oldest festival or seasonal custom",
                               "Oldest folk play, dance or game", "Oldest charity or dole"]},
    "objects": {"title": "Everyday things",
                "intro": "The oldest clothes and shoes, tools, boats and wheels, coins, jewellery and clocks found "
                         "or made in the isles.",
                "categories": ["Oldest clothing or footwear", "Oldest tool, vessel or vehicle", "Oldest coin or money",
                               "Oldest jewellery or ornament", "Oldest clock or mechanism"]},
    "media": {"title": "Pictures, science and media",
              "intro": "The oldest photographs and films, paintings and portraits, cards and stamps, and records "
                       "of science.",
              "categories": ["Oldest photograph or film", "Oldest painting or portrait",
                             "Oldest card, stamp or printed ephemera", "Oldest scientific instrument or record"]},
}


def path(theme):
    return DIR / f"{theme}.json"


def slug(text):
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def entries(theme, file=None):
    p = file or path(theme)
    return json.loads(p.read_text())["entries"] if p.exists() else []


def entry_id(theme, e):
    return f"{theme}-{slug(e['name'])}"


def validate(theme, es):
    """Problems in one theme's entries (fields, categories, years, places, sources)."""
    from .evidence import KINDS, VERDICTS
    cats, out, seen = THEMES[theme]["categories"], [], set()
    for i, e in enumerate(es):
        n = e.get("name") or f"#{i}"
        for k in ("category", "name", "age_text", "claim", "evidence", "verdict", "nation", "sources"):
            if not e.get(k):
                out.append(f"{theme} {n}: no {k}")
        if e.get("category") and e["category"] not in cats:
            out.append(f"{theme} {n}: category {e['category']!r}")
        if not isinstance(e.get("year"), int):
            out.append(f"{theme} {n}: year {e.get('year')!r}")
        if e.get("verdict") and e["verdict"] not in VERDICTS:
            out.append(f"{theme} {n}: verdict {e['verdict']!r}")
        if e.get("nation") and e["nation"] not in NATIONS:
            out.append(f"{theme} {n}: nation {e['nation']!r}")
        w = e.get("where")
        if w is not None and not (w.get("name") and w.get("role") in ROLES and isinstance(w.get("lat"), (int, float))
                                  and isinstance(w.get("lon"), (int, float)) and 49 < w["lat"] < 61.5
                                  and -11 < w["lon"] < 2.5):
            out.append(f"{theme} {n}: where {w!r}")
        if e.get("name") and entry_id(theme, e) in seen:
            out.append(f"{theme} {n}: duplicate")
        seen.add(entry_id(theme, e) if e.get("name") else i)
        for s in e.get("sources") or []:
            if s.get("kind") not in KINDS or not s.get("title") or not s.get("quote") or not s.get("url"):
                out.append(f"{theme} {n}: source {s.get('title')!r} needs title, url, quote and kind in {KINDS}")
    return out


def problems():
    out = []
    for t in THEMES:
        out += validate(t, entries(t))
    return out


def claims(only=None, file=None):
    """Evidence claims for every entry (checked by bidb.evidence.check into data/things_check.json)."""
    out = []
    for t in [only] if only else THEMES:
        for e in entries(t, file):
            out.append({"id": f"things-{entry_id(t, e)}", "record": f"thing:{entry_id(t, e)}", "name": e["name"],
                        "field": "age", "claim": e["claim"], "value": e.get("age_text"),
                        "verdict": e.get("verdict") or "open", "assessment": e.get("evidence") or "",
                        "sources": e["sources"]})
    return out


def checks():
    return json.loads(CHECK.read_text()) if CHECK.exists() else {}


def index():
    """{themes: [{id, title, intro, categories: [{category, entries}]}], counts} for the page /things; entries
    oldest first, each source with its last check result."""
    ck, themes, total = checks(), [], 0
    for t, spec in THEMES.items():
        es = sorted(entries(t), key=lambda e: e.get("year", 0))
        cats = []
        for c in spec["categories"]:
            rows = []
            for e in (e for e in es if e["category"] == c):
                res = ck.get(f"things-{entry_id(t, e)}", {}).get("sources", [])
                rows.append({**e, "id": entry_id(t, e),
                             "sources": [{**s, "check": res[i] if i < len(res) else None}
                                         for i, s in enumerate(e["sources"])]})
            if rows:
                cats.append({"category": c, "entries": rows})
        total += len(es)
        themes.append({"id": t, "title": spec["title"], "intro": spec["intro"], "categories": cats})
    return {"themes": themes, "count": total}


def main():
    from . import evidence
    args = sys.argv[1:]
    if args[:1] == ["--file"]:
        from pathlib import Path
        p = Path(args[1])
        theme = p.stem
        es = entries(theme, p)
        for x in validate(theme, es):
            print("problem:", x)
        res = evidence.check(claims=claims(theme, p), path=DATA_DIR / f"things_check_{theme}.tmp.json", log=lambda m: None)
        for c in claims(theme, p):
            for s, r in zip(c["sources"], res[c["id"]]["sources"]):
                if r != "quote-found":
                    print(f"{r}: {c['name']}: {s['url']} :: {s['quote'][:90]}")
        (DATA_DIR / f"things_check_{theme}.tmp.json").unlink(missing_ok=True)
        print(f"{len(es)} entries, {sum(r == 'quote-found' for v in res.values() for r in v['sources'])} of "
              f"{sum(len(v['sources']) for v in res.values())} quotes found")
        return
    for x in problems():
        print("problem:", x)
    if args[:1] == ["--check"]:
        evidence.check(claims=claims(), path=CHECK, only_new="--new" in args)
    else:
        for t in THEMES:
            print(f"{t:10} {len(entries(t)):3} entries")


if __name__ == "__main__":
    main()
