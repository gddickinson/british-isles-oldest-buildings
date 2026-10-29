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
    c.execute("ALTER TABLE buildings ADD COLUMN plan_image")
    c.executemany("UPDATE buildings SET plan_image = ? WHERE id = ?", [("Plan b1.png", "b1"), ("", "b2"), ("Plan b5.png", "b5"), ("Plan b6.jpg", "b6")])
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

    def test_plans_of_real_examples(self):
        # BT6b: records with a Commons plan (an empty name is none), oldest first; the main type's own first
        self.assertEqual([(p["id"], p["plan"]) for p in type_pages.plans(conn(), "castle")],
                         [("b5", "Plan b5.png"), ("b1", "Plan b1.png")])
        self.assertEqual([p["id"] for p in type_pages.type_page(conn(), "town-hall", DATA, MDATA)["plans"]], ["b6", "b5"])
        # begun too early for the type: last (castles from 1050; b3 is dated 500 BC)
        c = conn()
        c.execute("UPDATE buildings SET plan_image = 'Plan b3.png' WHERE id = 'b3'")
        with mock.patch.object(type_pages.type_stats, "early_ok", return_value={}):
            self.assertEqual([p["id"] for p in type_pages.plans(c, "castle", DATA["types"][0])], ["b5", "b1", "b3"])
        self.assertEqual(type_pages.type_page(conn(), "donjon", DATA, MDATA)["plans"], [])

    def test_plans_of_places(self):
        # BT6c2a: places with a plan (bidb.place_plans) after the catalogue records, with what the page shows of them
        c = conn()
        c.execute("CREATE TABLE place_plans (place_id, file, via)")
        c.executemany("INSERT INTO place_plans VALUES (?,?,?)", [("p1", "Plan p1.svg", "wikidata"),
                                                                  ("p2", "Plan p2.jpg", "commons category")])
        got = type_pages.plans(c, "castle")
        self.assertEqual([(p["id"], p["source"]) for p in got],
                         [("b5", "building"), ("b1", "building"), ("p1", "place"), ("p2", "place")])
        self.assertEqual((got[2]["name"], got[2]["year"], got[2]["nation"], got[2]["plan"]),
                         ("Castle mound", 1052, "Scotland", "Plan p1.svg"))

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
