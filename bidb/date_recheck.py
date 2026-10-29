"""Date the text-mined records of an existing database again with today's rules.

`python -m bidb.date_recheck [--apply]`: records whose date came from a Wikipedia article, a register
description, the Wikidata description or a type estimate (or that had none) are dated again by the build's
own step (`date_fill.fill_missing_dates`, from the download cache); records dated from a Wikipedia list's
date text, and hoards, are read again with today's `dates.parse_text_year` ("Late 14th century" was 1301,
now 1351; a list date no longer earlier than Wikidata's gives way to it). The changes are listed in
`runs/date_recheck.json`. A rebuild would do the same but drop what the photo, plan and outline jobs added.
Dates kept after review (`date_confirmations.json`) and user corrections are left alone. With --apply the
changes are written, and records the build would now leave out (begun after the cutoff, neither a landmark
nor an oldest example) are listed for review, not deleted; NIAH records that came in only through a
digit missing from their date range are removed.
"""
import json
import re
import sys

from . import config, overrides
from .classify import period_for
from .date_fill import fill_missing_dates
from .dates import parse_text_year

MINED = ("From Wikipedia article", "From register description", "From Wikidata description",
         "Estimate (building type)", "Not recorded")
FIELDS = ("year_start", "date_text", "date_source", "date_confidence", "date_evidence", "period")
INPUTS = ("id", "name", "description", "classes", "wikipedia_title", "wikipedia_extract", "hes_id", "cadw_id",
          "landmark", "oldest_of_type")
OUT = config.ROOT / "runs" / "date_recheck.json"


def _kept():
    """Ids whose date stays: reviewed confirmations and user corrections."""
    path = config.ROOT / "data" / "curated" / "date_confirmations.json"
    kept = {k for k in json.loads(path.read_text()) if not k.startswith("_")} if path.exists() else set()
    return kept | {k for k, v in overrides.load().items() if "year_start" in v}


def records(conn):
    """The records dated by text mining or a type estimate, as dicts with their current date fields."""
    kept = _kept()
    marks = ", ".join("?" * len(MINED))
    rows = conn.execute(f"SELECT {', '.join(dict.fromkeys(INPUTS + FIELDS))} FROM buildings "
                        f"WHERE COALESCE(date_confidence, 'Not recorded') IN ({marks})", MINED)
    cols = [d[0] for d in rows.description]
    return [r for r in (dict(zip(cols, row)) for row in rows) if r["id"] not in kept]


def recheck(conn, log=print):
    """-> list of changes {id, name, old: {...}, new: {...}, leaves: bool}."""
    old = records(conn)
    fresh = [{k: r[k] for k in INPUTS} | {"year_start": None} for r in old]
    fill_missing_dates(fresh, log=log)
    changes = []
    for before, after in zip(old, fresh):
        a = {k: after.get(k) for k in FIELDS}
        a["date_confidence"] = a["date_confidence"] or "Not recorded"
        if a["year_start"] is None:            # as the build writes undated records
            a.update(date_text="Not recorded", date_source="", date_evidence=None, period="Unknown")
        b = {k: before[k] for k in FIELDS}
        if (b["year_start"], b["date_confidence"]) == (a["year_start"], a["date_confidence"]):
            continue                            # same date ("1170" or "c1170")
        leaves = (a["year_start"] is not None and a["year_start"] >= config.CUTOFF_YEAR
                  and not before["landmark"] and not before["oldest_of_type"])
        changes.append({"id": before["id"], "name": before["name"], "old": b, "new": a, "leaves": leaves})
    return changes


QUALIFIED = re.compile(r"\b(?:mid|middle|late|second half)\b[^.;]{0,25}?\d+(?:st|nd|rd|th)[\s-]+centur", re.I)


def listed(conn):
    """-> changes for records dated from a Wikipedia list whose qualified century ("Late 14th century") now
    reads as a later year."""
    kept = _kept()
    changes = []
    for row in conn.execute(f"SELECT id, name, {', '.join(FIELDS)} FROM buildings "
                            "WHERE date_source LIKE 'Wikipedia list%'"):
        b = dict(zip(("id", "name") + FIELDS, row))
        if b["id"] in kept or not QUALIFIED.search(b["date_text"] or ""):
            continue
        a = dict((k, b[k]) for k in FIELDS)
        m = re.fullmatch(r"(.*) \(Wikidata: (.*)\)", b["date_text"] or "", re.S)
        if b["date_source"].endswith("(earlier than Wikidata)") and m:
            listed_year, wd_year = parse_text_year(m.group(1)), parse_text_year(m.group(2))
            if wd_year is not None and listed_year is not None and listed_year >= wd_year:
                a.update(year_start=wd_year, date_text=f"{m.group(2)} (Wikipedia list: {m.group(1)})",
                         date_source="Wikidata inception")     # as records.build_record writes it
            else:
                a["year_start"] = listed_year
        else:
            a["year_start"] = parse_text_year(b["date_text"])
        if a["year_start"] is None or a["year_start"] == b["year_start"]:
            continue
        a["period"] = period_for(a["year_start"])
        changes.append({"id": b["id"], "name": b["name"], "old": {k: b[k] for k in FIELDS}, "new": a,
                        "leaves": False})
    return changes


def hoards(conn):
    """-> [(new year, period, id)] for hoards whose date text now reads as another year."""
    out = []
    for pid, year, text in conn.execute("SELECT id, year_start, date_text FROM places WHERE kind = 'hoard'"):
        y = parse_text_year(text or "")
        if y is not None and y != year:
            out.append((y, period_for(y), pid))
    return out


def niah_typos(conn):
    """NIAH records in only because a digit is missing from the start of their date range ("188–1840"):
    the build leaves them out now (niah.py)."""
    return [i for i, y, end in conn.execute(
        "SELECT id, year_start, CAST(substr(date_text, instr(date_text, '–') + 1, 4) AS INTEGER) FROM buildings "
        "WHERE date_source = 'NIAH' AND date_text LIKE '%NIAH date range%'") if y < 1000 and end > 1500]


def remove(conn, ids, log=print):
    """Delete records and the rows other tables keep for them."""
    marks = ", ".join("?" * len(ids))
    for (table,) in conn.execute("SELECT name FROM sqlite_master WHERE type = 'table'").fetchall():
        cols = {r[1] for r in conn.execute(f"PRAGMA table_info({table})")}
        for col in ("entity_id", "record_id", "building_id") if table != "buildings" else ():
            if col in cols and table == "places":         # a place merged with the record: keep the place
                conn.execute(f"UPDATE places SET {col} = NULL WHERE {col} IN ({marks})", ids)
            elif col in cols:
                conn.execute(f"DELETE FROM {table} WHERE {col} IN ({marks})", ids)
    conn.execute(f"DELETE FROM buildings_fts WHERE id IN ({marks})", ids)
    conn.execute(f"DELETE FROM buildings WHERE id IN ({marks})", ids)
    conn.commit()
    log(f"removed {len(ids)} records: {', '.join(ids)}")


def apply(conn, changes, log=print):
    """Write the new date fields, then recompute the date checks."""
    from .classify import regional_periods
    from .references import recheck as recheck_refs
    conn.executemany(f"UPDATE buildings SET {', '.join(k + ' = ?' for k in FIELDS)} WHERE id = ?",
                     [[c["new"][k] for k in FIELDS] + [c["id"]] for c in changes])
    conn.commit()
    log(f"{len(changes)} dates changed")
    regional_periods(conn)
    recheck_refs(log)


def main(argv):
    from .classify import regional_periods
    from .db import connect
    conn = connect()
    conn.execute("PRAGMA busy_timeout = 120000")
    changes = recheck(conn) + listed(conn)
    hoard_years = hoards(conn)
    print(f"hoards dated again: {len(hoard_years)}")
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(json.dumps(changes, indent=1, ensure_ascii=False))
    print(f"{len(changes)} changes ({sum(c['leaves'] for c in changes)} now after the cutoff) → {OUT}")
    typos = niah_typos(conn)
    print(f"NIAH records with a digit missing from their date: {typos}")
    if "--apply" in argv:
        apply(conn, changes)
        conn.executemany("UPDATE places SET year_start = ?, period = ? WHERE id = ?", hoard_years)
        conn.commit()
        regional_periods(conn)
        if typos:
            remove(conn, typos)


if __name__ == "__main__":
    main(sys.argv[1:])
