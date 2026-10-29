"""Patents in Ireland (roadmap C5e2b2b2c): national applications and grants, applications from the State and European
patents with effect in Ireland, one printed figure per row from the IPOI annual reports 2002-2025."""
import copy
import unittest

from bidb import change_patents_ie as cp


class Patents(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows = cp.load()

    def test_checks_pass(self):
        self.assertEqual(cp.check(self.rows), [])

    def test_a_part_unlike_its_total_is_caught(self):
        rows = copy.deepcopy(self.rows)
        r = next(r for r in rows if (r["report"], r["year"], r["measure"]) == (2010, 2010, "apps_short"))
        r["value"] += 1
        bad = cp.check(rows)
        self.assertTrue(any("apps_full" in b and "report 2010" in b for b in bad))

    def test_a_revision_not_known_is_caught(self):
        rows = copy.deepcopy(self.rows)
        r = next(r for r in rows if (r["report"], r["year"], r["measure"]) == (2023, 2022, "grants_total"))
        r["value"] = 72
        self.assertTrue(any("grants_total" in b for b in cp.check(rows)))

    def test_latest_report_kept(self):
        k = cp.latest(self.rows)
        self.assertEqual(k["apps_state"][2015], 250)          # 289 in the 2015 report
        self.assertEqual(k["apps_state"][2017], 183)
        self.assertEqual(k["ep_granted"][2019], 135374)        # the table, not the text
        self.assertEqual((k["grants_full"][2014], k["grants_short"][2014]), (69, 79))
        self.assertEqual((k["apps_total"][2000], k["grants_total"][2000]), (1079, 456))
        self.assertEqual((k["apps_total"][2025], k["grants_total"][2025], k["ep_granted"][2025]), (591, 110, 119552))

    def test_series(self):
        pts, rows = cp.series(cp.latest(self.rows))
        self.assertEqual(len(rows), 6)
        self.assertEqual(sorted(pts["ie_patents_applications"]), list(range(2000, 2026)))
        notes = {r["id"]: r.get("note", "") for r in rows}
        self.assertIn("from 1,169 in 2001 to 206 in 2022", notes["ie_patents_applications"])
        self.assertIn("135,374 at their height in 2019", notes["ie_patents_ep"])
        self.assertIn("642 of 774 in 2024", notes["ie_patents_short"])
        self.assertTrue(all(len(r.get("models", [])) <= 2 for r in rows))
        self.assertTrue(next(r for r in rows if r["id"] == "ie_patents_ep")["log"])


if __name__ == "__main__":
    unittest.main()
