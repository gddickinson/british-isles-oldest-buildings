import unittest

from bidb import building_types, type_map

CONCEPTS = {
    "1": {"term": "CASTLE", "broader": [], "narrower": ["2", "3"]},
    "2": {"term": "MOTTE AND BAILEY", "broader": ["1"], "narrower": []},
    "3": {"term": "SHELL KEEP CASTLE", "broader": ["1"], "narrower": []},
    "4": {"term": "THEATRE", "broader": [], "narrower": []},
    "5": {"term": "RUINED CASTLE", "broader": ["1"], "narrower": []},
}
LOOKUP = {"castle": "1", "motte-and-bailey castle": "2", "theatre building": "4", "castle ruin thing": "5"}
TYPES = [
    {"id": "castle", "name": "Castle", "fish": "1", "period": {"from": 1066, "to": 1500}},
    {"id": "motte-and-bailey", "name": "Motte and bailey", "fish": "2", "period": {"from": 1066, "to": 1200}},
    {"id": "georgian-playhouse", "name": "Georgian playhouse", "fish": "4", "period": {"from": 1766, "to": 1819}},
    {"id": "broch", "name": "Broch", "fish": None, "period": {"from": -400, "to": 200}},
    {"id": "tower-house", "name": "Tower house", "fish": None, "period": {"from": 1300, "to": 1650}},
    {"id": "abroad-type", "name": "Trace italienne", "abroad": True, "period": {"from": 1500, "to": 1700}},
]
ALIASES = {
    "classes": {"English country house": "castle"},
    "within_period": ["georgian-playhouse"],
    "nations": {"broch": ["Scotland"]},
    "names": [{"pattern": r"\bCastle$", "type": "castle", "categories": ["Castle / fortification"],
               "kinds": ["fort"]}],
    "categories": {"Tower": "tower-house"},
    "place_kinds": {"tr_bank": "castle"},
    "place_types": {"Castle - tower house": "tower-house"},
    "skip_kinds": ["object"],
}


def matcher():
    m = type_map.Matcher(TYPES, ALIASES, concepts=CONCEPTS, lookup=lambda x: LOOKUP.get(x.lower()))
    m._under = lambda a, b: (a, b) == ("motte-and-bailey", "castle")
    return m


class TestMatcher(unittest.TestCase):
    def test_class_routes(self):
        m = matcher()
        self.assertEqual(m.for_class("castle"), [("castle", "type")])
        self.assertEqual(m.for_class("Broch"), [("broch", "type")])
        self.assertEqual(m.for_class("English country house"), [("castle", "alias")])
        self.assertEqual(m.for_class("motte-and-bailey castle"), [("motte-and-bailey", "fish")])
        self.assertEqual(m.for_class("castle ruin thing"), [("castle", "broader")])
        self.assertEqual(m.for_class("Trace italienne"), [])          # abroad types are not mapped
        self.assertEqual(m.for_class("built structure"), [])

    def test_most_specific_first(self):
        found = matcher().record("castle; motte-and-bailey castle", "Hen Domen", "Castle / fortification", 1070)
        self.assertEqual([t for t, _, _ in found], ["motte-and-bailey"])

    def test_within_period_and_nations(self):
        m = matcher()
        self.assertEqual(m.record("theatre building", "Theatre Royal", "Other", 1790)[0][0], "georgian-playhouse")
        self.assertEqual(m.record("theatre building", "Palace Theatre", "Other", 1900), [])
        self.assertEqual(m.record("theatre building", "A theatre", "Other", None), [])
        self.assertEqual(m.record("Broch", "Mousa", "Prehistoric", -100, "Scotland")[0][0], "broch")
        self.assertEqual(m.record("Broch", "A broch", "Prehistoric", -100, "Wales"), [])

    def test_name_rules(self):
        m = matcher()
        self.assertEqual(m.record("built structure", "Dunvegan Castle", "Castle / fortification", 1300)[0][1], "name")
        self.assertEqual(m.record("built structure", "Gate Piers, Baldoon Castle", "Castle / fortification", 1600), [])
        self.assertEqual(m.record("built structure", "Clinch Castle", "Castle / fortification", -300), [])
        self.assertEqual(m.record("built structure", "Maiden Castle", "Prehistoric monument", None), [])
        self.assertEqual(m.record("building", "Old Tower", "Tower", 1400)[0][:2], ("tower-house", "category"))

    def test_places(self):
        m = matcher()
        self.assertEqual(m.place("scheduled", "Castle - tower house", "X", None)[0][:2], ("tower-house", "alias"))
        self.assertEqual(m.place("scheduled", "Castle - motte-and-bailey castle", "X", None)[0][0], "motte-and-bailey")
        self.assertEqual(m.place("tr_bank", "Bank", "Bank of X", 1450)[0][:2], ("castle", "kind"))
        self.assertEqual(m.place("tr_bank", "Bank", "Bank of X", 1800), [])       # far outside the period
        self.assertEqual(m.place("fort", "Fort", "Pendennis Castle", 1540)[0][1], "name")


class TestCuratedAliases(unittest.TestCase):
    def test_no_problems(self):
        self.assertEqual(type_map.problems(type_map.load_aliases(), building_types.load()["types"]), [])

    def test_problems_found(self):
        bad = type_map.problems({"classes": {"x": "nope"}, "names": [{"pattern": "(", "type": "castle"}],
                                 "within_period": ["nope"], "not_in_tree": ["x"]}, TYPES)
        self.assertEqual(len(bad), 5)


if __name__ == "__main__":
    unittest.main()
