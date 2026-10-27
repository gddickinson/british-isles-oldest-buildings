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


class Firsts(unittest.TestCase):
    """C9: "Which came first?" questions from the innovations and the trade laws."""

    def test_pool(self):
        from app.quiz_api import firsts
        f = firsts()
        self.assertGreaterEqual(sum(x["what"] == "Innovation" for x in f), 30)
        self.assertGreaterEqual(sum(x["what"] == "Law or institution" for x in f), 25)
        self.assertTrue(all(isinstance(x["year"], int) for x in f))


class Here(unittest.TestCase):
    def test_trade_and_innovation_here(self):
        from bidb.db import connect
        conn = connect()
        if not conn.execute("SELECT 1 FROM sqlite_master WHERE name = 'places'").fetchone():
            self.skipTest("needs the database (python -m bidb.bundle fetch, or a build)")
        h = ts.here(conn)
        mill = h.get("Q2566525")                  # Cromford Mill: Arkwright's mill, in the cotton story
        self.assertIsNotNone(mill)
        self.assertIn(["cotton", "Cotton"], mill["trades"])
        self.assertTrue(mill["made"])


if __name__ == "__main__":
    unittest.main()
