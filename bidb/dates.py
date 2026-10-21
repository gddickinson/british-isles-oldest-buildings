"""Convert Wikidata time values into sortable years and human-readable text."""
import re

# Wikidata precision codes
PREC_MILLENNIUM, PREC_CENTURY, PREC_DECADE, PREC_YEAR = 6, 7, 8, 9


def parse_year(time_str):
    """'+1086-00-00T00:00:00Z' / '-3000-01-01T..' -> int year (negative = BC)."""
    m = re.match(r"([+-]?)(\d+)-", time_str)
    if not m:
        return None
    year = int(m.group(2))
    return -year if m.group(1) == "-" else year


def _ordinal(n):
    suffix = "th" if 10 <= n % 100 <= 20 else {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
    return f"{n}{suffix}"


def format_year(year, precision=PREC_YEAR):
    """Human text for a year at a given Wikidata precision."""
    if year is None:
        return ""
    era = " BC" if year < 0 else ""
    a = abs(year)
    if precision <= PREC_MILLENNIUM:
        mill = (a - 1) // 1000 + 1 if a else 1
        return f"{_ordinal(mill)} millennium{era or ' AD'}"
    if precision == PREC_CENTURY and year < 0:
        return f"c. {a} BC"
    if precision == PREC_CENTURY:
        cent = (a - 1) // 100 + 1 if a else 1
        return f"{_ordinal(cent)} century{era}"
    if precision == PREC_DECADE:
        return f"{a // 10 * 10}s{era}"
    if year < 0:
        return f"c. {a} BC" if a > 500 else f"{a} BC"
    return f"{a}" if a >= 1000 else f"AD {a}"


def sort_year(year, precision):
    """For century/millennium precision Wikidata stores e.g. 1100 for the 11th c.; use the start."""
    if year is None:
        return None
    if precision == PREC_CENTURY and year > 0 and year % 100 == 0:
        return year - 99
    return year


def parse_text_year(text):
    """Best-effort year from free text like '3800 BC', 'c. 1080', '7th century'."""
    if not text:
        return None
    t = text.replace(" ", " ").replace("&nbsp;", " ")
    # "17th-century", "9th (baptistery) and 10th centuries": the first ordinal before "centur"
    m = re.search(r"(\d+)(?:st|nd|rd|th)\b[^.;]*?\bmillenni(?:um|a)\s*(BC)?", t, re.I)
    if m:
        k = int(m.group(1))
        return -(k * 1000) if m.group(2) else (k - 1) * 1000 + 1
    m = re.search(r"(\d+)(?:st|nd|rd|th)\b[^.;]*?\bcentur(?:y|ies)\s*(BC)?", t, re.I)
    if m:
        c = int(m.group(1))
        return -(c * 100) if m.group(2) else (c - 1) * 100 + 1
    for word, year in (("neolithic", -3000), ("bronze age", -1500), ("iron age", -400)):
        if word in t.lower() and not re.search(r"\d", t):
            return year
    m = re.search(r"(\d{2,4})\s*(BC|BCE)?", t, re.I)
    if m:
        y = int(m.group(1))
        if m.group(2) or re.search(r"\bBC", t[m.end():m.end() + 20], re.I):
            return -y
        return y
    return None
