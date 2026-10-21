"""Detailed offline-map layers in 1-degree tiles:
    python -m app.basemap_tiled minor     -> app/static/data/basemap/minor/
    python -m app.basemap_tiled streams   -> app/static/data/basemap/streams/

OpenStreetMap ways (minor roads: secondary and tertiary, i.e. B roads, R roads in Ireland and the
like; streams: named waterway=stream) are fetched per 1-degree tile from the Overpass API (cached in
<cache>/basemap/), simplified, joined end to end and written as one file per tile
(`<lat>_<lon>.json`, {"r": [[kind, label, [x0, y0, dx, dy, ...]], ...]} in 1/10000 degree) plus
`index.json` listing the tiles. The map loads only the tiles in view, and only when zoomed in.
"""
import json
import sys
import time

from bidb.config import ROOT
from bidb.land import near_land

from . import basemap_sources as src
from .geo_simplify import simplify

BASE = ROOT / "app" / "static" / "data" / "basemap"
TOLERANCE = 0.0002          # degrees (~15–20 m): enough detail for zoom 9–14
LAYERS = {
    "minor": {"query": 'way[highway~"^(secondary|tertiary)(_link)?$"]', "cache": "minor_roads",
              "kind": lambda tags: (tags.get("highway") or "t")[0],          # "s" / "t"
              "label": lambda tags: " ".join(x for x in (tags.get("ref"), tags.get("name")) if x)},
    "streams": {"query": "way[waterway=stream][name]", "cache": "streams",
                "kind": lambda tags: "w", "label": lambda tags: tags.get("name", "")},
    # lakes, lochs and reservoirs (closed rings, drawn filled; relations give their outer ways)
    "lakes": {"query": 'nwr[natural=water][name][water!~"^(river|canal|stream|ditch|wastewater|moat|basin)$"]',
              "cache": "lakes", "kind": lambda tags: "l", "label": lambda tags: tags.get("name", "")},
    # four layers from one query per tile: walking routes, cycle routes, Roman roads, buried rivers
    "routes": {"query": ('(relation[route=hiking][network~"^(rwn|lwn)$"]{bbox};'
                         'relation[route=bicycle][network~"^(ncn|rcn)$"]{bbox};way[historic=roman_road]{bbox};'
                         'way[waterway~"^(river|stream)$"][tunnel~"^(culvert|yes|flooded)$"][name]{bbox};)'),
               "cache": "routes", "members": "all",
               "split": lambda tags: ("cycling" if tags.get("route") == "bicycle" else "walking" if tags.get("route")
                                      else "roman" if tags.get("historic") == "roman_road" else "buried"),
               "kind": lambda tags: ({"ncn": "n", "rcn": "r"}.get(tags.get("network"), "w") if tags.get("route")
                                     else "R" if tags.get("historic") == "roman_road" else "b"),
               "label": lambda tags: " ".join(x for x in (tags.get("ref") if tags.get("route") == "bicycle" else None,
                                                          tags.get("name")) if x)},
}


def log(msg, t0=[time.time()]):
    print(f"[{time.time() - t0[0]:5.0f}s] {msg}", flush=True)


def land_tiles():
    """(lat, lon) south-west corners of 1-degree tiles in the British Isles box that touch land."""
    w, s, e, n = src.BOX
    out = []
    for lat in range(int(s), int(n) + 1):
        for lon in range(int(w) - 1, int(e) + 1):
            probe = [(lat + i / 4, lon + j / 4) for i in range(5) for j in range(5)]
            if any(near_land(y, x, 5) for y, x in probe):
                out.append((lat, lon))
    return out


def fetch_tile(layer, lat, lon):
    query, box = LAYERS[layer]["query"], f"({lat},{lon},{lat + 1},{lon + 1})"
    # relations (big lakes, routes) need "out geom" with the body: "out tags geom" drops their members
    # route relations span the country: clip their geometry to the tile ("out geom(bbox)")
    out = f"out geom{box};" if LAYERS[layer].get("members") else "out tags geom;"
    q = f"[out:json][timeout:300];{query.format(bbox=box) if '{bbox}' in query else query + box};{out}"
    return src.overpass(q, f"{LAYERS[layer]['cache']}_{lat}_{lon}", pause=3).get("elements", [])


def relations_tile(layer, lat, lon):
    """Lakes mapped as multipolygon relations, fetched again with their members (the first lakes run
    asked for "out tags geom", which leaves relations without members; ways are cached already)."""
    if layer != "lakes":
        return []
    q = (f'[out:json][timeout:300];relation[natural=water][name][water!~"^(river|canal|stream|ditch|wastewater|moat|basin)$"]'
         f"({lat},{lon},{lat + 1},{lon + 1});out geom;")
    return src.overpass(q, f"lakes_rel_{lat}_{lon}", pause=3).get("elements", [])


def _join(lines):
    """Chain lines that meet end to end (OSM splits one road into many ways)."""
    lines = [l for l in lines if len(l) > 1]
    by_end = {}
    for i, l in enumerate(lines):
        by_end.setdefault(tuple(l[0]), []).append(i)
        by_end.setdefault(tuple(l[-1]), []).append(i)
    used, out = set(), []
    for i in range(len(lines)):
        if i in used:
            continue
        used.add(i)
        chain = list(lines[i])
        for forward in (True, False):
            while True:
                end = tuple(chain[-1] if forward else chain[0])
                nxt = next((j for j in by_end.get(end, []) if j not in used), None)
                if nxt is None:
                    break
                used.add(nxt)
                l = lines[nxt]
                if forward:
                    chain += (l if tuple(l[0]) == end else l[::-1])[1:]
                else:
                    chain = (l if tuple(l[-1]) == end else l[::-1])[:-1] + chain
        out.append(chain)
    return out


def _encode(line):
    """[[lon, lat], ...] -> flat integers in 1/10000 degree: first point absolute, then steps."""
    ints = [(round(x * 1e4), round(y * 1e4)) for x, y in line]
    flat, prev = list(ints[0]), ints[0]
    for p in ints[1:]:
        if p != prev:
            flat += [p[0] - prev[0], p[1] - prev[1]]
            prev = p
    return flat


def build(layer):
    spec, out_dir = LAYERS[layer], BASE / layer
    tiles, seen, groups = land_tiles(), set(), {}
    log(f"{layer}: {len(tiles)} land tiles")
    for n, (lat, lon) in enumerate(tiles, 1):
        for w in relations_tile(layer, lat, lon) + fetch_tile(layer, lat, lon):   # relations with members first
            key_id = (w.get("type"), w["id"])
            if key_id in seen:
                continue
            seen.add(key_id)
            if w.get("type") == "relation":   # multipolygon: outer rings; route: all its ways
                outer = [part for m in w.get("members", [])
                         if (spec.get("members") == "all" or m.get("role") == "outer") and m.get("geometry")
                         for part in _pieces(m["geometry"])]
                parts = _join(outer)
            elif w.get("geometry"):
                parts = _pieces(w["geometry"])
            else:
                continue
            tags = w.get("tags", {})
            target = groups.setdefault(spec["split"](tags), {}) if "split" in spec else groups
            for pts in parts:
                _add(target, spec, tags, pts)
        if n % 10 == 0:
            log(f"  {n}/{len(tiles)} tiles fetched, {len(seen)} ways")
    if "split" in spec:
        for name, g in groups.items():
            _write(name, BASE / name, g, seen)
    else:
        _write(layer, out_dir, groups, seen)


def _pieces(geometry):
    """Overpass geometry -> lines of [lon, lat]; clipped geometry ("out geom(bbox)") has gaps (null)."""
    out, cur = [], []
    for g in geometry:
        if g is None:
            if len(cur) > 1:
                out.append(cur)
            cur = []
        else:
            cur.append([g["lon"], g["lat"]])
    if len(cur) > 1:
        out.append(cur)
    return out


def _add(groups, spec, tags, pts):
    """Simplify one line or ring and file it under the tile of its middle point."""
    if len(pts) < 2:
        return
    mid = pts[len(pts) // 2]
    if not near_land(mid[1], mid[0], 2):        # the box also covers northern France
        return
    geom = simplify({"type": "LineString", "coordinates": pts}, TOLERANCE)
    if not geom:
        return
    key = f"{int(mid[1] // 1)}_{int(mid[0] // 1)}"
    groups.setdefault(key, {}).setdefault((spec["kind"](tags), spec["label"](tags)), []).append(geom["coordinates"])


def _write(layer, out_dir, groups, seen):
    out_dir.mkdir(parents=True, exist_ok=True)
    for old in out_dir.glob("*.json"):
        old.unlink()
    index, total = {}, 0
    for key, by_way in sorted(groups.items()):
        rows = [[kind, label, _encode(line)] for (kind, label), lines in by_way.items()
                for line in _join(lines)]
        text = json.dumps({"r": rows}, ensure_ascii=False, separators=(",", ":"))
        (out_dir / f"{key}.json").write_text(text)
        index[key] = len(rows)
        total += len(text)
    (out_dir / "index.json").write_text(json.dumps(index, separators=(",", ":")))
    log(f"{layer}: {len(seen)} OSM ways -> {sum(index.values())} lines in {len(index)} tiles, {total / 1e6:.1f} MB")


KEEP_TAGS = ("highway", "ref", "name", "waterway", "natural", "water")


def slim_cache(layer, log=print):
    """Rewrite a layer's cached Overpass responses with only what build() reads (same format)."""
    before = after = 0
    for path in src.CACHE.glob(f"osm_{LAYERS[layer]['cache']}_*.json"):
        data = json.loads(path.read_text())
        before += path.stat().st_size
        geo = lambda g: [{"lat": round(p["lat"], 5), "lon": round(p["lon"], 5)} for p in g]
        els = []
        for e in data.get("elements", []):
            s = {"type": e.get("type"), "id": e["id"], "tags": {k: v for k, v in e.get("tags", {}).items() if k in KEEP_TAGS}}
            if e.get("geometry"):
                s["geometry"] = geo(e["geometry"])
            if e.get("members"):
                s["members"] = [{"role": m.get("role"), "geometry": geo(m["geometry"])} for m in e["members"]
                                if m.get("geometry")]
            els.append(s)
        path.write_text(json.dumps({"elements": els}, separators=(",", ":")))
        after += path.stat().st_size
    log(f"{layer}: cache {before / 1e6:.0f} MB -> {after / 1e6:.0f} MB")


if __name__ == "__main__":
    for name in sys.argv[1:] or LAYERS:
        build(name)
