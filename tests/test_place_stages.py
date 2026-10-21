"""Underground and military stages: kind keys, labels and the curated lists (no network)."""
import json
import unittest

from bidb import era_places, lore_places, maritime, military, underground
from bidb.place_kinds import KIND_GROUP, KIND_LABEL, KINDS as BASE_KINDS, PLACE_GROUPS


class UndergroundKinds(unittest.TestCase):
    def test_kinds_do_not_collide(self):
        # each stage deletes its own kinds before writing: a shared key would delete another stage's places
        from bidb import bridges, museums
        stages = [era_places.KINDS, maritime.KINDS, lore_places.KINDS, underground.KINDS, military.KINDS, museums.KINDS,
                  bridges.KINDS,
                  [k["key"] for k in BASE_KINDS]]
        seen = set()
        for kinds in stages:
            self.assertEqual(set(kinds) & seen, set())
            seen |= set(kinds)

    def test_every_kind_has_label_and_group(self):
        self.assertIn(underground.GROUP, PLACE_GROUPS)
        for k in underground.KINDS:
            self.assertEqual(KIND_GROUP[k], underground.GROUP, k)
            self.assertEqual(KIND_LABEL[k], underground.LABELS[k], k)

    def test_curated_sites(self):
        data = json.loads(underground.CURATED.read_text())
        qids = [s["qid"] for s in data["sites"]]
        self.assertEqual(len(qids), len(set(qids)))
        for s in data["sites"]:
            self.assertIn(s["kind"], underground.KINDS, s)
        self.assertTrue(all(q.startswith("Q") for q in data["still_open"] if not q.startswith("_")))


class MilitaryKinds(unittest.TestCase):
    def test_every_kind_has_label_and_group(self):
        self.assertIn(military.GROUP, PLACE_GROUPS)
        for k in military.KINDS:
            self.assertEqual(KIND_GROUP[k], military.GROUP, k)
            self.assertEqual(KIND_LABEL[k], military.LABELS[k], k)

    def test_burhs(self):
        burhs = json.loads(military.BURHS.read_text())["burhs"]
        self.assertGreaterEqual(len(burhs), 33)
        self.assertTrue(all(b["hides"] > 0 for b in burhs))

    def test_every_tour_theme_has_titles(self):
        from bidb import tours
        for theme in tours.THEMES:
            if theme != "trail":                   # trails take their route's name
                for mode in ("walk", "cycle", "drive"):
                    self.assertTrue(tours.title_for(theme, mode, "York"))

    def test_coastal_theme_labels_exist(self):
        from bidb.tours import COASTAL
        self.assertTrue(set(COASTAL) <= set(KIND_LABEL.values()))


class MuseumKinds(unittest.TestCase):
    def test_every_kind_has_label_and_group(self):
        from bidb import museums
        self.assertIn(museums.GROUP, PLACE_GROUPS)
        for k in museums.KINDS:
            self.assertEqual(KIND_GROUP[k], "Finds & treasures" if k == "kept" else museums.GROUP, k)
            self.assertIn(k, KIND_LABEL)

    def test_kind_from_classes(self):
        from bidb import museums
        self.assertEqual(museums._kind({"Q33506", "Q207694"}), "artmuseum")
        self.assertEqual(museums._kind({"Q33506"}), "museum")


class MappingMuseums(unittest.TestCase):
    def test_years(self):
        from bidb.mapping_museums import span_text, years
        self.assertIsNone(years("9999:9999"))
        self.assertEqual(years("2007:2017"), (2007, 2017))
        self.assertEqual(span_text((1971, 1971)), "1971")
        self.assertEqual(span_text((2007, 2017)), "2007–2017")

    def test_similar_names(self):
        from bidb.mapping_museums import similar
        self.assertTrue(similar("The Yorkshire Museum", "Yorkshire Museum"))
        self.assertTrue(similar("Museum of London Docklands", "London Docklands Museum"))
        self.assertFalse(similar("Science Museum", "Natural History Museum"))


class BridgeKinds(unittest.TestCase):
    def test_every_kind_has_label_and_group(self):
        from bidb import bridges
        self.assertIn(bridges.GROUP, PLACE_GROUPS)
        for k in bridges.KINDS:
            self.assertEqual(KIND_GROUP[k], bridges.GROUP, k)
            self.assertEqual(KIND_LABEL[k], bridges.LABELS[k], k)

    def test_kind_from_classes(self):
        from bidb import bridges
        self.assertEqual(bridges._kind({"Q12280", "Q7123018"}), "br_early")
        self.assertEqual(bridges._kind({"Q537127"}), "bridge")

    def test_group_stages_protect_each_other(self):
        from bidb import place_stage, underground
        self.assertTrue(set(underground.KINDS) <= place_stage.protected())


if __name__ == "__main__":
    unittest.main()
