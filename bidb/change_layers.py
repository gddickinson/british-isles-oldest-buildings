"""Map layers for "Change over time" (roadmap E3): HYDE 3.2.1 population density and cropland through the
centuries as small coloured PNG overlays that follow the year slider.

HYDE's global 5-arc-minute grids are read one file at a time from the 5.3 GB archive on DANS (bidb.remote_zip),
cropped to the isles (lon −11..2, lat 49..61), kept as compact JSON in <cache>/hyde/, and drawn as palette PNGs
already reprojected to Web Mercator rows, so Leaflet's image overlay lines up with the map.

    python -m bidb.change_layers        → app/static/data/change/layers/hyde_<var>.json ({year: PNG data URI}; one
                                          file per variable, as the hosted copy allows 511 files) + layers.json
"""
import base64
import json
import math
import struct
import sys
import zlib

from .config import ROOT, cache_dir

ARCHIVE = "https://archaeology.datastations.nl/api/access/datafile/5490328"     # HYDE3_2_1-baseline.zip
OUT = ROOT / "app" / "static" / "data" / "change"
LON0, LON1, LAT0, LAT1, PER_DEG = -11.0, 2.0, 49.0, 61.0, 12
YEARS = [-4000, -3000, -2000, -1000, 0] + list(range(100, 1701, 100)) + [1750, 1800, 1850, 1900, 1950, 2000, 2017]
HYDE = {"short": "HYDE 3.2.1 (Klein Goldewijk et al. 2017)",
        "citation": "Klein Goldewijk, K., Beusen, A., Doelman, J., Stehfest, E. (2017) Anthropogenic land use estimates "
                    "for the Holocene – HYDE 3.2. Earth System Science Data 9:927–953, doi:10.5194/essd-9-927-2017. "
                    "Data: HYDE 3.2.1 baseline, DANS, doi:10.17026/dans-25g-gez3",
        "licence": "CC BY 3.0", "url": "https://doi.org/10.17026/dans-25g-gez3"}
# sequential ramps, light → dark (one hue each); a cell below the first edge stays transparent
LAYERS = {
    "popd": {"title": "People per km² (modelled)", "file": "popd_{y}.asc", "dir": "pop", "unit": "people per km²",
             "edges": [0.5, 2, 5, 10, 25, 50, 100, 500],
             "colors": ["#f6e3c8", "#efc795", "#e6a866", "#d68a43", "#bf6d2c", "#9f5420", "#7a3e17", "#55290f"],
             "note": "HYDE spreads each country's estimated population over the land by models of where people lived "
                     "(soils, climate, distance to water and towns); a picture of the estimates, not a census map. "
                     "Before about 1800 it rests on few figures."},
    "cropland": {"title": "Cropland (modelled)", "file": "cropland{y}.asc", "dir": "lu", "unit": "% of land",
                 "share": True, "edges": [1, 5, 10, 20, 30, 40, 55, 70],
                 "colors": ["#e8f2d9", "#cfe5b0", "#b1d487", "#8fc061", "#6ca842", "#4c8d2e", "#357023", "#22531a"],
                 "note": "Arable land as a share of each cell, from HYDE's country estimates spread by soil suitability "
                         "and population; pasture and grazing are not included."},
    "grazing": {"title": "Pasture and grazing (modelled)", "file": "grazing{y}.asc", "dir": "lu", "unit": "% of land",
                "share": True, "edges": [1, 5, 10, 20, 30, 40, 55, 70],
                "colors": ["#f3ecd2", "#e6d9a8", "#d6c27c", "#c2a956", "#a98f3b", "#8b742a", "#6b591f", "#4a3d15"],
                "note": "Land grazed by livestock as a share of each cell: managed pasture and rough grazing "
                        "(rangeland) together, from HYDE's country estimates spread by climate and population."},
    "uopp": {"title": "Built-up area (modelled)", "file": "uopp_{y}.asc", "dir": "pop", "unit": "% of land",
             "share": True, "edges": [0.2, 0.5, 1, 2, 5, 10, 20, 40],
             "colors": ["#ece3ee", "#dccbe0", "#c9afd0", "#b391bd", "#9b72a8", "#82548f", "#673a73", "#4b2554"],
             "note": "Towns and other built-up land as a share of each cell, modelled by HYDE from its urban "
                     "population estimates and typical town densities; compare the satellite built-up layer for 1975 "
                     "and 2020."},
}


def tag(y):
    return f"{-y}BC" if y < 0 else f"{y}AD"


def member(var, y):
    spec = LAYERS[var]
    return f"baseline/asc/{tag(y)}_{spec['dir']}/{spec['file'].format(y=tag(y))}"


def cell_km2(lat_s):
    """Area of a 1/12° cell whose south edge is at lat_s (spherical earth, as HYDE)."""
    r, d = 6371.0007, math.radians(1 / PER_DEG)
    return r * r * d * (math.sin(math.radians(lat_s + 1 / PER_DEG)) - math.sin(math.radians(lat_s)))


def crop(path, share=False):
    """Rows north → south of the isles window from an ESRI ASCII grid (None = no data)."""
    r0, r1 = round((90 - LAT1) * PER_DEG), round((90 - LAT0) * PER_DEG)
    c0, c1 = round((LON0 + 180) * PER_DEG), round((LON1 + 180) * PER_DEG)
    with open(path) as f:
        hdr = dict(f.readline().split() for _ in range(6))
        nodata = float(hdr.get("NODATA_value", hdr.get("nodata_value", -9999)))
        rows = []
        for i, line in enumerate(f):
            if i < r0:
                continue
            if i >= r1:
                break
            lat_s = 90 - (i + 1) / PER_DEG
            vals = [float(v) for v in line.split()[c0:c1]]
            rows.append([None if v == nodata else round(100 * v / cell_km2(lat_s), 2) if share else round(v, 3)
                         for v in vals])
    return rows


def grid(var, y, index):
    """Cropped grid for one variable and year, cached as JSON in <cache>/hyde/."""
    cache = cache_dir() / "hyde"
    cache.mkdir(parents=True, exist_ok=True)
    out = cache / f"{var}_{y}.json"
    if out.exists():
        return json.loads(out.read_text())
    from .remote_zip import extract
    name = member(var, y)
    asc = extract(index[name], cache / name.rsplit("/", 1)[1])
    try:
        rows = crop(asc, LAYERS[var].get("share"))
    finally:
        asc.unlink(missing_ok=True)
    out.write_text(json.dumps(rows, separators=(",", ":")))
    return rows


def _merc(lat):
    return math.log(math.tan(math.pi / 4 + math.radians(lat) / 2))


def png(rows, edges, colors, scale=2, per_deg=PER_DEG):
    """Palette PNG (index 0 transparent) with rows resampled to Web Mercator, `scale` output rows per source row.
    Rows run north → south from LAT1 at `per_deg` cells per degree; a value v gets the colour of the last edge ≤ v."""
    h, w = len(rows) * scale, len(rows[0])
    y0, y1 = _merc(LAT1), _merc(LAT0)
    raw = bytearray()
    for j in range(h):
        lat = math.degrees(2 * math.atan(math.exp(y0 + (y1 - y0) * (j + 0.5) / h)) - math.pi / 2)
        src = rows[min(len(rows) - 1, int((LAT1 - lat) * per_deg))]
        raw.append(0)                                   # filter: none
        for v in src:
            k = 0
            if v is not None:
                for i, e in enumerate(edges):
                    if v >= e:
                        k = i + 1
            raw.append(k)
    pal = b"\0\0\0" + b"".join(bytes.fromhex(c[1:]) for c in colors)
    trns = b"\0" + b"\xff" * len(colors)

    def chunk(t, d):
        return struct.pack(">I", len(d)) + t + d + struct.pack(">I", zlib.crc32(t + d) & 0xFFFFFFFF)
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 3, 0, 0, 0)) + chunk(b"PLTE", pal)
            + chunk(b"tRNS", trns) + chunk(b"IDAT", zlib.compress(bytes(raw), 9)) + chunk(b"IEND", b""))


def legend(spec):
    e = spec["edges"]
    return [{"color": c, "label": (f"{e[i]:g}–{e[i + 1]:g}" if i + 1 < len(e) else f"{e[i]:g}+")}
            for i, c in enumerate(spec["colors"])]


def run(log=print):
    from .remote_zip import members
    index = None
    (OUT / "layers").mkdir(parents=True, exist_ok=True)
    meta = []
    for var, spec in LAYERS.items():
        pack = {}
        for y in YEARS:
            if not (cache_dir() / "hyde" / f"{var}_{y}.json").exists() and index is None:
                index = members(ARCHIVE)
            rows = grid(var, y, index)
            pack[y] = "data:image/png;base64," + base64.b64encode(png(rows, spec["edges"], spec["colors"])).decode()
            log(f"  {var} {y}")
        (OUT / "layers" / f"hyde_{var}.json").write_text(json.dumps(pack, separators=(",", ":")))
        meta.append({"id": f"hyde_{var}", "title": spec["title"], "kind": "grid", "years": YEARS,
                     "file": f"layers/hyde_{var}.json", "bounds": [[LAT0, LON0], [LAT1, LON1]],
                     "unit": spec["unit"], "legend": legend(spec), "note": spec["note"], "source": HYDE, "modelled": True})
    path = OUT / "layers.json"                      # keep the fixed layers of bidb.change_geology
    old = json.loads(path.read_text())["layers"] if path.exists() else []
    keep = [l for l in old if not l["id"].startswith("hyde_")]
    path.write_text(json.dumps({"layers": meta + keep}, ensure_ascii=False, indent=1))
    size = sum(p.stat().st_size for p in (OUT / "layers").glob("hyde_*.json"))
    log(f"{len(meta)} layers × {len(YEARS)} years, {size // 1024} KB")


if __name__ == "__main__":
    run(lambda m: print(m, file=sys.stderr, flush=True))
