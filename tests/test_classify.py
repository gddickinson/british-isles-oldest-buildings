"""Period labels by nation: .venv/bin/python -m unittest discover tests"""
import sqlite3
import unittest

from bidb.classify import period_for, regional_period, regional_periods


class RegionalPeriod(unittest.TestCase):
    def test_no_roman_period_in_ireland_or_man(self):
        self.assertEqual(regional_period(period_for(450 - 100), "Republic of Ireland"), "Iron Age")
        self.assertEqual(regional_period(period_for(200), "Isle of Man"), "Iron Age")
        self.assertEqual(regional_period(period_for(200), "Wales"), "Roman Britain")
        self.assertEqual(regional_period(period_for(800), "Northern Ireland"), "Early Medieval")

    def test_sweep_of_rows_dated_later(self):
        conn = sqlite3.connect(":memory:")
        for t in ("buildings", "places"):
            conn.execute(f"CREATE TABLE {t} (id TEXT, nation TEXT, period TEXT)")
            conn.executemany(f"INSERT INTO {t} VALUES (?, ?, ?)", [
                ("a", "Republic of Ireland", "Roman Britain"), ("b", "Wales", "Roman Britain"),
                ("c", "Isle of Man", "Early Medieval"), ("d", None, "Roman Britain")])
        self.assertEqual(regional_periods(conn), 2)
        self.assertEqual(dict(conn.execute("SELECT id, period FROM places")),
                         {"a": "Iron Age", "b": "Roman Britain", "c": "Early Medieval", "d": "Roman Britain"})


if __name__ == "__main__":
    unittest.main()
