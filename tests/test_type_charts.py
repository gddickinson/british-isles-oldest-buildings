"""Charts of building types through time (bidb.type_charts, BT5): spread by county, lines of descent, materials by
century."""
import unittest

from bidb import type_charts
from tests.test_type_pages import DATA, MDATA, conn as pages_conn


def conn():
    c = pages_conn()
    c.executemany("UPDATE buildings SET county = ? WHERE id = ?",
                  [("Kent", "b1"), ("Kent", "b5"), ("Fife", "b4"), ("Gwent", "b3"), ("Kent", "b2")])
    return c


LINES = {"types": [
    {"id": "a", "name": "A", "period": {"from": 500}}, {"id": "b", "name": "B", "period": {"from": 900}},
    {"id": "c", "name": "C", "period": {"from": 1200}}, {"id": "d", "name": "D", "period": {"from": 1600}},
    {"id": "e", "name": "E", "period": {"from": 1300}}, {"id": "f", "name": "F", "period": {"from": 1400}},
], "links": [
    {"from": "a", "to": "b", "kind": "descent", "confidence": "documented"},
    {"from": "b", "to": "c", "kind": "descent", "confidence": "probable"},
    {"from": "c", "to": "d", "kind": "replacement", "confidence": "documented"},
    {"from": "d", "to": "b", "kind": "revival", "confidence": "documented"},       # a loop back: never twice
    {"from": "c", "to": "e", "kind": "variant", "confidence": "documented"},       # a form, not an heir
    {"from": "c", "to": "f", "kind": "influence", "confidence": "documented"},
]}


class TestTypeCharts(unittest.TestCase):
    def test_spread_first_example_per_county(self):
        rows = type_charts.spread(conn(), "castle", DATA)
        # Kent: b5 (1066) before b1 (1080); b2 demolished, b4 estimated, b3 too early: left out
        self.assertEqual([(r["county"], r["id"]) for r in rows], [("Kent", "b5")])
        self.assertIsNone(type_charts.spread(conn(), "nope", DATA))

    def test_chains_before_and_after(self):
        c = type_charts.chains("c", LINES)
        # back from C: A→B→C and D→B→C (revival), oldest first; the step next to C carries the B→C link
        self.assertEqual([[s["id"] for s in p] for p in c["before"]], [["a", "b"], ["d", "b"]])
        self.assertEqual(c["before"][0][-1]["confidence"], "probable")
        self.assertEqual(c["before"][0][0]["kind"], "descent")
        after = [[s["id"] for s in p] for p in c["after"]]
        self.assertEqual(after, [["d", "b"]])           # revival back to B, then stops (B→C would repeat C)
        self.assertNotIn("e", str(after))               # variants are not what came next
        self.assertIsNone(type_charts.chains("zz", LINES))

    def test_form_takes_its_parent_lines(self):
        c = type_charts.chains("e", LINES)
        self.assertEqual((c["before"], c["after"]), ([], []))
        self.assertEqual(c["form_of"]["id"], "c")
        self.assertTrue(c["form_of"]["before"] and c["form_of"]["after"])

    def test_material_centuries(self):
        d = type_charts.centuries(pages_conn(), MDATA)
        self.assertEqual(d["groups"], [["Stone", ["ashlar"]], ["Brick", ["brick"]]])
        self.assertEqual(d["first"]["brick"], 1220)
        self.assertIn("ashlar", d["counts"])


if __name__ == "__main__":
    unittest.main()
