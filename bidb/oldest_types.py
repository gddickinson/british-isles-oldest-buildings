"""'Oldest of each type': the earliest dated examples of each building type, at any date.

Two sources: a Wikidata query per type (TYPES) and the researched claims in
data/curated/oldest_by_type.json (written from web research; claims and evidence kept).
"""
import json

from .config import COUNTRIES, DATA_DIR
from .http import sparql

RESEARCH_PATH = DATA_DIR / "curated" / "oldest_by_type.json"

# (type label, category, Wikidata class QID) - QIDs verified against Wikidata labels
TYPES = [
    ("Pub", "Public house / inn", "Q212198"), ("Inn", "Public house / inn", "Q256020"),
    ("Coaching inn", "Public house / inn", "Q966002"), ("Hotel", "Hotel", "Q27686"),
    ("Theatre", "Theatre / entertainment", "Q24354"),
    ("Cinema", "Theatre / entertainment", "Q41253"),
    ("Concert hall", "Theatre / entertainment", "Q1060829"),
    ("Railway station", "Railway", "Q55488"), ("Lighthouse", "Lighthouse", "Q39715"),
    ("Windmill", "Mill", "Q38720"), ("Watermill", "Mill", "Q185187"),
    ("Tide mill", "Mill", "Q493694"), ("Almshouse", "Almshouse / hospital", "Q15548045"),
    ("Hospital", "Almshouse / hospital", "Q39364723"),
    ("School", "School / college", "Q1244442"),
    ("University building", "School / college", "Q19844914"),
    ("Library", "Library", "Q856584"), ("Prison", "Prison", "Q40357"),
    ("Bank", "Bank / office", "Q18761864"), ("Office building", "Bank / office", "Q1021645"),
    ("Post office", "Post office", "Q35054"), ("Market hall", "Market / shop", "Q2080521"),
    ("Market cross", "Market / shop", "Q427926"), ("Shop", "Market / shop", "Q213441"),
    ("Town hall", "Civic building", "Q25550691"), ("Courthouse", "Civic building", "Q1137809"),
    ("Barn", "Agricultural / industrial", "Q1303167"),
    ("Tithe barn", "Agricultural / industrial", "Q184698"),
    ("Dovecote", "Agricultural / industrial", "Q948878"),
    ("Brewery", "Agricultural / industrial", "Q131734"),
    ("Distillery", "Agricultural / industrial", "Q1251750"),
    ("Factory", "Agricultural / industrial", "Q83405"),
    ("Warehouse", "Agricultural / industrial", "Q181623"),
    ("Greenhouse", "Agricultural / industrial", "Q165044"),
    ("Bridge", "Bridge / infrastructure", "Q12280"), ("Viaduct", "Bridge / infrastructure", "Q181348"),
    ("Aqueduct", "Bridge / infrastructure", "Q474"), ("Canal", "Bridge / infrastructure", "Q12284"),
    ("Pier", "Bridge / infrastructure", "Q863454"),
    ("Observatory", "Observatory / science", "Q62832"),
    ("Synagogue", "Synagogue / mosque / meeting house", "Q34627"),
    ("Mosque", "Synagogue / mosque / meeting house", "Q32815"),
    ("Museum building", "Museum", "Q24699794"), ("House", "House / domestic", "Q3947"),
    ("Cottage", "House / domestic", "Q5783996"), ("Tenement", "House / domestic", "Q1078374"),
    ("Tower house", "Castle / fortification", "Q1535658"),
]
TYPE_CATEGORY = {label: cat for label, cat, _ in TYPES}
_COUNTRY_VALUES = " ".join(f"wd:{q}" for q in COUNTRIES)


def _query(qid, per, transitive):
    path = "wdt:P31/wdt:P279*" if transitive else "wdt:P31"
    return sparql(f"""
        SELECT ?item (MIN(?inc) AS ?first) WHERE {{
          VALUES ?country {{ {_COUNTRY_VALUES} }}
          ?item {path} wd:{qid}; wdt:P17 ?country; wdt:P571 ?inc .
        }} GROUP BY ?item ORDER BY ?first LIMIT {per}""")


def wikidata_oldest(per=12, log=print):
    """{qid: type label} for the `per` earliest dated items of each type."""
    out = {}
    for label, _cat, qid in TYPES:
        try:
            rows = _query(qid, per, transitive=True)
        except Exception:                          # broad classes can time out
            try:
                rows = _query(qid, per, transitive=False)
            except Exception as exc:
                log(f"  oldest-of-type query failed for {label}: {exc}")
                continue
        for r in rows:
            out.setdefault(r["item"]["value"].rsplit("/", 1)[-1], label)
    return out


def research_entries():
    """Flattened researched examples: dicts with type, category, name, wikipedia_title, ..."""
    try:
        data = json.loads(RESEARCH_PATH.read_text())
    except (FileNotFoundError, ValueError):
        return []
    out = []
    for t in data.get("types", []):
        for ex in t.get("examples", []):
            out.append({**ex, "type": t.get("type"), "category": t.get("category")})
    return out


def type_claim_text(entry):
    parts = []
    if entry.get("claimed_date"):
        parts.append(f"Claimed date: {entry['claimed_date']}")
    if entry.get("evidence_date"):
        parts.append(f"Evidence: {entry['evidence_date']}")
    if entry.get("claim"):
        parts.append(entry["claim"])
    if entry.get("source"):
        parts.append(f"Source: {entry['source']}")
    return ". ".join(p.rstrip(".") for p in parts)


def refresh_claims(log=print):
    """Rewrite the catalogue's "oldest of its type" notes from the research file without a rebuild
    (after corrections from the research track): python -c 'from bidb.oldest_types import refresh_claims; refresh_claims()'.
    Dates themselves change on the next build."""
    from .db import connect
    conn = connect()
    conn.execute("PRAGMA busy_timeout = 120000")
    n = 0
    for e in research_entries():
        cur = conn.execute("UPDATE buildings SET type_claim = ? WHERE oldest_of_type = ? AND (wikipedia_title = ? OR name = ?)",
                           (type_claim_text(e), e.get("type"), e.get("wikipedia_title"), e.get("name")))
        n += cur.rowcount
    conn.commit()
    log(f"refreshed {n} oldest-of-type notes")
    return n
