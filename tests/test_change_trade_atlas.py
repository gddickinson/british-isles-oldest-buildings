"""The main goods traded 1962-2024 as shares, from the Growth Lab's SITC Rev. 2 data (roadmap C5b2d3): shares without
gold, the comparison with the Annual Abstract, the written series."""
import csv
import unittest

from bidb import change_trade_atlas as ta
from bidb.change_firms import DATA


def _series(g):
    with open(DATA / f"gl_{g}_uk.csv", newline="") as f:
        return {int(r["year"]): float(r["value"]) for r in csv.DictReader(f)}


class Shares(unittest.TestCase):
    def test_gold_left_out(self):
        sh = ta.shares({2000: {"65": (10, 0), "71": (20, 0), "97": (70, 50), "04": (0, 25), "00": (70, 25)}})[2000]
        self.assertEqual(sh["textiles"], 10.0)                  # 10 of the 100 that are not gold
        self.assertEqual(sh["machinery"], 20.0)
        self.assertEqual(sh["cereals"], 50.0)
        self.assertAlmostEqual(sh["gold_x"], 70 / 170 * 100)
        self.assertAlmostEqual(sh["gold_i"], 50.0)

    def test_compare(self):
        gl = {1962: {g: 1.0 for g in ta.LABELS}, 1980: {g: 9.0 for g in ta.LABELS}}
        off = {1962: {g: 0.5 for g in ta.LABELS}, 1953: {g: 0.0 for g in ta.LABELS}}
        c0, c1, d = ta.compare(gl, off)
        self.assertEqual((c0, c1, d["coal"]), (1962, 1962, 0.5))

    def test_written_series_agree_with_the_abstract(self):
        off = ta.official()
        for g in ta.LABELS:
            s = _series(g)
            self.assertEqual(list(s), list(range(1962, max(s) + 1)), g)
            for y in range(1962, 1975):                         # within a point and a half in every year
                self.assertLess(abs(s[y] - off[y][g]), 1.5, (g, y))
        self.assertGreater(_series("machinery")[1999], 30)
        self.assertLess(_series("textiles")[1999], 2.5)


if __name__ == "__main__":
    unittest.main()
