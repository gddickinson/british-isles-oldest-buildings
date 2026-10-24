"""Main imports by value from the Statistical Abstract (roadmap C5b2b3a): the readings file, its totals and the join."""
import tempfile
import unittest
from pathlib import Path

from bidb import change_trade_imports as ti

HEAD = "row,year,value,number,edition,leaf,page,table,note\n"


class TradeImports(unittest.TestCase):
    def test_readings_add_up(self):
        rows = ti.load()
        self.assertEqual(ti.check(rows), [])
        self.assertEqual(sorted(ti.goods(rows)), list(range(1854, 1912)))

    def test_old_and_new_tables_join(self):
        rows = ti.load()
        self.assertEqual(ti.overlap(rows), {})
        # the known differences are lentils (grain) and 1898's revised sheep's wool; the rest agree to the pound
        for y in (1897, 1898):
            a, b = ti.old_goods(rows, y), ti.new_goods(rows, y)
            for k in ("cotton", "sugar", "tea", "timber"):
                self.assertEqual(a[k], b[k], (k, y))
        rows["n59_tea"][1897] += 1
        self.assertIn(1897, ti.overlap(rows))

    def test_each_edition_has_its_own_rows(self):
        rows = ti.load()
        g = ti.goods(rows)
        self.assertEqual(g[1855]["sugar"], rows["sugar_refined"][1855] + rows["sugar_rawtotal"][1855])
        self.assertEqual(g[1860]["timber"], rows["wood_hewntotal"][1860] + rows["wood_teak"][1860]
                         + rows["wood_sawntotal"][1860] + rows["wood_staves"][1860])
        self.assertEqual(g[1875]["wool"], rows["wool_all"][1875])
        self.assertEqual(g[1890]["wool"], rows["wool_sheep"][1890] + rows["wool_other"][1890])
        self.assertEqual(g[1898], ti.new_goods(rows, 1898))

    def test_check_finds_a_misread_figure(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "r.csv"
            p.write_text(HEAD + "".join(f"{k},1870,{v},30,x,522,46,22,\n" for k, v in (
                ("corn_wheat", 16264027), ("corn_barley", 2831885), ("corn_oats", 4381607), ("corn_maize", 5790550),
                ("corn_other", 1498043), ("corn_flourwheat", 3383751), ("corn_flourother", 20358),
                ("corn_total", 34170231))))
            rows = ti.load(p)
        self.assertEqual(ti.check(rows), ["corn_total 1870: parts - total = -10"])

    def test_series(self):
        year = {"grain": 3e6, "cotton": 2e6, "wool": 1e6, "sugar": 1e6, "tea": 1e6, "timber": 1e6}
        s = ti.series({1900: year}, {1900: 20e6})
        self.assertEqual(s["sa_imports_grain_uk"], [[1900, 3.0]])
        self.assertEqual(s["sa_imports_food_share_uk"], [[1900, 25.0]])
        self.assertEqual(s["sa_imports_materials_share_uk"], [[1900, 20.0]])


if __name__ == "__main__":
    unittest.main()
