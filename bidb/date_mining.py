"""Find construction dates in free text (Wikipedia articles, infoboxes, descriptions).

Every hit keeps the sentence it came from, so the GUI can show the evidence.
"""
import re

ORDINAL_WORDS = {"first": 1, "second": 2, "third": 3, "fourth": 4, "fifth": 5, "sixth": 6,
                 "seventh": 7, "eighth": 8, "ninth": 9, "tenth": 10, "eleventh": 11,
                 "twelfth": 12, "thirteenth": 13, "fourteenth": 14, "fifteenth": 15,
                 "sixteenth": 16, "seventeenth": 17, "eighteenth": 18, "nineteenth": 19}
_ORD = r"(\d{1,2})(?:st|nd|rd|th)|(" + "|".join(ORDINAL_WORDS) + r")"
_QUAL = r"(?:(early|mid|middle|late|first half of the|second half of the)[\s-]+(?:the\s+)?)?"
CENTURY = re.compile(_QUAL + r"(?<![\w-])(?:" + _ORD + r")[\s-]+centur(?:y|ies)(\s*(?:BC|BCE|B\.C\.))?", re.I)
MILLENNIUM = re.compile(_QUAL + r"(?<![\w-])(?:" + _ORD + r")[\s-]+millenni(?:um|a)(\s*(?:BC|BCE|B\.C\.))?",
                        re.I)
YEAR = re.compile(r"(?<![\w.,£$])(?:c\.\s*|circa\s+|around\s+|about\s+|ca\.\s*)?"
                  r"(\d{3,4})(?:\s*(?:–|-|to)\s*\d{2,4})?\s*(BC|BCE|B\.C\.|AD|CE)?(?![\d%]|\.\d)"
                  r"(?!\s*-?\s*(?:acres?|hectares?|ha\b|metres?|meters?|m\b|feet|foot|ft\b|miles?|km\b|yards?"
                  r"|people|men\b|years|tonnes?|seats?|rooms|books|items|visitors|students|pupils|beds"
                  r"|kg\b|kilograms?|lb\b|pounds|stone\b))", re.I)
PERIODS = [(r"\bneolithic\b", -3500, "Neolithic"),
           (r"\bbronze age\b", -1500, "Bronze Age"),
           (r"\biron age\b", -300, "Iron Age"),
           (r"\bearly christian\b", 600, "Early Christian period"),
           (r"\bearly medieval\b", 600, "early medieval period"),
           (r"\b(?:anglo-)?norman\b", 1200, "Anglo-Norman period")]

PERIOD_LABELS = {label for _, _, label in PERIODS}


_WIDE_RANGE = re.compile(r"(\d{3,4})\s*(?:–|-|to)\s*(\d{3,4})")


def is_period_level(hit):
    """A period word, an infobox period/epoch field, or a range of 800+ years
    (e.g. 'c. 4000–2500 BC', i.e. 'Neolithic') rather than a building date."""
    if hit[1] in PERIOD_LABELS or hit[2].startswith(("Infobox period", "Infobox epochs")):
        return True
    m = _WIDE_RANGE.search(hit[1]) or _WIDE_RANGE.search(hit[2][:120])
    return bool(m) and abs(int(m.group(1)) - int(m.group(2))) >= 800 and str(hit[0]).lstrip("-") == m.group(1)


def rank(hit):
    """Sort key for hits: specific dates (years, centuries) before period-level ones, then earliest."""
    return (is_period_level(hit), hit[0])


STRONG_WORDS = re.compile(r"\b(built|constructed|erected|dat(?:es|ing|ed)|raised|begun|was made"
                          r"|carved|-century)\b", re.I)
WEAK_WORDS = re.compile(r"\b(founded|foundation|established|origin)\b", re.I)
SKIP_WORDS = re.compile(r"\b(restor|repair|rebuil|renovat|dissol|destroy|burn|demolish|died|death"
                        r"|excavat|survey|record|listed|declared|acquired|sold|visited|"
                        r"suppress|plunder|raid|sack|born|publish|photograph|site of|previous"
                        r"|earlier|predecessor|said to|tradition|legend|reign|lord of|king of|kingdom"
                        r"|sits on|stands on|on the site|once stood|brought|moved|relic|shrine of|centenary"
                        r"|anniversary|celebrat|reopen|refurbish|closed|scheduled|designated)", re.I)
# sentences describing a structure that preceded the present one
EARLIER_STRUCTURE = re.compile(r"\b(once stood|formerly stood|previously stood|earlier (?:church|fort"
                               r"|building|structure)|replaced an?)\b", re.I)
# a date after these words describes something else the building is compared with
COMPARISON = re.compile(r"\b(resembl|modell?ed on|inspired|imitat|elsewhere|the continent|painter)", re.I)
# "8th–10th centuries", "7th or 8th century" -> keep the first century of the range
_CENT_RANGE = re.compile(r"(\b\d{1,2}(?:st|nd|rd|th)|\b(?:" + "|".join(ORDINAL_WORDS) + r"))"
                         r"\s*(?:–|-|or|to|and)\s*(?=(?:\d{1,2}(?:st|nd|rd|th)|"
                         + "|".join(ORDINAL_WORDS) + r")[\s-]+centur)", re.I)
# "(470–549)" right after a name: a lifespan or reign, not a construction date
_PAREN_RANGE = re.compile(r"\(\s*(?:c\.\s*)?\d{3,4}\s*[–-]\s*\d{2,4}\s*\)")


def _ord_value(num, word):
    return int(num) if num else ORDINAL_WORDS[word.lower()]


def _century_start(n, bc, qual):
    if bc:
        start = -n * 100
        return start + (66 if qual and qual.lower().startswith("late") else 0)
    start = (n - 1) * 100 + 1
    q = (qual or "").lower()
    if q.startswith("mid") or q.startswith("middle"):
        return start + 33
    if q.startswith("late") or q.startswith("second half"):
        return start + 50
    return start


def _sentences(text):
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+|\n+", text or "") if s.strip()]


def candidates(sentence):
    """All (year, label) date expressions in one sentence."""
    sentence = _PAREN_RANGE.sub(" ", _CENT_RANGE.sub(r"\1 century ", sentence))
    out = []
    for m in MILLENNIUM.finditer(sentence):
        n = _ord_value(m.group(2), m.group(3))
        bc = bool(m.group(4))
        out.append((-n * 1000 if bc else (n - 1) * 1000 + 1, m.group(0).strip()))
    for m in CENTURY.finditer(sentence):
        n = _ord_value(m.group(2), m.group(3))
        if n > 21:
            continue
        out.append((_century_start(n, bool(m.group(4)), m.group(1)), m.group(0).strip()))
    for m in YEAR.finditer(sentence):
        y = int(m.group(1))
        era = (m.group(2) or "").upper()
        if era.startswith("B"):
            y = -y
        elif not era and (y < 400 or y > 2030):
            continue          # bare small numbers are usually measurements
        out.append((y, m.group(0).strip()))
    if not out:
        for pat, year, label in PERIODS:
            if re.search(pat, sentence, re.I):
                out.append((year, label))
    return out


# strict mode (date checks): sentences about something other than the building's own fabric
NOT_FABRIC = re.compile(r"\b(saint|dedicated to|domesday|grave|burial|finds?|coins?|hoard|necklace|"
                        r"occupied by|stands today|now occupied|house called|on the site|owned by|"
                        r"granted|charter|mentioned|recorded in|first record|collections?|manuscripts?|"
                        r"artist|painter|portrait|in memory|cemetery|nearby|neighbouring|original village|"
                        r"not be confused|anniversary|fonts?|cross(?:es)?|cross shaft|carved stones?|"
                        r"inscribed stone|sundial|altars?|doorway|reused|gardens?|in the style of|"
                        r"adjoining|automaton|code|parish chest|coffin|-century [\w\s-]{0,30}style|reinterpretation|"
                        r"commemorat\w*|hero|pilgrimage|overlooks|proximity|outside the building|"
                        r"close to|formerly that of|inscription|legible|dedication to|entertained|"
                        r"grotto|water feature|façade of|flushwork)\b", re.I)


def date_from_text(text, max_sentences=60, strict=False):
    """Earliest date in a building-construction sentence -> (year, label, evidence) or None.

    Sentences about building ('built', 'dates from', '12th-century') win over founding
    sentences ('founded', 'established'), which often refer to an earlier site. strict=True
    (used to check dates) also skips sentences about saints, finds, later houses on the site …
    """
    strong = weak = None
    for s in _sentences(text)[:max_sentences]:
        is_strong, is_weak = bool(STRONG_WORDS.search(s)), bool(WEAK_WORDS.search(s))
        if not (is_strong or is_weak) or len(s) > 600 or EARLIER_STRUCTURE.search(s):
            continue
        if strict and NOT_FABRIC.search(s):
            continue
        clean = _PAREN_RANGE.sub(" ", _CENT_RANGE.sub(r"\1 century ", s))
        for year, label in candidates(s):
            pos = clean.find(label)
            if SKIP_WORDS.search(clean[max(0, pos - 120):pos]) or COMPARISON.search(clean[:max(pos, 0)]):
                continue
            hit = (year, label, s)
            if is_strong and (strong is None or rank(hit) < rank(strong)):
                strong = hit
            elif not is_strong and (weak is None or rank(hit) < rank(weak)):
                weak = hit
    return strong or weak


# "date"/"dates" are left out: in many infoboxes they hold the photo's date, not the building's
INFOBOX_FIELDS = ("built", "build", "construction_start_date", "start_date", "period", "constructed", "completion_date", "years", "construction",
                  "built_date", "beginning_date", "epochs", "established", "founded")


def date_from_infobox(wikitext):
    """Earliest date in the infobox's construction-type fields -> (year, label, evidence)."""
    best = None
    for field in INFOBOX_FIELDS:
        for m in re.finditer(r"\|\s*" + field + r"\s*=\s*([^\n|]+)", wikitext or "", re.I):
            raw = re.sub(r"\[\[(?:[^\]|]*\|)?([^\]]*)\]\]", r"\1", m.group(1))
            raw = re.sub(r"<[^>]+>|\{\{[^}]*\}\}", " ", raw).strip()
            for year, label in candidates(raw):
                hit = (year, label, f"Infobox {field}: {raw}")
                if best is None or rank(hit) < rank(best):
                    best = hit
    return best
