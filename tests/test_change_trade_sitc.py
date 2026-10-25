"""The main goods traded 1958-1974 by SITC (R) division (roadmap C5b2d2a): division and section sums, overlaps, shares."""
import unittest
from unittest import mock

from bidb import change_trade_sitc as ts


class Sitc(unittest.TestCase):
    def setUp(self):
        self.rows = ts.load()

    def test_readings(self):
        self.assertEqual(ts.check(self.rows), [])                 # divisions add up to sections, sections to totals
        g = ts.goods(self.rows)
        self.assertEqual(list(g), list(range(1958, 1975)))
        self.assertEqual({y: v["edition"] for y, v in g.items() if y in (1961, 1962, 1965, 1966, 1974)},
                         {1961: 104, 1962: 108, 1965: 108, 1966: 112, 1974: 112})
        self.assertEqual(g[1958]["machinery"], 773.8)             # 71: 545.7 + 72: 228.1
        self.assertEqual(g[1970]["exports"], 8061.1)              # No. 112's revision of No. 108's 8,062.8
        self.assertEqual(g[1974]["imports"], 23116.7)

    def test_check_finds_a_misread(self):
        self.rows[104]["x_65"][1960] += 1.0
        self.assertEqual(ts.check(self.rows), ["No. 104 1960 x: section 6 parts 990.0 != 988.9"])

    def test_known_misprint(self):
        with mock.patch.object(ts, "KNOWN", set()):              # 1969 fuels: 906.5 printed, parts 906.2
            self.assertEqual(ts.check(self.rows), ["No. 108 1969 i: section 3 parts 906.2 != 906.5",
                                                   "No. 112 1969 i: section 3 parts 906.2 != 906.5"])

    def test_overlaps(self):
        self.assertEqual([o for o in ts.overlap(self.rows, 104, 108) if o[0].startswith("i_") and o[1] < 1966], [])
        self.assertEqual({r for r, y, *_ in ts.overlap(self.rows, 108, 112) if y < 1970}, {"i_o8"})
        self.assertEqual(ts.reexports(self.rows, ("total",), 1962), (4062.3, 3904.6))

    def test_series(self):
        y = {"textiles": 30.0, "coal": 10.0, "iron": 20.0, "machinery": 70.0, "cereals": 40.0, "sugar": 5.0,
             "beverages": 5.0, "wood": 20.0, "fibres": 30.0, "exports": 400.0, "imports": 500.0}
        s = ts.series({1960: y})
        self.assertEqual(s["aas_textiles_share_uk"], [[1960, 7.5]])
        self.assertEqual(s["aas_metal_share_uk"], [[1960, 25.0]])
        self.assertEqual(s["aas_food_share_uk"], [[1960, 10.0]])
        self.assertEqual(s["aas_materials_share_uk"], [[1960, 10.0]])


if __name__ == "__main__":
    unittest.main()
