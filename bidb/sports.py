"""Build stage / CLI: sports grounds, stadiums and clubs -> places group "Sport & leisure" (after bidb.trade_works).

    python -m bidb.sports            fetch (cached) and add / regroup
    python -m bidb.sports --report   counts

Venues: every Wikidata item in the isles with coordinates whose class is a sports venue or one of its
subclasses (training colleges, function halls, marinas and the like left out), plus lidos, public baths,
bowling greens and tennis courts, by type: football grounds, rugby grounds, stadiums and arenas, cricket
grounds, golf courses and clubs, racecourses and circuits, swimming baths and lidos, other venues.
Clubs: sports clubs and teams (subclasses of sports club and sports team; national teams left out), placed at
their own coordinates or else at their home ground (P115): football, rugby, cricket, rowing and sailing, other.
Items in the building catalogue stay there; places of the other group stages keep their group. The researched
oldest examples are the "sport" list of bidb.oldest_lists.
"""
import argparse
import json
import re
import time

# the stage's modules are imported when it runs: bidb.place_kinds reads LABELS from here

GROUP = "Sport & leisure"
SPORTS_VENUE, SPORTS_CLUB, SPORTS_TEAM = "Q1076486", "Q847017", "Q12973014"
# kind: (label, classes); the first kind whose classes an item has wins, the last kind of each set takes the rest
VENUES = {
    "sp_football": ("Football ground", {"Q1154710", "Q124017602", "Q105755419", "Q126946265"}),
    "sp_rugby": ("Rugby ground", {"Q45290083", "Q15303456", "Q13054561"}),
    "sp_cricket": ("Cricket ground", {"Q682943"}),
    "sp_golf": ("Golf course or club", {"Q2022036", "Q1048525", "Q100148147", "Q1054671"}),
    "sp_racing": ("Racecourse, circuit or track", {"Q11822917", "Q1777138", "Q2338524", "Q926439", "Q778020",
                                                    "Q28174251", "Q1232319", "Q105360482", "Q357121", "Q830528"}),
    "sp_swim": ("Swimming baths, pool or lido", {"Q1501", "Q1757063", "Q2531616", "Q200023", "Q357380", "Q13586493",
                                                  "Q27106886", "Q740326", "Q15411990"}),
    "sp_gaelic": ("Gaelic games ground", set()),
    "sp_stadium": ("Stadium or arena", {"Q483110", "Q1049757", "Q641226", "Q1763828", "Q27951514"}),
    "sp_venue": ("Other sports venue", set()),
}
EXTRA_VENUES = {"Q1757063", "Q2531616", "Q895453", "Q741118"}           # lido, public bath, bowling green, tennis court
NOT_SPORT = {"Q2400020", "Q917182", "Q1935049", "Q1522839", "Q1898357", "Q29918961", "Q721207", "Q131370352",
             "Q12193401", "Q184590", "Q20635181"}   # halls, military and staff colleges, marinas, scout camps, runways, debating
CLUBS = {
    "spc_football": ("Football club", {"Q476028", "Q28140340", "Q94579592", "Q51481377", "Q15944511", "Q103229495"}),
    "spc_rugby": ("Rugby club", {"Q15221215", "Q43009164", "Q14645593", "Q63171169", "Q113144812", "Q63171186"}),
    "spc_cricket": ("Cricket club", {"Q17376093"}),
    "spc_water": ("Rowing, sailing or yacht club", {"Q7372078", "Q1855011", "Q114837185", "Q117314155", "Q4931504",
                                                     "Q1728211"}),
    "spc_gaelic": ("Gaelic games club", {"Q47006607"}),
    "spc_other": ("Other sports club or team", set()),
}
# a name says more than a loose class: (kinds it may refine, pattern, kind)
NAMED = [
    ({"sp_venue", "sp_stadium", "sp_football"}, r"\b(GAA|Páirc|Pairc|Gaelic|Croke Park|Casement Park)\b", "sp_gaelic"),
    ({"sp_venue", "sp_stadium"}, r"\bcricket\b|\bBat and Ball\b", "sp_cricket"),
    ({"sp_venue"}, r"\bgolf\b|\blinks\b", "sp_golf"),
    ({"sp_venue", "sp_stadium"}, r"\b(racecourse|greyhound|speedway|raceway|circuit|velodrome|motor ?sport)\b", "sp_racing"),
    ({"sp_venue"}, r"\b(baths|lido|swimming|pool)\b", "sp_swim"),
    ({"spc_other", "spc_football"}, r"\b(GAA|GAC|Gaels|Gaelic|hurling|camogie|CLG)\b", "spc_gaelic"),
    ({"spc_other"}, r"\bcricket\b", "spc_cricket"),
    ({"spc_other"}, r"\b(R\.?L\.?F\.?C|R\.?U\.?F\.?C|rugby)\b", "spc_rugby"),
    ({"spc_other"}, r"\b(rowing|boat club|yacht|sailing|canoe)\b", "spc_water"),
    ({"spc_football"}, r"\b(hockey|rugby|cricket)\b", "spc_other"),
]


def refine(kind, name):
    """The kind a record's name points to (e.g. a "sports venue" called "… Cricket Ground")."""
    for kinds, pattern, to in NAMED:
        if kind in kinds and re.search(pattern, name or "", re.I):
            return to
    return kind
NATIONAL = {"Q135408445", "Q58840819", "Q23905105"}                        # national teams
LABELS = {k: v[0] for k, v in {**VENUES, **CLUBS}.items()}
KINDS = tuple(LABELS)
VENUE_COORD = "{ ?i wdt:P625 ?own } UNION { ?i wdt:P115/wdt:P625 ?home } BIND(COALESCE(?own, ?home) AS ?coord)"


def kind_for(classes, table):
    """The first kind of `table` whose classes meet `classes`, else the table's last (catch-all) kind."""
    for kind, (_label, cls) in table.items():
        if cls & classes:
            return kind
    return list(table)[-1]


def clubs():
    """{qid: set of classes} for sports clubs and teams with coordinates or a home ground that has them."""
    from .http import sparql
    from .place_stage import COUNTRIES
    out = {}
    for c in COUNTRIES:
        for root in (SPORTS_CLUB, SPORTS_TEAM):
            for r in sparql(f"""SELECT DISTINCT ?i ?cls WHERE {{ ?i wdt:P31 ?cls ; wdt:P17 {c} .
                    ?cls wdt:P279* wd:{root} . {{ ?i wdt:P625 [] }} UNION {{ ?i wdt:P115/wdt:P625 [] }} }}"""):
                out.setdefault(r["i"]["value"].rsplit("/", 1)[-1], set()).add(r["cls"]["value"].rsplit("/", 1)[-1])
    return out


def build(log=print):
    from .maritime import _record
    from .place_stage import direct_items, rows_for, subclass_items
    kinds = {}
    venues = subclass_items(SPORTS_VENUE)
    for q, cls in direct_items(EXTRA_VENUES).items():
        venues.setdefault(q, set()).update(cls)
    for q, cls in venues.items():
        if not cls & NOT_SPORT:
            kinds[q] = kind_for(cls, VENUES)
    venue_ids = set(kinds)
    for q, cls in clubs().items():
        if q not in kinds and not cls & (NATIONAL | NOT_SPORT):
            kinds[q] = kind_for(cls, CLUBS)
    recs = {}
    for ids, coord in ((venue_ids, "?i wdt:P625 ?coord ."), (set(kinds) - venue_ids, VENUE_COORD)):
        for r in rows_for(ids, coord=coord):
            qid = r["i"]["value"].rsplit("/", 1)[-1]
            kind = refine(kinds[qid], r["iLabel"]["value"])
            x = _record(kind, LABELS[kind], r)
            if x and x["id"] not in recs:
                x["kind_group"], x["kind_label"] = GROUP, LABELS[x["kind"]]
                if r.get("end") and r["end"]["value"]:
                    x["type"] = f"{LABELS[x['kind']]} (gone or closed)"
                recs[x["id"]] = x
    log(f"  sport: {len(recs)} " + json.dumps({k: sum(r['kind'] == k for r in recs.values()) for k in KINDS}))
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
