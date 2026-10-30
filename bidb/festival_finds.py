"""What the catalogue already holds for each festival of bidb.festivals (page /festivals): churches of its saints,
stories that mention it, researched sky alignments of its sun event, places of its kinds or names, people linked
to buildings, what happened on its day, and the oldest customs and things of the page /things that belong to it.

`FIND` (chosen here, not by research) says where to look for each festival:
  dedications   catalogue `dedication` labels (Wikidata's saint names)
  words         regular expression (whole words, any case) for stories and oldest things
  sky           bidb.sky events of researched alignments (data/curated/sky_alignments.json)
  place_kinds   place kinds taken whole; `place_words` (regex on the place name) narrows them, or alone picks
                places of any kind by name
  people        Wikidata ids of people whose linked buildings and places belong to the festival
`page(conn, fid)` gives one festival with its finds; `index(conn)` every festival for the page and the hosted copy
(`python -m bidb.festival_finds [id]` prints the counts).
"""
import json
import re
import sys

from . import festivals
from .config import ROOT

SKY = ROOT / "data" / "curated" / "sky_alignments.json"
CHURCHES_SHOWN = 24
STORIES_SHOWN = 30
PLACES_SHOWN = 60
# names that only locate something by a nearby church, farm or road, or are clubs and works named after one
NOT_PLACE = re.compile(r"\b(\d+ ?m|yards?|milestones?|mileposts?|f\.?c\.?|farm|lane|road|street|park|"
                       r"tank|works|mills?|school|hospital|university|college|club)\b|\b(north|south|east|west) of\b", re.I)

FIND = {
    "christmas": {"dedications": ["Saint Nicholas", "Saint Stephen", "John the Evangelist", "Jesus Christ"],
                  "words": r"christmas|yule(tide)?|nativity|carols?|mince pies?|plum pudding|twelfth night|"
                           r"wassail\w*|mistletoe|holly|midwinter|winter solstice|plygain",
                  "sky": ["winter_solstice"]},
    "new-year": {"words": r"hogmanay|new year'?s?|first[- ]foot\w*|twelfth night|epiphany|wassail\w*|calennig|"
                          r"up helly aa|haxey hood|burning of the clavie",
                 "dedications": ["Epiphany"]},
    "burns-night": {"words": r"robert burns|rabbie burns|burns supper|haggis|tam o'? ?shanter|auld lang syne",
                    "people": ["Q81960"]},
    "imbolc": {"dedications": ["Brigid of Kildare"],
               "words": r"imbolc|st\.? (brigid|bride|bridget)|saint (brigid|bride|bridget)|brigid'?s cross|candlemas|"
                        r"laa'?l breeshey",
               "sky": ["imbolc"], "place_kinds": ["holy_well"], "place_words": r"\b(brigid|bride|bridget|brigit)'?s?\b"},
    "valentine": {
                  "words": r"valentine'?s?|dwynwen|love ?spoons?|lovers'? leap|lovers",
                  "place_words": r"\bdwynwen"},
    "st-david": {"dedications": ["Saint David", "Non"],
                 "words": r"st\.? david'?s day|saint david|dewi sant|daffodils?|\bleeks?\b|st\.? non\b"},
    "st-patrick": {"dedications": ["Saint Patrick"],
                   "words": r"st\.? patrick|saint patrick|shamrock|croagh patrick|patrick'?s purgatory|reek sunday",
                   "place_words": r"\b(st\.? patrick'?s?|saint patrick'?s?|tobar ph[aá]draig)\b"},
    "easter": {"dedications": ["True Cross", "Holy Sepulchre"],
               "words": r"easter|lent|shrove(tide| tuesday)|pancakes?|good friday|maundy|palm sunday|hot cross buns?|"
                        r"easter sepulchre|spring equinox|vernal equinox",
               "sky": ["equinox"]},
    "st-george": {"dedications": ["Saint George"],
                  "words": r"st\.? george'?s? day|saint george|dragon|order of the garter|mummers?"},
    "may-day": {"words": r"may ?day|beltane|bealtaine|maypoles?|may queen|'?obby '?oss|furry dance|jack[- ]in[- ]the[- ]green|"
                         r"garland day|oak apple day|morris( men| danc\w+)?|may morning",
                "sky": ["beltane"], "place_words": r"\b(maypole|beltane|may ?day)\b"},
    "midsummer": {"dedications": ["John the Baptist"],
                  "words": r"midsummer|summer solstice|st\.? john'?s eve|saint john'?s eve|golowan|bonfires?|"
                           r"longest day|tynwald day",
                  "sky": ["summer_solstice"], "place_words": r"\b(midsummer|solstice)\b"},
    "lammas": {
               "words": r"lammas|lughnasa\w*|lughnasadh|lugh\b|puck fair|reek sunday|garland sunday|bilberry sunday|"
                        r"harvest fair|tailtiu|teltown",
               "sky": ["lughnasa"], "place_words": r"\b(lammas|lughnasa\w*)\b"},
    "michaelmas": {"dedications": ["Michael"],
                   "words": r"michaelmas|st\.? michael|saint michael|harvest( home| festival)?|mop fairs?|hiring fairs?|"
                            r"goose fair|corn doll(y|ies)"},
    "halloween": {"dedications": ["All Saints' Day", "All Souls' Day"],
                  "words": r"hallowe'?en|all hallows|samhain|all saints'? day|all souls|ghosts?|haunted|haunts?|"
                           r"spectral|apparitions?|witch(es|craft)?|souling|soul cakes?|hop-tu-naa|punkie|"
                           r"otherworld|banshees?|fairies|faery",
                  "sky": ["samhain"], "place_kinds": ["haunted"]},
    "bonfire-night": {"words": r"gunpowder plot|guy fawkes|bonfire night|catesby|plotters?|fifth of november|"
                               r"5 november|bonfire societ\w+|tar barrels?",
                      "people": ["Q295279", "Q373493"]},
    "st-andrew": {"dedications": ["Andrew the Apostle"],
                  "words": r"st\.? andrew'?s? day|saint andrew|st\.? rule|st\.? regulus|saltire|athelstaneford"},
}


def _rx(spec, key="words"):
    return re.compile(r"\b(?:%s)\b" % spec[key], re.I) if spec.get(key) else None


def churches(conn, labels):
    """(count, oldest CHURCHES_SHOWN records, map points [id, lat, lon]) of catalogue records with these dedications."""
    if not labels:
        return 0, [], []
    q = ",".join("?" * len(labels))
    rows = conn.execute(f"""SELECT id, name, year_start, date_text, locality, nation, lat, lon, image_thumb, dedication
        FROM buildings WHERE dedication IN ({q}) ORDER BY year_start IS NULL, year_start""", labels).fetchall()
    keys = ("id", "name", "year", "date_text", "locality", "nation", "lat", "lon", "image_thumb", "dedication")
    return (len(rows), [dict(zip(keys, r)) for r in rows[:CHURCHES_SHOWN]],
            [[r[0], round(r[6], 4), round(r[7], 4)] for r in rows if r[6] is not None])


_STORIES = {}


def _all_stories(conn):
    """Every story with its record (the columns of bidb.stories_db.search), read once per connection."""
    if id(conn) not in _STORIES:
        from .stories_db import KINDS
        cols = ["entity_kind", "entity_id", "kind", "heading", "text", "source_url", "name", "nation", "locality",
                "lat", "lon", "image_thumb", "date_text", "licence"]
        try:
            rows = conn.execute("""SELECT s.entity_kind, s.entity_id, s.kind, s.heading, s.text, s.source_url,
                COALESCE(b.name, p.name), COALESCE(b.nation, p.nation), COALESCE(b.locality, p.locality),
                COALESCE(b.lat, p.lat), COALESCE(b.lon, p.lon), COALESCE(b.image_thumb, p.image_thumb),
                COALESCE(b.date_text, p.date_text), s.licence
                FROM stories s LEFT JOIN buildings b ON b.id = s.entity_id AND s.entity_kind = 'building'
                LEFT JOIN places p ON p.id = s.entity_id AND s.entity_kind = 'place'""").fetchall()
        except Exception:      # no stories table yet
            rows = []
        _STORIES[id(conn)] = [dict(zip(cols, r)) | {"kind_label": KINDS.get(r[2], r[2])} for r in rows if r[6]]
    return _STORIES[id(conn)]


def stories(conn, rx):
    """(count, stories) with a whole-word match, best first: those naming the festival most, curiosities after
    legends, folklore and the supernatural, longer before shorter."""
    if not rx:
        return 0, []
    cand = [r for r in _all_stories(conn) if rx.search(r["text"])]
    cand.sort(key=lambda r: (-len(rx.findall(r["text"])), r["kind"] == "curiosity", -len(r["text"])))
    return len(cand), cand[:STORIES_SHOWN]


def sky(events):
    if not events or not SKY.exists():
        return []
    keep = ("id", "record", "name", "lat", "lon", "body", "event", "rise_set", "claim", "verdict", "viewing")
    return [{k: a.get(k) for k in keep} for a in json.loads(SKY.read_text())["alignments"] if a.get("event") in events]


def places(conn, spec):
    """(count, places) of the festival's kinds narrowed by its name words, or of any kind by name words."""
    kinds, rx = spec.get("place_kinds") or [], _rx(spec, "place_words")
    if not kinds and not rx:
        return 0, []
    if kinds:
        rows = conn.execute(f"""SELECT id, name, kind, kind_label, year_start, date_text, locality, nation, lat, lon,
            image_thumb FROM places WHERE kind IN ({','.join('?' * len(kinds))})""", kinds).fetchall()
        if rx and spec.get("place_kinds") != ["haunted"]:
            rows = [r for r in rows if rx.search(r[1] or "")]
    else:
        words = re.findall(r"[a-z]{4,}", re.sub(r"\\[a-z]", " ", spec["place_words"]), re.I)
        rows = []
        for w in set(words):
            rows += conn.execute("""SELECT id, name, kind, kind_label, year_start, date_text, locality, nation, lat, lon,
                image_thumb FROM places WHERE name LIKE ?""", (f"%{w}%",)).fetchall()
        rows = list({r[0]: r for r in rows if rx.search(r[1] or "") and not NOT_PLACE.search(r[1] or "")}.values())
    keys = ("id", "name", "kind", "kind_label", "year", "date_text", "locality", "nation", "lat", "lon", "image_thumb")
    rows.sort(key=lambda r: (r[4] is None, r[4] or 0))
    return len(rows), [dict(zip(keys, r)) for r in rows[:PLACES_SHOWN]]


def people(conn, qids):
    """Buildings and places linked to these people (bidb.people), with the person and role."""
    if not qids:
        return []
    q = ",".join("?" * len(qids))
    rows = conn.execute(f"""SELECT p.name, l.role, l.target_type, l.target_id,
        COALESCE(b.name, pl.name), COALESCE(b.lat, pl.lat), COALESCE(b.lon, pl.lon), COALESCE(b.date_text, pl.date_text)
        FROM person_links l JOIN persons p ON p.id = l.person_id
        LEFT JOIN buildings b ON b.id = l.target_id LEFT JOIN places pl ON pl.id = l.target_id
        WHERE l.person_id IN ({q})""", qids).fetchall()
    keys = ("person", "role", "kind", "id", "name", "lat", "lon", "date_text")
    return [dict(zip(keys, r)) for r in rows if r[4]]


def on_the_day(conn, when):
    """What happened on a fixed-date festival's day (bidb.on_this_day), events before people, oldest first."""
    if not when.get("date"):
        return []
    from .on_this_day import for_day
    m, d = (int(x) for x in when["date"].split("-"))
    try:
        return for_day(conn, m, d, limit=20)
    except Exception:          # no on_this_day table yet
        return []


def things(rx):
    """Entries of the page /things whose name, claim or evidence matches."""
    if not rx:
        return []
    from .oldest_things import THEMES, entries, entry_id
    out = []
    for t in THEMES:
        for e in entries(t):
            if rx.search(" ".join(str(e.get(k, "")) for k in ("name", "claim", "evidence"))):
                out.append({"id": entry_id(t, e), "theme": t, "name": e["name"], "age_text": e["age_text"],
                            "claim": e["claim"], "where": e.get("where")})
    return out


def link_places(conn, f):
    """The catalogue record or place of each researched place and fact location, by its Wikidata id."""
    ids = {p.get("qid") for p in f.get("places", [])} | {(x.get("where") or {}).get("qid") for x in f.get("facts", [])}
    ids.discard(None)
    if not ids:
        return {}
    q = ",".join("?" * len(ids))
    out = {r[0]: ["building", r[0]] for r in conn.execute(f"SELECT id FROM buildings WHERE id IN ({q})", list(ids))}
    for pid, qid in conn.execute(f"SELECT id, wikidata_id FROM places WHERE wikidata_id IN ({q})", list(ids)):
        out.setdefault(qid, ["place", pid])
    return out


def page(conn, fid):
    """One festival: its researched file, sources with their last check, and the catalogue's finds."""
    f = next((x for x in festivals.load() if x["id"] == fid), None)
    if not f:
        return None
    spec, ck = FIND.get(fid, {}), festivals.checks()
    rx = _rx(spec)
    links = link_places(conn, f)

    def checked(cid, item):
        res = ck.get(cid, {}).get("sources", [])
        return {**item, "link": links.get(item.get("qid") or (item.get("where") or {}).get("qid")),
                "sources": [{**s, "check": res[i] if i < len(res) else None} for i, s in enumerate(item["sources"])]}
    n_ch, ch, ch_points = churches(conn, spec.get("dedications"))
    n_st, st = stories(conn, rx)
    n_pl, pl = places(conn, spec)
    return {**{k: v for k, v in f.items() if k not in ("facts", "places")},
            "facts": [checked(f"fest-{fid}-{festivals.slug(x['title'])}", x) for x in f.get("facts", [])],
            "places": [checked(f"fest-{fid}-place-{festivals.slug(p['name'])}", p) for p in f.get("places", [])],
            "finds": {"dedications": spec.get("dedications", []), "churches": ch, "church_count": n_ch,
                      "church_points": ch_points, "stories": st, "story_count": n_st, "sky": sky(spec.get("sky")),
                      "places": pl, "place_count": n_pl, "people": people(conn, spec.get("people")),
                      "on_the_day": on_the_day(conn, f["when"]), "things": things(rx)}}


def index(conn=None):
    """Every festival for the page's cards: id, title, also, season, when, when_text, intro, counts."""
    out = []
    for f in festivals.load():
        spec = FIND.get(f["id"], {})
        n_ch = churches(conn, spec.get("dedications"))[0] if conn else None
        out.append({k: f.get(k) for k in ("id", "title", "also", "season", "when", "when_text", "intro")}
                   | {"facts": len(f.get("facts", [])), "places": len(f.get("places", [])), "churches": n_ch})
    return out


def export(conn):
    """{index, pages} for the hosted copy (app.static_tours writes data/festivals.json)."""
    return {"index": index(conn), "pages": {f["id"]: page(conn, f["id"]) for f in festivals.load()}}


if __name__ == "__main__":
    import sqlite3
    from .config import db_path
    con = sqlite3.connect(db_path())
    for f in festivals.load():
        if len(sys.argv) > 1 and f["id"] not in sys.argv[1:]:
            continue
        p = page(con, f["id"])["finds"]
        print(f"{f['id']:14} churches {p['church_count']:4}  stories {p['story_count']:4}  sky {len(p['sky']):2}  "
              f"places {p['place_count']:4}  people {len(p['people']):3}  day {len(p['on_the_day']):3}  things {len(p['things'])}")
