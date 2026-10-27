"""Building types BT2b: per type, the catalogue records and places mapped to it (table type_map, bidb.type_map):
counts, map points, dated examples and the earliest surviving example, each checked against the type's period.

An example begun more than EARLY years before the type's first known date (period.from) is "too early": a mapping
or dating error to review, never the type's earliest example. The earliest surviving example is the earliest
dated catalogue record, of which it is the primary type, that is standing or a ruin, whose date is not itself an estimate from its building type
(that would be circular; for places, a date text that says "estimate" or a register period such as "Prehistoric
(register period)", whose year only stands for the period, bidb.registers.period_year) and not too early; failing that, the earliest such place (register monuments and
Wikidata places carry no standing/demolished status, so `surviving` is None for them).
Reviewed early examples that are right (the type's first known date is later than a real example) are listed in
`aliases.json` `early_ok` with the reason, and kept as examples.

    python -m bidb.type_stats [--report] [--type ID]
"""
import json
import re
import sys
from collections import defaultdict

from . import building_types, type_map
from .db import connect

EARLY = 100                 # years before a type's first known date that make an example "too early"
GONE = "Demolished / destroyed"
ESTIMATE = "Estimate (building type)"
REGISTER_PERIOD = "(register period)"   # date texts of register places dated only by their period
EXAMPLES = 200              # dated examples returned for one type
# Place groups whose dates are of the structure itself (a fort, a line, a bridge), not of an organisation founded
# earlier (a hospital, a firm): their places dated to the year rank with catalogue records (`structure_place`)
STRUCTURE_GROUPS = {"Military heritage", "Infrastructure & utilities", "Bridges", "Maritime heritage", "Underground"}
_TO_YEAR = re.compile(r"(?:(?:built|opened|founded|completed|begun|established) )?(?:\d{1,2} [A-Z][a-z]+ )?\d{3,4}")

_ROWS = """
SELECT tm.type_id, tm.source, tm.entity_id, tm.via, tm.is_primary, b.name, b.year_start, b.date_text, b.lat, b.lon,
       b.nation, b.county, b.status, b.date_confidence, b.image_thumb, NULL AS kind, NULL AS kind_group
FROM type_map tm JOIN buildings b ON tm.source = 'building' AND b.id = tm.entity_id {where}
UNION ALL
SELECT tm.type_id, tm.source, tm.entity_id, tm.via, tm.is_primary, p.name, p.year_start, p.date_text, p.lat, p.lon,
       p.nation, p.county, NULL, NULL, p.image_thumb, p.kind, p.kind_group
FROM type_map tm JOIN places p ON tm.source = 'place' AND p.id = tm.entity_id {where}
"""
_COLS = ("type_id", "source", "id", "via", "primary", "name", "year", "date_text", "lat", "lon", "nation",
         "county", "status", "date_confidence", "thumb", "kind", "kind_group")


def _rows(conn, type_id=None):
    where, args = ("WHERE tm.type_id = ?", (type_id, type_id)) if type_id else ("", ())
    return [dict(zip(_COLS, r)) for r in conn.execute(_ROWS.format(where=where), args)]


def types_by_id(data=None):
    data = data or building_types.load()
    return {t["id"]: t for t in data["types"] if not t.get("abroad")}


def early_ok():
    """{entity id: reason} of early examples reviewed and kept."""
    return type_map.load_aliases().get("early_ok", {})


def too_early(row, t, ok=None):
    """Begun more than EARLY years before the type's first known date; never a register period's year, which
    stands for the whole period (a broch in "Prehistoric" is dated -2000)."""
    first = (t.get("period") or {}).get("from")
    return (row["year"] is not None and first is not None and row["year"] < first - EARLY
            and row["id"] not in (ok or {}) and REGISTER_PERIOD not in (row.get("date_text") or "").lower())


def surviving(row):
    """True / False for catalogue records (standing or ruin / demolished); None for places (not recorded)."""
    return None if row["source"] == "place" else row["status"] != GONE


def estimated(row):
    """The date is an estimate from the building type (records), says it is an estimate or is a register period's
    representative year (places)."""
    text = (row["date_text"] or "").lower()
    return row["date_confidence"] == ESTIMATE or "estimate" in text or REGISTER_PERIOD in text


def _candidate(row, t, ok):
    return (row["year"] is not None and not too_early(row, t, ok) and surviving(row) is not False
            and not estimated(row))


def structure_place(row):
    """A place of a STRUCTURE_GROUPS group dated to the year ("1805", "opened 27 September 1825")."""
    return (row["source"] == "place" and row.get("kind_group") in STRUCTURE_GROUPS
            and bool(_TO_YEAR.fullmatch((row["date_text"] or "").strip())))


def earliest(rows, t, ok=None):
    """The earliest surviving example among a type's rows: where the type is the primary one (a castle later
    used as a town hall is no early town hall), catalogue records before places; then any. For a type with more
    places than records (railway lines, Martello towers), its structure places dated to the year rank with the
    records: the Stockton and Darlington Railway (1825) before a line in the catalogue of 1894."""
    mostly_places = (len({r["id"] for r in rows if r["source"] == "place"})
                     > len({r["id"] for r in rows if r["source"] == "building"}))
    for primary, source in ((True, "building"), (True, "place"), (False, "building"), (False, "place")):
        found = [r for r in rows if (r["source"] == source or (source == "building" and mostly_places
                                                               and structure_place(r)))
                 and (r["primary"] or not primary) and _candidate(r, t, ok)]
        if found:
            return min(found, key=lambda r: (r["year"], r["name"] or ""))
    return None


def _brief(row):
    return None if row is None else {k: row[k] for k in ("id", "source", "name", "year", "date_text", "nation",
                                                         "county", "status", "date_confidence", "thumb")}


def _period(t):
    p = t.get("period") or {}
    return {k: p.get(k) for k in ("text", "from", "flourish", "to", "ongoing")}


def summary(conn, data=None):
    """One line per isles type: counts, dated, too early, earliest surviving example."""
    types, ok = types_by_id(data), early_ok()
    by_type = defaultdict(list)
    for r in _rows(conn):
        by_type[r["type_id"]].append(r)
    out = []
    for tid, t in types.items():
        rows = by_type.get(tid, [])
        out.append({
            "id": tid, "name": t["name"], "family": t.get("family"), "domain": t.get("domain"),
            "period": _period(t),
            "buildings": len({r["id"] for r in rows if r["source"] == "building"}),
            "places": len({r["id"] for r in rows if r["source"] == "place"}),
            "dated": sum(r["year"] is not None for r in rows),
            "too_early": sum(too_early(r, t, ok) for r in rows),
            "earliest": _brief(earliest(rows, t, ok)),
        })
    return out


def detail(conn, type_id, data=None, limit=EXAMPLES):
    """One type: its curated entry, counts by nation and century, dated examples (oldest first, too early ones
    flagged), the earliest surviving example, map points [lat, lon, id, source, year, primary]."""
    types = types_by_id(data)
    t = types.get(type_id)
    if t is None:
        return None
    ok, rows = early_ok(), _rows(conn, type_id)
    nations, centuries = defaultdict(int), defaultdict(int)
    for r in rows:
        nations[r["nation"] or "Unknown"] += 1
        if r["year"] is not None:
            centuries[r["year"] // 100 * 100] += 1
    dated = sorted((r for r in rows if r["year"] is not None), key=lambda r: (r["year"], r["name"] or ""))
    examples = [dict(_brief(r), via=r["via"], primary=bool(r["primary"]), kind=r["kind"],
                     too_early=too_early(r, t, ok), surviving=surviving(r)) for r in dated[:limit]]
    return {
        "type": t, "period": _period(t),
        "buildings": len({r["id"] for r in rows if r["source"] == "building"}),
        "places": len({r["id"] for r in rows if r["source"] == "place"}),
        "dated": len(dated), "too_early": sum(too_early(r, t, ok) for r in rows),
        "earliest": _brief(earliest(rows, t, ok)),
        "by_nation": dict(sorted(nations.items(), key=lambda kv: -kv[1])),
        "by_century": dict(sorted(centuries.items())),
        "examples": examples,
        "points": [[r["lat"], r["lon"], r["id"], r["source"], r["year"], int(r["primary"])]
                   for r in rows if r["lat"] is not None and r["lon"] is not None],
    }


def for_entity(conn, entity_id, data=None):
    """The types of one record or place, primary first: [{id, name, family, via, primary}]."""
    types = types_by_id(data)
    return [{"id": tid, "name": types[tid]["name"], "family": types[tid].get("family"), "via": via,
             "primary": bool(primary)}
            for tid, via, primary in conn.execute(
                "SELECT type_id, via, is_primary FROM type_map WHERE entity_id = ? ORDER BY is_primary DESC",
                (entity_id,)) if tid in types]


def early_examples(conn, data=None):
    """Every too-early example: (type, first known, row)."""
    types, ok = types_by_id(data), early_ok()
    return sorted(((r["type_id"], types[r["type_id"]]["period"]["from"], r) for r in _rows(conn)
                   if r["type_id"] in types and too_early(r, types[r["type_id"]], ok)),
                  key=lambda x: (x[0], x[2]["year"]))


def report(conn):
    lines, rows = [], summary(conn)
    with_ex = [r for r in rows if r["buildings"] or r["places"]]
    lines.append(f"{len(with_ex)} of {len(rows)} isles types have examples; "
                 f"{sum(r['earliest'] is not None for r in rows)} an earliest surviving example; "
                 f"{sum(r['too_early'] for r in rows)} examples too early")
    for r in rows:
        e = r["earliest"]
        lines.append(f"  {r['id']:<30} {r['period']['from']!s:>6}  b {r['buildings']:>5}  p {r['places']:>5}  "
                     f"early {r['too_early']:>3}  earliest: "
                     + (f"{e['year']} {e['name']} ({e['source']} {e['id']})" if e else "-"))
    lines.append("Too early (type, first known, year, via, name, id):")
    lines += [f"  {tid} {first} {r['year']} {r['via']} {r['name']} [{r['source']} {r['id']}]"
              for tid, first, r in early_examples(conn)]
    return lines


if __name__ == "__main__":
    c = connect()
    if "--type" in sys.argv:
        d = detail(c, sys.argv[sys.argv.index("--type") + 1])
        print(json.dumps({k: v for k, v in (d or {}).items() if k not in ("type", "points")}, indent=1,
                         ensure_ascii=False)[:6000])
    else:
        print("\n".join(report(c)))
