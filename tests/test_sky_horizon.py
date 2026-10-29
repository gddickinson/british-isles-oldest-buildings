"""Real horizons (SK7): terrain tile PNG reading, skyline profiles and rising points over a skyline."""
import json
import math
import shutil
import struct
import subprocess
import unittest
import zlib
from pathlib import Path

from bidb import sky, sky_horizon as H
from bidb.terrain_tiles import decode_png, heights, _paeth

ROOT = Path(__file__).resolve().parent.parent


def png(rows, filters):
    """An 8-bit RGB PNG of these rows (lists of bytes), each line written with the given filter type."""
    w, bpp, out, prev = len(rows[0]) // 3, 3, b"", bytes(len(rows[0]))
    for line, f in zip(rows, filters):
        enc = bytearray()
        for i, x in enumerate(line):
            a = line[i - bpp] if i >= bpp else 0
            b, c = prev[i], prev[i - bpp] if i >= bpp else 0
            pred = (0, a, b, (a + b) // 2, _paeth(a, b, c))[f]
            enc.append((x - pred) & 255)
        out += bytes([f]) + bytes(enc)
        prev = line
    chunk = lambda k, d: struct.pack(">I", len(d)) + k + d + struct.pack(">I", zlib.crc32(k + d) & 0xffffffff)
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w, len(rows), 8, 2, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(out)) + chunk(b"IEND", b""))


class Cone:
    """A fake terrain: flat ground at 0 m with a conical hill 500 m high, 5 km due east of (55, 0)."""
    def height(self, lat, lon, z=12):
        x = lon * 111320 * math.cos(math.radians(55)) - 5000
        y = (lat - 55) * 111320
        return max(0.0, 500 - math.hypot(x, y) / 2)


class TestTiles(unittest.TestCase):
    def test_png_filters(self):
        rows = [bytes((r * 37 + i * 11) % 256 for i in range(12)) for r in range(5)]
        w, h, got, bpp = decode_png(png(rows, [0, 1, 2, 3, 4]))
        self.assertEqual((w, h, bpp), (4, 5, 3))
        self.assertEqual([bytes(r) for r in got], rows)

    def test_terrarium_heights(self):
        # 100 m = 32868 = 128 * 256 + 100; -5.5 m = 32762.5 = 127 * 256 + 250 + 128 / 256
        data = png([bytes([128, 100, 0, 127, 250, 128])], [0])
        self.assertEqual(heights(data), [[100.0, -5.5]])


class TestHorizon(unittest.TestCase):
    def test_flat_and_raised(self):
        for h in (0.0, 2.0):
            alt = [h] * 720
            for args in ((51.18, "sun", "summer_solstice", "rise", -2500), (58.2, "moon", "major_south", "set", -2900)):
                self.assertAlmostEqual(H.horizon_azimuth(*args, alt, 0.5), sky.event_azimuth(*args, horizon=h), places=2)

    def test_ridge(self):
        # a 3° ridge from 40° to 55°: midsummer sunrise at 51° N (about 48° flat) is pushed to where the sun
        # clears 3°, still behind the ridge, so further south than over a flat horizon
        alt = [3.0 if 40 <= i * 0.5 <= 55 else 0.0 for i in range(720)]
        flat = sky.event_azimuth(51.18, "sun", "summer_solstice", "rise", 2000)
        got = H.horizon_azimuth(51.18, "sun", "summer_solstice", "rise", 2000, alt, 0.5)
        self.assertGreater(got, flat + 2)
        self.assertLessEqual(got, 55.5)

    def test_profile_cone(self):
        p = H.profile(55.0, 0.0, terrain=Cone(), step=10)
        east = p["alt"][9]                                # 90°
        expected = math.degrees(math.atan2(500 - H.EYE - 5000 ** 2 * (1 - H.K) / (2 * H.EARTH), 5000))
        self.assertAlmostEqual(east, expected, delta=0.3)
        self.assertAlmostEqual(p["km"][9], 5.0, delta=0.2)
        self.assertLess(p["alt"][27], 0)                  # west: flat ground falls away with the earth's curve
        self.assertEqual(H.altitude_at([0, 1], 180, 90), 0.5)

    @unittest.skipUnless(shutil.which("node"), "node not installed")
    def test_browser_mirror(self):
        alt = [3.0 if 40 <= i * 0.5 <= 55 else 0.4 * math.sin(i / 20) for i in range(720)]
        cases = [(51.18, "sun", "summer_solstice", "rise", 2000), (53.7, "sun", "winter_solstice", "set", -3100),
                 (58.2, "moon", "major_south", "set", -2900), (57.0, "moon", "minor_north", "rise", 2000)]
        script = (ROOT / "app" / "static" / "sky.js").read_text() + f"""
            const ALT = {json.dumps(alt)};
            console.log(JSON.stringify({json.dumps(cases)}.map(([la, b, e, rs, y]) => Sky.horizonAzimuth(la, b, e, rs, y, ALT, 0.5))));"""
        js = json.loads(subprocess.run(["node", "-e", script], capture_output=True, text=True, check=True).stdout)
        for c, a in zip(cases, js):
            self.assertAlmostEqual(a, H.horizon_azimuth(*c, alt, 0.5), places=6)

    @unittest.skipUnless(shutil.which("node"), "node not installed")
    def test_browser_mirror_declination(self):
        alt = [2.0 if 120 <= i * 0.5 <= 135 else 0.3 * math.cos(i / 15) for i in range(720)]
        cases = [(51.5, 10.0, "sun", "rise"), (55.0, -20.0, "sun", "set"), (52.0, 5.0, "moon", "rise")]
        script = (ROOT / "app" / "static" / "sky.js").read_text() + f"""
            const ALT = {json.dumps(alt)};
            console.log(JSON.stringify({json.dumps(cases)}.map(([la, d, b, rs]) => Sky.horizonAzimuthDec(la, d, b, rs, ALT, 0.5))));"""
        js = json.loads(subprocess.run(["node", "-e", script], capture_output=True, text=True, check=True).stdout)
        for (la, d, b, rs), a in zip(cases, js):
            self.assertAlmostEqual(a, H.horizon_azimuth_dec(la, d, b, rs, alt, 0.5), places=6)
        flat = [0.0] * 720                                   # a flat skyline: the plain formula
        self.assertAlmostEqual(H.horizon_azimuth_dec(51.5, 10.0, "sun", "rise", flat, 0.5),
                               sky.azimuth(51.5, 10.0, "rise", "sun", 0.0), places=2)


if __name__ == "__main__":
    unittest.main()
