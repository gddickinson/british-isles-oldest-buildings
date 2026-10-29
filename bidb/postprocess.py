"""Final build steps: 'oldest of type' annotation, colour groups, cutoff, overrides, diff."""
import json
import re

from . import date_corrections, land, nhle_check, overrides
from .categories import group_for
from .classify import GENERIC_CATEGORIES, period_for, regional_period
from .config import DATA_DIR, DB_PATH
from .oldest_types import TYPE_CATEGORY, type_claim_text
from .records import commons_thumb

DIFF_PATH = DATA_DIR / "build_diff.json"
# Wikidata-found "oldest of type" examples must predate this (later inceptions in the per-type
# top lists are mostly restoration or listing dates, e.g. windmills "built" in 2021)
OLDEST_WD_BEFORE = 1900
OFFSHORE_KM = 60          # remote lighthouses and islands are kept


def annotate_oldest(records, wd_types, research_by_qid):
    """Mark records found by the oldest-of-type queries or the research file."""
    by_id = {r["id"]: r for r in records}
    for qid, label in wd_types.items():
        r = by_id.get(qid)
        if r and r.get("year_start") is not None and r["year_start"] < OLDEST_WD_BEFORE:
            r["oldest_of_type"] = label
            if r["category"] in GENERIC_CATEGORIES or r["category"] == "Other structure":
                r["category"] = TYPE_CATEGORY.get(label, r["category"])
    for qid, entry in research_by_qid.items():
        r = by_id.get(qid)
        if r:
            _apply_research(r, entry)


def _apply_research(r, entry):
    r["oldest_of_type"] = entry.get("type") or r.get("oldest_of_type")
    r["type_claim"] = type_claim_text(entry)
    if entry.get("category"):
        r["category"] = entry["category"]
    claimed = entry.get("year")
    if claimed is not None and r.get("year_start") is not None and int(claimed) < r["year_start"] - 50:
        # Wikidata's date is far later than the researched claim (often a rebuild or reopening)
        r.update(year_start=int(claimed), period=period_for(int(claimed)),
                 date_text=f"{entry.get('claimed_date') or claimed} (Wikidata: {r.get('date_text')})",
                 date_source="Research (claimed date)", date_confidence="Claimed (research)",
                 date_evidence=entry.get("evidence_date"))
    elif r.get("year_start") is None and claimed is not None:
        r.update(year_start=int(entry["year"]), period=period_for(int(entry["year"])),
                 date_text=entry.get("claimed_date") or str(entry["year"]),
                 date_source="Research (claimed date)", date_confidence="Claimed (research)",
                 date_evidence=entry.get("evidence_date"))


def research_only_record(entry, intro):
    """Record for a researched example with no Wikidata item."""
    year = entry.get("year")
    slug = re.sub(r"[^a-z0-9]+", "-", f"{entry['name']} {entry.get('location', '')}".lower())
    image = (intro or {}).get("image")
    return {
        "id": "rs-" + slug.strip("-")[:80], "name": entry["name"], "description": entry.get("type"),
        "category": entry.get("category") or "Other structure", "classes": entry.get("type") or "",
        "is_building": 1, "status": "Standing", "period": period_for(year), "year_start": year,
        "date_text": entry.get("claimed_date") or (str(year) if year is not None else ""),
        "date_source": "Research (claimed date)",
        "date_confidence": "Claimed (research)" if year is not None else "Not recorded",
        "date_evidence": entry.get("evidence_date"), "nation": entry.get("nation"),
        "locality": entry.get("location"), "heritage_grade": "Not recorded", "designations": "",
        "image_thumb": image, "wikipedia_title": entry.get("wikipedia_title"),
        "wikipedia_extract": (intro or {}).get("extract"), "curated": 0,
        "oldest_of_type": entry.get("type"), "type_claim": type_claim_text(entry),
        "curated_notes": (f"See the Wikipedia article on {entry['context_article']}"
                          if entry.get("context_article") else None),
    }


def finalise(records, cutoff, log=print):
    """Groups, cutoff (oldest-of-type examples are exempt), overrides; returns kept records."""
    kept = [r for r in records if r.get("oldest_of_type") or r.get("landmark")
            or r.get("year_start") is None or r["year_start"] < cutoff]
    # overseas territories (Gibraltar, Falklands, Cyprus bases...) share the UK's Wikidata country
    kept = [r for r in kept if r.get("lat") is None or land.near_land(r["lat"], r["lon"], OFFSHORE_KM)]
    for r in kept:
        r["category_group"] = group_for(r.get("category"))
        if r.get("image_file") and not r.get("image_thumb"):
            r["image_thumb"] = commons_thumb(r["image_file"])
    n = date_corrections.apply(kept)
    log(f"{nhle_check.apply(kept)} reviewed NHLE list entries")
    overrides.apply(kept)
    for r in kept:
        r["period"] = regional_period(r.get("period"), r.get("nation"))
    log(f"{n} reviewed date corrections")
    log(f"kept {len(kept)} records ({sum(bool(r.get('oldest_of_type')) for r in kept)} "
        f"oldest-of-type, {sum(bool(r.get('edited')) for r in kept)} with user corrections)")
    return kept


def write_diff(records):
    """Compare with the previous database and save a short 'what changed' summary."""
    import sqlite3
    old = {}
    if DB_PATH.exists():
        try:
            con = sqlite3.connect(DB_PATH)
            old = {i: (n, y) for i, n, y in con.execute("SELECT id, name, year_start FROM buildings")}
            con.close()
        except sqlite3.Error:
            old = {}
    new = {r["id"]: (r["name"], r.get("year_start")) for r in records}
    added = [new[i][0] for i in new.keys() - old.keys()]
    removed = [old[i][0] for i in old.keys() - new.keys()]
    redated = [f"{new[i][0]}: {old[i][1]} → {new[i][1]}" for i in new.keys() & old.keys()
               if old[i][1] != new[i][1]]
    diff = {"added": len(added), "removed": len(removed), "redated": len(redated),
            "examples": {"added": sorted(added)[:40], "removed": sorted(removed)[:40],
                         "redated": sorted(redated)[:40]}}
    DIFF_PATH.write_text(json.dumps(diff, indent=1, ensure_ascii=False))
    return diff
