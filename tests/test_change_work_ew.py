"""Occupations by sector in England and Wales 1881-1911 (roadmap C5c2b1): the readings from the 1911 Summary Tables, their
sums, the sharing out of bracketed lines, the sectors and the dots written with Keibek's."""
import csv
import unittest

from bidb import change_work as cw
from bidb import change_work_ew as ew
from bidb.change_firms import DATA


class Readings(unittest.TestCase):
    def setUp(self):
        self.rows = ew.load()

    def test_every_printed_sum_agrees(self):
        self.assertEqual(ew.check(self.rows), [])

    def test_a_misread_figure_is_found(self):
        rows = {k: dict(v) for k, v in self.rows.items()}
        rows["t65_o01"][1911] = 239261                 # the first reading, 50,000 short
        self.assertTrue(any("1911: orders" in b for b in ew.check(rows)))
        rows = {k: dict(v) for k, v in self.rows.items()}
        rows["t64_f_416"][1901] = 11027                # the blurred total, 900 short
        self.assertTrue(any("o20_food" in b for b in ew.check(rows)))

    def test_every_reading_has_its_page(self):
        with open(ew.READINGS, newline="") as f:
            for r in csv.DictReader(f):
                self.assertEqual(r["edition"], "censusofenglandw1911grea")
                self.assertIn((r["table"], r["leaf"], r["page"]),
                              {("65", "283", "274"), ("65", "285", "276"), ("65", "287", "278"), ("64", "281", "272")})


class Sectors(unittest.TestCase):
    def test_bracket_shared_as_in_1901(self):
        rows = {"t64_m_408": {1901: 300}, "t64_m_409": {1901: 100}, "t64_m_408+409": {1881: 1000}}
        self.assertEqual(ew.split(rows, "m", 1881), {"408": 750, "409": 250})

    def test_sectors_cover_everyone_occupied(self):
        rows = ew.load()
        for y in ew.YEARS:
            self.assertAlmostEqual(sum(ew.sectors(rows, y)), rows["t65_total_occupied"][y], places=6)

    def test_shares(self):
        s = ew.shares()
        for y, v in s.items():
            self.assertAlmostEqual(sum(v), 100, delta=0.02)
        self.assertEqual(s[1881], (18.23, 42.59, 39.18))
        self.assertEqual(s[1911], (14.95, 41.74, 43.31))

    def test_dots_follow_keibek(self):
        est = {sec: [(1851, 1.0, None, None, "k")] for sec in cw.SECTORS}
        out = cw.with_census(est, ew.points())
        self.assertEqual([r[0] for r in out["primary"]], [1851, 1881, 1891, 1901, 1911])
        self.assertIn("Census of England and Wales 1911", out["tertiary"][-1][4])

    def test_written_dots(self):
        with open(DATA / "work_secondary_est.csv", newline="") as f:
            rows = {int(r["year"]): float(r["value"]) for r in csv.DictReader(f)}
        self.assertEqual(rows[1601], 33.5)
        self.assertEqual(rows[1901], 43.3)


if __name__ == "__main__":
    unittest.main()
