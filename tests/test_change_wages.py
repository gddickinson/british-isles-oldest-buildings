"""Prices since 1800 and real wages (roadmap C5d): the ONS long-run RPI, the Board of Trade's and Ministry of Labour's
wage indexes read from page images, ONS average weekly earnings."""
import unittest

from bidb import change_prices as cp, change_wages as cw


class Wages(unittest.TestCase):
    def test_printed_means_agree(self):
        self.assertEqual(cw.check(), [])

    def test_a_misreading_is_caught(self):
        rows = cw.load_bot()
        rows[5]["coal"] += 1
        self.assertEqual(len(cw.check(rows)), 2)

    def test_editions(self):
        rows = cw.load_bot()
        self.assertEqual([r["year"] for r in rows], list(range(1879, 1914)))
        self.assertEqual({r["edition"] for r in rows if r["year"] > 1879}, {"op1256333-1001"})

    def test_war_and_after(self):
        rows = cw.load_war()
        r = cw.real_1914(rows)
        self.assertEqual(sorted(r), list(range(1914, 1935)))       # one point a year, July 1920 left out
        self.assertEqual(r[1914], (100.0, 100.0, 100.0))
        self.assertTrue(all(lo <= v <= hi for v, lo, hi in r.values()))
        self.assertLess(r[1917][0], 80)                            # prices outran wages in the war
        july, end = [x for x in rows if x["year"] == 1920]
        a, b = july["wage_high"] / july["cost_of_living"], end["wage_low"] / end["cost_of_living"]
        self.assertLess(abs(a - b), 0.02)                          # Bowley's July 1920 near the Ministry's end of 1920
        self.assertTrue(all(x["wage_low"] <= x["wage_high"] for x in rows))

    def test_quarters(self):
        m = cw.load_mol()
        self.assertEqual(m[1924], 100)
        self.assertEqual(sorted(m), list(range(1924, 1939)))

    def test_real(self):
        self.assertEqual(cw.real({1900: 50, 1901: 55}, {1900: 10, 1901: 10}, 1900), {1900: 100.0, 1901: 110.0})
        self.assertEqual(cw.at_prices({2000: 100}, {2000: 1, 2025: 2}, 2025), {2000: 200.0})


class Prices(unittest.TestCase):
    def test_not_rising(self):
        self.assertEqual(cp.not_rising({1934: 1, 1935: 2, 1936: 2, 1937: 3}), [1936])

    def test_series_row(self):
        p = {y: 10.0 + (y - 1800) * 0.1 for y in range(1800, 2026)}
        pts, row = cp.series(p)
        self.assertTrue(row["log"])
        self.assertEqual(len(pts), 226)


if __name__ == "__main__":
    unittest.main()
