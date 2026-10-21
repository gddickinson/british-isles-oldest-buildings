"""Date check statuses (bidb.references.date_check)."""
import unittest

from bidb.dates import parse_text_year
from bidb.references import date_check


def rec(year, extract, conf="Recorded", text=""):
    return {"year_start": year, "date_confidence": conf, "wikipedia_extract": extract, "date_text": text}


class DateCheckTest(unittest.TestCase):
    def test_conflict(self):
        st, _ = date_check(rec(1929, "The present house was built in the late 17th century."), [])
        self.assertEqual(st, "Conflict")

    def test_earlier_origin_is_not_a_conflict(self):
        st, _ = date_check(rec(1083, "The cathedral can trace its origin to the abbey founded in Ely in 672."), [])
        self.assertEqual(st, "Earlier origin")

    def test_later_addition_is_not_a_conflict(self):
        st, _ = date_check(rec(1150, "The tower was built in 1434 with money from a will."), [])
        self.assertNotEqual(st, "Conflict")

    def test_reviewed(self):
        self.assertEqual(date_check(rec(1615, "", conf="Corrected (reviewed)"), [])[0], "Reviewed")

    def test_hyphenated_century_text(self):
        self.assertEqual(parse_text_year("17th-century"), 1601)
        self.assertEqual(parse_text_year("9th (baptistery) and 10th centuries"), 801)


if __name__ == "__main__":
    unittest.main()
