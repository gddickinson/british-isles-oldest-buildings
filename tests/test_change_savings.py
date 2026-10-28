"""Savings banks 1846-1938 (roadmap C5e2b2b2b3a): Statistical Abstract, read from the page images."""
import copy
import unittest

from bidb import change_savings as cs


def find(rows, edition, bank, year, measure):
    return next(r for r in rows if (r["edition"], r["bank"], r["year"], r["measure"]) == (edition, bank, year, measure))


class SavingsBanks(unittest.TestCase):
    rows = cs.load()

    def test_rows_add_up_and_balance(self):
        self.assertEqual(cs.check(self.rows), [])
        self.assertEqual(len(self.rows), 929)

    def test_misreading_caught_by_nations(self):
        rows = copy.deepcopy(self.rows)
        find(rows, "8", "trustee", 1850, "paid")["ireland"] = 875961      # 375,961 read as 875,961
        self.assertEqual(len(cs.check(rows)), 1)

    def test_misreading_caught_by_balance(self):
        rows = copy.deepcopy(self.rows)
        r = find(rows, "59", "post_office", 1905, "paid")                  # no nations from No. 59
        r["united_kingdom"] += 5000
        bad = cs.check(rows)
        self.assertTrue(any("post_office 1905" in b for b in bad))
        rows = copy.deepcopy(self.rows)
        find(rows, "83", "post_office", 1934, "closed")["united_kingdom"] = 558838   # the bold 3 read as 8
        self.assertTrue(any("1934" in b for b in cs.check(rows)))

    def test_editions_compared_with_interest_added(self):
        # No. 46's Post Office receipts include interest; No. 59 prints it apart
        self.assertEqual(find(self.rows, "46", "post_office", 1897, "received")["united_kingdom"],
                         find(self.rows, "59", "post_office", 1897, "received")["united_kingdom"]
                         + find(self.rows, "59", "post_office", 1897, "interest")["united_kingdom"])
        rows = copy.deepcopy(self.rows)
        find(rows, "59", "trustee", 1911, "due")["united_kingdom"] += 3
        self.assertTrue(any("Nos. 59 and 70" in b for b in cs.check(rows)))

    def test_latest_edition_and_revisions(self):
        best = cs.latest(self.rows)
        self.assertEqual(best[("trustee", 1860, "due")]["united_kingdom"], 41258368)   # No. 8's was an estimate
        self.assertEqual(best[("post_office", 1924, "due")]["edition"], "83")
        self.assertEqual(best[("post_office", 1924, "due")]["united_kingdom"], 280373000)

    def test_series(self):
        pts, out = cs.series(self.rows)
        self.assertEqual(sorted(pts["savings_due_trustee_uk"]), list(range(1846, 1939)))
        self.assertEqual(sorted(pts["savings_due_po_uk"]), list(range(1863, 1939)))
        self.assertEqual(min(pts["savings_due_special_uk"]), 1924)
        self.assertEqual(cs.facts(self.rows)["over"], 1885)
        self.assertEqual(out[0]["models"], ["savings_due_po_uk", "savings_due_special_uk"])
        self.assertEqual([b[0] for b in out[3]["breaks"]], [1909, 1924, 1933])


if __name__ == "__main__":
    unittest.main()
