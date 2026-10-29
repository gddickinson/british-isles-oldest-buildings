"""Plans of typed places (bidb.place_plans, BT6c2a)."""
import sqlite3
import unittest
from unittest import mock

from bidb import place_plans


def conn():
    c = sqlite3.connect(":memory:")
    c.execute("CREATE TABLE buildings (id, plan_image)")
    c.execute("CREATE TABLE places (id, name, wikidata_id, building_id, wikipedia_title, year_start)")
    c.execute("CREATE TABLE type_map (entity_id, source, type_id, via, label, is_primary)")
    c.executemany("INSERT INTO buildings VALUES (?,?)", [("Q1", "Plan.png"), ("Q9", None)])
    c.executemany("INSERT INTO places VALUES (?,?,?,?,?,?)", [
        ("p1", "Fort A", "Q11", None, "Fort A", 1860),
        ("p2", "Fort B", "Q12", "", None, 1850),
        ("p3", "Fort C", "Q13", None, "Fort C", 1700),
        ("p4", "Catalogue fort", "Q9", None, None, 1500),        # a catalogue record's item
        ("p5", "Linked fort", "Q15", "Q1", None, 1500),          # linked to a catalogue record
        ("p6", "No item", None, None, None, 1500)])
    c.executemany("INSERT INTO type_map VALUES (?,?,?,?,?,?)",
                  [(p, "place", "fort", "x", "x", 1) for p in ("p1", "p2", "p3", "p4", "p5", "p6")]
                  + [("Q1", "building", "castle", "x", "x", 1)])
    return c


class TestPlacePlans(unittest.TestCase):
    def test_targets_leave_out_catalogue_records(self):
        self.assertEqual(place_plans.targets(conn()), {"Q11": ["p1"], "Q12": ["p2"], "Q13": ["p3"]})

    def test_queue_article_first_then_oldest(self):
        q = place_plans.search_queue(conn(), set())
        self.assertEqual([p for p, _, _ in q["fort"]], ["p3", "p1", "p2"])
        self.assertNotIn("castle", q)                   # no places
        with mock.patch.object(place_plans, "WANT", 1):  # one plan found already: the type is not searched
            self.assertEqual(place_plans.search_queue(conn(), {"p1"}), {})

    def test_maps_and_sections_are_no_plans(self):
        with mock.patch.object(place_plans.footprints, "plans", return_value={
                "Q11": "Ham Hill Somerset Map.jpg", "Q12": "Section of new Eddystone Lighthouse.jpg",
                "Q13": "Fort Gomer Plan.jpg"}), \
                mock.patch.object(place_plans.commons_plans, "plans", return_value={}):
            self.assertEqual(place_plans.find(["Q11", "Q12", "Q13"], log=lambda *a: None),
                             {"Q13": ("Fort Gomer Plan.jpg", "wikidata")})

    def test_report(self):
        c = conn()
        place_plans.write(c, [("p1", "Plan p1.png", "wikidata"), ("p3", "Plan p3.png", "commons")])
        self.assertEqual(place_plans.report(c), [("fort", 0, 2), ("castle", 1, 0)])


if __name__ == "__main__":
    unittest.main()
