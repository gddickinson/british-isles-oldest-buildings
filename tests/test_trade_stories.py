"""Trade stories (roadmap C8): the stories file checks, words match whole words, a story brings its parts together."""
import unittest

from bidb import trade_stories as ts


class Stories(unittest.TestCase):
    def test_file_checks(self):
        self.assertEqual(ts.check(), [])
        self.assertEqual([s["id"] for s in ts.load()],
                         ["wool", "tea", "sugar", "cotton", "linen", "coal", "iron", "fishing", "drink", "banking"])

    def test_whole_words(self):
        rx = ts.pattern(["rum", "weav*"])
        self.assertTrue(rx.search("Rum warehouse") and rx.search("Weavers' Hall"))
        self.assertIsNone(rx.search("Drummond Street"))
        self.assertIsNone(ts.pattern(["iron"]).search("Ironbridge"))

    def test_events_and_innovations(self):
        cotton = next(s for s in ts.load() if s["id"] == "cotton")
        ev = ts.events(cotton)
        self.assertTrue(any(e.get("kind") == "innovation" for e in ev))
        self.assertEqual([e["year"] for e in ev], sorted(e["year"] for e in ev))

    def test_notes_quoted(self):
        for s in ts.load():
            self.assertTrue(s["notes"], s["id"])
            for n in s["notes"]:
                self.assertTrue(all(x["quote"] and x["url"].startswith("https://") for x in n["sources"]))


if __name__ == "__main__":
    unittest.main()
