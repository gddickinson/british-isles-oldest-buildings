"""Bankers' clearing houses 1868-1974 (roadmap C5e2b2b2b3b1, C5e2b2b2b3b2a, C5e2b2b2b3b2b): Statistical Abstract and
Annual Abstract, read from the page images."""
import copy
import unittest

from bidb import change_clearing as cc
from bidb import change_clearing_post as cp


def find(rows, edition, year):
    return next(r for r in rows if (r["edition"], r["year"]) == (edition, year))


class ClearingHouses(unittest.TestCase):
    rows = cc.load()

    def test_rows_add_up_and_agree(self):
        self.assertEqual(cc.check(self.rows), [])
        self.assertEqual([len(r) for r in self.rows], [229, 120])

    def test_misreading_caught_by_parts(self):
        lon, pro = copy.deepcopy(self.rows)
        find(lon, "83", 1938)["country"] = 3613                   # 3,673 read as 3,613; printed once
        find(pro, "83", 1926)["leicester"] = 30.9                  # 39.9 read as 30.9
        bad = cc.check((lon, pro))
        self.assertEqual(len(bad), 3)                              # two sums, and No. 83 against No. 82 for 1926
        self.assertTrue(any("London No. 83 1938" in b for b in bad))

    def test_misreading_caught_by_editions(self):
        lon, pro = copy.deepcopy(self.rows)
        find(lon, "59", 1905)["half_year"] = 6062                  # no sum covers the six months to June
        self.assertEqual(cc.check((lon, pro)), ["London half_year 1905: Nos. 59 6,062 and 62 6,082"])

    def test_revisions_allowed(self):
        lon, pro = self.rows
        self.assertEqual((find(lon, "31", 1883)["fourth"], find(lon, "32", 1883)["fourth"]), (237, 239))
        self.assertEqual((find(pro, "66", 1916)["leeds"], find(pro, "69", 1916)["leeds"]), (28.0, 38.5))
        _, pro = copy.deepcopy(self.rows)
        find(pro, "62", 1912)["leeds"] = 24.0                      # a revision before No. 69 not listed
        self.assertTrue(any("leeds 1912" in b for b in cc.check((self.rows[0], pro))))

    def test_series(self):
        prices = {y: 50.0 if y < 1974 else 100.0 for y in range(1800, 1975)}     # no download in the tests
        pts, out = cc.series(self.rows, prices=prices)
        self.assertEqual(sorted(pts["clearing_london_uk"]), list(range(1868, 1975)))
        self.assertEqual(sorted(pts["clearing_provincial_uk"]), list(range(1897, 1968)))
        self.assertEqual(min(pts["clearing_country_uk"]), 1902)
        self.assertEqual(pts["clearing_london_uk"][1929], 44897)
        self.assertEqual(pts["clearing_london_uk"][1938], 39611)           # Statistical Abstract to 1938
        self.assertEqual(pts["clearing_london_uk"][1974], 1640190)
        self.assertEqual(pts["clearing_country_uk"][1944], 28292)          # the general clearing from 1939
        self.assertEqual(pts["clearing_provincial_uk"][1919], 2284.4)    # No. 71, with Bradford
        self.assertEqual(pts["clearing_provincial_uk"][1939], 1269.4)    # no total printed: the houses' sum
        self.assertEqual(pts["clearing_london_real_uk"][1938], 2 * 39611)
        self.assertEqual(pts["clearing_london_real_uk"][1974], 1640190)
        ids = [r["id"] for r in out]
        self.assertEqual([b[0] for b in out[ids.index("clearing_provincial_uk")]["breaks"]],
                         [1909, 1912, 1921, 1943, 1945])
        self.assertEqual([b[0] for b in out[0]["breaks"]], [1936, 1939])
        self.assertTrue(out[0]["log"])
        self.assertNotIn("{", "".join(r.get("note", "") for r in out))
        # the credit clearing (C5e2b2b2b3b2b): 1960 from 1 May not drawn, 1970 on the new basis, breaks 1970 and 1971
        credit = pts["clearing_credit_uk"]
        self.assertEqual(sorted(credit), list(range(1961, 1975)))
        self.assertEqual((credit[1970], credit[1974]), (10969, 18580))
        self.assertEqual([b[0] for b in out[ids.index("clearing_credit_uk")]["breaks"]], [1970, 1971])


class AnnualAbstract(unittest.TestCase):
    rows = cp.load()

    def test_rows_add_up_and_agree(self):
        self.assertEqual(cp.check(self.rows), [])
        self.assertEqual([len(r) for r in self.rows], [100, 84])

    def test_misreadings_caught(self):
        lon, pro = copy.deepcopy(self.rows)
        find(lon, 84, 1943)["general"] = 26385                     # 26,335 read as 26,385: printed once by No. 84
        find(pro, 99, 1956)["birmingham"] = 300                    # the broken "3 0" read as 300
        bad = cp.check((lon, pro))
        self.assertTrue(any("London No. 84 1943" in b for b in bad))
        self.assertTrue(any("birmingham 1956" in b for b in bad))

    def test_revisions(self):
        lon, _ = self.rows
        self.assertEqual((find(lon, 108, 1968)["debit_total"], find(lon, 111, 1968)["debit_total"]), (599546, 600162))
        self.assertEqual((find(lon, 108, 1970)["credit"], find(lon, 112, 1970)["credit"]), (14391, 10969))
        lon2 = copy.deepcopy(lon)
        find(lon2, 112, 1972)["credit"] = 14060
        self.assertEqual(cp.check((lon2, self.rows[1])), ["London credit 1972: Nos. 111 14,006 and 112 14,060"])

    def test_facts(self):
        f = cp.facts(self.rows)
        self.assertEqual(sorted(f["afternoon"]), list(range(1968, 1975)))
        self.assertEqual(f["provincial"][1940], 1407.9)
        self.assertEqual(max(f["provincial"]), 1967)


if __name__ == "__main__":
    unittest.main()
