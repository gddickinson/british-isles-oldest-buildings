"""Trade stories (roadmap C8): one page per trade (wool and cloth, tea, sugar and slavery, cotton, linen, coal, iron
and steel, fishing, brewing and distilling, banking and finance), from `data/curated/trade/stories.json`.

Each story brings together what the project already holds about its trade:
- `events`: the dated events of change/events.json whose `trade` is one of the story's `tags` (or whose `topic` is
  one of its `topics`), with its innovations, oldest first;
- `places` and `buildings`: places of the story's kinds, and places (of the trade-related `GROUPS`) and catalogue
  buildings whose name or type has one of its words as a whole word (`match`; "weav*" for word starts, `pattern`), the dated ones first, at most `LIMIT`;
- `people`: the people linked to those places and buildings (person_links), best known first;
- `series`: graphs of Change over time; `innovations`: entries of trade/innovations.json; `notes`: analysis notes
  with exact quotes.

`check` tests the file (every graph, innovation and note source exists). `story(conn, id)` and `index()` feed
`/api/trades` and `/api/trade/<id>` (app/trades_api.py); `export(conn)` writes them for the hosted copy.

    python -m bidb.trade_stories          check, and the counts per story
"""
import json
import re
import sys

from .config import DATA_DIR

PATH = DATA_DIR / "curated" / "trade" / "stories.json"
EVENTS = DATA_DIR / "curated" / "change" / "events.json"
SERIES = DATA_DIR / "curated" / "change" / "series.json"
INNOVATIONS = DATA_DIR / "curated" / "trade" / "innovations.json"
LIMIT = 400
# word matches are taken only from these place groups (names elsewhere carry farm and wood names: "Weaver Farm",
# "Beck Plantation"); a story's `groups` overrides it; shipwrecks are never a trade's places
GROUPS = ("Industrial heritage", "Markets & trade", "Maritime heritage", "Plaques & people", "Museums & collections",
          "Infrastructure & utilities", "Innovations & firsts", "Victorian era", "History events")
NOT_BUILDINGS = ("Prehistoric", "Roman", "Fortification")      # word matches there are place names ("Iron Age fort")
PEOPLE = 16


def load(path=PATH):
    return json.loads(path.read_text())["stories"]


def check(stories=None):
    """Problems: unknown graphs or innovations, notes without a quoted, linked source, duplicate ids."""
    stories = stories or load()
    series = {s["id"] for s in json.loads(SERIES.read_text())}
    inv = {e["name"] for e in json.loads(INNOVATIONS.read_text())["entries"]}
    bad, seen = [], set()
    for s in stories:
        if s["id"] in seen:
            bad.append(f"{s['id']}: duplicate id")
        seen.add(s["id"])
        bad += [f"{s['id']}: unknown graph {x}" for x in s.get("series", []) if x not in series]
        bad += [f"{s['id']}: unknown innovation {x}" for x in s.get("innovations", []) if x not in inv]
        if not s.get("match", {}).get("words") and not s.get("match", {}).get("kinds"):
            bad.append(f"{s['id']}: nothing to match places with")
        for n in s.get("notes", []):
            if not n.get("sources") or any(not (x.get("quote") and x.get("url")) for x in n["sources"]):
                bad.append(f"{s['id']}: note '{n['title']}' needs quoted, linked sources")
    return bad


def events(s):
    """The story's dated events, and its innovations as events, oldest first."""
    tags, topics = set(s.get("tags", [])), set(s.get("topics", []))
    ev = [e for e in json.loads(EVENTS.read_text()) if e.get("trade") in tags or e.get("topic") in topics]
    ev += [{"year": i["year"], "end": i["year"], "title": i["name"], "text": i["claim"], "kind": "innovation",
            "place": i["id"]} for i in innovations(s)]
    return sorted(ev, key=lambda e: (e["year"], e["title"]))


def pattern(words):
    """A regex of the story's words: whole words, or word starts where a word ends in '*' ("weav*")."""
    parts = [re.escape(w[:-1]) + r"\w*" if w.endswith("*") else re.escape(w) for w in words]
    return re.compile(r"\b(?:" + "|".join(parts) + r")\b", re.I)


def _matching(conn, sql, cols, words, args=()):
    """Rows of `sql` (filtered roughly by LIKE) whose `cols` match the words exactly (`pattern`)."""
    rx = pattern(words)
    like = " OR ".join(f"LOWER({c}) LIKE ?" for _ in words for c in cols)
    stems = [f"%{w.rstrip('*').lower()}%" for w in words for _ in cols]
    rows = conn.execute(sql.format(where=f"({like})"), list(args) + stems)
    return [dict(r) for r in rows if any(r[c] and rx.search(r[c]) for c in cols)]


def places(conn, s, limit=LIMIT):
    """Places of the story: its kinds, or one of its words in the name or type; dated ones first."""
    m = s.get("match", {})
    cols = "id, name, type, kind, kind_label, kind_group, year_start, date_text, lat, lon, nation"
    out = {}
    if m.get("kinds"):
        q = ",".join("?" * len(m["kinds"]))
        out.update((r["id"], dict(r)) for r in conn.execute(
            f"SELECT {cols} FROM places WHERE lat IS NOT NULL AND kind IN ({q})", m["kinds"]))
    if m.get("words"):
        groups = s.get("groups") or GROUPS
        q = ",".join("?" * len(groups))
        out.update((r["id"], r) for r in _matching(
            conn, f"SELECT {cols} FROM places WHERE lat IS NOT NULL AND kind != 'wreck' AND kind_group IN ({q}) "
                  f"AND {{where}}", ("name", "type"), m["words"], groups))
    rows = sorted(out.values(), key=lambda r: (r["year_start"] is None, r["year_start"] or 0, r["name"]))[:limit]
    return [{k: r[k] for k in r if k not in ("type", "kind")} for r in rows]


def buildings(conn, s, limit=LIMIT):
    """Catalogue buildings (not prehistoric, Roman or fortifications) whose name has one of the story's words."""
    words = s.get("match", {}).get("words")
    if not words:
        return []
    q = ",".join("?" * len(NOT_BUILDINGS))
    rows = _matching(conn, "SELECT id, name, category, category_group, year_start, date_text, lat, lon, nation "
                           f"FROM buildings WHERE lat IS NOT NULL AND category_group NOT IN ({q}) AND {{where}}",
                     ("name",), words, NOT_BUILDINGS)
    return sorted(rows, key=lambda r: (r["year_start"] is None, r["year_start"] or 0, r["name"]))[:limit]


def people(conn, ids, limit=PEOPLE):
    """People linked to these places and buildings, best known first: [{id, name, description, birth, death, roles,
    places}]."""
    if not ids:
        return []
    q = ",".join("?" * len(ids))
    rows = conn.execute(f"SELECT p.id, p.name, p.description, p.birth, p.death, p.sitelinks, l.role, l.target_id "
                        f"FROM person_links l JOIN persons p ON p.id = l.person_id WHERE l.target_id IN ({q})", ids)
    out = {}
    for r in rows:
        p = out.setdefault(r["id"], {k: r[k] for k in ("id", "name", "description", "birth", "death", "sitelinks")}
                           | {"roles": set(), "places": set()})
        p["roles"].add(r["role"])
        p["places"].add(r["target_id"])
    best = sorted(out.values(), key=lambda p: (-(p["sitelinks"] or 0), p["name"]))[:limit]
    return [p | {"roles": sorted(p["roles"]), "places": sorted(p["places"])} for p in best]


def innovations(s):
    names = set(s.get("innovations", []))
    from .oldest_lists import record_id
    return [{"id": record_id("innovations", e), "name": e["name"], "year": e["year"], "location": e.get("location"),
             "claim": e.get("claim")}
            for e in json.loads(INNOVATIONS.read_text())["entries"] if e["name"] in names]


def index(stories=None):
    """[{id, title, intro}] for the list of stories."""
    return [{"id": s["id"], "title": s["title"], "intro": s["intro"]} for s in stories or load()]


def story(conn, sid, stories=None):
    s = next((x for x in stories or load() if x["id"] == sid), None)
    if s is None:
        return None
    pl, bl = places(conn, s), buildings(conn, s)
    return {k: s[k] for k in ("id", "title", "intro", "series", "notes")} | {
        "events": events(s), "places": pl, "buildings": bl, "innovations": innovations(s),
        "people": people(conn, [p["id"] for p in pl] + [b["id"] for b in bl])}


def export(conn):
    """{index, stories: {id: story}} for the hosted copy."""
    st = load()
    return {"index": index(st), "stories": {s["id"]: story(conn, s["id"], st) for s in st}}


if __name__ == "__main__":
    from .db import connect
    problems = check()
    for p in problems:
        print("problem:", p)
    c = connect()
    for s in load():
        x = story(c, s["id"])
        print(f"{s['id']:8} events {len(x['events']):2}  places {len(x['places']):3}  buildings {len(x['buildings']):3}  "
              f"people {len(x['people']):2}  graphs {len(x['series'])}  notes {len(x['notes'])}")
    sys.exit(1 if problems else 0)
