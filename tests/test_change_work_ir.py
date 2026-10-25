"""Ireland's occupations at the censuses of 1891 and 1901 by sub-order (roadmap C5c2c2c1): Table 91 of the 1901 General
Report, checked against its own totals."""
import unittest

from bidb import change_work_ir as ir


class Table91(unittest.TestCase):
    def setUp(self):
        self.rows = ir.load()

    def test_every_row_order_and_class_agrees(self):
        self.assertEqual(ir.check(self.rows), [])

    def test_every_sub_order_once(self):
        codes = [r["code"] for r in self.rows if r["level"] == "sub_order"]
        self.assertEqual(len(codes), len(set(codes)))
        self.assertEqual(len(codes), 80)

    def test_a_misreading_is_caught(self):
        rows = [dict(r) for r in self.rows]
        next(r for r in rows if r["code"] == "17.3")["m1891"] += 10
        self.assertEqual(len(ir.check(rows)), 2)              # the row and its order

    def test_misprint_kept_as_printed(self):
        printed = next(r for r in self.rows if r["code"] == "16.1")
        self.assertEqual(printed["f1901"], 5570)
        fixed = next(r for r in ir.corrected(self.rows) if r["code"] == "16.1")
        self.assertEqual(fixed["f1901"], 5572)

    def test_totals(self):
        self.assertEqual(ir.occupied(self.rows), {1891: 2145729, 1901: 1963817})
        self.assertEqual(ir.sub_orders(self.rows)["3.5"], 93280)       # students among the literary and scientific
        self.assertEqual(ir.sub_orders(self.rows, 1901)["22.2"], 139272)


if __name__ == "__main__":
    unittest.main()
