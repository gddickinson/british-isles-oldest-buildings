"""Add researched examples (data/curated/oldest_by_type.json) that are missing from an existing database,
without a rebuild: python -m bidb.research_add [--dry-run]

A rebuild replaces the buildings table and with it what the photo, plan and outline jobs added, so new
research entries with a Wikidata item (key "wikidata", or a linked Wikipedia article) are built here with
the build's own steps (record, research note, reviewed date correction, user corrections, references) and
inserted. Run bidb.dendro afterwards to match tree-ring dates to the new records.
"""
import sys

from . import date_corrections, enrich, overrides, references, wikidata as wd
from .build import LABEL_PROPS
from .categories import group_for
from .classify import regional_period
from .db import COLUMN_NAMES, FTS_FIELDS, connect
from .oldest_types import research_entries, type_claim_text
from .postprocess import annotate_oldest
from .records import build_record, commons_thumb
from .wikipedia_list import titles_to_qids


def missing(conn):
    """{qid: research entry} for researched examples whose Wikidata item is not in the catalogue."""
    entries = research_entries()
    by_title = titles_to_qids({e["wikipedia_title"] for e in entries
                               if e.get("wikipedia_title") and not e.get("wikidata")})
    out = {}
    for e in entries:
        q = e.get("wikidata") or by_title.get(e.get("wikipedia_title") or "")
        if q and not conn.execute("SELECT 1 FROM buildings WHERE id = ?", (q,)).fetchone():
            out.setdefault(q, e)
    return out


def mark_existing(conn, log=print):
    """Oldest-of-type notes for catalogue records named by a research entry's "wikidata" key that have none yet
    (refresh_claims only rewrites notes already there)."""
    n = 0
    for e in research_entries():
        if e.get("wikidata"):
            n += conn.execute("UPDATE buildings SET oldest_of_type = ?, type_claim = ?, category = ? "
                              "WHERE id = ? AND oldest_of_type IS NULL",
                              (e["type"], type_claim_text(e), e["category"], e["wikidata"])).rowcount
    conn.commit()
    log(f"oldest-of-type notes added to {n} existing records")


def records_for(research, log=print):
    """Catalogue records for {qid: research entry}, as the build makes them."""
    entities = {q: e for q, e in wd.get_entities(set(research)).items() if "missing" not in e and "claims" in e}
    classes = {c for e in entities.values() for c in wd.item_ids(e, "P31")}
    struct_cls, building_cls = wd.structure_classes(classes)
    for q in [q for q, e in entities.items() if not set(wd.item_ids(e, "P31")) & struct_cls]:
        label = wd.label(entities.pop(q))
        if research[q].get("wikidata"):               # others link a town article on purpose (text-only records)
            log(f"  {q} {label}: not a structure on Wikidata, left out")
    ref = {r for e in entities.values() for p in LABEL_PROPS for r in wd.item_ids(e, p)}
    label_map = {q: wd.label(e) for q, e in wd.get_entities(ref, label_only=True).items()}
    nation_map = wd.nations_for(entities)
    postcodes = {q: enrich.address_from_postcode(pc) for q, pc in
                 enrich.reverse_geocode({q: wd.coords(e) for q, e in entities.items()}).items()}
    titles = {q: wd.enwiki_title(e) or research[q].get("wikipedia_title") for q, e in entities.items()}
    intros = enrich.wikipedia_intros([t for t in titles.values() if t])
    records = [build_record(q, e, label_map, building_cls, nation_map, postcodes.get(q),
                            intros.get(titles[q]), None) for q, e in entities.items()]
    annotate_oldest(records, {}, {r["id"]: research[r["id"]] for r in records})
    for r in records:                                  # as postprocess.finalise
        r["category_group"] = group_for(r.get("category"))
        if r.get("image_file") and not r.get("image_thumb"):
            r["image_thumb"] = commons_thumb(r["image_file"])
    date_corrections.apply(records)
    overrides.apply(records)
    for r in records:
        r["period"] = regional_period(r.get("period"), r.get("nation"))
    references.annotate(records, log)
    return records


def insert(conn, records):
    conn.executemany(f"INSERT OR REPLACE INTO buildings ({', '.join(COLUMN_NAMES)}) "
                     f"VALUES ({', '.join('?' for _ in COLUMN_NAMES)})",
                     [[r.get(c) for c in COLUMN_NAMES] for r in records])
    conn.executemany("DELETE FROM buildings_fts WHERE id = ?", [(r["id"],) for r in records])
    conn.executemany(f"INSERT INTO buildings_fts (id, {', '.join(FTS_FIELDS)}) "
                     f"VALUES (?, {', '.join('?' for _ in FTS_FIELDS)})",
                     [[r["id"]] + [r.get(f) or "" for f in FTS_FIELDS] for r in records])
    conn.commit()


def run(dry_run=False, log=print):
    conn = connect()
    conn.execute("PRAGMA busy_timeout = 120000")
    if not dry_run:
        mark_existing(conn, log)
    research = missing(conn)
    log(f"{len(research)} researched examples not in the catalogue")
    if not research:
        return []
    records = records_for(research, log)
    for r in records:
        log(f"  {r['id']} {r['name']} ({r.get('locality')}): {r.get('date_text')} [{r.get('date_source')}]")
    if not dry_run:
        insert(conn, records)
        log(f"added {len(records)} records")
    return records


if __name__ == "__main__":
    run(dry_run="--dry-run" in sys.argv[1:])
