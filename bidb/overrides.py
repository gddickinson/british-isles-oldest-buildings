"""Manual corrections made in the GUI, kept in data/overrides.json so they survive rebuilds."""
import json
import time

from .config import DATA_DIR

OVERRIDES_PATH = DATA_DIR / "overrides.json"
EDITABLE = {"name": str, "date_text": str, "year_start": int, "category": str, "status": str,
            "heritage_grade": str, "description": str, "street_address": str, "notes": str}


def load():
    try:
        return json.loads(OVERRIDES_PATH.read_text())
    except (FileNotFoundError, ValueError):
        return {}


def save_one(bid, fields, note=""):
    """Validate and store corrections for one building; returns the cleaned fields."""
    clean = {}
    for k, v in fields.items():
        if k not in EDITABLE:
            continue
        if v in ("", None):
            clean[k] = None
        else:
            clean[k] = EDITABLE[k](v)
    data = load()
    entry = data.get(bid, {})
    entry.update(clean)
    entry["_updated"] = time.strftime("%Y-%m-%d %H:%M")
    if note:
        entry["_note"] = note
    data[bid] = entry
    OVERRIDES_PATH.write_text(json.dumps(data, indent=1, ensure_ascii=False))
    return clean


def remove(bid):
    data = load()
    data.pop(bid, None)
    OVERRIDES_PATH.write_text(json.dumps(data, indent=1, ensure_ascii=False))


def apply(records):
    """Apply stored corrections to freshly built records (in place)."""
    from .classify import period_for
    from .categories import group_for
    data = load()
    by_id = {r["id"]: r for r in records}
    for bid, fields in data.items():
        r = by_id.get(bid)
        if not r:
            continue
        for k, v in fields.items():
            if not k.startswith("_") and v is not None and k in EDITABLE and k != "notes":
                r[k] = v
        if fields.get("notes"):
            r["user_notes"] = fields["notes"]
        if "year_start" in fields:
            r["period"] = period_for(r["year_start"])
            r["date_confidence"] = "Corrected by user"
        r["category_group"] = group_for(r.get("category"))
        r["edited"] = 1
    return records
