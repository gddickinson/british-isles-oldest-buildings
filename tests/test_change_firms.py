"""Firms through time (bidb.change_firms, roadmap C4a): which Wikidata items count as firms, their industry, and the
decade counts of the graphs."""
import unittest

from bidb import change_firms as cf


def item(name, opened, classes, inds="", closed=None, coord="POINT(-0.1 51.5)"):
    b = {"i": {"value": "http://www.wikidata.org/entity/Q1"}, "name": {"value": name}, "open": {"value": str(opened)},
         "classes": {"value": classes}, "coord": {"value": coord}}
    if inds:
        b["inds"] = {"value": inds}
    if closed:
        b["close"] = {"value": str(closed)}
    return b


class FirmsTest(unittest.TestCase):
    def test_not_firms(self):
        for c in (["parish council"], ["NHS foundation trust"], ["business", "railway line"], ["learned society"],
                  ["website"], ["non-metropolitan district council"]):
            self.assertFalse(cf.is_firm(c), c)
        for c in (["business"], ["investment trust"], ["building society"], ["consumer cooperative"], ["brewery"]):
            self.assertTrue(cf.is_firm(c), c)

    def test_sector(self):
        name = lambda k: None if k is None else cf.SECTORS[k][0]
        self.assertEqual(name(cf.sector(["brewery"], [])), "Food, drink and tobacco")
        self.assertEqual(name(cf.sector(["business"], ["insurance"])), "Banks, finance and insurance")
        self.assertEqual(name(cf.sector(["railway company"], [])), "Transport and utilities")
        self.assertEqual(name(cf.sector(["publishing house"], [])), "Publishing, print and media")
        self.assertEqual(name(cf.sector(["business"], ["mining"])), "Farming, mining and quarrying")
        self.assertEqual(name(cf.sector(["shipbuilding company"], [])), "Making things")
        self.assertEqual(name(cf.sector(["retail chain"], [])), "Shops and trade")
        self.assertEqual(name(cf.sector(["law firm"], [])), "Services and other")
        self.assertEqual(name(cf.sector(["business"], [], "Benskins Brewery")), "Food, drink and tobacco")
        self.assertIsNone(cf.sector(["business"], [], "A. Gray & Son"))        # the name never means "services"

    def test_rows_and_counts(self):
        bs = [item("Old Bank", 1694, "bank"), item("Shut Mill", 1790, "business", "textile industry", closed=1890),
              item("Bad Dates", 1900, "business", closed=1850), item("Parish", 1894, "parish council"),
              item("Abroad", 1990, "company", coord="POINT(-74.0 40.7)")]
        rows = cf.firms(bs)
        self.assertEqual([r[0] for r in rows], ["Old Bank", "Shut Mill"])          # dates out of order, council, abroad
        self.assertEqual(rows[1][4:6], [1890, 5])                                  # closed; Making things
        counts = cf.founded(bs)
        self.assertEqual(counts[1790][:2], [1, 1])
        self.assertEqual(counts[1690][2 + 1], 1)                                   # a bank
        self.assertNotIn(1890, counts)                                             # the council

    def test_head_office_spread(self):
        dy, dx = cf._jitter("http://www.wikidata.org/entity/Q42")
        self.assertLess(abs(dy), 0.01)
        self.assertLess(abs(dx), 0.015)
        self.assertEqual((dy, dx), cf._jitter("http://www.wikidata.org/entity/Q42"))


if __name__ == "__main__":
    unittest.main()
