import io
import unittest
import zipfile
from unittest import mock

from bidb import fish_types

TERMS = """THE_TE_UID,TERM,INDEX_TERM,SCOPE_NOTE,CLA_GR_UID,STATUS,IMAGE_EXISTS
1,"DOMESTIC",N,"-",1,P,"-"
2,"HOUSE",Y,"A building for living in.",1,P,"-"
3,"HALL HOUSE",Y,"A house with an open hall.",1,P,"-"
4,"WEALDEN HOUSE",Y,"A medieval house with central open hall.",1,P,"-"
5,"MONUMENT <BY FORM>",N,"-",1,P,"-"
6,"TIMBER FRAMED HOUSE",Y,"-",1,P,"-"
7,"Wealden Hall House",N,"-",1,N,"-"
8,"AISLED HOUSE",Y,"-",1,P,"-"
"""
PREFS = "THE_TE_UID_1,THE_TE_UID_2\n7,4\n"
USES = """TH_T_U_UID,TERM,CLA_GR_UID,BROAD_TERM_U_UID,TOP_TERM_U_UID
10,DOMESTIC,1,,10
11,HOUSE,1,10,10
12,HALL HOUSE,1,11,10
13,WEALDEN HOUSE,1,12,10
14,MONUMENT <BY FORM>,1,,14
15,TIMBER FRAMED HOUSE,1,14,14
16,WEALDEN HOUSE,1,15,14
17,AISLED HOUSE,1,11,10
"""
RELS = "TH_T_U_UID_1,TH_T_U_UID_2\n17,12\n"


def fake_zip(*_args, **_kw):
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        for name, text in (("ThesaurusTerms.csv", TERMS), ("ThesaurusTermPreferences.csv", PREFS),
                           ("ThesaurusTermUses.csv", USES), ("ThesaurusTermRelations.csv", RELS)):
            z.writestr(name, text)
    buf.seek(0)
    return buf


class FishTypesTest(unittest.TestCase):
    def setUp(self):
        for f in (fish_types.concepts, fish_types._index):
            f.cache_clear()
        patcher = mock.patch("bidb.change_registers._download", fake_zip)
        patcher.start()
        self.addCleanup(patcher.stop)
        self.addCleanup(fish_types.concepts.cache_clear)
        self.addCleanup(fish_types._index.cache_clear)

    def test_polyhierarchy(self):
        c = fish_types.concepts()
        self.assertEqual(sorted(c["4"]["broader"]), ["3", "6"])
        self.assertEqual(sorted(fish_types.tops()), ["1", "5"])
        self.assertEqual(sorted(map(tuple, fish_types.paths("4"))), [("1", "2", "3", "4"), ("5", "6", "4")])
        self.assertEqual(fish_types.descendants("2"), {"2", "3", "4", "8"})

    def test_notes_alt_related(self):
        c = fish_types.concepts()
        self.assertEqual(c["1"]["note"], "")
        self.assertEqual(c["4"]["alt"], ["Wealden Hall House"])
        self.assertEqual(c["8"]["related"], ["3"])
        self.assertEqual(c["3"]["related"], ["8"])
        self.assertEqual(fish_types.label("4"), "Wealden house")
        self.assertTrue(fish_types.uri("4").endswith("/eh_tmt2/concepts/4"))

    def test_lookup(self):
        self.assertEqual(fish_types.lookup("Wealden hall-house"), "4")
        self.assertEqual(fish_types.lookup("hall houses"), "3")
        self.assertEqual(fish_types.lookup("house building"), "2")
        self.assertIsNone(fish_types.lookup("castle"))


if __name__ == "__main__":
    unittest.main()
