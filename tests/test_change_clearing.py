"""Bankers' clearing houses 1868-1938 (roadmap C5e2b2b2b3b1): Statistical Abstract, read from the page images."""
import copy
import unittest

from bidb import change_clearing as cc


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
        pts, out = cc.series(self.rows)
        self.assertEqual(sorted(pts["clearing_london_uk"]), list(range(1868, 1939)))
        self.assertEqual(sorted(pts["clearing_provincial_uk"]), list(range(1897, 1939)))
        self.assertEqual(min(pts["clearing_country_uk"]), 1902)
        self.assertEqual(pts["clearing_london_uk"][1929], 44897)
        self.assertEqual(pts["clearing_provincial_uk"][1919], 2284.4)    # No. 71, with Bradford
        self.assertEqual([b[0] for b in out[3]["breaks"]], [1909, 1912, 1921])
        self.assertTrue(out[0]["log"])


if __name__ == "__main__":
    unittest.main()
