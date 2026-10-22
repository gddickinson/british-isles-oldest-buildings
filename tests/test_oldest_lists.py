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
        ids = [oldest_lists.record_id(n, e) for n in oldest_lists.LISTS for e in oldest_lists.entries(n)]
        self.assertEqual(len(ids), len(set(ids)))


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
