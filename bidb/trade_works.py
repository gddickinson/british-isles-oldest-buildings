"""Build stage / CLI: markets and trade, works and manufacturers, infrastructure -> places (after bidb.burials).

    python -m bidb.trade_works            fetch (cached) and add / regroup
    python -m bidb.trade_works --report   counts

Every Wikidata item in the isles with coordinates of the classes below, at any date (the industrial
stage, bidb.era_places, keeps its 1700–1914 selection):
  "Markets & trade"            market halls and places, market crosses, corn exchanges, shops, arcades and
                               department stores, banks, inns, coffee houses, market towns; guild houses, livery
                               and cloth halls, stock exchanges, merchants' houses, and the livery companies at
                               their halls (bidb.livery); guild houses are never town halls (bidb.institutions)
  "Industrial heritage"        factories, mills of every kind, breweries, maltings, distilleries, brick, glass,
                               gas and water works, foundries, forges, furnaces, quarries, lime kilns, shipyards,
                               workshops and manufacturers
  "Infrastructure & utilities" Roman roads, causeways, fords, milestones; reservoirs, dams, weirs, sluices,
                               water towers, pumping stations, drinking fountains; sea walls and levees; canals
                               and locks; railway lines, signal boxes, funiculars; power stations, substations,
                               telephone exchanges; airports, bus stations, tram depots
Items in the building catalogue stay there; places of the other group stages and of the industrial and
Victorian stage keep their group. The researched oldest examples are lists of bidb.oldest_lists.
"""
import argparse
import json
import time

from . import era_places, livery, place_stage
from .db import connect
from .maritime import _record
from .place_stage import direct_items, rows_for

# kind: (group, label, Wikidata classes)
CLASSES = {
    "tr_market": ("Markets & trade", "Market hall or market place", {"Q2080521", "Q330284", "Q13033698"}),
    "tr_cross": ("Markets & trade", "Market cross", {"Q427926"}),
    "tr_exchange": ("Markets & trade", "Corn exchange", {"Q5171053"}),
    "tr_shop": ("Markets & trade", "Shop, store or arcade", {"Q213441", "Q216107", "Q97495053", "Q274393"}),
    "tr_bank": ("Markets & trade", "Bank", {"Q18761864"}),
    "tr_inn": ("Markets & trade", "Inn or coffee house", {"Q256020", "Q4236467"}),
    "tr_town": ("Markets & trade", "Market town", {"Q18511725"}),
    "tr_guild": ("Markets & trade", livery.GUILD_LABEL, {"Q1961493", "Q98034180", "Q977382"}),
    "tr_bourse": ("Markets & trade", "Stock exchange", {"Q11691"}),
    "tr_merchant": ("Markets & trade", "Merchant's house", {"Q1868065"}),
    "tr_livery": ("Markets & trade", "Livery company or guild", set()),          # from bidb.livery
    "iw_mill": ("Industrial heritage", "Mill (water, wind, tide, textile, paper)",
                {"Q44494", "Q185187", "Q38720", "Q493694", "Q946725", "Q8563702", "Q3973051", "Q918088"}),
    "iw_factory": ("Industrial heritage", "Factory, workshop or manufacturer", {"Q83405", "Q656720", "Q13235160"}),
    "iw_drink": ("Industrial heritage", "Brewery, maltings or distillery", {"Q131734", "Q943876", "Q1251750"}),
    "iw_works": ("Industrial heritage", "Brick, glass, gas or water works",
                 {"Q198632", "Q1179791", "Q1495738", "Q10373565"}),
    "iw_metal": ("Industrial heritage", "Foundry, forge or furnace", {"Q13883136", "Q1368573", "Q181485"}),
    "iw_quarry": ("Industrial heritage", "Quarry or lime kiln", {"Q188040", "Q59772"}),
    "iw_shipyard": ("Industrial heritage", "Shipyard", {"Q190928"}),
    "in_road": ("Infrastructure & utilities", "Road, causeway, ford or milestone",
                {"Q194029", "Q892168", "Q12743", "Q10145"}),
    "in_water": ("Infrastructure & utilities", "Reservoir, dam, weir or waterworks",
                 {"Q131681", "Q12323", "Q1066997", "Q610559", "Q274153", "Q446013", "Q1630622"}),
    "in_flood": ("Infrastructure & utilities", "Sea wall or embankment", {"Q1359152", "Q105190"}),
    "in_canal": ("Infrastructure & utilities", "Canal or lock", {"Q12284", "Q105731"}),
    "in_rail": ("Infrastructure & utilities", "Railway line, signal box or funicular", {"Q728937", "Q39015397", "Q142031"}),
    "in_power": ("Infrastructure & utilities", "Power station, substation or telephone exchange",
                 {"Q159719", "Q174814", "Q256132"}),
    "in_transport": ("Infrastructure & utilities", "Airport, bus station or tram depot", {"Q1248784", "Q494829", "Q27028153"}),
}
GUILD_CLASSES = CLASSES["tr_guild"][2]
FIRMS = {"Q783794", "Q4830453", "Q43229"}     # company, business, organisation: not a stock exchange's building
LABELS = {k: v[1] for k, v in CLASSES.items()}
GROUPS = {k: v[0] for k, v in CLASSES.items()}
KINDS = tuple(CLASSES)


def build(log=print):
    kinds = {}
    for kind, (_g, _l, classes) in CLASSES.items():
        for q, cls in (direct_items(classes) if classes else {}).items():
            if not (kind == "tr_bourse" and cls & FIRMS):
                kinds.setdefault(q, kind)
    recs = {}
    for r in rows_for(kinds):
        qid = r["i"]["value"].rsplit("/", 1)[-1]
        x = _record(kinds[qid], LABELS[kinds[qid]], r)
        if x and x["id"] not in recs:
            x["kind_group"], x["kind_label"] = GROUPS[x["kind"]], LABELS[x["kind"]]
            if r.get("end") and r["end"]["value"]:
                x["type"] = f"{LABELS[x['kind']]} (gone or closed)"
            recs[x["id"]] = x
    for x in livery.build(log):
        if x["kind"] == "tr_livery" or x["id"] not in recs:
            x["kind_group"], x["kind_label"] = GROUPS[x["kind"]], LABELS[x["kind"]]
            recs[x["id"]] = x
    log(f"  trade and works: {len(recs)} " + json.dumps({k: sum(r['kind'] == k for r in recs.values()) for k in KINDS}))
    return list(recs.values())


def run(log=print):
    t0 = time.time()
    conn = connect()
    conn.execute("PRAGMA busy_timeout = 120000")
    recs = build(log)
    guilds = [r["id"] for r in recs if r["kind"] == "tr_guild"]   # guild houses that an older build made town halls
    old = f"SELECT id FROM places WHERE kind = 'pi_civic' AND id IN ({','.join('?' * len(guilds))})"
    conn.execute(f"DELETE FROM places_fts WHERE id IN ({old})", guilds)
    conn.execute(f"DELETE FROM places WHERE id IN ({old})", guilds)
    keep = set(era_places.KINDS)                   # the industrial and Victorian stage's places keep their group
    for group in dict.fromkeys(GROUPS.values()):
        kinds = tuple(k for k in KINDS if GROUPS[k] == group)
        place_stage.write(conn, [r for r in recs if r["kind"] in kinds], kinds, group,
                          lambda kind, r: kind not in keep, lambda m: log(f"[{time.time() - t0:5.0f}s] {m}"))
    log(f"  livery companies linked to their hall: {livery.link_halls(conn)}")
    conn.commit()


def report(log=print):
    conn = connect()
    log(json.dumps({g: place_stage.report(conn, g) for g in dict.fromkeys(GROUPS.values())}, indent=1))


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--report", action="store_true")
    a = ap.parse_args()
    report() if a.report else run()


if __name__ == "__main__":
    main()
