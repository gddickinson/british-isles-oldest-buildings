"""Build stage / CLI: old recorded forms of Welsh place names (List of Historic Place Names of Wales, RCAHMW, OGL).

    python -m bidb.welsh_names            fetch (cached) and link -> tables old_names, old_name_links
    python -m bidb.welsh_names <id>       the forms shown for one record

The List records every form of a place name found in maps, charters and surveys, with the date of the source.
Its ~11,500 forms that belong to a settlement's headname (e.g. "Abbey Cwmhir / Abaty Cwm-hir") are grouped by
headname; a record in Wales is linked to the headname of its town (Wikidata, as for pronunciations), of a part of its
locality or of its own name, when that headname lies within 10 km of it. Detail views list the forms oldest first.
"""
import json
import math
import re
import sys
import time
import unicodedata

from .osgrid import to_latlon

URL = "https://datamap.gov.wales/geoserver/ows"
PARAMS = {"service": "WFS", "version": "2.0.0", "request": "GetFeature", "outputFormat": "csv", "count": "50000",
          "typeNames": "geonode:rcahmw_historicplacenames_wales_recordednames", "cql_filter": "prife_hnme IS NOT NULL",
          "propertyName": "enw_name,discy_pdes,blwgyn_eye,prife_hnme,cyfgr_grrf,prim_srce"}
ATTRIBUTION = ("List of Historic Place Names of Wales, Royal Commission on the Ancient and Historical Monuments of "
               "Wales (RCAHMW), Open Government Licence v3.0.")
REACH_KM = 10
SCHEMA = """CREATE TABLE old_names (headname TEXT, form TEXT, year INTEGER, date_text TEXT, source TEXT);
            CREATE INDEX old_names_head ON old_names (headname);
            CREATE TABLE old_name_links (record_id TEXT PRIMARY KEY, headname TEXT)"""


def fold(text):
    t = unicodedata.normalize("NFD", (text or "").lower())
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9 ]", " ", "".join(c for c in t if not unicodedata.combining(c)))).strip()


def _csv(text):
    import csv
    import io
    return list(csv.DictReader(io.StringIO(text.lstrip("﻿"))))


def fetch():
    from .http import request_json
    return request_json(URL, params=PARAMS, extract=_csv)


def headnames(rows):
    """{headname: {"names": {folded name parts}, "lat", "lon", "forms": [(form, year, date text, source)]}}."""
    out = {}
    for r in rows:
        head = (r.get("prife_hnme") or "").strip()
        if not head:
            continue
        h = out.setdefault(head, {"names": {fold(p) for p in head.split("/") if fold(p)}, "points": [], "forms": []})
        try:
            year = int(r.get("blwgyn_eye") or "")
        except ValueError:
            year = None
        h["forms"].append(((r.get("enw_name") or "").strip(), year, (r.get("discy_pdes") or "").strip() or None,
                           (r.get("prim_srce") or "").strip() or None))
        try:
            h["points"].append(to_latlon(r.get("cyfgr_grrf") or ""))
        except (ValueError, TypeError, KeyError):
            pass
    for h in out.values():
        pts = [p for p in h.pop("points") if p]
        h["lat"], h["lon"] = (sorted(p[0] for p in pts)[len(pts) // 2], sorted(p[1] for p in pts)[len(pts) // 2]) \
            if pts else (None, None)
    return out


def _km(a, b, c, d):
    return math.hypot((a - c) * 111.2, (b - d) * 111.2 * math.cos(math.radians(a)))


def link(conn, heads):
    """{record id: headname} for catalogue buildings and places in Wales."""
    by_name = {}
    for head, h in heads.items():
        for n in h["names"]:
            by_name.setdefault(n, []).append(head)
    towns = dict(conn.execute("SELECT record_id, town FROM pron_towns")) \
        if conn.execute("SELECT 1 FROM sqlite_master WHERE name = 'pron_towns'").fetchone() else {}
    rows = conn.execute("SELECT id, name, locality, lat, lon FROM buildings WHERE nation = 'Wales' AND lat IS NOT NULL "
                        "UNION ALL SELECT id, name, locality, lat, lon FROM places WHERE nation = 'Wales' AND lat IS NOT NULL")
    out = {}
    for rid, name, locality, lat, lon in rows:
        tries = [towns.get(rid), *(locality or "").split(","), name]
        for t in tries:
            best = [(_km(lat, lon, heads[hd]["lat"], heads[hd]["lon"]), hd) for hd in by_name.get(fold(t), [])
                    if heads[hd]["lat"] is not None]
            best = [b for b in best if b[0] <= REACH_KM]
            if best:
                out[rid] = min(best)[1]
                break
    return out


def run(log=print):
    from .db import connect
    t0 = time.time()
    heads = headnames(fetch())
    conn = connect()
    conn.execute("PRAGMA busy_timeout = 120000")
    links = link(conn, heads)
    used = set(links.values())
    conn.executescript("DROP TABLE IF EXISTS old_names; DROP TABLE IF EXISTS old_name_links;" + SCHEMA)
    conn.executemany("INSERT INTO old_names VALUES (?, ?, ?, ?, ?)",
                     [(hd, *f) for hd in used for f in heads[hd]["forms"] if f[0]])
    conn.executemany("INSERT INTO old_name_links VALUES (?, ?)", links.items())
    conn.commit()
    log(f"[{time.time() - t0:5.0f}s] {len(heads)} headnames; {len(links)} records linked to {len(used)} of them")


def for_record(conn, rid, limit=12):
    """{"headname", "forms": [{form, year, date_text, source}] oldest first, "total"} or None."""
    if not conn.execute("SELECT 1 FROM sqlite_master WHERE name = 'old_name_links'").fetchone():
        return None
    row = conn.execute("SELECT headname FROM old_name_links WHERE record_id = ?", (rid,)).fetchone()
    if not row:
        return None
    forms, seen = [], set()
    for form, year, text, src in conn.execute("SELECT form, year, date_text, source FROM old_names WHERE headname = ? "
                                              "ORDER BY year IS NULL, year, form", (row[0],)):
        if fold(form) not in seen:                 # each spelling once, at its earliest
            seen.add(fold(form))
            forms.append({"form": form, "year": year, "date_text": text, "source": src})
    return {"headname": row[0], "forms": forms[:limit], "total": len(forms)}


if __name__ == "__main__":
    if sys.argv[1:]:
        from .db import connect
        print(json.dumps(for_record(connect(), sys.argv[1]), indent=1, ensure_ascii=False))
    else:
        run()
