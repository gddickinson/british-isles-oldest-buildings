import unittest

from bidb.enrich import tidy_extract


class TidyExtract(unittest.TestCase):
    def test_empty_brackets_left_by_ipa(self):
        self.assertEqual(tidy_extract("Sir Christopher Wren (; 30 October 1632 – 8 March 1723) was"),
                         "Sir Christopher Wren (30 October 1632 – 8 March 1723) was")
        self.assertEqual(tidy_extract("Mary Wollstonecraft (, also UK: ; 27 April 1759)"), "Mary Wollstonecraft (27 April 1759)")
        self.assertEqual(tidy_extract("Hever ( ) is"), "Hever is")

    def test_respellings_kept(self):
        self.assertEqual(tidy_extract("Chequers ( CHEK-ərz) is"), "Chequers ( CHEK-ərz) is")
        self.assertIsNone(tidy_extract(None))


if __name__ == "__main__":
    unittest.main()
