"""Static export of pronunciations (used by app.static_export): data/pron.json, read by static/pron.js."""
import json

from bidb import pron_db

FIELDS = ["name", "lang", "variety", "ipa", "respell", "audio", "source", "source_url", "entity_kind", "entity_id"]


def export(conn, out_dir):
    """Rows as compact arrays (trailing empties dropped) and record -> towns links that have one."""
    if not pron_db.has_tables(conn):
        return
    rows = []
    for r in pron_db.all_rows(conn):
        a = [r[f] or "" for f in FIELDS]
        while a and not a[-1]:
            a.pop()
        rows.append(a)
    with_rows = {r[-1] for r in rows}
    towns = {}
    for rec, town_id, town in conn.execute("SELECT record_id, town_id, town FROM pron_towns"):
        if town_id in with_rows:
            towns.setdefault(rec, []).append([town_id, town])
    path = out_dir / "pron.json"
    cov = {**pron_db.coverage(conn), "missing": pron_db.missing_tricky(conn)}
    path.write_text(json.dumps({"rows": rows, "towns": towns, "coverage": cov}, ensure_ascii=False,
                               separators=(",", ":")))
    print(f"exported {len(rows)} pronunciations ({path.stat().st_size / 1e6:.1f} MB)")
