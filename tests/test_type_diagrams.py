"""Labelled diagrams of building types (bidb.type_diagrams, BT6c): labels only from the quoted sources."""
import unittest

from bidb import type_diagrams as td

DATA = {"types": [
    {"id": "hut", "name": "Hut", "plan": "one round room",
     "sources": [{"title": "A", "url": "a", "quote": "A round hut with a central hearth (the fire).", "about": ["plan"]},
                 {"title": "B", "url": "b", "quote": "Walls of wattle-and-daub.", "about": ["structure"]},
                 {"title": "C", "url": "c", "quote": "Built in 1200 with a porch.", "about": ["period"]}]},
], "links": []}


def diagram(**kw):
    d = {"id": "hut-plan", "type": "hut", "view": "plan", "title": "Hut: plan", "size": [100, 100],
         "shapes": [["circle", 50, 50, 40, "room"], ["rect", 10, 10, 5, 5, "door", 2], ["line", [0, 0, 100, 100], "dash"],
                    ["path", "M10 90 Q50 60 90 90", "ground"]],
         "labels": [{"t": "Central hearth", "at": [50, 50], "to": [50, 55]},
                    {"t": "wattle and daub", "at": [50, 90], "to": [[10, 50], [90, 50]], "a": "start"},
                    {"t": "plan", "at": [90, 10]}]}
    d.update(kw)
    return d


class Diagrams(unittest.TestCase):
    def test_curated_files_valid(self):
        ds = td.load()
        self.assertGreaterEqual(len(ds), 20)
        self.assertEqual(td.validate(ds), [])

    def test_norm(self):
        self.assertEqual(td.norm("Cross-passage (usually) “30 m”"), "cross passage usually 30m")

    def test_valid_diagram(self):
        self.assertEqual(td.validate([diagram()], DATA), [])

    def test_label_must_be_quoted(self):
        probs = td.validate([diagram(labels=[{"t": "porch", "at": [5, 5]}, {"t": "fire pit", "at": [5, 5]}])], DATA)
        self.assertEqual(len(probs), 2)        # porch is only in a period source
        self.assertTrue(all("in no quote" in p for p in probs))

    def test_shapes_checked(self):
        probs = td.validate([diagram(shapes=[["circle", 95, 50, 20, "room"], ["rect", 1, 1, 2, 2, "lava"],
                                             ["hexagon", 1], ["path", "M0 0 <script>", "thin"],
                                             ["poly", [1, 2, 3], "room"]])], DATA)
        self.assertEqual(len(probs), 5)

    def test_labels_and_types_checked(self):
        probs = td.validate([diagram(labels=[{"t": "plan", "at": [150, 5]}]),
                             diagram(type="tower"), diagram(view="map")], DATA)
        self.assertIn("hut-plan: label 'plan' off the canvas", probs)
        self.assertIn("hut-plan: duplicate id", probs)
        self.assertIn("hut-plan: unknown type 'tower'", probs)
        self.assertIn("hut-plan: view 'map'", probs)

    def test_drawn_from(self):
        out = td.for_type("hut", DATA, [diagram()])
        self.assertEqual([s["title"] for s in out[0]["sources"]], ["A", "B"])
        self.assertEqual(td.for_type("none", DATA, [diagram()]), [])


if __name__ == "__main__":
    unittest.main()
