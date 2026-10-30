"""Which buildings and structures could become 3D models (roadmap SH4 survey): `python -m bidb.model_survey`.

Four checks over the catalogue, written to `data/model_survey.json`:
- `osm_3d`: records whose OpenStreetMap object (matched by its wikidata tag) carries a height, roof shape or number
  of levels, and how many building parts lie inside them (one isles-wide Overpass query each);
- `lidar`: records with an OSM footprint by nation, and a sample of English records tested against the
  Environment Agency's 1 m first-return surface model (open web service);
- `scans`: notable records with a downloadable, openly licensed 3D model on Sketchfab (public search API;
  downloading needs an account, so these are pointers only);
- `inventories`: Royal Commission inventories published before 1976 (Crown copyright expired) on the Internet Archive.
"""
import json
import random
import sqlite3
import time

import requests

from .config import DATA_DIR, USER_AGENT, db_path
from .http import request_json
from .model_geometry import OVERPASS

OUT = DATA_DIR / "model_survey.json"
BOX = "(49.8,-11.0,61.0,2.2)"
DSM = ("https://environment.data.gov.uk/spatialdata/lidar-composite-digital-surface-model-first-return-dsm-1m/wcs",
       "df4e3ec3-315e-48aa-aaaf-b5ae74d7b2bb__Lidar_Composite_Elevation_FZ_DSM_1m")
OPEN = {"CC Attribution", "CC Attribution-ShareAlike", "CC0 Public Domain"}     # Sketchfab licence labels


def osm_3d(conn):
    q = (f'[out:json][timeout:900];(way[wikidata][~"^(height|roof:shape|building:levels)$"~"."]{BOX};'
         f'relation[wikidata][~"^(height|roof:shape|building:levels)$"~"."]{BOX};);out tags;')
    res = request_json(OVERPASS, data={"data": q}, method="POST", min_interval=2)
    ids = {r[0] for r in conn.execute("select id from buildings")}
    rows = {}
    for e in res["elements"]:
        t = e.get("tags", {})
        qid = t.get("wikidata")
        if qid in ids:
            rows[qid] = {k: t[k] for k in ("height", "roof:shape", "building:levels", "building") if k in t}
    names = dict(conn.execute("select id, name from buildings"))
    tall = sorted(rows, key=lambda q: -float(str(rows[q].get("height", "0")).split()[0].replace("m", "") or 0)
                  if str(rows[q].get("height", "0")).split()[0].replace("m", "").replace(".", "", 1).isdigit() else 0)
    return {"count": len(rows), "with_height": sum("height" in v for v in rows.values()),
            "with_roof_shape": sum("roof:shape" in v for v in rows.values()),
            "examples": [{"id": q, "name": names[q], **rows[q]} for q in tall[:40]], "ids": sorted(rows)}


def dsm_covered(lat, lon):
    """True if the EA first-return DSM has values at a point (a 4 m square), False if not, None on failure."""
    from . import osgrid
    from .stonehenge_sources import read_tiff
    e, n = osgrid.to_en(lat, lon)
    params = {"service": "WCS", "version": "2.0.1", "request": "GetCoverage", "CoverageId": DSM[1],
              "format": "image/tiff", "subset": [f"E({round(e) - 2},{round(e) + 2})", f"N({round(n) - 2},{round(n) + 2})"]}
    try:
        r = requests.get(DSM[0], params=params, timeout=60, headers={"User-Agent": USER_AGENT})
        if r.status_code != 200 or r.content[:2] not in (b"II", b"MM"):
            return False
        vals = [v for row in read_tiff(r.content) for v in row]
        return any(-100 < v < 2000 for v in vals)
    except Exception:
        return None


def lidar(conn, sample=40):
    by = dict(conn.execute("select coalesce(nation, '?'), count(*) from buildings where footprint is not null "
                           "and footprint != '' group by nation"))
    eng = conn.execute("select id, name, lat, lon from buildings where nation = 'England' and footprint is not null "
                       "and footprint != '' and lat is not null").fetchall()
    random.seed(1)
    picks = random.sample(eng, min(sample, len(eng)))
    tested = [(i, n, dsm_covered(la, lo)) for i, n, la, lo in picks]
    ok = [t for t in tested if t[2]]
    return {"footprints_by_nation": by, "england_sample": len(tested), "england_covered": len(ok),
            "england_failed": sum(t[2] is None for t in tested),
            "missing": [{"id": i, "name": n} for i, n, c in tested if c is False]}


def scans(conn, limit=80):
    rows = conn.execute("select id, name from buildings where landmark = 1 or oldest_of_type is not null "
                        "order by (landmark = 1) desc, year_start limit ?", (limit,)).fetchall()
    out = []
    for qid, name in rows:
        try:
            r = requests.get("https://api.sketchfab.com/v3/search", timeout=40, headers={"User-Agent": USER_AGENT},
                             params={"type": "models", "q": name, "downloadable": "true", "count": 24})
            res = r.json().get("results", []) if r.status_code == 200 else []
        except (requests.RequestException, ValueError):
            res = []
        hits = [{"name": m["name"], "uri": m.get("viewerUrl"), "licence": (m.get("license") or {}).get("label"),
                 "user": (m.get("user") or {}).get("username")} for m in res
                if (m.get("license") or {}).get("label") in OPEN and name.split(",")[0].split("(")[0].strip().lower()[:12] in m["name"].lower()]
        if hits:
            out.append({"id": qid, "name": name, "models": hits[:5]})
        time.sleep(1.2)
    return {"searched": len(rows), "with_open_models": len(out), "records": out,
            "note": "Downloadable under CC BY, CC BY-SA or CC0 on Sketchfab; downloading needs a Sketchfab account; "
                    "many are artists' models, not surveys, so each needs looking at."}


def inventories():
    res = requests.get("https://archive.org/advancedsearch.php", timeout=60, headers={"User-Agent": USER_AGENT}, params={
        "q": 'title:(inventory) AND (title:("ancient and historical monuments") OR title:("historical monuments")) AND year:[1900 TO 1975]',
        "fl[]": ["identifier", "title", "year"], "rows": 200, "output": "json"}).json()
    docs = res.get("response", {}).get("docs", [])
    return {"count": len(docs), "items": sorted(({"id": d["identifier"], "title": d.get("title"), "year": d.get("year")}
                                                 for d in docs), key=lambda d: str(d["year"]))}


def run(log=print):
    conn = sqlite3.connect(db_path())
    out = {"date": time.strftime("%Y-%m-%d")}
    for key, fn in (("osm_3d", lambda: osm_3d(conn)), ("lidar", lambda: lidar(conn)), ("scans", lambda: scans(conn)),
                    ("inventories", inventories)):
        try:
            out[key] = fn()
        except Exception as exc:                       # one check failing does not stop the others
            out[key] = {"error": str(exc)}
        log(key, {k: v for k, v in out[key].items() if not isinstance(v, (list, dict))})
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1) + "\n")
    return out


if __name__ == "__main__":
    run()
