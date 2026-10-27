"""Tea prices read from the Statistical Abstract page images (C2d3, C2d3b): files cover their years, and the
price of tea from India and Ceylon stays close to the average of all tea where both are printed."""
import unittest

from bidb import change_series as cs

DATA = cs.SRC / "data"


def points(name):
    return {p[0]: p[1] for p in cs.read_points(DATA / name)}


class TeaPrices(unittest.TestCase):
    def test_years(self):
        self.assertEqual(sorted(points("tea_auction_uk.csv")), [1913] + list(range(1920, 1939)))
        for name in ("tea_price_india_uk.csv", "tea_price_china_uk.csv"):
            self.assertEqual(sorted(points(name)), list(range(1908, 1923)), name)

    def test_india_close_to_all_tea(self):
        india, all_tea = points("tea_price_india_uk.csv"), points("tea_price_uk.csv")
        both = sorted(set(india) & set(all_tea))
        self.assertEqual(both, list(range(1908, 1920)))
        for y in both:
            self.assertLess(abs(india[y] - all_tea[y]), 0.5, y)

    def test_every_row_cites_its_page(self):
        import csv
        for name in ("tea_auction_uk.csv", "tea_price_india_uk.csv", "tea_price_china_uk.csv"):
            with open(DATA / name, newline="") as f:
                for r in csv.DictReader(f):
                    self.assertTrue(r["edition"] and r["leaf"].isdigit() and r["page"].isdigit(), (name, r["year"]))


if __name__ == "__main__":
    unittest.main()
