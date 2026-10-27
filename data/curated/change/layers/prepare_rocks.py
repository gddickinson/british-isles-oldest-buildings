"""One-off: BGS Geology 625k bedrock (OGL) → bgs625k_bedrock_rock.geojson, the polygons of Great Britain dissolved by
period and by the kinds of building rock each unit contains (building types BT3c2: a material's region drawn over the
geology); GSI/GSNI Bedrock Geology 1:500k (CC BY 4.0 / OGL) → gsi500k_bedrock_rock.geojson, the same for all
Ireland. Read by bidb.change_geology, which writes app/static/data/change/rocks.json.

A unit "contains" a kind when its rock description (RCS_D, e.g. "MUDSTONE, SILTSTONE, LIMESTONE AND SANDSTONE")
names it, so mixed units count for each of their rocks. Periods as bidb.change_geology.bgs_period: p from MAX_PERIOD
and MAX_ERA (the oldest age of the unit), q from MIN_PERIOD and MIN_ERA (the youngest), so the Lias Group (Triassic
to Jurassic) is found by both. Needs ogr2ogr (GDAL_BIN) and shapely, not the project's environment:

    GDAL_BIN=/opt/anaconda3/envs/flika/bin/ /opt/anaconda3/envs/flika/bin/python prepare_rocks.py bgs <bgs625k_shp.zip>
    ... prepare_rocks.py gsi <gsi500k.zip>

The BGS zip is the download "BGS Geology 625k GIS line and polygon data, shapefile format" (16 MB, 2025 release V5);
the GSI zip is IE_GSI_GSNI_Bedrock_Geology_Datasets_500K_IE32_ITM.zip (7 MB, data.gov.ie "Bedrock Geology 1:500,000
Ireland (ROI/NI) ITM", 2024). Irish units name their rocks in plain words (UNITNAME "61, Marine shelf & ramp facies;
Argillaceous dark-grey bioclastic limestone, subsidiary shale"), matched by GSI_KINDS as whole words; their age
bracket (AGEBRACKET "Caledonian (Silurian - Devonian)") gives the period range.
"""
import json
import os
import re
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
# the same kinds in GSI's words (whole words, case-insensitive): metamorphic rocks left out as BGS's are (gneiss,
# schist, quartzite, meta-dolerite; Dalradian marble is metamorphosed limestone, kept as BGS keeps metalimestone),
# lavas and tuffs left out of felsic as in BGS (rhyolite), shale counted with mudstone (BGS maps it as mudstone)
GSI_KINDS = [r"limestone|marble", r"chalk", r"sandstone|greywacke", r"mudstone|shale|slate|pelitic|phyllite",
             r"granite|granodiorite|microgranite|granophyre|tonalite|syenite",
             r"(?<!meta-)(?:dolerite|basalt|gabbro)"]
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


def gsi_kinds(unit):
    rocks = unit.split(";")[-1] if ";" in unit else unit.split(",", 1)[-1]   # the rocks, not the facies or group name
    return sum(1 << i for i, pat in enumerate(GSI_KINDS) if re.search(rf"\b(?:{pat})\b", rocks, re.I))


def gsi_periods(age):
    """An Irish age bracket → (oldest, youngest) period index, as bidb.change_geology.gsi_period but keeping the range."""
    hits = [n for n in NAMES if n in age]
    if "proterozoic" in age.lower():
        hits.append("Precambrian")
    if "Lower Palaeozoic" in age:
        hits += ["Cambrian", "Silurian"]
    if "Palaeocene" in age or "Oligocene" in age:
        hits.append("Palaeogene")
    if "Mississipp" in age or "Pennsyl" in age:
        hits.append("Carboniferous")
    idx = sorted(NAMES.index(h) for h in hits) or [NAMES.index("Intrusions and undivided")]
    return idx[0], idx[-1]


def _read(src, layer, fields):
    with tempfile.TemporaryDirectory() as tmp:
        out = os.path.join(tmp, "bedrock.geojson")
        subprocess.run([G + "ogr2ogr", "-f", "GeoJSON", "-simplify", "300", "-t_srs", "EPSG:4326",
                        "-select", fields, out, src, layer], check=True)
        return json.load(open(out))["features"]


def _write(groups, name, n_in):
    result = []
    for (p, q, k), geoms in sorted(groups.items()):
        g = unary_union(geoms).simplify(0.004)                          # about 300-450 m, as the period layer's 400 m
        parts = [q for q in getattr(g, "geoms", [g]) if q.area >= MIN_AREA]
        g = unary_union(parts) if parts else None
        if g is not None and not g.is_empty:
            result.append({"type": "Feature", "properties": {"p": p, "q": q, "k": k}, "geometry": _round(mapping(g))})
    path = os.path.join(HERE, name)
    json.dump({"type": "FeatureCollection", "kinds": [k for k, _ in KINDS], "features": result}, open(path, "w"),
              separators=(",", ":"))
    print(f"{n_in} polygons → {len(result)} features, {os.path.getsize(path) // 1024} KB")


def bgs(zip_path):
    src = f"/vsizip/{zip_path}/BGS_Geology_625k_Shapefile/Bedrock/{LAYER}.shp"
    feats = _read(src, LAYER, "RCS_D,MAX_PERIOD,MAX_ERA,MIN_PERIOD,MIN_ERA")
    groups = {}
    for f in feats:
        pr, k = f["properties"], kinds(f["properties"]["RCS_D"])
        if k and f["geometry"]:
            p, q = (NAMES.index(period(pr[f"{m}_PERIOD"], pr[f"{m}_ERA"])) for m in ("MAX", "MIN"))
            groups.setdefault((p, q if q >= p else p, k), []).append(shape(f["geometry"]).buffer(0))
    _write(groups, "bgs625k_bedrock_rock.geojson", len(feats))


def gsi(zip_path):
    layer = "IE_GSI_GSNI_Bedrock_Geology_500k_IE32_ITM_MS"
    feats = _read(f"/vsizip/{zip_path}/{layer}.shp", layer, "UNITNAME,AGEBRACKET")
    groups = {}
    for f in feats:
        pr = f["properties"]
        k = gsi_kinds(pr["UNITNAME"] or "")
        if k and f["geometry"]:
            groups.setdefault((*gsi_periods(pr["AGEBRACKET"] or ""), k), []).append(shape(f["geometry"]).buffer(0))
    _write(groups, "gsi500k_bedrock_rock.geojson", len(feats))


if __name__ == "__main__":
    {"bgs": bgs, "gsi": gsi}[sys.argv[1]](sys.argv[2])
