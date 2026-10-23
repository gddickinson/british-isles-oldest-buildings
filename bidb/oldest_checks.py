"""Research track / build stage: the earliest dated places of the newer groups, checked (roadmap N5).

    python -m bidb.oldest_checks           after bidb.oldest_lists: date precision, reviewed corrections
    python -m bidb.oldest_checks --todo    candidates not yet reviewed -> runs/oldest_checks_todo.json
    python -m bidb.oldest_checks --report  counts per verdict

The Oldest page lists the earliest dated places of each kind in the groups of `PLACE_GROUPS` (dates from
Wikidata). Two checks stand between Wikidata and that list:
  precision - a date given to the century or decade ("19th century", stored as 1819 or 1801) is shown as such
              ("between 1800 and 1839", "19th century", "1830s") and is not a candidate for "earliest dated";
  review    - `data/curated/oldest_places_review.json`: each candidate checked against its sources, with a
              verdict: kept (the date holds), corrected (year and age text from the sources), dropped (wrong
              kind of place, a date of something else, or no support; `reason` says which), open (not settled:
              still shown as unchecked).
Reviewed entries with sources become evidence claims (bidb.evidence.load), so their quotes are checked too.
"""
import json
import sys
import time

from .config import DATA_DIR, ROOT

REVIEW = DATA_DIR / "curated" / "oldest_places_review.json"
TODO = ROOT / "runs" / "oldest_checks_todo.json"
PLACE_GROUPS = ("Markets & trade", "Industrial heritage", "Infrastructure & utilities", "Graves & burial grounds",
                "Sport & leisure", "Public institutions")
BATCH = 1000


def review():
    """{qid: reviewed entry}."""
    try:
        return {e["qid"]: e for e in json.loads(REVIEW.read_text())["entries"]}
    except (FileNotFoundError, ValueError, KeyError):
        return {}


def claims():
    """Evidence claims for reviewed entries with sources (read through bidb.oldest_lists.claims)."""
    return [{"id": f"earliest-{qid}", "record": qid, "name": e["name"], "field": "age",
             "claim": f"Earliest dated {e.get('kind_label', 'place').lower()}: {e.get('age_text') or e.get('year')}",
             "value": e.get("age_text") or str(e.get("year")), "verdict": e["verdict"],
             "assessment": e.get("reason") or "", "sources": e["sources"], "researched": e.get("reviewed", "2026-10-22")}
            for qid, e in review().items() if e.get("sources") and e["verdict"] in ("kept", "corrected")]


def century(year):
    c = (year - 1) // 100 + 1 if year > 0 else None
    if c is None:
        return None
    suffix = "th" if 10 <= c % 100 <= 20 else {1: "st", 2: "nd", 3: "rd"}.get(c % 10, "th")
    return f"{c}{suffix} century"


def date_text(year, precision, earliest=None, latest=None):
    """How a Wikidata date of less than year precision reads."""
    if earliest and latest and earliest != latest:
        return f"between {earliest} and {latest}"     # not "1800–1839", which reads as opened and closed
    if precision == 8:
        return f"{year // 10 * 10}s"
    if precision == 7:
        # Wikidata stores "19th century" as any year in it (1801, 1819, 1900): the century the year falls in,
        # except a round hundred, which is the last year of its century
        return century(year)
    return None


def _year(time):
    try:
        return int(time[:time.index("-", 1)]) if time else None
    except (TypeError, ValueError):
        return None


def _qualifier_year(claim, prop):
    for snak in claim.get("qualifiers", {}).get(prop, []):
        if snak.get("snaktype") == "value":
            return _year(snak["datavalue"]["value"].get("time"))
    return None


def precision_of(entity):
    """(precision, earliest, latest) of the date bidb.place_stage.query reads (P1619 opening, else P571
    inception; the most precise statement), or None."""
    for prop in ("P1619", "P571"):
        best = None
        for c in entity.get("claims", {}).get(prop, []):
            snak = c.get("mainsnak", {})
            if c.get("rank") == "deprecated" or snak.get("snaktype") != "value":
                continue
            p = snak["datavalue"]["value"].get("precision", 9)
            if best is None or p > best[0]:
                best = (p, _qualifier_year(c, "P1319"), _qualifier_year(c, "P1326"))
        if best:
            return best
    return None


def precisions(qids, log=print):
    """{qid: (precision, earliest, latest)} for dates coarser than a year (wbgetentities, 50 per request;
    the query service is not needed)."""
    from .wikidata import get_entities
    out = {}
    qids = sorted(set(qids))
    for i in range(0, len(qids), BATCH):
        for q, ent in get_entities(qids[i:i + BATCH], props="claims").items():
            p = precision_of(ent)
            if p and p[0] < 9:
                out[q] = p
        log(f"  precision: {min(i + BATCH, len(qids))}/{len(qids)}")
    return out


def apply_precision(conn, log=print):
    """Places of PLACE_GROUPS dated from Wikidata to less than a year: date text says so, year = earliest."""
    q = ",".join("?" for _ in PLACE_GROUPS)
    rows = conn.execute(f"""SELECT id, wikidata_id, year_start FROM places WHERE kind_group IN ({q})
        AND year_start IS NOT NULL AND wikidata_id LIKE 'Q%' AND date_text = CAST(year_start AS TEXT)""",
                        PLACE_GROUPS).fetchall()
    found = precisions([r[1] for r in rows], log)
    from .classify import period_for
    updates = []
    for rid, qid, year in rows:
        if qid in found:
            p, earliest, latest = found[qid]
            start = earliest if earliest is not None else year
            updates.append((start, date_text(year, p, earliest, latest), period_for(start), rid))
    conn.executemany("UPDATE places SET year_start = ?, date_text = ?, period = ? WHERE id = ?", updates)
    log(f"  {len(updates)} of {len(rows)} Wikidata dates are given to the decade or century")
    return len(updates)


def apply_review(conn, log=print):
    """Corrected years and age texts from the review go to the places."""
    from .classify import period_for
    rows = [(e["year"], e.get("age_text") or str(e["year"]), period_for(e["year"]), qid)
            for qid, e in review().items() if e["verdict"] == "corrected" and isinstance(e.get("year"), int)]
    conn.executemany("UPDATE places SET year_start = ?, date_text = ?, period = ? WHERE id = ?", rows)
    log(f"  {len(rows)} reviewed corrections applied")


def candidates(conn, per=6, reviewed=None):
    """The earliest `per` places of each kind (group, kind label) that a review has not dropped, with a precise
    date: [(group, label, row dict, review entry or None)]."""
    from .oldest_lists import KINDS, KIND_LABEL
    reviewed = review() if reviewed is None else reviewed
    dropped = [q for q, e in reviewed.items() if e["verdict"] == "dropped"]
    corrected = [q for q, e in reviewed.items() if e["verdict"] == "corrected"]
    ph = lambda xs: ",".join("?" for _ in xs) or "''"
    rows = conn.execute(f"""SELECT id, name, kind_group, kind_label, year_start, date_text, locality, nation FROM (
        SELECT *, ROW_NUMBER() OVER (PARTITION BY kind_group, kind_label ORDER BY year_start, name) AS n FROM places
        WHERE kind_group IN ({ph(PLACE_GROUPS)}) AND year_start IS NOT NULL AND kind NOT IN ({ph(KINDS)})
              AND kind_label NOT IN ({ph(KIND_LABEL)}) AND id NOT IN ({ph(dropped)})
              AND (date_text = CAST(year_start AS TEXT) OR id IN ({ph(corrected)})))
        WHERE n <= ? ORDER BY kind_group, kind_label, year_start, name""",
                        (*PLACE_GROUPS, *KINDS, *KIND_LABEL.values(), *dropped, *corrected, per)).fetchall()
    return [(r[2], r[3], dict(zip(("id", "name", "group", "label", "year", "text", "locality", "nation"), r)),
             reviewed.get(r[0])) for r in rows]


def earliest(conn, per=6):
    """The Oldest page sections: earliest dated places of each kind, with review verdicts."""
    out = {}
    for group, label, r, rev in candidates(conn, per):
        rev = rev if rev and rev["verdict"] != "open" else None      # open: still unchecked
        g = out.setdefault(group, {"title": f"Earliest dated: {group}", "group": group, "unchecked": 0, "categories": {}})
        g["unchecked"] += rev is None
        g["categories"].setdefault(label, []).append({
            "id": r["id"], "name": r["name"], "age": r["text"] or str(r["year"]), "year": r["year"],
            "verdict": rev["verdict"] if rev else None, "claim": rev.get("reason") if rev else None,
            "location": ", ".join(x for x in (r["locality"], r["nation"]) if x)})
    return {f"places:{g}": {**v, "categories": [{"category": c, "entries": e} for c, e in v["categories"].items()]}
            for g, v in out.items()}


def todo(conn, per=6):
    """Unreviewed candidates (with their Wikipedia title and description) for the next round of research."""
    reviewed = review()
    ids = [r["id"] for _g, _l, r, rev in candidates(conn, per, reviewed) if rev is None]
    if not ids:
        print("nothing to review")
        return []
    extra = {row[0]: row[1:] for row in conn.execute(
        f"SELECT id, wikipedia_title, description, source FROM places WHERE id IN ({','.join('?' * len(ids))})", ids)}
    out = [{"qid": r["id"], "name": r["name"], "group": g, "kind_label": l, "year": r["year"],
            "location": ", ".join(x for x in (r["locality"], r["nation"]) if x),
            "wikipedia_title": extra[r["id"]][0], "description": extra[r["id"]][1], "source": extra[r["id"]][2]}
           for g, l, r, rev in candidates(conn, per, reviewed) if rev is None]
    TODO.parent.mkdir(exist_ok=True)
    TODO.write_text(json.dumps(out, indent=1, ensure_ascii=False))
    print(f"{len(out)} candidates to review -> {TODO}")
    return out


def run(log=print):
    from .db import connect
    t0 = time.time()
    conn = connect()
    conn.execute("PRAGMA busy_timeout = 120000")
    apply_precision(conn, lambda m: log(f"[{time.time() - t0:5.0f}s] {m}"))
    apply_review(conn, lambda m: log(f"[{time.time() - t0:5.0f}s] {m}"))
    conn.commit()


def report():
    from collections import Counter
    from .db import connect
    print("review:", dict(Counter(e["verdict"] for e in review().values())))
    rows = candidates(connect())
    print(f"candidates shown: {len(rows)}, unreviewed {sum(r[3] is None for r in rows)}")


if __name__ == "__main__":
    if sys.argv[1:] == ["--todo"]:
        from .db import connect
        todo(connect())
    elif sys.argv[1:] == ["--report"]:
        report()
    else:
        run()
