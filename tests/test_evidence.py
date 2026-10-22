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


class Listings(unittest.TestCase):
    def test_list_description_from_both_page_layouts(self):
        from bidb.listings import _blb_text
        old = "<nav>Search</nav> Tagged with: Mill Description TOTTON Tide Mill II* Tide Mill. Mid C18 on site of mill. Listing NGR: SU36"
        new = "<p>Tagged with: Pub</p> Summary A public house, late-C17. Description More. History x. External Links Wikidata"
        self.assertTrue(_blb_text(old).startswith("Description TOTTON") and _blb_text(old).endswith("site of mill."))
        self.assertTrue(_blb_text(new).startswith("Summary A public house") and "External" not in _blb_text(new))
        self.assertEqual(_blb_text("<p>no listing here</p>"), "")

    def test_dated_sentences_skip_list_headers(self):
        from bidb.listings import dated_sentences
        text = ("SK9771NE 1941-1/9/378 08/10/53 LINCOLN STEEP HILL GV I House. Late C12, restored 1858. "
                "This list entry was subject to a Minor Amendment on 08/12/2020. Built of ashlar.")
        self.assertEqual(dated_sentences(text), ["Late C12, restored 1858."])
