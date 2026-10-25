"""The main goods traded 1953-1957 by the classes of the original SITC (roadmap C5b2d2b): class sums, overlaps, the
1958 join."""
import unittest

from bidb import change_trade_classes as tc
from bidb import change_trade_sitc as ts


class Classes(unittest.TestCase):
    def setUp(self):
        self.rows = tc.load()

    def test_readings(self):
        self.assertEqual(tc.check(self.rows), [])                 # divisions add up to classes, classes to totals
        g = tc.goods(self.rows)
        self.assertEqual({y: v["edition"] for y, v in g.items()}, {1953: 99, 1954: 100, 1955: 100, 1956: 100, 1957: 100})
        self.assertEqual(g[1953]["textiles"], 324.8)              # D6-D9: 87.3 + 117.0 + 39.3 + 81.2
        self.assertEqual(g[1953]["fibres"], 390.8)                # B7, B8 and other: 245.1 + 107.2 + 38.5
        self.assertEqual((g[1957]["exports"], g[1957]["imports"]), (3295.0, 4043.7))

    def test_check_finds_a_misread(self):
        self.rows[100]["x_D7"][1955] += 1.0
        self.assertEqual(tc.check(self.rows), ["No. 100 1955 x: class D parts 2372.0 != 2370.9"])  # printed parts 2,371.0

    def test_overlap(self):
        self.assertEqual({y for _, y, *_ in tc.overlap(self.rows, 99, 100)}, {1961})   # only the first estimate

    def test_join(self):
        old, new = tc.in_1958(self.rows), ts.goods(ts.load())[1958]
        self.assertEqual(old["coal"], new["coal"])
        self.assertEqual(old["wood"], new["wood"])
        self.assertEqual((old["imports"], new["imports"]), (3747.5, 3833.5))  # precious stones from No. 104
        for g in ("textiles", "iron", "machinery", "cereals", "sugar", "beverages", "fibres"):
            self.assertLess(abs(old[g] - new[g]) / new[g], 0.02, g)


if __name__ == "__main__":
    unittest.main()
