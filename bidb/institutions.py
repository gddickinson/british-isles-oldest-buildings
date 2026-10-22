"""Build stage / CLI: schools, universities, hospitals and public services -> places group "Public institutions"
(after bidb.sports).

    python -m bidb.institutions            fetch (cached) and add / regroup
    python -m bidb.institutions --report   counts

Every Wikidata item in the isles with coordinates whose class is one of the roots below or a subclass of one:
universities and colleges, schools, hospitals and asylums, post offices, courts, police stations, fire and
ambulance stations, town halls and government buildings, prisons, and community buildings (village halls,
almshouses, workhouses, orphanages, mechanics' institutes, register offices). An item of several kinds takes the
first in KINDS order. Schools number about 30,000 on Wikidata (most from the schools registers): only those
founded before SCHOOL_BEFORE are kept. Items in the building catalogue stay there;
places of the other group stages keep their group (drill halls stay military, workhouses Victorian…).
"""
import argparse
import json
import time

GROUP = "Public institutions"
SCHOOL_BEFORE = 1900
# kind: (label, root classes); order = precedence
KINDS_SPEC = {
    "pi_university": ("University or college", ("Q3918", "Q189004")),
    "pi_hospital": ("Hospital or asylum", ("Q16917", "Q608502", "Q1774898")),
    "pi_prison": ("Prison or gaol", ("Q40357",)),
    "pi_court": ("Court or courthouse", ("Q1137809",)),
    "pi_police": ("Police station", ("Q861951",)),
    "pi_fire": ("Fire or ambulance station", ("Q1195942", "Q927519")),
    "pi_post": ("Post office", ("Q35054", "Q915063")),
    "pi_civic": ("Town hall or government building", ("Q543654", "Q25550691", "Q16831714")),
    "pi_community": ("Village hall, almshouse or workhouse", ("Q367885", "Q15548045", "Q628155", "Q160645",
                                                              "Q6804572", "Q745221")),
    "pi_school": ("School", ("Q3914",)),
}
LABELS = {k: v[0] for k, v in KINDS_SPEC.items()}
KINDS = tuple(LABELS)


def keep_school(r):
    """A school record worth a place: founded before SCHOOL_BEFORE."""
    return r.get("year_start") is not None and r["year_start"] < SCHOOL_BEFORE


def build(log=print):
    from .maritime import _record
    from .place_stage import rows_for, subclass_items
    kinds = {}
    for kind, (_label, roots) in KINDS_SPEC.items():
        for root in roots:
            for q in subclass_items(root):
                kinds.setdefault(q, kind)
    recs = {}
    for r in rows_for(kinds):
        qid = r["i"]["value"].rsplit("/", 1)[-1]
        x = _record(kinds[qid], LABELS[kinds[qid]], r)
        if not x or x["id"] in recs or (x["kind"] == "pi_school" and not keep_school(x)):
            continue
        x["kind_group"], x["kind_label"] = GROUP, LABELS[x["kind"]]
        if r.get("end") and r["end"]["value"]:
            x["type"] = f"{LABELS[x['kind']]} (gone or closed)"
        recs[x["id"]] = x
    log(f"  institutions: {len(recs)} " + json.dumps({k: sum(r['kind'] == k for r in recs.values()) for k in KINDS}))
    return list(recs.values())


def run(log=print):
    from . import era_places, place_stage
    from .db import connect
    t0 = time.time()
    conn = connect()
    conn.execute("PRAGMA busy_timeout = 120000")
    place_stage.write(conn, build(log), KINDS, GROUP, lambda kind, r: kind not in era_places.KINDS,
                      lambda m: log(f"[{time.time() - t0:5.0f}s] {m}"))
    conn.commit()


def report(log=print):
    from . import place_stage
    from .db import connect
    log(json.dumps(place_stage.report(connect(), GROUP), indent=1))


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--report", action="store_true")
    a = ap.parse_args()
    report() if a.report else run()


if __name__ == "__main__":
    main()
