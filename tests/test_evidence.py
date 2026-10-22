"""Research track: the evidence file is well formed and quotes match despite typography (no network)."""
import unittest

from bidb import evidence


class Evidence(unittest.TestCase):
    def test_file_is_valid(self):
        self.assertEqual(evidence.validate(evidence.load()), [])

    def test_quote_matching_ignores_typography(self):
        text = "Country House.  C.1508, for John Spencer, remodelled by Henry Holland 1789 . Ashlar…"
        self.assertTrue(evidence.quote_found("c.1508, for John Spencer, remodelled by Henry Holland 1789", text))
        self.assertTrue(evidence.quote_found("tower 1838–40", "Tower 1838-40"))
        self.assertFalse(evidence.quote_found("c.1608", text))

    def test_validate_reports_problems(self):
        bad = [{"id": "x", "record": "Q1", "field": "date", "claim": "c", "verdict": "maybe",
                "sources": [{"title": "t", "kind": "blog", "quote": "q"}]}]
        problems = evidence.validate(bad)
        self.assertTrue(any("verdict" in p for p in problems) and any("kind" in p for p in problems))
