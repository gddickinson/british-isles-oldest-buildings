"""Main imports by quantity from the Statistical Abstract (roadmap C5b2b3c1-C5b2b3c3): the readings file, its totals,
the joins of the editions, units and the price index."""
import tempfile
import unittest
from pathlib import Path

from bidb import change_trade_quantities as tq

HEAD = "row,year,value,number,edition,leaf,page,table,note\n"


class TradeQuantities(unittest.TestCase):
    def test_readings_add_up(self):
        rows = tq.load()
        self.assertEqual(tq.check(rows), [])
        self.assertEqual(sorted(tq.goods(rows)), list(range(1854, 1939)))

    def test_early_editions(self):
        rows = tq.load()
        g, p = tq.goods(rows), tq.price_goods(rows)
        self.assertNotIn("grain", g[1856])  # Nos. 16 and 18 give no other kinds of corn
        self.assertNotIn("timber", g[1856])
        self.assertEqual(g[1857]["grain"], rows["q_corn_total"][1857])  # No. 19
        self.assertEqual(g[1855]["sugar"], rows["qe_sugar_refined"][1855] + rows["qe_sugar_rawtotal"][1855])
        # prices to 1867 with the values' editions: No. 18's timber (with teak), No. 19's grain
        self.assertEqual(p[1860]["timber"], sum(rows["qe_" + k][1860] for k in tq.EARLY_WOOD))
        self.assertEqual(p[1860]["grain"], g[1860]["grain"])
        self.assertEqual(p[1870], g[1870])
        bad, timber = tq.early_overlap(rows)
        self.assertEqual(bad, {})
        self.assertEqual(sorted(timber), list(range(1857, 1868)))
        self.assertTrue(all(d > 0 for d in timber.values()))  # No. 19 always above No. 18
        rows["qe_tea"][1860] += 1
        self.assertIn(1860, tq.early_overlap(rows)[0])

    def test_known_slip(self):
        rows = tq.load()
        self.assertEqual(rows["qe_wood_hewntotal"][1854], 1216920)  # as printed
        self.assertEqual(tq.check(rows), [])
        rows["qe_wood_hewntotal"][1855] += 7
        self.assertEqual(tq.check(rows), ["qe_wood_hewntotal 1855: parts - total = -7"])

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
        self.assertAlmostEqual(tq.tons("cotton", 1911, 2240), 0.1)  # from 1911 in centals of 100 lb
        self.assertAlmostEqual(tq.tons("cotton", 1930, 2240), 0.1)
        self.assertAlmostEqual(tq.tons("softwood", 1930, 2_500_000), 2.5)
        self.assertAlmostEqual(tq.tons("timber", 1900, 2_500_000), 2.5)

    def test_classification_of_1920(self):
        rows = tq.load()
        self.assertEqual(tq.c20_overlap(rows), {})
        g = tq.goods(rows)
        self.assertEqual(g[1911], tq.new_goods(rows, 1911) | {"softwood": 5382643 + 2896009})  # No. 59, No. 70's softwood
        self.assertEqual(g[1919]["cotton"], rows["q70_cotton"][1919])  # waste inside raw cotton to 1919
        self.assertAlmostEqual(g[1920]["cotton"], rows["q70_cotton"][1920] + rows["q70_cotton_waste"][1920] * 1.12)
        self.assertEqual(g[1923]["wool"], rows["q70_wool"][1923] * 100)  # No. 70: centals
        self.assertEqual(g[1924]["tea"], rows["q83_tea"][1924] * 1000)  # No. 83: thousand lb
        self.assertEqual(g[1934]["softwood"], rows["q83_wood_sawnsoft"][1934] + rows["q83_wood_pitprops"][1934])
        self.assertNotIn("softwood", g[1935])
        self.assertNotIn("timber", g[1912])
        rows["q83_wood_pitprops"][1925] += 1
        self.assertEqual(tq.c20_overlap(rows), {1925: {"softwood": 1}})
        rows["q83_wood_pitprops"][1925] -= 1
        rows["q83_tea"][1924] += 1  # beyond the rounding of thousand lb
        self.assertIn(1924, tq.c20_overlap(rows))
        rows["q70_barley"][1911] += 5
        self.assertEqual(tq.c20_overlap(rows)[1911], {"grain": tq.C20_KNOWN["grain"] + 5})

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

    def test_timber_price_linked(self):
        q = {g: 20_000 for g in ("grain", "cotton", "sugar")} | {"wool": 2_240_000, "tea": 2_240_000}
        v = {g: 100.0 for g in tq.GOODS}
        by_year = {1900: q | {"timber": 1e6}, 1901: q | {"timber": 1e6, "softwood": 1e6}, 1902: q | {"softwood": 1e6}}
        by_value = {1900: v, 1901: {**v, "timber": 120.0, "softwood": 60.0}, 1902: {**v, "softwood": 90.0}}
        s = tq.series(by_year, by_value)
        self.assertEqual(s["sa_qty_timber_price_uk"], [[1900, 100.0], [1901, 120.0], [1902, 180.0]])
        self.assertEqual(s["sa_qty_softwood_uk"], [[1901, 1.0], [1902, 1.0]])


if __name__ == "__main__":
    unittest.main()
