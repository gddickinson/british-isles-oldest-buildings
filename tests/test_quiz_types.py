"""Building types in the quiz pool (app.quiz_api.types, BT7): isles types with a first date, photographed records
by their main type."""
import sqlite3
import unittest

from app.quiz_api import types
from tests.test_type_pages import DATA, conn


class QuizTypesTest(unittest.TestCase):
    def setUp(self):
        self.c = conn()
        self.c.row_factory = sqlite3.Row
        self.c.executemany("UPDATE buildings SET image_thumb = ? WHERE id = ?",
                           [("t1.jpg", "b1"), ("t2.jpg", "b2"), ("t5.jpg", "b5"), ("t6.jpg", "b6")])

    def test_kinds_leave_out_types_abroad(self):
        kinds = types(self.c, data=DATA)["kinds"]
        self.assertEqual([k["id"] for k in kinds], ["castle", "town-hall", "keep"])
        self.assertEqual(kinds[0]["year"], 1050)

    def test_photos_by_main_type_and_capped(self):
        photos = types(self.c, per_type=2, data=DATA)["photos"]
        by = {}
        for p in photos:
            by.setdefault(p["type_id"], []).append(p["id"])
        self.assertEqual(len(by["castle"]), 2)                  # b1, b2, b5 are castles: two kept
        self.assertEqual(by["town-hall"], ["b6"])               # b5 is a town hall only as a secondary type
        self.assertTrue(all(p["image_thumb"] for p in photos))


if __name__ == "__main__":
    unittest.main()
