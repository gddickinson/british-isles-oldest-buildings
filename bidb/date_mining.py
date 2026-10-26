"""Find construction dates in free text (Wikipedia articles, infoboxes, descriptions).

Every hit keeps the sentence it came from, so the GUI can show the evidence.
"""
import re

ORDINAL_WORDS = {"first": 1, "second": 2, "third": 3, "fourth": 4, "fifth": 5, "sixth": 6,
                 "seventh": 7, "eighth": 8, "ninth": 9, "tenth": 10, "eleventh": 11,
                 "twelfth": 12, "thirteenth": 13, "fourteenth": 14, "fifteenth": 15,
                 "sixteenth": 16, "seventeenth": 17, "eighteenth": 18, "nineteenth": 19}
_ORD = r"(\d{1,2})(?:st|nd|rd|th)|(" + "|".join(ORDINAL_WORDS) + r")"
# "early-mid", "mid to late": the first qualifier counts (the earliest)
_QUAL = (r"(?:(early|mid|middle|late|first half of the|second half of the)[\s-]+"
         r"(?:(?:to\s+)?(?:early|mid|middle|late|later)[\s-]+)?(?:the\s+)?)?")
# the look-behind comes before the qualifier, so "mid-15th century" still matches
CENTURY = re.compile(r"(?<![\w-])" + _QUAL + r"(?:" + _ORD + r")[\s-]+centur(?:y|ies)(\s*(?:BC|BCE|B\.C\.))?", re.I)
MILLENNIUM = re.compile(r"(?<![\w-])" + _QUAL + r"(?:" + _ORD + r")[\s-]+millenni(?:um|a)(\s*(?:BC|BCE|B\.C\.))?",
                        re.I)
YEAR = re.compile(r"(?<![\w.,£$])(c\.?\s*|circa\s+|around\s+|about\s+|ca\.\s*)?"
                  r"(\d{3,4})(?:\s*(?:–|-|to)\s*\d{2,4})?(?:\s*±\s*\d{1,4})?\s*(BC|BCE|B\.C\.|AD|CE)?(?![\d%]|\.\d|,\d{3})"
                  r"(?!(?:st|nd|rd|th)\b|-year|\s*(?:and|to|or|-|–)\s*[\d,]+\s*years|\s*(?:sq\b|square|cubic|long\b|short\b))"
                  r"(?!\s*-?\s*(?:acres?|hectares?|ha\b|metres?|meters?|m\b|m2\b|mm\b|cm\b|feet|foot|ft\b"
                  r"|inch(?:es)?|miles?|km\b|yards?|yd\b|people|men\b|years|tonnes?|tons|seats?|rooms|books|items"
                  r"|visitors|students|pupils|beds|kg\b|kilograms?|lb\b|pounds|stone\b|coins|jobs|workers|employees"
                  r"|staff|soldiers|troops|cavalry\w*|infantry\w*|squadron|regiment|megawatts?|mw\b|kw\b|volts?"
                  r"|horsepower|hp\b|houses|homes|dwellings|families|residential|units|vehicles|cars|trains"
                  r"|passengers|households|persons|inhabitants|residents|members|graves|burials|bodies|skeletons"
                  r"|into\b|of\s+(?:them|these|those|which)))", re.I)
# "around AD 75", "AD 100–400": years under 400 only with the era in front
AD_SHORT = re.compile(r"(?<![\w.])(?:(?:c\.|circa|around|about)\s*)?(?:AD|A\.D\.)\s?(\d{1,3})(?![\d,.]\d|\s*-?\s*(?:years|%))\b")
_LIFE = re.compile(r"\b(?:d|b|fl|r)\.\s*(?:AD\s*)?$|\b(?:died|born)\s+(?:in\s+)?(?:AD\s*)?$", re.I)
# a bare number under 1000 (no "AD", "c.") counts as a year only after words that introduce one
_BARE_CONTEXT = re.compile(r"(?:^|:\s*|\b(?:AD|CE|in|from|of|by|after|before|between|and|until|till|to|since|year|early|late"
                           r"|mid|built|founded|dated?|established|begun|erected)\s+(?:the\s+year\s+)?)$", re.I)
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
# "a Grade I listed house built in 1540": the grade says nothing about the date ("listed in 1952" does)
_GRADE = re.compile(r"(?<!made a )(?<!became a )(?<!designated a )(?<!designated as a )\b(?:grade|category)\s+(?:I{1,3}|II\*|[AB]\+?)\s+listed\b", re.I)
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
    # not after "(d. 655)", "b. 1590", "c. 1200", "fl. 1400"
    return [s.strip() for s in re.split(r"(?<!\bd\.)(?<!\bb\.)(?<!\bc\.)(?<!\bfl\.)(?<=[.!?])\s+|\n+", text or "")
            if s.strip()]


def _bare_year(sentence, m):
    """A number under 1000 with no era: a decade after "the" ("the 550s"), else a year only after "c."
    or a word that introduces one ("in 924", "before 959")."""
    before = sentence[:m.start()]
    if sentence[m.end():m.end() + 1] == "s" and not sentence[m.end() + 1:m.end() + 2].isalpha():
        return bool(re.search(r"\bthe\s+$", before))
    return bool(m.group(1)) or bool(_BARE_CONTEXT.search(before.rstrip() + (" " if before else "")))


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
        if _LIFE.search(sentence[:m.start()]):
            continue          # "(d. 655)", "(b. 1270)": a person's dates
        y = int(m.group(2))
        era = (m.group(3) or "").upper()
        if era.startswith("B"):
            y = -y
        elif not era and (y < 400 or y > 2030):
            continue          # bare small numbers are usually measurements
        elif not era and y < 1000 and not _bare_year(sentence, m):
            continue          # "the remaining 600", "generating 400 megawatts", "500s": counts, not years
        out.append((y, m.group(0).strip()))
    out += [(int(m.group(1)), m.group(0).strip()) for m in AD_SHORT.finditer(sentence)
            if int(m.group(1)) < 400 and not _LIFE.search(sentence[:m.start()])]
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
            if SKIP_WORDS.search(_GRADE.sub("", clean[max(0, pos - 120):pos])) or \
                    COMPARISON.search(clean[:max(pos, 0)]):
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
