"""Quiz material: /api/quiz (photographed buildings with a well-supported date) and /api/quiz_pool (names
to pronounce, stories, history events, the researched oldest lists and oldest things, building types, materials). The questions are made in the browser
(static/quiz_kinds.js); `pool` is also written to data/quiz.json for the hosted copy (static_tours.py).
"""
import json
import re
from difflib import SequenceMatcher

from flask import Blueprint, jsonify, request

from bidb.config import DATA_DIR

from .common import conn

bp = Blueprint("quiz", __name__)
BUILDING_COLS = ("id", "name", "year_start", "date_text", "period", "category", "category_group", "locality",
                 "county", "nation")


@bp.route("/api/quiz")
def quiz():
    """Random buildings with a photo and a well-supported date."""
    n = min(int(request.args.get("n", 10)), 120)
    rows = conn().execute(f"""SELECT {", ".join(BUILDING_COLS)}, image_thumb FROM buildings
        WHERE image_thumb IS NOT NULL AND year_start IS NOT NULL AND period != 'Unknown'
        AND date_check IN ('Corroborated', 'Referenced', 'Reviewed') ORDER BY random() LIMIT ?""", (n,)).fetchall()
    return jsonify([dict(r) for r in rows])


@bp.route("/api/quiz_pool")
def quiz_pool():
    return jsonify(pool(conn()))


def surprising(name, respell):
    """True when a name is not said the way it is spelt (the respelling differs from the letters)."""
    letters = re.sub(r"[^a-z]", "", name.lower())
    said = re.sub(r"[^a-z]", "", respell.lower())
    return bool(letters) and bool(said) and SequenceMatcher(None, letters, said).ratio() < 0.72


def pronunciations(db):
    """Names whose English respelling surprises: name, respelling, IPA, recording, record."""
    out, seen = [], set()
    for r in db.execute("""SELECT name, respell, ipa, audio, entity_id, entity_kind FROM pronunciations
            WHERE lang = 'en' AND respell != '' AND respell NOT LIKE '%,%' AND respell NOT LIKE '%…%'
            AND respell NOT LIKE '%''%' ORDER BY name"""):
        whole = len(re.split(r"[\s-]+", r["name"])) == len(r["respell"].split())     # the respelling covers the name
        if r["name"] not in seen and whole and len(r["name"]) <= 30 and surprising(r["name"], r["respell"]):
            seen.add(r["name"])
            out.append({"name": r["name"], "respell": r["respell"], "ipa": r["ipa"], "audio": r["audio"] or None,
                        "id": r["entity_id"], "kind": r["entity_kind"]})
    return out


def stories(db, per_kind=120):
    """Stories that name the place they are told of (so the name can be hidden): text, kind and the record."""
    out = []
    for kind in ("supernatural", "legend", "folklore", "curiosity"):
        for r in db.execute("""SELECT s.entity_id, s.kind, s.text, COALESCE(b.name, p.name) AS name,
                COALESCE(b.nation, p.nation) AS nation FROM stories s
                LEFT JOIN buildings b ON b.id = s.entity_id LEFT JOIN places p ON p.id = s.entity_id
                WHERE s.kind = ? AND length(s.text) BETWEEN 120 AND 700 ORDER BY random()""", (kind,)):
            short = re.split(r",| \(", r["name"] or "")[0].strip()
            if short and len(short) > 3 and short.lower() in r["text"].lower():
                out.append({"id": r["entity_id"], "kind": r["kind"], "name": r["name"], "short": short,
                            "nation": r["nation"], "text": r["text"]})
                if sum(1 for x in out if x["kind"] == kind) >= per_kind:
                    break
    return out


def history():
    try:
        events = json.loads((DATA_DIR / "curated" / "history.json").read_text())["events"]
    except (FileNotFoundError, ValueError, KeyError):
        return []
    return [{k: e.get(k) for k in ("year", "date_text", "title", "description", "region", "source")}
            for e in events if e.get("year") is not None]


def oldest_lists():
    """Entries of the researched oldest lists and of the oldest things (/things) with a year: name, list, category,
    age, place."""
    from bidb.oldest_lists import LISTS, entries
    out = [{"list": spec["title"], "category": e["category"], "name": e["name"], "age": e.get("age_text"),
            "year": e["year"], "location": e.get("location"), "claim": e.get("claim"), "verdict": e.get("verdict")}
           for name, spec in LISTS.items() for e in entries(name) if isinstance(e.get("year"), int)]
    return out + [{"list": f"Oldest things: {t['theme_title']}", "category": t["category"], "name": t["name"],
                   "age": t["age"], "year": t["year"], "location": t["where"], "claim": t["claim"],
                   "verdict": t["verdict"]} for t in things()]


def things():
    """The oldest things (bidb.oldest_things) for the quiz "Oldest things" and "Which came first?"."""
    from bidb.oldest_things import THEMES, entries, entry_id
    return [{"id": entry_id(t, e), "theme": t, "theme_title": spec["title"], "category": e["category"], "name": e["name"],
             "age": e["age_text"], "year": e["year"], "claim": e["claim"], "verdict": e["verdict"],
             "where": (e.get("where") or {}).get("name")}
            for t, spec in THEMES.items() for e in entries(t) if isinstance(e.get("year"), int)]


def firsts():
    """Innovations (C6) and the laws and institutions of the trades (C7) with a year, for "Which came first?"."""
    from bidb.oldest_lists import entries
    out = [{"title": e["name"], "year": e["year"], "what": "Innovation", "text": e.get("claim"), "where": e.get("location")}
           for e in entries("innovations") if isinstance(e.get("year"), int)]
    try:
        events = json.loads((DATA_DIR / "curated" / "change" / "events.json").read_text())
    except (FileNotFoundError, ValueError):
        events = []
    out += [{"title": e["title"], "year": e["year"], "what": "Law or institution", "text": e.get("text"), "where": None}
            for e in events if e.get("topic") == "law"]
    # the oldest things since the Romans (older ones are years apart from anything else and too easy)
    out += [{"title": t["name"], "year": t["year"], "what": t["theme_title"], "text": t["claim"], "where": t["where"],
             "page": "things"} for t in things() if t["year"] >= 43]
    return out


def types(db, per_type=4, data=None):
    """Building types (BT7): isles types with a first known date, for "Which type came first?", and photographed
    catalogue records of each type (their main type), for "Name the type"."""
    from bidb import building_types
    data = data or building_types.load()
    kinds = [{"id": t["id"], "name": t["name"], "domain": t["domain"], "family": t["family"],
              "year": (t.get("period") or {}).get("from")} for t in data["types"] if not t.get("abroad")]
    known = {t["id"] for t in kinds}
    photos, n = [], {}
    for r in db.execute("""SELECT b.id, b.name, b.image_thumb, b.nation, t.type_id FROM type_map t
            JOIN buildings b ON b.id = t.entity_id WHERE t.source = 'building' AND t.is_primary = 1
            AND b.image_thumb IS NOT NULL ORDER BY random()"""):
        if r["type_id"] in known and n.get(r["type_id"], 0) < per_type:
            n[r["type_id"]] = n.get(r["type_id"], 0) + 1
            photos.append(dict(r))
    return {"kinds": kinds, "photos": photos}


# the groups a building is built of, walls first (a record's question asks about its walling when it has one), for
# "What is it built of?"; windows and glass left out
BUILT_OF = ("Stone", "Brick and tile", "Timber", "Earth", "Concrete", "Iron and steel", "Roofs", "Mortar and render")


def materials(db, per_material=6, data=None):
    """Materials (BT3) of photographed catalogue records, found in the register text or on Wikidata (not the looser
    Wikipedia sentences), for "What is it built of?": materials with their group and the materials related to each
    by a family link (never offered as a wrong answer), and records with all their materials and one evidence."""
    from bidb import building_materials
    data = data or building_materials.load()
    kinds = {m["id"]: {"id": m["id"], "name": m["name"], "group": m["group"], "kind": m.get("kind")} for m in data["materials"]
             if m["group"] in BUILT_OF}
    related = {}
    for ln in data["links"]:
        related.setdefault(ln["from"], set()).add(ln["to"])
        related.setdefault(ln["to"], set()).add(ln["from"])
    recs = {}
    for r in db.execute("""SELECT b.id, b.name, b.image_thumb, b.nation, m.material_id, m.via, m.evidence
            FROM material_map m JOIN buildings b ON b.id = m.entity_id WHERE m.source = 'building'
            AND b.image_thumb IS NOT NULL ORDER BY random()"""):
        rec = recs.setdefault(r["id"], {"id": r["id"], "name": r["name"], "image_thumb": r["image_thumb"],
                                        "nation": r["nation"], "all": set(), "found": {}})
        rec["all"].add(r["material_id"])
        if r["via"] != "wikipedia" and r["material_id"] in kinds:
            rec["found"].setdefault(r["material_id"], (r["via"], (r["evidence"] or "")[:200]))
    photos, n = [], {}
    rank = {m: BUILT_OF.index(k["group"]) for m, k in kinds.items()}
    for rec in recs.values():
        for mid, (via, ev) in sorted(rec["found"].items(), key=lambda x: rank[x[0]]):
            if n.get(mid, 0) < per_material:
                n[mid] = n.get(mid, 0) + 1
                photos.append({"id": rec["id"], "name": rec["name"], "image_thumb": rec["image_thumb"],
                               "nation": rec["nation"], "material": mid, "via": via, "evidence": ev,
                               "all": sorted(rec["all"])})
                break
    used = {p["material"] for p in photos}
    return {"kinds": [k | {"related": sorted(related.get(k["id"], ()))} for k in kinds.values()],
            "photos": [p for p in photos if p["material"] in used]}


def pool(db):
    return {"pron": pronunciations(db), "stories": stories(db), "history": history(), "lists": oldest_lists(),
            "firsts": firsts(), "types": types(db), "things": things(), "materials": materials(db)}
