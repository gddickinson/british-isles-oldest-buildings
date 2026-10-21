"""Build stage / CLI: "On this day" -> table `on_this_day`.

    python -m bidb.on_this_day            fetch (cached) and write the table
    python -m bidb.on_this_day 10-14      what happened on 14 October

Dates known to the day on Wikidata: births and deaths of the people linked to the catalogue
(P569/P570), battles and other events among the places (P585 point in time, P580 start), and
buildings consecrated, opened or founded on a known day (P571 inception, P1619 official opening).
"""
import sys
import time

from .db import connect
from .http import sparql

COLUMNS = ["month", "day", "year", "what", "entity_kind", "entity_id", "name"]
WHAT = {"P569": "born", "P570": "died", "P585": "battle or event", "P580": "began", "P571": "founded or built",
        "P1619": "opened"}


JULIAN = "Q1985786"


def gregorian_to_julian(y, m, d):
    """Proleptic Gregorian date -> Julian calendar date (via the Julian day number)."""
    a = (14 - m) // 12
    yy, mm = y + 4800 - a, m + 12 * a - 3
    jdn = d + (153 * mm + 2) // 5 + 365 * yy + yy // 4 - yy // 100 + yy // 400 - 32045
    c = jdn + 32082
    dd = (4 * c + 3) // 1461
    e = c - 1461 * dd // 4
    mo = (5 * e + 2) // 153
    return dd - 4800 + mo // 10, mo + 3 - 12 * (mo // 10), e - (153 * mo + 2) // 5 + 1


def _days(qids, props, kind, log, chunk=250):
    """[(month, day, year, what, kind, qid)] for statements with day precision (11)."""
    out, ids = [], sorted({q for q in qids if q and q.startswith("Q")})
    values_p = " ".join(f"(p:{p} psv:{p} \"{p}\")" for p in props)
    for i in range(0, len(ids), chunk):
        values = " ".join("wd:" + q for q in ids[i:i + chunk])
        rows = sparql(f"""SELECT ?i ?t ?cal ?prop WHERE {{ VALUES ?i {{ {values} }}
            VALUES (?pp ?psv ?prop) {{ {values_p} }}
            ?i ?pp ?st . ?st ?psv ?v . ?v wikibase:timePrecision 11 ; wikibase:timeValue ?t ;
            wikibase:timeCalendarModel ?cal . }}""")
        for r in rows:
            t = r["t"]["value"]                       # always proleptic Gregorian in the query service
            neg = t.startswith("-")
            y, m, d = (int(x) for x in t.lstrip("-+").split("T")[0].split("-"))
            y = -y if neg else y
            if r["cal"]["value"].endswith(JULIAN):    # dated in the Julian calendar: give that date
                y, m, d = gregorian_to_julian(y, m, d)
            out.append((m, d, y, WHAT[r["prop"]["value"]], kind, r["i"]["value"].rsplit("/", 1)[-1]))
        if (i // chunk) % 20 == 0:
            log(f"  {kind}: {min(i + chunk, len(ids))}/{len(ids)}")
    return out


def run(log=print):
    t0 = time.time()
    say = lambda m: log(f"[{time.time() - t0:6.0f}s] {m}")
    conn = connect()
    conn.execute("PRAGMA busy_timeout = 120000")
    names = {}
    people = [(i, n) for i, n in conn.execute("SELECT id, name FROM persons")]
    places = [(w, i, n) for w, i, n in conn.execute(
        "SELECT wikidata_id, id, name FROM places WHERE wikidata_id IS NOT NULL")]
    builds = [(w or i, i, n) for w, i, n in conn.execute("SELECT wikidata_id, id, name FROM buildings")]
    for i, n in people:
        names[("person", i)] = (i, n)
    rows = _days([i for i, _ in people], ["P569", "P570"], "person", say)
    place_of = {w: (i, n) for w, i, n in places}
    rows += _days(place_of, ["P585", "P580"], "place", say)
    build_of = {w: (i, n) for w, i, n in builds}
    rows += _days(build_of, ["P571", "P1619"], "building", say)
    out = []
    for m, d, y, what, kind, qid in rows:
        rid, name = (qid, names.get(("person", qid), ("", ""))[1]) if kind == "person" else \
            (place_of if kind == "place" else build_of).get(qid, ("", ""))
        if rid and name:
            out.append((m, d, y, what, kind, rid, name))
    out = sorted(set(out))
    conn.executescript(f"""DROP TABLE IF EXISTS on_this_day;
        CREATE TABLE on_this_day ({", ".join(c + (" INTEGER" if c in ("month", "day", "year") else " TEXT")
                                             for c in COLUMNS)});
        CREATE INDEX idx_otd ON on_this_day(month, day);""")
    conn.executemany(f"INSERT INTO on_this_day VALUES ({', '.join('?' for _ in COLUMNS)})", out)
    conn.commit()
    say(f"wrote {len(out)} dated events ({sum(1 for r in out if r[4] == 'person')} people, "
        f"{sum(1 for r in out if r[4] == 'place')} places, {sum(1 for r in out if r[4] == 'building')} buildings)")


def for_day(conn, month, day, limit=60):
    """What happened on this day, oldest first (people only when few other events)."""
    if not conn.execute("SELECT 1 FROM sqlite_master WHERE name = 'on_this_day'").fetchone():
        return []
    rows = [dict(zip(COLUMNS, r)) for r in conn.execute(
        f"SELECT {', '.join(COLUMNS)} FROM on_this_day WHERE month = ? AND day = ? ORDER BY year", (month, day))]
    events = [r for r in rows if r["entity_kind"] != "person"]
    people = [r for r in rows if r["entity_kind"] == "person"]
    return (events + people)[:limit]


if __name__ == "__main__":
    if len(sys.argv) > 1:
        m, d = (int(x) for x in sys.argv[1].split("-"))
        for r in for_day(connect(), m, d):
            print(r["year"], r["what"], r["name"])
    else:
        run()
