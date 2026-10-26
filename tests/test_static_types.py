"""The hosted copy's compact /types data (app.static_types) and place links (app.static_places)."""
import unittest

from app import static_places, static_types


class StaticTypesTest(unittest.TestCase):
    def test_deltas_round_trip(self):
        pts = [(51.5074, -0.1278), (53.3498, -6.2603), (53.3499, -6.2603)]
        flat = static_types.deltas(pts)
        lat = lon = 0
        back = []
        for i in range(0, len(flat), 2):            # as steps() in static_types.js
            lat, lon = lat + flat[i], lon + flat[i + 1]
            back.append((lat / 1000, lon / 1000))
        for (a, b), (c, d) in zip(pts, back):
            self.assertAlmostEqual(a, c, delta=0.0005)
            self.assertAlmostEqual(b, d, delta=0.0005)
        self.assertEqual(flat[-2:], [0, 0])

    def test_ref(self):
        self.assertEqual(static_types.ref({"id": "Q1", "source": "building", "name": "X", "year": 1200}), "Q1")
        p = {"id": "P1", "source": "place", "name": "Mound", "year": 1100, "date_text": "c. 1100",
             "county": "Kent", "nation": "England"}
        self.assertEqual(static_types.ref(p), ["P1", "Mound", 1100, "c. 1100", "Kent", "England"])

    def test_points_split(self):
        pts = [[51.0, 0.0, "Q1", "building", 1200, 1], [52.0, 1.0, "Q2", "building", 1300, 0],
               [53.0, 2.0, "P1", "place", None, 1]]
        out = static_types._points(pts, primary_at=5)
        self.assertEqual(out["b"], ["Q1"])
        self.assertEqual(out["b2"], ["Q2"])
        self.assertEqual(out["p"], [53000, 2000])
        self.assertNotIn("p2", out)
        self.assertEqual(static_types._points(pts[1:2])["b"], ["Q2"])     # materials: no main type

    def test_evidence_trimmed(self):
        self.assertEqual(len(static_types._trim("x" * 500)), static_types.EVIDENCE)
        self.assertEqual(static_types._trim("short"), "short")

    def test_url_prefixes_distinct(self):
        p = static_places.URL_PREFIXES
        self.assertEqual(len(p), len(set(p)))
        for i, a in enumerate(p):                   # the first match wins: no prefix may start with an earlier one
            self.assertFalse(any(a.startswith(b) for b in p[:i]))


if __name__ == "__main__":
    unittest.main()
