"""People of the guilds, companies, banks, exchanges, inns and shops (roadmap C3c): python -m bidb.trade_people

The people stage of bidb.places_build runs before bidb.trade_works and bidb.oldest_lists add the Markets & trade
places, so this stage links their people afterwards, from Wikidata:
  the place roles of bidb.people (founded, owner, architect, occupant, lived, died, buried…), and for
  organisations three more:
    Member                        person member of (P463) the company, guild or exchange
    Worked for                    person employer (P108)
    Master, governor or officer   person holding a position (P39) of the organisation (the position's P2389
                                  organisation directed, P642 of or P361 part of: Master of the Drapers,
                                  Governor of the Bank of England, Master Cutler); the organisation's
                                  chairperson (P488), chief executive (P169), director/manager (P1037),
                                  board member (P3320)
Market towns, and places recorded on a settlement's item, are left out: being born in a town or its
mayor is not a link with its trade.
Re-running replaces this stage's links (place targets of the group); people already in the table are kept.

    org_links(targets)   [(person, target, role)] for the organisation roles
    run()                links, people and their references written to persons / person_links
"""
import sys
import time

from . import people
from .http import sparql

GROUP = "Markets & trade"
SKIP_KINDS = ("tr_town",)
SETTLEMENT = "Q486972"
MEMBER, WORKED, OFFICER = "Member", "Worked for", "Master, governor or officer"
PERSON_PROPS = {"P463": MEMBER, "P108": WORKED}
HEAD_PROPS = ("P488", "P169", "P1037", "P3320")
POSITION_OF = ("P2389", "P642", "P361")


def _q(uri):
    return uri.rsplit("/", 1)[-1]


def org_links(targets, log=print):
    """[(person qid, target qid, role)] for membership, employment and offices of the target organisations."""
    links = set()
    p2t = " ".join("wdt:" + p for p in PERSON_PROPS)
    heads = " ".join("wdt:" + p for p in HEAD_PROPS)
    of = "|".join("wdt:" + p for p in POSITION_OF)
    targets = sorted(t for t in targets if t.startswith("Q"))
    for i in range(0, len(targets), 300):
        values = " ".join("wd:" + q for q in targets[i:i + 300])
        for r in sparql(f"""SELECT ?p ?t ?prop WHERE {{ VALUES ?t {{ {values} }} VALUES ?prop {{ {p2t} }}
                ?p ?prop ?t . ?p wdt:P31 wd:Q5 . }}"""):
            links.add((_q(r["p"]["value"]), _q(r["t"]["value"]), PERSON_PROPS[_q(r["prop"]["value"])]))
        for r in sparql(f"""SELECT DISTINCT ?p ?t WHERE {{ VALUES ?t {{ {values} }}
                {{ ?pos {of} ?t . ?p wdt:P39 ?pos . }} UNION {{ VALUES ?prop {{ {heads} }} ?t ?prop ?p . }}
                ?p wdt:P31 wd:Q5 . }}"""):
            links.add((_q(r["p"]["value"]), _q(r["t"]["value"]), OFFICER))
        if i % 3000 == 0:
            log(f"  organisation people: {i}/{len(targets)} targets, {len(links)} links")
    return sorted(links)


def targets(conn, settlements=None):
    """The group's places with a Wikidata id, less market towns and places whose item is a settlement (an oldest
    market recorded on its town's item)."""
    q = ",".join("?" for _ in SKIP_KINDS)
    ids = {i for (i,) in conn.execute(
        f"SELECT id FROM places WHERE kind_group = ? AND kind NOT IN ({q}) AND id LIKE 'Q%'", (GROUP, *SKIP_KINDS))}
    return ids - (settlements if settlements is not None else _settlements(ids))


def _settlements(ids):
    out, ids = set(), sorted(ids)
    for i in range(0, len(ids), 300):
        values = " ".join("wd:" + q for q in ids[i:i + 300])
        out |= {_q(r["t"]["value"]) for r in sparql(
            f"SELECT DISTINCT ?t WHERE {{ VALUES ?t {{ {values} }} ?t wdt:P31/wdt:P279* wd:{SETTLEMENT} }}")}
    return out


def write(conn, targets, persons, rows):
    """Replace the place links of `targets` with `rows`; add people not yet in the table."""
    from .people import PERSON_COLUMNS
    ids = sorted(targets)
    for i in range(0, len(ids), 500):
        chunk = ids[i:i + 500]
        conn.execute(f"DELETE FROM person_links WHERE target_type = 'place' AND target_id IN "
                     f"({','.join('?' for _ in chunk)})", chunk)
    cols = [c for c, _ in PERSON_COLUMNS]
    conn.executemany(f"INSERT OR IGNORE INTO persons VALUES ({', '.join('?' for _ in cols)})",
                     [[p.get(c) for c in cols] for p in persons])
    conn.executemany("INSERT INTO person_links VALUES (?, ?, ?, ?, ?)", rows)
    conn.commit()


def run(log=print):
    from .db import connect
    t0 = time.time()
    say = lambda m: log(f"[{time.time() - t0:5.0f}s] {m}")
    conn = connect()
    conn.execute("PRAGMA busy_timeout = 120000")
    tg = targets(conn)
    group = targets(conn, settlements=set())
    links = people.find_links(tg, say) + org_links(tg, say)
    persons, links = people.prepare(links, say, intros_for=1500)
    refs = people.link_references(links, say, PERSON_PROPS)
    write(conn, group, persons, [(p, t, "place", role, refs.get((p, t, role))) for p, t, role in links])
    say(f"trade people: {len(tg)} places, {len(persons)} people, {len(links)} links "
        f"({len(refs)} with a Wikidata reference)")
    conn.close()


def report():
    from collections import Counter
    from .db import connect
    conn = connect()
    tg = targets(conn, settlements=set())
    rows = conn.execute("SELECT l.role, p.kind FROM person_links l JOIN places p ON p.id = l.target_id "
                        "WHERE p.kind_group = ?", (GROUP,)).fetchall()
    print(f"{len(tg)} places; links by role:", dict(Counter(r for r, _ in rows).most_common()))
    print("by kind:", dict(Counter(k for _, k in rows).most_common()))
    for t, n in conn.execute("SELECT p.name, COUNT(*) FROM person_links l JOIN places p ON p.id = l.target_id "
                             "WHERE p.kind_group = ? GROUP BY p.id ORDER BY 2 DESC LIMIT 15", (GROUP,)):
        print(f"  {n:4d}  {t}")


if __name__ == "__main__":
    report() if sys.argv[1:] == ["--report"] else run()
