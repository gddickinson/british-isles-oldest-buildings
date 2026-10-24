import unittest

from bidb import burials, oldest_lists, trade_works
from bidb.evidence import KINDS, VERDICTS, validate


class OldestLists(unittest.TestCase):
    def test_claims_valid(self):
        claims = oldest_lists.claims()
        self.assertTrue(claims)
        self.assertEqual(validate(claims), [])
        self.assertEqual(len({c["id"] for c in claims}), len(claims))
        for c in claims:
            self.assertIn(c["verdict"], VERDICTS)
            self.assertTrue(all(s["kind"] in KINDS for s in c["sources"]))

    def test_every_category_has_a_kind(self):
        for name, spec in oldest_lists.LISTS.items():
            for e in oldest_lists.entries(name):
                self.assertIn(e["category"], spec["kinds"], f"{name}: {e['name']}")

    def test_record_ids_unique_within_lists(self):
        ids = [oldest_lists.record_id(n, e) for n in oldest_lists.LISTS for e in oldest_lists.entries(n)
               if not e.get("listed_in")]
        self.assertEqual(len(ids), len(set(ids)))

    def test_listed_in_entries_resolve(self):
        # an entry kept in another list (Twinings in the tea list) takes that list's entry, id and sources
        for n in oldest_lists.LISTS:
            for e in oldest_lists.entries(n):
                if e.get("listed_in"):
                    self.assertTrue(e.get("sources") and e.get("lat"), f"{n}: {e['name']}")
        self.assertFalse([r for r in oldest_lists.records("tea") if r["id"] in ("Q1054692", "Q498563")])

    def test_guilds_unplaced_companies_are_not_links(self):
        # a company with no single standing place (the Weavers) has no coordinates and no place: listed only
        import sqlite3
        conn = sqlite3.connect(":memory:")
        conn.execute("CREATE TABLE buildings (id TEXT)")
        conn.execute("CREATE TABLE places (id TEXT)")
        conn.executemany("INSERT INTO places VALUES (?)", [("Q805708",), ("Q8037025",)])
        from unittest import mock
        with mock.patch("bidb.oldest_checks.earliest", return_value={}):
            lists = oldest_lists.lists(conn)
        out = {e["name"]: e for c in lists["guilds"]["categories"] for e in c["entries"]}
        self.assertFalse(out["Worshipful Company of Weavers"]["placed"])
        self.assertTrue(out["Baltic Exchange"]["placed"])
        self.assertTrue(out["Worshipful Company of Drapers"]["placed"])     # a livery-company place of trade_works
        self.assertEqual(out["Worshipful Company of Weavers"]["year"], 1130)


class Stages(unittest.TestCase):
    def test_prehistoric_burials_left_out(self):
        for name in ("Gwern y Cleppa chambered cairn", "Long barrow", "Wedge tomb", "Bowl barrow cemetery"):
            self.assertTrue(burials.PREHISTORIC.search(name), name)
        self.assertFalse(burials.PREHISTORIC.search("Kensal Green Cemetery"))

    def test_kinds_do_not_clash(self):
        all_kinds = list(burials.KINDS) + list(trade_works.KINDS) + list(oldest_lists.KINDS)
        self.assertEqual(len(all_kinds), len(set(all_kinds)))
        classes = [c for _g, _l, cs in trade_works.CLASSES.values() for c in cs]
        self.assertEqual(len(classes), len(set(classes)))


if __name__ == "__main__":
    unittest.main()
