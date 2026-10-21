"""Building outlines and floor plans: python -m bidb.footprints

- Outlines: OpenStreetMap ways/relations tagged wikidata=<catalogue item> (Overpass API, ODbL),
  stored as simplified GeoJSON in buildings.footprint.
- Floor plans: Wikidata "plan view image" (P3311) files on Wikimedia Commons, else the best file
  in a Commons "Plans of <building>" category (commons_plans), in buildings.plan_image. The GUI can lay a plan over the outline (an approximate fit: plans have
  no georeferencing, so the image is stretched to the outline's bounding box).
"""
import json
import sqlite3
import time

import requests

from .config import CACHE_DIR, DB_PATH, USER_AGENT, require_locations
from . import commons_plans
from .http import sparql

OVERPASS = "https://overpass-api.de/api/interpreter"
CACHE = CACHE_DIR / "footprints"


def _overpass(query, name):
    CACHE.mkdir(parents=True, exist_ok=True)
    path = CACHE / f"{name}.json"
    if path.exists():
        return json.loads(path.read_text())
    for attempt in range(5):
        time.sleep(4 * (attempt + 1))
        r = requests.post(OVERPASS, data={"data": query}, headers={"User-Agent": USER_AGENT}, timeout=400)
        if r.status_code in (429, 502, 503, 504):
            continue
        r.raise_for_status()
        path.write_text(r.text)
        return r.json()
    return {"elements": []}


def _ring_area(ring):
    return abs(sum(x1 * y2 - x2 * y1 for (x1, y1), (x2, y2) in zip(ring, ring[1:]))) / 2


def _geometry(el):
    from app.geo_simplify import join_rings, simplify
    if el["type"] == "way":
        pts = [[g["lon"], g["lat"]] for g in el.get("geometry", [])]
        rings = [pts] if len(pts) >= 4 and pts[0] == pts[-1] else []
    else:
        ways = [[[g["lon"], g["lat"]] for g in m["geometry"]] for m in el.get("members", [])
                if m.get("type") == "way" and m.get("role") in ("outer", "") and m.get("geometry")]
        rings = join_rings(ways)
    if not rings:
        return None
    rings.sort(key=_ring_area, reverse=True)
    geom = {"type": "MultiPolygon", "coordinates": [[r] for r in rings[:20]]}
    return simplify(geom, 0.000008, nd=6)


def outlines(qids, batch=120, log=print):
    out = {}
    ids = sorted(q for q in qids if q.startswith("Q"))
    for n in range(0, len(ids), batch):
        chunk = ids[n:n + batch]
        rx = "^(" + "|".join(chunk) + ")$"
        q = (f'[out:json][timeout:300];(way["wikidata"~"{rx}"](49,-11,61.2,2.2);'
             f'relation["wikidata"~"{rx}"](49,-11,61.2,2.2););out geom;')
        for el in _overpass(q, f"fp_{chunk[0]}_{len(chunk)}").get("elements", []):
            qid = el.get("tags", {}).get("wikidata")
            if qid in out:
                continue
            geom = _geometry(el)
            if geom:
                out[qid] = geom
        if n % (batch * 20) == 0:
            log(f"  outlines: {n}/{len(ids)} items queried, {len(out)} found")
    return out


def plans(qids):
    out = {}
    ids = sorted(q for q in qids if q.startswith("Q"))
    for n in range(0, len(ids), 300):
        values = " ".join("wd:" + q for q in ids[n:n + 300])
        for r in sparql(f"SELECT ?i ?p WHERE {{ VALUES ?i {{ {values} }} ?i wdt:P3311 ?p . }}"):
            from urllib.parse import unquote
            out.setdefault(r["i"]["value"].rsplit("/", 1)[1], unquote(r["p"]["value"].rsplit("/", 1)[1]))
    return out


def run(log=print):
    require_locations()
    conn = sqlite3.connect(DB_PATH, timeout=300)
    ids = [r[0] for r in conn.execute("SELECT id FROM buildings WHERE id LIKE 'Q%'")]
    pl = plans(ids)
    log(f"floor plans (P3311): {len(pl)}")
    extra = commons_plans.plans([q for q in ids if q not in pl], log)
    log(f"floor plans from Commons 'Plans of' categories: {len(extra)}")
    pl.update(extra)
    fp = outlines(ids, log=log)
    log(f"outlines: {len(fp)} of {len(ids)}")
    conn.execute("UPDATE buildings SET footprint = NULL, plan_image = NULL")
    conn.executemany("UPDATE buildings SET plan_image = ? WHERE id = ?", [(v, k) for k, v in pl.items()])
    conn.executemany("UPDATE buildings SET footprint = ? WHERE id = ?",
                     [(json.dumps(v, separators=(",", ":")), k) for k, v in fp.items()])
    conn.commit()


if __name__ == "__main__":
    run()
