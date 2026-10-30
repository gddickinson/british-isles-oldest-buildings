"""Church orientation (bidb.church_orientation): axes from outlines, Julian-calendar feast sunrises, the test."""
import json
import math
import unittest

from bidb import church_axes as ca
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

    def test_wall_axis(self):
        for az in (60, 84.5, 90, 112, 150):
            got, el, share = ca.wall_axis(rectangle(az))
            self.assertAlmostEqual(got, az, delta=0.2)
            self.assertAlmostEqual(el, 40 / 12, delta=0.05)
            self.assertAlmostEqual(share, 1.0)
        # a nave at 88° with a square west tower set at 70°: the smallest rectangle turns, the walls hardly do
        nave = rectangle(88, 30, 10)["coordinates"][0][:-1]
        a = math.radians(88)
        k = 111320 * math.cos(math.radians(52))
        cx, cy = -1.0 - 17 * math.sin(a) / k, 52.0 - 17 * math.cos(a) / 111320     # 17 m west of the centre
        tower = rectangle(70, 8, 8, lat=cy, lon=cx)["coordinates"][0][:-1]
        geom = {"type": "MultiPolygon", "coordinates": [[nave + nave[:1]], [tower + tower[:1]]]}
        self.assertAlmostEqual(ca.wall_axis(geom)[0], 88, delta=1.0)
        self.assertEqual(ca.diff(179, 1), 2)
        self.assertIsNone(ca.wall_axis({"type": "Polygon", "coordinates": [[[0, 0], [0, 0], [0, 0], [0, 0]]]}))

    def test_parts(self):
        outlines = {"c": rectangle(80, 40, 15)}
        parts = [{"part": "church", "geom": rectangle(80, 30, 10)}, {"part": "nave", "geom": rectangle(95, 20, 8)},
                 {"part": "nave", "geom": rectangle(95, 5, 3, lat=53)}]           # outside: another church
        by = ca.parts_of(outlines, parts)
        self.assertEqual(len(by["c"]), 2)
        self.assertAlmostEqual(ca.body_axis(by["c"])[0], 95, delta=0.3)              # nave before church
        self.assertIsNone(ca.body_axis([{"part": "nave", "geom": rectangle(95, 10, 9)}]))    # too near square

    def test_sites(self):
        from bidb import church_sites as cs
        self.assertIsNone(cs.site_kind({"building": "church"}))
        self.assertIsNone(cs.site_kind(None))                                          # tags unknown: as before
        self.assertEqual(cs.site_kind({"historic": "monastery"}), "site")
        self.assertEqual(cs.site_kind({"amenity": "grave_yard", "building": "no"}), "site")
        self.assertEqual(cs.site_kind({"building": "tower"}), "other building")
        precinct = rectangle(20, 200, 150)                                           # a field round the abbey
        church = {"geom": rectangle(97, 60, 18), "tags": {"building": "church"}}
        chapel = {"geom": rectangle(80, 12, 6, lat=52.0003), "tags": {"building": "chapel"}}
        away = {"geom": rectangle(90, 80, 20, lat=53), "tags": {"building": "church"}}
        self.assertIs(cs.inner_church(precinct, [chapel, church, away]), church)     # largest inside
        self.assertIsNone(cs.inner_church(precinct, [away]))
        rows = [{"id": "a", "axis": [20.0, 1.33], "src": "walls"}, {"id": "b", "axis": [20.0, 1.33], "src": "walls"},
                {"id": "c", "axis": [97.0, 3.0], "src": "walls"}]
        tags = {"a": {"historic": "monastery"}, "b": {"landuse": "cemetery"}, "c": {"building": "church"}}
        co._site_axes(rows, {"a": precinct, "b": rectangle(20, 50, 40, lat=54), "c": church["geom"]}, tags, [church])
        self.assertEqual(rows[0]["src"], "building")
        self.assertAlmostEqual(rows[0]["axis"][0], 97, delta=0.3)
        self.assertEqual((rows[1]["axis"], rows[1]["src"]), (None, "site"))             # nothing inside: left out
        self.assertEqual(rows[2]["src"], "walls")

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

    def test_skyline_and_other_saints(self):
        lat = 52.0
        # a higher horizon: the sun clears it further south, and the axis catches it on different days
        self.assertGreater(co.feast_azimuth(lat, 1300, "03-12", 3.0), co.feast_azimuth(lat, 1300, "03-12") + 3)
        self.assertNotEqual(co.axis_dates(lat, 89.0, 1250, 3.0), co.axis_dates(lat, 89.0, 1250))
        entry = {"feasts": [{"name": "A day", "date": "03-12"}], "if_other_saint": {"name": "Other A", "date": "11-30"}}
        self.assertEqual([f["name"] for f in co.fixed_feasts(entry)], ["A day"])
        self.assertEqual([f["name"] for f in co.fixed_feasts(entry, other=True)], ["A day", "Other A"])
        feasts = {"A": entry, "B": {"feasts": [{"name": "B day", "date": "08-01"}]}}
        hz = 2.0
        az_other = co.feast_azimuth(lat, 1200, "11-30", hz)       # these face the other saint's sunrise over a hill
        rows = [{"id": f"a{i}", "lat": lat, "year": 1200, "dedication": "A", "axis": (az_other, 3.0), "hz": hz}
                for i in range(10)]
        rows += [{"id": f"b{i}", "lat": lat, "year": 1200, "dedication": "B", "axis": (100.0, 3.0), "hz": hz}
                 for i in range(10)]
        per, s = co.analyse(rows, feasts)
        self.assertEqual(s["skyline"]["observed"], 0)
        self.assertEqual(s["other_saints"]["observed"], 10)
        self.assertEqual(s["other_saints"]["labels"], ["A"])
        self.assertEqual(per["a0"]["hz"], hz)
        self.assertIn("dates_hz", per["a0"])

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
