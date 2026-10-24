"""Main imports by quantity from the Statistical Abstract (roadmap C5b2b3c1): the readings file, its totals, the join
of the old and new tables, units and the price index."""
import tempfile
import unittest
from pathlib import Path

from bidb import change_trade_quantities as tq

HEAD = "row,year,value,number,edition,leaf,page,table,note\n"


class TradeQuantities(unittest.TestCase):
    def test_readings_add_up(self):
        rows = tq.load()
        self.assertEqual(tq.check(rows), [])
        self.assertEqual(sorted(tq.goods(rows)), list(range(1868, 1912)))

    def test_old_and_new_tables_join(self):
        rows = tq.load()
        self.assertEqual(tq.overlap(rows), {})
        for y in (1897, 1898):
            a, b = tq.old_goods(rows, y), tq.new_goods(rows, y)
            for k in ("cotton", "sugar", "tea", "timber"):
                self.assertEqual(a[k], b[k], (k, y))
        rows["q59_tea"][1898] += 1
        self.assertIn(1898, tq.overlap(rows))

    def test_each_edition_has_its_own_rows(self):
        rows = tq.load()
        g = tq.goods(rows)
        self.assertEqual(g[1870]["sugar"], rows["q_sugar_refined"][1870] + rows["q_sugar_raw"][1870])
        self.assertEqual(g[1875]["wool"], rows["q_wool"][1875])
        self.assertEqual(g[1890]["wool"], rows["q_wool_sheep"][1890] + rows["q_wool_other"][1890])
        self.assertEqual(g[1890]["timber"], sum(rows["q_" + k][1890] for k in (
            "wood_hewnfir", "wood_hewnoak", "wood_hewnteak", "wood_hewnother", "wood_sawnfir", "wood_sawnother",
            "wood_staves")))
        self.assertEqual(g[1898], tq.new_goods(rows, 1898))
        self.assertEqual(g[1904]["grain"], sum(rows[k][1904] for k in tq.GRAIN59))  # from No. 62

    def test_units(self):
        self.assertAlmostEqual(tq.tons("grain", 1900, 20_000), 1.0)  # thousand tons: 20 cwt to the ton
        self.assertAlmostEqual(tq.tons("tea", 1900, 2_240_000), 1.0)
        self.assertAlmostEqual(tq.tons("cotton", 1911, 2240), 0.1)  # 1911 in centals of 100 lb
        self.assertAlmostEqual(tq.tons("timber", 1900, 2_500_000), 2.5)

    def test_check_finds_a_misread_figure(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "r.csv"
            p.write_text(HEAD + "".join(f"{k},1868,{v},30,x,516,40,21,\n" for k, v in (
                ("q_corn_wheat", 32639768), ("q_corn_barley", 7476490), ("q_corn_oats", 8112563),
                ("q_corn_maize", 11472226), ("q_corn_other", 4150657), ("q_corn_flourwheat", 3093022),
                ("q_corn_flourother", 62643), ("q_corn_total", 67007379))))
            rows = tq.load(p)
        self.assertEqual(tq.check(rows), ["q_corn_total 1868: parts - total = -10"])

    def test_series(self):
        q = {g: 20_000 for g in ("grain", "cotton", "sugar")} | {"wool": 2_240_000, "tea": 2_240_000,
                                                                 "timber": 1_000_000}
        v = {g: 100.0 for g in tq.GOODS}
        s = tq.series({1900: q, 1901: q}, {1900: v, 1901: {**v, "tea": 150.0}})
        self.assertEqual(s["sa_qty_grain_uk"], [[1900, 1.0], [1901, 1.0]])
        self.assertEqual(s["sa_qty_timber_uk"][0], [1900, 1.0])
        self.assertEqual(s["sa_qty_tea_price_uk"], [[1900, 100.0], [1901, 150.0]])


if __name__ == "__main__":
    unittest.main()
