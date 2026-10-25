"""Ireland's occupation lines at the censuses of 1891, 1901 and 1911 (roadmap C5c2c2c2-c4): every sub-order that mixes
sectors read line by line and checked against its printed total; 1911 the four provinces summed."""
import unittest

from bidb import change_work_ir as ir, change_work_ir_1911 as ir11


class Lines(unittest.TestCase):
    def setUp(self):
        self.lines = ir.load_lines()

    def test_every_sub_order_adds_up(self):
        self.assertEqual(ir.check_lines(self.lines), [])

    def test_a_misreading_is_caught(self):
        lines = [dict(r) for r in self.lines]
        next(r for r in lines if r["year"] == 1911 and r["province"] == "Ulster" and r["line"] == "Tailor")["value"] += 1
        self.assertEqual(len(ir.check_lines(lines)), 1)

    def test_kinds_known(self):
        self.assertEqual({r["kind"] for r in self.lines if not r["kind"].startswith("x:")} - set(ir.SECTOR), set())

    def test_every_province_read(self):
        self.assertEqual({r["province"] for r in self.lines if r["year"] == 1911}, set(ir11.PROVINCES))


class Frame1911(unittest.TestCase):
    def test_provinces_add_to_ireland(self):
        self.assertEqual(ir11.check(), [])
        self.assertEqual(ir11.occupied(), 1817290)

    def test_whole_classes(self):
        s = ir11.sub_orders()
        self.assertEqual(set(s) & {"I", "II", "III"}, {"I", "II", "III"})
        self.assertEqual(ir.whole_kind("II"), "s")


class Shares(unittest.TestCase):
    def test_three_censuses(self):
        s = ir.shares()
        self.assertEqual(s[1901], (47.4, 21.8, 30.8))
        self.assertEqual(sorted(s), [1891, 1901, 1911])
        self.assertTrue(all(abs(sum(v) - 100) < 0.05 for v in s.values()))
        self.assertEqual(ir.left_out(), {1891: 5.8, 1901: 6.0, 1911: 8.2})


if __name__ == "__main__":
    unittest.main()
