"""Main exports by value from the Statistical Abstract (roadmap C5b2b1, C5b2b2, C5b2b3d): the readings file, its totals and the joins."""
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
        self.assertEqual(sorted(tg.goods(rows)), list(range(1846, 1939)))

    def test_old_and_new_tables_agree(self):
        self.assertEqual(tg.overlap(tg.load()), {1897: {}, 1898: {}})

    def test_classification_of_1920(self):
        rows = tg.load()
        # 1911 from No. 70's rows: what No. 59 calls cotton yarn, linen and wool yarn
        g70 = tg.c20_goods(rows, 70, 1911)
        self.assertEqual(g70["cotton_yarn"], rows["cottont_yarn"][1911])
        self.assertEqual(g70["linen_yarn"] + g70["linen_manuf"], tg.new_goods(rows, 1911)["linen_yarn"]
                         + tg.new_goods(rows, 1911)["linen_manuf"])
        # the later edition is used where two give a year, but 1911 stays No. 59's
        g = tg.goods(rows)
        self.assertEqual(g[1911], tg.new_goods(rows, 1911))
        self.assertEqual(g[1924], tg.c20_goods(rows, 83, 1924))
        self.assertEqual(g[1923], tg.c20_goods(rows, 70, 1923))

    def test_c20_known_differences_are_checked(self):
        rows = tg.load()
        rows["n83_m_other"][1924] += 1
        self.assertIn(1924, tg.overlap(rows))

    def test_totals_match_the_summary_table(self):
        rows, summary = tg.load(), tv.load()
        for y, v in rows["all"].items():
            if 1854 <= y < 1885:  # the summary table begins in 1854 and adds the parcel post from 1885
                self.assertEqual(v, summary[y]["uk_produce"], y)
        for y, v in rows["n70_all"].items():
            self.assertEqual(v, summary[y]["uk_produce"], y)

    def test_no_8_years(self):
        rows = tg.load()
        g = tg.goods(rows)
        # 1846-47: No. 8's wider lines (old iron inside wrought iron; tin plates with tin and pewter ware)
        self.assertEqual(g[1846]["iron"], rows["iron_total"][1846] + rows["tin_pewter"][1846])
        # 1848: tin plates from No. 10, old iron still in; from 1849 old iron left out (Nos. 11 and 13)
        self.assertEqual(g[1848]["iron"], rows["iron_total"][1848] + rows["tin_plates"][1848])
        self.assertEqual(g[1853]["iron"], 10845422 - 72741 + 1181069)
        # No. 8's 1854 column (not loaded: No. 16 gives 1854) agrees with No. 16; all exports 1846-53 from table 15
        self.assertEqual(rows["all"][1853], 98933781)
        del rows["iron_oldin"][1850]
        with self.assertRaises(KeyError):
            tg.old_goods(rows, 1850)

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
