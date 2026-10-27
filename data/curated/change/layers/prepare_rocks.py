"""One-off: BGS Geology 625k bedrock (OGL) → bgs625k_bedrock_rock.geojson, the polygons of Great Britain dissolved by
period and by the kinds of building rock each unit contains (building types BT3c2: a material's region drawn over the
geology). Read by bidb.change_geology, which writes app/static/data/change/rocks.json.

A unit "contains" a kind when its rock description (RCS_D, e.g. "MUDSTONE, SILTSTONE, LIMESTONE AND SANDSTONE")
names it, so mixed units count for each of their rocks. Periods as bidb.change_geology.bgs_period: p from MAX_PERIOD
and MAX_ERA (the oldest age of the unit), q from MIN_PERIOD and MIN_ERA (the youngest), so the Lias Group (Triassic
to Jurassic) is found by both. Needs ogr2ogr (GDAL_BIN) and shapely, not the project's environment:

    GDAL_BIN=/opt/anaconda3/envs/flika/bin/ /opt/anaconda3/envs/flika/bin/python prepare_rocks.py <bgs625k_shp.zip>

The zip is the BGS download "BGS Geology 625k GIS line and polygon data, shapefile format" (16 MB, 2025 release V5).
"""
import json
import os
import subprocess
import sys
import tempfile

from shapely.geometry import mapping, shape
from shapely.ops import unary_union

HERE = os.path.dirname(os.path.abspath(__file__))
G = os.environ.get("GDAL_BIN", "")
LAYER = "625k_V5_BEDROCK_Geology_Polygons"
# kind → words of RCS_D naming it (bit = position); see bidb.change_geology.ROCKS
KINDS = [("limestone", ("LIMESTONE", "DOLOSTONE", "DOLOMITE")),          # dolomitised and metalimestone too
         ("chalk", ("CHALK",)),
         ("sandstone", ("SANDSTONE", "QUARTZ-ARENITE", "WACKE")),
         ("mudstone", ("MUDSTONE", "PELITE", "ARGILLACEOUS ROCKS", "CLAYSTONE")),   # slate country at this scale
         ("felsic", ("FELSIC-ROCK", "SYENITIC-ROCK")),                   # granite and allied intrusions (not lavas or tuffs)
         ("mafic", ("MAFIC IGNEOUS-ROCK", "DOLERITE", "BASALT", "MAFIC LAVA"))]   # whinstone
MIN_AREA = 1e-4                    # square degrees, about 0.7 km²: slivers left by the simplification left out
NAMES = ["Precambrian", "Cambrian", "Ordovician", "Silurian", "Devonian", "Carboniferous", "Permian", "Triassic",
         "Jurassic", "Cretaceous", "Palaeogene", "Neogene", "Intrusions and undivided"]


def kinds(rcs):
    rcs = (rcs or "").upper()
    return sum(1 << i for i, (_, words) in enumerate(KINDS) if any(w in rcs for w in words))


def period(p, era):
    if p and p.title() in NAMES:
        return p.title()
    return "Precambrian" if "PROTEROZOIC" in (era or "") else "Intrusions and undivided"


def _round(geom, nd=4):
    def r(c):
        return [round(c[0], nd), round(c[1], nd)] if isinstance(c[0], float) else [r(x) for x in c]
    return {"type": geom["type"], "coordinates": r(geom["coordinates"])}


def main(zip_path):
    src = f"/vsizip/{zip_path}/BGS_Geology_625k_Shapefile/Bedrock/{LAYER}.shp"
    with tempfile.TemporaryDirectory() as tmp:
        out = os.path.join(tmp, "bedrock.geojson")
        subprocess.run([G + "ogr2ogr", "-f", "GeoJSON", "-simplify", "300", "-t_srs", "EPSG:4326",
                        "-select", "RCS_D,MAX_PERIOD,MAX_ERA,MIN_PERIOD,MIN_ERA", out, src, LAYER], check=True)
        feats = json.load(open(out))["features"]
    groups = {}
    for f in feats:
        pr, k = f["properties"], kinds(f["properties"]["RCS_D"])
        if k and f["geometry"]:
            p, q = (NAMES.index(period(pr[f"{m}_PERIOD"], pr[f"{m}_ERA"])) for m in ("MAX", "MIN"))
            groups.setdefault((p, q if q >= p else p, k), []).append(shape(f["geometry"]).buffer(0))
    result = []
    for (p, q, k), geoms in sorted(groups.items()):
        g = unary_union(geoms).simplify(0.004)                          # about 300-450 m, as the period layer's 400 m
        parts = [q for q in getattr(g, "geoms", [g]) if q.area >= MIN_AREA]
        g = unary_union(parts) if parts else None
        if g is not None and not g.is_empty:
            result.append({"type": "Feature", "properties": {"p": p, "q": q, "k": k}, "geometry": _round(mapping(g))})
    path = os.path.join(HERE, "bgs625k_bedrock_rock.geojson")
    json.dump({"type": "FeatureCollection", "kinds": [k for k, _ in KINDS], "features": result}, open(path, "w"),
              separators=(",", ":"))
    print(f"{len(feats)} polygons → {len(result)} features, {os.path.getsize(path) // 1024} KB")


if __name__ == "__main__":
    main(sys.argv[1])
