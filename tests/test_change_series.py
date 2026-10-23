"""Change-over-time series: every series and event cites a source with a licence, and the data files read."""
import json
import unittest

from bidb import change_series as cs


class ChangeSeries(unittest.TestCase):
    def test_curated_files_pass_the_checks(self):
        sources = json.loads((cs.SRC / "sources.json").read_text())
        series = json.loads((cs.SRC / "series.json").read_text())
        events = json.loads((cs.SRC / "events.json").read_text())
        self.assertEqual(cs.check(sources, series, events), [])
        for s in series:
            pts = cs.read_points(cs.SRC / "data" / s["file"])
            self.assertTrue(pts, s["id"])
            self.assertEqual([p[0] for p in pts], sorted(p[0] for p in pts), s["id"])

    def test_check_finds_missing_sources_and_licences(self):
        bad = cs.check({"a": {"citation": "x", "url": "u"}},
                       [{"id": "s", "theme": "Nowhere", "sources": ["b"], "file": "none.csv"}],
                       [{"title": "e", "theme": "Sea and coast"}])
        self.assertIn("source a: no licence", bad)
        self.assertIn("s: unknown source b", bad)
        self.assertIn("s: unknown theme Nowhere", bad)
        self.assertIn("e: no source", bad)
        self.assertIn("s: missing data/none.csv", bad)

    def test_notes_quote_their_sources(self):
        series = json.loads((cs.SRC / "series.json").read_text())
        notes = json.loads((cs.SRC / "notes.json").read_text())
        self.assertEqual(cs.check_notes(notes, series), [])
        self.assertEqual(len({n["id"] for n in notes}), len(notes))
        bad = cs.check_notes([{"id": "n", "text": "t", "series": ["nope"], "sources": [{"short": "x", "url": "u"}]}], series)
        self.assertIn("note n: unknown series nope", bad)
        self.assertIn("note n: a source has no quote", bad)


if __name__ == "__main__":
    unittest.main()
