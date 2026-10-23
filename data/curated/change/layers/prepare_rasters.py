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


GHS_POP = ("https://jeodpp.jrc.ec.europa.eu/ftp/jrc-opendata/GHSL/GHS_POP_GLOBE_R2023A/GHS_POP_E{y}_GLOBE_R2023A_4326_30ss/"
           "V1-0/GHS_POP_E{y}_GLOBE_R2023A_4326_30ss_V1_0.zip/GHS_POP_E{y}_GLOBE_R2023A_4326_30ss_V1_0.tif")


def ghs_pop():
    """People per km² at 1/60°, for the observed epochs 1975–2020 (only the isles' window is read from each zip)."""
    for y in range(1975, 2021, 5):
        crop, dst = os.path.join(TMP, f"p{y}c.tif"), os.path.join(TMP, f"p{y}.tif")
        run(G + "gdal_translate", "-q", "-projwin", LON0, LAT1, LON1, LAT0, "/vsizip//vsicurl/" + GHS_POP.format(y=y), crop)
        run(G + "gdalwarp", "-q", "-overwrite", "-te", LON0, LAT0, LON1, LAT1, "-ts", W, H, "-r", "sum", crop, dst)
        a = np.clip(read(dst).astype(float), 0, None) / cell_km2()
        save(f"ghs_pop_{y}", np.round(a).astype(int))
        os.remove(crop)


CRU = "https://crudata.uea.ac.uk/cru/data/hrg/cru_ts_4.10/cruts.2604091129.v4.10/{v}/cru_ts4.10.{a}.{b}.{v}.dat.nc.gz"


def cru():
    """CRU TS 4.10 yearly grids over the isles at 0.5°, 1901–2025: mean temperature (°C) and rainfall (mm); months
    with no station within reach (the value is then the climatology) are left out."""
    from scipy.io import netcdf_file
    out = {"per_deg": 2, "lon0": LON0, "lat1": LAT1, "tmp": {}, "pre": {}}
    for a in range(1901, 2022, 10):
        for v in ("tmp", "pre"):
            gz, nc = os.path.join(TMP, "c.nc.gz"), os.path.join(TMP, "c.nc")
            run("curl", "-s", "-f", "-o", gz, CRU.format(v=v, a=a, b=min(a + 9, 2025)))
            run("gunzip", "-f", gz)
            f = netcdf_file(nc, "r", mmap=True)
            lat, lon = f.variables["lat"][:], f.variables["lon"][:]
            r = np.where((lat > LAT0) & (lat < LAT1))[0]; c = np.where((lon > LON0) & (lon < LON1))[0]
            x = np.array(f.variables[v][:, r[0]:r[-1] + 1, c[0]:c[-1] + 1], dtype=float)
            stn = np.array(f.variables["stn"][:, r[0]:r[-1] + 1, c[0]:c[-1] + 1], dtype=float)
            f.close(); os.remove(nc)
            x[x > 1e30] = np.nan
            x[stn <= 0] = np.nan                                  # no station within reach: climatology, not data
            years = x.shape[0] // 12
            yearly = x[:years * 12].reshape(years, 12, *x.shape[1:])
            yearly = yearly.mean(axis=1) if v == "tmp" else yearly.sum(axis=1)   # a year with a month missing → nan
            for k in range(years):                                # each year's grid, rows north → south
                out[v][a + k] = [[None if np.isnan(q) else round(float(q), 2) for q in row] for row in yearly[k][::-1]]
            print(v, a, flush=True)
    with gzip.open(os.path.join(OUT, "cru_years.json.gz"), "wt") as fh:
        json.dump(out, fh, separators=(",", ":"))


S3 = "https://download.pangaea.de/dataset/945729/files/Data_S3_BRITICE_CHRONO_empirical_reconstruction_GIS_data_zip.zip"
S5 = ("/vsizip//vsicurl/https://download.pangaea.de/dataset/945729/files/Data_S5_BRITICE_CHRONO_palaeotopographies_and_"
      "coastlines_GIS_data.zip/Data S5 BRITICE CHRONO palaeotopographies and coastlines GIS data/{}_PT_500m.tif")
ETOPO = "/vsicurl/https://www.ngdc.noaa.gov/mgg/global/relief/ETOPO2022/data/30s/30s_surface_elev_gtif/ETOPO_2022_v1_30s_N90W180_surface.tif"


def ice_coast():
    """Each 1,000 years from 31 to 1 ka: 1 = land then, under the sea now; 2 = sea then, land now; 3 = ice sheet (the
    reconstruction's optimum); 4 = ice in its largest version only. 1/30° grid; ice from BRITICE-CHRONO S3 polygons,
    land and sea from the S5 palaeotopographies (elevation above that time's sea level) against ETOPO 2022 today."""
    e0, e1, n0, n1 = -12.0, 9.0, 48.0, 62.0             # wider than the isles' window: Doggerland lies east of 2°E
    pd, w, h = 30, int((e1 - e0) * 30), int((n1 - n0) * 30)
    warp = lambda src, dst, extra=(): run(G + "gdalwarp", "-q", "-overwrite", "-t_srs", "EPSG:4326", "-te", e0, n0,
                                          e1, n1, "-ts", w, h, "-r", "average", "-ot", "Float32", "-novshiftgrid",
                                          *extra, src, dst)   # heights stay above sea level (no geoid shift)
    crop, now = os.path.join(TMP, "etopo.tif"), os.path.join(TMP, "now.tif")
    run(G + "gdal_translate", "-q", "-projwin", e0, n1, e1, n0, ETOPO, crop)
    warp(crop, now)
    land_now = read(now) > 0
    zipf = os.path.join(TMP, "s3.zip")
    run("curl", "-s", "-f", "-o", zipf, S3)
    names = subprocess.run(["unzip", "-Z1", zipf], capture_output=True, text=True).stdout.splitlines()
    shp = lambda ka, kind: next((n for n in names if n.endswith(".shp") and f"/{kind}/" in n.replace("Optimum", "optimum").replace("Max", "max")
                                 and n.rsplit("/", 1)[1].replace("_ka", "ka").startswith(f"{ka}ka")), None)
    out = {"per_deg": pd, "lon0": e0, "lat1": n1, "dates": {}}
    for ka in range(31, 0, -1):
        pt = os.path.join(TMP, f"pt{ka}.tif"); warp(S5.format(ka), pt, ("-srcnodata", "-32768"))
        then = read(pt)
        cls = np.zeros((h, w), int)
        cls[(then > 0) & ~land_now] = 1
        cls[(then <= 0) & land_now] = 2
        for kind, code in (("max", 4), ("optimum", 3)):
            n = shp(ka, kind)
            if not n:
                continue
            r, gp = os.path.join(TMP, f"ice{ka}{kind}.tif"), os.path.join(TMP, f"ice{ka}{kind}.gpkg")
            run(G + "ogr2ogr", "-q", "-overwrite", "-f", "GPKG", "-t_srs", "EPSG:4326", "-nln", "ice", gp, f"/vsizip/{zipf}/{n}")
            run(G + "gdal_rasterize", "-q", "-te", e0, n0, e1, n1, "-ts", w, h, "-ot", "Byte", "-burn", 1,
                "-init", 0, "-at", "-l", "ice", gp, r)
            cls[read(r) > 0] = code
        out["dates"][ka] = cls.tolist()
        print("ice/coast", ka, "ka", int((cls == 1).sum()), int((cls == 3).sum()), flush=True)
    with gzip.open(os.path.join(OUT, "ice_coast.json.gz"), "wt") as fh:
        json.dump(out, fh, separators=(",", ":"))


NTL = "https://api.figshare.com/v2/articles/9828827"


def night_lights():
    """Harmonised night-time lights (Li et al. 2020, figshare v10; DMSP 1992–2013, VIIRS converted 2014–2024), digital
    number 0–63 averaged to 1/60° (the isles' window read from each global file)."""
    files = json.loads(subprocess.run(["curl", "-s", NTL], capture_output=True, text=True).stdout)["files"]
    for f in files:
        name = f["name"]
        if not name.startswith("Harmonized_DN_NTL_"):
            continue
        y = int(name.split("_")[3])
        crop, dst = os.path.join(TMP, f"n{y}c.tif"), os.path.join(TMP, f"n{y}.tif")
        run(G + "gdal_translate", "-q", "-projwin", LON0, LAT1, LON1, LAT0, "/vsicurl/https://ndownloader.figshare.com/files/"
            + str(f["id"]), crop)
        run(G + "gdalwarp", "-q", "-overwrite", "-te", LON0, LAT0, LON1, LAT1, "-ts", W, H, "-r", "average", "-ot", "Float32", crop, dst)
        save(f"ntl_{y}", np.round(read(dst)).astype(int))
        os.remove(crop)


GFC = "/vsicurl/https://storage.googleapis.com/earthenginepartners-hansen/GFC-2024-v1.12/Hansen_GFC-2024-v1.12_lossyear_{}.tif"


def forest_loss():
    """Hansen Global Forest Change v1.12: for each 1/40° cell (100 × 100 pixels of 0.00025°) the share of the cell
    where tree cover was lost in each year 2001–2024 → gfc_loss.json.gz {per_deg, lon0, lat1, years: {y: rows of ‰}}."""
    pd = 40
    w, h = int((LON1 - LON0) * pd), int((LAT1 - LAT0) * pd)
    counts = np.zeros((24, h, w), np.int32)
    for tile, (top, left) in {"70N_020W": (70, -20), "70N_010W": (70, -10), "70N_000E": (70, 0), "60N_020W": (60, -20),
                              "60N_010W": (60, -10), "60N_000E": (60, 0), "50N_010W": (50, -10), "50N_000E": (50, 0)}.items():
        x0, x1 = max(LON0, left), min(LON1, left + 10)
        y1, y0 = min(LAT1, top), max(LAT0, top - 10)
        if x0 >= x1 or y0 >= y1:
            continue
        crop = os.path.join(TMP, "gfc")
        run(G + "gdal_translate", "-q", "-of", "ENVI", "-projwin", x0, y1, x1, y0, GFC.format(tile), crop)
        with open(crop + ".hdr") as f:
            hdr = f.read()
        cw = int(hdr.split("samples = ")[1].split()[0]); ch = int(hdr.split("lines   = ")[1].split()[0])
        a = np.memmap(crop, dtype=np.uint8, mode="r", shape=(ch, cw))
        r0, c0 = round((LAT1 - y1) * pd), round((x0 - LON0) * pd)
        for i in range(ch // 100):                       # one row of cells at a time
            band = np.asarray(a[i * 100:(i + 1) * 100, :(cw // 100) * 100]).reshape(100, cw // 100, 100)
            for yr in range(1, 25):
                counts[yr - 1, r0 + i, c0:c0 + cw // 100] += (band == yr).sum(axis=(0, 2))
        del a
        os.remove(crop)
        print("gfc", tile, flush=True)
    per_mille = np.round(counts * 1000 / 10000).astype(int)          # ‰ of the cell's pixels, each year
    out = {"per_deg": pd, "lon0": LON0, "lat1": LAT1, "years": {2000 + k + 1: per_mille[k].tolist() for k in range(24)}}
    with gzip.open(os.path.join(OUT, "gfc_loss.json.gz"), "wt") as fh:
        json.dump(out, fh, separators=(",", ":"))


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
    for step in sys.argv[1:] or ["ghsl", "ghs_pop", "corine", "alc", "superficial", "awi", "cru", "ice_coast", "night_lights", "forest_loss"]:
        globals()[step]()
