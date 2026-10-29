"""Research track: the evidence file is well formed and quotes match despite typography (no network)."""
import unittest

from bidb import evidence
from bidb.verify_research import pdf_text


def tiny_pdf(lines):
    """A one-page PDF with these lines of Helvetica text (for the PDF reader)."""
    body = "BT /F1 12 Tf 72 720 Td " + " 0 -16 Td ".join(f"({t}) Tj" for t in lines) + " ET"
    objs = ["<< /Type /Catalog /Pages 2 0 R >>", "<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
            "<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R "
            "/Resources << /Font << /F1 5 0 R >> >> >>",
            f"<< /Length {len(body)} >>\nstream\n{body}\nendstream",
            "<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>"]
    out, offsets = "%PDF-1.4\n", []
    for i, o in enumerate(objs, 1):
        offsets.append(len(out))
        out += f"{i} 0 obj\n{o}\nendobj\n"
    xref = len(out)
    out += f"xref\n0 {len(objs) + 1}\n0000000000 65535 f \n" + "".join(f"{o:010d} 00000 n \n" for o in offsets)
    return (out + f"trailer\n<< /Size {len(objs) + 1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n").encode()


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


    def test_pdf_sources_are_read(self):
        text = pdf_text(tiny_pdf(["Ruggles has sug-", "gested that this corresponds"]))
        if text is None:
            self.skipTest("pdftotext not installed")
        self.assertTrue(evidence.quote_found("Ruggles has suggested that this corresponds", text))


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
