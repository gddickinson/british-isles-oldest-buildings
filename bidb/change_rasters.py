"""More map layers for "Change over time" (roadmap E3), drawn from grids prepared once from the published data
(data/curated/change/layers/, see its README.md): built-up land from satellites (GHSL, 1975 and 2020), people
per km² (GHS-POP, 1975–2020), land cover
(CORINE 2000–2018), tree cover from pollen through the Holocene (LandClimII REVEALS, 1° cells), ancient woodland,
agricultural land grades (England), superficial geology (Great Britain), and towns and cities by size (Buringh,
700–2000) as dots that follow the year slider.

    python -m bidb.change_rasters      → app/static/data/change/layers/<id>.json + entries in layers.json
"""
import base64
import csv
import gzip
import json
import sys

from .change_layers import LAT0, LAT1, LON0, LON1, OUT, PER_DEG, png

SRC = OUT.parents[3] / "data" / "curated" / "change" / "layers"
BOUNDS = [[LAT0, LON0], [LAT1, LON1]]
OGL = "OGL v3.0"
SOURCES = {
    "ghsl": {"short": "GHSL built-up surface R2023A", "licence": "© European Union; reuse with acknowledgement",
             "url": "https://human-settlement.emergency.copernicus.eu/ghs_buS2023.php",
             "citation": "Pesaresi, M. (2023) GHS-BUILT-S R2023A – GHS built-up surface grid, derived from Sentinel-2 "
                         "composite and Landsat, multitemporal (1975–2030). European Commission, Joint Research Centre, "
                         "doi:10.2905/9F06F36F-4B11-47EC-ABB0-4F8B7B1D72EA. © European Union, 1995–2025"},
    "ghs_pop": {"short": "GHSL population grid R2023A", "licence": "© European Union; reuse with acknowledgement",
                "url": "https://human-settlement.emergency.copernicus.eu/ghs_pop2023.php",
                "citation": "Schiavina, M., Freire, S., Carioli, A., MacManus, K. (2023) GHS-POP R2023A – GHS population "
                            "grid multitemporal (1975–2030). European Commission, Joint Research Centre, "
                            "doi:10.2905/2FF68A52-5B5B-4A22-8F40-C41DA8332CFE. © European Union, 1995–2025"},
    "cru": {"short": "CRU TS 4.10 (Harris et al. 2020)", "licence": "Open Database License (ODbL)",
            "url": "https://crudata.uea.ac.uk/cru/data/hrg/cru_ts_4.10/",
            "citation": "Harris, I., Osborn, T.J., Jones, P., Lister, D. (2020) Version 4 of the CRU TS monthly "
                        "high-resolution gridded multivariate climate dataset. Scientific Data 7:109, "
                        "doi:10.1038/s41597-020-0453-3; data CRU TS v4.10, University of East Anglia Climatic Research Unit"},
    "corine": {"short": "CORINE Land Cover", "licence": "Copernicus free and open data (attribution)",
               "url": "https://land.copernicus.eu/en/products/corine-land-cover",
               "citation": "Generated using European Union's Copernicus Land Monitoring Service information: CORINE Land "
                           "Cover 2000, 2006, 2012 and 2018, doi:10.2909/960998c1-1870-4e82-8051-6485205ebbac (2018); "
                           "read from the European Environment Agency's map service"},
    "reveals": {"short": "Githumbi et al. 2022 (LandClimII REVEALS)", "licence": "CC BY 4.0",
                "url": "https://doi.org/10.1594/PANGAEA.937075",
                "citation": "Fyfe, R.M., Githumbi, E., Trondman, A.-K. et al. (2021) A full Holocene record of transient "
                            "gridded vegetation cover in Europe. PANGAEA, doi:10.1594/PANGAEA.937075; described in "
                            "Githumbi, E. et al. (2022) ESSD 14:1581–1619, doi:10.5194/essd-14-1581-2022"},
    "awi_eng": {"short": "Ancient Woodland (England), Natural England", "licence": OGL,
                "url": "https://environment.data.gov.uk/api/file/download?fileDataSetId=008cdfcf-893b-48f6-937a-3891a2a698c9&fileName=Ancient_Woodland_England.geojson.zip",
                "citation": "Natural England, Ancient Woodland (England). © Natural England copyright. Contains Ordnance "
                            "Survey data © Crown copyright and database right 2026"},
    "awi_scot": {"short": "Ancient Woodland Inventory (Scotland), NatureScot", "licence": "OS Open Data licence / OGL",
                 "url": "https://gis-downloads.nature.scot/",
                 "citation": "Copyright NatureScot. Contains Ordnance Survey data © Crown copyright and database right 2023"},
    "awi_wal": {"short": "Ancient Woodland Inventory 2021 (Wales), NRW", "licence": OGL,
                "url": "https://datamap.gov.wales/layers/inspire-nrw:NRW_ANCIENT_WOODLAND_INVENTORY_2021",
                "citation": "© CNC/NRW, Ancient Woodland Inventory 2021; re-used under the Open Government Licence. "
                            "Contains Ordnance Survey data"},
    "alc": {"short": "Provisional Agricultural Land Classification, Natural England", "licence": OGL,
            "url": "https://environment.data.gov.uk/api/file/download?fileDataSetId=f33896b6-9847-4f03-b5d9-3c55497a003c&fileName=Provisional_Agricultural_Land_Classification_ALC.geojson.zip",
            "citation": "Natural England, Provisional Agricultural Land Classification (ALC) (England). © Natural England "
                        "copyright. Contains Ordnance Survey data © Crown copyright and database right"},
    "bgs_sup": {"short": "BGS Geology 625k superficial deposits", "licence": OGL,
                "url": "https://www.bgs.ac.uk/datasets/bgs-geology-625k-digmapgb/",
                "citation": "British Geological Survey (2025) BGS Geology 625k (DiGMapGB-625) superficial deposits, V5. "
                            "Contains British Geological Survey materials © UKRI 2025"},
    "buringh": {"short": "Buringh 2020, European urban population 700–2000", "licence": "CC0",
                "url": "https://doi.org/10.17026/DANS-XZY-U62Q",
                "citation": "Buringh, E. (2020) European urban population, 700–2000. DANS, doi:10.17026/DANS-XZY-U62Q; "
                            "described in Buringh, E. (2021) Research Data Journal for the Humanities and Social "
                            "Sciences 6(1):1–16, doi:10.1163/24523666-06010003"},
}
GREENS = ["#e8f2d9", "#cfe5b0", "#b1d487", "#8fc061", "#6ca842", "#4c8d2e", "#357023", "#22531a"]
GREYS = ["#e9dfe6", "#d3bfcf", "#bb9fb8", "#a27fa0", "#876089", "#6b4370", "#4e2a55"]


def _grid(name):
    with gzip.open(SRC / f"{name}.json.gz", "rt") as f:
        return json.load(f)


def _uri(rows, edges, colors, per_deg):
    return "data:image/png;base64," + base64.b64encode(png(rows, edges, colors, 1, per_deg)).decode()


def _legend(edges, colors, labels=None):
    if labels:
        return [{"color": c, "label": l} for c, l in zip(colors, labels)]
    return [{"color": c, "label": f"{e:g}–{edges[i + 1]:g}" if i + 1 < len(edges) else f"{e:g}+"}
            for i, (e, c) in enumerate(zip(edges, colors))]


def _layer(lid, title, pack, legend, note, sources, unit="", modelled=False, date=None):
    (OUT / "layers").mkdir(parents=True, exist_ok=True)
    (OUT / "layers" / f"{lid}.json").write_text(json.dumps(pack, separators=(",", ":")))
    years = sorted(int(y) for y in pack)
    meta = {"id": lid, "title": title, "kind": "grid", "years": years, "file": f"layers/{lid}.json", "bounds": BOUNDS,
            "unit": unit, "legend": legend, "note": note, "sources": sources}
    if modelled:
        meta["modelled"] = True
    if date:
        meta["date"] = date
    return meta


def built():
    edges, colors = [1, 2, 5, 10, 15, 20, 30], GREYS
    pack = {y: _uri(_grid(f"ghsl_built_{y}")["rows"], edges, colors, 60) for y in (1975, 2020)}
    return _layer("ghsl_built", "Built-up land from satellites", pack, _legend(edges, colors),
                  "Share of the ground covered by buildings, mapped by the EU's Global Human Settlement Layer from "
                  "Landsat and Sentinel-2 images, in cells of about 1 by 2 km. Shown for 1975 and 2020; before 1975 "
                  "nothing is drawn.", [SOURCES["ghsl"]], "% of the ground under buildings")


def people():
    from .change_layers import LAYERS
    edges, colors = [1, 10, 50, 150, 500, 1000, 2500, 5000], LAYERS["popd"]["colors"]
    pack = {y: _uri(_grid(f"ghs_pop_{y}")["rows"], edges, colors, 60) for y in range(1975, 2021, 5)}
    return _layer("ghs_pop", "People per km² from satellites and censuses", pack, _legend(edges, colors),
                  "Census counts spread over the built-up areas seen by satellites (EU Global Human Settlement Layer), "
                  "every five years from 1975 to 2020, in cells of about 1 by 2 km. Before 1975 nothing is drawn; "
                  "for earlier centuries see the modelled people per km² (HYDE).", [SOURCES["ghs_pop"]], "people per km²")


WARM = ["#3b6fb6", "#8fb3dc", "#d9d4cc", "#f2c4a0", "#e6905f", "#cc5a37", "#9e2a1f"]   # diverging, grey at "no change"
WET = ["#8c5a2b", "#c9a26b", "#d9d4cc", "#9cc9c1", "#4f9c95", "#1f6d6a"]


def climate():
    """Decade averages from CRU TS against 1901–1930: temperature difference (°C) and rainfall (% of 1901–1930)."""
    if not (SRC / "cru_decades.json.gz").exists():     # prepared by prepare_rasters.py cru
        return []
    with gzip.open(SRC / "cru_decades.json.gz", "rt") as f:
        d = json.load(f)
    out = []
    for var, lid, title, edges, colors, unit, note in (
            ("tmp", "cru_temp", "Warmer or cooler than 1901–1930", [-99, -0.45, -0.15, 0.15, 0.45, 0.75, 1.05], WARM, "°C",
             "Average temperature of each decade compared with 1901–1930, in squares of half a degree (about 55 km), "
             "from weather-station records interpolated by the Climatic Research Unit. Grey is within 0.15 °C of the "
             "early-20th-century average."),
            ("pre", "cru_rain", "Wetter or drier than 1901–1930", [-99, 90, 96, 104, 110, 116], WET, "% of 1901–1930",
             "Average yearly rainfall of each decade as a share of 1901–1930, in squares of half a degree, from "
             "rain-gauge records interpolated by the Climatic Research Unit. Grey is within 4% of the "
             "early-20th-century average.")):
        dec = {int(k): v for k, v in d[var].items()}
        base = [[_mean([dec[y][r][c] for y in (1901, 1911, 1921)]) for c in range(len(dec[1901][0]))]
                for r in range(len(dec[1901]))]
        pack = {}
        for y, rows in dec.items():
            pack[y] = _uri([[None if v is None or b is None else (v - b if var == "tmp" else 100 * v / b if b else None)
                             for v, b in zip(row, brow)] for row, brow in zip(rows, base)], edges, colors, d["per_deg"])
        labels = {y: f"{y}–{min(y + 9, 2025)}" for y in dec}
        legend = _legend(edges, colors)
        legend[0]["label"] = f"below {edges[1]:g}"
        meta = _layer(lid, title, pack, legend, note, [SOURCES["cru"]], unit)
        meta["labels"] = labels
        out.append(meta)
    return out


def _mean(vals):
    vals = [v for v in vals if v is not None]
    return sum(vals) / len(vals) if vals else None


CORINE = [("Towns, industry and mines", "#c0392b"), ("Arable land", "#f2d35e"), ("Pasture", "#b9dc7a"),
          ("Mixed farming and orchards", "#e3a857"), ("Woods and forest", "#2e7d32"),
          ("Moor, heath and rough grassland", "#a98bc4"), ("Bare rock, beaches and dunes", "#bdbdbd"),
          ("Bogs, marshes and saltmarsh", "#5d8aa8"), ("Lakes and rivers", "#3f6fd8")]


def land_cover():
    colors = [c for _, c in CORINE]
    edges = list(range(1, len(CORINE) + 1))
    pack = {y: _uri(_grid(f"corine_{y}")["rows"], edges, colors, 60) for y in (2000, 2006, 2012, 2018)}
    return _layer("corine", "Land cover (CORINE)", pack, _legend(edges, colors, [n for n, _ in CORINE]),
                  "What covers the land, from satellite images (patches of 25 hectares or more), with the 44 CORINE classes gathered into nine. Read from the EEA's generalised map at "
                  "about 1.5 km; for exact areas use the full product. Before 2000 nothing is drawn.",
                  [SOURCES["corine"]])


def pollen_trees():
    """1° cells of tree cover (% of land) for each pollen time window, drawn on the 1/12° grid."""
    cells = json.loads((SRC / "pollen_tree_cells.geojson").read_text())["features"]
    years = sorted({int(y) for c in cells for y in c["properties"]["tree_cover_pct_se"]})
    h, w = round((LAT1 - LAT0) * PER_DEG), round((LON1 - LON0) * PER_DEG)
    edges, pack = [5, 10, 20, 30, 40, 50, 60, 70], {}
    for y in years:
        rows = [[None] * w for _ in range(h)]
        for c in cells:
            v = c["properties"]["tree_cover_pct_se"].get(str(y))
            if not v:
                continue
            p = c["properties"]
            r0, c0 = round((LAT1 - p["lat"] - 0.5) * PER_DEG), round((p["lon"] - 0.5 - LON0) * PER_DEG)
            for r in range(max(0, r0), min(h, r0 + PER_DEG)):
                for k in range(max(0, c0), min(w, c0 + PER_DEG)):
                    rows[r][k] = max(v[0], 0.01)
        pack[y] = _uri(rows, edges, GREENS, PER_DEG)
    return _layer("pollen_trees", "Tree cover from pollen", pack, _legend(edges, GREENS),
                  "Tree cover estimated from pollen in lake and bog cores with the REVEALS model, in squares of one "
                  "degree, for time windows of a few centuries (the date shown is the middle of the window). Squares "
                  "without enough pollen sites stay empty. Woodland spread after the Ice Age and was cleared by "
                  "farmers from the Neolithic on.", [SOURCES["reveals"]], "% of the land under trees", modelled=True)


def ancient_woodland():
    edges = [1, 5, 10, 20, 35, 50]
    pack = {2023: _uri(_grid("ancient_woodland")["rows"], edges, GREENS[2:], 60)}
    return _layer("ancient_woodland", "Ancient woodland", pack, _legend(edges, GREENS[2:]),
                  "Share of each cell (about 1 by 2 km) that is ancient woodland: land wooded since at least 1600 in England "
                  "and Wales and since about 1750 (Roy's Military Survey) in Scotland, from old maps; both surviving "
                  "native woods and plantations on ancient woodland sites. Northern Ireland and Ireland are not "
                  "included.", [SOURCES["awi_eng"], SOURCES["awi_wal"], SOURCES["awi_scot"]], "% of the land",
                  date="inventories of 2021–2026")


ALC = [("Grade 1 (excellent)", "#1a6b2f"), ("Grade 2 (very good)", "#4f9a3a"), ("Grade 3 (good to moderate)", "#a9cf6b"),
       ("Grade 4 (poor)", "#e4cf7a"), ("Grade 5 (very poor)", "#c08a4a"), ("Not farmland", "#c9c9c9"),
       ("Towns", "#8e5a8a")]


def land_grades():
    colors, edges = [c for _, c in ALC], list(range(1, len(ALC) + 1))
    pack = {1988: _uri(_grid("alc_grades")["rows"], edges, colors, 60)}
    return _layer("alc", "Farmland quality (England)", pack, _legend(edges, colors, [n for n, _ in ALC]),
                  "How good the land is for farming, graded from soil, climate, slope and wetness on the 1:250,000 "
                  "provisional maps of the 1970s; not for single fields. England only.",
                  [SOURCES["alc"]], date="maps of the 1970s")


SUPERFICIAL = [("Till (boulder clay)", "#9fb3c8"), ("Glacial sand and gravel", "#e8c36a"),
               ("River alluvium, terraces and lake beds", "#7cc0b0"), ("Peat", "#6b4f3a"),
               ("Raised beaches and blown sand", "#f3e6a2"), ("Clay-with-flints, brickearth, crag", "#d39a6a"),
               ("Landslip", "#b05050")]


def superficial():
    colors, edges = [c for _, c in SUPERFICIAL], list(range(1, len(SUPERFICIAL) + 1))
    pack = {2025: _uri(_grid("superficial")["rows"], edges, colors, 60)}
    return _layer("superficial", "Superficial deposits (Great Britain)", pack,
                  _legend(edges, colors, [n for n, _ in SUPERFICIAL]),
                  "Loose deposits left on top of the bedrock, mostly by the ice ages: boulder clay, sands and gravels, "
                  "river silts, peat and old beaches. Where none is shown the bedrock is at or near the surface. Great "
                  "Britain only.", [SOURCES["bgs_sup"]], date="mapped at 1:625,000")


def cities():
    """Towns and cities by size for each Buringh date: [[name, lat, lon, {year: [thousands, imputed]}]]."""
    places = {}
    with open(SRC / "buringh_cities.csv", newline="") as f:
        for r in csv.DictReader(f):
            p = places.setdefault(r["city"], [r["city"], float(r["lat"]), float(r["lon"]), {}])
            p[3][int(r["year"])] = [float(r["thousands"]), 1 if r["estimate"] == "imputed" else 0]
    data = sorted(places.values(), key=lambda p: p[0])
    (OUT / "layers" / "cities.json").write_text(json.dumps(data, separators=(",", ":"), ensure_ascii=False))
    years = sorted({y for p in data for y in p[3]})
    return {"id": "cities", "title": "Towns and cities by size", "kind": "points", "years": years,
            "file": "layers/cities.json", "unit": "thousand people",
            "legend": [{"color": "#b5502b", "label": "From a source"}, {"color": "#f1c9b8", "label": "Estimated by Buringh"}],
            "note": "Estimated population of the 192 places in Buringh's database of European cities that became "
                    "sizeable towns (by century to 1500, every 50 years after); small towns that never grew are not in it. Dot area follows population; pale "
                    "dots are Buringh's estimates where no figure survives. Positions are as given in the database.",
            "sources": [SOURCES["buringh"]]}


def run(log=print):
    layers = [built(), people(), *climate(), land_cover(), pollen_trees(), ancient_woodland(), land_grades(), superficial(), cities()]
    ids = {l["id"] for l in layers}
    path = OUT / "layers.json"
    old = json.loads(path.read_text())["layers"] if path.exists() else []
    path.write_text(json.dumps({"layers": [l for l in old if l["id"] not in ids] + layers}, ensure_ascii=False, indent=1))
    for l in layers:
        log(f"  {l['id']}: {len(l['years'])} dates, {(OUT / l['file']).stat().st_size // 1024} KB")


if __name__ == "__main__":
    run(lambda m: print(m, file=sys.stderr, flush=True))
