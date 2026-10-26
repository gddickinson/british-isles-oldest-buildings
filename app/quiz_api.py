"""Quiz material: /api/quiz (photographed buildings with a well-supported date) and /api/quiz_pool (names
to pronounce, stories, history events, the researched oldest lists). The questions are made in the browser
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
    """Entries of the researched oldest lists with a year: name, list, category, age, place."""
    from bidb.oldest_lists import LISTS, entries
    return [{"list": spec["title"], "category": e["category"], "name": e["name"], "age": e.get("age_text"),
             "year": e["year"], "location": e.get("location"), "claim": e.get("claim"), "verdict": e.get("verdict")}
            for name, spec in LISTS.items() for e in entries(name) if isinstance(e.get("year"), int)]


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
    return out


def pool(db):
    return {"pron": pronunciations(db), "stories": stories(db), "history": history(), "lists": oldest_lists(),
            "firsts": firsts()}
