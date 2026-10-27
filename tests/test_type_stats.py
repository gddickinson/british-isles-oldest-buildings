import sqlite3
import unittest

from bidb import type_stats

TYPES = {"types": [
    {"id": "castle", "name": "Castle", "family": "Castles", "period": {"from": 1050, "to": 1500}},
    {"id": "town-hall", "name": "Town hall", "period": {"from": 1120, "ongoing": True}},
    {"id": "empty", "name": "Empty type", "period": {"from": 1600, "to": 1700}},
    {"id": "abroad", "name": "Abroad", "abroad": True, "period": {"from": 1500, "to": 1600}},
]}
BUILDINGS = [  # id, name, year, date_text, lat, lon, nation, status, date_confidence
    ("b1", "Old Castle", 1080, "1080", 51.0, -1.0, "England", "Standing", "Recorded"),
    ("b2", "Gone Castle", 1060, "1060", 52.0, -1.0, "England", "Demolished / destroyed", "Recorded"),
    ("b3", "Hillfort Castle", -500, "Iron Age", 53.0, -2.0, "Wales", "Ruin", "Recorded"),
    ("b4", "Guessed Castle", 1055, "c. 1055", 54.0, -2.0, "Scotland", "Standing", "Estimate (building type)"),
    ("b5", "Castle used as town hall", 1066, "1066", 51.5, -0.5, "England", "Standing", "Recorded"),
    ("b6", "Guildhall", 1206, "1206", 50.4, -3.7, "England", "Standing", "Recorded"),
]
PLACES = [("p1", "Castle mound", 1052, None, 55.0, -3.0, "Scotland", "scheduled"),
          ("p2", "Undated castle", None, None, None, None, "Wales", "scheduled")]
MAP = [("b1", "building", "castle", "type", "x", 1), ("b2", "building", "castle", "type", "x", 1),
       ("b3", "building", "castle", "type", "x", 1), ("b4", "building", "castle", "type", "x", 1),
       ("b5", "building", "castle", "type", "x", 1), ("b5", "building", "town-hall", "fish", "x", 0),
       ("b6", "building", "town-hall", "fish", "x", 1),
       ("p1", "place", "castle", "alias", "x", 1), ("p2", "place", "castle", "alias", "x", 1)]


def conn():
    c = sqlite3.connect(":memory:")
    c.execute("CREATE TABLE buildings (id, name, year_start, date_text, lat, lon, nation, county, status, "
              "date_confidence, image_thumb)")
    c.execute("CREATE TABLE places (id, name, year_start, date_text, lat, lon, nation, county, image_thumb, kind, "
              "kind_group)")
    c.execute("CREATE TABLE type_map (entity_id, source, type_id, via, label, is_primary)")
    c.executemany("INSERT INTO buildings VALUES (?,?,?,?,?,?,?,NULL,?,?,NULL)", BUILDINGS)
    c.executemany("INSERT INTO places VALUES (?,?,?,?,?,?,?,NULL,NULL,?,NULL)", PLACES)
    c.executemany("INSERT INTO type_map VALUES (?,?,?,?,?,?)", MAP)
    return c


class TestTypeStats(unittest.TestCase):
    def test_summary(self):
        rows = {r["id"]: r for r in type_stats.summary(conn(), TYPES)}
        self.assertNotIn("abroad", rows)
        castle = rows["castle"]
        self.assertEqual((castle["buildings"], castle["places"], castle["dated"], castle["too_early"]), (5, 2, 6, 1))
        # not demolished, not a type estimate, not too early: b5 (1066) before b1 (1080)
        self.assertEqual(castle["earliest"]["id"], "b5")
        self.assertEqual(rows["empty"]["earliest"], None)
        # a castle later used as a town hall is no early town hall: the primary example wins
        self.assertEqual(rows["town-hall"]["earliest"]["id"], "b6")

    def test_detail(self):
        d = type_stats.detail(conn(), "castle", TYPES)
        self.assertEqual([e["id"] for e in d["examples"]], ["b3", "p1", "b4", "b2", "b5", "b1"])
        self.assertEqual([e["id"] for e in d["examples"] if e["too_early"]], ["b3"])
        self.assertEqual(d["examples"][3]["surviving"], False)
        self.assertEqual(d["examples"][1]["surviving"], None)          # places record no status
        self.assertEqual(d["by_nation"]["England"], 3)
        self.assertEqual(d["by_century"], {-500: 1, 1000: 5})
        self.assertEqual(len(d["points"]), 6)
        self.assertIsNone(type_stats.detail(conn(), "nope", TYPES))

    def test_early_ok_and_for_entity(self):
        t = TYPES["types"][0]
        row = {"id": "b3", "year": -500}
        self.assertTrue(type_stats.too_early(row, t))
        self.assertFalse(type_stats.too_early(row, t, {"b3": "reviewed"}))
        self.assertFalse(type_stats.too_early({"id": "x", "year": 951}, t))     # within EARLY years
        period = {"id": "x", "year": -2000, "date_text": "Prehistoric (register period)"}
        self.assertFalse(type_stats.too_early(period, t))        # the year only stands for the period

    def test_register_period_is_an_estimate(self):
        row = {"date_confidence": None, "date_text": "Medieval (register period)"}
        self.assertTrue(type_stats.estimated(row))
        self.assertFalse(type_stats.estimated(dict(row, date_text="1250")))
        t = {"id": "castle", "period": {"from": 1066}}
        rows = [{"id": "p1", "source": "place", "primary": 1, "year": 1250, "name": "A",
                 "date_text": "Medieval (register period)", "status": None, "date_confidence": None},
                {"id": "p2", "source": "place", "primary": 1, "year": 1300, "name": "B",
                 "date_text": "1300", "status": None, "date_confidence": None}]
        self.assertEqual(type_stats.earliest(rows, t)["id"], "p2")
        self.assertEqual([(x["id"], x["primary"]) for x in type_stats.for_entity(conn(), "b5", TYPES)],
                         [("castle", True), ("town-hall", False)])

    def test_structure_places_rank_with_records(self):
        t = {"id": "railway", "period": {"from": 1825}}
        line = {"source": "place", "primary": 1, "status": None, "date_confidence": None,
                "kind_group": "Infrastructure & utilities"}
        rows = [{"id": "b1", "source": "building", "primary": 1, "year": 1894, "name": "City line",
                 "date_text": "1894", "status": "Standing", "date_confidence": "Recorded", "kind_group": None},
                dict(line, id="p1", year=1825, name="S&D", date_text="opened 27 September 1825"),
                dict(line, id="p2", year=1830, name="L&M", date_text="1830")]
        self.assertTrue(type_stats.structure_place(rows[1]))
        self.assertEqual(type_stats.earliest(rows, t)["id"], "p1")
        self.assertEqual(type_stats.earliest(rows[:2], t)["id"], "b1")      # not mostly places
        hospital = [rows[0]] + [dict(r, kind_group="Public institutions") for r in rows[1:]]
        self.assertEqual(type_stats.earliest(hospital, t)["id"], "b1")      # a founding date, not the building's
        century = [rows[0]] + [dict(r, date_text="19th century") for r in rows[1:]]
        self.assertEqual(type_stats.earliest(century, t)["id"], "b1")


if __name__ == "__main__":
    unittest.main()
