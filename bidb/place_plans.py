"""Building types BT6c2a / CLI/build stage after type_map: floor plans of typed places (Wikidata places, not the
catalogue's own records, which bidb.footprints and bidb.photo_search cover) from Wikidata's plan view image (P3311),
else a file named as a plan in the item's Commons "Plans of <category>" category (bidb.commons_plans), else, for
types with fewer than `type_pages.PLANS` plans, a file titled as a plan inside the place's own Commons category tree
whose title holds every distinctive word of its name (`photo_search.category_plan`; up to `TRIES` places a type,
those with a Wikipedia article first, then oldest) → table `place_plans` (place_id, file, via), read by
type_pages.plans. `python -m bidb.place_plans [--report]`."""
import re
import sqlite3
import sys

from . import commons_plans, footprints, photo_search, progress
from .images_extra import _words
from .config import DB_PATH, require_locations

NOT_PLAN = re.compile(r"\b(map|maps|section|elevation|engineering drawing)\b", re.I)
NOT_PLANS = {                               # reviewed 2026-10-28
    "Wyre Light.jpg",                                                                   # an elevation
    "Tracts vol 57 p252 1821 Plan of intended Stockton and Darlington Railway.jpg",     # the route, a map
    "Liverpool Royal Infirmary Nurses Home floor plan, 1923 (14652181872).jpg",         # another building
    "Plans de La Hougue avec son projet - btv1b550031846 (1 of 2).jpg",                 # a proposal
    "Grime's Graves Clarke 1963 General Plan.jpg",           # flint mines, typed a round barrow by mistake
}
TRIES = 25                  # places with a Commons category searched per type short of plans
WANT = 12                   # = type_pages.PLANS
SCHEMA = "CREATE TABLE IF NOT EXISTS place_plans (place_id TEXT, file TEXT, via TEXT)"


def targets(conn):
    """{qid: [place ids]} for typed places with a Wikidata item that is not a catalogue record."""
    rows = conn.execute("""SELECT DISTINCT p.id, p.wikidata_id FROM type_map tm JOIN places p ON p.id = tm.entity_id
                           WHERE tm.source = 'place' AND p.wikidata_id LIKE 'Q%'
                             AND (p.building_id IS NULL OR p.building_id = '')
                             AND p.wikidata_id NOT IN (SELECT id FROM buildings)""").fetchall()
    out = {}
    for pid, q in rows:
        out.setdefault(q, []).append(pid)
    return out


def find(qids, log=print):
    """{qid: (file, via)}: P3311 first, then the Commons plans categories."""
    # P3311 on places is sometimes a map of the site ("Ham Hill Somerset Map.jpg") or a section or elevation of it:
    # left out (files reviewed as no plan of the place: NOT_PLANS, for every source)
    found = {q: (f, "wikidata") for q, f in footprints.plans(qids).items()
             if not NOT_PLAN.search(f)}
    log(f"  plan view images (P3311): {len(found)}")
    extra = commons_plans.plans([q for q in qids if q not in found], log)
    log(f"  from Commons 'Plans of' categories: {len(extra)}")
    found.update({q: (f, "commons") for q, f in extra.items()})
    return found


def search_queue(conn, found_ids):
    """{type: [(place id, qid, name)]} for each type with fewer than WANT plans (catalogue + places found so far),
    its places not yet with a plan: those with a Wikipedia article first, then oldest."""
    have = {}
    for t, n in conn.execute("""SELECT tm.type_id, COUNT(*) FROM type_map tm JOIN buildings b ON b.id = tm.entity_id
                                WHERE tm.source = 'building' AND b.plan_image IS NOT NULL AND b.plan_image != ''
                                GROUP BY 1"""):
        have[t] = n
    rows = conn.execute("""SELECT tm.type_id, p.id, p.wikidata_id, p.name FROM type_map tm
                           JOIN places p ON p.id = tm.entity_id
                           WHERE tm.source = 'place' AND p.wikidata_id LIKE 'Q%'
                             AND (p.building_id IS NULL OR p.building_id = '')
                             AND p.wikidata_id NOT IN (SELECT id FROM buildings)
                           ORDER BY (p.wikipedia_title IS NULL OR p.wikipedia_title = ''), p.year_start IS NULL,
                                    p.year_start""").fetchall()
    out = {}
    for t, pid, q, name in rows:
        if pid in found_ids:
            have[t] = have.get(t, 0) + 1
        else:
            out.setdefault(t, []).append((pid, q, name))
    return {t: ps for t, ps in out.items() if have.get(t, 0) < WANT}


def search(queue, log=print):
    """{qid: file} from the Commons category trees, TRIES places with a category per type at most."""
    qids = sorted({q for ps in queue.values() for _, q, _ in ps})
    cats = photo_search.categories(qids)
    log(f"  places of types short of plans: {len(qids)}, with a Commons category: {len(cats)}")
    out, tried = {}, {}
    for n, (t, ps) in enumerate(sorted(queue.items())):
        k = 0
        for _, q, name in ps:
            if q not in cats or k >= TRIES:
                continue
            k += 1
            if q not in tried:
                tried[q] = photo_search.category_plan(cats[q], _words(name))
            if tried[q]:
                out[q] = tried[q]
                log(f"    {t}: {name}: {tried[q]}")
        progress.items(n + 1, len(queue))
    log(f"  from the places' own Commons categories: {len(out)} of {len(tried)} searched")
    return out


def write(conn, rows):
    conn.execute(SCHEMA)
    conn.execute("DELETE FROM place_plans")
    conn.executemany("INSERT INTO place_plans VALUES (?,?,?)", rows)
    conn.commit()


def run(log=print):
    require_locations()
    conn = sqlite3.connect(DB_PATH, timeout=300)
    t = targets(conn)
    log(f"typed places with a Wikidata item: {len(t)}")
    progress.note(f"plans of {len(t)} places")
    found = find(sorted(t), log)
    ids = {pid for q in found for pid in t[q]}
    found.update({q: (f, "commons category") for q, f in search(search_queue(conn, ids), log).items()
                  if q not in found})
    rows = [(pid, f, via) for q, (f, via) in found.items() if f not in NOT_PLANS for pid in t[q]]
    write(conn, rows)
    log(f"place plans: {len(rows)} places")
    return len(rows)


def report(conn):
    """Plans per type: [(type, catalogue plans, place plans)] for types with any, most place plans first."""
    conn.execute(SCHEMA)
    rows = conn.execute("""SELECT tm.type_id,
                                  SUM(tm.source = 'building' AND b.plan_image IS NOT NULL AND b.plan_image != ''),
                                  SUM(tm.source = 'place' AND pp.file IS NOT NULL)
                           FROM type_map tm LEFT JOIN buildings b ON b.id = tm.entity_id AND tm.source = 'building'
                           LEFT JOIN place_plans pp ON pp.place_id = tm.entity_id AND tm.source = 'place'
                           GROUP BY tm.type_id""").fetchall()
    return sorted(((t, a or 0, b or 0) for t, a, b in rows if a or b), key=lambda r: (-r[2], -r[1], r[0]))


if __name__ == "__main__":
    if "--report" in sys.argv:
        rows = report(sqlite3.connect(DB_PATH))
        print(f"{len(rows)} types with a plan; {sum(1 for r in rows if r[1] == 0)} only from places")
        for t, a, b in rows:
            print(f"  {t:32} catalogue {a:4}  places {b:4}")
    else:
        run()
