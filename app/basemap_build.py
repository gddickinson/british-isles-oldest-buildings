"""Build the offline map layers: python -m app.basemap_build -> app/static/data/basemap/*.json

Layers (each its own file, loaded only when switched on):
  land       British Isles counties/council areas (fill + borders) and neighbouring land
  roads      major roads (Natural Earth; motorway/expressway, primary, secondary, ferries)
  rail       railways (Natural Earth)
  rivers     named rivers (OpenStreetMap, merged by name and area) and lakes (Natural Earth)
  parks      national parks, AONBs / National Landscapes (OpenStreetMap), National Scenic Areas (Scottish
             Government, OGL)
  towns      cities, towns and villages as [name, lat, lon, tier, population] (GeoNames)
  landscape  hills, ranges, forests, moors, glens, islands, lochs, bays, headlands (GeoNames, NE)
  airports   (Natural Earth)
Sources and licences are written to basemap/SOURCES.md.
"""
import json
import time

from bidb.config import ROOT

from . import basemap_sources as src
from .geo_simplify import bbox_centre, collection, feature, join_rings, line_length_km, simplify

OUT = ROOT / "app" / "static" / "data" / "basemap"


def log(msg, t0=[time.time()]):
    print(f"[{time.time() - t0[0]:5.0f}s] {msg}", flush=True)


def _write(name, obj):
    OUT.mkdir(parents=True, exist_ok=True)
    text = json.dumps(obj, ensure_ascii=False, separators=(",", ":"))
    (OUT / f"{name}.json").write_text(text)
    log(f"{name}.json: {len(text) / 1e6:.2f} MB")


def build_land():
    feats = []
    for f in src.natural_earth("ne_10m_admin_1_states_provinces"):
        p = f["properties"]
        if p.get("adm0_a3") not in src.ADM0:
            continue
        label = [round(p["longitude"], 4), round(p["latitude"], 4)] if p.get("latitude") else None
        feats.append(feature(simplify(f["geometry"], 0.002), n=p.get("name"), t=p.get("type_en") or p.get("type"),
                             c=p.get("admin"), l=label or bbox_centre(f["geometry"])))
    for f in src.natural_earth("ne_10m_admin_0_countries"):    # neighbours, for context only
        p = f["properties"]
        if p.get("ADM0_A3") in src.ADM0 or p.get("ADM0_A3") == "GBR":
            continue
        feats.append(feature(simplify(f["geometry"], 0.01, nd=3), n=p.get("NAME"), x=1))
    _write("land", collection(feats))


def build_roads():
    kinds = {"Major Highway": "major", "Secondary Highway": "secondary", "Road": "road",
             "Ferry Route": "ferry", "Ferry, seasonal": "ferry"}
    feats = []
    for f in src.natural_earth("ne_10m_roads"):
        p = f["properties"]
        kind = "motorway" if p.get("expressway") == 1 else kinds.get(p.get("type"), "road")
        name = p.get("local") or p.get("label2") or p.get("label")
        feats.append(feature(simplify(f["geometry"], 0.001), k=kind, n=name))
    _write("roads", collection(feats))


def build_rail():
    feats = [feature(simplify(f["geometry"], 0.001)) for f in src.natural_earth("ne_10m_railroads")
             if f["properties"].get("featurecla") == "Railroad"]
    _write("rail", collection(feats))


def build_rivers():
    from bidb.land import near_land as on_land
    groups = {}
    for w in src.osm_rivers() + src.osm_canals():
        name = w.get("tags", {}).get("name")
        canal = w.get("tags", {}).get("waterway") == "canal"
        pts = [[g["lon"], g["lat"]] for g in w.get("geometry", [])]
        if not name or len(pts) < 2 or not on_land(pts[len(pts) // 2][1], pts[len(pts) // 2][0], 3):
            continue                  # the box also covers northern France
        cell = (round(pts[0][1] * 2) / 2, round(pts[0][0] * 2) / 2)
        key = (name, cell, canal)
        groups.setdefault(key, []).append(pts)
    # merge cells of the same name that touch, so one river is one feature
    feats = []
    for (name, _, canal), lines in groups.items():
        km = sum(line_length_km(l) for l in lines)
        if km < 2:
            continue
        rank = 1 if km >= 40 else 2 if km >= 12 else 3
        geom = simplify({"type": "MultiLineString", "coordinates": lines},
                        {1: 0.001, 2: 0.0015, 3: 0.002}[rank])
        feats.append(feature(geom, n=name, r=rank, **({"c": 1} if canal else {})))
    for layer in ("ne_10m_lakes", "ne_10m_lakes_europe"):
        for f in src.natural_earth(layer):
            feats.append(feature(simplify(f["geometry"], 0.001), n=f["properties"].get("name"), lake=1))
    _write("rivers", collection(feats))


def build_trails():
    from bidb.land import near_land
    feats = []
    for rel in src.osm_trails():
        tags = rel.get("tags", {})
        lines = [[[g["lon"], g["lat"]] for g in m["geometry"]] for m in rel.get("members", [])
                 if m.get("type") == "way" and m.get("geometry")]
        lines = [l for l in lines if len(l) > 1]
        if not lines or not tags.get("name"):
            continue
        mid = lines[len(lines) // 2][0]
        if not near_land(mid[1], mid[0], 3):          # the box also covers northern France
            continue
        geom = simplify({"type": "MultiLineString", "coordinates": lines}, 0.001)
        if geom:
            feats.append(feature(geom, n=tags.get("name:en") or tags["name"], o=tags.get("operator")))
    _write("trails", collection(feats))


def build_parks():
    feats = []
    for rel in src.osm_parks():
        tags = rel.get("tags", {})
        name = tags.get("name:en") or tags.get("name")
        rings = []
        for m in rel.get("members", []):
            if m.get("type") == "way" and m.get("role") in ("outer", "") and m.get("geometry"):
                rings.append([[g["lon"], g["lat"]] for g in m["geometry"]])
        if not rings or not name:
            continue
        desig = tags.get("designation", "")
        kind = ("National Park" if "national park" in name.lower() or "national_park" in (desig, tags.get("boundary"))
                else "National Scenic Area" if "scenic" in name.lower() or desig == "national_scenic_area"
                else "AONB / National Landscape")
        closed = join_rings(rings)
        geom = (simplify({"type": "MultiPolygon", "coordinates": [[r] for r in closed]}, 0.002)
                if closed else simplify({"type": "MultiLineString", "coordinates": rings}, 0.002))
        if geom and kind != "National Scenic Area":           # Scotland's own outlines below
            feats.append(feature(geom, n=name, k=kind, l=bbox_centre(geom)))
    for f in src.scotland_nsas():
        geom = simplify(f["geometry"], 0.002) if f.get("geometry") else None
        name = (f.get("properties") or {}).get("nsaname")
        if geom and name:
            feats.append(feature(geom, n=f"{name} National Scenic Area", k="National Scenic Area", l=bbox_centre(geom)))
    _write("parks", collection(feats))


# GeoNames feature codes kept as landscape labels -> short kind
LANDSCAPE = {"MT": "hill", "PK": "hill", "HLL": "hill", "MTS": "range", "HLLS": "range",
             "FRST": "forest", "MOOR": "moor", "HTH": "moor", "VAL": "glen", "ISL": "island",
             "ISLS": "island", "LK": "lake", "LKS": "lake", "RSV": "lake", "BAY": "bay", "SD": "bay",
             "FJD": "bay", "INLT": "bay", "CAPE": "headland", "HDLD": "headland", "PEN": "headland"}


def _num(v):
    try:
        return int(v)
    except (TypeError, ValueError):
        return None


def build_towns_and_landscape():
    rows = [r for c in src.COUNTRY_CODES for r in src.geonames(c)]
    towns, land = [], []
    for r in rows:
        lat, lon = round(float(r["lat"]), 4), round(float(r["lon"]), 4)
        if r["fclass"] == "P" and r["fcode"] not in ("PPLX", "PPLH", "PPLQ", "PPLW", "PPLCH"):
            pop = _num(r["population"]) or 0
            tier = (0 if r["fcode"] in ("PPLC", "PPLA") or pop >= 100_000
                    else 1 if pop >= 5_000 or r["fcode"] == "PPLA2" else 2)
            towns.append([r["name"], lat, lon, tier, pop])
        elif r["fcode"] in LANDSCAPE:
            kind = LANDSCAPE[r["fcode"]]
            elev = max(_num(r["elevation"]) or 0, _num(r["dem"]) or 0)
            if r["fcode"] == "HLL" and elev < 350:
                continue
            land.append([r["name"], lat, lon, kind, elev or None])
    for f in src.natural_earth("ne_10m_geography_regions_polys"):
        p = f["properties"]
        x, y = bbox_centre(f["geometry"])
        land.append([p.get("LABEL") or p.get("NAME"), y, x, "region", None])
    towns.sort(key=lambda t: (t[3], -t[4]))
    _write("towns", towns)
    _write("landscape", land)


def build_historic_counties():
    """Pre-1974 counties (Historic County Borders Project): outlines + label point per county."""
    feats = []
    for name, rings in src.historic_counties():
        geom = simplify({"type": "MultiPolygon", "coordinates": [[r] for r in rings]}, 0.002)
        if not geom:
            continue
        big = max(rings, key=len)
        lon = sum(p[0] for p in big) / len(big)
        lat = sum(p[1] for p in big) / len(big)
        feats.append(feature(geom, n=name, l=[round(lon, 4), round(lat, 4)]))
    _write("historic_counties", collection(feats))


def build_stations():
    """[name, lat, lon, kind] kind: rail | heritage | metro | bus (for "getting there" and a map layer)."""
    from bidb.land import near_land
    out = []
    for e in src.osm_stations():
        t = e.get("tags", {})
        lat, lon = (e.get("lat"), e.get("lon")) if "lat" in e else (e.get("center", {}).get("lat"), e.get("center", {}).get("lon"))
        if lat is None or not near_land(lat, lon, 2):
            continue
        if t.get("amenity") == "bus_station":
            kind = "bus"
        elif t.get("usage") == "tourism" or t.get("railway:historic") or t.get("tourism") or "heritage" in (t.get("operator") or "").lower():
            kind = "heritage"
        elif t.get("station") in ("subway", "light_rail", "monorail") or t.get("subway") == "yes":
            kind = "metro"
        else:
            kind = "rail"
        out.append([t["name"], round(lat, 5), round(lon, 5), kind])
    _write("stations", out)


def build_underground():
    """Underground railways and tunnels; k: s subway (tube), r railway tunnel, d disused railway
    tunnel, c canal tunnel, h road tunnel."""
    from bidb.land import near_land
    feats = []
    for w in src.osm_underground():
        t = w.get("tags", {})
        line = [[g["lon"], g["lat"]] for g in w.get("geometry") or []]
        if len(line) < 2 or not near_land(line[0][1], line[0][0], 3):
            continue
        kind = ("s" if t.get("railway") == "subway" else "c" if t.get("waterway") else "h" if t.get("highway")
                else "d" if t.get("railway") in ("disused", "abandoned") else "r")
        geom = simplify({"type": "LineString", "coordinates": line}, 0.0002)
        if geom:
            feats.append(feature(geom, k=kind, n=t.get("tunnel:name") or t.get("name"), u=1 if t.get("tunnel") else 0))
    _write("underground", collection(feats))


def build_defences():
    """[name, lat, lon, kind] for pillboxes, bunkers, gun emplacements and trenches (kind from bunker_type)."""
    from bidb.land import near_land
    out = []
    for e in src.osm_defences():
        t = e.get("tags", {})
        lat, lon = (e.get("lat"), e.get("lon")) if "lat" in e else (e.get("center", {}).get("lat"), e.get("center", {}).get("lon"))
        if lat is None or not near_land(lat, lon, 1):
            continue
        bt = (t.get("bunker_type") or "").lower()
        kind = ("trench" if t.get("military") == "trench" else "pillbox" if "pillbox" in bt or t.get("historic") == "pillbox"
                else "gun" if bt in ("gun_emplacement", "munitions", "gun_position") else "bunker")
        out.append([t.get("name") or "", round(lat, 5), round(lon, 5), kind])
    _write("defences", out)


def build_airports():
    out = [[p["name"], round(f["geometry"]["coordinates"][1], 4), round(f["geometry"]["coordinates"][0], 4),
            p.get("iata_code"), p.get("type")]
           for f in src.natural_earth("ne_10m_airports") for p in [f["properties"]]]
    _write("airports", out)


SOURCES = """# Offline map data

Built by `python -m app.basemap_build` from:

- **Natural Earth** 10m (public domain): counties and council areas (admin-1), neighbouring
  countries, major roads, railways, lakes, mountain regions, airports.
- **GeoNames** (CC BY 4.0, geonames.org): cities, towns and villages; hills, ranges, forests, moors,
  glens, islands, lakes, bays and headlands.
- **OpenStreetMap** (© OpenStreetMap contributors, ODbL 1.0): named rivers and canals; national
  parks, AONBs / National Landscapes and National Scenic Areas; national walking routes; railway and bus
  stations (`stations.json`); minor (secondary and tertiary) roads and named streams (`minor/`, `streams/`, built by
  `python -m app.basemap_tiled`). `rivers.json`, `parks.json`, `trails.json`, `minor/` and `streams/` are derived from OpenStreetMap and are available
  under the Open Database Licence. Underground railways and tunnels (`underground.json`) and
  pillboxes, bunkers and trenches (`defences.json`) also come from OpenStreetMap.

- **Historic County Borders Project** (county-borders.co.uk; free for any use with
  acknowledgement): this project made use of data provided by the Historic County Borders Project
  (`historic_counties.json`, pre-1974 counties, definition A).

Geometries are simplified for display; they are not survey-accurate.
"""


def main():
    for fn in (build_land, build_roads, build_rail, build_trails, build_rivers, build_parks,
               build_towns_and_landscape, build_airports, build_stations, build_historic_counties, build_underground,
               build_defences):
        fn()
    (OUT / "SOURCES.md").write_text(SOURCES)


if __name__ == "__main__":
    main()
