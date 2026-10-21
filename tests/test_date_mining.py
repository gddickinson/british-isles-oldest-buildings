"""Date mining from article text: comparison sentences are not construction dates."""
import unittest

from bidb.date_mining import date_from_text


class ComparisonTest(unittest.TestCase):
    def test_date_after_comparison_is_ignored(self):
        text = ("These megalithic tombs were built to resemble the long timber houses constructed "
                "by farmers in the Danube basin from circa 4800 BC.")
        self.assertIsNone(date_from_text(text))

    def test_date_before_comparison_is_kept(self):
        hit = date_from_text("The church was built in 1822, modelled on Kintore Church.")
        self.assertEqual(hit[0], 1822)

    def test_plain_date(self):
        self.assertEqual(date_from_text("The tower was built in the 12th century.")[0], 1101)


if __name__ == "__main__":
    unittest.main()


class StrictCheckTest(unittest.TestCase):
    """date_from_text(strict=True) is what the date check uses."""

    def test_units_and_decimals_are_not_years(self):
        self.assertIsNone(date_from_text("Several buildings on the 693-acre property were built as cottages.", strict=True))
        self.assertEqual(date_from_text("Standing at 148.65 metres (487.7 ft), it was built in 1974.", strict=True)[0], 1974)

    def test_fittings_saints_and_styles_skipped(self):
        for s in ("The font dates from the 12th century.",
                  "The church is dedicated to a 6th-century Welsh saint.",
                  "Designed in a 9th-century neo-Byzantine style, it was built in brick."):
            self.assertIsNone(date_from_text(s, strict=True), s)
        self.assertEqual(date_from_text("It was built in the 12th century in the Romanesque style.", strict=True)[0], 1101)

    def test_ordinal_compounds(self):
        hit = date_from_text("Probably constructed in the thirty-seventh century BC.")
        self.assertTrue(hit is None or hit[0] != -700)
