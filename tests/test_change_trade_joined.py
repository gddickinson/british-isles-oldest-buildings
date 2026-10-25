"""The main goods traded 1846-2024 as shares, one line across the eras (roadmap C5b2d4): the join, the breaks and
the series written."""
import csv
import unittest

from bidb import change_series as cs
from bidb import change_trade_joined as tj
from bidb.change_firms import DATA


def _series(sid):
    with open(DATA / f"{sid}.csv", newline="") as f:
        return {int(r["year"]): (float(r["value"]), r["era"]) for r in csv.DictReader(f)}


class Join(unittest.TestCase):
    def test_each_year_from_one_era(self):
        for gid, _, _, eras, _ in tj.JOINED:
            s = _series(f"tj_{gid}_uk")
            self.assertEqual(list(s), list(range(eras[0][0], 2025)), gid)
            for y0, y1, spec in eras:
                v = tj.era_values(spec)
                for y in (y0, y1):
                    self.assertAlmostEqual(s[y][0], v[y], places=2, msg=(gid, y))
                    self.assertEqual(s[y][1], f"{y0}-{y1}")

    def test_sums_and_computed_shares(self):
        gl = tj.era_values(["gl_coal_uk", "gl_iron_uk", "gl_machinery_uk"])
        self.assertAlmostEqual(gl[2000], sum(tj.read(f"gl_{g}_uk")[2000] for g in ("coal", "iron", "machinery")))
        cer = tj.era_values((["aas_cereals_uk"], "aas_imports_uk"))
        self.assertAlmostEqual(cer[1953], 100 * tj.read("aas_cereals_uk")[1953] / tj.read("aas_imports_uk")[1953])

    def test_gap_refused(self):
        with self.assertRaises(ValueError):
            tj.join([(1846, 1938, ["sa_goods_textiles_share_uk"]), (1940, 1952, ["aa_textiles_share_uk"])])

    def test_breaks_give_both_definitions(self):
        pts, both = tj.join(tj.JOINED[0][3])
        br = dict(tj.breaks(pts, both))
        self.assertIn("1938 on both: 17.0% and 16.2%", br[1939])
        self.assertNotIn("{a}", br[1912])
        self.assertIn(1962, br)
        pts, both = tj.join(tj.JOINED[2][3])
        self.assertNotIn(1962, dict(tj.breaks(pts, both, "imports")))   # re-exports: exports only

    def test_textiles_fall(self):
        s = _series("tj_textiles_x_uk")
        self.assertGreater(s[1846][0], 60)
        self.assertLess(s[2024][0], 1)


class Breaks(unittest.TestCase):
    def test_check(self):
        s = {"id": "x", "file": "tj_textiles_x_uk.csv"}
        self.assertEqual(cs.check_breaks({**s, "breaks": [[1912, "a"], [1939, "b"]]}), [])
        self.assertTrue(cs.check_breaks({**s, "breaks": [[1939, "a"], [1912, "b"]]}))
        self.assertTrue(cs.check_breaks({**s, "breaks": [[1846, "a"]]}))        # the first year is no break
        self.assertTrue(cs.check_breaks({**s, "breaks": [[1912, ""]]}))


if __name__ == "__main__":
    unittest.main()
