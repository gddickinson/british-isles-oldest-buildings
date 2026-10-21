"""Typological date estimates: the accepted construction range for a monument type.

Used only when no recorded or text-derived date exists; such dates are always labelled
'Estimate (building type)' in the database and GUI.
"""
import re

# (pattern matched against class labels + name, start year, end year, label)
TYPE_RANGES = [
    (r"portal tomb|dolmen|quoit", -3800, -3200, "portal tombs / dolmens"),
    (r"court tomb|court cairn", -3700, -3500, "court tombs"),
    (r"passage (?:tomb|grave)", -3300, -2900, "passage tombs"),
    (r"wedge tomb", -2500, -2000, "wedge tombs"),
    (r"stone circle|stone row", -2500, -1500, "stone circles"),
    (r"standing stone|menhir|monolith", -2500, -1000, "standing stones"),
    (r"hill ?fort", -1000, 400, "hillforts"),
    (r"promontory fort", -500, 1000, "promontory forts"),
    (r"crannog", 500, 1000, "crannogs (early medieval)"),
    (r"ringfort|ring fort|\brath\b|cashel", 600, 1000, "ringforts and cashels"),
    (r"ogham", 400, 700, "ogham stones"),
    (r"souterrain", 500, 1200, "souterrains"),
    (r"round tower", 900, 1200, "Irish round towers"),
    (r"high cross|celtic cross", 750, 1150, "Irish high crosses"),
    (r"cross[- ]slab|cross slab|pillar stone", 600, 900, "early cross-slabs"),
    (r"motte", 1070, 1250, "Norman and Anglo-Norman mottes"),
    (r"\bhenge", -3000, -2000, "henges"),
    (r"long barrow", -3800, -3300, "long barrows"),
    (r"(?:round|bowl|bell|disc|pond|ring|saucer) barrow|tumulus", -2200, -1500, "round barrows"),
    (r"chambered cairn", -3500, -2500, "chambered cairns"),
    (r"\bbroch", -400, 100, "brochs"),
    (r"\bdun\b", -500, 1000, "duns"),
    (r"cup[- ]and[- ]ring|rock art", -3500, -2000, "cup-and-ring rock art"),
    (r"pictish", 500, 900, "Pictish symbol stones"),
    (r"roman villa", 43, 410, "Roman villas"),
    (r"tower house", 1400, 1650, "tower houses"),
    (r"friary", 1224, 1540, "Irish friaries"),
]


def estimate(class_labels, name):
    """-> (start year, display text, evidence) or None."""
    text = " ".join([*(class_labels or []), name or ""]).lower()
    for pattern, start, end, label in TYPE_RANGES:
        if re.search(pattern, text):
            span = f"{_fmt(start)}–{_fmt(end)}"
            return start, f"c. {span} (typical for {label})", f"Typical construction range for {label}"
    return None


def _fmt(y):
    return f"{-y} BC" if y < 0 else f"AD {y}" if y < 1000 else str(y)
