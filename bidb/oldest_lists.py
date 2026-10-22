"""Research track / CLI / build stage: researched "oldest" lists of things that are not buildings.

    python -m bidb.oldest_lists           write their places (after the place stages)
    python -m bidb.oldest_lists --report  counts

Lists (`data/curated/oldest_<list>.json`, each entry with category, name, Wikidata id, coordinates, the
age claim, how well it is established, sources with exact quotes and a verdict):
  nature  - ancient trees and woods, oldest rocks, fossil sites, early human traces, natural wonders
            -> places group "Nature & deep time"
  graves  - oldest burials, gravestones, churchyards, cemeteries, notable graves
            -> places group "Graves & burial grounds" (with bidb.burials)
  trade   - oldest markets and fairs, market buildings, shops and trading firms -> "Markets & trade";
            manufacturers and industrial works -> "Industrial heritage" (with bidb.trade_works)
  infra   - oldest roads, water supply, railways, canals, harbours, power and communications
            -> "Infrastructure & utilities" (with bidb.trade_works)
An entry whose Wikidata item is already a catalogue building stays there; one already a place moves to the
list's group and takes the researched age. The sources become evidence claims (bidb.evidence.load), and
`lists()` feeds the "Oldest in nature" and "Oldest graves" sections of the Oldest page.
"""
import json
import re
import sys
import time

from .config import DATA_DIR

LISTS = {
    "nature": {"group": "Nature & deep time", "prefix": "nt", "title": "Oldest in nature",
               "kinds": {"Ancient tree": "nt_tree", "Ancient woodland or wood remains": "nt_wood",
                         "Oldest rock": "nt_rock", "Fossil site": "nt_fossil", "Early human traces": "nt_human",
                         "Natural wonder": "nt_wonder"}},
    "graves": {"group": "Graves & burial grounds", "prefix": "gr", "title": "Oldest graves and burial grounds",
               "kinds": {"Oldest burial": "gr_burial", "Oldest dated gravestone or grave marker": "gr_stone",
                         "Oldest churchyard or burial ground": "gr_churchyard", "Oldest cemetery": "gr_cemetery",
                         "Notable grave": "gr_grave"}},
    "trade": {"group": "Markets & trade", "prefix": "tr", "title": "Oldest markets, shops and manufacturers",
              "kinds": {"Oldest market or fair": "tro_market", "Oldest market building": "tro_building",
                        "Oldest shop or trading business": "tro_shop", "Oldest manufacturer": "tro_maker",
                        "Oldest industrial works": "tro_works"},
              "groups": {"Oldest manufacturer": "Industrial heritage", "Oldest industrial works": "Industrial heritage"}},
    "infra": {"group": "Infrastructure & utilities", "prefix": "in", "title": "Oldest infrastructure",
              "kinds": {"Oldest road or trackway": "ino_road", "Oldest water supply or drainage": "ino_water",
                        "Oldest railway, tramway or waggonway": "ino_rail", "Oldest canal or navigation": "ino_canal",
                        "Oldest harbour, dock or sea defence": "ino_harbour",
                        "Oldest power, gas or communications": "ino_power"}},
}
KIND_LABEL = {k: cat for spec in LISTS.values() for cat, k in spec["kinds"].items()}
KIND_GROUP = {k: spec.get("groups", {}).get(cat, spec["group"]) for spec in LISTS.values() for cat, k in spec["kinds"].items()}
KINDS = tuple(KIND_LABEL)


def path(name):
    return DATA_DIR / "curated" / f"oldest_{name}.json"


def slug(text):
    return re.sub(r"-+", "-", re.sub(r"[^a-z0-9]+", "-", text.lower())).strip("-")[:60]


def entries(name):
    try:
        return json.loads(path(name).read_text())["entries"]
    except (FileNotFoundError, ValueError, KeyError):
        return []


def record_id(name, e):
    return e.get("qid") or f"{LISTS[name]['prefix']}-{slug(e['name'])}"


def claims():
    """Evidence claims for every entry (read by bidb.evidence.load)."""
    out = []
    for name in LISTS:
        for e in entries(name):
            if e.get("sources"):
                out.append({"id": f"{name}-{slug(e['name'])}", "record": record_id(name, e), "name": e["name"],
                            "field": "age", "claim": f"{e.get('claim') or ''}. {e.get('evidence') or ''}".strip(". "),
                            "value": e.get("age_text"), "verdict": e.get("verdict") or "open",
                            "assessment": e.get("evidence") or "", "sources": e["sources"], "researched": "2026-10-22"})
    return out


def lists(conn=None):
    """{list: {title, group, categories: [{category, entries: [...]}]}} for the Oldest page."""
    ids = [record_id(n, e) for n in LISTS for e in entries(n)]
    buildings = {r[0] for r in conn.execute(f"SELECT id FROM buildings WHERE id IN ({','.join('?' * len(ids))})", ids)} \
        if conn is not None and ids else set()
    out = {}
    for name, spec in LISTS.items():
        cats = {}
        for e in entries(name):
            cats.setdefault(e["category"], []).append({
                "id": record_id(name, e), "name": e["name"], "age": e.get("age_text"), "year": e.get("year"),
                "claim": e.get("claim"), "verdict": e.get("verdict"), "location": e.get("location"),
                "nation": e.get("nation"), "museum": e.get("museum"), "building": record_id(name, e) in buildings})
        out[name] = {"title": spec["title"], "group": spec["group"],
                     "categories": [{"category": c, "entries": cats[c]} for c in spec["kinds"] if c in cats]}
    if conn is not None:
        out.update(oldest_places(conn))
    return out


PLACE_GROUPS = ("Markets & trade", "Industrial heritage", "Infrastructure & utilities", "Graves & burial grounds")


def oldest_places(conn, per=6):
    """The earliest dated places of each kind in the groups above (Wikidata dates, not checked)."""
    q = ",".join("?" for _ in PLACE_GROUPS)
    rows = conn.execute(f"""SELECT id, name, kind_group, kind_label, year_start, date_text, locality, nation FROM (
        SELECT *, ROW_NUMBER() OVER (PARTITION BY kind_group, kind_label ORDER BY year_start, name) AS n FROM places
        WHERE kind_group IN ({q}) AND year_start IS NOT NULL AND kind NOT IN ({",".join("?" for _ in KINDS)})
              AND kind_label NOT IN ({",".join("?" for _ in KIND_LABEL)}))
        WHERE n <= ? ORDER BY kind_group, kind_label, year_start""", (*PLACE_GROUPS, *KINDS, *KIND_LABEL.values(), per)).fetchall()
    out = {}
    for rid, name, group, label, year, text, loc, nation in rows:
        g = out.setdefault(group, {"title": f"Earliest dated: {group}", "group": group, "unchecked": True, "categories": {}})
        g["categories"].setdefault(label, []).append({"id": rid, "name": name, "age": text or str(year), "year": year,
                                                      "location": ", ".join(x for x in (loc, nation) if x)})
    return {f"places:{g}": {**v, "categories": [{"category": c, "entries": e} for c, e in v["categories"].items()]}
            for g, v in out.items()}


def records(name):
    from .place_records import blank          # place_kinds reads KIND_LABEL from here: import when used
    spec = LISTS[name]
    out = []
    for e in entries(name):
        if e.get("lat") is None:
            continue
        kind = spec["kinds"].get(e["category"])
        rid = record_id(name, e)
        out.append(blank(rid, kind, e["name"], kind_label=KIND_LABEL[kind], kind_group=KIND_GROUP[kind],
                         type=e["category"], description=e.get("claim"), year_start=e.get("year"),
                         date_text=e.get("age_text"), lat=e["lat"], lon=e["lon"], nation=e.get("nation"),
                         locality=e.get("location"), wikipedia_title=e.get("wikipedia_title"),
                         wikidata_id=e.get("qid"), source="Research (sources in Evidence)",
                         url=(e.get("sources") or [{}])[0].get("url"),
                         extra={"museum": e["museum"]} if e.get("museum") else None))
    return out


def run(log=print):
    from . import place_stage
    from .classify import period_for
    from .db import connect
    t0 = time.time()
    conn = connect()
    conn.execute("PRAGMA busy_timeout = 120000")
    for name, spec in LISTS.items():
        recs = records(name)
        for group in dict.fromkeys(KIND_GROUP[k] for k in spec["kinds"].values()):
            kinds = tuple(k for k in spec["kinds"].values() if KIND_GROUP[k] == group)
            part = [r for r in recs if r["kind"] in kinds]
            _new, moved, _cat = place_stage.write(conn, part, kinds, group, lambda kind, r: True,
                                                  lambda m: log(f"[{time.time() - t0:5.0f}s] {m}"))
            by = {r["id"]: r for r in part}
            conn.executemany("UPDATE places SET year_start = ?, date_text = ?, period = ?, type = ? WHERE id = ?",
                             [(by[i]["year_start"], by[i]["date_text"], period_for(by[i]["year_start"])
                               if by[i]["year_start"] is not None else "Unknown", by[i]["type"], i) for i in moved])
    conn.commit()


def report():
    for name, spec in LISTS.items():
        es = entries(name)
        print(f"{name}: {len(es)} entries", json.dumps({c: sum(e['category'] == c for e in es) for c in spec["kinds"]}))


if __name__ == "__main__":
    report() if sys.argv[1:] == ["--report"] else run()
