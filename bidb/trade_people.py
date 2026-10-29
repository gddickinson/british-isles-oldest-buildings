"""People of the guilds, companies, banks, exchanges, inns and shops (roadmap C3c): python -m bidb.trade_people [--later]

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

The same for the other groups the place stages add after the people stage of places_build (`LATER`: maritime,
military, museums, sport, institutions, bridges, graves...; `run_later`, build stage after this one): the place
roles for all of them, the organisation roles only for museums (directors, curators, trustees) as for trade; for
universities, hospitals and the like "employer" would bring in everyone who ever worked there.

    org_links(targets)   [(person, target, role)] for the organisation roles
    run()                links, people and their references written to persons / person_links
    run_later()          the same for the LATER groups
"""
import sys
import time

from . import people
from .http import sparql

GROUP = "Markets & trade"
LATER = ("Maritime heritage", "Military heritage", "Museums & collections", "Sport & leisure", "Public institutions",
         "Infrastructure & utilities", "Bridges", "Industrial heritage", "Graves & burial grounds", "Underground",
         "Victorian era", "Excavations", "Legends & literature", "Innovations & firsts", "Nature & deep time")
ORG_GROUPS = (GROUP, "Museums & collections")
SKIP_KINDS = ("tr_town",)
SETTLEMENT = "Q486972"
ADMIN_AREA = "Q56061"       # counties, nations: settings of literary works ("Devon") gather everyone born there;
                            # only for literary places: forts reach it through "military area"
ISLAND = "Q23442"           # the island of Ireland as a setting
LITERARY = "literary"
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


def targets(conn, settlements=None, groups=(GROUP,)):
    """The groups' places with a Wikidata id, less market towns and places whose item is a settlement (an oldest
    market recorded on its town's item), and literary settings that are administrative areas or islands (a novel
    set in a county)."""
    q = ",".join("?" for _ in SKIP_KINDS)
    g = ",".join("?" for _ in groups)
    ids = {i for (i,) in conn.execute(
        f"SELECT id FROM places WHERE kind_group IN ({g}) AND kind NOT IN ({q}) AND id LIKE 'Q%'",
        (*groups, *SKIP_KINDS))}
    if settlements is None:
        lit = {i for (i,) in conn.execute(f"SELECT id FROM places WHERE kind = ? AND kind_group IN ({g})",
                                          (LITERARY, *groups))} & ids
        settlements = _settlements(ids) | (_settlements(lit, f"wd:{SETTLEMENT} wd:{ADMIN_AREA} wd:{ISLAND}") if lit else set())
    return ids - settlements


def _settlements(ids, classes=f"wd:{SETTLEMENT}"):
    out, ids = set(), sorted(ids)
    for i in range(0, len(ids), 300):
        values = " ".join("wd:" + q for q in ids[i:i + 300])
        out |= {_q(r["t"]["value"]) for r in sparql(
            f"SELECT DISTINCT ?t WHERE {{ VALUES ?t {{ {values} }} VALUES ?c {{ {classes} }} "
            f"?t wdt:P31/wdt:P279* ?c }}")}
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


def run(log=print, groups=(GROUP,), what="trade"):
    from .db import connect
    t0 = time.time()
    say = lambda m: log(f"[{time.time() - t0:5.0f}s] {m}")
    conn = connect()
    conn.execute("PRAGMA busy_timeout = 120000")
    tg = targets(conn, groups=groups)
    group = targets(conn, settlements=set(), groups=groups)
    org = targets(conn, settlements=set(), groups=[g for g in groups if g in ORG_GROUPS]) & tg
    links = sorted(set(people.find_links(tg, say)) | set(org_links(org, say) if org else []))
    persons, links = people.prepare(links, say, intros_for=1500)
    refs = people.link_references(links, say, PERSON_PROPS)
    write(conn, group, persons, [(p, t, "place", role, refs.get((p, t, role))) for p, t, role in links])
    say(f"{what} people: {len(tg)} places, {len(persons)} people, {len(links)} links "
        f"({len(refs)} with a Wikidata reference)")
    conn.close()


def run_later(log=print):
    run(log, groups=LATER, what="later place groups'")


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
    if sys.argv[1:] == ["--report"]:
        report()
    else:
        run_later() if sys.argv[1:] == ["--later"] else run()
