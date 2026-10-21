"""Pronunciations from the opening of a Wikipedia article (wikitext).

    '''Belvoir Castle''' ({{IPAc-en|ˈ|b|iː|v|ər|audio=En-belvoir_castle.ogg}} {{respell|BEE|vər}})
    '''Kilkenny Castle''' ({{langx|ga|Caisleán Chill Chainnigh}} {{IPA|ga|ˈkaʃlʲaːnˠ …|pron}})

`parse_lead(text, title)` returns one dict per pronunciation or native name:
    {"name", "lang", "variety", "ipa", "respell", "audio"}
English rows are labelled by any qualifier ("locally", "US", "Scotland"); native-name rows by
their language (Welsh, Scottish Gaelic, Irish, Manx, Cornish, Scots, Jèrriais …), with an Irish
dialect when the template gives one (Munster, Connacht, Ulster).
"""
import re

LANGS = {
    "en": "English", "cy": "Welsh", "gd": "Scottish Gaelic", "ga": "Irish", "gv": "Manx",
    "kw": "Cornish", "sco": "Scots", "nrf": "Jèrriais / Guernésiais", "nfr": "Jèrriais / Guernésiais",
    "fr": "French", "la": "Latin", "ang": "Old English", "non": "Old Norse", "sga": "Old Irish",
    "pgl": "Primitive Irish", "wlm": "Middle Welsh", "enm": "Middle English", "xcb": "Cumbric",
    "pi": "Pictish", "nrn": "Norn", "yol": "Yola", "shta": "Shelta", "ulst1238": "Ulster Scots",
    "scz": "Shetland Scots (Shaetlan)", "mga": "Middle Irish", "xno": "Anglo-Norman", "owl": "Old Welsh",
    "fro": "Old French", "frm": "Middle French", "gem": "Proto-Germanic", "cel": "Proto-Celtic",
}
# languages of the isles (and of their place names); other languages only when an article gives them
ISLES_LANGS = set(LANGS)
OTHER_LANGS = {
    "de": "German", "nl": "Dutch", "it": "Italian", "es": "Spanish", "pt": "Portuguese", "ru": "Russian",
    "el": "Greek", "grc": "Ancient Greek", "he": "Hebrew", "yi": "Yiddish", "ar": "Arabic", "pl": "Polish",
    "uk": "Ukrainian", "cs": "Czech", "hu": "Hungarian", "no": "Norwegian", "nb": "Norwegian", "da": "Danish",
    "sv": "Swedish", "is": "Icelandic", "fi": "Finnish", "ja": "Japanese", "zh": "Chinese", "hi": "Hindi",
    "ur": "Urdu", "bn": "Bengali", "pa": "Punjabi", "mr": "Marathi", "fa": "Persian", "tr": "Turkish",
    "rus": "Russian", "be": "Belarusian", "bg": "Bulgarian", "ca": "Catalan", "eu": "Basque", "ro": "Romanian",
    "th": "Thai", "uz": "Uzbek", "egy": "Egyptian", "arz": "Egyptian Arabic",
}
# words that qualify an English pronunciation, as template labels or just before the template
QUALIFIERS = {
    "local": "Local", "locally": "Local", "uk": "British English", "us": "American English", "also": "Alternative",
    "scotland": "Scottish English", "scottish": "Scottish English", "ireland": "Irish English",
    "irish": "Irish English", "wales": "Welsh English", "welsh": "Welsh English",
    "traditionally": "Traditional", "traditional": "Traditional", "formerly": "Traditional",
    "rp": "Received Pronunciation", "commonly": "Common", "usually": "Common",
    "northern": "Northern English", "ulster": "Ulster English", "australia": None, "or": None,
    "lang": None, "pron": None, "": None,
}
REGIONAL = {"en-gb": "British English", "en-us": "American English", "en-ie": "Irish English",
            "en-scotland": "Scottish English", "cy-north": "Welsh (north)", "cy-south": "Welsh (south)"}
IRISH_DIALECTS = {"munster": "Munster", "connacht": "Connacht", "ulster": "Ulster", "cois fharraige": "Connacht"}
WINDOW = 450                 # only templates this close after the bold name describe it
NOTE_TEMPLATES = {"efn", "efn-ua", "efn-lr", "efn-lg", "refn", "notetag"}
_REF = re.compile(r"<ref[^>/]*/>|<ref[^>]*>.*?</ref>|<!--.*?-->", re.S)
_BOLD = re.compile(r"'''(.+?)'''")


def variety_of(lang):
    """Language code -> variety label ('en-gb' -> British English, 'gd' -> Scottish Gaelic)."""
    lang = (lang or "en").lower()
    base = lang.split("-")[0]
    return REGIONAL.get(lang) or LANGS.get(lang) or LANGS.get(base) or OTHER_LANGS.get(base, lang)


def templates(text):
    """Top-level {{templates}} in text -> [(start, end, name, [args])] (nested ones kept in args)."""
    out, i, n = [], 0, len(text)
    while True:
        i = text.find("{{", i)
        if i < 0:
            return out
        depth, j = 0, i
        while j < n - 1:
            if text.startswith("{{", j):
                depth += 1
                j += 2
            elif text.startswith("}}", j):
                depth -= 1
                j += 2
                if depth == 0:
                    break
            else:
                j += 1
        if depth:
            return out
        body = text[i + 2:j - 2]
        parts = _split_args(body)
        out.append((i, j, parts[0].strip().lower(), parts[1:]))
        i = j


def _split_args(body):
    parts, depth, cur = [], 0, []
    k = 0
    while k < len(body):
        two = body[k:k + 2]
        if two in ("{{", "[["):
            depth += 1
            cur.append(two)
            k += 2
            continue
        if two in ("}}", "]]"):
            depth -= 1
            cur.append(two)
            k += 2
            continue
        if body[k] == "|" and depth == 0:
            parts.append("".join(cur))
            cur = []
        else:
            cur.append(body[k])
        k += 1
    parts.append("".join(cur))
    return parts


def plain(s):
    """Wikitext fragment -> plain text ([[a|b]] -> b, templates and markup dropped)."""
    s = re.sub(r"\[\[(?:[^|\]]*\|)?([^\]]*)\]\]", r"\1", s)
    s = re.sub(r"\{\{[^{}]*\}\}", "", s)
    s = re.sub(r"'{2,}|<[^>]+>", "", s)
    return re.sub(r"\s+", " ", s).strip(" ,;:")


def _named(args):
    pos, named = [], {}
    for a in args:
        m = re.match(r"\s*([a-z0-9_-]+)\s*=(.*)$", a, re.S)
        if m:
            named[m.group(1).lower()] = m.group(2).strip()
        else:
            pos.append(a.strip())
    return pos, named


def _ipac_en(args):
    """{{IPAc-en|lang|ˈ|b|iː|v|ər}} -> (ipa, [qualifier labels])."""
    pos, named = _named(args)
    labels, sounds = [], []
    for a in pos:
        key = a.lower().rstrip(":")
        if key in QUALIFIERS and not sounds:          # labels come before the phonemes
            if QUALIFIERS[key]:
                labels.append(QUALIFIERS[key])
            continue
        sounds.append({"'": "ˈ", ",": "ˌ", ",_": ", ", ";_": "; ", "_": " ", "-": ""}.get(a, a.replace("_", " ")))
    ipa = "".join(sounds).strip()
    return ipa, labels, named.get("audio", "")


def _partial(args):
    """{{IPAc-en|-|f|ɑː|s|t}}: only the end of the word (an alternative ending)."""
    pos, _ = _named(args)
    return bool(pos) and pos[0] in ("-", "…")


def _respell(args):
    pos, _ = _named(args)
    return "-".join(p.replace("_", " ") for p in pos if p)


def _ipa_template(name, args):
    """{{IPA|cy|…|pron}} / {{IPA-cy|…}} -> (lang, ipa, label, audio) or None."""
    pos, named = _named(args)
    if name == "ipa" and pos:
        lang, pos = pos[0].lower(), pos[1:]
    elif name.startswith("ipa-"):
        lang = name[4:]
    else:
        return None
    if not pos or not pos[0]:
        return None
    label = pos[1].lower() if len(pos) > 1 else ""
    return lang, pos[0].strip(), label, named.get("audio", "")


def _lang_name(name, args):
    """{{langx|cy|Castell Caernarfon}}, {{lang-cy|…}}, {{lang|gd|…}} -> (lang, text) or None."""
    pos, _ = _named(args)
    if name in ("langx", "lang", "langr", "lang-x") and len(pos) >= 2:
        return pos[0].lower(), plain(pos[1])
    if name.startswith("lang-") and pos:
        return name[5:], plain(pos[0])
    return None


def _qualifier_before(text, start):
    """'' locally '' or 'US:' written just before a template."""
    tail = plain(re.sub(r"\{\{[^{}]*\}\}", "", text[max(0, start - 40):start])).lower()
    words = re.findall(r"[a-z]+", tail)
    for w in reversed(words[-3:]):
        if QUALIFIERS.get(w):
            return QUALIFIERS[w]
    return None


def _names_subject(scope, start, raw=""):
    """A {{lang}} name is the subject's own when it is bold, follows "also known as", or sits
    in the brackets opened after the first bold name; not foreign words in the running text
    ("… on {{langr|ga|Inis Mór}}")."""
    before = plain(scope[max(0, start - 40):start]).lower()
    if re.search(r"\b(from|meaning|derive[sd]?|word|literally)\b[^.;]*$", before):
        return False                             # etymology, not another name
    if scope[max(0, start - 3):start] == "'''" or "'''" in raw:
        return True
    if re.search(r"(also|formerly|otherwise) (known|called) as\s*$|\bor\s*$", scope[max(0, start - 30):start]):
        return True
    first_bold = scope.find("'''")
    if first_bold < 0 or first_bold > start:
        return False
    between = re.sub(r"\{\{(?:[^{}]|\{\{[^{}]*\}\})*\}\}", "", scope[first_bold:start])
    return between.count("(") > between.count(")")


def clean_lead(wikitext):
    """Opening paragraph(s) of an article: refs removed, starting at the first bold name."""
    lead = _REF.sub("", wikitext.split("\n==")[0])
    spans = [(a, b) for a, b, _, _ in templates(lead)]

    def inside(k):
        return any(a <= k < b for a, b in spans)
    for m in re.finditer(r"'''", lead):
        if not inside(m.start()):
            return lead[lead.rfind("\n", 0, m.start()) + 1:].strip()
    for m in re.finditer(r"(?m)^[A-Z][^\n]{40,}", lead):      # no bold name: first prose line
        if not inside(m.start()):
            return lead[m.start():].strip()
    return ""


def parse_lead(text, title=""):
    """Pronunciation / native-name rows from a cleaned lead (see module docstring)."""
    text = text[:2500]
    bold = _BOLD.search(text)
    head = plain(bold.group(1)) if bold else re.sub(r"\s*\(.*\)$", "", title)
    rows, last_native = [], {}
    first_para_end = text.find("\n\n")
    scope = text if first_para_end < 0 else text[:first_para_end]
    limit = (bold.end() if bold else 0) + WINDOW
    found = []
    for start, end, name, args in templates(scope):
        if start > limit:
            break
        if name in NOTE_TEMPLATES and args:                  # pronunciations kept in a footnote
            found += [(start, end, n, a) for _, _, n, a in templates(args[-1])]
        else:
            found.append((start, end, name, args))
    for start, end, name, args in found:
        if name in ("ipac-en", "ipa-cen"):          # IPA-cen: a variant spelling of IPAc-en
            ipa, labels, audio = _ipac_en(args)
            if (not ipa and not audio) or _partial(args):
                continue
            q = _qualifier_before(scope, start)
            rows.append({"name": head, "lang": "en", "variety": labels[0] if labels else (q or "English"),
                         "ipa": ipa, "respell": "", "audio": audio})
        elif name == "respell":
            sp = _respell(args)
            if sp.startswith("-") or _partial(args):
                continue
            target = next((r for r in reversed(rows) if (r["ipa"] or r["lang"] == "en") and not r["respell"]), None)
            if target and start - _end_of(scope, target) < 40:
                target["respell"] = sp
            elif sp:
                rows.append({"name": head, "lang": "en", "variety": _qualifier_before(scope, start) or "English",
                             "ipa": "", "respell": sp, "audio": ""})
        elif name == "ipa" or name.startswith("ipa-"):
            got = _ipa_template(name, args)
            if not got:
                continue
            lang, ipa, label, audio = got
            variety = variety_of(lang)
            if lang == "ga" and label in IRISH_DIALECTS:
                variety += f" ({IRISH_DIALECTS[label]})"
            if lang == "en":
                variety = QUALIFIERS.get(label) or _qualifier_before(scope, start) or "English"
            nm = last_native.get(lang) or head
            rows.append({"name": nm, "lang": lang, "variety": variety, "ipa": ipa, "respell": "",
                         "audio": audio})
        else:
            got = _lang_name(name, args)
            if got and got[1] and got[0] != "en" and _names_subject(scope, start, "|".join(args)):
                lang, nm = got
                last_native[lang] = nm
                rows.append({"name": nm, "lang": lang, "variety": variety_of(lang), "ipa": "",
                             "respell": "", "audio": "", "_native": True})
        if rows:
            rows[-1].setdefault("_end", end)
    return _merge(rows)


def _end_of(scope, row):
    return row.get("_end", 0)


def _merge(rows):
    """A native name followed by its IPA becomes one row; drop helper keys and duplicates."""
    out = []
    for r in rows:
        prev = next((o for o in reversed(out) if o["lang"] == r["lang"] and o["name"] == r["name"]
                     and o.get("_native") and not o["ipa"]), None)
        if prev and r["ipa"] and not r.get("_native"):
            prev.update(ipa=r["ipa"], audio=r["audio"] or prev["audio"], variety=r["variety"])
            prev.pop("_native", None)
            continue
        out.append(r)
    seen, final = set(), []
    for r in out:
        r = {k: v for k, v in r.items() if not k.startswith("_")}
        key = (r["name"], r["lang"], r["variety"], r["ipa"], r["respell"])
        if key not in seen:
            seen.add(key)
            final.append(r)
    return final
