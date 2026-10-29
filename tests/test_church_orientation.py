"""Church orientation (bidb.church_orientation): axes from outlines, Julian-calendar feast sunrises, the test."""
import json
import math
import unittest

from bidb import church_orientation as co


def rectangle(az, length=40, width=12, lat=52.0, lon=-1.0):
    """A GeoJSON polygon of a length x width rectangle whose long axis points to az (degrees from north)."""
    a = math.radians(az)
    ux, uy = math.sin(a), math.cos(a)           # along the axis (east, north)
    vx, vy = uy, -ux
    k = 111320
    pts = [(sx * length / 2 * ux + sy * width / 2 * vx, sx * length / 2 * uy + sy * width / 2 * vy)
           for sx, sy in ((1, 1), (1, -1), (-1, -1), (-1, 1))]
    ring = [[lon + x / (k * math.cos(math.radians(lat))), lat + y / k] for x, y in pts]
    return {"type": "Polygon", "coordinates": [ring + [ring[0]]]}


class ChurchOrientationTest(unittest.TestCase):
    def test_axis(self):
        for az in (60, 84.5, 90, 112):
            got, el = co.axis(rectangle(az))
            self.assertAlmostEqual(got, az, delta=0.2)
            self.assertAlmostEqual(el, 40 / 12, delta=0.05)
        multi = {"type": "MultiPolygon", "coordinates": [rectangle(95)["coordinates"]]}
        self.assertAlmostEqual(co.axis(multi)[0], 95, delta=0.2)
        self.assertIsNone(co.axis({"type": "Polygon", "coordinates": [[[0, 0], [0, 0]]]}))

    def test_julian_calendar(self):
        self.assertEqual(co.julian_calendar_day(1582, 10, 4) + 1, 2299160.5)    # 4 Oct (Julian) → 15 Oct 1582
        self.assertEqual(co._julian_md(co.julian_calendar_day(1250, 3, 12) + 0.25), (3, 12))
        # in 1250 the spring equinox fell on about 12-13 March of the Julian calendar
        dates = co.axis_dates(52, 89.0, 1250)
        self.assertEqual(len(dates), 2)
        self.assertIn(dates[0], [(3, d) for d in range(11, 15)])
        self.assertEqual(co.axis_dates(52, 30, 1250), [])        # further north than the sun ever rises

    def test_feast_azimuth(self):
        # midsummer sunrise: St John the Baptist's day (24 June Julian) in 1300 is about 2 days after the solstice
        self.assertAlmostEqual(co.feast_azimuth(52, 1300, "06-24"), 49.4, delta=1.0)

    def test_analyse(self):
        lat = 52.0
        feasts = {"A": {"feasts": [{"name": "A day", "date": "03-12"}]}, "B": {"feasts": [{"name": "B day", "date": "11-30"}]},
                  "T": {"feasts": [{"name": "Trinity", "movable": True}]}}
        az_a = co.feast_azimuth(lat, 1200, "03-12")
        rows = [{"id": f"a{i}", "lat": lat, "year": 1200, "dedication": "A", "axis": (az_a, 3.0)} for i in range(20)]
        rows += [{"id": f"b{i}", "lat": lat, "year": 1200, "dedication": "B", "axis": (az_a, 3.0)} for i in range(20)]
        rows += [{"id": "t", "lat": lat, "year": 1200, "dedication": "T", "axis": (az_a, 3.0)},
                 {"id": "late", "lat": lat, "year": 1850, "dedication": "A", "axis": (az_a, 3.0)},
                 {"id": "square", "lat": lat, "year": 1200, "dedication": "A", "axis": (az_a, 1.1)}]
        per, s = co.analyse(rows, feasts)
        self.assertEqual(s["tested"], 40)                        # not movable, not post-medieval, not square
        self.assertEqual(s["observed"], 20)
        self.assertEqual(per["a0"]["feast"], "A day")
        self.assertLess(per["a0"]["diff"], 0.5)
        self.assertNotIn("dates", per["square"])
        self.assertIsNone(per["late"]["cal"])
        self.assertEqual(s["by_dedication"][0][0], "A")

    def test_curated(self):
        data = co.load()
        for name, e in data["feasts"].items():
            self.assertTrue(e["sources"], name)
            for f in e["feasts"]:
                self.assertTrue(f.get("movable") or len(f["date"]) == 5, name)
        for st in data.get("studies", []):
            self.assertIn(st["supports"], ("yes", "partly", "no"))


if __name__ == "__main__":
    unittest.main()
