"""Old forms of Welsh place names (bidb.welsh_names). .venv/bin/python -m unittest discover tests"""
import sqlite3
import unittest

from bidb import welsh_names as wn


ROWS = [{"enw_name": "Kard'", "discy_pdes": "c.1102", "blwgyn_eye": "1102", "prife_hnme": "Cardiff / Caerdydd",
         "cyfgr_grrf": "ST 18000 76000", "prim_srce": "Cartae"},
        {"enw_name": "Cardif", "discy_pdes": "1107 (1496)", "blwgyn_eye": "1107", "prife_hnme": "Cardiff / Caerdydd",
         "cyfgr_grrf": "ST 18000 76000", "prim_srce": "CPR"},
        {"enw_name": "cardif", "discy_pdes": "1290", "blwgyn_eye": "1290", "prife_hnme": "Cardiff / Caerdydd",
         "cyfgr_grrf": "ST 18000 76000", "prim_srce": "X"},
        {"enw_name": "Castell", "discy_pdes": "", "blwgyn_eye": "", "prife_hnme": "Castell", "cyfgr_grrf": "SH 60000 70000",
         "prim_srce": ""}]


class OldNames(unittest.TestCase):
    def test_fold(self):
        self.assertEqual(wn.fold("Llanfihangel-y-Pennant"), "llanfihangel y pennant")
        self.assertEqual(wn.fold("Ynys Môn"), "ynys mon")

    def test_link_by_town_within_reach(self):
        heads = wn.headnames(ROWS)
        self.assertEqual(heads["Cardiff / Caerdydd"]["names"], {"cardiff", "caerdydd"})
        conn = sqlite3.connect(":memory:")
        conn.executescript("""CREATE TABLE buildings (id, name, locality, lat, lon, nation);
            CREATE TABLE places (id, name, locality, lat, lon, nation);
            INSERT INTO buildings VALUES ('Q1', 'Cardiff Castle', 'Castle, Cathays, Cardiff', 51.482, -3.181, 'Wales');
            INSERT INTO buildings VALUES ('Q2', 'Far Hall', 'Cardiff', 52.9, -3.5, 'Wales');""")
        self.assertEqual(wn.link(conn, heads), {"Q1": "Cardiff / Caerdydd"})       # Q2 is 150 km away
        conn.executescript(wn.SCHEMA)
        conn.executemany("INSERT INTO old_names VALUES (?, ?, ?, ?, ?)",
                         [("Cardiff / Caerdydd", *f) for f in heads["Cardiff / Caerdydd"]["forms"]])
        conn.execute("INSERT INTO old_name_links VALUES ('Q1', 'Cardiff / Caerdydd')")
        got = wn.for_record(conn, "Q1")
        self.assertEqual([f["form"] for f in got["forms"]], ["Kard'", "Cardif"])    # each spelling once, oldest first


if __name__ == "__main__":
    unittest.main()
