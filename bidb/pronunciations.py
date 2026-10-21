"""Build stage: how names are said, with regional and language varieties.

    python -m bidb.pronunciations            # after bidb.build / places_build (cached; resumable)
    python -m bidb.pronunciations --report   # coverage only

For every building, place and person with a Wikipedia article or Wikidata item, and for the
towns they lie in (Wikidata P131), collects pronunciations from the article opening (IPA,
respelling, audio, native names: see pron_parse) and from Wikidata (P443 recordings, e.g. the
Lingua Libre Welsh place names, and P898 IPA). Writes tables `pronunciations` and `pron_towns`.
"""
import argparse
import re
import time
from urllib.parse import quote, unquote

from . import places_db, pron_db, pron_wiktionary
from .config import require_locations
from .db import connect, set_other_names
from .http import sparql
from .pron_parse import ISLES_LANGS, parse_lead, variety_of
from .pron_sources import wikidata_pronunciations, wikipedia_leads

WIKI = "https://en.wikipedia.org/wiki/"


def _entities(conn):
    """[(kind, id, qid, wikipedia title, name)] for buildings, places and people."""
    out = [("building", i, q, t, n) for i, q, t, n in conn.execute(
        "SELECT id, wikidata_id, wikipedia_title, name FROM buildings")]
    out += [("place", i, q, t, n) for i, q, t, n in conn.execute(
        "SELECT id, wikidata_id, wikipedia_title, name FROM places")]
    out += [("person", i, i, t, n) for i, t, n in conn.execute(
        "SELECT id, wikipedia_title, name FROM persons")]
    return [(k, i, q or "", t or "", n or "") for k, i, q, t, n in out]


def towns_for(qids, log=print, chunk=300):
    """{record qid: [(town qid, town label, enwiki title)]} from Wikidata P131."""
    qids = sorted({q for q in qids if q and q.startswith("Q")})
    out = {}
    for i in range(0, len(qids), chunk):
        values = " ".join(f"wd:{q}" for q in qids[i:i + chunk])
        rows = sparql(f"""SELECT ?i ?t ?tLabel ?article WHERE {{
          VALUES ?i {{ {values} }} ?i wdt:P131 ?t.
          OPTIONAL {{ ?article schema:about ?t; schema:isPartOf <https://en.wikipedia.org/> }}
          SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en". }} }}""")
        for b in rows:
            rec = b["i"]["value"].rsplit("/", 1)[-1]
            town = b["t"]["value"].rsplit("/", 1)[-1]
            title = b.get("article", {}).get("value", "").rsplit("/wiki/", 1)[-1]
            out.setdefault(rec, []).append((town, b.get("tLabel", {}).get("value", town),
                                            unquote(title).replace("_", " ")))
        if (i // chunk) % 20 == 0:
            log(f"  towns: {min(i + chunk, len(qids))}/{len(qids)} items")
    return out


def _wiki_rows(kind, eid, title, lead):
    url = WIKI + quote(title.replace(" ", "_")) if title else ""
    rows = parse_lead(lead, title)
    if kind == "person":            # the bold name may be a birth name or full title: use the article's
        short = re.sub(r"\s*\(.*\)$", "", title)
        for r in rows:
            if r["lang"] == "en":
                r["name"] = short
    return [{**r, "entity_kind": kind, "entity_id": eid, "source": "Wikipedia", "source_url": url,
             "licence": pron_db.SOURCES["Wikipedia"]} for r in rows]


def _wd_rows(kind, eid, qid, name, rows, wiki):
    """Wikidata rows, skipping what the article already gave and attaching a recording to the
    article's native-name row in the same language (Tintern Abbey -> "Abaty Tyndyrn" + audio)."""
    out = []
    have_audio = {r["audio"] for r in wiki if r["audio"]}
    have_ipa = {(r["lang"].split("-")[0], r["ipa"].strip("/[] ")) for r in wiki if r["ipa"]}
    for r in rows:
        ipa = r["ipa"].strip("/[] ")
        base = r["lang"].split("-")[0]
        if base not in ISLES_LANGS:
            continue                                   # e.g. a Marathi recording of "London"
        if (r["audio"] and r["audio"] in have_audio) or (ipa and (base, ipa) in have_ipa):
            continue                                   # already from the article
        if r["audio"]:
            same = next((w for w in wiki if w["lang"] == base and not w["audio"]), None)
            if same:
                same["audio"] = r["audio"]
                have_audio.add(r["audio"])
                continue
        out.append({**r, "ipa": ipa, "name": r["name"] or name, "variety": variety_of(r["lang"]),
                    "lang": base, "entity_kind": kind, "entity_id": eid, "source": "Wikidata",
                    "source_url": f"https://www.wikidata.org/wiki/{qid}",
                    "licence": pron_db.SOURCES["Wikidata"]})
    return out


def _norm(ipa):
    return re.sub(r"[./\[\]ˈˌ ]", "", ipa)


def _wikt_rows(eid, name, entry, have):
    """Wiktionary rows for a town that add a form (or variety) not already given."""
    seen = {(r["lang"], _norm(r["ipa"])) for r in have if r["ipa"]}
    audio = {r["audio"] for r in have if r["audio"]}
    out = []
    for r in pron_wiktionary.parse(name, entry):
        if (r["ipa"] and (r["lang"], _norm(r["ipa"])) in seen) or (r["audio"] and r["audio"] in audio):
            continue
        if not r["ipa"] and r["audio"] and r["audio"] in audio:
            continue
        seen.add((r["lang"], _norm(r["ipa"])))
        out.append({**r, "entity_kind": "town", "entity_id": eid, "source": "Wiktionary",
                    "source_url": "https://en.wiktionary.org/wiki/" + quote(name.replace(" ", "_")),
                    "licence": pron_db.SOURCES["Wiktionary"]})
    return out


def run(log=print):
    require_locations()
    t0 = time.time()

    def say(msg):
        log(f"[{time.time() - t0:6.0f}s] {msg}")

    conn = connect()
    ents = _entities(conn)
    say(f"{len(ents)} records (buildings, places, people)")
    towns = towns_for([q for k, _, q, _, _ in ents if k != "person"], say)
    town_ents = {}
    for lst in towns.values():
        for tq, label, title in lst:
            town_ents[tq] = ("town", tq, tq, title, label)
    say(f"{len(town_ents)} towns and areas")
    allents = ents + list(town_ents.values())
    leads = wikipedia_leads([t for *_, t, _ in allents], say)
    say(f"{sum(1 for v in leads.values() if v)} article openings")
    wd = wikidata_pronunciations([q for _, _, q, _, _ in allents], say)
    wikt = pron_wiktionary.fetch([name for kind, *_, name in allents if kind == "town"], say)
    rows = []
    for kind, eid, qid, title, name in allents:
        got = _wiki_rows(kind, eid, title, leads.get(title, "")) if title else []
        got += _wd_rows(kind, eid, qid, name, wd.get(qid, []), got)
        if kind == "town":
            got += _wikt_rows(eid, name, wikt.get(name), got)
        rows += got
    links = []
    for kind, eid, qid, _, _ in ents:
        for tq, label, _ in towns.get(qid, []):
            links.append((eid, tq, label))
    pron_db.write(conn, rows, links)
    other, other_places = pron_db.other_names(conn, "building"), pron_db.other_names(conn, "place")
    set_other_names(conn, other)
    places_db.set_other_names(conn, other_places)
    say(f"other-language names searchable for {len(other)} buildings and {len(other_places)} places")
    say(f"wrote {len(rows)} pronunciation rows, {len(links)} record-town links")
    report(conn, log)


def report(conn=None, log=print):
    conn = conn or connect()
    cov = pron_db.coverage(conn)
    if not cov:
        log("no pronunciations table yet: run python -m bidb.pronunciations")
        return
    log(f"records with their own entry: {cov['entities']}")
    log(f"records whose town has one: {cov['records_with_town']}")
    for v in cov["varieties"][:25]:
        log(f"  {v['variety']:<28} {v['rows']:>6} rows, {v['ipa']:>6} IPA, {v['audio']:>5} audio")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--report", action="store_true", help="print coverage only")
    a = ap.parse_args()
    report() if a.report else run()


if __name__ == "__main__":
    main()
