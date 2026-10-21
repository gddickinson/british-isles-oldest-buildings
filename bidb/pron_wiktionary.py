"""Regional pronunciations of town names from English Wiktionary (CC BY-SA).

    * {{IPA|en|/ˈnjuːˌkæsl̩/|a=Northern England,Midlands}}
    ** {{audio|en|En-uk-Bicester.ogg|a=UK}}
    ==Welsh== * {{IPA|cy|/ɬaˈnɛɬi/}}

Only sections for languages of the isles are read; lines whose accent labels are not from the isles
(US, Australia, US vowel mergers …) or that are marked as a place elsewhere are skipped. An entry is
used only when its English section describes a place in the isles.
"""
import json
import re

from .http import request_json
from .pron_parse import _named, templates, variety_of
from .pron_sources import load_store, save_store

API = "https://en.wiktionary.org/w/api.php"
SECTIONS = {"English": "en", "Welsh": "cy", "Irish": "ga", "Scottish Gaelic": "gd", "Manx": "gv",
            "Cornish": "kw", "Scots": "sco"}
# accent labels from the isles -> variety; anything not listed (US states, mergers such as
# "cot-caught", Hong Kong, Australia …) means the line is not about a pronunciation used here
ACCENTS = {"rp": "Received Pronunciation", "ssbe": "Received Pronunciation", "ssb": "Received Pronunciation",
           "received pronunciation": "Received Pronunciation", "uk": "British English", "gb": "British English",
           "uk (places)": "British English", "england": "British English", "british": "British English",
           "southern england": "Southern English", "south east england": "Southern English",
           "south west england": "West Country", "west country": "West Country",
           "northern england": "Northern English", "northeast england": "Northeast England",
           "north east england": "Northeast England", "midlands": "Midlands",
           "scotland": "Scottish English", "scottish": "Scottish English", "ireland": "Irish English",
           "ie": "Irish English", "irish": "Irish English", "munster": "Irish English (Munster)",
           "wales": "Welsh English", "welsh": "Welsh English", "cy-n": "Welsh (north)", "cy-s": "Welsh (south)",
           "ulster": "Ulster English", "ni": "Ulster English", "northern ireland": "Ulster English",
           "local": "Local", "locally": "Local", "uk local": "Local", "anglicised": "Anglicised",
           "geordie": "Geordie", "scouse": "Scouse", "london": "London", "estuary english": "Estuary English",
           "cockney": "Cockney", "yorkshire": "Yorkshire", "lancashire": "Lancashire", "norfolk": "Norfolk",
           "essex": "Essex", "hampshire": "Hampshire", "berkshire": "Berkshire", "gloucestershire": "Gloucestershire",
           "northumberland": "Northumberland", "humberside": "Humberside", "tees valley": "Teesside",
           "cornwall": "Cornwall", "devon": "Devon", "somerset": "Somerset", "brummie": "Brummie"}
NEUTRAL = {"non-rhotic", "rhotic", "weak vowel", "r-insertion", "near-square", "non-near-square", "also"}
DATED = {"dated", "archaic", "obsolete", "early modern", "traditional", "older"}
US_SOUNDS = re.compile(r"[ɚɝ]|oʊ")
ISLES = re.compile(r"England|Scotland|Wales|Ireland|Isle of Man|Jersey|Guernsey|Cornwall|United Kingdom|"
                   r"\bUK\b|Britain|\{\{place\|en\|[^}]*(?:county|borough|parish|district)[^}]*(?:UK|"
                   r"England|Scotland|Wales|Ireland)", re.I)


def _pron_lines(text):
    """Wiktionary page -> {"isles": bool, "lines": {lang: [pronunciation lines]}} (what we cache)."""
    out, lang, isles = {}, None, False
    for line in text.splitlines():
        m = re.match(r"^==([^=].*?)==\s*$", line)
        if m:
            lang = SECTIONS.get(m.group(1).strip())
            continue
        if lang and ("{{IPA|" in line or "{{audio|" in line):
            out.setdefault(lang, []).append(line.strip())
        if lang == "en" and not isles and ISLES.search(line) and not line.startswith("*"):
            isles = True
    return {"isles": isles, "lines": out}


def _pages(text):
    if not text:
        return {}
    pages = json.loads(text).get("query", {}).get("pages", [])
    return {p["title"]: _pron_lines(p["revisions"][0]["slots"]["main"].get("content", ""))
            for p in pages if p.get("revisions")}


def fetch(titles, log=print, batch=50):
    """{title: cached pronunciation lines} for Wiktionary page titles (per-title store)."""
    titles = sorted({t for t in titles if t})
    store = load_store("wiktionary_pron")
    todo = [t for t in titles if t not in store]
    log(f"  wiktionary: {len(titles) - len(todo)} stored, {len(todo)} to fetch")
    for i in range(0, len(todo), batch):
        chunk = todo[i:i + batch]
        got = request_json(API, params={"action": "query", "prop": "revisions", "rvprop": "content",
                                        "rvslots": "main", "titles": "|".join(chunk), "format": "json",
                                        "formatversion": 2}, min_interval=0.5, extract=_pages, use_cache=False)
        for t in chunk:
            store[t] = got.get(t, {})
        if (i // batch) % 40 == 0:
            log(f"  wiktionary: {i + len(chunk)}/{len(todo)}")
            save_store(store, "wiktionary_pron")
    if todo:
        save_store(store, "wiktionary_pron")
    return {t: store.get(t, {}) for t in titles}


def _labels(named, line_labels=""):
    """Accent labels -> [varieties] ([] = unlabelled), or None when the line is about somewhere else."""
    if re.search(r"\b(US|America|Canada|Australia)\b", named.get("qq", "") + named.get("q", "")):
        return None
    text = named.get("a", "") or line_labels
    raw = [re.sub(r"[\[\]()]", "", a).strip() for a in text.replace("<<", "").replace(">>", "").split(",")]
    kept, dated, foreign = [], False, False
    for a in filter(None, raw):
        k = a.lower()
        if k.startswith("local "):
            k = "local"
        if k in ACCENTS:
            kept.append(ACCENTS[k])
        elif k in DATED:
            dated = True
        elif k not in NEUTRAL:
            foreign = True
    if foreign and not kept:
        return None
    return kept or (["Traditional"] if dated else [])


def parse(name, entry):
    """Cached entry -> pronunciation rows for a town called `name`."""
    if not entry or not entry.get("isles"):
        return []
    rows = []
    for lang, lines in entry.get("lines", {}).items():
        for line in lines:
            found = templates(line)
            # labels written once for the line (e.g. on {{enPR|…|a=US}}) apply to its IPA too
            line_labels = next((_named(a)[1].get("a", "") for _, _, n, a in found if _named(a)[1].get("a")), "")
            for _, _, tname, args in found:
                pos, named = _named(args)
                labels = _labels(named, line_labels)
                if labels is None or len(pos) < 2:
                    continue
                variety = labels[0] if labels else variety_of(lang)
                if lang != "en" and not labels:
                    variety = variety_of(lang)
                if tname == "ipa":
                    ipas = [p.strip("/") for p in pos[1:] if p.startswith("/")][:2]
                    if ipas:
                        rows.append({"name": name, "lang": lang, "variety": variety, "ipa": ", ".join(ipas),
                                     "respell": "", "audio": "", "_labels": labels})
                elif tname == "audio":
                    same = next((r for r in reversed(rows) if r["lang"] == lang and not r["audio"]
                                 and (not labels or variety in r.get("_labels", []))), None)
                    if same:
                        same["audio"] = pos[1]
                    else:
                        rows.append({"name": name, "lang": lang, "variety": variety, "ipa": "",
                                     "respell": "", "audio": pos[1]})
    british = any(r["ipa"] and r["variety"] != "English" for r in rows)
    return [{k: v for k, v in r.items() if k != "_labels"} for r in rows
            if not (british and r["lang"] == "en" and r["variety"] == "English" and US_SOUNDS.search(r["ipa"]))]
