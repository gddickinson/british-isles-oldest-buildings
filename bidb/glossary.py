"""Glossary page: terms used in the catalogue, from `data/curated/glossary.json`, the periods of bidb.classify and
the building types of bidb.building_types.

A curated term has its own `text`, or a `fish` id whose FISH scope note (Historic England, OGL v3.0) is its
definition; the thesaurus's indexing advice ("Use more specific type where known.") is left out. Building types
take their FISH scope note, else their own note. Without the cached thesaurus the FISH terms are left out.

    python -m bidb.glossary        check the file (unknown `see` terms, duplicates) and print the counts
"""
import json
import re
import sys
from collections import Counter

from .classify import PERIODS
from .config import DATA_DIR

PATH = DATA_DIR / "curated" / "glossary.json"
FISH = {"title": "FISH Thesaurus of Monument Types (Historic England, OGL v3.0)",
        "url": "https://www.heritagedata.org/live/schemes/eh_tmt2/concepts/{}.html"}
# the advice's own sentences only: "house with" is no "Use with" (case and word boundary matter)
ADVICE = re.compile(r"\s*\b(Use (?:with |only |more |wider |specific |the )[^.]*\.|Index (?:with|under) [^.]*\.)")


def load():
    return json.loads(PATH.read_text())


def _fish():
    try:
        from . import fish_types
        return fish_types.concepts()
    except (OSError, KeyError, ValueError):
        return {}


def scope_note(concept):
    """A FISH scope note without the thesaurus's indexing advice."""
    return ADVICE.sub("", concept.get("note") or "").strip()


def _year(y):
    return f"{-y} BC" if y < 0 else f"AD {y}" if y < 1000 else str(y)


def periods():
    """The catalogue's periods as terms, with their years."""
    out = []
    for label, start, end in PERIODS:
        span = f"from {_year(start)}" if end >= 3000 else f"{_year(start)} to {_year(end)}"
        out.append({"term": label, "group": "Periods",
                    "text": f"The catalogue's period for records begun {span}."
                            + (" In Ireland and the Isle of Man these years are shown as Iron Age."
                               if label == "Roman Britain" else ""),
                    "see": ["Regional period"] if label == "Roman Britain" else []})
    return out


def building_types(fish):
    """Building types of the family tree (not those abroad) with a definition."""
    from . import building_types as bt
    out = []
    for t in bt.load()["types"]:
        if t.get("abroad"):
            continue
        text, source = "", None
        if t.get("fish") and t["fish"] in fish:
            text = scope_note(fish[t["fish"]])
            source = {"title": FISH["title"], "url": FISH["url"].format(t["fish"])}
        if not text and t.get("note"):
            text = t["note"]
        if text:
            out.append({"term": t["name"], "group": "Building types", "text": text, "source": source,
                        "family": f"{t['domain']}: {t['family']}"})
    return out


def entries():
    """Every term: {term, group, text, see, link?, source?, family?}, sorted by term within the page."""
    fish, data = _fish(), load()
    out = []
    for t in data["terms"]:
        e = {k: v for k, v in t.items() if k != "fish"}
        if t.get("fish"):
            if t["fish"] not in fish:
                continue
            e["text"] = scope_note(fish[t["fish"]])
            e["source"] = {"title": FISH["title"], "url": FISH["url"].format(t["fish"])}
        out.append(e)
    have = {e["term"].lower() for e in out}
    out += [e for e in periods() + building_types(fish) if e["term"].lower() not in have]
    for e in out:
        e.setdefault("see", [])
    return {"groups": data["groups"], "terms": sorted(out, key=lambda e: e["term"].lower())}


def problems(data=None, terms=None):
    """Curated terms without a definition, in an unknown group, duplicated, or pointing to unknown terms."""
    data = data or load()
    terms = terms if terms is not None else entries()["terms"]
    names = {e["term"] for e in terms}
    bad = [f"{t['term']}: no text or fish" for t in data["terms"] if not (t.get("text") or t.get("fish"))]
    bad += [f"{t['term']}: group {t['group']!r}" for t in data["terms"] if t["group"] not in data["groups"]]
    bad += [f"{n}: duplicate" for n, k in Counter(t["term"].lower() for t in data["terms"]).items() if k > 1]
    bad += [f"{e['term']}: see {s!r} unknown" for e in terms for s in e.get("see", []) if s not in names]
    return bad


def main():
    out = entries()
    bad = problems(terms=out["terms"])
    print("\n".join(bad) or f"{len(out['terms'])} terms: " + ", ".join(
        f"{g} {n}" for g, n in Counter(e["group"] for e in out["terms"]).most_common()))
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
