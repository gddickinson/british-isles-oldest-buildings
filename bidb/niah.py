"""Buildings from Ireland's National Inventory of Architectural Heritage (NIAH) dated before 1500
that are not already in the catalogue (matched by NIAH registration number)."""
import re

from .categories import group_for  # noqa: F401  (groups are applied in postprocess.finalise)
from .classify import categorise, period_for
from .registers import ATTRIBUTION, niah_early


def _title(s):
    s = (s or "").strip()
    letters = [c for c in s if c.isalpha()]
    mostly_upper = letters and sum(c.isupper() for c in letters) > 0.7 * len(letters)
    return s.title() if mostly_upper else s


def niah_records(records, log=print):
    have = {str(r.get("ie_niah_id")) for r in records if r.get("ie_niah_id")}
    try:
        rows = niah_early()
    except Exception as exc:                     # register unavailable: carry on without it
        log(f"NIAH unavailable: {exc}")
        return []
    out = []
    for a in rows:
        reg = str(a.get("REG_NO"))
        if reg in have:
            continue
        name = _title(a.get("NAME")) or _title(a.get("ORIGINAL_TYPE")) or f"NIAH {reg}"
        year, end = a.get("DATEFROM"), a.get("DATETO")
        if year and end and year < 1000 and end > 1500:
            continue            # a digit lost from DATEFROM ("188–1840" for a house built c. 1820)
        desc = re.sub(r"\s+", " ", a.get("DESCRIPTION") or "").strip()
        appraisal = re.sub(r"\s+", " ", a.get("APPRAISAL") or "").strip()
        place = ", ".join(x for x in (_title(a.get("TOWN")) or _title(a.get("TOWNLAND")),
                                      f"County {_title(a.get('COUNTY'))}" if a.get("COUNTY") else None) if x)
        out.append({
            "id": f"niah-{reg}", "name": name, "description": _title(a.get("ORIGINAL_TYPE")),
            "category": categorise([a.get("ORIGINAL_TYPE") or ""], name),
            "classes": _title(a.get("ORIGINAL_TYPE")) or "", "is_building": 1, "status": "Standing",
            "period": period_for(year), "year_start": year,
            "date_text": (f"c. {year} (NIAH date range {year}–{end})" if end and end - year > 100
                          else f"{year}–{end}" if end and end != year else str(year)),
            "date_source": "NIAH", "date_confidence": "Recorded",
            "nation": "Republic of Ireland", "county": f"County {_title(a.get('COUNTY'))}",
            "locality": place, "lat": a.get("LATITUDE"), "lon": a.get("LONGITUDE"),
            "heritage_grade": f"NIAH rating: {a.get('RATING')}" if a.get("RATING") else "NIAH record (IE)",
            "designations": "National Inventory of Architectural Heritage", "ie_niah_id": reg,
            "register_notes": " ".join(x for x in (desc, appraisal) if x)[:2000] or None,
            "register_url": a.get("WEBSITE_LINK"), "register_source": ATTRIBUTION["NIAH"],
            "curated": 0,
        })
    log(f"NIAH buildings before 1500: {len(rows)}, {len(out)} new")
    return out
