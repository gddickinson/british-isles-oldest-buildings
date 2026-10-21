"""Build stage / CLI: a timeline for each building -> table `timeline`.

    python -m bidb.timeline            from the cached full articles (bidb.stories), no downloads
    python -m bidb.timeline Q1529151   show one building's timeline

Dated sentences of the building's own Wikipedia article that say something happened to it
(built, rebuilt, enlarged, besieged, burned, dissolved, sold, restored, opened, closed …), one
event per year and kind, at most MAX_EVENTS per building, earliest first.
"""
import re
import sys
import time

from .date_mining import candidates
from .db import connect
from .pron_sources import load_store
from .stories import STORE
from .stories_parse import SKIP_SECTIONS, _sentences

COLUMNS = ["entity_id", "year", "kind", "label", "text"]
# kind -> words (first match wins: order matters)
EVENTS = [
    ("destroyed", r"destroyed|demolished|burn(?:ed|t) down|razed|slighted|pulled down|collapsed"),
    ("war", r"besieged|siege|captured|attacked|stormed|sacked|garrisoned|surrendered|bombed"),
    ("dissolved", r"dissolved|dissolution|suppressed"),
    ("fire", r"\bfire\b|burned(?! at the stake)|burnt(?! at the stake)"),
    ("restored", r"restored|restoration|repaired|renovated|refurbished|conserved"),
    ("rebuilt", r"rebuilt|reconstructed|remodell?ed|altered|refaced|re-?roofed"),
    ("enlarged", r"enlarged|extended|added|extension|new wing|heightened"),
    ("built", r"\bbuilt|constructed|erected|completed|begun|founded|established|consecrated|raised"),
    ("owners", r"sold|bought|purchased|inherited|granted|acquired|passed to|bequeathed"),
    ("opened", r"opened|reopened|open to the public|museum"),
    ("closed", r"closed|abandoned|ruinous|fell into (?:ruin|disrepair)|deserted|disused"),
    ("listed", r"listed|scheduled|designated|guardianship|taken into state care|National Trust|English Heritage"),
    ("visit", r"visited|stayed|entertained|imprisoned|held prisoner|died at|born at|married"),
]
EVENT_RE = [(k, re.compile(r"\b(?:" + p + r")", re.I)) for k, p in EVENTS]
LABEL = {"destroyed": "Destroyed", "war": "War and siege", "dissolved": "Dissolved", "fire": "Fire",
         "restored": "Restored", "rebuilt": "Rebuilt", "enlarged": "Enlarged", "built": "Built or founded",
         "owners": "Changed hands", "opened": "Opened", "closed": "Closed or abandoned", "listed": "Protected",
         "visit": "Visitors and residents"}
MAX_EVENTS = 14
FIRST = re.compile(r"\b(?:first|originally|initially) (?:built|constructed|erected|founded)", re.I)


def events(entry):
    """Cached article entry -> [(year, kind, sentence)] (one per year and kind)."""
    out, seen = [], set()
    for heading, body in entry.get("s", []):
        if SKIP_SECTIONS.match(heading or ""):
            continue
        for s in _sentences(body):
            if len(s) > 400:
                continue
            kind = "built" if FIRST.search(s) else next((k for k, pat in EVENT_RE if pat.search(s)), None)
            if not kind or (kind == "listed" and not re.search(r"\b1[89]\d\d|\b20\d\d", s)):
                continue
            years = [y for y, label in candidates(s) if -4000 < y <= 2030]
            if not years:
                continue
            y = min(years)
            if (y, kind) in seen:
                continue
            seen.add((y, kind))
            out.append((y, kind, s))
    out.sort()
    if len(out) > MAX_EVENTS:                     # keep the spread: first, last and evenly between
        step = (len(out) - 1) / (MAX_EVENTS - 1)
        out = [out[round(i * step)] for i in range(MAX_EVENTS)]
    return out


def run(log=print):
    t0 = time.time()
    conn = connect()
    conn.execute("PRAGMA busy_timeout = 120000")
    store = load_store(STORE)
    rows = []
    for bid, title in conn.execute("SELECT id, wikipedia_title FROM buildings WHERE coalesce(wikipedia_title, '') != ''"):
        for y, kind, text in events(store.get(title) or {}):
            rows.append((bid, y, kind, LABEL[kind], text))
    conn.executescript(f"""DROP TABLE IF EXISTS timeline;
        CREATE TABLE timeline ({", ".join(c + (" INTEGER" if c == "year" else " TEXT") for c in COLUMNS)});
        CREATE INDEX idx_timeline ON timeline(entity_id);""")
    conn.executemany(f"INSERT INTO timeline VALUES ({', '.join('?' for _ in COLUMNS)})", rows)
    conn.commit()
    log(f"[{time.time() - t0:5.0f}s] wrote {len(rows)} timeline events for "
        f"{len({r[0] for r in rows})} buildings")


def for_record(conn, rid):
    if not conn.execute("SELECT 1 FROM sqlite_master WHERE name = 'timeline'").fetchone():
        return []
    return [dict(zip(COLUMNS, r)) for r in conn.execute(
        f"SELECT {', '.join(COLUMNS)} FROM timeline WHERE entity_id = ? ORDER BY year", (rid,))]


if __name__ == "__main__":
    if len(sys.argv) > 1:
        for e in for_record(connect(), sys.argv[1]):
            print(e["year"], e["label"], "|", e["text"][:140])
    else:
        run()
