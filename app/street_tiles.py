"""Street-level map detail for areas saved for offline use (local GUI).

"Save this area for offline" on a map downloads the vector tiles of the area in view (zoom 10–15)
from the Protomaps daily build of OpenStreetMap (one PMTiles archive, ODbL, read with HTTP range
requests: only the area's tiles are fetched) into <cache>/street_tiles.sqlite. The server then
serves them at /tiles/<z>/<x>/<y>.mvt and static/vendor/protomaps-leaflet.js draws them.
Adapted from cycle_routes (cycleroutes/offline/basemap.py).
"""
import json
import math
import sqlite3
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from functools import lru_cache

import requests

from bidb.config import USER_AGENT, cache_dir

BUILDS = "https://build-metadata.protomaps.dev/builds.json"
BUILD = "https://build.protomaps.com/{key}"
MIN_ZOOM, MAX_ZOOM, MAX_TILES, WORKERS = 10, 15, 6000, 6
ATTRIBUTION = "© OpenStreetMap contributors, Protomaps"
_lock = threading.Lock()
JOB = {"state": "idle"}                       # progress of the current download, for the GUI


def path():
    return cache_dir() / "street_tiles.sqlite"


def _db():
    db = sqlite3.connect(path(), check_same_thread=False)
    db.executescript("""CREATE TABLE IF NOT EXISTS tiles (z INTEGER, x INTEGER, y INTEGER, data BLOB,
                            PRIMARY KEY (z, x, y));
                        CREATE TABLE IF NOT EXISTS areas (name TEXT, bbox TEXT, tiles INTEGER, bytes INTEGER,
                            saved REAL, compression INTEGER);""")
    return db


class _Ranges:
    def __init__(self, url):
        self.url, self.s = url, requests.Session()
        self.s.headers["User-Agent"] = USER_AGENT

    @lru_cache(maxsize=256)
    def get(self, offset, length):
        for attempt in range(4):
            try:
                r = self.s.get(self.url, timeout=60, headers={"Range": f"bytes={offset}-{offset + length - 1}"})
                if r.status_code in (200, 206):
                    return r.content
            except requests.RequestException:
                pass
            time.sleep(2 * (attempt + 1))
        raise RuntimeError("Street map source unavailable")


def tiles_for(bbox, z):
    s, w, n, e = bbox
    k = 2 ** z
    xy = lambda lat, lon: (int((lon + 180) / 360 * k), int((1 - math.asinh(math.tan(math.radians(lat))) / math.pi) / 2 * k))
    x0, y0 = xy(n, w)
    x1, y1 = xy(s, e)
    return [(z, x, y) for x in range(max(x0, 0), min(x1, k - 1) + 1) for y in range(max(y0, 0), min(y1, k - 1) + 1)]


def plan(bbox):
    """All tiles for a bbox (south, west, north, east) at zoom MIN_ZOOM..MAX_ZOOM."""
    return [t for z in range(MIN_ZOOM, MAX_ZOOM + 1) for t in tiles_for(bbox, z)]


def save_area(name, bbox):
    """Download in the background; JOB reports progress. Refuses areas over MAX_TILES tiles."""
    todo = plan(bbox)
    if len(todo) > MAX_TILES:
        return {"error": f"That area needs {len(todo):,} tiles; zoom in (at most {MAX_TILES:,})."}
    if not _lock.acquire(blocking=False):
        return {"error": "Another area is being saved."}
    JOB.update(state="running", name=name, done=0, total=len(todo), error=None)
    threading.Thread(target=_run, args=(name, bbox, todo), daemon=True).start()
    return {"started": True, "tiles": len(todo)}


def _run(name, bbox, todo):
    from pmtiles.reader import Reader
    try:
        key = requests.get(BUILDS, timeout=30, headers={"User-Agent": USER_AGENT}).json()[-1]["key"]
        reader = Reader(_Ranges(BUILD.format(key=key)).get)
        comp = int(reader.header()["tile_compression"].value)
        db = _db()
        have = {(z, x, y) for z, x, y in db.execute("SELECT z, x, y FROM tiles")}
        todo = [t for t in todo if t not in have]
        stored = size = 0
        with ThreadPoolExecutor(WORKERS) as pool:
            for (z, x, y), data in zip(todo, pool.map(lambda t: reader.get(*t), todo)):
                JOB["done"] += 1
                if data:
                    db.execute("INSERT OR REPLACE INTO tiles VALUES (?,?,?,?)", (z, x, y, data))
                    stored += 1
                    size += len(data)
        db.execute("INSERT INTO areas VALUES (?,?,?,?,?,?)", (name, json.dumps(bbox), stored, size, time.time(), comp))
        db.commit()
        db.close()
        JOB.update(state="done", tiles=stored, bytes=size)
    except Exception as e:                       # noqa: BLE001 - reported to the GUI
        JOB.update(state="error", error=str(e))
    finally:
        _lock.release()


def areas():
    if not path().exists():
        return []
    db = _db()
    rows = [{"name": n, "bbox": json.loads(b), "tiles": t, "mb": round(s / 1e6, 1), "saved": d}
            for n, b, t, s, d, _ in db.execute("SELECT * FROM areas ORDER BY saved DESC")]
    db.close()
    return rows


_reader = {"db": None}


def tile(z, x, y):
    """(bytes, gzip?) or None."""
    if not path().exists():
        return None
    if _reader["db"] is None:
        _reader["db"] = sqlite3.connect(path(), check_same_thread=False)
    db = _reader["db"]
    row = db.execute("SELECT data FROM tiles WHERE z = ? AND x = ? AND y = ?", (z, x, y)).fetchone()
    if not row:
        return None
    comp = db.execute("SELECT compression FROM areas LIMIT 1").fetchone()
    return row[0], bool(comp and comp[0] == 2)


def clear():
    _reader["db"] = None
    if path().exists():
        path().unlink()
