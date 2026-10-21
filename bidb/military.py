"""Build stage / CLI: military heritage -> places group "Military heritage" (run after bidb.underground).

    python -m bidb.military            fetch (cached) and add / regroup
    python -m bidb.military --report   counts

Defences through the ages and the works of the two world wars and the Cold War, from Wikidata
items in the isles with coordinates:
  burh         Saxon burhs of the Burghal Hidage (`data/curated/burhs.json`, at the town)
  tower        Martello towers, blockhouses, redoubts and fortified towers
  fort         forts and fortifications begun from 1500 (earlier ones are castles and
               archaeology), incl. Henry VIII's Device Forts and the Palmerston Forts
  battery      coastal, gun and anti-aircraft batteries
  barracks     barracks, drill halls, military camps and arsenals
  pillbox      pillboxes, anti-tank obstacles and observation posts
  radar        radar stations, sound mirrors and signal stations
  airfield     military airfields and RAF stations
  powcamp      prisoner-of-war camps
  defenceline  defence and stop lines (GHQ Line, Taunton Stop Line…)
  memorial     war memorials
Air-raid shelters, bunkers and Royal Observer Corps posts are in the Underground group; naval
bases and dockyards in Maritime heritage. Items already in the building catalogue stay there;
Victorian and industrial places of these kinds move to this group (with this stage's label).
"""
import argparse
import json
import time

from .classify import period_for
from .config import DATA_DIR
from .db import connect
from .maritime import _record
from . import place_stage
from .place_stage import query as _query

GROUP = "Military heritage"
BURHS = DATA_DIR / "curated" / "burhs.json"
# kind: (label, Wikidata classes)
CLASSES = {
    "tower": ("Martello or defensive tower", ["Q91285", "Q81917", "Q82101", "Q90754"]),
    "fort": ("Fort or fortification", ["Q1785071", "Q57821"]),
    "battery": ("Gun or anti-aircraft battery", ["Q16536851", "Q56344492", "Q123905961"]),
    "barracks": ("Barracks, drill hall or camp", ["Q131263", "Q5307555", "Q1198413", "Q81669", "Q1412205"]),
    "pillbox": ("Pillbox or anti-tank defence", ["Q92069", "Q2801289", "Q163021"]),
    "radar": ("Radar station, sound mirror or signal station", ["Q89578131", "Q444789", "Q17142507"]),
    "airfield": ("Military airfield", ["Q695850", "Q7373622"]),
    "powcamp": ("Prisoner-of-war camp", ["Q1070290"]),
    "defenceline": ("Defence or stop line", ["Q2973801"]),
    "memorial": ("War memorial", ["Q575759"]),
}
FORT_GROUPS = {"Q5267014": "Device Forts", "Q7128307": "Palmerston Forts", "Q7128317": "Palmerston Forts"}
LABELS = {k: v[0] for k, v in CLASSES.items()} | {"burh": "Saxon burh"}
KINDS = tuple(LABELS)
FORT_FROM = 1500
# places made by these stages may move here (e.g. Victorian barracks, an industrial-site airfield)
REGROUP_FROM = ("industrial", "victorian_public", "victorian_leisure", "victorian_style", "railway", "engine",
                "warehouse")


def _burhs(recs, log):
    from .wikipedia_list import titles_to_qids
    data = json.loads(BURHS.read_text())
    titles = [b["title"] for b in data["burhs"] if b["title"]]
    qids = titles_to_qids(titles)
    rows = {r["i"]["value"].rsplit("/", 1)[-1]: r
            for r in _query(f"VALUES ?i {{ {' '.join('wd:' + q for q in set(qids.values()))} }}")}
    n = 0
    for b in data["burhs"]:
        row = rows.get(qids.get(b["title"] or ""))
        x = row and _record("burh", LABELS["burh"], row)
        if not x:
            continue
        slug = b["name"].split(" (")[0].lower().replace(" ", "-")
        x.update(id=f"burh-{slug}", name=f"{b['name']} (burh)", wikidata_id=None, year_start=880,
                 date_text="c. 880–914 (Burghal Hidage)", period=period_for(880),
                 description=f"Fortified place of Wessex in the Burghal Hidage, assessed at {b['hides']} hides",
                 url=data["source"])
        recs[x["id"]] = x
        n += 1
    log(f"  burh: {n} of {len(data['burhs'])}")


def _fort_groups():
    """{qid: "Device Forts" | "Palmerston Forts"} for the members of those fort building programmes."""
    out = {}
    for parent, name in FORT_GROUPS.items():
        for r in _query(f"?i wdt:P361 wd:{parent} ."):
            out[r["i"]["value"].rsplit("/", 1)[-1]] = (name, r)
    return out


def build(log=print):
    recs = {}
    _burhs(recs, log)
    for qid, (name, r) in _fort_groups().items():
        x = _record("fort", LABELS["fort"], r)
        if x:
            x["type"] = f"Fort ({name})"
            recs.setdefault(x["id"], x)
    for kind, (label, classes) in CLASSES.items():
        got = []
        for cls in classes:                                 # one query per class keeps each one light
            for r in _query(f"?i wdt:P31 wd:{cls} ."):
                x = _record(kind, label, r)
                if x and not (kind == "fort" and x["year_start"] is not None and x["year_start"] < FORT_FROM):
                    got.append(x)
        for x in got:
            recs.setdefault(x["id"], x)
        log(f"  {kind}: {len(got)}")
    for r in recs.values():
        r["kind_group"] = GROUP
    return list(recs.values())


def run(log=print):
    t0 = time.time()
    conn = connect()
    conn.execute("PRAGMA busy_timeout = 120000")
    recs = build(log)
    place_stage.write(conn, recs, KINDS, GROUP, lambda kind, r: kind in REGROUP_FROM,
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
