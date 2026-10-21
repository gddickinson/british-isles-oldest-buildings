"""Construction dates from official register descriptions (Scotland: HES portal; Wales: Cadw).

Listed-building descriptions usually open with the date and architect ("William Leiper, 1871;
addition ... 1902", "Late C17th/early C18th origins."), so the first clause is read on its own;
otherwise a construction sentence anywhere in the description is used ("a hillfort dating
probably to the Iron Age"). England's register has no machine-readable dates.
"""
import html
import re

from .date_mining import candidates, date_from_text
from .http import cached, request_json

HES_PAGE = "https://portal.historicenvironment.scot/designation/{}"
CADW_PAGE = "https://cadwpublic-api.azurewebsites.net/reports/listedbuilding/FullReport?lang=en&id={}"
HES_END = ("Statement of Special Interest", "Statement of National Importance", "References")
CADW_SECTIONS = ("Period", "History", "Exterior", "Interior")
CADW_END = ("Reason for designation", "Sources")
EARLIER = re.compile(r"\b(site of|replac|predecessor|formerly|earlier)", re.I)


def _lines(page):
    page = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", page, flags=re.S | re.I)
    page = re.sub(r"</?(sup|sub|em|i|b|strong|span|a)\b[^>]*>", "", page, flags=re.I)   # inline: "18<sup>th</sup>"
    text = html.unescape(re.sub(r"<[^>]+>", "\n", page))
    return [re.sub(r"\s+", " ", ln).strip() for ln in text.split("\n") if ln.strip()]


def _hes_text(page):
    lines = _lines(page)
    starts = [i for i, ln in enumerate(lines) if ln == "Description"]
    if not starts:
        return ""
    out = []
    for ln in lines[starts[-1] + 1:]:
        if ln in HES_END:
            break
        out.append(ln)
    return "\n".join(out)[:6000]


def _cadw_text(page):
    lines = _lines(page)
    out, keep = [], False
    for ln in lines:
        if ln in CADW_END:
            break
        if ln in CADW_SECTIONS:
            keep = ln in ("Period", "History")      # the date is stated there, not in Exterior
            continue
        if keep:
            out.append(ln)
    return "\n".join(out)[:6000]


def description(rec):
    """-> (register name, url, text) for a record with an HES or Cadw id, else None."""
    if rec.get("hes_id"):
        url = HES_PAGE.format(rec["hes_id"])
        return "HES", url, request_json(url, extract=_hes_text, min_interval=1.0)
    if rec.get("cadw_id"):
        url = CADW_PAGE.format(rec["cadw_id"])
        return "Cadw", url, request_json(url, extract=_cadw_text, min_interval=1.0)
    return None


def cached_description(rec):
    """Like description(), from the download cache only (None when the page was never fetched)."""
    for reg, key, page in (("HES", "hes_id", HES_PAGE), ("Cadw", "cadw_id", CADW_PAGE)):
        if rec.get(key):
            url = page.format(rec[key])
            text = cached(url)
            return (reg, url, text) if text else None
    return None


def normalise(text):
    """Register shorthand -> plain English: 'earlyC18th' -> 'early 18th century', '17th/18th' -> '17th or 18th'."""
    text = re.sub(r"\b(early|mid|late|later)?\s*-?C(\d{1,2})(?:st|nd|rd|th)?\b",
                  lambda m: f"{(m.group(1) or '').replace('later', 'late')} {m.group(2)}th century".strip(),
                  text, flags=re.I)
    text = re.sub(r"\b(Later|Earlier)(?=\s+\d)", lambda m: {"Later": "late", "Earlier": "early"}[m.group(1)], text)
    text = re.sub(r"(\d{1,2}(?:st|nd|rd|th))\s*/\s*(?=\d{1,2}(?:st|nd|rd|th))", r"\1 or ", text)
    text = re.sub(r"\bcentury century\b", "century", text)
    text = re.sub(r"\b(?:some |about |over )?\d[\d,]* years (?:old|ago)\b", "", text)   # ages, not dates
    return re.sub(r"\b(\d{1,2})th century(?= century)", r"\1th", text)


def date_from_register(text):
    """(year, label, evidence, kind) from a register description, or None.

    kind 'lead': the first date in the opening clause (listing style: "John Thin, 1796");
    kind 'text': a construction sentence elsewhere (weaker; scheduled-monument style)."""
    text = normalise(text or "")
    first = re.split(r"[.;\n]", text.strip(), maxsplit=1)[0]
    if len(first) <= 300 and not EARLIER.search(first):
        hits = [h for h in candidates(first) if -4000 < h[0] < 2030]
        if hits:
            year, label = min(hits, key=lambda h: first.find(h[1]))
            return year, label, first, "lead"
    hit = date_from_text(text, max_sentences=12)
    return (*hit, "text") if hit else None


def register_dates(records, log=print):
    """{record id: (year, label, evidence, kind, register name)} for records with an HES/Cadw id."""
    out, todo = {}, [r for r in records if r.get("hes_id") or r.get("cadw_id")]
    for i, r in enumerate(todo, 1):
        try:
            name, url, text = description(r)
        except Exception as exc:          # one unreachable page should not stop the build
            log(f"  register page failed for {r['id']}: {exc}")
            continue
        hit = date_from_register(text)
        if hit:
            out[r["id"]] = (*hit, name)
        if i % 500 == 0:
            log(f"  register descriptions: {i}/{len(todo)}, {len(out)} dated")
    return out


if __name__ == "__main__":
    import sys
    from .db import connect
    conn = connect()
    rows = [dict(r) for r in conn.execute(
        "SELECT id, hes_id, cadw_id FROM buildings WHERE (hes_id IS NOT NULL OR cadw_id IS NOT NULL) "
        "AND COALESCE(date_confidence, '') != 'Recorded'")]
    limit = int(sys.argv[1]) if len(sys.argv) > 1 else None
    found = register_dates(rows[:limit])
    print(f"{len(found)} of {len(rows[:limit])} dated")
