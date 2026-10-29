"""Stonehenge in 3D: the LiDAR TIFF reader, placing the plan on the ground, the complete monument's layout, and the
sky positions of stonehenge_astro.js (against Meeus's worked examples)."""
import json
import math
import shutil
import struct
import subprocess
import unittest
from pathlib import Path

from bidb import stonehenge_layout as L
from bidb.stonehenge_sources import read_tiff

ROOT = Path(__file__).resolve().parent.parent
CURATED = ROOT / "data" / "curated" / "stonehenge"


def tiff(values, width, height, order=">", tile=None):
    """A single-band float32 TIFF, in strips (one row each) or square tiles."""
    entries, blobs = [], []
    data_at = 8 + 2 + 12 * 12 + 4

    def put(tag, typ, count, value):
        entries.append((tag, typ, count, value))

    if tile:
        across, down = -(-width // tile), -(-height // tile)
        chunks = []
        for ty in range(down):
            for tx in range(across):
                chunk = []
                for r in range(tile):
                    for c in range(tile):
                        y, x = ty * tile + r, tx * tile + c
                        chunk.append(values[y][x] if y < height and x < width else 0.0)
                chunks.append(struct.pack(order + "f" * len(chunk), *chunk))
    else:
        chunks = [struct.pack(order + "f" * width, *row) for row in values]
    n = len(chunks)
    offsets_at = data_at
    sizes_at = offsets_at + 4 * n
    first = sizes_at + 4 * n
    offs, pos = [], first
    for ch in chunks:
        offs.append(pos)
        pos += len(ch)
    short = lambda v: (v << 16) if order == ">" else v      # noqa: E731  SHORT in the value field's first half
    put(256, 3, 1, short(width)); put(257, 3, 1, short(height)); put(258, 3, 1, short(32)); put(259, 3, 1, short(1))
    put(262, 3, 1, short(1)); put(277, 3, 1, short(1)); put(339, 3, 1, short(3))
    if tile:
        put(322, 3, 1, short(tile)); put(323, 3, 1, short(tile)); put(324, 4, n, offsets_at); put(325, 4, n, sizes_at)
    else:
        put(273, 4, n, offsets_at); put(278, 3, 1, short(1)); put(279, 4, n, sizes_at)
    while len(entries) < 12:
        put(65000 + len(entries), 3, 1, 0)
    head = (b"MM" if order == ">" else b"II") + struct.pack(order + "HI", 42, 8)
    ifd = struct.pack(order + "H", 12) + b"".join(struct.pack(order + "HHII", *e) for e in entries) + struct.pack(order + "I", 0)
    body = struct.pack(order + "I" * n, *offs) + struct.pack(order + "I" * n, *map(len, chunks)) + b"".join(chunks)
    return head + ifd + body


class TiffTest(unittest.TestCase):
    def test_strips_and_tiles(self):
        vals = [[100 + r + c / 10 for c in range(5)] for r in range(3)]
        for kw in ({"order": ">"}, {"order": "<"}, {"order": ">", "tile": 4}, {"order": "<", "tile": 2}):
            got = read_tiff(tiff(vals, 5, 3, **kw))
            self.assertEqual(len(got), 3)
            for r in range(3):
                for c in range(5):
                    self.assertAlmostEqual(got[r][c], vals[r][c], places=4, msg=kw)


class LayoutTest(unittest.TestCase):
    def test_register_recovers_a_rotation_and_shift(self):
        lat0, lon0 = 51.1788, -1.8262
        plan = [{"outline": [(15 * math.sin(a) + dx, 15 * math.cos(a) + dy) for dx, dy in ((0, 0), (1, 0), (1, 0.5))]}
                for a in [i * 0.4 for i in range(15)]]
        theta, shift = math.radians(1.5), (2.0, -3.0)
        osm = []
        for s in plan:
            pts = []
            for p in s["outline"]:
                x, y = L.rotate(p, theta)
                x, y = x + shift[0], y + shift[1]
                pts.append((lat0 + y / 110574, lon0 + x / (111320 * math.cos(math.radians(lat0)))))
            osm.append({"kind": "stone", "outline": pts})
        fit = L.register(plan, osm, lat0, lon0)
        self.assertAlmostEqual(fit["theta"], theta, places=4)
        self.assertAlmostEqual(fit["shift"][0], 2.0, places=2)
        self.assertAlmostEqual(fit["shift"][1], -3.0, places=2)
        self.assertLess(fit["rms"], 0.01)

    def test_circle_and_mirror(self):
        cx, cy, r = L.fit_circle([(3 + 10 * math.cos(a), -2 + 10 * math.sin(a)) for a in (0.1, 1, 2, 3, 4.5, 5.5)])
        self.assertAlmostEqual(cx, 3, places=6); self.assertAlmostEqual(cy, -2, places=6); self.assertAlmostEqual(r, 10, places=6)
        p = L.at((0, 0), 5, L.AXIS + 30)
        self.assertAlmostEqual(L.azimuth(L.mirror(p, (0, 0))), L.AXIS - 30, places=6)
        self.assertEqual(len(L.box((0, 0), 90, 2, 1)), 4)

    @unittest.skipUnless((CURATED / "plan_stones.json").exists(), "plan not digitised")
    def test_complete_monument(self):
        plan = {s["id"]: [tuple(p) for p in s["outline"]] for s in json.loads((CURATED / "plan_stones.json").read_text())["stones"]}
        research = json.loads((CURATED / "stones.json").read_text())
        record = {s["id"]: s for s in research["stones"]}
        built, ring = L.built(plan, record, {}, research["dimensions"])
        groups = {}
        for s in built:
            groups[s["group"]] = groups.get(s["group"], 0) + 1
        self.assertEqual(groups["sarsen_upright"], 30)
        self.assertEqual(groups["sarsen_lintel"], 30)
        self.assertEqual(groups["trilithon_upright"], 10)
        self.assertEqual(groups["trilithon_lintel"], 5)
        self.assertAlmostEqual(ring["step"], 12, delta=0.3)              # 30 uprights round the circle
        self.assertTrue(14.5 < ring["radius"] < 16.5)
        mirrored = {s["id"]: s["status"] for s in built if s["group"] == "trilithon_upright"}
        self.assertEqual(mirrored["55"], "placed"); self.assertEqual(mirrored["59"], "placed")
        now = L.now(plan, record, {})
        lintels = sorted(s["id"] for s in now if s.get("state") == "in place")
        self.assertEqual(lintels, ["101", "102", "105", "107", "122", "130", "152", "154", "158"])


@unittest.skipUnless(shutil.which("node"), "node not installed")
class AstroTest(unittest.TestCase):
    def run_js(self, expr):
        src = (ROOT / "app" / "static" / "sky.js").read_text() + (ROOT / "app" / "static" / "stonehenge_astro.js").read_text()
        out = subprocess.run(["node", "-e", src + f"\nconsole.log(JSON.stringify({expr}));"], capture_output=True, text=True, check=True)
        return json.loads(out.stdout)

    def test_meeus_examples(self):
        moon = self.run_js("SkyPos.moon(2448724.5)")                    # Meeus example 47.a, 1992 April 12 0h TD
        self.assertAlmostEqual(moon["lon"], 133.162655, delta=0.01)
        self.assertAlmostEqual(moon["lat"], -3.229126, delta=0.01)
        self.assertAlmostEqual(moon["km"], 368409.7, delta=50)
        p = self.run_js("SkyPos.precess(41.054063, 49.227750, 2462088.69)")   # example 21.b, θ Persei
        self.assertAlmostEqual(p["ra"], 41.547214, delta=2e-5)
        self.assertAlmostEqual(p["dec"], 49.348483, delta=2e-5)
        self.assertAlmostEqual(self.run_js("SkyPos.siderealTime(2446895.5)"), 197.693195, delta=1e-5)   # example 12.a
        self.assertEqual(self.run_js("SkyPos.julianDay(2000, 1, 1, 12)"), 2451545)
        self.assertEqual(self.run_js("SkyPos.calendarDate(SkyPos.julianDay(-2499, 6, 21, 3))"),
                         {"year": -2499, "month": 6, "day": 21, "hours": 3})

    def test_moment(self):
        dt = self.run_js("[SkyPos.deltaT(2000), SkyPos.deltaT(-2500) / 3600]")
        self.assertAlmostEqual(dt[0], 63.86, places=2)
        self.assertTrue(15 < dt[1] < 18)                               # about 16.6 hours by 2500 BC
        # Local solar noon at Stonehenge on the June solstice: sun due south at 90 - lat + obliquity.
        s = self.run_js("SkyPos.at(2026, 6, 21, 12, 51.1789, -1.8262).sun")
        self.assertAlmostEqual(s["az"], 180, delta=1.0)
        self.assertAlmostEqual(s["alt"], 90 - 51.1789 + 23.44, delta=0.1)


if __name__ == "__main__":
    unittest.main()
