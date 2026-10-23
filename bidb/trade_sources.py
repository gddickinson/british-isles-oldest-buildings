"""Trade, enterprise and innovation (roadmap C1): the researched sources for items C2–C8.

Curated input `data/curated/trade/sources.json`:
    {id: {short, publisher, citation, licence, licence_url, licence_quote, url, download_url, checked, years,
          regions, resolution, format, size, records, for: ["C2".."C8"], use, verdict, reason}}
    verdict: use (open licence) / quote figures (published figures cited with page and quote) / link only /
             ask (licence unclear or needs permission: `reason` says whom) / left out (`reason` says why)

    python -m bidb.trade_sources            check the file and print the sources per item and verdict
"""
import json
import sys
from collections import Counter

from .config import ROOT

PATH = ROOT / "data" / "curated" / "trade" / "sources.json"
VERDICTS = ("use", "quote figures", "link only", "ask", "left out")
ITEMS = ("C2", "C3", "C4", "C5", "C6", "C7", "C8")
REQUIRED = ("short", "publisher", "citation", "licence", "url", "checked", "use", "verdict")


def load(path=PATH):
    return json.loads(path.read_text())


def check(sources):
    """Problems: missing fields, unknown verdicts or items, an open-licence source without its licence quote,
    a source we cannot use without the reason."""
    bad = []
    for sid, s in sources.items():
        bad += [f"{sid}: no {k}" for k in REQUIRED if not s.get(k)]
        if s.get("verdict") not in VERDICTS:
            bad.append(f"{sid}: verdict {s.get('verdict')!r}")
        if not s.get("for") or any(x not in ITEMS for x in s["for"]):
            bad.append(f"{sid}: items {s.get('for')!r}")
        if s.get("verdict") == "use" and not s.get("licence_quote"):
            bad.append(f"{sid}: open licence without a quote")
        if s.get("verdict") in ("ask", "left out") and not s.get("reason"):
            bad.append(f"{sid}: {s['verdict']} without a reason")
    return bad


def summary(sources):
    """Lines: count per verdict, then per item the usable sources."""
    lines = [", ".join(f"{v}: {n}" for v, n in Counter(s["verdict"] for s in sources.values()).most_common())]
    for item in ITEMS:
        ids = [k for k, s in sources.items() if item in s["for"] and s["verdict"] in ("use", "quote figures")]
        lines.append(f"{item}: {len(ids)} usable — {', '.join(ids)}")
    return lines


def main():
    sources = load()
    bad = check(sources)
    print("\n".join(bad or summary(sources)))
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
