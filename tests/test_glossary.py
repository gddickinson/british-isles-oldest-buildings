"""Glossary page data (bidb.glossary): curated terms, FISH scope notes, periods, building types."""
import unittest
from unittest import mock

from bidb import glossary

FISH = {"70096": {"note": "Circular enclosure with a bank. Use more specific type where known."},
        "68841": {"note": "An earthen mound for a castle tower."}}
DATA = {"groups": ["Archaeology", "In this app", "Periods", "Building types"],
        "terms": [{"term": "Henge", "group": "Archaeology", "fish": "70096", "see": ["Cut-off year"]},
                  {"term": "Cut-off year", "group": "In this app", "text": "Begun before 1500."},
                  {"term": "Regional period", "group": "In this app", "text": "Iron Age in Ireland."},
                  {"term": "Gone", "group": "Archaeology", "fish": "99999"}]}


class GlossaryTest(unittest.TestCase):
    def entries(self):
        with mock.patch.object(glossary, "load", return_value=DATA), \
                mock.patch.object(glossary, "_fish", return_value=FISH), \
                mock.patch.object(glossary, "building_types", return_value=[]):
            return glossary.entries()["terms"]

    def test_fish_note_without_indexing_advice(self):
        henge = next(t for t in self.entries() if t["term"] == "Henge")
        self.assertEqual(henge["text"], "Circular enclosure with a bank.")
        self.assertIn("/70096.html", henge["source"]["url"])

    def test_missing_fish_concept_left_out_and_periods_added(self):
        names = [t["term"] for t in self.entries()]
        self.assertNotIn("Gone", names)
        self.assertIn("Roman Britain", names)
        self.assertEqual(names, sorted(names, key=str.lower))

    def test_problems(self):
        terms = self.entries()
        self.assertEqual(glossary.problems(DATA, terms), [])
        bad = {"groups": DATA["groups"], "terms": DATA["terms"] + [{"term": "X", "group": "Nope", "see": ["Y"]}]}
        found = glossary.problems(bad, terms + [{"term": "X", "see": ["Y"]}])
        self.assertIn("X: no text or fish", found)
        self.assertIn("X: group 'Nope'", found)
        self.assertIn("X: see 'Y' unknown", found)

    def test_curated_file(self):
        data = glossary.load()
        self.assertEqual(glossary.problems(data, self.entries_real()), [])

    def entries_real(self):
        return glossary.entries()["terms"]


if __name__ == "__main__":
    unittest.main()
