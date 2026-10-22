import unittest

from bidb import burials, oldest_lists, place_kinds, place_stage, sports, trade_works
from app.quiz_api import surprising


class Sports(unittest.TestCase):
    def test_kinds_registered_and_distinct(self):
        all_kinds = list(sports.KINDS) + list(burials.KINDS) + list(trade_works.KINDS) + list(oldest_lists.KINDS)
        self.assertEqual(len(all_kinds), len(set(all_kinds)))
        self.assertIn("Sport & leisure", place_kinds.PLACE_GROUPS)
        for k in sports.KINDS:
            self.assertEqual(place_kinds.KIND_GROUP[k], "Sport & leisure")
        self.assertTrue(set(sports.KINDS) <= place_stage.protected())

    def test_classes_once(self):
        for table in (sports.VENUES, sports.CLUBS):
            classes = [c for _l, cs in table.values() for c in cs]
            self.assertEqual(len(classes), len(set(classes)))
        self.assertFalse(sports.NOT_SPORT & {c for _l, cs in sports.VENUES.values() for c in cs})

    def test_kind_for(self):
        self.assertEqual(sports.kind_for({"Q682943"}, sports.VENUES), "sp_cricket")
        self.assertEqual(sports.kind_for({"Q1076486"}, sports.VENUES), "sp_venue")
        self.assertEqual(sports.kind_for({"Q476028"}, sports.CLUBS), "spc_football")
        self.assertEqual(sports.kind_for({"Q847017"}, sports.CLUBS), "spc_other")

    def test_refine_by_name(self):
        self.assertEqual(sports.refine("sp_venue", "Mount Pleasant (cricket ground)"), "sp_cricket")
        self.assertEqual(sports.refine("sp_venue", "Albion Greyhound Stadium"), "sp_racing")
        self.assertEqual(sports.refine("sp_stadium", "Páirc Uí Chaoimh"), "sp_gaelic")
        self.assertEqual(sports.refine("spc_other", "Clooney Gaels GAC"), "spc_gaelic")
        self.assertEqual(sports.refine("spc_other", "Doncaster R.L.F.C."), "spc_rugby")
        self.assertEqual(sports.refine("spc_football", "Grange Hockey Club"), "spc_other")
        self.assertEqual(sports.refine("spc_football", "Cowdenbeath F.C."), "spc_football")


class Institutions(unittest.TestCase):
    def test_kinds_registered(self):
        from bidb import institutions
        self.assertTrue(set(institutions.KINDS).isdisjoint(sports.KINDS + oldest_lists.KINDS + trade_works.KINDS))
        self.assertIn("Public institutions", place_kinds.PLACE_GROUPS)
        self.assertTrue(set(institutions.KINDS) <= place_stage.protected())
        self.assertEqual(list(institutions.KINDS)[-1], "pi_school")       # schools only when nothing else fits

    def test_keep_school(self):
        from bidb.institutions import keep_school
        self.assertFalse(keep_school({"wikipedia_title": "Eton College", "year_start": None}))   # undated
        self.assertTrue(keep_school({"wikipedia_title": None, "year_start": 1850}))
        self.assertFalse(keep_school({"wikipedia_title": None, "year_start": 1965}))
        self.assertFalse(keep_school({"wikipedia_title": None, "year_start": None}))


class QuizNames(unittest.TestCase):
    def test_surprising(self):
        self.assertTrue(surprising("Woodnesborough", "WINZ-brə"))
        self.assertTrue(surprising("Cholmondeley", "CHUM-lee"))
        self.assertFalse(surprising("Hartlepool", "HART-lih-pool"))


if __name__ == "__main__":
    unittest.main()
