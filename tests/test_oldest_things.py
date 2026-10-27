"""Oldest things (/things): the researched files are well formed, bad entries are caught, the page data is ordered."""
import unittest
from unittest import mock

from bidb import oldest_things as ot

GOOD = {"category": "Oldest recipe or cookery book", "name": "The Forme of Cury", "year": 1390, "age_text": "c. 1390",
        "claim": "one of the oldest English cookery books", "evidence": "Nine manuscripts survive.", "verdict": "open",
        "nation": "England", "where": {"name": "John Rylands Library", "role": "kept", "lat": 53.4805, "lon": -2.2486},
        "sources": [{"title": "The Forme of Cury", "kind": "reference", "url": "https://en.wikipedia.org/wiki/The_Forme_of_Cury",
                     "quote": "an extensive 14th-century collection of medieval English recipes"}]}


class Validate(unittest.TestCase):
    def test_good(self):
        self.assertEqual(ot.validate("food", [GOOD]), [])

    def test_bad(self):
        bad = {**GOOD, "category": "Oldest bicycle", "year": "1390", "verdict": "maybe", "nation": "France",
               "where": {"name": "Paris", "role": "kept", "lat": 48.85, "lon": 2.35},
               "sources": [{"title": "x", "kind": "blog", "url": "https://example.org"}]}
        problems = " | ".join(ot.validate("food", [bad, GOOD, GOOD]))
        for word in ("category", "year", "verdict", "nation", "where", "source", "duplicate"):
            self.assertIn(word, problems)

    def test_files(self):
        self.assertEqual(ot.problems(), [])
        for t in ot.THEMES:
            for e in ot.entries(t):
                self.assertTrue(e["sources"], e["name"])


class Index(unittest.TestCase):
    def test_order_and_checks(self):
        later = {**GOOD, "name": "A later cookbook", "year": 1500}
        with mock.patch.object(ot, "entries", lambda t, f=None: [later, GOOD] if t == "food" else []), \
                mock.patch.object(ot, "checks", lambda: {"things-food-the-forme-of-cury": {"sources": ["quote-found"]}}):
            data = ot.index()
            record = ot.claims("food")[0]["record"]
        food = next(t for t in data["themes"] if t["id"] == "food")
        rows = food["categories"][0]["entries"]
        self.assertEqual([r["name"] for r in rows], ["The Forme of Cury", "A later cookbook"])
        self.assertEqual(rows[0]["sources"][0]["check"], "quote-found")
        self.assertIsNone(rows[1]["sources"][0]["check"])
        self.assertEqual(data["count"], 2)
        self.assertEqual(record, "thing:food-a-later-cookbook")


if __name__ == "__main__":
    unittest.main()
