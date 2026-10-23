import unittest

from bidb import trade_sources

GOOD = {"short": "X", "publisher": "P", "citation": "C", "licence": "OGL v3.0", "licence_quote": "q",
        "url": "https://x", "checked": "2026-10-23", "use": "u", "verdict": "use", "for": ["C5"]}


class TradeSourcesTest(unittest.TestCase):
    def test_good(self):
        self.assertEqual(trade_sources.check({"a": GOOD}), [])

    def test_problems(self):
        bad = trade_sources.check({"a": {**GOOD, "licence_quote": ""}, "b": {**GOOD, "verdict": "ask"},
                                   "c": {**GOOD, "for": ["C9"]}})
        self.assertEqual(len(bad), 3)

    def test_curated_file(self):
        if trade_sources.PATH.exists():
            self.assertEqual(trade_sources.check(trade_sources.load()), [])


if __name__ == "__main__":
    unittest.main()
