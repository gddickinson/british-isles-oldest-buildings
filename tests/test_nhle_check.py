"""Records on an outbuilding's NHLE list entry: .venv/bin/python -m unittest discover tests"""
import unittest

from bidb import nhle_check


class NhleCheck(unittest.TestCase):
    def test_head_of_an_entry(self):
        self.assertEqual(nhle_check.head("CHURCH OF ST MARY AND ATTACHED WALL AND RAILINGS"), "CHURCH")
        self.assertEqual(nhle_check.head("STABLEBLOCK, CIRCA 80 METRES NORTH-EAST OF ORMESBY HALL"), "STABLEBLOCK")
        self.assertEqual(nhle_check.head("Hawk Stone standing stone 700m south of Claridges Barn"),
                         "Hawk Stone standing stone")

    def test_flags_an_outbuilding_entry(self):
        self.assertEqual(nhle_check.flag("Ormesby Hall", "STABLEBLOCK, CIRCA 80 METRES NORTH-EAST OF ORMESBY HALL"),
                         ["stableblock"])
        self.assertEqual(nhle_check.flag("The Homestead", "FORMER COACH HOUSE OF THE HOMESTEAD"), ["coachhouse"])

    def test_main_building_with_extras_fits(self):
        self.assertEqual(nhle_check.flag("Winkburn Hall", "WINKBURN HALL AND ATTACHED WALL"), [])
        self.assertEqual(nhle_check.flag("Colchester Roman town walls", "THE ROMAN TOWN WALL"), [])
        self.assertEqual(nhle_check.flag("Dovecot at Court House", "DOVECOTE ABOUT 10 METRES WEST OF COURT HOUSE"), [])
        self.assertEqual(nhle_check.flag("Peveril Castle", "PEVERIL CASTLE CURTAIN WALLS",
                                         "Castle / fortification"), [])

    def test_reviewed_corrections_apply(self):
        fixes = nhle_check.corrections()
        self.assertTrue(fixes)
        recs = [{"id": q, "nhle_id": e["was"]} for q, e in fixes.items()] + [{"id": "Q1", "nhle_id": "1"}]
        self.assertEqual(nhle_check.apply(recs), len(fixes))
        self.assertTrue(all(r["nhle_id"] == fixes[r["id"]]["nhle_id"] for r in recs[:-1]))
        self.assertEqual(recs[-1]["nhle_id"], "1")
        for e in fixes.values():
            self.assertTrue(e["reason"] and e["entry"] and e["nhle_id"].isdigit())


if __name__ == "__main__":
    unittest.main()
