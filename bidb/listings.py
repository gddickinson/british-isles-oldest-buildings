"""Official list descriptions of catalogue records, for citing as evidence (research track R3/R5).

    python -m bidb.listings <record id>   the record's list description and its dated sentences
    python -m bidb.listings --oldest      the same for every oldest-of-type example -> runs/listing_review.json

England: Historic England's list pages cannot be read by a script (bot check), so the list description
is read from its reproduction on British Listed Buildings (https://britishlistedbuildings.co.uk/10<list
entry number>), which keeps the official text word for word. Scotland and Wales: the HES portal and
Cadw's full report (bidb.register_dates). Results are cached like every download.
"""
import html
import json
import re
import sys

from .config import ROOT
from .date_mining import candidates
from .http import request_json
from .register_dates import description as register_description, normalise

BLB_PAGE = "https://britishlistedbuildings.co.uk/10{}"
REVIEW = ROOT / "runs" / "listing_review.json"
# list-entry headers and amendment notes: grid references, file numbers, listing dates
_HEADER = re.compile(r"\b\d+-?\d*/\d+/\d+|list entry was subject|\b[A-Z]{2}\s?\d{4}\s?[NS][EW]\b|\bGV\b", re.I)


def _blb_text(page):
    """The list description on a British Listed Buildings page (from "Summary" or "Description" to the end of the entry)."""
    text = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", page, flags=re.S | re.I)
    text = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", text))
    text = html.unescape(text)
    start = next((i for i in (text.find(" Summary "), text.find(" Description ")) if i >= 0), -1)
    ends = [i for i in (text.find(k, start) for k in ("Listing NGR", "External Links", "Recommended Books")) if i > start]
    return text[start:min(ends)].strip()[:12000] if start >= 0 and ends else ""


def _forget(url):
    from .http import _cache_path
    _cache_path(json.dumps(["GET", url, None, None, None], sort_keys=True)).unlink(missing_ok=True)


def listing(rec):
    """-> (register, url, text) for a record with a list entry, else None."""
    if rec.get("nhle_id"):
        url = BLB_PAGE.format(rec["nhle_id"])
        text = request_json(url, extract=_blb_text, min_interval=1.0)
        if not text:                              # cached before the newer list-entry layout was read
            _forget(url)
            text = request_json(url, extract=_blb_text, min_interval=1.0)
        return "Historic England (reproduced by British Listed Buildings)", url, text
    return register_description(rec)


def dated_sentences(text, limit=6):
    """Sentences of a description that give a date, as written (not normalised)."""
    out = []
    for s in re.split(r"(?<=[.;])\s+(?=[A-Z0-9])", text or ""):
        if _HEADER.search(s):
            continue
        if any(-4000 < y < 2030 for y, _ in candidates(normalise(s))):
            out.append(s.strip()[:300])
            if len(out) >= limit:
                break
    return out


def review(rows, log=print):
    out = []
    for r in rows:
        got = None
        try:
            got = listing(r)
        except Exception as exc:                  # one unreachable page should not stop the list
            log(f"  {r['id']}: {exc}")
        if not got or not got[2]:
            continue
        out.append({"id": r["id"], "name": r["name"], "type": r.get("oldest_of_type"), "date_text": r.get("date_text"),
                    "year": r.get("year_start"), "register": got[0], "url": got[1], "dated": dated_sentences(got[2])})
        log(f"  {r['name']}: {len(out[-1]['dated'])} dated sentences")
    return out


def main():
    from .db import connect
    conn = connect()
    cols = "id, name, oldest_of_type, date_text, year_start, nhle_id, hes_id, cadw_id"
    if sys.argv[1:] == ["--oldest"]:
        rows = [dict(r) for r in conn.execute(f"SELECT {cols} FROM buildings WHERE oldest_of_type IS NOT NULL "
                                              "AND (nhle_id IS NOT NULL OR hes_id IS NOT NULL OR cadw_id IS NOT NULL)")]
        out = review(rows)
        REVIEW.write_text(json.dumps(out, indent=1, ensure_ascii=False))
        print(f"{len(out)} of {len(rows)} oldest-of-type examples with a list description -> {REVIEW}")
    elif sys.argv[1:]:
        r = conn.execute(f"SELECT {cols} FROM buildings WHERE id = ?", (sys.argv[1],)).fetchone()
        got = listing(dict(r)) if r else None
        print(json.dumps({"register": got[0], "url": got[1], "text": got[2], "dated": dated_sentences(got[2])}
                         if got else None, indent=1, ensure_ascii=False))
    else:
        print(__doc__)


if __name__ == "__main__":
    main()
