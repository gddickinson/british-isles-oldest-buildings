"""Stories from Wikipedia articles: legends and myths, ghosts and the supernatural, folklore and
customs, and curious history (secret passages, treasure, smugglers …).

    article wikitext --sections()--> {"s": [[heading, plain text], …], "c": [categories]}
                     --find()------> [{"kind", "heading", "text"}]

A whole section counts when its heading names the theme ("Legends", "Ghosts", "Folklore");
elsewhere single sentences (with the next one when it continues the tale) are taken.
"""
import html
import re

from .pron_parse import templates

KINDS = {
    "supernatural": "Ghosts & the supernatural",
    "legend": "Legends & myths",
    "folklore": "Folklore & customs",
    "curiosity": "Curious history",
}
SKIP_SECTIONS = re.compile(r"^(references?|notes?|citations?|sources?|bibliography|further reading|"
                           r"external links?|see also|gallery|footnotes|literature|(?:in )?popular culture|"
                           r"in (?:literature|fiction|film|films|art|the arts|media|television)|media|"
                           r"cultural references|filming|film and television|present use|present day|"
                           r"current use|today|tourism|visitor\w*|events|sport|transport|media appearances|"
                           r"appearances in media|in the media|filming location\w*|stands?|facilities|"
                           r"notable (?:interments|burials|residents|people|graves)|burials|residents|"
                           r"notable people|in film and television)$", re.I)
HEADINGS = [
    ("supernatural", re.compile(r"ghost|haunt|paranormal|supernatural|spectr|apparition", re.I)),
    ("legend", re.compile(r"legend|myths?\b|arthur|fair(?:y|ies)|giants?\b|dragon", re.I)),
    ("folklore", re.compile(r"folklore|folk ?tales?|traditions\b|customs\b|superstition|curse|witch", re.I)),
]
PATTERNS = [
    ("supernatural", re.compile(
        r"\b(ghosts?|ghostly|haunt(?:ed|ing|s)?|spectr(?:e|es|al)|apparitions?|poltergeists?|phantoms?|"
        r"paranormal|banshee|boggarts?|supernatural|(?:grey|gray|white|green|blue|brown|pink) lady|"
        r"headless (?:horseman|man|woman|drummer|figure)|black dog)\b", re.I)),
    ("legend", re.compile(
        r"\b([Ll]egends?|[Ll]egendary|myth (?:says|has it|tells)|local myth|according to (?:local )?(?:tradition|"
        r"legend|folklore|myth)|[Tt]radition (?:holds|has it|says|states|relates)|King Arthur|Arthurian|"
        r"Robin Hood|a giant (?:named|called|who)|giants? (?:who|which|that) |the [Dd]evil (?:is said|was said|"
        r"built|threw|appeared|himself)|fairy (?:fort|ring|mound|tree|folk)|fairies|miracles?|"
        r"[Ff]olk ?tales?|is said to have been (?:buried|killed|born|hidden))\b")),
    ("folklore", re.compile(
        r"\b(folklore|superstitions?|superstitious|well[- ]dressing|wishing (?:well|tree|stone)|"
        r"healing (?:well|waters?|powers?)|holy well|cursed?|curses|witch(?:es|craft)?|pagan (?:ritual|"
        r"custom|festival|worship|sanctuary)|Beltane|Samhain|"
        r"(?:annual|ancient|local|old) custom|solstice|fertility (?:rite|ritual|stone|charm))\b", re.I)),
    ("curiosity", re.compile(
        r"\b(secret (?:passages?|tunnels?|rooms?|chambers?|stair\w*)|priest[- ]holes?|tunnels? (?:is|are|was|"
        r"were) said|hidden (?:chamber|room|treasure|passage)|buried treasure|treasure (?:is|was) said|"
        r"smuggl\w*|was murdered|gibbet|mummified|witch bottles?|concealed shoes|"
        r"mysterious (?:death|disappearance|figure|stranger)|unexplained (?:death|noises?|lights?|events?))\b", re.I)),
]
# sentences that mention a theme word but are not a story (popular culture, sport, business …)
NOT_A_STORY = re.compile(r"\b(film|television|TV series|episode|video game|novel|album|band|football|"
                         r"rugby|cricket|hotel|restaurant|company|brand|ship|locomotive|the Legend of|"
                         r"legendary (?:player|status)|Ghostbusters|tour(?:s|ism)?|ghost walks?|"
                         r"Most Haunted|programme|documentary|podcast|YouTube|investigat\w*|"
                         r"Shakespeare|A Midsummer|suicide|died by|painting|painted|sculpture|carving|"
                         r"carved|depict\w*|panel|motifs?|ornament\w*|decorated|manuscript|chronicle|watercolou?r|lounge|"
                         r"hospitality|stadium|club|League of Legends|Doctor Who|filming|filmed|"
                         r"Robin Hood (?:Gate|Way|Road|Lane|Street))\b", re.I)
SPORTING_LEGEND = re.compile(r"\b[A-Z]\w+ legend [A-Z]")             # "Leeds legend Norman Hunter"
# curious history is about the past: sentences about the 20th/21st century are left out
MODERN = re.compile(r"\b(19|20)\d\d\b")
MAX_STORIES, MAX_CHARS = 4, 700
CATEGORY_KINDS = [("supernatural", re.compile(r"haunted|ghost", re.I)),
                  ("legend", re.compile(r"legend|mytholog|arthurian", re.I)),
                  ("folklore", re.compile(r"folklore|holy wells", re.I))]


# ---- wikitext -> plain sections -----------------------------------------------------------
_REMOVE = re.compile(r"<!--.*?-->|<ref[^>]*/>|<ref[^>]*>.*?</ref>|<gallery.*?</gallery>|"
                     r"<timeline.*?</timeline>|<math.*?</math>", re.S | re.I)
KEEP_LAST = {"lang", "langx", "transl", "nowrap", "small", "nobr", "em", "lang-cy", "lang-ga",
             "lang-gd", "lang-la", "lang-kw", "lang-gv", "lang-sco", "lang-ang", "lang-non"}


def _template_text(name, args):
    if name in ("circa", "c.", "c"):
        return "c. " + (args[0] if args else "")
    if name == "convert" and len(args) >= 2:
        return f"{args[0]} {args[1]}"
    if name in KEEP_LAST or name.startswith("lang-"):
        pos = [a for a in args if "=" not in a.split("|")[0]]
        return pos[-1] if pos else ""
    if name in ("as of",):
        return "as of " + (args[0] if args else "")
    return ""


def _drop_templates(text):
    out, last = [], 0
    for start, end, name, args in templates(text):
        out.append(text[last:start])
        out.append(_drop_templates(_template_text(name, args)))
        last = end
    out.append(text[last:])
    return "".join(out)


def _drop_files(text):
    """Remove [[File:…]] / [[Image:…]] including nested links in captions."""
    while True:
        m = re.search(r"\[\[(?:File|Image):", text, re.I)
        if not m:
            return text
        depth, j = 0, m.start()
        while j < len(text) - 1:
            if text.startswith("[[", j):
                depth += 1
                j += 2
            elif text.startswith("]]", j):
                depth -= 1
                j += 2
                if depth == 0:
                    break
            else:
                j += 1
        text = text[:m.start()] + text[j:]


def _plain(text):
    text = re.sub(r"\{\|.*?\|\}", " ", text, flags=re.S)                   # tables
    text = _drop_files(_drop_templates(text))
    text = re.sub(r"\[\[(?:[^|\]]*\|)?([^\]]*)\]\]", r"\1", text)
    text = re.sub(r"\[https?://\S+\s+([^\]]*)\]|\[https?://\S+\]", r"\1", text)
    text = html.unescape(re.sub(r"'{2,}|<[^>]+>|__\w+__", "", text)).replace("\xa0", " ")
    text = re.sub(r"^[*#:;]+\s*", "", text, flags=re.M)
    text = re.sub(r"[ \t]+", " ", text)
    return re.sub(r"\n{2,}", "\n\n", text).strip()


def sections(wikitext):
    """Full article wikitext -> {"s": [[heading, plain text], …], "c": [category names]} (cached)."""
    cats = re.findall(r"\[\[Category:([^\]|]+)", wikitext or "")
    text = _REMOVE.sub("", wikitext or "")
    text = re.sub(r"\[\[Category:[^\]]*\]\]", "", text)
    parts = re.split(r"^(={2,})\s*(.*?)\s*\1\s*$", text, flags=re.M)
    out = [["", _plain(parts[0])]]
    for i in range(1, len(parts) - 2, 3):
        heading = _plain(parts[i + 1])
        if SKIP_SECTIONS.match(heading):
            continue
        body = _plain(parts[i + 2])
        if body:
            out.append([heading, body])
    return {"s": [s for s in out if s[1]], "c": cats}


# ---- plain sections -> stories ------------------------------------------------------------
def _sentences(text):
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+(?=[A-Z\"'‘“(])|\n+", text) if s.strip()]


def _kind_of(sentence):
    if NOT_A_STORY.search(sentence) or SPORTING_LEGEND.search(sentence):
        return None
    for kind, pat in PATTERNS:
        if pat.search(sentence):
            return None if MODERN.search(sentence) else kind     # tales are about the past
    return None


def _trim(text):
    if len(text) <= MAX_CHARS:
        return text
    cut = text[:MAX_CHARS]
    end = max(cut.rfind(". "), cut.rfind('." '))
    return (cut[:end + 1] if end > MAX_CHARS // 2 else cut.rsplit(" ", 1)[0]) + " …"


CONTINUES = re.compile(r"(She|He|They|It|This|These|Her|His|Their|Eventually|However|Later|Afterwards|"
                       r"Subsequently|Thereafter|Then)\b")
TELL_CHARS = 450              # a sentence-level story keeps the rest of its paragraph up to this


def _clean_sentences(text):
    return [s for s in _sentences(text) if not NOT_A_STORY.search(s)]


def find(entry):
    """Cached article entry -> [{"kind", "heading", "text"}] (at most MAX_STORIES).
    Whole themed sections ("Ghosts") may mention modern sightings; single sentences may not."""
    if not entry:
        return []
    stories = []
    for heading, body in entry.get("s", []):
        if SKIP_SECTIONS.match(heading):
            continue
        body = html.unescape(body).replace("\xa0", " ")
        hk = next((k for k, pat in HEADINGS if heading and pat.search(heading)), None)
        if hk and not NOT_A_STORY.search(heading):
            text = " ".join(_clean_sentences(body))
            if text:
                stories.append({"kind": hk, "heading": heading, "text": _trim(text)})
            continue
        for para in body.split("\n\n"):
            sents = _sentences(para)
            i = used = 0
            while i < len(sents):
                kind = _kind_of(sents[i])
                if not kind:
                    i += 1
                    continue
                if i > used and CONTINUES.match(sents[i]) and len(sents[i - 1]) < 300:
                    i -= 1                           # "Eventually, she was accused …": say who first
                j, size = i + 1, len(sents[i])
                while j < len(sents) and size + len(sents[j]) <= TELL_CHARS and not NOT_A_STORY.search(sents[j]):
                    size += len(sents[j])
                    j += 1
                stories.append({"kind": kind, "heading": heading, "text": _trim(" ".join(sents[i:j]))})
                i = used = j
    # one story per theme first, then more of the same theme, in article order
    first, rest = [], []
    for s in stories:
        (rest if s["kind"] in {x["kind"] for x in first} else first).append(s)
    picked = (first + rest)[:MAX_STORIES]
    have = {s["kind"] for s in picked}
    for kind, pat in CATEGORY_KINDS:
        cat = next((c for c in entry.get("c", []) if pat.search(c)), None)
        if cat and kind not in have:
            picked.append({"kind": kind, "heading": "", "text": f"Wikipedia lists it under “{cat.strip()}”."})
    order = {s["text"]: n for n, s in enumerate(stories)}
    return sorted(picked, key=lambda s: order.get(s["text"], 99))
