"""Scotland's occupations at the censuses of 1901 and 1911 (roadmap C5c2c2a): Table D1 of the 1911 report read line by
line, checked against its printed changes and totals, and grouped into three sectors."""
import unittest

from bidb import change_work_sc as sc
from bidb import change_work_sc_1891 as sc91


class Readings(unittest.TestCase):
    def setUp(self):
        self.rows = sc.load()

    def test_every_line_and_total_agrees(self):
        self.assertEqual(sc.check(self.rows), [])

    def test_every_line_once(self):
        self.assertEqual(sorted(r["line"] for r in self.rows), list(range(1, 398)))

    def test_a_misreading_is_caught(self):
        rows = [dict(r) for r in self.rows]
        rows[0]["m1911"] += 10
        self.assertTrue(any(p.startswith("m line") or p.startswith("m a") for p in sc.check(rows)))

    def test_braces_stay_in_one_sector(self):
        self.assertEqual(sc._brackets_in_one_sector(self.rows), [])

    def test_every_line_in_one_sector(self):
        groups = (sc.PRIMARY, sc.SECONDARY, sc.SERVICES, sc.NO_INDUSTRY)
        for n in range(1, 398):
            self.assertEqual(sum(n in g for g in groups), 1, n)


class Sectors(unittest.TestCase):
    def test_shares(self):
        s = sc.shares()
        self.assertEqual(s[1901], (18.98, 43.62, 37.4))
        self.assertEqual(s[1911], (19.05, 41.71, 39.24))

    def test_dealers_in_services(self):
        for line in (131, 188, 311, 338, 348, 354):          # coal, ironmongers, drapers, butchers, grocers, tobacco
            self.assertIn(line, sc.SERVICES)
        for line in (343, 356, 394):                          # bread makers, brewers, engine drivers
            self.assertIn(line, sc.SECONDARY)

    def test_left_out(self):
        self.assertEqual(sc.left_out(), {1901: 2.8, 1911: 1.7})



class Census1891(unittest.TestCase):
    def test_every_sub_order_and_class_agrees(self):
        self.assertEqual(sc91.check(), [])

    def test_a_misreading_is_caught(self):
        rows = sc91.load()
        next(r for r in rows if r["line"] == "Baker")["value"] += 100
        self.assertEqual(len(sc91.check(rows)), 1)

    def test_shared_lines(self):
        self.assertAlmostEqual(sc91.split("x:354/353+354"), (715 + 1232) / (811 + 2476 + 715 + 1232))

    def test_shares(self):
        self.assertEqual(sc91.shares(), {1891: (19.75, 42.73, 37.52)})
        self.assertEqual(sc91.left_out(), {1891: 3.7})

    def test_every_kind_known(self):
        for r in sc91.load():
            self.assertIn(r["kind"].split(":")[0], sc91.KINDS)


if __name__ == "__main__":
    unittest.main()
