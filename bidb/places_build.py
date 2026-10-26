"""Build places of interest, people and their links: python -m bidb.places_build

Runs after bidb.build (it reads the buildings table). Stages:
  Wikidata place kinds -> objects in buildings -> history events -> official registers
  (merged with Wikidata places that describe the same site) -> people -> SQLite.
"""
import json
import re
import time

from . import (enrich, history_geo, land, objects_in, openplaques, people, place_fetch, places_db,
               references, registers, typology)
from .classify import period_for, regional_period
from .config import require_locations
from . import wikidata as wd
from .db import connect
from .place_kinds import KINDS, in_box
from .place_records import blank, from_wikidata, nation_from_country
from .records import commons_thumb

STOP = {"the", "of", "and", "at", "on", "in", "a", "battle", "site", "st", "saint", "s", "near",
        "e", "w", "n", "ne", "nw", "se", "sw", "m"}


def log(msg, t0=[time.time()]):
    print(f"[{time.time() - t0[0]:6.0f}s] {msg}", flush=True)


def _tokens(name):
    return {t for t in re.findall(r"[a-z]+", (name or "").lower()) if t not in STOP and len(t) > 2}


class Grid:
    """Points on a 0.02° grid for 'is there already something here?' checks."""
    def __init__(self):
        self.cells = {}

    def add(self, rec):
        if rec.get("lat") is not None:
            self.cells.setdefault((round(rec["lat"] / 0.02), round(rec["lon"] / 0.02)), []).append(rec)

    def near(self, lat, lon, km):
        cy, cx, out = round(lat / 0.02), round(lon / 0.02), []
        span = int(km / 1.3) + 1
        for dy in range(-span, span + 1):
            for dx in range(-span, span + 1):
                for r in self.cells.get((cy + dy, cx + dx), []):
                    d = wd_dist(lat, lon, r["lat"], r["lon"])
                    if d <= km:
                        out.append((d, r))
        return sorted(out, key=lambda x: x[0])


def wd_dist(a, b, c, d):
    from .db import dist_km
    return dist_km(a, b, c, d)


def wikidata_places(building_ids):
    kinds, base = {}, {}
    for kind in KINDS:
        items = place_fetch.base_items(kind, log)
        if kind["geo"] != "country":          # box / location / find-spot: keep only British Isles land
            km = 40 if kind["group"] == "Battles & sieges" else 15   # naval battles are offshore
            items = {q: r for q, r in items.items() if land.near_land(r["lat"], r["lon"], km)}
        for q, row in items.items():
            if q not in building_ids and q not in base:
                base[q], kinds[q] = row, kind
    log(f"wikidata places: {len(base)} items")
    det = place_fetch.details(base)
    dates = {}
    for kind in KINDS:
        qids = [q for q, k in kinds.items() if k is kind]
        dates.update(place_fetch.dates(qids, kind["date"]))
    extra = place_fetch.extras(base)
    keep = {q for q in base if kinds[q].get("require") != "media"
            or det.get(q, {}).get("image") or det.get(q, {}).get("title")}
    uk = [q for q in keep if base[q]["country"] in (None, "Q145")]
    nations = wd.nations_for(uk)
    intros = enrich.wikipedia_intros([det[q]["title"] for q in keep if det.get(q, {}).get("title")])
    log(f"wikidata places kept: {len(keep)}; nations {len(nations)}; intros {len(intros)}")
    out = []
    for q in keep:
        d = det.get(q, {})
        nation = nation_from_country(base[q]["country"]) or nations.get(q)
        out.append(from_wikidata(q, kinds[q]["key"], base[q], d, dates.get(q), extra.get(q),
                                 nation, intros.get(d.get("title"))))
    return out


def object_places(buildings):
    out = []
    for o in objects_in.objects_in(list(buildings), log):
        b = buildings[o["building_id"]]
        out.append(blank(o["id"], "object", o["name"], type=o["type"], description=o["description"],
                         lat=b["lat"], lon=b["lon"], nation=b["nation"], locality=b["name"],
                         image_thumb=commons_thumb(o["image"], 400) if o["image"] else None,
                         wikipedia_title=o["title"], wikidata_id=o["id"], source="Wikidata",
                         building_id=o["building_id"]))
    return out


def event_places():
    hist = json.loads(history_geo.HISTORY.read_text())["events"]
    geo = history_geo.locate_events(log)
    out = []
    for e in hist:
        g = geo.get(e["title"])
        if g:
            out.append(blank("ev-" + history_geo.slug(e["title"]), "event", e["title"],
                             type=e.get("kind"), description=e.get("description"),
                             year_start=e["year"], date_text=e.get("date_text"),
                             lat=g["lat"], lon=g["lon"], locality=g["place"], url=e.get("source"),
                             source="History timeline", extra=json.dumps({"region": e.get("region")})))
    return out


def register_places(grid):
    """Register records; ones that duplicate an existing place lend it their official link."""
    out, merged = [], 0
    for fn in registers.ALL:
        try:
            recs = fn(log)
        except Exception as exc:                       # one register down should not stop the build
            log(f"  register {fn.__name__} failed: {exc}")
            continue
        for r in recs:
            if not in_box(r.get("lat"), r.get("lon")):
                continue
            radius = 0.15 if r["kind"] == "scheduled" else 2.5
            toks = _tokens(r["name"])
            dup = None
            for d, other in grid.near(r["lat"], r["lon"], radius):
                if d < 0.05 or toks & _tokens(other.get("name")):
                    dup = other
                    break
            r["extra"] = json.dumps({"register_ref": r.pop("extra_ref", None)})
            if dup is not None:
                merged += 1
                if "kind" in dup and not dup.get("url"):
                    dup["url"] = r.get("url")
                    dup["designation"] = "; ".join(x for x in (dup.get("designation"), r.get("designation")) if x)
                continue
            out.append(r)
            grid.add(r)
    log(f"register places: {len(out)} added, {merged} merged into existing records")
    return out


def plaque_places(grid):
    """Open Plaques plaques; one within 25 m of a Wikidata plaque lends it its Open Plaques link."""
    out, merged = [], 0
    try:
        recs = openplaques.plaques(log)
    except Exception as exc:                           # the API has had long outages
        log(f"  open plaques failed: {exc}")
        return out
    for r in recs:
        if not in_box(r["lat"], r["lon"]):
            continue
        dup = next((o for d, o in grid.near(r["lat"], r["lon"], 0.025) if o.get("kind") == "plaque"), None)
        if dup is not None:
            merged += 1
            dup["url"] = dup.get("url") or r["url"]
            continue
        out.append(r)
    log(f"open plaques: {len(out)} added, {merged} merged into Wikidata plaques")
    return out


def estimate_dates(places):
    """Undated monuments get the accepted date range for their type (labelled as an estimate)."""
    n = 0
    for p in places:
        if p.get("year_start") is None and p["kind_group"] == "Archaeological sites":
            # Irish SMR names are "class, townland": a townland called Rath or Cashel is no ringfort
            name = None if p["id"].startswith("iesmr-") else p.get("name")
            est = typology.estimate([p.get("type") or ""], name)
            if est:
                year, text, _ = est
                p.update(year_start=year, date_text=f"{text}, estimate", period=period_for(year))
                n += 1
    log(f"type-based date estimates for {n} places")


def people_stage(target_ids):
    links = people.find_links(target_ids, log)
    persons, links = people.prepare(links, log)
    log(f"people: {len(persons)} people, {len(links)} links")
    return persons, links


def run():
    require_locations()
    conn = connect()
    buildings = {r["id"]: dict(r) for r in conn.execute(
        "SELECT id, name, lat, lon, nation FROM buildings")}
    places = wikidata_places(set(buildings))
    places += object_places({k: v for k, v in buildings.items() if v["lat"] is not None})
    places += event_places()
    grid = Grid()
    for rec in list(buildings.values()) + places:
        grid.add(rec)
    places += register_places(grid)
    places += plaque_places(grid)
    estimate_dates(places)
    unnamed = {p["id"]: p for p in places if p["name"] == p["id"] or not p["name"]}
    for q, name in wd.labels_any_language([q for q in unnamed if q.startswith("Q")]).items():
        unnamed[q]["name"] = name
    seen, unique = set(), []
    for p in places:
        if p["id"] not in seen and land.near_land(p["lat"], p["lon"], 60):
            seen.add(p["id"])
            unique.append(p)
    refs = references.wikidata_references([p["id"] for p in unique], log, references.PLACE_PROPS)
    for p in unique:
        if refs.get(p["id"]):
            p["refs"] = json.dumps(refs[p["id"]], ensure_ascii=False)
    log(f"places with Wikidata references: {len(refs)}")
    targets = set(buildings) | {p["id"] for p in unique if p["id"].startswith("Q") and p["kind"] != "object"}
    persons, links = people_stage(targets)
    kinds = {p["id"]: "place" for p in unique}
    refs = people.link_references(links, log)
    log(f"people links with a Wikidata reference: {len(refs)} of {len(links)}")
    link_rows = [(p, t, "place" if t in kinds else "building", role, refs.get((p, t, role)))
                 for p, t, role in links]
    for p in unique:
        p["period"] = regional_period(p.get("period"), p.get("nation"))
    places_db.write(conn, unique, persons, link_rows)
    conn.close()
    counts = {}
    for p in unique:
        counts[p["kind_group"]] = counts.get(p["kind_group"], 0) + 1
    log(f"wrote {len(unique)} places {counts}")


if __name__ == "__main__":
    run()
