"""Build stage / CLI: fill in the nation of places that have none, from where they are.

    python -m bidb.nation_geo

Wikidata's located-in-administrative-area chain (P131) first; otherwise the bundled county and
council-area outlines (app/static/data/basemap/land.json, Natural Earth
admin-1, each tagged with its country). Irish, Manx and Channel Island areas give their nation
directly; each UK area takes the nation most of the catalogued buildings inside it have (areas never
cross a national border). Where at least 4 of the 7 nearest catalogued buildings within 8 km agree,
their nation wins (the simplified outlines are a few km out along the borders). Points outside every
area (lighthouses, offshore sites) take the nation of the nearest catalogued buildings within 40 km.
"""
import json
import math
import time
from collections import Counter

from .config import ROOT
from .db import connect

COUNTRY_NATION = {"Ireland": "Republic of Ireland", "Isle of Man": "Isle of Man", "Jersey": "Jersey",
                  "Guernsey": "Guernsey"}


def _polygons():
    """[(country, name, bbox, [rings])] for every area."""
    gj = json.loads((ROOT / "app" / "static" / "data" / "basemap" / "land.json").read_text())
    out = []
    for f in gj["features"]:
        g = f["geometry"]
        polys = g["coordinates"] if g["type"] == "MultiPolygon" else [g["coordinates"]]
        rings = [p[0] for p in polys]
        xs = [x for r in rings for x, _ in r]
        ys = [y for r in rings for _, y in r]
        out.append((f["properties"].get("c"), f["properties"].get("n"), (min(xs), min(ys), max(xs), max(ys)), rings))
    return out


def _inside(x, y, ring):
    hit, j = False, len(ring) - 1
    for i in range(len(ring)):
        xi, yi = ring[i]
        xj, yj = ring[j]
        if (yi > y) != (yj > y) and x < (xj - xi) * (y - yi) / (yj - yi) + xi:
            hit = not hit
        j = i
    return hit


def _area_of(polys, lat, lon):
    for k, (_, _, (x0, y0, x1, y1), rings) in enumerate(polys):
        if x0 <= lon <= x1 and y0 <= lat <= y1 and any(_inside(lon, lat, r) for r in rings):
            return k
    return None


class NationFinder:
    """nation(lat, lon) from the area outlines, with buildings as the guide for UK areas."""

    def __init__(self, conn):
        self.polys = _polygons()
        self.buildings = [(lat, lon, n) for lat, lon, n in conn.execute(
            "SELECT lat, lon, nation FROM buildings WHERE lat IS NOT NULL AND nation IS NOT NULL")]
        votes = {}
        for lat, lon, n in self.buildings:
            k = _area_of(self.polys, lat, lon)
            if k is not None:
                votes.setdefault(k, Counter())[n] += 1
        self.area_nation = {}
        for k, (country, _, _, _) in enumerate(self.polys):
            if country in COUNTRY_NATION:
                self.area_nation[k] = COUNTRY_NATION[country]
            elif k in votes:
                self.area_nation[k] = votes[k].most_common(1)[0][0]
        self._grid = {}
        for lat, lon, n in self.buildings:
            self._grid.setdefault((round(lat * 2), round(lon)), []).append((lat, lon, n))

    def nearest(self, lat, lon, km=40, k=5, agree=1):
        cand = [b for dy in (-1, 0, 1) for dx in (-1, 0, 1)
                for b in self._grid.get((round(lat * 2) + dy, round(lon) + dx), [])]
        scale = math.cos(math.radians(lat))
        cand = sorted(((((b[0] - lat) * 111) ** 2 + ((b[1] - lon) * 111 * scale) ** 2) ** 0.5, b[2]) for b in cand)
        near = [n for d, n in cand[:k] if d <= km]
        best = Counter(near).most_common(1)
        return best[0][0] if best and best[0][1] >= agree else None

    def nation(self, lat, lon):
        if lat is None or lon is None:
            return None
        local = self.nearest(lat, lon, km=8, k=7, agree=4)    # the simplified outlines are off by a few km at borders
        if local:
            return local
        k = _area_of(self.polys, lat, lon)
        return self.area_nation.get(k) if k is not None and k in self.area_nation else self.nearest(lat, lon)


def run(log=print):
    t0 = time.time()
    conn = connect()
    conn.execute("PRAGMA busy_timeout = 120000")
    rows = conn.execute("SELECT id, lat, lon, wikidata_id FROM places WHERE (nation IS NULL OR nation = '' "
                        "OR nation = 'Unknown') AND lat IS NOT NULL").fetchall()
    from .wikidata import nations_for                    # Wikidata's administrative areas (P131) first
    by_wd = nations_for({q for *_, q in rows if q})
    log(f"  {len(by_wd)} of {sum(1 for *_, q in rows if q)} from Wikidata's administrative areas")
    finder = NationFinder(conn)
    found = [(n, pid) for pid, lat, lon, q in rows if (n := by_wd.get(q) or finder.nation(lat, lon))]
    conn.executemany("UPDATE places SET nation = ? WHERE id = ?", found)
    conn.commit()
    log(f"[{time.time() - t0:5.0f}s] nations: {len(found)} of {len(rows)} places without one placed "
        f"({', '.join(f'{n} {c}' for n, c in Counter(n for n, _ in found).most_common())})")


if __name__ == "__main__":
    run()
