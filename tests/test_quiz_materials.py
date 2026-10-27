"""Materials and oldest things in the quiz pool (app.quiz_api.materials, things): walls before roofs, reliable sources
only, the related materials that must never be a wrong answer."""
import sqlite3
import unittest

from app.quiz_api import firsts, materials, things

DATA = {"materials": [{"id": "sandstone", "name": "Sandstone", "group": "Stone", "kind": "material"},
                      {"id": "red-sandstone", "name": "Red sandstone", "group": "Stone", "kind": "material"},
                      {"id": "slate", "name": "Slate", "group": "Roofs", "kind": "material"},
                      {"id": "brick", "name": "Brick", "group": "Brick and tile", "kind": "material"},
                      {"id": "sash-window", "name": "Sash window", "group": "Glass", "kind": "technique"}],
        "links": [{"from": "sandstone", "to": "red-sandstone"}]}


def conn():
    c = sqlite3.connect(":memory:")
    c.row_factory = sqlite3.Row
    c.execute("CREATE TABLE buildings (id, name, image_thumb, nation)")
    c.execute("CREATE TABLE material_map (entity_id, source, material_id, via, label, place, evidence)")
    c.executemany("INSERT INTO buildings VALUES (?,?,?,?)", [("b1", "Kirk", "k.jpg", "Scotland"),
                  ("b2", "Mill", "m.jpg", "England"), ("b3", "No photo", None, "Wales")])
    c.executemany("INSERT INTO material_map VALUES (?,?,?,?,?,?,?)", [
        ("b1", "building", "slate", "register", "", "", "slate roof"),
        ("b1", "building", "sandstone", "register", "", "", "sandstone rubble"),
        ("b1", "building", "sash-window", "register", "", "", "12-pane sashes"),
        ("b2", "building", "brick", "wikipedia", "", "", "a brick mill"),          # Wikipedia only: not asked
        ("b3", "building", "brick", "register", "", "", "brick")])                 # no photo
    return c


class QuizMaterialsTest(unittest.TestCase):
    def test_walls_first_and_reliable_sources(self):
        m = materials(conn(), data=DATA)
        self.assertEqual([(p["id"], p["material"]) for p in m["photos"]], [("b1", "sandstone")])
        self.assertEqual(m["photos"][0]["all"], ["sandstone", "sash-window", "slate"])
        self.assertNotIn("sash-window", [k["id"] for k in m["kinds"]])      # windows are not what it is built of
        rel = {k["id"]: k["related"] for k in m["kinds"]}
        self.assertEqual(rel["sandstone"], ["red-sandstone"])
        self.assertEqual(rel["red-sandstone"], ["sandstone"])

    def test_oldest_things_in_the_pool(self):
        ts = things()
        self.assertGreaterEqual(len(ts), 100)
        self.assertTrue(all(isinstance(t["year"], int) and t["claim"] and t["theme_title"] for t in ts))
        fs = [f for f in firsts() if f.get("page") == "things"]
        self.assertTrue(fs and all(f["year"] >= 43 for f in fs))


if __name__ == "__main__":
    unittest.main()
