"""Catalogue categories from Wikidata class labels (bidb.classify.categorise, bidb.categories)."""
import unittest

from bidb.categories import CATEGORY_ORDER
from bidb.classify import categorise


class TestCategories(unittest.TestCase):
    def test_guild_halls_are_civic(self):
        # "guild house" must not fall to the generic "house", nor "city hall" to "hall" (found in C3a)
        self.assertEqual(categorise(["guild house", "independent museum"], "Merchant Adventurers' Hall"), "Civic building")
        self.assertEqual(categorise(["city hall"], "Windsor Guildhall"), "Civic building")
        self.assertEqual(categorise(["residential building"], "Old Cloth Hall"), "House / domestic")

    def test_castle_before_city_hall(self):
        self.assertEqual(categorise(["castle", "city hall"], "Hertford Castle"), "Castle / fortification")

    def test_order_lists_each_category_once(self):
        self.assertEqual(len(CATEGORY_ORDER), len(set(CATEGORY_ORDER)))
        self.assertEqual(CATEGORY_ORDER.count("Civic building"), 1)


if __name__ == "__main__":
    unittest.main()
