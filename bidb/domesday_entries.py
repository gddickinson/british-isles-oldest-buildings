"""Research track R4 / CLI: what Domesday Book says about a settlement -> table `domesday_entries`.

    python -m bidb.domesday_entries           fetch the entries of settlements with a church, abbey or cathedral
    python -m bidb.domesday_entries --report  pre-1100 religious records: church or priest recorded in 1086?

Open Domesday (Anna Powell-Smith, CC BY-SA) place pages give each settlement's entry: households
(including priests), resources (including churches), the Phillimore reference. Pages are fetched for
the settlements of the catalogue's churches, abbeys and cathedrals (`domesday` table, bidb.domesday)
and cached; one row per settlement: churches, priests, households, Phillimore reference(s).
"""
import json
import re
import sys
import time

from .db import connect
from .http import request_json

PAGE = "https://opendomesday.org/place/{}/"
RELIGIOUS = ("Church / chapel", "Abbey / monastery", "Cathedral")
COLUMNS = ["od_id", "churches", "priests", "households", "phillimore"]


def _num(pattern, text):
    return sum(float(n) for n in re.findall(pattern, text))


def parse(page):
    """Counts from a place page's entries (several manors on one page are added together; shares such as
    "0.5 church" kept, "church lands" and the notes' "1/4 church" not counted)."""
    text = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", page, flags=re.S | re.I)))
    if "Domesday" not in text:
        return None
    hh = re.search(r"recorded population of ([\d.]+) households", text)
    return {"churches": _num(r"(?<![\d/.])(\d+(?:\.\d+)?) (?:churches|church)\b(?! lands?\b)", text),
            "priests": _num(r"(?<![\d/.])(\d+(?:\.\d+)?) priests?\b", text),
            "households": float(hh.group(1)) if hh else None,
            "phillimore": "; ".join(dict.fromkeys(re.findall(r"Phillimore reference : ([^»]+?) View on page", text))) or None}


def fetch(od_id):
    return request_json(PAGE.format(od_id), extract=parse, min_interval=1.0)


def settlements(conn):
    return [r[0] for r in conn.execute(
        f"SELECT DISTINCT d.od_id FROM domesday d JOIN buildings b ON b.id = d.entity_id WHERE b.category IN "
        f"({', '.join('?' for _ in RELIGIOUS)}) AND d.od_id IS NOT NULL ORDER BY d.od_id", RELIGIOUS)]


def run(log=print):
    t0 = time.time()
    conn = connect()
    conn.execute("PRAGMA busy_timeout = 120000")
    rows = []
    ids = settlements(conn)
    for i, od in enumerate(ids):
        try:
            got = fetch(od)
        except Exception as exc:                  # one missing page should not stop the rest
            log(f"  {od}: {exc}")
            continue
        if got:
            rows.append((od, got["churches"], got["priests"], got["households"], got["phillimore"]))
        if i % 200 == 0:
            log(f"  {i}/{len(ids)} settlements")
    conn.execute("DROP TABLE IF EXISTS domesday_entries")
    conn.execute(f"CREATE TABLE domesday_entries ({', '.join(COLUMNS)})")
    conn.execute("CREATE INDEX domesday_entries_od ON domesday_entries(od_id)")
    conn.executemany(f"INSERT INTO domesday_entries VALUES ({', '.join('?' for _ in COLUMNS)})", rows)
    conn.commit()
    log(f"[{time.time() - t0:5.0f}s] Domesday entries: {len(rows)} of {len(ids)} settlements; "
        f"{sum(1 for r in rows if r[1] or r[2])} with a church or priest")


def entry(conn, od_id):
    if not od_id or not conn.execute("SELECT 1 FROM sqlite_master WHERE name = 'domesday_entries'").fetchone():
        return None
    r = conn.execute(f"SELECT {', '.join(COLUMNS)} FROM domesday_entries WHERE od_id = ?", (od_id,)).fetchone()
    return dict(zip(COLUMNS, r)) if r else None


def report():
    """Religious records dated before 1100 or 1086-1200 in a Domesday settlement: church/priest recorded?"""
    conn = connect()
    rows = conn.execute(
        "SELECT b.id, b.name, b.year_start, d.settlement, d.itself, e.churches, e.priests FROM buildings b "
        "JOIN domesday d ON d.entity_id = b.id JOIN domesday_entries e ON e.od_id = d.od_id "
        f"WHERE b.category IN ({', '.join('?' for _ in RELIGIOUS)}) AND b.year_start < 1200", RELIGIOUS).fetchall()
    early = [r for r in rows if r[2] < 1086]
    later = [r for r in rows if r[2] >= 1086 and (r[5] or r[6])]
    print(f"{len(early)} religious records dated before 1086 in a Domesday settlement: "
          f"{sum(1 for r in early if r[5] or r[6])} with a church or priest recorded")
    print(f"{len(later)} dated 1086-1199 where Domesday already records a church or priest (an earlier church on the site?)")
    for r in sorted(later, key=lambda r: r[2])[:40]:
        print(f"  {r[2]:5} {r[1][:45]:45} {r[3]}: {r[5]:g} church(es), {r[6]:g} priest(s)")


if __name__ == "__main__":
    report() if sys.argv[1:] == ["--report"] else run()
