"""Roadmap C3c: halls from OpenStreetMap, people of the trade places, trade_works kinds (no network)."""
import sqlite3
import unittest
from unittest import mock

from bidb import people, trade_people, trade_works
from bidb.people import LINK_COLUMNS, PERSON_COLUMNS
from bidb.livery import osm_halls

OSM = {"elements": [
    {"type": "node", "id": 1, "lat": 51.51396, "lon": -0.09191,
     "tags": {"name": "Mercers' Hall", "addr:street": "Ironmonger Lane"}},
    {"type": "node", "id": 2, "lat": 51.51711, "lon": -0.09578,
     "tags": {"name": "Plaisterers’ Hall", "addr:street": "London Wall"}},
    {"type": "node", "id": 3, "lat": 51.51695, "lon": -0.09296,         # the plaque for the earlier halls
     "tags": {"name": "Plaisterers' Hall", "historic": "memorial", "memorial": "plaque"}},
    {"type": "way", "id": 4, "center": {"lat": 51.5, "lon": -0.1},      # right name, another street
     "tags": {"name": "Clothworkers' Hall", "addr:street": "Elsewhere Road"}}]}


class OsmHalls(unittest.TestCase):
    def test_street_must_agree(self):
        info = {"Q1": {"hall": "Mercers' Hall, Ironmonger Lane"},
                "Q2": {"hall": "Plaisterers' Hall, London Wall"},
                "Q3": {"hall": "Clothworkers' Hall, Dunster Court, Mincing Lane"},
                "Q4": {"hall": "Insurers' Hall (closed)"},
                "Q5": {"hall": None}}
        with mock.patch("app.basemap_sources.overpass", return_value=OSM) as op:
            got = osm_halls(info)
        self.assertEqual(got, {"Q1": (51.51396, -0.09191, "node/1"), "Q2": (51.51711, -0.09578, "node/2")})
        query = op.call_args[0][0]
        self.assertIn("Mercers['’]?", query)          # either apostrophe matches
        self.assertNotIn("Insurers", query)           # closed halls are not looked up

    def test_nothing_to_look_up(self):
        with mock.patch("app.basemap_sources.overpass") as op:
            self.assertEqual(osm_halls({"Q9": {"hall": None}}), {})
        op.assert_not_called()


def _db():
    conn = sqlite3.connect(":memory:")
    cols = lambda spec: ", ".join(f"{c} {t}" for c, t in spec)
    conn.executescript(f"""CREATE TABLE places (id TEXT PRIMARY KEY, kind TEXT, kind_group TEXT, name TEXT);
        CREATE TABLE persons ({cols(PERSON_COLUMNS)}); CREATE TABLE person_links ({cols(LINK_COLUMNS)});""")
    conn.executemany("INSERT INTO places VALUES (?, ?, ?, ?)", [
        ("Q1", "tr_livery", "Markets & trade", "Drapers"), ("Q2", "tr_town", "Markets & trade", "Kendal"),
        ("Q3", "tro_market", "Markets & trade", "Kirkby Lonsdale market"), ("Q4", "iw_mill", "Industrial heritage", "Mill"),
        ("tea-x", "tea_room", "Markets & trade", "No Wikidata id")])
    return conn


class TradePeople(unittest.TestCase):
    def test_targets(self):
        conn = _db()
        self.assertEqual(trade_people.targets(conn, settlements={"Q3"}), {"Q1"})   # no towns, no other groups
        self.assertEqual(trade_people.targets(conn, settlements=set()), {"Q1", "Q3"})
        # the later place groups (run_later): the mill only
        self.assertEqual(trade_people.targets(conn, settlements=set(), groups=trade_people.LATER), {"Q4"})

    def test_organisation_roles_only_for_trade_and_museums(self):
        conn = _db()
        found = {}
        with mock.patch("bidb.db.connect", return_value=conn), \
                mock.patch.object(trade_people, "_settlements", return_value=set()), \
                mock.patch.object(trade_people.people, "find_links", return_value=[]), \
                mock.patch.object(trade_people, "org_links", side_effect=lambda t, log: found.setdefault("org", set(t)) and []), \
                mock.patch.object(trade_people.people, "prepare", return_value=([], [])), \
                mock.patch.object(trade_people.people, "link_references", return_value={}):
            trade_people.run_later(log=lambda *a: None)
        self.assertNotIn("org", found)                 # the mill's group has no organisation roles

    def test_write_replaces_links_keeps_people(self):
        conn = _db()
        conn.execute("INSERT INTO persons (id, name) VALUES ('P1', 'Old name')")
        conn.executemany("INSERT INTO person_links VALUES (?, ?, ?, ?, ?)", [
            ("P1", "Q1", "place", "Member", None),          # replaced
            ("P1", "Q4", "place", "Owner", None),           # another group's place: kept
            ("P1", "Q1", "building", "Owner", None)])       # a building with the same id: kept
        trade_people.write(conn, {"Q1", "Q3"}, [{"id": "P1", "name": "New name"}, {"id": "P2", "name": "Two"}],
                           [("P2", "Q1", "place", trade_people.OFFICER, None)])
        self.assertEqual(conn.execute("SELECT name FROM persons WHERE id = 'P1'").fetchone()[0], "Old name")
        self.assertEqual(sorted(conn.execute("SELECT person_id, target_id, target_type, role FROM person_links")), [
            ("P1", "Q1", "building", "Owner"), ("P1", "Q4", "place", "Owner"),
            ("P2", "Q1", "place", "Master, governor or officer")])

    def test_roles_are_new(self):
        known = set(people.PERSON_TO_PLACE.values()) | set(people.PLACE_TO_PERSON.values())
        self.assertTrue({trade_people.MEMBER, trade_people.WORKED, trade_people.OFFICER}.isdisjoint(known))


class References(unittest.TestCase):
    def _refs(self, row, links):
        with mock.patch("bidb.people.sparql", return_value=[row]):
            return people.link_references(links, lambda m: None, trade_people.PERSON_PROPS)

    def test_unlabelled_source_links_its_item(self):
        e = "http://www.wikidata.org/entity/"
        row = {"s": {"value": e + "P1"}, "p": {"value": e + "P463"}, "o": {"value": e + "Q1"},
               "statedLabel": {"value": "Q64697845"}}
        got = self._refs(row, [("P1", "Q1", trade_people.MEMBER), ("P1", "Q1", trade_people.OFFICER)])
        self.assertEqual(list(got), [("P1", "Q1", "Member")])     # the officer role has no single property
        self.assertIn('"u": "https://www.wikidata.org/wiki/Q64697845"', got[("P1", "Q1", "Member")])


class MerchantHouses(unittest.TestCase):
    def test_merchant_house_yields(self):
        """An item that is both a merchant's house and a distillery (Plymouth Gin) is a distillery."""
        both = {"Q1868065", "Q131734"}
        seen = {}
        direct = lambda classes: {"QX": classes & both} if classes & both else {}
        with mock.patch.object(trade_works, "direct_items", side_effect=direct), \
                mock.patch.object(trade_works, "rows_for", side_effect=lambda kinds: seen.update(kinds) or []), \
                mock.patch.object(trade_works.livery, "build", return_value=[]):
            trade_works.build(lambda m: None)
        self.assertEqual(seen, {"QX": "iw_drink"})


if __name__ == "__main__":
    unittest.main()
