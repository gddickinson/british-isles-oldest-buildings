"""Bus stops and ferry terminals near a record (bidb.naptan). .venv/bin/python -m unittest discover tests"""
import sqlite3
import unittest

from bidb import naptan


class Near(unittest.TestCase):
    def test_nearest_stops_one_per_name(self):
        conn = sqlite3.connect(":memory:")
        conn.executescript(naptan.SCHEMA)
        conn.executemany("INSERT INTO stops VALUES (?, ?, ?, ?, ?, ?)", [
            ("1", "High Street", "Town", "bus", 51.5001, -0.1000),
            ("2", "High Street", "Town", "bus", 51.5002, -0.1001),     # the other side of the road
            ("3", "Church Lane", "Town", "bus", 51.5040, -0.1000),
            ("4", "Far Away", "Town", "bus", 51.6, -0.1),
            ("5", "Town Pier", "Town", "ferry", 51.55, -0.1)])
        got = naptan.near(conn, 51.5, -0.1)
        self.assertEqual([s["name"] for s in got["bus"]], ["High Street", "Church Lane"])
        self.assertEqual(got["ferry"][0]["name"], "Town Pier")
        self.assertEqual(naptan.near(sqlite3.connect(":memory:"), 51.5, -0.1), {"bus": [], "ferry": []})


if __name__ == "__main__":
    unittest.main()
