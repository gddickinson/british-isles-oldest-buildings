import sqlite3
import unittest

from bidb import building_materials, material_map, material_stats
from bidb.material_text import Rules

ALIASES = material_map.load_aliases()
RULES = Rules(ALIASES)


def found(sentence):
    return set(RULES.in_sentence(sentence))


class TestRules(unittest.TestCase):
    def test_terms_and_cues(self):
        self.assertEqual(found("The church is built of flint with Bath stone dressings and a Welsh slate roof."),
                         {"flint", "bath-stone", "welsh-slate", "slate"})
        self.assertIn("timber-framing", found("It is a timber-framed house with a jettied upper storey."))
        self.assertIn("jetty", found("It is a timber-framed house with a jettied upper storey."))
        self.assertIn("brick", found("The house is built of red brick."))

    def test_not_the_building(self):
        self.assertNotIn("brick", found("The parish had several brick kilns in the 19th century."))
        self.assertNotIn("purbeck-marble", found("The church has a Purbeck marble font."))
        self.assertNotIn("cast-iron", found("Stone stairs with cast-iron balusters."))
        self.assertNotIn("rubble", found("The interior has been partly cleared of rubble."))
        self.assertNotIn("jetty", found("By 1923 there were eight jetties at the docks."))
        self.assertNotIn("earthfast-posts", found("It was during the digging of a post hole for the fence."))
        self.assertIn("earthfast-posts", found("Postholes show a timber building stood here."))
        self.assertNotIn("plate-glass", found("It is sometimes considered a plate glass university."))

    def test_register_sentences_about_other_structures(self):
        self.assertEqual(found("BOUNDARY WALLS: drystone walls and gateposts to entrance drive."), set())
        self.assertIn("dry-stone", found("The broch is a dry stone structure on a knoll."))

    def test_sections(self):
        art = {"s": [["", "The church is built of flint."], ["Churchyard", "The wall is of red brick."]]}
        blocks = RULES.article_blocks(art)
        self.assertEqual([w for w, _ in blocks], ["Wikipedia"])
        self.assertEqual(set(RULES.find(blocks)), {"flint"})


class TestAliases(unittest.TestCase):
    def test_no_problems(self):
        known = {m["id"] for m in building_materials.load()["materials"]}
        self.assertEqual(material_map.problems(ALIASES, known), [])

    def test_problems_found(self):
        bad = dict(ALIASES, wikidata={"Q1": "no-such"},
                   terms=[{"material": "nothing", "pattern": "x"}])
        self.assertEqual(len(material_map.problems(bad, {"brick"})), 2)


class TestLinker(unittest.TestCase):
    def test_order_and_evidence(self):
        linker = material_map.Linker(ALIASES, None, {"Q9": [("Q40089", "brick")]},
                                     {"T": {"s": [["Exterior", "The roof is thatched."]]}})
        out = {m: (via, where, ev) for m, via, _, where, ev in
               linker.link("Q9", [("HES", "Red brick with a thatched roof.")], "T", "")}
        self.assertEqual(out["brick"][0], "wikidata")
        self.assertEqual(out["thatch"][:2], ("register", "HES"))
        self.assertEqual(out["thatch"][2], "Red brick with a thatched roof.")
        self.assertNotIn("Exterior", str(out))
        out = linker.link(None, [], "Missing", "It is a cob cottage with a thatched roof.")
        self.assertEqual({m for m, *_ in out}, {"cob", "thatch"})

    def test_specific_stone_kept(self):
        general = material_map.general_of(building_materials.load())
        self.assertIn("limestone", general["bath-stone"])
        self.assertEqual(general["purbeck-marble"], {"limestone", "marble"})
        self.assertNotIn("ashlar", general)          # rubble is not general: both are kept
        linker = material_map.Linker(ALIASES, None, {}, {}, general)
        mats = lambda text: {m for m, *_ in linker.link(None, [], None, text)}
        self.assertEqual(mats("The church is built of Bath limestone ashlar."), {"bath-stone", "ashlar"})
        self.assertEqual(mats("The church has nave piers of Purbeck marble."), {"purbeck-marble"})
        self.assertEqual(mats("The church is built of limestone rubble."), {"limestone", "rubble"})
        self.assertEqual(mats("Walls of red sandstone with grey sandstone dressings."), {"red-sandstone"})


class TestGenericStones(unittest.TestCase):
    def test_stones(self):
        self.assertIn("sandstone", found("Coursed sandstone rubble with ashlar dressings."))
        self.assertIn("whinstone", found("Whinstone rubble with ashlar dressings."))
        self.assertIn("chalk", found("The church was built of flint and chalk rubble."))
        self.assertIn("chalk", found("Built of flint rubble with clunch dressings."))
        self.assertIn("marble", found("The portico has columns of white marble."))
        self.assertIn("coade-stone", found("The south front has Coade stone ornaments."))

    def test_not_the_building(self):
        self.assertNotIn("marble", found("The house has a fine marble chimneypiece in the drawing room."))
        self.assertNotIn("marble", found("The earlier font is of white marble."))
        self.assertNotIn("limestone", found("It was constructed on a karst landscape formed from limestone."))
        self.assertNotIn("sarsen", found("The builders chose not to use sarsens, which are naturally present."))
        self.assertNotIn("whinstone", found("FORMER WALLED GARDEN: random rubble whinstone wall to N of the drive."))
        self.assertNotIn("york-stone", found("The terrace is paved with York stone flags."))


MATS = {"materials": [{"id": "brick", "name": "Brick", "group": "Brick and tile", "kind": "material",
                       "period": {"from": 1220, "ongoing": True}},
                      {"id": "oak", "name": "Oak", "group": "Timber", "kind": "material",
                       "period": {"from": 1063, "ongoing": True, "earlier": True}}]}


def conn():
    c = sqlite3.connect(":memory:")
    c.execute("CREATE TABLE buildings (id, name, year_start, date_text, lat, lon, nation, county, status, "
              "date_confidence, image_thumb)")
    c.execute("CREATE TABLE places (id, name, year_start, date_text, lat, lon, nation, county, image_thumb)")
    c.execute(f"CREATE TABLE material_map ({', '.join(material_map.COLUMNS)})")
    c.executemany("INSERT INTO buildings VALUES (?,?,?,?,1,1,'England',NULL,?,?,NULL)", [
        ("b1", "Norman church", 1100, "1100", "Standing", "Recorded"),       # brick of a later phase
        ("b2", "Tudor hall", 1480, "1480", "Standing", "Recorded"),
        ("b3", "Brick tower", 1230, "1230", "Demolished / destroyed", "Recorded"),
        ("b4", "Hall", 1000, "1000", "Standing", "Recorded")])
    c.executemany("INSERT INTO places VALUES (?,?,?,?,1,1,'Wales',NULL,NULL)", [("p1", "Kiln", 1250, "1250")])
    c.executemany("INSERT INTO material_map VALUES (?,?,?,'wikipedia','x','Wikipedia','e')", [
        ("b1", "building", "brick"), ("b2", "building", "brick"), ("b3", "building", "brick"),
        ("p1", "place", "brick"), ("b4", "building", "oak")])
    return c


class TestStats(unittest.TestCase):
    def test_earliest_and_too_early(self):
        s = {x["id"]: x for x in material_stats.summary(conn(), MATS)}
        self.assertEqual(s["brick"]["too_early"], 1)
        self.assertEqual(s["brick"]["earliest"]["name"], "Tudor hall")     # Norman church begun before brick
        self.assertEqual(s["oak"]["earliest"]["name"], "Hall")             # earlier: a century's grace

    def test_detail_and_centuries(self):
        d = material_stats.detail(conn(), "brick", MATS)
        self.assertEqual(d["count"], 4)
        self.assertEqual([e["too_early"] for e in d["examples"]], [True, False, False, False])
        self.assertEqual(material_stats.by_century(conn(), MATS)["brick"], {1200: 2, 1400: 1})
        self.assertEqual(material_stats.century(-50), -100)
        self.assertEqual([m["id"] for m in material_stats.for_entity(conn(), "b4", MATS)], ["oak"])


if __name__ == "__main__":
    unittest.main()
