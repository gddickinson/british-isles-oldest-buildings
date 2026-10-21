"""Fill missing construction dates: register description, Wikipedia article text/infobox,
then building-type estimate.

Each record gets date_confidence:
    'Recorded'                 Wikidata inception or a curated Wikipedia list
    'From register description' HES (Scotland) or Cadw (Wales) listing text (evidence kept)
    'From Wikipedia article'   mined from the article infobox or text (evidence kept)
    'From Wikidata description' e.g. '13th-century tower house in County Clare'
    'Estimate (building type)' accepted date range for the monument type
    'Not recorded'
"""
from . import enrich
from .classify import period_for
from .date_mining import date_from_infobox, date_from_text, is_period_level, rank
from .register_dates import register_dates
from .typology import estimate


def _apply(r, year, text, source, confidence, evidence):
    r.update(year_start=year, date_text=text, date_source=source, date_confidence=confidence,
             date_evidence=evidence, period=period_for(year))


def fill_missing_dates(records, log=print, intro_only=()):
    """intro_only: ids whose date is mined from the Wikipedia intro only (no full-article fetch)."""
    for r in records:
        if r.get("year_start") is not None:
            r["date_confidence"] = "Recorded"
    missing = [r for r in records if r.get("year_start") is None]
    articles = enrich.wikipedia_articles(r["wikipedia_title"] for r in missing
                                         if r.get("wikipedia_title") and r["id"] not in intro_only)
    registered = register_dates(missing, log)
    counts = {"From register description": 0, "From Wikipedia article": 0, "From Wikidata description": 0,
              "Estimate (building type)": 0, "Not recorded": 0}
    for r in missing:
        reg = registered.get(r["id"])
        est = estimate((r.get("classes") or "").split("; "), r.get("name"))
        # the listing's opening clause dates the building itself; a sentence further down a
        # monument description is weaker than the monument-type range
        if reg and (reg[3] == "lead" or not est) and not (est and is_period_level(reg)):
            year, label, evidence, _, register = reg
            _apply(r, year, label, f"{register} register", "From register description", evidence[:400])
            counts["From register description"] += 1
            continue
        art = articles.get(r.get("wikipedia_title") or "", {})
        hit = date_from_infobox(art.get("lead_wikitext"))
        text_hit = date_from_text(art.get("text") or r.get("wikipedia_extract"))
        if text_hit and (hit is None or rank(text_hit) < rank(hit)):
            hit = text_hit
        if hit and est and is_period_level(hit):
            # only a whole-period date in the article: the monument-type range is more specific
            year, text, evidence = est
            _apply(r, year, text, "Typology", "Estimate (building type)",
                   f"{evidence}; the Wikipedia article gives only the period ({hit[1]})")
            counts["Estimate (building type)"] += 1
            continue
        if hit:
            year, label, evidence = hit
            _apply(r, year, label, "Wikipedia article", "From Wikipedia article", evidence[:400])
            counts["From Wikipedia article"] += 1
            continue
        desc_hit = date_from_text(r.get("description") or "")
        if desc_hit:
            year, label, evidence = desc_hit
            _apply(r, year, label, "Wikidata description", "From Wikidata description", evidence)
            counts["From Wikidata description"] += 1
            continue
        if est:
            year, text, evidence = est
            _apply(r, year, text, "Typology", "Estimate (building type)", evidence)
            counts["Estimate (building type)"] += 1
            continue
        r["date_confidence"] = "Not recorded"
        counts["Not recorded"] += 1
    log(f"date fill for {len(missing)} undated records: {counts}")
    return records
