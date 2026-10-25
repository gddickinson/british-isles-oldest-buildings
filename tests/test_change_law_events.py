"""Laws and institutions as dated events (roadmap C7): each cited with a quote and tagged with its trade (read by the
trade stories, C8)."""
import json
import unittest

from bidb.change_series import SRC

TRADES = {"wool", "trade", "work", "tea", "banking", "slavery", "farming", "cotton"}


class LawEvents(unittest.TestCase):
    def setUp(self):
        self.ev = [e for e in json.loads((SRC / "events.json").read_text()) if e.get("topic") == "law"]

    def test_cited_with_quotes(self):
        self.assertGreaterEqual(len(self.ev), 25)
        for e in self.ev:
            self.assertIn('"', e["citation"], e["title"])
            self.assertIn("https://", e["citation"], e["title"])
            self.assertLessEqual(e["year"], e["end"])

    def test_trades(self):
        self.assertEqual({e["trade"] for e in self.ev} - TRADES, set())
        self.assertGreaterEqual(sum(e["trade"] == "slavery" for e in self.ev), 4)


if __name__ == "__main__":
    unittest.main()
