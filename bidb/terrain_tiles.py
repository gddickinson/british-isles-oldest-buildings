"""Ground heights from the Terrain Tiles on AWS (Mapzen "terrarium" PNGs; open data, no key), read with the stdlib.

Sources by area (the tiles' own documentation): the Environment Agency's LiDAR for much of England, SRTM and
EU-DEM elsewhere in the isles, GMTED/ETOPO1 at small zooms. Tiles are cached once in `<cache>/terrain/z/x/y.png`.

    Terrain().height(lat, lon, zoom)  ground height in metres (bilinear between pixel centres)
    decode_png(data)                  -> (width, height, rows of RGB bytes) for 8-bit RGB/RGBA PNGs
"""
import math
import struct
import zlib

import requests

from .config import USER_AGENT, cache_dir

URL = "https://s3.amazonaws.com/elevation-tiles-prod/terrarium/{z}/{x}/{y}.png"
ATTRIBUTION = ("Terrain Tiles (Mapzen / AWS Open Data): Environment Agency LiDAR (OGL), SRTM, EU-DEM, GMTED, ETOPO1; "
               "see https://github.com/tilezen/joerd/blob/master/docs/attribution.md")
SIZE = 256


def _paeth(a, b, c):
    p = a + b - c
    pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
    return a if pa <= pb and pa <= pc else b if pb <= pc else c


def decode_png(data):
    """Width, height and the unfiltered rows (bytes, `channels` per pixel) of a non-interlaced 8-bit PNG."""
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError("not a PNG")
    pos, idat, width = 8, [], None
    while pos < len(data):
        n, kind = struct.unpack(">I4s", data[pos:pos + 8])
        body = data[pos + 8:pos + 8 + n]
        if kind == b"IHDR":
            width, height, depth, colour, _, _, interlace = struct.unpack(">IIBBBBB", body)
            if depth != 8 or colour not in (2, 6) or interlace:
                raise ValueError(f"unsupported PNG (depth {depth}, colour type {colour}, interlace {interlace})")
            bpp = 3 if colour == 2 else 4
        elif kind == b"IDAT":
            idat.append(body)
        elif kind == b"IEND":
            break
        pos += 12 + n
    raw = zlib.decompress(b"".join(idat))
    stride, rows, prev = width * bpp, [], bytearray(width * bpp)
    for r in range(height):
        f = raw[r * (stride + 1)]
        line = bytearray(raw[r * (stride + 1) + 1:(r + 1) * (stride + 1)])
        if f == 1:
            for i in range(bpp, stride):
                line[i] = (line[i] + line[i - bpp]) & 255
        elif f == 2:
            for i in range(stride):
                line[i] = (line[i] + prev[i]) & 255
        elif f == 3:
            for i in range(stride):
                line[i] = (line[i] + ((line[i - bpp] if i >= bpp else 0) + prev[i]) // 2) & 255
        elif f == 4:
            for i in range(stride):
                line[i] = (line[i] + _paeth(line[i - bpp] if i >= bpp else 0, prev[i],
                                            prev[i - bpp] if i >= bpp else 0)) & 255
        rows.append(line)
        prev = line
    return width, height, rows, bpp


def heights(data):
    """A terrarium tile's PNG → list of rows of heights in metres (R * 256 + G + B / 256 - 32768)."""
    w, h, rows, bpp = decode_png(data)
    return [[line[i] * 256 + line[i + 1] + line[i + 2] / 256 - 32768 for i in range(0, w * bpp, bpp)] for line in rows]


def tile_xy(lat, lon, z):
    """Fractional Web Mercator tile coordinates of a point."""
    n = 2 ** z
    x = (lon + 180) / 360 * n
    y = (1 - math.asinh(math.tan(math.radians(lat))) / math.pi) / 2 * n
    return x, y


def metres_per_pixel(lat, z):
    return 40075016.686 * math.cos(math.radians(lat)) / (SIZE * 2 ** z)


class Terrain:
    """Ground heights from cached tiles (each decoded once per object)."""

    def __init__(self, session=None):
        self.tiles = {}
        self.session = session or requests.Session()
        self.session.headers.setdefault("User-Agent", USER_AGENT)
        self.downloads = 0

    def tile(self, z, x, y):
        key = (z, x, y)
        if key not in self.tiles:
            path = cache_dir() / "terrain" / str(z) / str(x) / f"{y}.png"
            if not path.exists():
                resp = self.session.get(URL.format(z=z, x=x, y=y), timeout=60)
                resp.raise_for_status()
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(resp.content)
                self.downloads += 1
            self.tiles[key] = heights(path.read_bytes())
        return self.tiles[key]

    def pixel(self, z, px, py):
        """Height at a whole pixel of the zoom's world grid."""
        n = SIZE * 2 ** z
        px, py = px % n, min(max(py, 0), n - 1)
        return self.tile(z, px // SIZE, py // SIZE)[py % SIZE][px % SIZE]

    def height(self, lat, lon, z=12):
        """Ground height in metres at a point, bilinear between the four nearest pixel centres."""
        x, y = tile_xy(lat, lon, z)
        fx, fy = x * SIZE - 0.5, y * SIZE - 0.5
        x0, y0 = math.floor(fx), math.floor(fy)
        tx, ty = fx - x0, fy - y0
        a, b = self.pixel(z, x0, y0), self.pixel(z, x0 + 1, y0)
        c, d = self.pixel(z, x0, y0 + 1), self.pixel(z, x0 + 1, y0 + 1)
        return (a * (1 - tx) + b * tx) * (1 - ty) + (c * (1 - tx) + d * tx) * ty
