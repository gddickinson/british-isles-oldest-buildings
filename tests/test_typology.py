"""Type-based date estimates: an Irish SMR townland named Rath or Cashel is no ringfort."""
import unittest
from unittest import mock

from bidb import places_build
from bidb.typology import estimate


def place(pid, typ, name):
    return {"id": pid, "type": typ, "name": name, "year_start": None,
            "kind_group": "Archaeological sites"}


class EstimateTest(unittest.TestCase):
    def test_friars_house_is_a_friary(self):
        self.assertEqual(estimate(["Religious house - Dominican friars"], None)[0], 1224)

    def test_smr_townland_is_not_read(self):
        rows = [place("iesmr-CL025-084001-", "Church", "Church, Rath"),
                place("iesmr-CL025-008002-", "Castle - tower house", "Castle - tower house, Rath"),
                place("q1", "Scheduled monument", "Skye, Dun Liath")]
        with mock.patch.object(places_build, "log", lambda *a: None):
            places_build.estimate_dates(rows)
        self.assertIsNone(rows[0]["year_start"])
        self.assertEqual(rows[1]["year_start"], 1400)
        self.assertEqual(rows[2]["year_start"], -500)     # other registers' names still count


if __name__ == "__main__":
    unittest.main()
