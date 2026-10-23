"""One-off preparation of the E3 raster inputs (needs GDAL, numpy and Pillow; not part of the app or its build).
Writes gzipped JSON grids {per_deg, lon0, lat1, rows} to data/curated/change/layers/ (lon -11..2, lat 49..61).
Rasters are classed or summarised to 1/60 degree; bidb.change_rasters draws them."""
import gzip, json, math, os, subprocess, sys, tempfile
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))   # RES: the research folder holding raw/ and extracts/ (not in git)
RES = os.environ.get("CHANGE_RESEARCH", os.path.join(HERE, "research"))
OUT = HERE
G = os.environ.get("GDAL_BIN", "") # folder of gdal_translate, gdalwarp, gdal_rasterize, ogr2ogr (with a trailing /)
LON0, LON1, LAT0, LAT1, PD = -11.0, 2.0, 49.0, 61.0, 60
W, H = int((LON1 - LON0) * PD), int((LAT1 - LAT0) * PD)
TMP = tempfile.mkdtemp(dir=os.path.join(RES, "tmp"))


def run(*a):
    subprocess.run([str(x) for x in a], check=True, stdout=subprocess.DEVNULL)


def read(tif):
    out = os.path.join(TMP, "dump")
    run(G + "gdal_translate", "-q", "-of", "ENVI", tif, out)
    with open(out + ".hdr") as f:
        hdr = f.read()
    dt = {"1": np.uint8, "2": np.int16, "4": np.float32, "5": np.float64, "12": np.uint16, "3": np.int32, "13": np.uint32}[
        hdr.split("data type = ")[1].split()[0]]
    w = int(hdr.split("samples = ")[1].split()[0]); h = int(hdr.split("lines   = ")[1].split()[0])
    return np.fromfile(out, dtype=dt).reshape(h, w)


def save(name, arr, nodata=None):
    rows = [[None if (nodata is not None and v == nodata) else int(v) for v in r] for r in arr.tolist()]
    with gzip.open(os.path.join(OUT, name + ".json.gz"), "wt") as f:
        json.dump({"per_deg": PD, "lon0": LON0, "lat1": LAT1, "rows": rows}, f, separators=(",", ":"))
    print(name, arr.shape, os.path.getsize(os.path.join(OUT, name + ".json.gz")) // 1024, "KB", flush=True)


def cell_km2():
    r, d = 6371.0007, math.radians(1 / PD)
    lat_n = LAT1 - np.arange(H) / PD
    return (r * r * d * (np.sin(np.radians(lat_n)) - np.sin(np.radians(lat_n - 1 / PD))))[:, None]


def ghsl():
    for y in (1975, 2020):
        src = os.path.join(RES, f"raw/ghsl/builts_{y}_isles.tif")
        dst = os.path.join(TMP, f"g{y}.tif")
        # built m² per 30" cell → summed to 1/60° (average × 4), then % of the cell's area
        run(G + "gdalwarp", "-q", "-overwrite", "-te", LON0, LAT0, LON1, LAT1, "-ts", W, H, "-r", "average", src, dst)
        a = read(dst).astype(float) * 4 / 1e6 / cell_km2() * 100
        save(f"ghsl_built_{y}", np.clip(np.round(a), 0, 100).astype(int))


def burn(src, dst, per_deg, where=None, attr=None, layer=None, extra=()):
    w, h = int((LON1 - LON0) * per_deg), int((LAT1 - LAT0) * per_deg)
    args = [G + "gdal_rasterize", "-q", "-te", LON0, LAT0, LON1, LAT1, "-ts", w, h, "-ot", "Byte", "-init", 0]
    args += ["-a", attr] if attr else ["-burn", 100]
    if where: args += ["-where", where]
    if layer: args += ["-l", layer]
    run(*args, *extra, src, dst)


def awi():
    fine = 1200
    parts = [(f"/vsizip/{RES}/raw/awi/eng.zip/Ancient_Woodland_England.geojson", None, None),
             (f"/vsizip/{RES}/raw/awi/scot.zip/AWI_SCOTLAND.geojson", "ANTIQUITY_ IN ('1a','2a')", None),
             (f"{RES}/raw/awi/wales.json", "category_name NOT LIKE '%Deleted'", None)]
    total = None
    for i, (src, where, _) in enumerate(parts):
        f = os.path.join(TMP, f"awi{i}.tif")
        burn(src, f, fine, where)
        c = os.path.join(TMP, f"awi{i}c.tif")
        run(G + "gdalwarp", "-q", "-overwrite", "-ts", W, H, "-r", "average", "-ot", "Float32", f, c)
        a = read(c).astype(float)
        total = a if total is None else np.maximum(total, a)
        os.remove(f)
        print("awi part", i, flush=True)
    save("ancient_woodland", np.round(total).astype(int))


def classed(src, name, field, classes, srs_from=None, layer=None):
    """Polygons → class codes (classes: {value: code}) → majority per 1/60° cell; 0 = none."""
    gp = os.path.join(TMP, name + ".gpkg")
    case = " ".join(f"WHEN {field} = '{k}' THEN {v}" for k, v in classes.items())
    sql = f"SELECT CASE {case} ELSE 0 END AS cls, geometry FROM \"{layer}\""
    args = [G + "ogr2ogr", "-q", "-f", "GPKG", gp, src, "-dialect", "sqlite", "-sql", sql, "-nln", "x",
            "-t_srs", "EPSG:4326"]
    run(*args)
    f = os.path.join(TMP, name + "_f.tif")
    burn(gp, f, 600, "cls > 0", attr="cls", layer="x")
    c = os.path.join(TMP, name + "_c.tif")
    run(G + "gdalwarp", "-q", "-overwrite", "-ts", W, H, "-r", "mode", "-srcnodata", "None", f, c)
    save(name, read(c).astype(int))


def alc():
    classes = {"Grade 1": 1, "Grade 2": 2, "Grade 3": 3, "Grade 4": 4, "Grade 5": 5, "Non Agricultural": 6, "Urban": 7}
    classed(f"/vsizip/{RES}/raw/ne_alc/alc_provisional.geojson.zip/Agricultural_Land_Classification_Provisional_England.geojson",
            "alc_grades", "alc_grade", classes, layer="Agricultural_Land_Classification_Provisional_England")


SUPERFICIAL = {"TILL": 1, "GLACIAL SAND AND GRAVEL": 2, "ALLUVIUM": 3, "RIVER TERRACE DEPOSITS (UNDIFFERENTIATED)": 3,
               "LACUSTRINE DEPOSITS (UNDIFFERENTIATED)": 3, "PEAT": 4, "RAISED MARINE DEPOSITS (UNDIFFERENTIATED)": 5,
               "BLOWN SAND": 5, "CLAY-WITH-FLINTS": 6, "BRICKEARTH": 6, "SAND AND GRAVEL OF UNCERTAIN AGE AND ORIGIN": 6,
               "CRAG GROUP": 6, "LANDSLIP": 7}


def superficial():
    classed(f"/vsizip/{RES}/raw/bgs625k/bgs625k_shp.zip/BGS_Geology_625k_Shapefile/Superficial/UK_625k_SUPERFICIAL_Geology_Polygons.shp",
            "superficial", "LEX_D", SUPERFICIAL, layer="UK_625k_SUPERFICIAL_Geology_Polygons")


# CORINE: standard CLC colours → class → group (0 = sea / no data)
CLC = {(230, 0, 77): 111, (255, 0, 0): 112, (204, 77, 242): 121, (204, 0, 0): 122, (230, 204, 204): 123,
       (230, 204, 230): 124, (166, 0, 204): 131, (166, 77, 0): 132, (255, 77, 255): 133, (255, 166, 255): 141,
       (255, 230, 255): 142, (255, 255, 168): 211, (255, 255, 0): 212, (230, 230, 0): 213, (230, 128, 0): 221,
       (242, 166, 77): 222, (230, 166, 0): 223, (230, 230, 77): 231, (255, 230, 166): 241, (255, 230, 77): 242,
       (230, 204, 77): 243, (242, 204, 166): 244, (128, 255, 0): 311, (0, 166, 0): 312, (77, 255, 0): 313,
       (204, 242, 77): 321, (166, 255, 128): 322, (166, 230, 77): 323, (166, 242, 0): 324, (230, 230, 230): 331,
       (204, 204, 204): 332, (204, 255, 204): 333, (0, 0, 0): 334, (166, 230, 204): 335, (166, 166, 255): 411,
       (77, 77, 255): 412, (204, 204, 255): 421, (230, 230, 255): 422, (166, 166, 230): 423, (0, 204, 242): 511,
       (128, 242, 230): 512, (0, 255, 166): 521, (166, 255, 230): 522, (230, 242, 255): 523}


def group(c):
    if c < 200: return 1                      # towns, industry, mines, green urban
    if c < 220: return 2                      # arable
    if c == 231: return 3                     # pasture
    if c < 300: return 4                      # mixed farming, orchards
    if c < 320: return 5                      # woods
    if c < 330: return 6                      # moor, heath, grassland, scrub
    if c < 400: return 7                      # rock, beaches, sparse
    if c < 500: return 8                      # bog, marsh, saltmarsh
    if c < 520: return 9                      # lakes and rivers
    return 0


def corine():
    def merc(lat): return math.log(math.tan(math.pi / 4 + math.radians(lat) / 2))
    for y in (2000, 2006, 2012, 2018):           # the 1990 map has no Great Britain
        im = Image.open(os.path.join(RES, f"extracts/corine_clc{y}_isles.png")).convert("RGB")
        a = np.asarray(im); ih, iw = a.shape[:2]
        lut = {k: group(v) for k, v in CLC.items()}
        lat = LAT1 - (np.arange(H) + 0.5) / PD
        py = np.clip(((merc(LAT1) - np.vectorize(merc)(lat)) / (merc(LAT1) - merc(LAT0)) * ih).astype(int), 0, ih - 1)
        px = np.clip(((np.arange(W) + 0.5) / PD / (LON1 - LON0) * iw).astype(int), 0, iw - 1)
        sub = a[py][:, px]
        out = np.zeros((H, W), int)
        for rgb, g in lut.items():
            out[np.all(sub == rgb, axis=-1)] = g
        save(f"corine_{y}", out)


if __name__ == "__main__":
    for step in sys.argv[1:] or ["ghsl", "corine", "alc", "superficial", "awi"]:
        globals()[step]()
