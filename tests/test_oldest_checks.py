"""Earliest dated places: Wikidata date precision and reviewed verdicts (bidb.oldest_checks)."""
import unittest

from bidb.oldest_checks import century, date_text, precision_of


def claim(time, precision, rank="normal", earliest=None, latest=None):
    q = {}
    for prop, year in (("P1319", earliest), ("P1326", latest)):
        if year:
            q[prop] = [{"snaktype": "value", "datavalue": {"value": {"time": f"+{year}-00-00T00:00:00Z"}}}]
    return {"rank": rank, "qualifiers": q, "mainsnak": {"snaktype": "value", "datavalue": {
        "value": {"time": time, "precision": precision}}}}


class Precision(unittest.TestCase):
    def test_texts(self):
        self.assertEqual(century(1819), "19th century")
        self.assertEqual(century(1900), "19th century")
        self.assertEqual(century(1201), "13th century")
        self.assertEqual(century(2001), "21st century")
        self.assertEqual(date_text(1819, 7, 1800, 1839), "between 1800 and 1839")
        self.assertEqual(date_text(1601, 7), "17th century")
        self.assertEqual(date_text(1834, 8), "1830s")

    def test_opening_date_wins_and_most_precise_statement(self):
        ent = {"claims": {"P571": [claim("+1819-00-00T00:00:00Z", 7, earliest=1800, latest=1819)]}}
        self.assertEqual(precision_of(ent), (7, 1800, 1819))
        ent["claims"]["P1619"] = [claim("+1825-09-27T00:00:00Z", 11)]
        self.assertEqual(precision_of(ent)[0], 11)
        ent = {"claims": {"P571": [claim("+1700-00-00T00:00:00Z", 7), claim("+1712-00-00T00:00:00Z", 9),
                                   claim("+1650-00-00T00:00:00Z", 9, rank="deprecated")]}}
        self.assertEqual(precision_of(ent), (9, None, None))
        self.assertIsNone(precision_of({"claims": {}}))


if __name__ == "__main__":
    unittest.main()
