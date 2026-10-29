"""Savings banks 1846-1938 (roadmap C5e2b2b2b3a: Statistical Abstract) and 1939-1975 (C5e2b2b2b3b2b: Annual
Abstract), read from the page images."""
import copy
import unittest

from bidb import change_savings as cs
from bidb import change_savings_post as sp


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
        # the trustee banks' departments are printed together 1939-1948, so their lines start again in 1949
        self.assertEqual(sorted(pts["savings_due_trustee_uk"]), list(range(1846, 1939)) + list(range(1949, 1976)))
        self.assertEqual(sorted(pts["savings_due_po_uk"]), list(range(1863, 1976)))
        self.assertEqual(min(pts["savings_due_special_uk"]), 1924)
        self.assertEqual(pts["savings_due_po_uk"][1939], 523.7)
        self.assertEqual(cs.facts(self.rows)["over"], 1885)
        self.assertEqual(out[0]["models"], ["savings_due_po_uk", "savings_due_special_uk"])
        self.assertEqual([b[0] for b in out[0]["breaks"]], [1939])
        self.assertEqual([b[0] for b in out[6]["breaks"]], [1909, 1924, 1933])
        self.assertIn("passed the Post Office's ordinary accounts in 1965", out[0]["note"])

    def test_by_nation(self):
        nat = cs.by_nation(self.rows)
        self.assertEqual(sorted(nat["sc"]), list(range(1846, 1899)))
        # 1846: trustee banks only; England and Wales from England + Wales
        self.assertEqual(nat["ew"][1846], round((26759817 + 674657) / 1e6, 3))
        self.assertEqual(nat["ir"][1846], 2.925)
        # 1863: the Post Office added
        self.assertGreater(nat["ew"][1863] - nat["ew"][1862], 3)


class SavingsBanksAnnualAbstract(unittest.TestCase):
    rows = sp.load()

    def test_rows_add_up_balance_and_agree(self):
        self.assertEqual(sp.check(self.rows), [])
        self.assertEqual(len(self.rows), 2728)

    def test_misreadings_caught(self):
        rows = copy.deepcopy(self.rows)
        r = next(r for r in rows if (r["edition"], r["item"], r["year"]) == (99, "received_tsb_special", 1961))
        r["value"] = 141.4                                   # 111.4 read as 141.4: receipts no longer add up
        self.assertTrue(any("No. 99 1961 received" in b for b in sp.check(rows)))
        rows = copy.deepcopy(self.rows)
        r = next(r for r in rows if (r["edition"], r["item"], r["year"]) == (112, "interest_po", 1973))
        r["value"] = 58.8                                    # interest has no total: caught by the balance
        self.assertTrue(any("po No. 112 1973" in b for b in sp.check(rows)))

    def test_revisions_listed(self):
        rows = copy.deepcopy(self.rows)
        r = next(r for r in rows if (r["edition"], r["item"], r["year"]) == (99, "due_po", 1955))
        r["value"] = 1739.4
        self.assertTrue(any("('due_po', 1955)" in b for b in sp.check(rows)))
        best = sp.latest(self.rows)
        self.assertEqual(best[("due_po", 1971)], 1474.7)          # No. 112 revised No. 108's 1,472.0
        self.assertEqual(best[("due_po", 1949)], 1973.4)          # No. 88 revised No. 86's 1,982.9

    def test_trustee_departments_together(self):
        both = sp.tsb_both(self.rows)
        self.assertEqual(both[1939], 242.9)
        self.assertEqual(both[1949], round(714.9 + 110.9, 1))     # No. 96 prints them apart from 1949
        self.assertEqual(sorted(both), list(range(1939, 1976)))


if __name__ == "__main__":
    unittest.main()
