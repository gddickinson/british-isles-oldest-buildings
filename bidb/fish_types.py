"""Building types BT1a: the FISH Thesaurus of Monument Types (Historic England, Open Government Licence v3.0;
the licence is stated in the scheme's own RDF at heritagedata.org), read from the yearly CSV release.

A polyhierarchy: one concept may sit under several broader concepts, under its function (DOMESTIC > DWELLING >
HOUSE > HALL HOUSE > WEALDEN HOUSE) and under its form (MONUMENT <BY FORM> > TIMBER FRAMED BUILDING > ... >
WEALDEN HOUSE). Each concept has a scope note (its definition), non-preferred terms ("Half Wealden House") and
related terms. Ids are the thesaurus's own (Wikidata P14369 uses the same numbers).

    python -m bidb.fish_types [--report]     counts, and how many catalogue classes find a concept
"""
import csv
import io
import re
import sys
import zipfile
from collections import Counter
from functools import lru_cache

URL = "https://heritage-standards.org.uk/2026/zip_files/MonumentTypeV29.zip"
VERSION = "29 (24 April 2026)"
CONCEPT_URI = "http://purl.org/heritagedata/schemes/eh_tmt2/concepts/{}"
ATTRIBUTION = ("FISH Thesaurus of Monument Types, version 29, Historic England, "
               "Open Government Licence v3.0")
BY_FORM = "MONUMENT <BY FORM>"


def _rows(z, name):
    return list(csv.DictReader(io.StringIO(z.read(name).decode("utf-8", errors="replace"))))


@lru_cache(maxsize=1)
def concepts():
    """{id: {id, term, note, alt: [non-preferred terms], broader: [ids], narrower: [ids], related: [ids]}}.
    The CSVs place each term once per broader term ("uses", by label) and give related terms between uses."""
    from .change_registers import _download
    with zipfile.ZipFile(_download(URL, URL.rsplit("/", 1)[1], print, folder="fish")) as z:
        terms, prefs = _rows(z, "ThesaurusTerms.csv"), _rows(z, "ThesaurusTermPreferences.csv")
        uses, rels = _rows(z, "ThesaurusTermUses.csv"), _rows(z, "ThesaurusTermRelations.csv")
    out, by_term = {}, {}
    for t in terms:
        if t["STATUS"] == "P":
            note = t["SCOPE_NOTE"] if t["SCOPE_NOTE"] not in ("", "-") else ""
            out[t["THE_TE_UID"]] = {"id": t["THE_TE_UID"], "term": t["TERM"], "note": note, "alt": [],
                                    "broader": [], "narrower": [], "related": []}
            by_term[t["TERM"]] = t["THE_TE_UID"]
    names = {t["THE_TE_UID"]: t["TERM"] for t in terms}
    for p in prefs:
        if p["THE_TE_UID_2"] in out and p["THE_TE_UID_1"] in names:
            out[p["THE_TE_UID_2"]]["alt"].append(names[p["THE_TE_UID_1"]])
    use_term = {u["TH_T_U_UID"]: by_term[u["TERM"]] for u in uses if u["TERM"] in by_term}
    for u in uses:
        child, parent = use_term.get(u["TH_T_U_UID"]), use_term.get(u["BROAD_TERM_U_UID"])
        if child and parent and parent not in out[child]["broader"]:
            out[child]["broader"].append(parent)
            out[parent]["narrower"].append(child)
    for r in rels:
        a, b = use_term.get(r["TH_T_U_UID_1"]), use_term.get(r["TH_T_U_UID_2"])
        if a and b and a != b:
            for x, y in ((a, b), (b, a)):
                if y not in out[x]["related"]:
                    out[x]["related"].append(y)
    return out


def label(cid):
    """Display form of a concept's term: sentence case ("Wealden house")."""
    term = concepts()[cid]["term"]
    return term[:1] + term[1:].lower()


def uri(cid):
    return CONCEPT_URI.format(cid)


def tops():
    """Top concepts (the function classes and MONUMENT <BY FORM>)."""
    return [c for c, v in concepts().items() if not v["broader"] and v["narrower"]]


def paths(cid):
    """Every path from a top concept down to the concept, as lists of ids."""
    c = concepts()[cid]
    if not c["broader"]:
        return [[cid]]
    return [p + [cid] for b in c["broader"] for p in paths(b)]


def descendants(cid):
    """The concept and every concept below it."""
    seen, todo = set(), [cid]
    while todo:
        c = todo.pop()
        if c not in seen:
            seen.add(c)
            todo += concepts()[c]["narrower"]
    return seen


def normalise(text):
    """Key for matching labels: lower case, '&' as 'and', hyphens and slashes as spaces, single spaces."""
    t = text.lower().replace("&", " and ")
    return re.sub(r"\s+", " ", re.sub(r"[-/_,()]", " ", t)).strip()


@lru_cache(maxsize=1)
def _index():
    idx = {}
    for cid, c in concepts().items():
        idx.setdefault(normalise(c["term"]), cid)
    for cid, c in concepts().items():                # non-preferred terms never displace a preferred one
        for a in c["alt"]:
            idx.setdefault(normalise(a), cid)
    return idx


def lookup(text):
    """Concept id for a label (preferred or non-preferred term; also without a trailing 's' or ' building'),
    or None."""
    idx, key = _index(), normalise(text)
    for k in (key, key.removesuffix(" building"), key.removesuffix("s"), key.removesuffix("es")):
        if k in idx:
            return idx[k]
    return None


def coverage(conn):
    """(matched class uses, all class uses, Counter of unmatched class labels) over the catalogue's
    Wikidata classes (buildings.classes, ';'-separated)."""
    uses, missing = Counter(), Counter()
    for (classes,) in conn.execute("SELECT classes FROM buildings"):
        for x in filter(None, (s.strip() for s in (classes or "").split(";"))):
            uses[x] += 1
    for x, n in uses.items():
        if not lookup(x):
            missing[x] = n
    total = sum(uses.values())
    return total - sum(missing.values()), total, missing


def report(conn=None):
    c = concepts()
    lines = [f"FISH Thesaurus of Monument Types {VERSION}: {len(c)} preferred terms, "
             f"{sum(len(v['alt']) for v in c.values())} non-preferred, "
             f"{sum(len(v['broader']) > 1 for v in c.values())} under more than one broader term"]
    for t in sorted(tops(), key=lambda t: c[t]["term"]):
        lines.append(f"  {c[t]['term']}: {len(descendants(t)) - 1} below")
    if conn is not None:
        hit, total, missing = coverage(conn)
        lines.append(f"catalogue class uses with a FISH concept: {hit} of {total} ({100 * hit / total:.1f}%)")
        lines.append("most used without one: " + ", ".join(f"{k} ({n})" for k, n in missing.most_common(25)))
    return lines


def main():
    conn = None
    if "--report" in sys.argv:
        import sqlite3
        from .config import db_path
        conn = sqlite3.connect(db_path())
    print("\n".join(report(conn)))


if __name__ == "__main__":
    main()
