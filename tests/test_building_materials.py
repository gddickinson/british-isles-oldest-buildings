"""BT3a: the checker of the curated materials and techniques (bidb.building_materials)."""
import unittest

from bidb import building_materials as bm

SRC = {"title": "Cob", "author": "Wikipedia", "kind": "reference", "url": "https://en.wikipedia.org/wiki/Cob",
       "locator": "lead", "quote": "Cob is a natural building material"}


def material(mid, **kw):
    m = {"id": mid, "name": mid.title(), "group": "Earth", "kind": "material", "fish": None,
         "period": {"text": "since about 1200", "from": 1200, "ongoing": True},
         "sources": [dict(SRC, about=["period"])]}
    m.update(kw)
    return m


def link(a, b, **kw):
    x = {"id": f"{a}>{b}", "from": a, "to": b, "kind": "replacement", "confidence": "documented",
         "claim": "c", "sources": [SRC]}
    x.update(kw)
    return x


class MaterialsTest(unittest.TestCase):
    def check(self, materials, links=(), partial=False):
        return bm.validate({"materials": materials, "links": list(links)}, type_ids={"longhouse"}, partial=partial)

    def test_good(self):
        m = material("cob", regions={"text": "Devon", "nations": ["England"]}, types=["longhouse"],
                     sources=[dict(SRC, about=["period", "region"])])
        self.assertEqual(self.check([m, material("thatch")], [link("cob", "thatch")]), [])

    def test_fields_need_sources(self):
        bad = self.check([material("cob", technology="the railways", geology=["Devonian"],
                                   examples=[{"name": "A house"}])])
        self.assertEqual(sorted(bad), ["material cob: no source about its example",
                                       "material cob: no source about its geology",
                                       "material cob: no source about its technology"])

    def test_unknown_values(self):
        m = material("cob", group="Plastic", kind="idea", geology=["Cheese"], types=["igloo"],
                     regions={"text": "x", "nations": ["Ireland"]}, fish={"scheme": "x", "id": "1"},
                     sources=[dict(SRC, about=["period", "geology", "region", "colour"])])
        bad = " | ".join(self.check([m]))
        for word in ("group 'Plastic'", "kind 'idea'", "geology 'Cheese'", "building type 'igloo'",
                     "regions", "fish", "source about ['period', 'geology', 'region', 'colour']"):
            self.assertIn(word, bad)

    def test_period(self):
        bad = self.check([material("cob", period={"text": "x", "from": 1900, "to": 1800})])
        self.assertTrue(any("out of order" in b for b in bad))

    def test_links(self):
        bad = self.check([material("cob"), material("cob")], [link("cob", "brick"), link("cob", "cob")])
        self.assertIn("material cob: duplicate id", bad)
        self.assertIn("link cob>brick: unknown material 'brick'", bad)
        self.assertIn("link cob>cob: links a material to itself", bad)
        self.assertNotIn("link cob>brick: unknown material 'brick'", self.check([material("cob")],
                                                                                [link("cob", "brick")], True))

    def test_loop_and_dispute(self):
        bad = self.check([material("a"), material("b")],
                         [link("a", "b", kind="descent"), link("b", "a", kind="descent", confidence="disputed")])
        self.assertTrue(any("descent loop" in b for b in bad))
        self.assertIn("link b>a: disputed without two views", bad)

    def test_unlinked_is_fine_and_groups(self):
        data = {"materials": [material("cob"), material("slate", group="Roofs"), material("lump")], "links": []}
        self.assertEqual(bm.validate(data, type_ids=set()), [])
        self.assertEqual(list(bm.by_group(data)), ["Earth", "Roofs"])
        self.assertEqual([c["id"] for c in bm.claims(data)], ["material:cob", "material:slate", "material:lump"])


if __name__ == "__main__":
    unittest.main()
