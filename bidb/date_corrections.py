"""Reviewed date corrections (data/curated/date_corrections.json), each with the sentence and
source that justify it. Applied in the build before the user's own corrections (overrides), and
to an existing database with:  python -m bidb.date_corrections

Entries come from reviewing the date-check conflicts: cases where the record's own Wikipedia
introduction states that the building (or its surviving fabric) dates from another time than the
catalogue's date, e.g. a Wikidata "inception" that is really a re-opening or listing year.
"""
import json

from .classify import period_for
from .config import DATA_DIR

PATH = DATA_DIR / "curated" / "date_corrections.json"
CONFIDENCE = "Corrected (reviewed)"


def load():
    try:
        return json.loads(PATH.read_text())
    except (OSError, ValueError):
        return {}


def fields(entry):
    """Columns a correction sets."""
    return {"year_start": entry["year_start"], "date_text": entry["date_text"],
            "period": period_for(entry["year_start"]), "date_confidence": CONFIDENCE,
            "date_source": f"Reviewed correction ({entry['source']})", "date_evidence": entry["evidence"]}


def apply(records):
    """Apply to freshly built records in place; returns how many were corrected."""
    data = load()
    n = 0
    for r in records:
        e = data.get(r["id"])
        if e:
            r.update(fields(e))
            n += 1
    return n


def apply_to_db(log=print):
    from .db import connect
    from .references import recheck
    conn = connect()
    conn.execute("PRAGMA busy_timeout = 120000")       # background jobs may be writing
    data = load()
    for bid, e in data.items():
        f = fields(e)
        conn.execute(f"UPDATE buildings SET {', '.join(k + ' = ?' for k in f)} WHERE id = ?",
                     [*f.values(), bid])
    conn.commit()
    log(f"applied {len(data)} reviewed date corrections")
    recheck(log)


if __name__ == "__main__":
    apply_to_db()
