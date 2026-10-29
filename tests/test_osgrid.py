"""OS and Irish grid references (bidb.osgrid) and the browser mirror (app/static/osgrid.js)."""
import json
import shutil
import subprocess
import unittest
from pathlib import Path

from bidb import osgrid

ROOT = Path(__file__).resolve().parent.parent

# (lat, lon) -> (easting, northing) by pyproj 3.7 / PROJ with OSTN15 (EPSG:27700) and EPSG:29903; a Helmert shift is
# within a few metres of them
GB = [((51.1789, -1.8262), (412244.65, 142200.00)), ((51.50101, -0.14189), (529067.29, 179644.40)),
      ((57.1, -3.5), (309223.28, 802003.29)), ((60.2, -1.3), (438909.92, 1146384.88)),
      ((50.1, -5.5), (149806.10, 28081.26))]
IE = [((53.6947, -6.4755), (300749.23, 272727.10)), ((52.0, -9.5), (97032.08, 84110.40))]


class OsGrid(unittest.TestCase):
    def test_against_proj(self):
        for cases, irish in ((GB, False), (IE, True)):
            for (lat, lon), (e, n) in cases:
                E, N = osgrid.to_en(lat, lon, irish)
                self.assertLess(abs(E - e) + abs(N - n), 6, (lat, lon))
                ref = osgrid.format_en(e, n, irish)
                lat2, lon2 = osgrid.to_latlon(ref, irish)
                self.assertLess(abs(lat2 - lat) * 111000 + abs(lon2 - lon) * 70000, 8, ref)

    def test_letters(self):
        self.assertEqual(osgrid.from_latlon(51.1789, -1.8262), "SU 12245 42199")      # Stonehenge
        self.assertEqual(osgrid.from_latlon(51.1789, -1.8262, digits=6), "SU 122 421")
        self.assertTrue(osgrid.from_latlon(60.2, -1.3).startswith("HU "))              # Shetland
        self.assertTrue(osgrid.from_latlon(50.1, -5.5).startswith("SW "))              # Cornwall
        self.assertEqual(osgrid.from_latlon(53.6947, -6.4755, irish=True), "O 00749 72727")   # Newgrange

    def test_which_grid(self):
        self.assertEqual(osgrid.for_point(53.6947, -6.4755)[1], "Irish")
        self.assertEqual(osgrid.for_point(55.29, -6.2)[1], "Irish")              # Rathlin
        self.assertEqual(osgrid.for_point(55.3, -5.75)[1], "OS")                 # Mull of Kintyre
        self.assertEqual(osgrid.for_point(55.75, -6.2)[1], "OS")                 # Islay
        self.assertTrue(osgrid.for_point(54.2, -4.5)[0].startswith("SC "))       # Isle of Man
        self.assertEqual(osgrid.for_point(51.72, -5.67)[1], "OS")                # the Smalls
        self.assertIsNone(osgrid.for_point(49.2, -2.1))                          # Jersey: neither grid
        self.assertEqual(osgrid.for_point(55.667, -9.0)[1], "Irish")               # a wreck north of the outline

    @unittest.skipUnless(shutil.which("node"), "node not installed")
    def test_browser_mirror(self):
        points = [p for p, _ in GB + IE] + [(55.29, -6.2), (55.3, -5.75), (49.2, -2.1), (54.2, -4.5), (55.667, -9.0)]
        refs = ["SP 536 027", "S0 281 554", "NN 1667 7128", "SP 12345"]
        script = (ROOT / "app" / "static" / "osgrid.js").read_text() + f"""
            const out = {{points: {json.dumps(points)}.map(([a, b]) => OSGrid.forPoint(a, b)),
              en: {json.dumps(points)}.map(([a, b]) => OSGrid.toEN(a, b, OSGrid.inIreland(a, b))),
              refs: {json.dumps(refs)}.map((r) => OSGrid.toLatLon(r)), irish: OSGrid.toLatLon("C 799 348", true)}};
            console.log(JSON.stringify(out));"""
        js = json.loads(subprocess.run(["node", "-e", script], capture_output=True, text=True, check=True).stdout)
        for (lat, lon), got, en in zip(points, js["points"], js["en"]):
            want = osgrid.for_point(lat, lon)
            self.assertEqual(got and [got["ref"], got["grid"]], want and list(want))
            for a, b in zip(en, osgrid.to_en(lat, lon, osgrid.in_ireland(lat, lon))):
                self.assertAlmostEqual(a, b, places=4)
        for ref, got in zip(refs, js["refs"]):
            want = osgrid.to_latlon(ref)
            self.assertEqual(got is None, want is None, ref)
            for a, b in zip(got or (), want or ()):
                self.assertAlmostEqual(a, b, places=9)
        for a, b in zip(js["irish"], osgrid.to_latlon("C 799 348", irish=True)):
            self.assertAlmostEqual(a, b, places=9)


if __name__ == "__main__":
    unittest.main()
