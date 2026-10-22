"""Shipwrecks from the wreck inventories (bidb.wrecks). .venv/bin/python -m unittest discover tests"""
import unittest

from bidb.wrecks import loss_year, vessel


class Wrecks(unittest.TestCase):
    def test_year_of_loss_from_site_type(self):
        self.assertEqual(loss_year("DUTCH EAST INDIAMAN (17TH CENTURY)-(1664)"), (1664, "lost 1664"))
        self.assertEqual(loss_year("STEAMSHIP (20TH CENTURY)-(1916)"), (1916, "lost 1916"))
        self.assertEqual(loss_year("CRAFT (18TH CENTURY)"), (1701, "lost in the 18th century"))
        self.assertEqual(loss_year("CRAFT"), (None, None))

    def test_vessel_type(self):
        self.assertEqual(vessel("DUTCH EAST INDIAMAN (17TH CENTURY)-(1664)"), "Dutch east indiaman")
        self.assertEqual(vessel("OBSTRUCTION"), "Obstruction")
        self.assertIsNone(vessel(""))


if __name__ == "__main__":
    unittest.main()
