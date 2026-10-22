"""Build the database: python -m bidb.build [--cutoff 1500] [--no-places] [--no-pron] [--no-stories]
    [--refresh-days N] [--refresh wikidata,wikipedia,…]  (fetch cached downloads again: bidb.refresh)

Stages: curated Wikipedia lists + researched oldest-of-type examples -> Wikidata candidates
(inception < cutoff, Irish National Monuments, oldest of each type) -> class filter -> entity
details -> labels -> nations/counties -> postcodes.io -> Wikipedia intros -> records -> date
fill -> oldest-of-type annotation -> overrides -> diff -> SQLite.
"""
import argparse
import json
import time

from . import enrich, landmarks, references, oldest_types, place_fetch, postprocess, wikidata as wd
from .place_kinds import KINDS
from .config import CURATED_LIST_PAGES, CUTOFF_YEAR, DATA_DIR, db_path, require_locations
from .db import write_all
from .classify import categorise, is_non_building
from .niah import niah_records
from .date_fill import fill_missing_dates
from .records import build_record, record_from_curated_only
from .wikipedia_list import fetch_curated_list, titles_to_qids

LABEL_PROPS = ["P31", "P1435", "P131", "P149", "P186", "P84", "P140", "P825", "P5816"]


def log(msg, t0=[time.time()]):
    from . import progress
    print(f"[{time.time() - t0[0]:6.0f}s] {msg}", flush=True)
    progress.note(msg)


def early_monuments():
    """Prehistoric and early monuments with a photo or Wikipedia article -> {qid: type label}."""
    kind = next(k for k in KINDS if k["key"] == "archaeology")
    base = place_fetch.base_items(kind, log)
    det = place_fetch.details(base)
    out = {q: base[q]["type"] for q in base if det.get(q, {}).get("image") or det.get(q, {}).get("title")}
    log(f"early monuments with a photo or article: {len(out)} of {len(base)}")
    return out


def run(cutoff):
    curated = [e for page in CURATED_LIST_PAGES for e in fetch_curated_list(page)]
    title_qid = titles_to_qids({e["title"] for e in curated if e["linked"]})
    curated_by_qid = {}
    for e in curated:
        q = title_qid.get(e["title"])
        if q:
            curated_by_qid.setdefault(q, e)
    curated_unlinked = [e for e in curated if e["title"] not in title_qid]
    log(f"curated list: {len(curated)} rows, {len(curated_by_qid)} linked to Wikidata")
    research = oldest_types.research_entries()
    r_qids = titles_to_qids({e["wikipedia_title"] for e in research if e.get("wikipedia_title")})
    research_by_qid, research_unlinked = {}, []
    for e in research:
        q = r_qids.get(e.get("wikipedia_title") or "")
        if q and q in research_by_qid and research_by_qid[q]["name"] != e["name"]:
            research_unlinked.append(e)               # another building described in the same article (Ewelme)
        elif q:
            research_by_qid.setdefault(q, e)
        else:
            research_unlinked.append(e)
    wd_types = oldest_types.wikidata_oldest(log=log)
    log(f"oldest-of-type: {len(wd_types)} from Wikidata, {len(research)} researched "
        f"({len(research_by_qid)} linked)")

    candidates = wd.find_candidates(cutoff)
    designated = wd.find_designated()
    for q, cls in designated.items():
        candidates.setdefault(q, set()).update(cls)
    marks = landmarks.find_landmarks(log)
    for q, (cls, _) in marks.items():
        candidates.setdefault(q, set()).update(cls)
    arch = early_monuments()
    all_classes = set().union(*candidates.values())
    struct_cls, building_cls = wd.structure_classes(all_classes)
    # designated national monuments are kept whatever their class (ringforts, crosses, tombs)
    keep = ({q for q, cls in candidates.items() if cls & struct_cls}
            | set(curated_by_qid) | set(designated) | set(wd_types) | set(research_by_qid)
            | set(arch))
    log(f"candidates: {len(candidates)} items, {len(keep)} are structures or curated")

    entities = wd.get_entities(keep)
    # Drop curated items that turned out to be outside the British Isles (none expected) and redirects
    entities = {q: e for q, e in entities.items() if "missing" not in e and "claims" in e}
    # curated items not in the inception query still need building-class membership
    extra_cls = {c for q in set(curated_by_qid) | set(wd_types) | set(research_by_qid) | set(arch)
                 if q in entities for c in wd.item_ids(entities[q], "P31")}
    extra_cls -= all_classes
    if extra_cls:
        s2, b2 = wd.structure_classes(extra_cls)
        building_cls |= b2
        struct_cls |= s2
    # research entries sometimes link a town article (no own article): keep them as text-only
    for q in list(research_by_qid):
        e = entities.get(q)
        if e is None or not set(wd.item_ids(e, "P31")) & struct_cls:
            entry = research_by_qid.pop(q)
            research_unlinked.append({**entry, "wikipedia_title": None, "qid": q,
                                      "context_article": entry.get("wikipedia_title")})
            if q not in candidates and q not in curated_by_qid and q not in wd_types:
                entities.pop(q, None)
    log(f"entities fetched: {len(entities)}")

    ref = {r for e in entities.values() for p in LABEL_PROPS for r in wd.item_ids(e, p)}
    label_map = {q: wd.label(e) for q, e in wd.get_entities(ref, label_only=True).items()}
    log(f"labels: {len(label_map)}")

    nation_map = wd.nations_for(entities)
    log(f"nations resolved: {len(nation_map)}")
    irish = [q for q, e in entities.items() if "Q27" in wd.item_ids(e, "P17")
             or nation_map.get(q) == "Northern Ireland"]
    counties = wd.irish_counties_for(irish)
    log(f"Irish counties resolved: {len(counties)} of {len(irish)}")

    points = {q: wd.coords(e) for q, e in entities.items()}
    postcodes = {q: enrich.address_from_postcode(pc)
                 for q, pc in enrich.reverse_geocode(points).items()}
    log(f"addresses (postcodes.io): {len(postcodes)}")

    titles = {q: wd.enwiki_title(e) or (curated_by_qid.get(q) or {}).get("title")
              for q, e in entities.items()}
    intros = enrich.wikipedia_intros(list(titles.values()) +
                                     [e["title"] for e in curated_unlinked] +
                                     [e.get("wikipedia_title") for e in research_unlinked])
    log(f"wikipedia intros: {len(intros)}")

    records = []
    for q, e in entities.items():
        records.append(build_record(q, e, label_map, building_cls, nation_map,
                                    postcodes.get(q), intros.get(titles[q]),
                                    curated_by_qid.get(q), counties.get(q)))
    seen = set()
    for e in curated_unlinked:
        key = (e["name"].lower(), e["location"].lower())
        if key not in seen:
            seen.add(key)
            records.append(record_from_curated_only(e, intros.get(e["title"])))
    records = [r for r in records if r["curated"] or not is_non_building(r["classes"].split("; "))]
    for r in records:
        if r["id"] in marks:
            r["landmark"] = marks[r["id"]][1]
        if r["id"] in arch and r["category"] in ("Other structure", "Ruin / archaeological site"):
            r["category"] = categorise([arch[r["id"]]], r["name"])
    records = [r for r in records if not landmarks.not_a_building(r)]
    unnamed = {r["id"]: r for r in records if r["name"] == r["id"]}
    for q, name in wd.labels_any_language(unnamed).items():
        unnamed[q]["name"] = name
    records += niah_records(records, log)
    # full articles for every undated record (~1,400 requests); landmarks used to get the intro only
    fill_missing_dates(records, log)
    postprocess.annotate_oldest(records, wd_types, research_by_qid)
    have = {r["id"] for r in records}
    # an item outside the structure classes may still be in the catalogue (e.g. from a curated list)
    postprocess.annotate_oldest(records, {}, {e["qid"]: e for e in research_unlinked if e.get("qid") in have})
    for e in research_unlinked:
        if e.get("qid") in have:
            continue
        rec = postprocess.research_only_record(e, intros.get(e.get("wikipedia_title") or ""))
        if rec["id"] not in have:
            have.add(rec["id"])
            records.append(rec)
    records = postprocess.finalise(records, cutoff, log)
    references.annotate(records, log)
    diff = postprocess.write_diff(records)
    log(f"changes vs previous build: {diff['added']} added, {diff['removed']} removed, "
        f"{diff['redated']} re-dated")
    write_all(records)
    (DATA_DIR / "build_info.json").write_text(json.dumps({
        "built": time.strftime("%Y-%m-%d %H:%M"), "cutoff_year": cutoff,
        "records": len(records), "curated": sum(r["curated"] for r in records),
        "sources": ["Wikidata", "Wikipedia (en)", "Wikimedia Commons", "postcodes.io"],
        "nations": sorted({r["nation"] or "Unknown" for r in records}),
    }, indent=2))
    log(f"wrote {len(records)} records to {db_path()}")


def stages(cutoff=CUTOFF_YEAR, places=True, pron=True, stories=True):
    """[(stage name, function)] for a full build (also run from the GUI by app/jobs.py)."""
    from . import (bridges, burials, dendro, depictions, digs, domesday, domesday_entries, era_places, hoards, institutions,
                   lore_places, mapping_museums, maritime, military, museums, nation_geo, oldest_checks, oldest_lists, on_this_day,
                   places_build, pronunciations, sports, timeline, tours, trade_works, underground, wrecks, visiting)
    from . import stories as stories_mod
    out = [("Buildings", lambda: run(cutoff))]
    if places:
        out += [("Places and people", places_build.run), ("Legends and literature", lore_places.run),
                ("Maritime heritage", maritime.run), ("Shipwrecks", wrecks.run), ("Industrial and Victorian", era_places.run),
                ("Underground", underground.run), ("Military heritage", military.run),
                ("Museums and collections", museums.run), ("Mapping Museums", mapping_museums.run),
                ("Hoards", hoards.run), ("Bridges", bridges.run), ("Excavations", digs.run),
                ("Graves and burial grounds", burials.run),
                ("Markets, works and infrastructure", trade_works.run), ("Sport", sports.run), ("Public institutions", institutions.run), ("Oldest in nature and graves", oldest_lists.run), ("Earliest dated places checked", oldest_checks.run),
                ("Nations for places", nation_geo.run)]
        if pron:
            out += [("Pronunciations", pronunciations.run), ("Domesday Book", domesday.run),
                    ("Domesday entries", domesday_entries.run)]
        out.append(("Tree-ring dates", dendro.run))
        out.append(("Paintings and prints", depictions.run))
        if stories:
            out += [("Stories", stories_mod.run), ("Timelines", timeline.run), ("Tours", tours.run),
                    ("On this day", on_this_day.run), ("Visiting information", visiting.run)]
    return out


def main():
    from . import progress, refresh
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--cutoff", type=int, default=CUTOFF_YEAR,
                    help="include buildings begun before this year")
    ap.add_argument("--no-places", action="store_true",
                    help="skip the places/people stage and everything after it (python -m bidb.places_build)")
    ap.add_argument("--no-pron", action="store_true",
                    help="skip the pronunciations stage (python -m bidb.pronunciations)")
    ap.add_argument("--no-stories", action="store_true",
                    help="skip stories, timelines, tours, on-this-day and visiting")
    ap.add_argument("--refresh-days", type=float, metavar="N",
                    help="download again anything cached more than N days ago")
    ap.add_argument("--refresh", metavar="SOURCES", default="",
                    help="download again from these sources only: " + ", ".join(refresh.SOURCES))
    args = ap.parse_args()
    require_locations()
    refresh.set_rule(args.refresh_days, [s for s in args.refresh.split(",") if s])
    if refresh.active():
        log(f"refresh: {refresh.describe()}")
    progress.run_stages("build", stages(args.cutoff, not args.no_places, not args.no_pron, not args.no_stories),
                        options={"cutoff": args.cutoff, "refresh": refresh.describe()})


if __name__ == "__main__":
    main()
