"""Building types BT3b: per material or technique, the catalogue records and places linked to it (table
material_map, bidb.material_map): counts by how found, by nation and by century begun, dated examples and the
earliest example, each checked against the material's period.

A record names the materials of all its phases, and its year is when it was begun, so an example begun more than
EARLY years before the material's first date (period.from) is "too early": most often a later phase (a Norman
church re-roofed in Welsh slate, a medieval house refronted in brick), sometimes a matching error; such examples
are counted but never the earliest. The earliest example is the earliest dated catalogue record that survives,
whose date is not an estimate from its building type and that was begun in or after the material's first year
(within EARLY years before it when that year is only the earliest a source names, period.earlier); failing that,
the earliest such place. It is the oldest building known to use the material, begun when the material was in use;
the material may still belong to a later phase of it.

    python -m bidb.material_stats [--report] [--material ID]
"""
import sys
from collections import Counter, defaultdict

from . import building_materials
from .db import connect
from .type_stats import _brief, estimated, surviving

EARLY = 100                 # years before a material's first date that make an example "too early"
EXAMPLES = 200              # dated examples returned for one material

_ROWS = """
SELECT mm.material_id, mm.source, mm.entity_id, mm.via, mm.label, mm.place, mm.evidence, b.name, b.year_start,
       b.date_text, b.lat, b.lon, b.nation, b.county, b.status, b.date_confidence, b.image_thumb
FROM material_map mm JOIN buildings b ON mm.source = 'building' AND b.id = mm.entity_id {where}
UNION ALL
SELECT mm.material_id, mm.source, mm.entity_id, mm.via, mm.label, mm.place, mm.evidence, p.name, p.year_start,
       p.date_text, p.lat, p.lon, p.nation, p.county, NULL, NULL, p.image_thumb
FROM material_map mm JOIN places p ON mm.source = 'place' AND p.id = mm.entity_id {where}
"""
_COLS = ("material_id", "source", "id", "via", "label", "place", "evidence", "name", "year", "date_text", "lat",
         "lon", "nation", "county", "status", "date_confidence", "thumb")


def _rows(conn, material_id=None, entity_id=None):
    where, args = "", ()
    if material_id:
        where, args = "WHERE mm.material_id = ?", (material_id, material_id)
    elif entity_id:
        where, args = "WHERE mm.entity_id = ?", (entity_id, entity_id)
    return [dict(zip(_COLS, r)) for r in conn.execute(_ROWS.format(where=where), args)]


def materials_by_id(data=None):
    return {m["id"]: m for m in (data or building_materials.load())["materials"]}


def too_early(row, m):
    first = (m.get("period") or {}).get("from")
    return row["year"] is not None and first is not None and row["year"] < first - EARLY


def _candidate(row, m):
    p = m.get("period") or {}
    first = p.get("from")
    if row["year"] is None or surviving(row) is False or estimated(row):
        return False
    return first is None or row["year"] >= first - (EARLY if p.get("earlier") else 0)


def earliest(rows, m):
    for source in ("building", "place"):
        found = [r for r in rows if r["source"] == source and _candidate(r, m)]
        if found:
            return min(found, key=lambda r: (r["year"], r["name"] or ""))
    return None


def century(year):
    """1066 → 1000 (the 11th century), -50 → -100."""
    return (year // 100) * 100


def _period(m):
    p = m.get("period") or {}
    return {k: p.get(k) for k in ("text", "from", "flourish", "to", "ongoing", "earlier")}


def summary(conn, data=None):
    """One line per material: counts (records, places, by how found), dated, too early, earliest example."""
    mats, by = materials_by_id(data), defaultdict(list)
    for r in _rows(conn):
        by[r["material_id"]].append(r)
    out = []
    for mid, m in mats.items():
        rows = by.get(mid, [])
        out.append({
            "id": mid, "name": m["name"], "group": m["group"], "kind": m["kind"], "period": _period(m),
            "buildings": sum(r["source"] == "building" for r in rows),
            "places": sum(r["source"] == "place" for r in rows),
            "via": dict(Counter(r["via"] for r in rows)),
            "dated": sum(r["year"] is not None for r in rows),
            "too_early": sum(too_early(r, m) for r in rows),
            "earliest": _brief(earliest(rows, m)),
        })
    return out


def by_century(conn, data=None):
    """{material id: {century: examples begun then}} (too early ones left out), for the charts of BT5."""
    mats, out = materials_by_id(data), defaultdict(Counter)
    for r in _rows(conn):
        m = mats.get(r["material_id"])
        if m and r["year"] is not None and not too_early(r, m):
            out[r["material_id"]][century(r["year"])] += 1
    return {k: dict(sorted(v.items())) for k, v in out.items()}


def detail(conn, material_id, data=None, limit=EXAMPLES):
    """One material: its curated entry, counts by nation and century, dated examples oldest first (too early ones
    flagged) with the evidence, the earliest example, map points [lat, lon, id, source, year]."""
    m = materials_by_id(data).get(material_id)
    if m is None:
        return None
    rows = _rows(conn, material_id=material_id)
    dated = sorted((r for r in rows if r["year"] is not None), key=lambda r: (r["year"], r["name"] or ""))
    ex = [dict(_brief(r), via=r["via"], label=r["label"], place=r["place"], evidence=r["evidence"],
               too_early=too_early(r, m)) for r in dated[:limit]]
    return {
        "material": m, "count": len(rows), "dated": len(dated),
        "by_nation": dict(Counter(r["nation"] or "Unknown" for r in rows).most_common()),
        "by_century": dict(sorted(Counter(century(r["year"]) for r in dated if not too_early(r, m)).items())),
        "via": dict(Counter(r["via"] for r in rows)),
        "earliest": _brief(earliest(rows, m)), "examples": ex,
        "points": [[r["lat"], r["lon"], r["id"], r["source"], r["year"]] for r in rows if r["lat"] is not None],
    }


def for_entity(conn, entity_id, data=None):
    """The materials of one record or place with how each was found and the evidence."""
    mats = materials_by_id(data)
    return [{"id": r["material_id"], "name": mats[r["material_id"]]["name"], "group": mats[r["material_id"]]["group"],
             "via": r["via"], "label": r["label"], "place": r["place"], "evidence": r["evidence"]}
            for r in _rows(conn, entity_id=entity_id) if r["material_id"] in mats]


def report(conn):
    lines = []
    for s in sorted(summary(conn), key=lambda s: -(s["buildings"] + s["places"])):
        e = s["earliest"]
        lines.append(f"{s['id']:26} {s['buildings']:5} rec {s['places']:5} pl  from {s['period']['from']}  "
                     f"too early {s['too_early']:4}  earliest: "
                     + (f"{e['name']} ({e['year']})" if e else "-"))
    return lines


if __name__ == "__main__":
    c = connect()
    if "--material" in sys.argv:
        d = detail(c, sys.argv[sys.argv.index("--material") + 1])
        for x in (d or {}).get("examples", [])[:40]:
            print(x["year"], x["name"], "|", x["via"], x["place"], "|", "EARLY" if x["too_early"] else "",
                  x["evidence"])
    else:
        print("\n".join(report(c)))
