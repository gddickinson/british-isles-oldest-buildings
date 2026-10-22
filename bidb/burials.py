"""Build stage / CLI: graves and burial grounds -> places group "Graves & burial grounds" (after bidb.bridges).

    python -m bidb.burials            fetch (cached) and add / regroup
    python -m bidb.burials --report   counts

Every Wikidata item in the isles with coordinates that is a cemetery (or a subclass: war, Jewish…
cemeteries), a churchyard, a tomb, chest or table tomb, burial vault, mausoleum or grave. Prehistoric
burial monuments (cairns, barrows, chambered and megalithic tombs, anything dated BC) stay with archaeology, and those in
the building catalogue stay there. The researched oldest graves and gravestones (bidb.oldest_lists)
join the same group.
"""
import argparse
import json
import re
import time

from . import place_stage
from .db import connect
from .maritime import _record
from .place_stage import direct_items, rows_for, subclass_items

GROUP = "Graves & burial grounds"
CEMETERY = "Q39614"
CHURCHYARD, WAR = {"Q2749813"}, {"Q1707610", "Q1241568"}
DIRECT = {"bu_tomb": {"Q381885", "Q19833736", "Q386037", "Q1578744"}, "bu_mausoleum": {"Q162875"},
          "bu_grave": {"Q173387"}}
LABELS = {"bu_cemetery": "Cemetery", "bu_churchyard": "Churchyard or burial ground", "bu_war": "War cemetery",
          "bu_tomb": "Tomb or chest tomb", "bu_mausoleum": "Mausoleum", "bu_grave": "Grave"}
KINDS = tuple(LABELS)
PREHISTORIC = re.compile(r"cairn|barrow|chambered|megalith|dolmen|cromlech|quoit|court tomb|portal tomb|passage "
                         r"(?:tomb|grave)|wedge tomb|long mound|cist", re.I)


def _cemetery_kind(classes):
    return "bu_churchyard" if classes & CHURCHYARD else "bu_war" if classes & WAR else "bu_cemetery"


def build(log=print):
    kinds = {q: _cemetery_kind(c) for q, c in subclass_items(CEMETERY).items()}
    for q in direct_items(CHURCHYARD):
        kinds[q] = "bu_churchyard"
    for kind, classes in DIRECT.items():
        for q in direct_items(classes):
            kinds.setdefault(q, kind)
    recs = {}
    for r in rows_for(kinds):
        qid = r["i"]["value"].rsplit("/", 1)[-1]
        if PREHISTORIC.search(r["iLabel"]["value"]):
            continue
        x = _record(kinds[qid], LABELS[kinds[qid]], r)
        if x and (x["year_start"] or 0) < 0:          # barrow cemeteries, henges and tombs: archaeology
            continue
        if x and x["id"] not in recs:
            x["kind_group"] = GROUP
            recs[x["id"]] = x
    log(f"  burials: {len(recs)} " + json.dumps({k: sum(r['kind'] == k for r in recs.values()) for k in KINDS}))
    return list(recs.values())


def run(log=print):
    t0 = time.time()
    conn = connect()
    conn.execute("PRAGMA busy_timeout = 120000")
    recs = build(log)
    # archaeological sites (barrow cemeteries, Anglo-Saxon cemeteries…) stay in their group
    place_stage.write(conn, recs, KINDS, GROUP, lambda kind, r: kind != "archaeology",
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
