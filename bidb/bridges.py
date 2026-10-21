"""Build stage / CLI: bridges -> places group "Bridges" (run after bidb.museums).

    python -m bidb.bridges            fetch (cached) and add / regroup
    python -m bidb.bridges --report   counts

Every Wikidata item in the isles with coordinates whose class is bridge or one of its subclasses,
by type, with opening years: clapper, packhorse and stepping-stone crossings; aqueducts; moving
bridges; suspension and cable-stayed bridges; railway viaducts and bridges; footbridges; and the
rest (road bridges, arch bridges…). Culverts and pedestrian subways are left out. The bridges in
the building catalogue stay there; places from other stages (iron bridges, viaducts, aqueducts,
scheduled bridges) move to this group, except those of the other group stages.
"""
import argparse
import json
import time

from . import place_stage
from .db import connect
from .maritime import _record
from .place_stage import rows_for, subclass_items

GROUP = "Bridges"
BRIDGE = "Q12280"
# kind: (label, classes that decide it); checked in this order, "bridge" otherwise
KIND_CLASSES = {
    "br_early": ("Clapper, packhorse or stepping-stone crossing", {"Q7123018", "Q265881", "Q1415899"}),
    "br_aqueduct": ("Aqueduct", {"Q1030403", "Q18870689", "Q7197275"}),
    "br_moving": ("Swing or bascule bridge", {"Q950431", "Q911663"}),
    "br_suspension": ("Suspension or cable-stayed bridge", {"Q12570", "Q158555"}),
    "br_rail": ("Railway viaduct or bridge", {"Q39486269", "Q1210334", "Q181348", "Q40531603", "Q18615527"}),
    "br_foot": ("Footbridge", {"Q1068842", "Q2502622"}),
}
LABELS = {k: v[0] for k, v in KIND_CLASSES.items()} | {"bridge": "Bridge"}
KINDS = tuple(LABELS)
NOT_BRIDGE = {"Q4168092", "Q1188673"}            # culvert, pedestrian subway


def _kind(classes):
    for kind, (_, cls) in KIND_CLASSES.items():
        if classes & cls:
            return kind
    return "bridge"


def build(log=print):
    classes = {q: c for q, c in subclass_items(BRIDGE).items() if not c <= NOT_BRIDGE}
    recs = {}
    for r in rows_for(classes):
        qid = r["i"]["value"].rsplit("/", 1)[-1]
        kind = _kind(classes[qid])
        x = _record(kind, LABELS[kind], r)
        if x and x["id"] not in recs:
            if r.get("end") and r["end"]["value"]:
                x["type"] = f"{LABELS[kind]} (gone or closed)"
            x["kind_group"] = GROUP
            recs[x["id"]] = x
    log(f"  bridges: {len(recs)} " + json.dumps({k: sum(r['kind'] == k for r in recs.values()) for k in KINDS}))
    return list(recs.values())


def run(log=print):
    t0 = time.time()
    conn = connect()
    conn.execute("PRAGMA busy_timeout = 120000")
    recs = build(log)
    place_stage.write(conn, recs, KINDS, GROUP, lambda kind, r: True, lambda m: log(f"[{time.time() - t0:5.0f}s] {m}"))
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
