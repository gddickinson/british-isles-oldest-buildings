"""Assemble flat place records (for the `places` table) from fetched Wikidata pieces."""
import json
from urllib.parse import quote

from .classify import period_for
from .config import COMMONS_FILE_PAGE, COUNTRIES
from .place_kinds import KIND_GROUP, KIND_LABEL
from .records import commons_thumb

PLACE_COLUMNS = [
    ("id", "TEXT PRIMARY KEY"), ("kind", "TEXT"), ("kind_label", "TEXT"), ("kind_group", "TEXT"),
    ("type", "TEXT"), ("name", "TEXT"), ("description", "TEXT"),
    ("year_start", "INTEGER"), ("date_text", "TEXT"), ("period", "TEXT"),
    ("lat", "REAL"), ("lon", "REAL"), ("nation", "TEXT"), ("county", "TEXT"), ("locality", "TEXT"),
    ("designation", "TEXT"), ("image_thumb", "TEXT"), ("image_page", "TEXT"),
    ("wikipedia_title", "TEXT"), ("wikipedia_extract", "TEXT"), ("wikidata_id", "TEXT"),
    ("url", "TEXT"), ("source", "TEXT"), ("building_id", "TEXT"), ("extra", "TEXT"),
    ("image_note", "TEXT"), ("refs", "TEXT"),
]
PLACE_COLUMN_NAMES = [c for c, _ in PLACE_COLUMNS]


def blank(pid, kind, name, **fields):
    rec = dict.fromkeys(PLACE_COLUMN_NAMES)
    rec.update(id=pid, kind=kind, kind_label=KIND_LABEL.get(kind, kind),
               kind_group=KIND_GROUP.get(kind, "Archaeological sites"), name=name)
    rec.update(fields)
    if rec.get("year_start") is not None and not rec.get("period"):
        rec["period"] = period_for(rec["year_start"])
    rec["period"] = rec.get("period") or "Unknown"
    return rec


def from_wikidata(qid, kind, base, det, date, extra, nation, intro):
    """One place from the base row, details, date, extras and enrichment."""
    det = det or {}
    image = det.get("image")
    year, text = date or (None, None)
    extra = extra or {}
    loc = extra.pop("location", None)
    return blank(
        qid, kind, det.get("name") or qid,
        type=base.get("type") or (det.get("classes") or [None])[0],
        description=det.get("description"),
        year_start=year, date_text=text or "",
        lat=base["lat"], lon=base["lon"], nation=nation,
        locality=", ".join(det.get("admin") or loc or []) or None,
        designation="; ".join(det.get("designations") or []) or None,
        image_thumb=commons_thumb(image, 400) if image else (intro or {}).get("image"),
        image_page=(COMMONS_FILE_PAGE + quote(image.replace(" ", "_"))) if image else None,
        wikipedia_title=det.get("title"), wikipedia_extract=(intro or {}).get("extract"),
        wikidata_id=qid, source="Wikidata",
        extra=json.dumps(extra, ensure_ascii=False) if extra else None,
    )


def nation_from_country(country_qid):
    name = COUNTRIES.get(country_qid)
    return None if name in (None, "United Kingdom") else name
