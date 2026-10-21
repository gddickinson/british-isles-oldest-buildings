"""Build stage / CLI: the Industrial Revolution and the Victorian era -> places (run after bidb.places_build).

    python -m bidb.era_places            fetch (cached) and add these places
    python -m bidb.era_places --report   counts

Wikidata items in the isles with coordinates and a founding date (P571):
  Industrial heritage group  mills and factories, mines and quarries, ironworks and foundries,
      canals, locks and aqueducts, railway stations, viaducts and tunnels, engine houses, pumping
      stations, gasworks and water towers, kilns, iron and suspension bridges, warehouses and
      breweries, dated 1700–1914 (mills of all ages are kept only in that span)
  Victorian era group  public buildings dated 1837–1901 (town halls, workhouses, prisons, market
      halls, theatres, libraries, museums, hospitals and asylums, schools, almshouses, piers,
      glasshouses, tram depots) and anything in the Victorian architecture style (P149)
Items already in the building catalogue or among the places are left as they are.
"""
import argparse
import json
import time

from .db import connect
from .http import sparql
from .lore_places import ISLES
from .maritime import _items, _record
from .place_records import PLACE_COLUMN_NAMES

INDUSTRIAL = {  # kind: (label, classes)
    "mill": ("Mill or factory", ["Q83405", "Q46398483", "Q946725", "Q104200053", "Q185187", "Q38720"]),
    "mine": ("Mine or quarry", ["Q959309", "Q820477", "Q16659581", "Q16764598"]),
    "ironworks": ("Ironworks or foundry", ["Q10832530", "Q181485", "Q13883136"]),
    "canal": ("Canal, lock or aqueduct", ["Q12284", "Q474", "Q105731"]),
    "railway": ("Railway station, viaduct or tunnel", ["Q55488", "Q181348", "Q39486269", "Q1311958", "Q10283556"]),
    "engine": ("Engine house, pumping station or works", ["Q1342377", "Q446013", "Q1495738", "Q274153"]),
    "kiln": ("Kiln", ["Q59772", "Q1621967"]),
    "ironbridge": ("Iron or suspension bridge", ["Q21170235", "Q12570"]),
    "warehouse": ("Warehouse or brewery", ["Q181623", "Q57778855"]),
}
VICTORIAN = {
    "victorian_public": ("Victorian public building", ["Q628155", "Q25550691", "Q40357", "Q2080521", "Q24354", "Q28564",
                                                       "Q24699794", "Q39364723", "Q210999", "Q1244442", "Q15548045"]),
    "victorian_leisure": ("Victorian pier, glasshouse or tram depot", ["Q863454", "Q165044", "Q27028153"]),
}
INDUSTRIAL_YEARS, VICTORIAN_YEARS = (1700, 1914), (1837, 1901)
KINDS = tuple(INDUSTRIAL) + tuple(VICTORIAN) + ("victorian_style",)
GROUPS = {**{k: "Industrial heritage" for k in INDUSTRIAL}, **{k: "Victorian era" for k in VICTORIAN},
          "victorian_style": "Victorian era"}


def _victorian_style():
    """Anything in the Victorian architecture style (Q565165) in the isles."""
    return sparql(f"""SELECT ?i ?iLabel ?coord ?article ?desc ?start ?end WHERE {{
        ?i wdt:P149 wd:Q565165 ; wdt:P625 ?coord ; wdt:P17 ?c . VALUES ?c {{ {ISLES} }}
        OPTIONAL {{ ?i wdt:P571 ?s BIND(YEAR(?s) AS ?start) }} OPTIONAL {{ ?i wdt:P576 ?e BIND(YEAR(?e) AS ?end) }}
        OPTIONAL {{ ?article schema:about ?i ; schema:isPartOf <https://en.wikipedia.org/> }}
        OPTIONAL {{ ?i schema:description ?desc FILTER(lang(?desc) = "en") }}
        SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en". }} }}""")


def build(log=print):
    recs = {}
    for table, years in ((INDUSTRIAL, INDUSTRIAL_YEARS), (VICTORIAN, VICTORIAN_YEARS)):
        for kind, (label, classes) in table.items():
            got = []
            for cls in classes:                          # one query per class keeps each one light
                got += [x for x in (_record(kind, label, r) for r in _items([cls])) if x]
            got = [x for x in got if x["year_start"] is not None and years[0] <= x["year_start"] <= years[1]]
            for x in got:
                recs.setdefault(x["id"], x)
            log(f"  {kind}: {len(got)}")
    style = [x for x in (_record("victorian_style", "Victorian building", r) for r in _victorian_style()) if x]
    for x in style:
        recs.setdefault(x["id"], x)
    log(f"  victorian_style: {len(style)}")
    for r in recs.values():
        r["kind_group"] = GROUPS[r["kind"]]
    return list(recs.values())


def run(log=print):
    from . import places_db
    from .enrich import wikipedia_intros
    t0 = time.time()
    conn = connect()
    conn.execute("PRAGMA busy_timeout = 120000")
    recs = build(log)
    known = {q for (q,) in conn.execute("SELECT wikidata_id FROM buildings WHERE wikidata_id IS NOT NULL")}
    known |= {q for (q,) in conn.execute(f"SELECT wikidata_id FROM places WHERE wikidata_id IS NOT NULL "
                                         f"AND kind NOT IN ({','.join('?' for _ in KINDS)})", KINDS)}
    new = [r for r in recs if r["id"] not in known]
    intros = wikipedia_intros([r["wikipedia_title"] for r in new if r.get("wikipedia_title")])
    for r in new:
        got = intros.get(r.get("wikipedia_title") or "") or {}
        r["wikipedia_extract"] = (got.get("extract") or "")[:900] or None
        r["image_thumb"] = got.get("image")
    q = ",".join("?" for _ in KINDS)
    conn.execute(f"DELETE FROM places_fts WHERE id IN (SELECT id FROM places WHERE kind IN ({q}))", KINDS)
    conn.execute(f"DELETE FROM places WHERE kind IN ({q})", KINDS)
    ph = ", ".join("?" for _ in PLACE_COLUMN_NAMES)
    conn.executemany(f"INSERT OR REPLACE INTO places VALUES ({ph})", [[r.get(c) for c in PLACE_COLUMN_NAMES] for r in new])
    cols = places_db.PLACE_FTS
    conn.executemany(f"INSERT INTO places_fts (id, {', '.join(cols)}) VALUES (?, {', '.join('?' for _ in cols)})",
                     [[r["id"]] + [r.get(c) or "" for c in cols] for r in new])
    conn.commit()
    log(f"[{time.time() - t0:5.0f}s] {len(new)} new places ({sum(r['kind_group'] == 'Victorian era' for r in new)} "
        f"Victorian, {sum(r['kind_group'] == 'Industrial heritage' for r in new)} industrial); "
        f"{len(recs) - len(new)} already in the database")


def report(log=print):
    conn = connect()
    q = ",".join("?" for _ in KINDS)
    log(json.dumps(dict(conn.execute(f"SELECT kind_label, COUNT(*) FROM places WHERE kind IN ({q}) GROUP BY 1", KINDS)
                        .fetchall()), indent=1))


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--report", action="store_true")
    a = ap.parse_args()
    report() if a.report else run()


if __name__ == "__main__":
    main()
