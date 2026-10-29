"""Catalogue records whose NHLE list entry (Wikidata P1216) is that of an outbuilding (found with Ormesby Hall,
whose Wikidata NHLE id is the stable block's).

    python -m bidb.nhle_check           -> runs/nhle_check.json and a summary
    python -m bidb.nhle_check --apply   write the reviewed corrections to an existing database

Reviewed corrections (data/curated/nhle_corrections.json: the right list entry, what Wikidata gave, why) are
applied in the build (postprocess.finalise, `apply`) before the record's references are made.

Each record's list entry name is read from Historic England's open NHLE layers (Listed Building points, then
Scheduled Monuments, the parks and gardens, battlefields, wrecks and World Heritage Sites; OGL), cached like every
download. A record is flagged when the head of the entry's name (before the first comma, "and", "with",
"including"...: "Church of St Mary and attached railings" is the church) has an outbuilding word (stables, lodge,
gate piers, garden wall...) that the record's own name does not, e.g. "Ormesby Hall" -> "Stableblock, circa 80 metres north-east of Ormesby Hall".
"""
import json
import re
from collections import Counter

from .config import DATA_DIR, ROOT
from .http import request_json
from .registers import HE

OUT = ROOT / "runs" / "nhle_check.json"
CORRECTIONS = DATA_DIR / "curated" / "nhle_corrections.json"
LAYERS = (0, 6, 7, 8, 9, 10)       # listed buildings, scheduled monuments, parks and gardens, battlefields, wrecks, World Heritage
BATCH = 150
PART = re.compile(r"\b(stables?|stable ?blocks?|stable buildings?|coach ?houses?|coach-houses?|lodges?|gate ?piers?|"
                  r"walls?|railings?|outbuildings?|barns?|dovecote?s?|summer ?houses?|ha-?ha|boundary|"
                  r"service (?:wing|range)|kitchen garden|orangery|ice ?house|brewhouse|laundry|"
                  r"granary|cart ?shed|pigsty|kennels?|steps|terraces?|sundial|headstones?|"
                  r"telephone kiosk|pump|wings?)\b", re.I)
# the head of an entry's name ends where its extras or its locator begin ("... 700m south of Claridges Barn")
HEAD_END = re.compile(r"[,;:(.]|\b(?:and|with|including|incl|adjoining|attached|together|of|at|near|to|on|in|"
                      r"about|approximately|circa|\d+ ?m|\d+ metres)\b", re.I)
# whose list entry may well be its walls: a castle's curtain wall, a ruin's standing wall
WALLED = {"Castle / fortification", "Abbey / monastery", "Roman structure", "Prehistoric monument",
          "Ruin / archaeological site"}

# flagged, read and found right: the record is what the entry lists
KEPT = {
    "Q17528410": "Charlecote Park outbuildings: the entry is the laundry, brewhouse, stables and coach house",
    "Q17529252": "Old Cloth Hall (Newbury): the hall is its east and west wings",
    "Q5877115": "Hogarth's House: the house's own entry, with its wall and gate",
    "Q7458558": "Sexey's Hospital: its Grade I entry (west wing with chapel); no other entry nearby names it",
    "Q7494494": "Shepherd Gate Clock: the clock is set in the observatory wall the entry lists",
    "Q8001075": "Wilder's Folly: \"a folly and dovecote\" (its article), listed as the dovecote east of Nunhide Manor",
}


def names(ids, log=print):
    """{list entry number: (name, layer)} for the given NHLE ids."""
    out, todo = {}, sorted({str(i) for i in ids if str(i).isdigit()})
    for layer in LAYERS:
        for k in range(0, len(todo), BATCH):
            chunk = todo[k:k + BATCH]
            res = request_json(f"{HE}/{layer}/query", min_interval=1.1, params={
                "where": f"ListEntry IN ({','.join(chunk)})", "outFields": "ListEntry,Name",
                "returnGeometry": "false", "f": "json"})
            for f in res.get("features", []):
                a = f["attributes"]
                out[str(a["ListEntry"])] = (a.get("Name") or "", layer)
        todo = [i for i in todo if i not in out]
        log(f"  layer {layer}: {len(out)} named, {len(todo)} left")
    return out


def _words(s):
    return {re.sub(r"[ -]|s$", "", m.group(0).lower()).replace("dovecote", "dovecot") for m in PART.finditer(s or "")}


def head(entry):
    """What the list entry is of: its name up to the first comma, "and", "with", "including"..."""
    return HEAD_END.split(entry or "", 1)[0].strip()


def flag(name, entry, category=None):
    """Outbuilding words of the head of the list entry's name that the record's name lacks (empty: entry fits)."""
    words = _words(head(entry)) - _words(name)
    return sorted(words - {"wall"} if category in WALLED else words)


def corrections():
    try:
        return json.loads(CORRECTIONS.read_text())
    except (OSError, ValueError):
        return {}


def apply(records):
    """The reviewed list entries on freshly built records, in place -> how many were corrected."""
    fixes, n = corrections(), 0
    for r in records:
        if r["id"] in fixes:
            r["nhle_id"] = fixes[r["id"]]["nhle_id"]
            n += 1
    return n


def apply_to_db(log=print):
    """The reviewed list entries on an existing database, with each record's source links made again."""
    from .db import connect
    from .references import sources
    conn = connect()
    conn.execute("PRAGMA busy_timeout = 120000")
    conn.row_factory = __import__("sqlite3").Row
    n = 0
    for q, e in corrections().items():
        row = conn.execute("SELECT * FROM buildings WHERE id = ?", (q,)).fetchone()
        if row:
            r = dict(row, nhle_id=e["nhle_id"])
            conn.execute("UPDATE buildings SET nhle_id = ?, sources = ? WHERE id = ?",
                         (e["nhle_id"], json.dumps(sources(r), ensure_ascii=False), q))
            n += 1
    conn.commit()
    log(f"applied {n} reviewed NHLE list entries")


def run(log=print):
    from .db import connect
    conn = connect()
    rows = conn.execute("SELECT id, name, nhle_id, category FROM buildings WHERE nhle_id IS NOT NULL").fetchall()
    found, fixes = names([r[2] for r in rows], log), corrections()
    flagged, missing = [], []
    for rid, name, nhle, category in rows:
        if str(nhle) not in found:
            missing.append({"id": rid, "name": name, "nhle_id": nhle})
            continue
        entry, layer = found[str(nhle)]
        words = flag(name, entry, category)
        if words and rid not in fixes and rid not in KEPT:
            flagged.append({"id": rid, "name": name, "category": category, "nhle_id": nhle,
                            "entry": entry, "layer": layer, "words": words})
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(json.dumps({"checked": len(rows), "flagged": flagged, "missing": missing},
                              indent=1, ensure_ascii=False))
    log(f"{len(rows)} records with an NHLE id; {len(missing)} not in the open layers; {len(flagged)} flagged → {OUT}")
    log("  words: " + ", ".join(f"{w} {n}" for w, n in Counter(w for f in flagged for w in f["words"]).most_common(15)))
    return flagged


if __name__ == "__main__":
    import sys
    apply_to_db() if "--apply" in sys.argv else run()
