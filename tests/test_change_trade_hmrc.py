"""The main goods traded since 2000 (roadmap C5b2c): HMRC headings summed per good, complete years, shares."""
import unittest

from bidb import change_trade_hmrc as th


class Hmrc(unittest.TestCase):
    def test_headings(self):
        every = [h for hs in th.GOODS.values() for h in hs] + th.GOLD
        self.assertEqual(len(every), len(set(every)))                       # no heading counted twice
        inside = lambda h: any(a <= int(h) <= b for a, b in th.RANGES)
        self.assertEqual([h for h in every if not inside(h)], [])          # every heading is fetched
        self.assertNotIn("7204", th.GOODS["iron"])                          # scrap left out, as old iron was
        self.assertNotIn("1006", th.GOODS["grain"])                         # rice left out
        self.assertEqual(set(th.GOODS), set(th.EXPORT_GOODS + th.IMPORT_GOODS))

    def test_complete(self):
        tot = {(f, m): 1.0 for f in (1, 2, 3, 4) for m in range(1, 13)}
        self.assertTrue(th.complete(tot))
        del tot[(3, 12)]
        self.assertFalse(th.complete(tot))

    def test_goods_and_series(self):
        heads = {(3, "0902"): (100.0, 50.0), (1, "0902"): (20.0, 10.0), (4, "0902"): (999.0, 9.0),   # tea exports out
                 (2, "5205"): (30.0, 3.0), (4, "5208"): (10.0, 1.0), (2, "8471"): (500.0, 5.0),
                 (4, "7108"): (400.0, 0.0), (3, "7108"): (100.0, 0.0)}
        tot = {(1, 1): 1000.0, (3, 1): 1100.0, (2, 1): 1000.0, (4, 1): 400.0}
        g = th.goods(heads, tot)
        self.assertEqual(g["tea"], (120.0, 60.0))
        self.assertEqual(g["cotton"], (40.0, 4.0))
        self.assertEqual(g["machinery"], (500.0, 5.0))
        self.assertEqual(g["exports"][0], 1000.0)                           # 1,400 less 400 of gold
        self.assertEqual(g["imports"][0], 2000.0)
        empty = {k: (0.0, 0.0) for k in th.GOODS}
        s = th.series({2000: {**empty, **g}})
        self.assertEqual(s["hmrc_tea_uk"], [[2000, 0.0]])                   # £ million, two decimals
        self.assertEqual(s["hmrc_textiles_share_uk"], [[2000, 4.0]])
        self.assertEqual(s["hmrc_metal_share_uk"], [[2000, 50.0]])
        self.assertEqual(s["hmrc_food_share_uk"], [[2000, 6.0]])


if __name__ == "__main__":
    unittest.main()
