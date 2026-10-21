"""Assemble one flat database record per building from the fetched sources."""
import re
from urllib.parse import quote

from . import wikidata as wd
from .classify import GENERIC_CATEGORIES, categorise, heritage_grade, period_for, status_for
from .config import COMMONS_FILE_PAGE, COMMONS_FILEPATH, COUNTRIES
from .dates import format_year, parse_text_year, parse_year, sort_year

def commons_thumb(filename, width=640):
    name = filename.replace(" ", "_")
    return f"{COMMONS_FILEPATH}{quote(name)}?width={width}"


def _labels(qids, label_map):
    return [label_map.get(q, "") for q in qids if label_map.get(q)]


def _earliest_inception(entity):
    best = None
    for t, prec in wd.times(entity, "P571"):
        y = parse_year(t)
        if y is None:
            continue
        key = sort_year(y, prec)
        if best is None or key < best[0]:
            best = (key, y, prec)
    return best


def _curated_date(entry):
    year = parse_text_year(entry.get("date_text"))
    text = entry.get("date_text") or ""
    if year is None:
        year = parse_text_year(entry.get("period_heading"))
        text = text or entry.get("period_heading", "")
    return year, text


def _nation(qid, entity, nation_map, postcode, curated):
    """Non-UK jurisdiction from P17 first, then the UK constituent country."""
    countries = [COUNTRIES[c] for c in wd.item_ids(entity, "P17") if c in COUNTRIES]
    non_uk = [c for c in countries if c != "United Kingdom"]
    if non_uk and nation_map.get(qid) != "Northern Ireland":
        return non_uk[0]
    return (nation_map.get(qid) or (postcode or {}).get("nation")
            or _nation_from_text(curated))


def build_record(qid, entity, label_map, building_classes, nation_map, postcode, intro, curated,
                 county=None):
    """Combine Wikidata entity + enrichment into a record dict for db.write_all."""
    class_ids = wd.item_ids(entity, "P31")
    class_labels = _labels(class_ids, label_map)
    name = wd.label(entity) or (curated or {}).get("name") or qid
    desc = entity.get("descriptions", {}).get("en", {}).get("value", "")

    inc = _earliest_inception(entity)
    if inc:
        year, date_text, date_source = inc[0], format_year(inc[1], inc[2]), "Wikidata inception"
    else:
        year, date_text, date_source = None, "Not recorded", ""
    if curated:
        c_year, c_text = _curated_date(curated)
        if year is None and c_year is not None:
            date_text = ""
            year, date_text, date_source = c_year, c_text, "Wikipedia list"
        elif c_year is not None and year is not None and c_year < year:
            date_text = f"{c_text} (Wikidata: {date_text})"
            year, date_source = c_year, "Wikipedia list (earlier than Wikidata)"
        elif c_text and c_year != year and c_text != date_text:
            date_text = f"{date_text} (Wikipedia list: {c_text})" if date_text else c_text

    designations = _labels(wd.item_ids(entity, "P1435"), label_map)
    lat, lon = wd.coords(entity)
    pc = postcode or {}

    status = status_for(class_labels, _labels(wd.item_ids(entity, "P5816"), label_map), desc)

    image_file = (wd.first_string(entity, "P18") or (curated or {}).get("image"))
    image_thumb = commons_thumb(image_file) if image_file else (intro or {}).get("image")
    title = wd.enwiki_title(entity) or (curated or {}).get("title")

    category = categorise(class_labels, name)
    if category in GENERIC_CATEGORIES and year is not None and year < 43:
        category = "Prehistoric monument"

    return {
        "id": qid,
        "name": name,
        "description": desc,
        "category": category,
        "classes": "; ".join(class_labels),
        "is_building": int(bool(set(class_ids) & building_classes)),
        "status": status,
        "period": period_for(year),
        "year_start": year,
        "date_text": date_text,
        "date_source": date_source,
        "nation": _nation(qid, entity, nation_map, postcode, curated),
        "county": (f"County {county}" if county and not county.startswith("County") else county)
                  or pc.get("county") or pc.get("district")
                  or (_labels(wd.item_ids(entity, "P131"), label_map) or [None])[0],
        "district": pc.get("district"),
        "locality": (pc.get("locality") or (curated or {}).get("location")
                     or ", ".join(_labels(wd.item_ids(entity, "P131"), label_map))),
        "located_in": ", ".join(_labels(wd.item_ids(entity, "P131"), label_map)),
        "street_address": wd.first_string(entity, "P6375"),
        "postcode": wd.first_string(entity, "P281") or pc.get("postcode"),
        "lat": lat, "lon": lon,
        "heritage_grade": heritage_grade(designations),
        "designations": "; ".join(designations),
        "nhle_id": wd.first_string(entity, "P1216"),
        "hes_id": wd.first_string(entity, "P709"),
        "cadw_id": wd.first_string(entity, "P1459"),
        "ie_smr_id": wd.first_string(entity, "P4057"),
        "ie_niah_id": wd.first_string(entity, "P4088"),
        "ie_nm_id": wd.first_string(entity, "P4059"),
        "style": ", ".join(_labels(wd.item_ids(entity, "P149"), label_map)),
        "materials": ", ".join(_labels(wd.item_ids(entity, "P186"), label_map)),
        "architect": ", ".join(_labels(wd.item_ids(entity, "P84"), label_map)),
        "religion": ", ".join(_labels(wd.item_ids(entity, "P140"), label_map)),
        "dedication": ", ".join(_labels(wd.item_ids(entity, "P825"), label_map)),
        "condition": ", ".join(_labels(wd.item_ids(entity, "P5816"), label_map)),
        "height_m": wd.quantity(entity, "P2048"),
        "website": wd.first_string(entity, "P856"),
        "image_file": image_file,
        "image_thumb": image_thumb,
        "image_page": (COMMONS_FILE_PAGE + quote(image_file.replace(" ", "_"))) if image_file else None,
        "wikipedia_title": title,
        "wikipedia_extract": (intro or {}).get("extract"),
        "wikidata_id": qid if qid.startswith("Q") else None,
        "curated": int(bool(curated)),
        "curated_notes": _curated_note(curated),
    }


def _slug(text):
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")[:80]


def _curated_note(entry):
    if not entry:
        return None
    page = entry.get("source_page", "").replace("_", " ")
    note = entry.get("notes") or ""
    return f"{note} [{page}]".strip() if page else note


def _nation_from_text(curated):
    if (curated or {}).get("source_page", "").endswith("Scotland"):
        return "Scotland"
    loc = ((curated or {}).get("location") or "").lower()
    for n in ("Northern Ireland", "Scotland", "Wales", "England"):
        if n.lower() in loc:
            return n
    return None


def record_from_curated_only(entry, intro):
    """Record for a list entry that has no Wikidata item (red link)."""
    year, text = _curated_date(entry)
    image = entry.get("image")
    return {
        "id": "wp-" + _slug(entry["name"] + " " + (entry["location"] or "")),
        "name": entry["name"] or entry["title"],
        "description": entry.get("use") or "",
        "category": categorise([entry.get("use") or ""], entry["name"] or entry["title"]),
        "classes": entry.get("use") or "", "is_building": 1, "status": "Standing", "period": period_for(year),
        "year_start": year, "date_text": text, "date_source": "Wikipedia list",
        "nation": _nation_from_text(entry), "locality": entry.get("location"),
        "heritage_grade": heritage_grade([]), "designations": "",
        "image_file": image, "image_thumb": commons_thumb(image) if image else None,
        "image_page": (COMMONS_FILE_PAGE + quote(image.replace(" ", "_"))) if image else None,
        "wikipedia_title": None, "wikipedia_extract": (intro or {}).get("extract"),
        "curated": 1, "curated_notes": _curated_note(entry),
    }
