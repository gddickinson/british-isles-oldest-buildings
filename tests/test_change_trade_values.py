"""Overseas trade values from the Statistical Abstract (roadmap C5b2a): the readings file and its own sums."""
import tempfile
import unittest
from pathlib import Path

from bidb import change_trade_values as tv

HEAD = "year,imports,net_imports,uk_produce,re_exports,total_exports,total_trade,number,edition,leaf,page,table,note\n"


class TradeValues(unittest.TestCase):
    def test_readings_add_up(self):
        rows = tv.load()
        self.assertEqual(tv.check(rows), [])
        self.assertEqual((min(rows), max(rows)), (1854, 1938))
        self.assertEqual(rows[1913]["imports"], 768_734_739)

    def test_check_finds_a_misread_figure(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "r.csv"
            p.write_text(HEAD + "1868,294460214,,179677812,48100642,227778454,522472062,18,x,527,17,13,\n"
                                "1869,295460214,248399119,189953957,47061095,237015052,,30,x,509,33,19,\n")
            rows = tv.load(p)
        self.assertEqual(tv.check(rows), ["1868: imports + exports != total trade"])

    def test_series(self):
        rows = {1913: {"imports": 768_734_739, "uk_produce": 525_253_595, "re_exports": 109_566_731,
                       "total_exports": 634_820_326}}
        s = tv.series(rows)
        self.assertEqual(s["sa_trade_imports_uk"], [[1913, 768.73]])
        self.assertEqual(s["sa_trade_reexport_share_uk"], [[1913, 17.26]])


if __name__ == "__main__":
    unittest.main()
