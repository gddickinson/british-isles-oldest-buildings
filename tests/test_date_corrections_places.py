"""Reviewed date corrections reach places too (bidb.date_corrections.apply_places)."""
import unittest
from unittest import mock

from bidb import date_corrections


class TestPlaceCorrections(unittest.TestCase):
    def test_apply_places(self):
        data = {"Q638485": {"year_start": -2600, "date_text": "c. 2600–2300 BC (worked)", "evidence": "e", "source": "s"}}
        places = [{"id": "Q638485", "year_start": -2200, "date_text": "c. 2200 BC–1500 BC (typical for round barrows), estimate",
                   "period": "Bronze Age"}, {"id": "Q1", "year_start": 1200, "date_text": "1200", "period": "x"}]
        with mock.patch.object(date_corrections, "load", return_value=data):
            self.assertEqual(date_corrections.apply_places(places), 1)
        self.assertEqual((places[0]["year_start"], places[0]["period"]), (-2600, "Neolithic"))
        self.assertEqual(places[1]["year_start"], 1200)


if __name__ == "__main__":
    unittest.main()
