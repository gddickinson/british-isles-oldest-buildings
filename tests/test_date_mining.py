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


class QuantityTest(unittest.TestCase):
    """Numbers that are counts, lengths or road numbers are not years (bidb.date_recheck, 2026-10-26)."""

    def test_counts_and_measures(self):
        for s in ("The station was built for the GER; the remaining 600 into tenements constructed at the company's cost.",
                  "It was built in two stages and capable of generating 400 megawatts.",
                  "It was built for a contingent of up to 500 cavalrymen.",
                  "It was built with 98 acres (400,000 m2) of gardens.",
                  "It was built 170 yards to the west (TL 761 260).",
                  "The carved head was added to commemorate the 900th anniversary.",
                  "The yew was built around, estimated to be between 600 and 1,000 years old.",
                  "The hall was built near a demonstration by a handful of 500s."):
            self.assertIsNone(date_from_text(s), s)

    def test_years_after_introducing_words(self):
        self.assertEqual(date_from_text("It was built before 959.")[0], 959)
        self.assertEqual(date_from_text("It was built in the year 924 by Edward.")[0], 924)
        self.assertEqual(date_from_text("Built in 1728 in the Queen Anne style.")[0], 1728)
        self.assertEqual(date_from_text("Y Gaer was built around AD 75.")[0], 75)
        self.assertEqual(date_from_text("Durrow was probably founded around the 550s.")[0], 550)

    def test_written_forms(self):
        from bidb.date_mining import candidates
        self.assertEqual(candidates("Infobox: c1460"), [(1460, "c1460")])
        self.assertEqual(candidates("510±70 BC"), [(-510, "510±70 BC")])
        self.assertEqual(candidates("It was built in the mid-15th century.")[0][0], 1434)
        self.assertEqual(candidates("Mid-late 18th century")[0][0], 1734)
        self.assertEqual(candidates("Early-mid 16th century")[0][0], 1501)

    def test_life_dates_and_grades(self):
        self.assertIsNone(date_from_text("A monastery was founded at Balla by Mo Chua of Balla (d. AD 637)."))
        self.assertEqual(date_from_text("It was built in 1325 by Gilbert de Southworth (b. 1270).")[0], 1325)
        self.assertEqual(date_from_text("The grade I listed manor house was built by Sir Roger Bluett c. 1540 "
                                        "and owned by the family until 1858.")[0], 1540)
        self.assertIsNone(date_from_text("The station was made a Grade II Listed Building on 17 May 1994."))


class RegisterTextTest(unittest.TestCase):
    def test_scanned_and_glued_text(self):
        from bidb.register_dates import date_from_register
        self.assertEqual(date_from_register("Later l7th century")[0], 1651)
        self.assertEqual(date_from_register("Thomas Mackenzie, Elgin, l851-4")[0], 1851)
        self.assertEqual(date_from_register("Gatehouse of C14, 1368-99")[0], 1301)
        self.assertEqual(date_from_register("Anglican parish church, probably15th century with vaulted nave")[0], 1401)
        self.assertIsNone(date_from_register("The fort is situated on a knoll approximately 400m SW of the summit"))


class ListDateTextTest(unittest.TestCase):
    """dates.parse_text_year (Wikipedia list and hoard dates) reads qualifiers as the text miner does."""

    def test_qualified_centuries(self):
        from bidb.dates import parse_text_year
        self.assertEqual(parse_text_year("Late 14th century"), 1351)        # Clackmannan Tower, was 1301
        self.assertEqual(parse_text_year("mid-12th century (Wikidata: 1136)"), 1134)
        self.assertEqual(parse_text_year("second half of the 15th century"), 1451)
        self.assertEqual(parse_text_year("late 3rd century BC"), -234)
        self.assertEqual(date_from_text("It was built in the late 14th century.")[0], 1351)

    def test_first_qualifier_and_plain_centuries(self):
        from bidb.dates import parse_text_year
        self.assertEqual(parse_text_year("Early-mid 16th century"), 1501)
        self.assertEqual(parse_text_year("early to mid-18th century"), 1701)
        self.assertEqual(parse_text_year("13th century (rebuilt late 14th century)"), 1201)
        self.assertEqual(parse_text_year("14th century"), 1301)
