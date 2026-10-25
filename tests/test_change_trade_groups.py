"""The main goods traded 1938-1952 by group (roadmap C5b2d1): class totals, latest edition per year, shares."""
import unittest

from bidb import change_trade_groups as tg


class Groups(unittest.TestCase):
    def setUp(self):
        self.rows = tg.load()

    def test_readings(self):
        self.assertEqual(tg.check(self.rows), [])                 # every edition's classes add up to its totals
        g = tg.goods(self.rows)
        self.assertEqual(list(g), list(range(1938, 1953)))
        self.assertEqual({y: v["edition"] for y, v in g.items() if y in (1938, 1939, 1941, 1943, 1952)},
                         {1938: 90, 1939: 84, 1941: 88, 1943: 89, 1952: 90})
        self.assertEqual(g[1938]["coal"], 40.7)                   # coal 37.4 + coke and fuel 3.3
        self.assertEqual(g[1939]["exports"], 439.5)               # No. 84: sum of the classes (its total is 440)
        self.assertEqual(g[1952]["imports"], 3481.5)

    def test_check_finds_a_misread(self):
        self.rows[89]["i_food"][1945] += 1.0
        self.assertEqual(tg.check(self.rows), ["No. 89 1945 i: classes 1104.7 != total 1103.7"])

    def test_series(self):
        y = {"cotton": 30.0, "wool": 20.0, "coal": 10.0, "iron": 10.0, "machinery": 30.0, "grain": 50.0,
             "raw_cotton": 10.0, "raw_wool": 10.0, "timber": 5.0, "exports": 200.0, "imports": 500.0}
        s = tg.series({1950: y})
        self.assertEqual(s["aa_textiles_share_uk"], [[1950, 25.0]])
        self.assertEqual(s["aa_metal_share_uk"], [[1950, 25.0]])
        self.assertEqual(s["aa_grain_share_uk"], [[1950, 10.0]])
        self.assertEqual(s["aa_materials_share_uk"], [[1950, 5.0]])
        self.assertEqual(s["aa_machinery_uk"], [[1950, 30.0]])

    def test_revisions(self):
        self.assertEqual(tg.revisions(self.rows, "machinery", 1938), {84: 57.9, 88: 57.2, 89: 57.2, 90: 57.2})


if __name__ == "__main__":
    unittest.main()
