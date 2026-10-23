"""Surfaces of bike rides from OpenStreetMap ways (bidb.tour_surface)."""
import unittest

from bidb.tour_surface import kind, points, shares


class Surface(unittest.TestCase):
    def test_kind_from_tags(self):
        self.assertEqual(kind({"highway": "residential"}), "paved")
        self.assertEqual(kind({"highway": "track"}), "unpaved")
        self.assertEqual(kind({"highway": "track", "tracktype": "grade1"}), "paved")
        self.assertEqual(kind({"highway": "cycleway", "surface": "fine_gravel"}), "unpaved")
        self.assertEqual(kind({"highway": "path", "surface": "asphalt"}), "paved")

    def test_points_every_step(self):
        line = [(55.0, -3.0), (55.0 + 1.0 / 111.2, -3.0)]          # 1 km north
        self.assertEqual(len(points(line, 0.2)), 6)

    def test_shares_take_nearest_way(self):
        road = ({"highway": "tertiary"}, [(55.0, -3.0), (55.01, -3.0)])
        path = ({"highway": "cycleway", "surface": "gravel"}, [(55.01, -3.0), (55.02, -3.0)])
        samples = [(55.002, -3.0), (55.008, -3.0), (55.012, -3.0), (55.018, -3.0), (56.0, -3.0)]
        self.assertEqual(shares(samples, [road, path]), {"paved": 50, "unpaved": 50, "traffic_free": 50})
        self.assertIsNone(shares([(56.0, -3.0)], [road]))


if __name__ == "__main__":
    unittest.main()
