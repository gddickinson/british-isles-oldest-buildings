"""Build stage / CLI: underground works -> places group "Underground" (run after bidb.era_places).

    python -m bidb.underground            fetch (cached) and add / regroup
    python -m bidb.underground --report   counts

Wikidata items in the isles with coordinates:
  tube      stations of the London Underground, Glasgow Subway and Tyne and Wear Metro, and other
            underground railway stations, with opening years
  ghost     the same stations once closed (closing date, dissolved, or "disused"): Aldwych, Down
            Street, British Museum… (cancelled stations are left out)
  tunnel    railway, canal, road, foot and water tunnels
  shelter   air-raid and deep-level shelters, bunkers, Royal Observer Corps posts
  cave      show caves, underground quarries, and caves with a Wikipedia article
  ug_mine   mines with a Wikipedia article (mines dated 1700–1914 stay in Industrial heritage)
  icehouse  ice houses
  grotto    grottoes, incl. shell grottoes
  catacomb  catacombs, crypts, vaults and buried streets
  sewer     sewers, cisterns and water works below ground
plus `data/curated/underground_sites.json` (notable works whose Wikidata class is none of these).
Items already in the building catalogue stay there; places already in the database move to this
group with the underground label (except legends, maritime places, plaques, finds and events, and
mines, which keep theirs); their kind stays, so the stage that made them can rebuild them.
"""
import argparse
import json
import time

from .config import DATA_DIR
from .db import connect
from . import place_stage
from .maritime import _record
from .place_stage import query as _query

GROUP = "Underground"
CURATED = DATA_DIR / "curated" / "underground_sites.json"
# kind: (label, Wikidata classes, only items with an English Wikipedia article)
CLASSES = {
    "tube": ("Underground or metro station", ["Q14562709", "Q55491", "Q85641138", "Q168565"], False),
    "tunnel": ("Tunnel", ["Q1311958", "Q5031071", "Q2354973", "Q44377", "Q24897103", "Q12719343"], False),
    "shelter": ("Shelter or bunker", ["Q389959", "Q91122", "Q7374635"], False),
    "cave": ("Cave or cavern", ["Q2232001", "Q140463560"], False),
    "cave_wp": ("Cave or cavern", ["Q35509"], True),
    "ug_mine": ("Mine", ["Q820477", "Q58917"], True),
    "icehouse": ("Ice house", ["Q253893"], False),
    "grotto": ("Grotto", ["Q1131329", "Q30754717"], False),
    "catacomb": ("Catacomb, crypt or vault", ["Q172896", "Q192619"], False),
    "sewer": ("Sewer, cistern or water tunnel", ["Q838858"], False),
}
LABELS = {k: v[0] for k, v in CLASSES.items() if k != "cave_wp"}
LABELS.update({"ghost": "Disused underground station", "ug_railway": "Underground railway"})
KINDS = tuple(LABELS)
NETWORKS = "wd:Q20075 wd:Q506290"          # London Underground, Glasgow Subway (stations by network)


def _add(recs, kind, label, rows):
    got = [x for x in (_record(kind, label, r) for r in rows) if x]
    for x in got:
        recs.setdefault(x["id"], x)
    return got


def _stations(recs, log):
    """Underground and metro stations; closed ones become ghost stations."""
    classes = " ".join("wd:" + c for c in CLASSES["tube"][1])
    rows = _query(f"""{{ VALUES ?cls {{ {classes} }} ?i wdt:P31 ?cls . }} UNION
        {{ VALUES ?net {{ {NETWORKS} }} ?i wdt:P16 ?net ; wdt:P31/wdt:P279* wd:Q55488 . }}""")
    still_open = json.loads(CURATED.read_text())["still_open"]
    open_, ghost = [], []
    for r in rows:
        closed = r.get("end") or r.get("closed", {}).get("value") == "true"
        closed = closed and r["i"]["value"].rsplit("/", 1)[-1] not in still_open
        (ghost if closed else open_).append(r)
    log(f"  tube: {len(_add(recs, 'ghost', LABELS['ghost'], ghost))} disused, "
        f"{len(_add(recs, 'tube', LABELS['tube'], open_))} open")


def _curated(recs, log):
    sites = json.loads(CURATED.read_text())["sites"]
    kind_of = {s["qid"]: s["kind"] for s in sites}
    rows = _query(f"VALUES ?i {{ {' '.join('wd:' + q for q in kind_of)} }}")
    n = 0
    for r in rows:
        qid = r["i"]["value"].rsplit("/", 1)[-1]
        x = _record(kind_of[qid], LABELS[kind_of[qid]], r)
        if x:
            recs[x["id"]] = x                               # the curated kind wins
            n += 1
    log(f"  curated: {n} of {len(sites)}")


def build(log=print):
    recs = {}
    _curated(recs, log)
    _stations(recs, log)
    for key, (label, classes, wp_only) in CLASSES.items():
        if key == "tube":
            continue
        kind = "cave" if key == "cave_wp" else key
        got = []
        for cls in classes:                                 # one query per class keeps each one light
            got += _add(recs, kind, label, _query(f"?i wdt:P31 wd:{cls} .", wp_only))
        log(f"  {key}: {len(got)}")
    for r in recs.values():
        r["kind_group"] = GROUP
    return list(recs.values())


def run(log=print):
    t0 = time.time()
    conn = connect()
    conn.execute("PRAGMA busy_timeout = 120000")
    recs = build(log)
    # mines dated 1700–1914 stay in Industrial heritage
    place_stage.write(conn, recs, KINDS, GROUP, lambda kind, r: not (r["kind"] == "ug_mine" and kind == "mine"),
                      lambda m: log(f"[{time.time() - t0:5.0f}s] {m}"))
    conn.commit()


def report(log=print):
    log(json.dumps(place_stage.report(connect(), GROUP), indent=1))


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--report", action="store_true")
    a = ap.parse_args()
    report() if a.report else run()


if __name__ == "__main__":
    main()
