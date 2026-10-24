"""Build stage / CLI: archaeological excavations -> table `excavations` and places group "Excavations".

    python -m bidb.digs            fetch (cached) and write
    python -m bidb.digs --report   counts
    python -m bidb.digs <id>       one record's excavations

Wikidata (CC0): sites with an "archaeological excavation" significant event (P793, with its dates),
directors of archaeological fieldwork (P4345) and discoverers (P61). Wikipedia (CC BY-SA): the digs
of Channel 4's Time Team, 1994–2014 and 2022–, from the series pages (location, coordinates, year,
summary). Each building or place gets its excavations in the `excavations` table ("Excavated:" in
detail views; a Time Team dig within NEAR_KM of a catalogue building counts for it too). Excavated
sites not yet in the database and every Time Team dig become places in the "Excavations" group.
"""
import argparse
import json
import re
import sys
import time
from urllib.parse import quote

from . import place_stage
from .db import connect, dist_km
from .hoards import coord, wikitext
from .http import sparql
from .maritime import _record
from .place_kinds import in_box
from .place_records import blank
from .wikipedia_list import _strip_wikitext

GROUP = "Excavations"
KINDS = ("excavated", "timeteam")
LABELS = {"excavated": "Excavated site", "timeteam": "Time Team dig"}
COLUMNS = ["entity_id", "what", "years", "who"]
NEAR_KM = 0.3
TT_LIST = "List of Time Team episodes"


def _qid(v):
    return v.rsplit("/", 1)[-1]


def wikidata_digs():
    """{qid: {"years": [(from, to)], "who": [names], "row": query row}} for excavated sites in the isles."""
    out = {}
    for r in place_stage.query("?i p:P793 ?ev . ?ev ps:P793 wd:Q959782 ."):
        out.setdefault(_qid(r["i"]["value"]), {"years": [], "who": [], "row": r})
    rows = sparql(f"""SELECT ?i ?y ?y2 WHERE {{ ?i p:P793 ?ev . ?ev ps:P793 wd:Q959782 .
        ?i wdt:P17 ?c VALUES ?c {{ {' '.join(place_stage.COUNTRIES)} }}
        OPTIONAL {{ ?ev pq:P585|pq:P580 ?d BIND(YEAR(?d) AS ?y) }} OPTIONAL {{ ?ev pq:P582 ?d2 BIND(YEAR(?d2) AS ?y2) }} }}""")
    for r in rows:
        if r.get("y") and _qid(r["i"]["value"]) in out:
            span = (int(r["y"]["value"]), int(r["y2"]["value"]) if r.get("y2") else None)
            if span not in out[_qid(r["i"]["value"])]["years"]:
                out[_qid(r["i"]["value"])]["years"].append(span)
    who = {}
    for prop, prefix in (("P4345", ""), ("P61", "found by ")):         # director of fieldwork, discoverer
        rows = sparql(f"""SELECT ?i ?wLabel WHERE {{ ?i wdt:{prop} ?w ; wdt:P17 ?c .
            VALUES ?c {{ {' '.join(place_stage.COUNTRIES)} }}
            SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en". }} }}""")
        for r in rows:
            name = r["wLabel"]["value"]
            if not name.startswith("http"):
                who.setdefault(_qid(r["i"]["value"]), []).append(prefix + name)
    for q, names in who.items():
        out.setdefault(q, {"years": [], "who": [], "row": None})["who"] = sorted(set(names))
    return out


def years_text(spans):
    return ", ".join(f"{a}–{b}" if b and b != a else str(a) for a, b in sorted(spans, key=lambda s: (s[0], s[1] or s[0])))


def time_team():
    """[{title, location, lat, lon, year, summary, page}] for every Time Team dig with coordinates."""
    pages = re.findall(r"\{\{:(Time Team[^}|]+)\}\}", wikitext(TT_LIST))
    out = []
    for page in pages:
        text = wikitext(page)
        for block in re.split(r"\{\{Episode list/sublist", text)[1:]:
            fields = dict(re.findall(r"\n\|\s*(\w+)\s*=\s*(.*?)(?=\n\|\s*\w+\s*=|\n\}\})", block, flags=re.S))
            ll = coord(fields.get("Aux3", ""))
            if not ll:
                continue
            year = re.search(r"\{\{Start date\|(\d{4})", fields.get("OriginalAirDate", ""))
            out.append({"title": _strip_wikitext(fields.get("Title", "")) or "Time Team dig",
                        "location": _strip_wikitext(fields.get("Aux1", "").replace("<br />", "; ").replace("<br/>", "; ")),
                        "lat": ll[0], "lon": ll[1],
                        "year": int(year.group(1)) if year else None,
                        "summary": re.sub(r"\s+", " ", _strip_wikitext(fields.get("ShortSummary", "")))[:700] or None,
                        "page": page})
    return out


def run(log=print):
    t0 = time.time()
    conn = connect()
    conn.execute("PRAGMA busy_timeout = 120000")
    digs, tt = wikidata_digs(), time_team()
    ids = {}
    for rid, q in list(conn.execute("SELECT id, wikidata_id FROM buildings WHERE wikidata_id IS NOT NULL")) + list(
            conn.execute(f"SELECT id, wikidata_id FROM places WHERE wikidata_id IS NOT NULL "    # this stage's own
                         f"AND kind NOT IN ({','.join('?' * len(KINDS))})", KINDS)):              # are rewritten
        ids.setdefault(q, rid)
    rows, new = [], []
    for q, d in digs.items():
        what = years_text(d["years"])
        if q not in ids and d["row"]:
            x = _record("excavated", LABELS["excavated"], d["row"])
            if not x:
                continue
            x.update(kind_group=GROUP, date_text=f"excavated {what}" if what else x["date_text"])
            new.append(x)
            ids[q] = x["id"]
        if q in ids:
            rows.append((ids[q], "excavation", what or None, "; ".join(d["who"]) or None))
    buildings = list(conn.execute("SELECT id, lat, lon FROM buildings WHERE lat IS NOT NULL"))
    for i, e in enumerate(tt):
        pid = f"tt-{i + 1}-{re.sub(r'[^a-z0-9]+', '-', e['title'].lower()).strip('-')}"
        if not in_box(e["lat"], e["lon"]):           # the specials abroad (Maryland, Mallorca, Denia, Utrecht)
            continue
        new.append(blank(pid, "timeteam", e["title"], kind_group=GROUP, lat=e["lat"], lon=e["lon"],
                         locality=e["location"] or None, description=e["summary"],
                         date_text=f"Time Team, {e['year']}" if e["year"] else "Time Team", source="Wikipedia",
                         type=LABELS["timeteam"], url="https://en.wikipedia.org/wiki/" + quote(e["page"].replace(" ", "_"))))
        rows.append((pid, "time team", str(e["year"]) if e["year"] else None, None))
        for bid, lat, lon in buildings:
            if abs(lat - e["lat"]) < 0.01 and dist_km(lat, lon, e["lat"], e["lon"]) <= NEAR_KM:
                rows.append((bid, "time team", str(e["year"]) if e["year"] else None, None))
    place_stage.write(conn, new, KINDS, GROUP, lambda kind, r: False, lambda m: log(f"[{time.time() - t0:5.0f}s] {m}"))
    conn.execute("DROP TABLE IF EXISTS excavations")
    conn.execute(f"CREATE TABLE excavations ({', '.join(COLUMNS)})")
    conn.execute("CREATE INDEX excavations_entity ON excavations(entity_id)")
    conn.executemany("INSERT INTO excavations VALUES (?, ?, ?, ?)", rows)
    conn.commit()
    log(f"[{time.time() - t0:5.0f}s] excavations: {len(digs)} excavated sites on Wikidata, {len(tt)} Time Team digs; "
        f"{len({r[0] for r in rows})} buildings and places with an excavation")


def for_record(conn, rid):
    if not conn.execute("SELECT 1 FROM sqlite_master WHERE name = 'excavations'").fetchone():
        return []
    return [dict(zip(COLUMNS, r)) for r in conn.execute(f"SELECT {', '.join(COLUMNS)} FROM excavations WHERE entity_id = ?",
                                                        (rid,))]


def report(log=print):
    log(json.dumps(place_stage.report(connect(), GROUP), indent=1))


def main():
    if len(sys.argv) > 1 and not sys.argv[1].startswith("-"):
        print(json.dumps(for_record(connect(), sys.argv[1]), indent=1))
        return
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--report", action="store_true")
    a = ap.parse_args()
    report() if a.report else run()


if __name__ == "__main__":
    main()
