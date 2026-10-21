"""Period labels by nation: .venv/bin/python -m unittest discover tests"""
import unittest

from bidb.classify import period_for, regional_period


class RegionalPeriod(unittest.TestCase):
    def test_no_roman_period_in_ireland_or_man(self):
        self.assertEqual(regional_period(period_for(450 - 100), "Republic of Ireland"), "Iron Age")
        self.assertEqual(regional_period(period_for(200), "Isle of Man"), "Iron Age")
        self.assertEqual(regional_period(period_for(200), "Wales"), "Roman Britain")
        self.assertEqual(regional_period(period_for(800), "Northern Ireland"), "Early Medieval")


if __name__ == "__main__":
    unittest.main()
