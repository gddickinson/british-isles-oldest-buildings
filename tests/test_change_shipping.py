"""Shipping registered and built, 1884-1938 (roadmap C5e1), read from the Statistical Abstract."""
import unittest

from bidb import change_shipping as cs


class Shipping(unittest.TestCase):
    def test_parts_add_to_totals(self):
        self.assertEqual(cs.check("registered") + cs.check("built"), [])

    def test_years_and_units(self):
        reg, built = cs.load("registered"), cs.load("built")
        self.assertEqual(sorted(reg), list(range(1884, 1939)))
        self.assertEqual(sorted(built), list(range(1897, 1939)))
        self.assertAlmostEqual(reg[1924]["total"], 11716)          # thousand tons, No. 83
        self.assertAlmostEqual(reg[1923]["total"], 11711.066)      # tons → thousand, No. 70

    def test_series(self):
        pts, rows = cs.series(cs.load("registered"), cs.load("built"))
        self.assertEqual(pts["shipping_reg_total_uk"][1914], 12.415)
        self.assertIn("already exceeded sail in 1884", rows[0]["note"])


if __name__ == "__main__":
    unittest.main()
