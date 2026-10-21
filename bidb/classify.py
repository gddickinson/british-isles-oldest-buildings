"""Rule-based classification: building category, historical period, heritage grade."""
import re

from .categories import CATEGORY_ORDER, CATEGORY_RULES  # noqa: F401  (re-exported)

# Wikidata classes that describe land holdings or abstract sites rather than structures
NON_BUILDING_CLASSES = {"manor estate", "manorial estate", "estate", "landed estate"}

DEMOLISHED_WORDS = ("demolished", "destroyed", "lost building", "site of", "no longer extant",
                    "no remains", "former building")


def is_non_building(class_labels):
    """True when every class of the item is a land-holding style class."""
    labels = [c.lower() for c in class_labels if c]
    return bool(labels) and all(c in NON_BUILDING_CLASSES for c in labels)


def status_for(class_labels, condition_labels, description):
    """'Demolished / destroyed', 'Ruin' or 'Standing' from type, condition and description.

    Wikidata P576 is not used: for abbeys it records the Dissolution, not demolition.
    """
    text = " | ".join(class_labels + condition_labels + [description or ""]).lower()
    if any(w in text for w in DEMOLISHED_WORDS):
        return "Demolished / destroyed"
    if "ruin" in text:
        return "Ruin"
    return "Standing"


# (label, start year inclusive, end year exclusive)
PERIODS = [
    ("Neolithic", -10000, -2500),
    ("Bronze Age", -2500, -800),
    ("Iron Age", -800, 43),
    ("Roman Britain", 43, 410),
    ("Early Medieval", 410, 1066),
    ("Norman", 1066, 1154),
    ("High Medieval", 1154, 1307),
    ("Late Medieval", 1307, 1485),
    ("Tudor", 1485, 1603),
    ("Stuart", 1603, 1714),
    ("Georgian", 1714, 1837),
    ("Victorian", 1837, 1901),
    ("Modern", 1901, 3000),
]

PERIOD_ORDER = [p[0] for p in PERIODS]


def categorise(class_labels, name=""):
    """Pick the first category whose keywords appear in any class label (then the name)."""
    texts = [t.lower() for t in class_labels if t]
    from_classes = _match(texts)
    if from_classes and from_classes not in GENERIC_CATEGORIES:
        return from_classes
    return _match([name.lower()]) or from_classes or "Other structure"


GENERIC_CATEGORIES = {"Ruin / archaeological site", "Other structure"}


def _match(pool):
    for category, keys in CATEGORY_RULES:
        for k in keys:
            if any(re.search(r"\b" + re.escape(k) + r"(?:s|es)?\b", t) for t in pool):
                return category
    return None


def period_for(year):
    if year is None:
        return "Unknown"
    for label, start, end in PERIODS:
        if start <= year < end:
            return label
    return "Neolithic" if year < -10000 else "Unknown"


# Rome never ruled Ireland or the Isle of Man: their Iron Age runs on to c. AD 400
NOT_ROMAN = {"Republic of Ireland", "Northern Ireland", "Isle of Man"}


def regional_period(period, nation):
    """The period label as used in the record's own nation."""
    return "Iron Age" if period == "Roman Britain" and nation in NOT_ROMAN else period


def heritage_grade(designations):
    """Collapse designation labels into the highest headline grade."""
    joined = " | ".join(d.lower() for d in designations)
    for key, grade in [("world heritage", "World Heritage Site"),
                       ("grade i listed", "Grade I"), ("category a listed", "Category A"),
                       ("grade a listed", "Grade A (NI)"), ("grade ii* listed", "Grade II*"),
                       ("grade b+", "Grade B+ (NI)"), ("category b listed", "Category B"),
                       ("grade ii listed", "Grade II"), ("category c", "Category C"),
                       ("scheduled monument", "Scheduled monument"),
                       ("national monument of ireland", "National Monument (IE)"),
                       ("national inventory of architectural heritage", "NIAH record (IE)"),
                       ("record of protected structures", "Protected structure (IE)"),
                       ("registered building", "Registered building (IoM)"),
                       ("state care", "State care (NI)")]:
        if key in joined:
            return grade
    return "Designated (other)" if designations else "Not recorded"
