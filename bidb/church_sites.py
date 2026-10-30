"""Outlines that are not the church (roadmap SK5b2c), read by bidb.church_orientation.

A record's outline is the OpenStreetMap way or relation tagged with its Wikidata id (bidb.footprints). For about 200
religious records that is not a church building: the precinct of an abbey or friary (historic=monastery,
archaeological_site, ruins over a field), a churchyard (amenity=grave_yard, landuse=cemetery), or another building
that carries the id (a tower, lych gate, house or barn). The edges of such an outline say nothing about the church's
axis. `site_kind` reads the outline's own tags from the cached Overpass responses; for an outline that is not a
church building, `inner_church` looks for the largest church, chapel or cathedral building mapped inside it
(`fetch_buildings`, Overpass, cached), and when there is none the record is left out of the test.
"""
import glob
import hashlib
import json

from .church_axes import _area, _inside, _metres, _rings
from .config import CACHE_DIR

# building=* values taken as the church itself (ruins: most ruined churches are mapped so; yes: untyped buildings)
CHURCH_BUILDINGS = {"church", "chapel", "cathedral", "ruins", "yes", "religious", "basilica", "place_of_worship",
                    "monastery", "priory", "mosque", "synagogue", "historic", "heritage", "church;yes",
                    "university_chapel", "abbey", "temple", "convent", "friary", "shrine", "chapel;yes"}
BATCH = 40          # outlines per Overpass query


def outline_tags():
    """{qid: tags of the OSM element its outline came from}: the first element per id in the cached responses of
    bidb.footprints.outlines, as that function keeps it."""
    out = {}
    for path in sorted(glob.glob(str(CACHE_DIR / "footprints" / "fp_*.json"))):
        try:
            elements = json.loads(open(path).read()).get("elements", [])
        except ValueError:
            continue
        for el in elements:
            qid = el.get("tags", {}).get("wikidata")
            if qid and qid not in out and (el.get("geometry") or el.get("members")):
                out[qid] = el.get("tags", {})
    return out


def site_kind(tags):
    """None when the outline is a church building (or its tags are unknown); else what it is: 'site' (no building
    tag: precinct, churchyard, ruin site) or 'other building' (a tower, house, barn...)."""
    if tags is None:
        return None
    b = (tags.get("building") or "").lower()
    if not b or b == "no":
        return "site"
    return None if b in CHURCH_BUILDINGS else "other building"


def _box(geom, pad=0.0003):
    pts = [p for r in _rings(geom) for p in r]
    return (min(p[1] for p in pts) - pad, min(p[0] for p in pts) - pad,
            max(p[1] for p in pts) + pad, max(p[0] for p in pts) + pad)


def fetch_buildings(outlines, log=print):
    """Church, chapel and cathedral buildings (also any building tagged as a place of worship or historic=church)
    within the boxes of the given outlines ({id: geom}): [{geom, tags}] (Overpass, cached per batch)."""
    from .footprints import _geometry, _overpass
    ids = sorted(outlines)
    out = []
    for n in range(0, len(ids), BATCH):
        boxes = ["(%.5f,%.5f,%.5f,%.5f)" % _box(outlines[i]) for i in ids[n:n + BATCH]]
        filters = ('["building"~"^(church|chapel|cathedral)$"]', '["building"]["amenity"="place_of_worship"]',
                   '["building"]["historic"="church"]')
        q = "[out:json][timeout:300];(" + "".join(f"{t}{f}{b};" for b in boxes for f in filters
                                                   for t in ("way", "relation")) + ");out tags geom;"
        name = "church_bodies_" + hashlib.sha1(q.encode()).hexdigest()[:12]
        for el in _overpass(q, name).get("elements", []):
            geom = _geometry(el)
            if geom:
                out.append({"geom": geom, "tags": el.get("tags", {})})
    log(f"{len(out)} church buildings round {len(ids)} outlines that are not a church")
    return out


def inner_church(geom, buildings):
    """The largest of `buildings` whose centre lies inside `geom` and that is not `geom` itself, else None."""
    best, size = None, 0.0
    own = _area(_metres(_rings(geom))[0]) if _rings(geom) else 0.0
    for b in buildings:
        ring = _rings(b["geom"])[0][:-1]
        c = (sum(p[0] for p in ring) / len(ring), sum(p[1] for p in ring) / len(ring))
        if not _inside(c, geom):
            continue
        a = _area(_metres(_rings(b["geom"]))[0])
        if a > size and abs(a - own) > 1:
            best, size = b, a
    return best
