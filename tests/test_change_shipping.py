"""Shipping registered 1848-1938 and built 1846-1938 (roadmap C5e1, C5e2a, C5e2b1), read from the Statistical Abstract."""
import unittest

from bidb import change_shipping as cs
from bidb import change_shipping_built as early


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

    def test_built_before_1897(self):
        """Ships for British owners 1846-1896, each year from the latest edition, breaks at 1871 and 1897."""
        self.assertEqual(early.check(), [])
        self.assertEqual(early.revisions(), early.REVISED)
        e = early.latest()
        self.assertEqual(e[1861]["no"], 23)                     # No. 9 printed 310,900
        self.assertEqual(int(e[1861]["total"]), 200839)
        self.assertEqual(e[1870]["no"], 32)
        self.assertEqual(e[1871]["basis"], "british")
        self.assertEqual(int(e[1877]["total"]), 433650)         # No. 32 revised No. 26's 433,694
        self.assertEqual(int(early.latest(foreign=True)[1898]["total"]), 174611)
        built = cs.load("built")
        j = early.joined(built)
        self.assertEqual(sorted(j), list(range(1846, 1939)))
        self.assertEqual((j[1846], j[1896], j[1897]), (125.3, 520.0, 635.2))
        self.assertEqual([b[0] for b in early.breaks(built)], [1871, 1897])
        f = early.facts()
        self.assertEqual((f["steam_first"], f["sail_last"], f["peak"]), (1870, 1885, 1883))

    def test_misreading_caught(self):
        r = [dict(x) for x in early.rows() if x["no"] == 46 and x["year"] == 1890]
        r[0]["steam"] = "528,780".replace(",", "")
        self.assertTrue(early.check(r))


if __name__ == "__main__":
    unittest.main()
