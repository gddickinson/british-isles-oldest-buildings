"""Main exports by value from the Statistical Abstract (roadmap C5b2b1): the readings file, its totals and the joins."""
import tempfile
import unittest
from pathlib import Path

from bidb import change_trade_goods as tg
from bidb import change_trade_values as tv

HEAD = "row,year,value,number,edition,leaf,page,table,note\n"


class TradeGoods(unittest.TestCase):
    def test_readings_add_up(self):
        rows = tg.load()
        self.assertEqual(tg.check(rows), [])
        self.assertEqual(sorted(tg.goods(rows)), list(range(1854, 1912)))

    def test_old_and_new_tables_agree(self):
        self.assertEqual(tg.overlap(tg.load()), {1897: {}, 1898: {}})

    def test_totals_match_the_summary_table(self):
        rows, summary = tg.load(), tv.load()
        for y, v in rows["all"].items():
            if y < 1885:  # the summary table adds the parcel post from 1885
                self.assertEqual(v, summary[y]["uk_produce"], y)

    def test_check_finds_a_misread_figure(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "r.csv"
            p.write_text(HEAD + "linen_white,1875,5904958,30,x,552,76,31,\nlinen_printed,1875,470295,30,x,552,76,31,\n"
                                "linen_sail,1875,243312,30,x,552,76,31,\nlinen_other,1875,654355,30,x,552,76,31,\n"
                                "linen_total,1875,7272930,30,x,552,76,31,\n")
            rows = tg.load(p)
        self.assertEqual(tg.check(rows), ["linen_total 1875: parts - total = -10"])

    def test_series(self):
        year = {"coal": 2e6, "cotton_yarn": 1e6, "cotton_manuf": 3e6, "wool_yarn": 0, "wool_manuf": 1e6,
                "linen_yarn": 0, "linen_manuf": 1e6, "iron": 1e6, "machinery": 1e6}
        s = tg.series({1900: year}, {1900: 20e6})
        self.assertEqual(s["sa_goods_cotton_uk"], [[1900, 4.0]])
        self.assertEqual(s["sa_goods_textiles_share_uk"], [[1900, 30.0]])
        self.assertEqual(s["sa_goods_metal_share_uk"], [[1900, 20.0]])


if __name__ == "__main__":
    unittest.main()
