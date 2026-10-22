"""Research track: researched claims and their evidence (`data/curated/evidence.json`).

    python -m bidb.evidence            list the claims and their last check
    python -m bidb.evidence --check    fetch every source again and look for its quote
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


def load():
    return json.loads(FILE.read_text())["claims"]


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


def check(log=print):
    """Fetch every source again and record whether its quote is there."""
    from .verify_research import source_text
    claims, out, texts = load(), {}, {}
    for c in claims:
        res = []
        for s in c["sources"]:
            url = s.get("url")
            if url and url not in texts:
                texts[url] = source_text(url)
                time.sleep(0.5)
            text = texts.get(url)
            res.append("unreachable" if text is None else "quote-found" if quote_found(s["quote"], text) else "quote-missing")
        out[c["id"]] = {"sources": res, "checked": time.strftime("%Y-%m-%d")}
        log(f"  {c['id']}: {', '.join(res)}")
    CHECK.write_text(json.dumps(out, indent=1) + "\n")
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
        check()
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
