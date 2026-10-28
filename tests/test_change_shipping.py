"""Shipping registered 1848-1970 and built 1846-1974, trading fleet 1950-2025 (roadmap C5e1, C5e2a, C5e2b1, C5e2b2a, C5e2b2b1), read from the Statistical
Abstract and the Annual Abstract."""
import unittest

from bidb import change_shipping as cs
from bidb import change_shipping_built as early
from bidb import change_shipping_post as post
from bidb import change_shipping_fleet as fleet


def _fle0301():
    try:
        from bidb.config import cache_dir
        path = cache_dir() / "registers" / "dft" / "fle0301.ods"
    except Exception:
        return None
    return path if path.exists() else None


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

    def test_annual_abstract(self):
        """1939-1970 fleet and 1940-1974 completions: parts add up, overlaps as REVISED, misprints replaced by sums."""
        self.assertEqual(post.check("registered") + post.check("built"), [])
        self.assertEqual(post.overlaps(), post.REVISED)
        reg = post.registered()
        self.assertEqual(sorted(reg), list(range(1939, 1971)))
        self.assertEqual((reg[1942], reg[1962], reg[1970]), (9.0, 11.501, 14.7))
        done = post.built()["shipping_completed_uk"]
        self.assertEqual(sorted(done), list(range(1940, 1975)))
        self.assertEqual((done[1941], done[1961], done[1954]), (1158, 1390, 1493))   # No. 88; No. 108's sum
        self.assertEqual(post.latest("registered")[1944]["no"], 88)
        self.assertEqual(post.value("registered", next(r for r in post.rows("registered")
                                                       if r["no"] == 84 and r["year"] == 1944), "number"), 12525)
        pts, rows = cs.series(cs.load("registered"), cs.load("built"))
        self.assertEqual(pts["shipping_reg_total_uk"][1938], 10.702)               # Statistical Abstract, with sail
        self.assertEqual(pts["shipping_reg_total_uk"][1939], 10.511)               # Annual Abstract, steam and motor
        self.assertEqual(rows[0]["breaks"][0][0], 1939)
        self.assertIn("611 in 1967 (51% of all completed)", rows[5]["note"])

    def test_trading_fleet(self):
        """DfT FLE0301 (stored ODS) equals the Annual Abstract 1961-1974 but for 1962-1963; breaks at 1986, 2009, 2022."""
        self.assertEqual(fleet.check(), [])
        if not _fle0301():
            self.skipTest("DfT FLE0301 not downloaded (no data folder)")
        fle, old = fleet.dft(_fle0301())
        self.assertEqual(fleet.problems(fle), [])
        self.assertEqual(sorted(old), [1986, 2009])
        self.assertEqual((old[1986]["gross"], fle[1986]["gross"]), (7711, 8046))
        self.assertEqual(fleet.latest()[1968]["tramps"], 2174)                     # No. 112's revision
        pts, rows = fleet.series(fle, old, reg1961=21.193)
        g = pts["fleet_500gt_uk"]
        self.assertEqual((g[1950], g[1975], g[1993]), (17.198, 31.489, 4.67))
        self.assertEqual(min(pts["fleet_500gt_container_uk"]), 1969)
        self.assertEqual([b[0] for b in rows[0]["breaks"]], [1986, 2009, 2022])
        self.assertIn("31.5 million in 1975 (1,682 ships", rows[0]["note"])

    def test_fleet_misreading_caught(self):
        r = [dict(x) for x in fleet.aa_rows() if x["no"] == 110 and x["year"] == 1972]
        r[0]["bulk"] = 6125
        self.assertTrue(fleet.check(r))

    def test_annual_misreading_caught(self):
        r = [dict(x) for x in post.rows("built") if x["no"] == 94 and x["year"] == 1953]
        r[0]["tankers"] = "596"
        self.assertTrue(post.check("built", r))

    def test_misreading_caught(self):
        r = [dict(x) for x in early.rows() if x["no"] == 46 and x["year"] == 1890]
        r[0]["steam"] = "528,780".replace(",", "")
        self.assertTrue(early.check(r))


if __name__ == "__main__":
    unittest.main()
