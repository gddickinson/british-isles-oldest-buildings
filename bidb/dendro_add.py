"""Buildings dated by tree-ring before the cutoff that the catalogue lacks: python -m bidb.dendro_add [--dry-run]

Wikidata gives most listed buildings no construction date, so the build never sees medieval inns, houses and barns
whose timbers the Vernacular Architecture Group's database dates. Entries (felled before the cutoff) that bidb.dendro
could not match to a catalogue record are matched by the same rules (dendro.match) to Wikidata items within 400 m;
those items become records dated by their earliest felling date. The items found are kept in data/dendro_items.json
(qid -> VAG locations), which the build reads (`load`, `apply`) so a rebuild keeps them; this CLI adds them to an
existing database without a rebuild. Run bidb.dendro afterwards.
"""
import json
import re
import sys
import time
from collections import defaultdict

from . import dendro
from .classify import period_for
from .config import CUTOFF_YEAR, DATA_DIR
from .db import connect
from .http import sparql

ITEMS = DATA_DIR / "dendro_items.json"
RADIUS_KM = 0.4
SOURCE = "Tree-ring date (VAG Dendrochronology Database)"
CONFIDENCE = "Tree-ring dated"


def _nearby(lat, lon):
    """[(qid, English label, lat, lon)] of Wikidata items with coordinates within RADIUS_KM."""
    rows = sparql(f"""SELECT ?i ?l ?c WHERE {{
      SERVICE wikibase:around {{ ?i wdt:P625 ?c. bd:serviceParam wikibase:center "Point({lon:.4f} {lat:.4f})"^^geo:wktLiteral;
        wikibase:radius "{RADIUS_KM}". }}
      ?i rdfs:label ?l. FILTER(lang(?l) = "en") }}""")
    out = []
    for r in rows:
        m = re.match(r"Point\(([-\d.eE]+) ([-\d.eE]+)\)", r["c"]["value"])
        if m:
            out.append((r["i"]["value"].rsplit("/", 1)[-1], r["l"]["value"], float(m.group(2)), float(m.group(1))))
    return out


# stricter than the catalogue matcher, since a match here creates a record: every word of the item's name must be in
# the entry, house numbers must agree, and a barn, cottage, gate or chapel is not the house beside it
LOOSE = {"the", "of", "and", "at", "to", "on", "in", "st", "saint", "house", "farm", "farmhouse", "public", "hotel",
         "inn", "church", "chapel", "former", "range", "main"}
KINDS = {"barn", "cottage", "lych", "gate", "gatehouse", "dovecote", "stable", "granary", "lodge"}
OPPOSED = [{"east", "west", "north", "south"}, {"first", "second", "third", "1st", "2nd", "3rd"},
           {"upper", "lower", "nether"}, {"great", "little"}, {"old", "new"}]
NOT_BUILDINGS = re.compile(r"\b(street|road|lane|square|village|hamlet|town|civil parish|settlement|locality)\b")
# fittings date nothing about the walls round them: a bellframe may be older than its church (Woodham Walter's, 1382+,
# hangs in a church of c.1563)
NOT_FABRIC = re.compile(r"\b(chest|coffin|door|table|bench|cupboard|screen|reused|re-used|ex situ|bell-?frame|bell frame)\b",
                        re.I)
# reviewed matches that are another building (LD2b, 2026-10-29)
SKIP = {"Q26543967": "Watchbell House is 14-15 Watchbell Street, Rye; the VAG entry is 27-28 (Watchbell Chambers)"}


def _plain(text):
    words = re.findall(r"[a-z0-9]+", (text or "").lower().replace("'s", ""))
    return {w[:-1] if w.endswith("s") and len(w) > 4 else w for w in words}


def plausible(label, entry):
    """Can the Wikidata item called `label` be the building of this VAG entry?"""
    if NOT_FABRIC.search(entry["location"]):
        return False
    lw, ew = _plain(label), _plain(entry["location"])
    ln, en = {w for w in lw if w.isdigit()}, {w for w in ew if w.isdigit()}
    if ln and not ln & en:
        return False
    if any((lw & k) and (lw & k) != (ew & k) for k in OPPOSED):
        return False
    if (lw & KINDS) != (ew & KINDS):
        return False
    return not {w for w in lw - LOOSE - ln if len(w) > 1} - ew


def candidates(conn=None, cutoff=CUTOFF_YEAR, log=print):
    """{qid: [VAG entries]} for Wikidata items matched by tree-ring entries felled before the cutoff that no
    catalogue record matches (conn: the catalogue to compare with; None = every entry)."""
    known = set()
    if conn is not None and conn.execute("SELECT 1 FROM sqlite_master WHERE name = 'dendro'").fetchone():
        known = {r[0] for r in conn.execute("SELECT location FROM dendro")}
    todo = [e for e in dendro.entries() if e["felled_from"] < cutoff and e["location"] not in known]
    if conn is not None:
        grid = dendro._index(conn)
        todo = [e for e in todo if not dendro.match(e, grid)]
    groups = defaultdict(list)                    # entries a few metres apart share one query
    for e in todo:
        groups[round(e["lat"], 3), round(e["lon"], 3)].append(e)
    found, t0 = defaultdict(list), time.time()
    for n, ((lat, lon), es) in enumerate(groups.items(), 1):
        items = _nearby(lat, lon)
        for e in es:
            grid = defaultdict(list)
            for qid, label, ilat, ilon in items:
                if qid not in SKIP and plausible(label, e):
                    grid[round(ilat * 20), round(ilon * 20)].append((qid, label, ilat, ilon, dendro.tokens(label)))
            m = dendro.match(e, grid)
            if m:
                found[m[0]].append(e)
        if n % 100 == 0:
            log(f"  {n}/{len(groups)} places, {len(found)} items matched ({time.time() - t0:.0f}s)")
    log(f"tree-ring entries before {cutoff} not in the catalogue: {len(todo)}; matched to {len(found)} Wikidata items")
    return dict(found)


def save(found, names):
    data = {q: {"name": names.get(q), "entries": sorted(e["location"] for e in es)} for q, es in sorted(found.items())}
    ITEMS.write_text(json.dumps(data, indent=1, ensure_ascii=False) + "\n")


def load():
    """{qid: [VAG entries]} of the items added before (data/dendro_items.json)."""
    try:
        data = json.loads(ITEMS.read_text())
    except (OSError, ValueError):
        return {}
    by_loc = defaultdict(list)
    for e in dendro.entries():
        by_loc[e["location"]].append(e)
    return {q: [e for loc in v["entries"] for e in by_loc.get(loc, [])] for q, v in data.items()}


def year_of(entry):
    """Felling year: the year itself, or the middle of a range wider than ten years ("1315-15+20": 1300-1335)."""
    lo, hi = entry["felled_from"], entry["felled_to"]
    return lo if hi - lo <= 10 else (lo + hi) // 2


def date_fields(entries):
    """Date columns from the earliest felling date of a building's entries."""
    e = min(entries, key=lambda e: (year_of(e), e["felled_to"]))
    others = sorted({x["date_text"] for x in entries} - {e["date_text"]})
    text = f"{e['date_text']} (tree-ring)" + (f"; also {', '.join(others[:3])}" if others else "")
    return {"year_start": year_of(e), "date_text": text, "period": period_for(year_of(e)),
            "date_source": SOURCE, "date_confidence": CONFIDENCE,
            "date_evidence": f"{e['location']}: felled {e['date_text']} ({e['reference']})"}


def apply(records, found):
    """Date records that have no year, or a later one, from their tree-ring entries; returns how many."""
    n = 0
    for r in records:
        es = found.get(r["id"])
        if es and (r.get("year_start") is None or r["year_start"] > min(year_of(e) for e in es)):
            r.update(date_fields(es))
            n += 1
    return n


def run(dry_run=False, log=print):
    from .research_add import insert, records_for
    conn = connect()
    conn.execute("PRAGMA busy_timeout = 120000")
    found = candidates(conn, log=log)
    have = {q for q in found if conn.execute("SELECT 1 FROM buildings WHERE id = ?", (q,)).fetchone()}
    new = {q: None for q in found if q not in have}
    records = records_for(new, log, adjust=lambda rs: apply(rs, found)) if new else []
    records = [r for r in records if r.get("year_start") is not None and r["year_start"] < CUTOFF_YEAR
               and not NOT_BUILDINGS.search((r.get("classes") or "").lower())]
    for r in sorted(records, key=lambda r: r["year_start"]):
        log(f"  {r['id']:11} {r['year_start']:5} {r['name'][:50]} ({(r.get('locality') or '')[:40]})")
    log(f"{len(records)} buildings to add; {len(have)} matched items already in the catalogue (not changed)")
    if not dry_run and records:
        insert(conn, records)
        kept = {**load(), **{r["id"]: found[r["id"]] for r in records}}
        save(kept, {**{q: v.get("name") for q, v in _saved().items()}, **{r["id"]: r["name"] for r in records}})
        log(f"added {len(records)} records ({ITEMS.name}: {len(kept)} items)")
    return records


def _saved():
    try:
        return json.loads(ITEMS.read_text())
    except (OSError, ValueError):
        return {}


if __name__ == "__main__":
    if set(sys.argv[1:]) - {"--dry-run"}:           # anything else would add records without being asked
        sys.exit("usage: python -m bidb.dendro_add [--dry-run]")
    run(dry_run="--dry-run" in sys.argv[1:])
