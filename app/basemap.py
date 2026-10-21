"""One-off: cut a British Isles coastline GeoJSON out of world-atlas countries-10m TopoJSON.

python -I -m app.basemap <path/to/countries-10m.json>  ->  app/static/data/british_isles.geojson
Used as the map background in the hosted version, where tile servers are blocked.
"""
import json
import sys

from bidb.config import ROOT

IDS = {"826": "United Kingdom", "372": "Ireland", "833": "Isle of Man", "832": "Jersey", "831": "Guernsey"}
OUT = ROOT / "app" / "static" / "data" / "british_isles.geojson"


def decode(topo):
    sx, sy = topo["transform"]["scale"]
    tx, ty = topo["transform"]["translate"]
    arcs = []
    for arc in topo["arcs"]:
        x = y = 0
        pts = []
        for dx, dy in arc:
            x, y = x + dx, y + dy
            pts.append((round(x * sx + tx, 3), round(y * sy + ty, 3)))
        arcs.append(pts)

    def ring(idx):
        pts = []
        for i in idx:
            seg = arcs[i] if i >= 0 else arcs[~i][::-1]
            pts.extend(seg if not pts else seg[1:])
        out = [pts[0]]
        for p in pts[1:]:
            if p != out[-1]:
                out.append(p)
        return out
    return ring


def main(src):
    topo = json.load(open(src))
    ring = decode(topo)
    feats = []
    for g in topo["objects"]["countries"]["geometries"]:
        if str(g.get("id")) not in IDS:
            continue
        polys = g["arcs"] if g["type"] == "MultiPolygon" else [g["arcs"]]
        coords = [[ring(r) for r in poly] for poly in polys]
        feats.append({"type": "Feature", "properties": {"name": IDS[str(g["id"])]},
                      "geometry": {"type": "MultiPolygon", "coordinates": coords}})
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({"type": "FeatureCollection", "features": feats}, separators=(",", ":")))
    print(f"wrote {len(feats)} features, {OUT.stat().st_size / 1e3:.0f} kB -> {OUT}")


if __name__ == "__main__":
    main(sys.argv[1])
