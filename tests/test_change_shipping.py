"""Shipping registered 1848-1938 and built 1897-1938 (roadmap C5e1, C5e2a), read from the Statistical Abstract."""
import unittest

from bidb import change_shipping as cs


class Shipping(unittest.TestCase):
    def test_parts_add_to_totals(self):
        self.assertEqual(cs.check("registered") + cs.check("built"), [])

    def test_years_and_units(self):
        reg, built = cs.load("registered"), cs.load("built")
        self.assertEqual(sorted(reg), list(range(1848, 1939)))
        self.assertEqual(sorted(built), list(range(1897, 1939)))
        self.assertAlmostEqual(reg[1924]["total"], 11716)          # thousand tons, No. 83
        self.assertAlmostEqual(reg[1923]["total"], 11711.066)      # tons → thousand, No. 70

    def test_series(self):
        pts, rows = cs.series(cs.load("registered"), cs.load("built"))
        self.assertEqual(pts["shipping_reg_total_uk"][1914], 12.415)
        self.assertIn("overtook sail in 1883", rows[0]["note"])
        self.assertEqual(pts["shipping_reg_total_uk"][1848], 3.401)
        self.assertEqual(pts["shipping_reg_sail_uk"][1865], 4.937)

    def test_editions(self):
        """Each year from one page; the 1883 misprint taken from No. 45, whose figure adds up."""
        reg = cs.load("registered")
        self.assertEqual(reg[1850]["raw"]["page"], "69")       # No. 10
        self.assertEqual(reg[1883]["raw"]["page"], "175")      # No. 45
        self.assertEqual(reg[1883]["steam"], 3728.268)
        self.assertIn(1883, cs.MISPRINTS)


if __name__ == "__main__":
    unittest.main()
