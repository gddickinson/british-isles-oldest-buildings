"""Prices since 1800 and real wages (roadmap C5d): the ONS long-run RPI, the Board of Trade's and Ministry of Labour's
wage indexes read from page images, ONS average weekly earnings."""
import unittest

from bidb import change_prices as cp, change_wages as cw, change_wages_post as cwp


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


class After1935(unittest.TestCase):
    def test_editions_and_links_agree(self):
        self.assertEqual(cwp.check(), [])

    def test_a_misreading_is_caught(self):
        rows = cwp.load()
        r = next(r for r in rows if r["year"] == 1960 and "_104" in r["edition"])
        r["low"] = r["high"] = r["value"] = 129.9
        self.assertEqual(len(cwp.check(rows)), 1)

    def test_chain(self):
        rows = cwp.load()
        c = cwp.chain(rows)
        self.assertEqual(sorted(c), list(range(1935, 1976)))
        self.assertEqual(c[1939], (100.0, "1939-09-01"))
        self.assertEqual(c[1947][1], "1939-09-01")                  # June 1947 is the new base's own date
        self.assertEqual(c[1971][0], round(221.0 * 1.675 * 1.561, 2))   # No. 112's revision, both links
        self.assertEqual(c[1973][1], "1972-07-31")
        self.assertAlmostEqual(cwp.links(rows)["1972-07-31"], 167.5 * 1.561 * 2.495, places=6)
        v = [x for x, _ in c.values()]
        self.assertTrue(all(b > a for a, b in zip(v, v[1:])))          # money rates never fell

    def test_latest_edition(self):
        r = cwp.latest(cwp.load())
        self.assertIn("_112", r[(1971, "1956-01-31")]["edition"])
        self.assertIn("_108", r[(1965, "1956-01-31")]["edition"])


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
