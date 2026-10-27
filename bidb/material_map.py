"""Building types BT3b: catalogue records and places linked to the materials and techniques of
bidb.building_materials → table material_map.

Each record or place is read from three kinds of source, in this order (a material found by an earlier one is
not repeated):
    wikidata   its Wikidata material statements (P186), by the material item's QID (material_aliases.json
               `wikidata`; items reviewed and left out are in `not_in_list`), queried once for the isles (QLever)
    register   the official description held in the download cache: HES (whole description), Cadw (Period and
               History only: the cached text) and NIAH (records' register_notes)
    wikipedia  the cached Wikipedia article (<cache>/wiki_articles.json, written by bidb.stories), sections not
               skipped, else the extract
Text is matched by the term rules of material_aliases.json (bidb.material_text), and the sentence that matched is
kept as evidence. The most specific stone is kept: a record built of Bath stone is not also linked to limestone
(a material marked `general` gives way to the materials it has variant links to, `general_of`; other variants, as
rubble and ashlar or slate and Welsh slate, are both kept). A material named in a text
may be of any phase of the building (a Norman church re-roofed in Welsh slate), so bidb.material_stats flags examples begun long before the material's first date.
Places are read when their kind is a building or structure (type_map's `skip_kinds` and the file's own left out).

    python -m bidb.material_map [--report]     → table material_map (entity_id, source, material_id, via, label,
                                                  place, evidence)
"""
import json
import sys
import time
from collections import Counter

from . import building_materials, type_map
from .change_firms import COUNTRIES, QLEVER
from .db import connect
from .http import request_json
from .material_text import Rules
from .pron_sources import load_store
from .register_dates import cached_description
from .stories import STORE

PATH = building_materials.FOLDER / "material_aliases.json"
COLUMNS = ("entity_id", "source", "material_id", "via", "label", "place", "evidence")
VIAS = ("wikidata", "register", "wikipedia")


def general_of(data):
    """{material: {general materials it is a variant of}}: variant links of bidb.building_materials from a material
    marked `general`."""
    general = {m["id"] for m in data["materials"] if m.get("general")}
    out = {}
    for x in data["links"]:
        if x["kind"] == "variant" and x["from"] in general:
            out.setdefault(x["to"], set()).add(x["from"])
    return out


def load_aliases(path=PATH):
    return json.loads(path.read_text())


def problems(aliases, known):
    """Aliases and terms naming unknown materials, items both mapped and left out, patterns that do not compile."""
    bad = [f"wikidata {q}: unknown material {m}" for q, m in aliases["wikidata"].items() if m not in known]
    bad += [f"term {t['pattern']}: unknown material {t['material']}" for t in aliases["terms"]
            if t["material"] not in known]
    left = {x.split()[0] for x in aliases["not_in_list"]["items"]}
    bad += [f"wikidata {q}: both mapped and left out" for q in sorted(left & set(aliases["wikidata"]))]
    try:
        Rules(aliases)
    except Exception as e:                     # re.error, KeyError
        bad.append(f"rules: {e}")
    return bad


def wikidata_materials():
    """{item QID: [(material QID, label)]} for items of the isles with coordinates and a material (QLever)."""
    q = f"""PREFIX wd: <http://www.wikidata.org/entity/> PREFIX wdt: <http://www.wikidata.org/prop/direct/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
SELECT DISTINCT ?i ?m ?l WHERE {{ VALUES ?c {{ {" ".join("wd:" + c for c in COUNTRIES.split())} }}
  ?i wdt:P17 ?c; wdt:P186 ?m; wdt:P625 ?x . OPTIONAL {{ ?m rdfs:label ?l FILTER(LANG(?l)="en") }} }}"""
    res = request_json(QLEVER, params={"query": q}, headers={"Accept": "application/sparql-results+json"},
                       min_interval=1.0)
    out = {}
    for b in res["results"]["bindings"]:
        qid = b["i"]["value"].rsplit("/", 1)[1]
        out.setdefault(qid, []).append((b["m"]["value"].rsplit("/", 1)[1], b.get("l", {}).get("value", "")))
    return out


class Linker:
    def __init__(self, aliases, known, wd_materials, articles, general=None):
        self.qids, self.rules = aliases["wikidata"], Rules(aliases, known)
        self.general = general or {}
        self.wd, self.articles = wd_materials, articles

    def from_wikidata(self, qid):
        return {self.qids[m]: (lab, "Wikidata", "") for m, lab in self.wd.get(qid or "", []) if m in self.qids}

    def wiki_blocks(self, title, extract):
        art = self.articles.get(title) if title else None
        return self.rules.article_blocks(art) if art else [("Wikipedia", extract or "")]

    def link(self, qid, register_blocks, title, extract):
        """[(material id, via, label, place, evidence)] for one record or place."""
        out = {}
        for via, found in (("wikidata", self.from_wikidata(qid)), ("register", self.rules.find(register_blocks)),
                           ("wikipedia", self.rules.find(self.wiki_blocks(title, extract)))):
            for mid, (label, where, ev) in found.items():
                out.setdefault(mid, (mid, via, label, where, ev))
        drop = {g for mid in out for g in self.general.get(mid, ())}
        return [v for mid, v in out.items() if mid not in drop]


def register_blocks(row):
    got = cached_description({"hes_id": row["hes_id"], "cadw_id": row["cadw_id"]})
    blocks = [(got[0], got[2])] if got and isinstance(got[2], str) else []
    if row["register_notes"]:
        blocks.append(("NIAH", row["register_notes"]))
    return blocks


def rows(conn, linker, skip_kinds=()):
    out = []
    for r in conn.execute("SELECT id, wikidata_id, hes_id, cadw_id, register_notes, wikipedia_title, "
                          "wikipedia_extract FROM buildings"):
        out += [(r["id"], "building") + x for x in linker.link(r["wikidata_id"], register_blocks(r),
                                                               r["wikipedia_title"], r["wikipedia_extract"])]
    skip = set(skip_kinds)
    for r in conn.execute("SELECT id, kind, wikidata_id, wikipedia_title, wikipedia_extract FROM places"):
        if r["kind"] not in skip:
            out += [(r["id"], "place") + x for x in linker.link(r["wikidata_id"], [], r["wikipedia_title"],
                                                                r["wikipedia_extract"])]
    return out


def write(conn, out):
    conn.execute("DROP TABLE IF EXISTS material_map")
    conn.execute(f"CREATE TABLE material_map ({', '.join(COLUMNS)})")
    conn.execute("CREATE INDEX material_map_material ON material_map(material_id)")
    conn.execute("CREATE INDEX material_map_entity ON material_map(entity_id)")
    conn.executemany(f"INSERT INTO material_map VALUES ({', '.join('?' for _ in COLUMNS)})", out)
    conn.commit()


def run(log=print):
    t0 = time.time()
    data = building_materials.load()
    known = {m["id"] for m in data["materials"]}
    aliases = load_aliases()
    bad = problems(aliases, known)
    if bad:
        raise ValueError("material_aliases.json: " + "; ".join(bad))
    linker = Linker(aliases, known, wikidata_materials(), load_store(STORE), general_of(data))
    conn = connect()
    conn.execute("PRAGMA busy_timeout = 120000")
    out = rows(conn, linker, type_map.load_aliases().get("skip_kinds", []) + aliases.get("skip_kinds", []))
    write(conn, out)
    linked = {s: len({r[0] for r in out if r[1] == s}) for s in ("building", "place")}
    log(f"[{time.time() - t0:5.0f}s] Materials: {linked['building']:,} records and {linked['place']:,} places "
        f"linked to {len({r[2] for r in out})} materials and techniques ({len(out):,} links)")


def report(conn, wd=None):
    """Coverage: links by how found, materials with most links, materials never found, unreviewed P186 items."""
    lines = []
    for source, table in (("building", "buildings"), ("place", "places")):
        total = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        n = conn.execute("SELECT COUNT(DISTINCT entity_id) FROM material_map WHERE source = ?", (source,)).fetchone()[0]
        vias = conn.execute("SELECT via, COUNT(*) FROM material_map WHERE source = ? GROUP BY via ORDER BY 2 DESC",
                            (source,)).fetchall()
        lines.append(f"{table}: {n:,} of {total:,} linked ({100 * n / total:.1f}%): "
                     + ", ".join(f"{v} {k:,}" for v, k in vias))
    counts = dict(conn.execute("SELECT material_id, COUNT(*) FROM material_map GROUP BY material_id").fetchall())
    lines.append("Materials by links: " + ", ".join(f"{m} {n}" for m, n in Counter(counts).most_common()))
    never = [m["id"] for m in building_materials.load()["materials"] if m["id"] not in counts]
    lines.append(f"Never found ({len(never)}): {', '.join(never)}")
    aliases = load_aliases()
    seen = set(aliases["wikidata"]) | {x.split()[0] for x in aliases["not_in_list"]["items"]}
    ids = {r[0] for r in conn.execute("SELECT wikidata_id FROM buildings UNION SELECT wikidata_id FROM places")}
    miss = Counter()
    for qid, mats in (wd if wd is not None else wikidata_materials()).items():
        if qid in ids:
            miss.update(f"{m} {lab}" for m, lab in mats if m not in seen)
    lines.append(f"Unreviewed P186 items of records and places ({len(miss)}): "
                 + "; ".join(f"{k} {n}" for k, n in miss.most_common(40)))
    return lines


if __name__ == "__main__":
    if "--report" in sys.argv:
        print("\n".join(report(connect())))
    else:
        run()
