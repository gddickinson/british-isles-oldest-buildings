"""Bank notes in circulation 1846-1922 (roadmap C5e2b2b2b2): Statistical Abstract, read from the page images."""
import copy
import unittest

from bidb import change_banknotes as cn


class BankNotes(unittest.TestCase):
    rows = cn.load()

    def test_rows_add_up_and_editions_agree(self):
        self.assertEqual(cn.check(self.rows), [])
        self.assertEqual(len(self.rows), 420)

    def test_misreading_caught(self):
        rows = copy.deepcopy(self.rows)
        rows[0]["scotland"] = 8018771                    # 3,018,771 read as 8,018,771
        self.assertEqual(len(cn.check(rows)), 1)
        rows = copy.deepcopy(self.rows)
        rows[1]["private"] += 9                          # private + joint stock no longer the country total
        self.assertEqual(len(cn.check(rows)), 1)

    def test_known_misprints_kept_as_printed(self):
        rows = copy.deepcopy(self.rows)
        r = next(r for r in rows if (r["edition"], r["year"], r["month"]) == ("59", 1897, "December"))
        r["bank_of_england"] = 27262928                  # misread: the known misprint must stay exactly as printed
        self.assertTrue(any("1897" in b for b in cn.check(rows)))

    def test_latest_edition_skips_misprints(self):
        best = cn.latest(self.rows)
        self.assertEqual(best[(1897, "December")]["edition"], "46")
        self.assertEqual(best[(1897, "December")]["bank_of_england"], 27262697)
        self.assertEqual(best[(1893, "December")]["bank_of_england"], 25296323)
        self.assertEqual(best[(1910, "March")]["edition"], "68")

    def test_series(self):
        pts, out = cn.series(self.rows)
        self.assertEqual(sorted(pts["banknotes_boe_uk"]), list(range(1846, 1923)))
        self.assertEqual(max(pts["banknotes_country_ew"]), 1921)
        self.assertEqual(max(pts["banknotes_private_ew"]), 1911)      # No. 68 does not divide the country banks
        self.assertAlmostEqual(pts["banknotes_country_ew"][1846], 7.646, places=3)
        self.assertEqual(out[0]["models"], ["banknotes_scotland_uk", "banknotes_ireland_uk"])
        self.assertIn("£2,000 remained in March 1921", out[3]["note"])


if __name__ == "__main__":
    unittest.main()
