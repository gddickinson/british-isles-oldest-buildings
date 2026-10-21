"""Check the researched files against their own sources: python -m bidb.verify_research

For every history event and every "oldest of its type" example, the cited source is fetched
(Wikipedia via the API, other sites as HTML) and searched for the stated year and the subject's
name. The sentence that contains the year is kept as evidence. Results go to
data/verification.json and are shown on the History, Oldest-by-type and Data quality pages.

Statuses:
  confirmed      the year (and, for examples, the name) appear in the cited source
  year-missing   the source was read but does not mention the stated year
  unreachable    the source could not be fetched
"""
import html
import json
import re
from urllib.parse import unquote

import requests

from .config import DATA_DIR, USER_AGENT, WIKIPEDIA_API
from .http import request_json

OUT = DATA_DIR / "verification.json"
_session = requests.Session()
_session.headers["User-Agent"] = USER_AGENT


def _wiki_title(url):
    m = re.search(r"en\.wikipedia\.org/wiki/([^#?]+)", url or "")
    return unquote(m.group(1)).replace("_", " ") if m else None


def source_text(url):
    """Plain text of a source page, or None."""
    title = _wiki_title(url)
    try:
        if title:
            res = request_json(WIKIPEDIA_API, params={
                "action": "query", "titles": title, "prop": "extracts", "explaintext": 1,
                "redirects": 1, "format": "json", "formatversion": 2}, min_interval=0.3)
            pages = res.get("query", {}).get("pages", [])
            return (pages[0].get("extract") or None) if pages else None
        r = _session.get(url, timeout=30)
        if r.status_code != 200:
            return None
        text = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", r.text, flags=re.S | re.I)
        return html.unescape(re.sub(r"<[^>]+>", " ", text))
    except (requests.RequestException, ValueError, RuntimeError):
        return None


def year_patterns(year):
    """Ways a year can be written: 1189, 3100 BC, 'twelfth century' is not attempted."""
    a = abs(int(year))
    if year < 0:
        return [rf"\b{a:,}\s*(?:BC|BCE)\b".replace(",", ",?"), rf"\b{a}\s*(?:BC|BCE)\b", rf"\b{a}\b"]
    return [rf"(?<![\d,]){a}(?!\d)"]


def check(text, year, name=None):
    if text is None:
        return {"status": "unreachable"}
    flat = re.sub(r"\s+", " ", text)
    for pat in year_patterns(year):
        m = re.search(pat, flat)
        if m:
            start = flat.rfind(". ", 0, m.start()) + 2
            end = flat.find(". ", m.end())
            sentence = flat[max(0, start):end + 1 if end > 0 else m.end() + 200][:400]
            name_ok = True
            if name:
                words = [w for w in re.findall(r"[A-Za-z]{4,}", name) if w.lower() not in ("olde", "inn", "the")]
                name_ok = not words or any(w.lower() in flat.lower() for w in words)
            return {"status": "confirmed" if name_ok else "name-missing", "evidence": sentence}
    return {"status": "year-missing"}


def run():
    hist = json.loads((DATA_DIR / "curated" / "history.json").read_text())
    types = json.loads((DATA_DIR / "curated" / "oldest_by_type.json").read_text())["types"]
    cache, out = {}, {"events": {}, "examples": {}}
    text = lambda url: cache.setdefault(url, source_text(url)) if url else None
    for e in hist["events"]:
        out["events"][e["title"]] = {"source": e.get("source"), **check(text(e.get("source")), e["year"])}
    for t in types:
        for ex in t["examples"]:
            if ex.get("year") is None:
                continue
            key = f"{t['type']}|{ex['name']}"
            out["examples"][key] = {"source": ex.get("source"),
                                    **check(text(ex.get("source")), ex["year"], ex["name"])}
    summary = {}
    for group in out.values():
        for v in group.values():
            summary[v["status"]] = summary.get(v["status"], 0) + 1
    out["summary"] = summary
    OUT.write_text(json.dumps(out, indent=1, ensure_ascii=False))
    print(f"verification: {summary}")
    return out


if __name__ == "__main__":
    run()
