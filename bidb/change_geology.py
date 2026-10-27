"""Fixed map layers for "Change over time" (roadmap E3): the rocks under the isles, which decided where coal,
iron, building stone and good soils lay, and so where industry and towns grew.

Inputs (simplified by the research step, in data/curated/change/layers/): BGS Geology 625k bedrock dissolved by
period (Great Britain; OGL), GSI/GSNI Bedrock Geology 1:500k dissolved by age bracket (all Ireland; CC BY 4.0 /
OGL) and the Coal Authority's coalfield consultation areas (OGL).

    python -m bidb.change_geology     → app/static/data/change/geology.json, coalfields.json (+ entries in layers.json),
                                        rocks.json (building types BT3c2: the UK (BGS) and all Ireland (GSI/GSNI) by period
                                        range and kinds of building rock, made by layers/prepare_rocks.py; drawn on
                                        material pages, not a layer here)
"""
import json

from .config import ROOT

SRC = ROOT / "data" / "curated" / "change" / "layers"
OUT = ROOT / "app" / "static" / "data" / "change"
# periods oldest first, in the International Commission on Stratigraphy's chart colours
PERIODS = [("Precambrian", "#F73563"), ("Cambrian", "#7FA056"), ("Ordovician", "#009270"), ("Silurian", "#B3E1B6"),
           ("Devonian", "#CB8C37"), ("Carboniferous", "#67A599"), ("Permian", "#F04028"), ("Triassic", "#812B92"),
           ("Jurassic", "#34B2C9"), ("Cretaceous", "#7FC64E"), ("Palaeogene", "#FD9A52"), ("Neogene", "#FFE619"),
           ("Intrusions and undivided", "#9A9A9A")]
NAMES = [p for p, _ in PERIODS]
SOURCES = {
    "bgs": {"short": "BGS Geology 625k", "licence": "OGL v3.0", "url": "https://www.bgs.ac.uk/datasets/bgs-geology-625k-digmapgb/",
            "citation": "British Geological Survey (2025) BGS Geology 625k (DiGMapGB-625) bedrock, V5. Contains British "
                        "Geological Survey materials © UKRI 2025"},
    "gsi": {"short": "GSI/GSNI Bedrock Geology 1:500,000", "licence": "CC BY 4.0 (GSI) / OGL v3.0 (GSNI)",
            "url": "https://data.gov.ie/dataset/bedrock-geology-1500000-ireland-roini-itm",
            "citation": "Geological Survey Ireland / Geological Survey of Northern Ireland (2024) Bedrock Geology 1:500,000 "
                        "Ireland (ROI/NI). Contains Irish Public Sector Data (Geological Survey Ireland) licensed under "
                        "CC BY 4.0; contains UK public sector information (GSNI) licensed under the Open Government Licence v3.0"},
    "coal": {"short": "Coal Authority coalfield areas", "licence": "OGL v3.0", "url": "https://datamine-cauk.hub.arcgis.com/",
             "citation": "Mining Remediation Authority (Coal Authority), Coalfield Consultation Areas. Contains public sector "
                         "information licensed under the Open Government Licence v3.0"},
}


# kinds of building rock in rocks.json, in bit order (prepare_rocks.KINDS): a material names its own in `rock`
ROCKS = [("limestone", "Limestone and dolostone"), ("chalk", "Chalk"), ("sandstone", "Sandstone"),
         ("mudstone", "Mudstone, pelite and slate"), ("felsic", "Granite and other felsic intrusions"),
         ("mafic", "Dolerite and basalt (whinstone)")]
IGNEOUS = {"felsic", "mafic"}                          # dated by when they cooled, so drawn whatever their period


def bgs_period(props):
    p, era = props.get("period"), props.get("era") or ""
    if p and p.title() in NAMES:
        return p.title()
    return "Precambrian" if "PROTEROZOIC" in era else "Intrusions and undivided"


def gsi_period(age):
    """An Irish age bracket → the oldest period it names (brackets spanning two periods show as the older)."""
    if "proterozoic" in age.lower():
        return "Precambrian"
    if age == "Lower Palaeozoic":
        return "Cambrian"
    hits = [n for n in NAMES if n in age or (n == "Palaeogene" and ("Oligocene" in age or "Palaeocene" in age))]
    if "Caledonian" in age:
        hits = ["Silurian"]
    return min(hits, key=NAMES.index) if hits else "Intrusions and undivided"


def _round(coords, nd=3):
    if isinstance(coords[0], (int, float)):
        return [round(coords[0], nd), round(coords[1], nd)]
    return [_round(c, nd) for c in coords]


def _feature(geom, props):
    return {"type": "Feature", "properties": props, "geometry": {"type": geom["type"], "coordinates": _round(geom["coordinates"])}}


def build():
    feats = []
    for f in json.loads((SRC / "bgs625k_bedrock_period.geojson").read_text())["features"]:
        feats.append(_feature(f["geometry"], {"p": NAMES.index(bgs_period(f["properties"])), "s": "bgs"}))
    for f in json.loads((SRC / "gsi500k_bedrock_age.geojson").read_text())["features"]:
        feats.append(_feature(f["geometry"], {"p": NAMES.index(gsi_period(f["properties"]["age"])), "s": "gsi",
                                              "a": f["properties"]["age"]}))
    (OUT / "geology.json").write_text(json.dumps({"type": "FeatureCollection", "features": feats}, separators=(",", ":")))
    coal = [_feature(f["geometry"], {"name": f["properties"]["name"].title()})
            for f in json.loads((SRC / "coal_authority_coalfield_areas.geojson").read_text())["features"]]
    (OUT / "coalfields.json").write_text(json.dumps({"type": "FeatureCollection", "features": coal}, separators=(",", ":")))
    layers = [{"id": "geology", "title": "Bedrock geology (by period)", "kind": "geojson", "file": "geology.json",
               "legend": [{"color": c, "label": n} for n, c in PERIODS],
               "note": "The age of the solid rock under the soil, oldest in the north-west, youngest in the south-east. "
                       "Carboniferous rocks hold the coal and much of the iron that fed the Industrial Revolution; "
                       "Jurassic limestones gave Cotswold and Portland stone; Cretaceous chalk the downs. Irish age "
                       "ranges spanning two periods are shown as the older one.",
               "sources": [SOURCES["bgs"], SOURCES["gsi"]]},
              {"id": "coalfields", "title": "Coalfields", "kind": "geojson", "file": "coalfields.json",
               "legend": [{"color": "#3b3b3b", "label": "Coalfield (surface coal resource area)"}],
               "note": "Areas over coal resources where planning consults the Coal Authority, a good outline of the "
                       "British coalfields; mining towns grew on them from the 18th century.",
               "sources": [SOURCES["coal"]]}]
    rocks = []
    for s, name in (("bgs", "bgs625k_bedrock_rock.geojson"), ("gsi", "gsi500k_bedrock_rock.geojson")):
        src = json.loads((SRC / name).read_text())
        assert src["kinds"] == [k for k, _ in ROCKS], "prepare_rocks.KINDS and ROCKS differ"
        rocks += [_feature(f["geometry"], {**f["properties"], "s": s}) for f in src["features"]]
    (OUT / "rocks.json").write_text(json.dumps({"type": "FeatureCollection", "kinds": [{"id": k, "label": l} for k, l in ROCKS],
                                                "features": rocks}, separators=(",", ":")))
    meta_path = OUT / "layers.json"
    meta = json.loads(meta_path.read_text()) if meta_path.exists() else {"layers": []}
    new = {l["id"]: l for l in layers}                 # replaced where they stand, so the chooser keeps its order
    meta["layers"] = [new.pop(l["id"], l) for l in meta["layers"]] + list(new.values())
    meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=1))
    return feats, coal


if __name__ == "__main__":
    g, c = build()
    print(f"geology: {len(g)} features, {(OUT / 'geology.json').stat().st_size // 1024} KB; "
          f"coalfields: {len(c)}, {(OUT / 'coalfields.json').stat().st_size // 1024} KB; "
          f"rocks: {(OUT / 'rocks.json').stat().st_size // 1024} KB")
