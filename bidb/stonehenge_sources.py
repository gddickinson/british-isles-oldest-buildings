"""Downloads for the Stonehenge model (bidb.stonehenge), each cached once in `<cache>/stonehenge/`:

    osm_stones()        OpenStreetMap stones and stone markers within 120 m (ODbL): [{ref, name, kind, outline}]
    osm_features()      OpenStreetMap features for the earlier stages within 250 m (Aubrey Hole markers, the North
                        and South Barrows, the Heelstone Ditch, the Avenue): [{name, ref, osm, outline}]
    lidar(e, n, size)   Environment Agency LiDAR composite DTM 1 m (OGL), a size × size m square centred on
                        British National Grid e, n → (rows of heights north to south, metres)
    bright_stars(mag)   Yale Bright Star Catalogue, 5th revised edition (Hoffleit and Warren 1991; HEASARC copy):
                        [ra, dec (J2000), pmRA·cos dec, pmDec (arcsec/yr), V, B-V, Bayer name]
"""
import gzip
import os
import struct

import requests

from .config import USER_AGENT, cache_dir
from .http import request_json

CENTRE = (51.178844, -1.826189)
OVERPASS = "https://overpass-api.de/api/interpreter"
WCS = "https://environment.data.gov.uk/spatialdata/lidar-composite-digital-terrain-model-dtm-1m/wcs"
DTM = "13787b9a-26a4-4775-8523-806d13af58fc__Lidar_Composite_Elevation_DTM_1m"
BSC = "https://heasarc.gsfc.nasa.gov/FTP/heasarc/dbase/tdat_files/heasarc_bsc5p.tdat.gz"
ATTRIBUTION = {
    "osm": "Stone positions © OpenStreetMap contributors (ODbL)",
    "lidar": "Ground: Environment Agency LiDAR Composite DTM 1 m, © Environment Agency (Open Government Licence)",
    "stars": "Stars: Yale Bright Star Catalogue, 5th revised edition (Hoffleit and Warren 1991, CDS V/50; HEASARC)",
}


def _dir():
    d = os.path.join(cache_dir(), "stonehenge")
    os.makedirs(d, exist_ok=True)
    return d


def _download(url, name, params=None, timeout=120):
    path = os.path.join(_dir(), name)
    if not os.path.exists(path):
        r = requests.get(url, params=params, headers={"User-Agent": USER_AGENT}, timeout=timeout)
        r.raise_for_status()
        with open(path + ".part", "wb") as f:
            f.write(r.content)
        os.replace(path + ".part", path)
    with open(path, "rb") as f:
        return f.read()


def osm_stones():
    query = (f"[out:json][timeout:60];(nwr(around:120,{CENTRE[0]},{CENTRE[1]})[natural=stone];"
             f"nwr(around:120,{CENTRE[0]},{CENTRE[1]})[historic~\"^(stone|memorial)$\"][ref];);out tags geom;")
    res = request_json(OVERPASS, data={"data": query}, method="POST", min_interval=2)
    out = []
    for e in res["elements"]:
        t = e.get("tags", {})
        geom = e.get("geometry") or [{"lat": e["lat"], "lon": e["lon"]}]
        out.append({"ref": t.get("ref"), "name": t.get("name"), "osm": f"{e['type']}/{e['id']}",
                    "kind": "marker" if t.get("historic") == "memorial" else "stone",
                    "outline": [(p["lat"], p["lon"]) for p in geom]})
    return out


def osm_features():
    query = (f"[out:json][timeout:60];nwr(around:250,{CENTRE[0]},{CENTRE[1]})"
             f"[name~\"^(Aubrey Hole|North Barrow|South Barrow|Heelstone Ditch|The Avenue)$\"];out tags geom;")
    res = request_json(OVERPASS, data={"data": query}, method="POST", min_interval=2)
    return [{"name": e["tags"]["name"], "ref": e["tags"].get("ref"), "osm": f"{e['type']}/{e['id']}",
             "outline": [(p["lat"], p["lon"]) for p in (e.get("geometry") or [{"lat": e["lat"], "lon": e["lon"]}])]}
            for e in res["elements"] if e.get("geometry") or "lat" in e]


def read_tiff(data):
    """Heights from an uncompressed single-band float32 TIFF (the WCS answer) → rows, top first."""
    order = "<" if data[:2] == b"II" else ">"
    (ifd,) = struct.unpack(order + "I", data[4:8])
    (n,) = struct.unpack(order + "H", data[ifd:ifd + 2])
    tags = {}
    for i in range(n):
        tag, typ, count, value = struct.unpack(order + "HHII", data[ifd + 2 + 12 * i: ifd + 14 + 12 * i])
        if typ == 3 and count == 1:                     # SHORT stored in the first half of the value field
            value = struct.unpack(order + "H", data[ifd + 10 + 12 * i: ifd + 12 + 12 * i])[0]
        tags[tag] = (typ, count, value)
    width, height = tags[256][2], tags[257][2]
    if tags.get(259, (0, 0, 1))[2] != 1 or tags[258][2] != 32:
        raise ValueError("expected an uncompressed 32-bit TIFF")
    def longs(tag):
        typ, count, value = tags[tag]
        if count == 1:
            return [value]
        size = 4 if typ == 4 else 2
        return list(struct.unpack(order + ("I" if typ == 4 else "H") * count, data[value: value + count * size]))

    def floats(offset, count):
        return struct.unpack(order + "f" * count, data[offset: offset + 4 * count])

    rows = [[0.0] * width for _ in range(height)]
    if 322 in tags:                                     # tiled
        tw, th = tags[322][2], tags[323][2]
        across = -(-width // tw)
        for i, off in enumerate(longs(324)):
            vals, x0, y0 = floats(off, tw * th), (i % across) * tw, (i // across) * th
            for r in range(min(th, height - y0)):
                w = min(tw, width - x0)
                rows[y0 + r][x0:x0 + w] = vals[r * tw: r * tw + w]
    else:                                               # strips
        per = tags.get(278, (0, 0, height))[2]
        for i, off in enumerate(longs(273)):
            for r in range(min(per, height - i * per)):
                rows[i * per + r] = list(floats(off + 4 * width * r, width))
    return rows


def lidar(e, n, size):
    e0, n0, half = round(e), round(n), size // 2
    params = {"service": "WCS", "version": "2.0.1", "request": "GetCoverage", "CoverageId": DTM,
              "format": "image/tiff", "subset": [f"E({e0 - half},{e0 + half})", f"N({n0 - half},{n0 + half})"]}
    return read_tiff(_download(WCS, f"dtm_{e0}_{n0}_{size}.tif", params))


def bright_stars(mag=5.5):
    text = gzip.decompress(_download(BSC, "bsc5p.tdat.gz")).decode("latin-1")
    head, _, body = text.partition("<DATA>")
    fields = next(line for line in head.splitlines() if line.startswith("line[1]")).split("=", 1)[1].split()
    col = {f: i for i, f in enumerate(fields)}
    stars = []
    for line in body.splitlines():
        v = line.split("|")
        if len(v) < len(fields) or not v[col["vmag"]].strip() or not v[col["ra"]].strip():
            continue
        vmag = float(v[col["vmag"]])
        if vmag > mag:
            continue
        num = lambda f: float(v[col[f]]) if v[col[f]].strip() else 0.0   # noqa: E731
        stars.append([num("ra"), num("dec"), num("pmra"), num("pmdec"), vmag, num("bv_color"),
                      " ".join(v[col["alt_name"]].split())])
    return stars
