"""Domesday marking and paintings of a place (no network)."""
import sqlite3
import unittest
from unittest import mock

from bidb import domesday


class DomesdayMarks(unittest.TestCase):
    def setUp(self):
        self.conn = sqlite3.connect(":memory:")
        self.conn.executescript("""
            CREATE TABLE buildings (id, wikidata_id); CREATE TABLE places (id, wikidata_id);
            CREATE TABLE pron_towns (record_id, town_id, town);
            INSERT INTO buildings VALUES ('Q1', 'Q1'), ('Q2', 'Q2'), ('Q3', 'Q3');
            INSERT INTO places VALUES ('mm-9', NULL), ('Q4', 'Q4');
            INSERT INTO pron_towns VALUES ('Q2', 'Q100', 'Coventry'), ('Q1', 'Q100', 'Coventry'), ('Q4', 'Q200', 'Nowhere');
        """)

    def test_marks(self):
        dom = {"Q1": ("Axminster", "axminster"), "Q100": ("Coventry", "coventry")}
        with mock.patch.object(domesday, "connect", return_value=self.conn), \
                mock.patch.object(domesday, "settlements", return_value=dom):
            domesday.run(log=lambda *_: None)
        self.assertEqual(domesday.for_record(self.conn, "Q1")["itself"], 1)          # itself wins over its town
        self.assertEqual(domesday.for_record(self.conn, "Q2")["settlement"], "Coventry")
        self.assertIsNone(domesday.for_record(self.conn, "Q3"))
        self.assertIsNone(domesday.for_record(self.conn, "Q4"))


if __name__ == "__main__":
    unittest.main()


class Depictions(unittest.TestCase):
    def test_distinct_drops_repeated_impressions(self):
        from bidb.depictions import distinct
        arts = [["Q1", "Caerlaverock Castle", "Edward Goodall", 1834, None, "a.jpg", ""],
                ["Q2", "Caerlaverock Castle", "Edward Goodall", 1834, None, "b.jpg", ""],
                ["Q3", "Edward Goodall - Caerlaverock Castle", "Edward Goodall", 1834, None, "c.jpg", ""],
                ["Q4", "Caerlaverock Castle", "Edward Goodall", None, None, "d.jpg", ""]]
        self.assertEqual([a[0] for a in distinct(arts)], ["Q1", "Q4"])
