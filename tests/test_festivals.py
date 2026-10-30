"""Festivals and seasons (bidb.festivals, bidb.festival_finds): the researched files and what the catalogue holds."""
import sqlite3
import unittest

from bidb import festival_finds as ff
from bidb import festivals


def catalogue():
    """A small in-memory catalogue with the tables festival_finds reads."""
    con = sqlite3.connect(":memory:")
    con.executescript("""
        CREATE TABLE buildings (id TEXT, name TEXT, year_start INT, date_text TEXT, locality TEXT, nation TEXT,
            lat REAL, lon REAL, image_thumb TEXT, dedication TEXT);
        CREATE TABLE places (id TEXT, name TEXT, kind TEXT, kind_label TEXT, year_start INT, date_text TEXT,
            locality TEXT, nation TEXT, lat REAL, lon REAL, image_thumb TEXT, wikidata_id TEXT);
        CREATE TABLE stories (entity_kind TEXT, entity_id TEXT, kind TEXT, heading TEXT, text TEXT, source_url TEXT,
            licence TEXT);
        CREATE TABLE persons (id TEXT, name TEXT);
        CREATE TABLE person_links (person_id TEXT, target_id TEXT, target_type TEXT, role TEXT, ref TEXT);
        INSERT INTO buildings VALUES ('Q1', 'St Andrew, Old', 1100, 'c. 1100', 'X', 'England', 52, -1, '', 'Andrew the Apostle'),
            ('Q2', 'St Andrew, New', 1300, '1300', 'Y', 'England', 53, -1, '', 'Andrew the Apostle'),
            ('Q3', 'Castle', 1200, '1200', 'Z', 'Scotland', 56, -3, '', '');
        INSERT INTO places VALUES ('P1', 'St Brigid''s Well', 'holy_well', 'holy well', NULL, '', 'K', 'Republic of Ireland', 53, -7, '', 'Q9'),
            ('P2', 'Lady Well', 'holy_well', 'holy well', NULL, '', 'K', 'England', 52, -2, '', NULL),
            ('P3', 'Bowl barrow 300m east of St Patrick''s Church', 'barrow', 'barrow', NULL, '', '', 'England', 52, -2, '', NULL),
            ('P4', 'St Patrick''s Chapel', 'chapel', 'chapel', 900, '', '', 'Wales', 51.9, -5.3, '', NULL);
        INSERT INTO stories VALUES ('building', 'Q3', 'supernatural', 'Ghosts', 'A ghost walks here at Halloween; the ghost is grey.', 'u', ''),
            ('building', 'Q1', 'legend', '', 'Saint Andrew''s relics, they say, came here.', 'u', ''),
            ('building', 'Q3', 'legend', '', 'Nothing seasonal at all, only ghostly echoes.', 'u', '');
        INSERT INTO persons VALUES ('Q81960', 'Robert Burns');
        INSERT INTO person_links VALUES ('Q81960', 'Q3', 'building', 'resident', '');
    """)
    return con


class FestivalFilesTest(unittest.TestCase):
    def test_files(self):
        self.assertEqual(festivals.problems(), [])
        ids = [c["id"] for c in festivals.claims()]
        self.assertEqual(len(ids), len(set(ids)))
        for f in festivals.load():
            self.assertIn(f["id"], ff.FIND, f["id"])         # every festival says where to look in the catalogue

    def test_validate(self):
        bad = {"id": "x", "title": "X", "season": "monsoon", "when": {"date": "25 Dec"}, "when_text": "t", "intro": "i",
               "facts": [{"kind": "gossip", "title": "a", "text": "b", "sources": []}],
               "places": [{"name": "Nowhere", "why": "w", "lat": 10, "lon": 10,
                           "sources": [{"title": "t", "url": "u", "quote": "q", "kind": "blog"}]}]}
        got = " | ".join(festivals.validate(bad))
        for part in ("season", "when", "kind 'gossip'", "no sources", "lat/lon", "kind in"):
            self.assertIn(part, got)


class FestivalFindsTest(unittest.TestCase):
    def test_finds(self):
        con = catalogue()
        n, rows, points = ff.churches(con, ["Andrew the Apostle"])
        self.assertEqual((n, [r["id"] for r in rows], len(points)), (2, ["Q1", "Q2"], 2))   # oldest first
        n, st = ff.stories(con, ff._rx(ff.FIND["halloween"]))
        self.assertEqual(n, 1)                                  # "ghostly" is not the whole word "ghost"
        self.assertEqual(st[0]["name"], "Castle")
        self.assertEqual(ff.stories(con, ff._rx(ff.FIND["st-andrew"]))[0], 1)
        n, pl = ff.places(con, ff.FIND["imbolc"])               # holy wells narrowed to Brigid's
        self.assertEqual([p["id"] for p in pl], ["P1"])
        n, pl = ff.places(con, ff.FIND["st-patrick"])           # by name, but not the barrow east of the church
        self.assertEqual([p["id"] for p in pl], ["P4"])
        self.assertEqual([p["id"] for p in ff.people(con, ["Q81960"])], ["Q3"])
        self.assertEqual(ff.link_places(con, {"places": [{"qid": "Q1"}, {"qid": "Q9"}, {"qid": "Q77"}]}),
                         {"Q1": ["building", "Q1"], "Q9": ["place", "P1"]})


if __name__ == "__main__":
    unittest.main()
