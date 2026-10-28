"""Wages before 1879 (roadmap C5d2b2b): Wood's 1899 table of average wages in towns, read from the page image, and
Bowley's 1900 index numbers by decade, quoted in estimates.json."""
import unittest

from bidb import change_wages_early as ce


class Wood(unittest.TestCase):
    def test_averages_agree_with_the_towns(self):
        self.assertEqual(ce.check(), [])

    def test_a_misreading_is_caught(self):
        t = ce.load()
        t["London"][1820] += 30                     # 17 towns in 1820: the mean moves by 1.8
        self.assertEqual(len(ce.check(t)), 1)

    def test_table(self):
        t = ce.load()
        self.assertEqual(len(t), 25)                # 24 towns and districts and the average
        self.assertTrue(all(v[1840] == 100 for name, v in t.items() if 1840 in v))
        a = ce.average(t)
        self.assertEqual(list(a), [1790, 1795, 1800, 1805, 1810, 1816, 1820, 1824, 1831, 1840, 1845, 1850, 1855, 1860])
        # Wood's text: up 69% 1790-1810, down 19% 1810-1845, 14% in the five years from 1850
        self.assertAlmostEqual(a[1810] / a[1790], 1.69, places=2)
        self.assertAlmostEqual(1 - a[1845] / a[1810], 0.19, places=2)
        self.assertAlmostEqual(a[1855] / a[1850], 1.14, places=2)

    def test_real(self):
        prices = {1799: 2.0, 1800: 1.0, 1801: 3.0, 1840: 1.0, 1850: 2.0}
        r = ce.real({1790: 50, 1800: 80, 1840: 100, 1850: 100}, prices)
        self.assertEqual(r, {1800: 40.0, 1840: 100.0, 1850: 50.0})   # 1800 over the mean of 1799-1801; 1790 no prices


class Bowley(unittest.TestCase):
    def test_decades(self):
        b = ce.bowley()
        self.assertEqual([p[0] for p in b], list(range(1785, 1896, 10)))
        by = {p[0]: p for p in b}
        self.assertEqual(by[1845][1], 100.0)        # 1840-50 = 100
        self.assertEqual(by[1895][1], round(100 / 60 * 100, 1))
        self.assertEqual(by[1805][2:4], (91.7, 108.3))    # "55 to 65"
        self.assertIsNone(by[1835][2])

    def test_quotes(self):
        for p in ce.model()["points"]:
            self.assertIn(f"{p['decade']} {p['printed']}", p["quote"])
