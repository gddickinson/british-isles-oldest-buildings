"""Data of the page /types (bidb.type_pages, BT4a, BT3c1): the tree, one type, one material, types here."""
import unittest
from unittest import mock

from bidb import type_pages
from tests.test_type_stats import conn as stats_conn

DATA = {"types": [
    {"id": "castle", "name": "Castle", "domain": "Defence", "family": "Castles", "fish": None,
     "period": {"from": 1050, "to": 1500}, "sources": []},
    {"id": "town-hall", "name": "Town hall", "domain": "Civic", "family": "Halls", "fish": None,
     "period": {"from": 1120, "ongoing": True}},
    {"id": "keep", "name": "Keep", "domain": "Defence", "family": "Castles", "fish": None,
     "period": {"from": 1070, "to": 1300}},
    {"id": "donjon", "name": "Donjon (France)", "domain": "Defence", "family": "Abroad", "fish": None,
     "abroad": True, "period": {"from": 950, "to": 1200}},
], "links": [
    {"id": "donjon>keep", "from": "donjon", "to": "keep", "kind": "descent", "confidence": "documented",
     "claim": "Keeps came from the donjons.", "sources": [{"title": "S", "url": "u", "quote": "q"}]},
    {"id": "castle>keep", "from": "castle", "to": "keep", "kind": "variant", "confidence": "probable",
     "claim": "A keep is a form of castle.", "sources": []},
]}
MDATA = {"materials": [
    {"id": "ashlar", "name": "Ashlar", "group": "Stone", "kind": "material", "fish": None,
     "period": {"from": 1000, "ongoing": True}, "types": ["castle", "gone-type"], "sources": []},
    {"id": "brick", "name": "Brick", "group": "Brick", "kind": "material", "fish": None,
     "period": {"from": 1220, "ongoing": True}, "sources": []},
], "links": [{"id": "ashlar>brick", "from": "ashlar", "to": "brick", "kind": "replacement",
              "confidence": "disputed", "claim": "c", "sources": []}]}
MATS = [("b1", "building", "ashlar", "register", "ashlar", None, "Built of ashlar."),
        ("b5", "building", "ashlar", "wikipedia", "ashlar", None, "Ashlar walls."),
        ("b5", "building", "brick", "wikipedia", "brick", None, "A brick front."),
        ("b6", "building", "brick", "wikidata", "brick", None, None)]


def conn():
    c = stats_conn()
    c.execute("CREATE TABLE material_map (entity_id, source, material_id, via, label, place, evidence)")
    c.executemany("INSERT INTO material_map VALUES (?,?,?,?,?,?,?)", MATS)
    return c


class TestTypePages(unittest.TestCase):
    def setUp(self):
        p = mock.patch.object(type_pages, "_definition", return_value=None)
        p.start()
        self.addCleanup(p.stop)

    def test_tree_keeps_file_order_and_abroad_types(self):
        t = type_pages.tree(conn(), DATA)
        self.assertEqual([d for d, _ in t["tree"]], ["Defence", "Civic"])
        self.assertEqual(t["tree"][0][1][0], ("Castles", ["castle", "keep"]))
        by = {x["id"]: x for x in t["types"]}
        self.assertTrue(by["donjon"]["abroad"])
        self.assertEqual(by["castle"]["buildings"], 5)
        self.assertEqual(by["castle"]["earliest"]["id"], "b5")
        self.assertNotIn("sources", t["links"][0])

    def test_type_page_links_and_materials(self):
        d = type_pages.type_page(conn(), "keep", DATA, MDATA)
        self.assertEqual({(k["other"], k["direction"]) for k in d["links"]}, {("donjon", "in"), ("castle", "in")})
        self.assertEqual(d["links"][0]["other_name"], "Donjon (France)")
        castle = type_pages.type_page(conn(), "castle", DATA, MDATA)
        self.assertEqual([m["id"] for m in castle["materials"]], ["ashlar"])
        # materials found in the castle records b1 and b5: ashlar 2, brick 1
        self.assertEqual([(m["id"], m["count"]) for m in castle["record_materials"]], [("ashlar", 2), ("brick", 1)])
        self.assertIsNone(type_pages.type_page(conn(), "nothing", DATA, MDATA))

    def test_abroad_type_has_no_examples(self):
        d = type_pages.type_page(conn(), "donjon", DATA, MDATA)
        self.assertTrue(d["abroad"])
        self.assertEqual(d["record_materials"], [])
        self.assertEqual(d["links"][0]["direction"], "out")

    def test_material_page(self):
        d = type_pages.material_page(conn(), "brick", DATA, MDATA)
        self.assertEqual(d["count"], 2)
        self.assertEqual(d["links"][0]["other_name"], "Ashlar")
        # main types of its records: b5 castle (primary), b6 town hall (primary)
        self.assertEqual(sorted(t["id"] for t in d["record_types"]), ["castle", "town-hall"])
        ashlar = type_pages.material_page(conn(), "ashlar", DATA, MDATA)
        self.assertEqual([t["id"] for t in ashlar["types"]], ["castle"])      # unknown type ids left out
        self.assertIsNone(type_pages.material_page(conn(), "nothing", DATA, MDATA))

    def test_materials_groups_in_order(self):
        m = type_pages.materials(conn(), MDATA)
        self.assertEqual(m["groups"][0][1], ["ashlar"])
        self.assertEqual({x["id"]: x["buildings"] for x in m["materials"]}, {"ashlar": 2, "brick": 2})

    def test_here(self):
        h = type_pages.here(conn(), "b5", DATA, MDATA)
        self.assertEqual([t["id"] for t in h["types"]], ["castle", "town-hall"])
        self.assertEqual({m["id"] for m in h["materials"]}, {"ashlar", "brick"})


if __name__ == "__main__":
    unittest.main()
