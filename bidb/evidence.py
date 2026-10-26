"""Research track: researched claims and their evidence (`data/curated/evidence.json`).

    python -m bidb.evidence            list the claims and their last check
    python -m bidb.evidence --check    fetch every source again and look for its quote
    python -m bidb.evidence --check --new   only the claims the last check has not seen
    python -m bidb.evidence <id>       the claims about one record

A claim is about one record (a building or place) and one field (a date, a builder, a fact). Each
of its sources says what kind of source it is, where in it the evidence is, and an exact short
quote. The check fetches the source (Wikipedia through the API, other pages as plain text) and
looks for the quote with spacing, case, quote marks and dashes made uniform; results go to
`data/evidence_check.json` (quote-found / quote-missing / unreachable). The app shows claims,
sources, quotes and check results in detail views ("Evidence").
"""
import json
import re
import sys
import time

from .config import DATA_DIR

FILE = DATA_DIR / "curated" / "evidence.json"
CHECK = DATA_DIR / "evidence_check.json"
KINDS = ("primary", "listing", "secondary", "reference")
VERDICTS = ("kept", "corrected", "open")
SLOW_HOSTS = {"apps.communities-ni.gov.uk": 4.0}      # answers with an empty page when asked quickly


def load():
    """The researched claims, and those of the researched "oldest" lists (bidb.oldest_lists)."""
    from .oldest_lists import claims
    return json.loads(FILE.read_text())["claims"] + claims()


def checks():
    return json.loads(CHECK.read_text()) if CHECK.exists() else {}


def normalise(text):
    """Lower case, one kind of quote mark and dash, single spaces, no space before punctuation."""
    t = (text or "").lower()
    t = re.sub(r"[‘’ʼ`]", "'", t)
    t = re.sub(r"[“”]", '"', t)
    t = re.sub(r"[‐-―−]", "-", t)
    t = re.sub(r"\s+", " ", t)
    return re.sub(r"\s+([,.;:)])", r"\1", t).strip()


def quote_found(quote, text):
    return normalise(quote) in normalise(text)


def validate(claims):
    """Problems in the file itself (missing fields, unknown kinds or verdicts, duplicate ids)."""
    problems, seen = [], set()
    for c in claims:
        for k in ("id", "record", "field", "claim", "verdict", "sources"):
            if not c.get(k):
                problems.append(f"{c.get('id')}: no {k}")
        if c.get("id") in seen:
            problems.append(f"{c['id']}: duplicate id")
        seen.add(c.get("id"))
        if c.get("verdict") not in VERDICTS:
            problems.append(f"{c.get('id')}: verdict {c.get('verdict')!r}")
        for s in c.get("sources", []):
            if s.get("kind") not in KINDS:
                problems.append(f"{c.get('id')}: source kind {s.get('kind')!r}")
            if not s.get("quote") or not s.get("title"):
                problems.append(f"{c.get('id')}: source without title or quote")
    return problems


def _dataset_text(url):
    """Text of a downloaded dataset cited by its DOI (its landing page does not hold the quoted notes), or None."""
    if url not in DATASETS:
        return None
    return DATASETS[url]()


def _vag_text():
    from . import dendro
    return "\n".join(f"{e['location']} {e['date_text']} {e['notes']}" for e in dendro.entries())


DATASETS = {"https://doi.org/10.5284/1132568": _vag_text}     # VAG Dendrochronology Database (bidb.dendro)


def check(log=print, only_new=False, claims=None, path=CHECK):
    """Fetch every source again and record whether its quote is there (only_new: just the claims the last
    check has not seen, kept with its results). `claims` and `path` let other curated files (building types)
    use the same check."""
    from .verify_research import source_text
    prev = json.loads(path.read_text()) if only_new and path.exists() else {}
    claims, out, texts = load() if claims is None else claims, prev, {}
    for c in claims:
        if c["id"] in out:
            continue
        res = []
        for s in c["sources"]:
            url = s.get("url")
            if not url:                               # a print or paywalled source: nothing to fetch
                res.append("no-link")
                continue
            if url not in texts:
                texts[url] = _dataset_text(url) or source_text(url)
                time.sleep(0 if url in DATASETS else SLOW_HOSTS.get(url.split("/")[2], 0.5))
            text = texts.get(url)
            res.append("unreachable" if text is None else "quote-found" if quote_found(s["quote"], text) else "quote-missing")
        out[c["id"]] = {"sources": res, "checked": time.strftime("%Y-%m-%d")}
        log(f"  {c['id']}: {', '.join(res)}")
    path.write_text(json.dumps(out, indent=1) + "\n")
    log(f"{sum(r == 'quote-found' for v in out.values() for r in v['sources'])} of "
        f"{sum(len(v['sources']) for v in out.values())} quotes found in their sources")
    return out


def for_record(rid):
    """The claims about one record, each source with its last check result."""
    ck = checks()
    out = []
    for c in load():
        if c["record"] == rid:
            res = ck.get(c["id"], {}).get("sources", [])
            out.append({**c, "sources": [{**s, "check": res[i] if i < len(res) else None}
                                         for i, s in enumerate(c["sources"])]})
    return out


def export():
    """{record id: [claims with check results]} for the hosted copy."""
    out = {}
    for c in load():
        out.setdefault(c["record"], [])
    return {rid: for_record(rid) for rid in out}


def main():
    args = sys.argv[1:]
    problems = validate(load())
    for p in problems:
        print("problem:", p)
    if args and args[0] == "--check":
        check(only_new="--new" in args)
    elif args:
        print(json.dumps(for_record(args[0]), indent=1, ensure_ascii=False))
    else:
        ck = checks()
        for c in load():
            print(f"{c['id']:30} {c['verdict']:9} {c['name']}: {', '.join(ck.get(c['id'], {}).get('sources', ['unchecked']))}")
    if problems:
        sys.exit(1)


if __name__ == "__main__":
    main()
