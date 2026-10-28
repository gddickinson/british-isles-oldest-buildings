"""Country banks (roadmap C5e2b2b2b1): Gilbart 1837, Tables I and II, read from the page images."""
import unittest

from bidb import change_banks as cb


class CountryBanks(unittest.TestCase):
    def test_counties_add_to_the_printed_totals(self):
        self.assertEqual(cb.check(), [])

    def test_misreading_caught(self):
        c = cb.counties()
        c["Yorkshire"][1811] = (57, 257)                 # 75 misread
        self.assertEqual(len(cb.check(c)), 1)
        c = cb.counties()
        c["Devonshire"][1815] = (41, 119)                # the known slip must stay exactly as printed
        self.assertEqual(len(cb.check(c)), 1)

    def test_table_one(self):
        lic = cb.licences()
        self.assertEqual([y for y, _, _ in lic], list(range(1809, 1833)))
        self.assertEqual(lic[5], (1814, 940, 27))
        self.assertEqual(lic[-1], (1832, 636, None))

    def test_series(self):
        pts, rows = cb.series()
        self.assertEqual(pts["banks_country_banks_ew"][1811], 739)
        self.assertEqual(sum(pts["banks_country_failures_ew"].values()), 311)
        self.assertNotIn(1831, pts["banks_country_failures_ew"])
        self.assertEqual(rows[0]["models"], ["banks_country_banks_ew"])
        self.assertIn("940 in 1814", rows[0]["note"])
        self.assertIn("Yorkshire had the most (75 in 1811-12)", rows[0]["note"])


if __name__ == "__main__":
    unittest.main()
