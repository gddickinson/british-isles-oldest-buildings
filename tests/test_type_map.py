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
    "place_types": {"Castle - tower house": "tower-house", "hut circle, roundhouse": "broch"},
    "texts": [{"pattern": r"\bshell keep\b", "type": "motte-and-bailey", "refines": ["castle"],
               "categories": ["Castle / fortification"], "kinds": ["scheduled"]},
              {"pattern": r"^[^|]*\bPlayhouse\b", "type": "georgian-playhouse", "slack": 0, "kinds": ["theatre"]}],
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


    def test_label_parts(self):
        parts = type_map.Matcher.label_parts("Prehistoric domestic: hut circle, roundhouse; Secular: hall")
        self.assertEqual(parts, ["Prehistoric domestic: hut circle, roundhouse; Secular: hall",
                                 "hut circle, roundhouse", "hall"])
        self.assertEqual(matcher().place("scheduled", "hut circle, roundhouse; Secular: farmstead", "X", -100,
                                         "Scotland")[0][:2], ("broch", "alias"))

    def test_text_rules(self):
        m = matcher()
        text = m.text_of("Orford", "castle in Suffolk", "Orford is a castle. It has a shell keep. Later on, more.")
        self.assertEqual(text, "Orford | castle in Suffolk | Orford is a castle. It has a shell keep.")
        # refines a general type found by class; the refined type is dropped
        self.assertEqual([t for t, _, _ in m.record("castle", "Orford", "Castle / fortification", 1170,
                                                    text=text)], ["motte-and-bailey"])
        # never outside its categories, never over a type it does not refine
        self.assertEqual(m.record("castle", "Orford", "Church / chapel", 1170, text=text)[0][0], "castle")
        self.assertEqual(m.record("Broch", "B", "Castle / fortification", -100, "Scotland", text=text)[0][0],
                         "broch")
        # places only of the rule's kinds; `slack` 0 keeps to the type's own period
        self.assertEqual(m.place("scheduled", None, "X", 1170, text=text)[0][:2], ("motte-and-bailey", "text"))
        self.assertEqual(m.place("fort", None, "X", 1170, text=text), [])
        self.assertEqual(m.place("theatre", None, "Playhouse", 1790, text="Playhouse")[0][0], "georgian-playhouse")
        self.assertEqual(m.place("theatre", None, "Playhouse", 1830, text="Playhouse"), [])


class TestCuratedAliases(unittest.TestCase):
    def test_no_problems(self):
        self.assertEqual(type_map.problems(type_map.load_aliases(), building_types.load()["types"]), [])

    def test_problems_found(self):
        bad = type_map.problems({"classes": {"x": "nope"}, "names": [{"pattern": "(", "type": "castle"}],
                                 "within_period": ["nope"], "not_in_tree": ["x"],
                                 "nations": {"broch": ["Ireland"]},
                                 "texts": [{"pattern": "[", "type": "castle", "refines": ["nope"]}]}, TYPES)
        self.assertEqual(len(bad), 8)
        bad = type_map.problems({"not_types": {"Q1": {"types": ["nope"]}}}, TYPES)
        self.assertEqual(len(bad), 2)                 # unknown type, no reason

    def test_not_types_drops_a_wrong_class(self):
        # Grime's Graves: Wikidata's class "round barrow" on a flint mine; a reviewed entry drops it
        import sqlite3
        c = sqlite3.connect(":memory:")
        c.execute("CREATE TABLE buildings (id, classes, name, category, year_start, nation, description, wikipedia_extract)")
        c.execute("CREATE TABLE places (id, kind, type, name, year_start, nation, description, wikipedia_extract)")
        c.executemany("INSERT INTO places VALUES (?,?,?,?,?,?,?,?)",
                      [("p1", "scheduled", "Castle - tower house", "A", 1400, None, None, None),
                       ("p2", "scheduled", "Castle - tower house", "B", 1400, None, None, None)])
        m = type_map.Matcher(TYPES, dict(ALIASES, not_types={"p2": {"types": ["tower-house"], "reason": "r"}}),
                             concepts=CONCEPTS, lookup=lambda x: LOOKUP.get(x.lower()))
        self.assertEqual([r[0] for r in type_map.rows(c, m)], ["p1"])


if __name__ == "__main__":
    unittest.main()


class TestGeneralTypes(unittest.TestCase):
    """BT1d: general types (theatre, school), forms of them through variant links, uses of a building."""
    TYPES = TYPES + [
        {"id": "theatre", "name": "Theatre", "fish": "4", "period": {"from": 140, "ongoing": True}},
        {"id": "school", "name": "School", "fish": None, "period": {"from": 597, "ongoing": True}},
        {"id": "grammar-school", "name": "Grammar school", "fish": None, "period": {"from": 1100, "ongoing": True}},
        {"id": "museum", "name": "Museum", "fish": None, "period": {"from": 1683, "ongoing": True}},
    ]
    LINKS = [{"from": "school", "to": "grammar-school", "kind": "variant"},
             {"from": "theatre", "to": "georgian-playhouse", "kind": "variant"}]
    ALIASES = dict(ALIASES, secondary=["museum", "school"],
                   names=ALIASES["names"] + [{"pattern": r"\bGrammar School$", "type": "grammar-school",
                                               "categories": ["School / college"], "kinds": ["pi_school"]}])

    def matcher(self):
        m = type_map.Matcher(self.TYPES, self.ALIASES, concepts=CONCEPTS, lookup=lambda x: LOOKUP.get(x.lower()),
                             links=self.LINKS)
        m._under = lambda a, b: False
        return m

    def test_shared_concept_goes_to_the_dated_type_when_the_year_fits(self):
        m = self.matcher()
        self.assertEqual(m.record("theatre", "Theatre Royal", "Other", 1790)[0][0], "georgian-playhouse")
        self.assertEqual([t for t, _, _ in m.record("theatre", "Apollo", "Other", 1930)], ["theatre"])

    def test_a_form_replaces_its_general_type(self):
        m = self.matcher()
        self.assertEqual([t for t, _, _ in m.record("school; grammar school", "X", "School / college", 1550)],
                         ["grammar-school"])
        found = m.place("pi_school", "School", "Hulme Grammar School", 1611)
        self.assertEqual([t for t, _, _ in found], ["grammar-school"])

    def test_uses_rank_after_the_building(self):
        m = self.matcher()
        self.assertEqual([t for t, _, _ in m.record("museum; castle", "Y Castle", "Museum", 1300)],
                         ["castle", "museum"])


class TestRailwayRules(unittest.TestCase):
    """BT1d tramways, funiculars, inclines and signal boxes: the curated rules on real names and descriptions."""
    def matcher(self):
        data = building_types.load()
        return type_map.Matcher(data["types"], type_map.load_aliases(), concepts={}, lookup=lambda x: None,
                                links=data["links"])

    def place(self, m, kind, name, desc=None, year=None, label=None):
        found = m.place(kind, label, name, year, text=m.text_of(name, desc, None))
        return found[0][0] if found else None

    def test_places(self):
        m = self.matcher()
        self.assertEqual(self.place(m, "in_rail", "Forsinard Station", "railway signal box in Highland"), "signal-box")
        self.assertEqual(self.place(m, "in_rail", "West Cliff Railway", "funicular in Bournemouth", 1908),
                         "funicular-railway")
        self.assertEqual(self.place(m, "in_rail", "Great Orme Tramway", "Cable tramway in North Wales", 1902),
                         "funicular-railway")
        self.assertEqual(self.place(m, "ino_rail", "Blackpool Tramway",
                                    "one of the oldest electric tramways in the world", 1885), "street-tramway")
        self.assertEqual(self.place(m, "ino_rail", "Surrey Iron Railway", "early plateway in south London", 1803),
                         "plateway")
        self.assertEqual(self.place(m, "scheduled", "Trefil Tramroad", label="Tramroad", year=1650), "plateway")
        self.assertEqual(self.place(m, "scheduled", "Coalport Inclined Plane"), "canal-inclined-plane")
        self.assertEqual(self.place(m, "in_rail", "Beckhole Incline", "disused railway incline"),
                         "railway-inclined-plane")
        self.assertIsNone(self.place(m, "in_rail", "Lickey Incline", "stretch of 2 miles of 1 in 37.7"))

    def test_staircase_lock_over_a_wrong_class(self):
        m = self.matcher()
        found = m.record("lock; canal inclined plane", "Bingley Five Rise Locks", "Bridge / infrastructure", 1774,
                         text="Bingley Five Rise Locks | staircase lock on the Leeds and Liverpool Canal")
        self.assertEqual(found[0][0], "pound-lock")


class TestBridgeRules(unittest.TestCase):
    """Bridge places by kind, canal aqueducts, swing, bascule and transporter bridges (curated rules)."""
    matcher, place = TestRailwayRules.matcher, TestRailwayRules.place

    def test_bridges(self):
        m = self.matcher()
        self.assertEqual(self.place(m, "br_rail", "Ynysafan Tramroad Bridge", label="Railway viaduct or bridge"),
                         "bridge")
        self.assertEqual(self.place(m, "bridge", "Old Ness Bridge", year=1684, label="Bridge (gone or closed)"),
                         "bridge")
        self.assertEqual(self.place(m, "br_aqueduct", "Dove Aqueduct", "canal aqueduct over the River Dove"),
                         "canal-aqueduct")
        self.assertEqual(self.place(m, "br_aqueduct", "Carmuirs Aqueduct"), "canal-aqueduct")
        self.assertEqual(self.place(m, "br_aqueduct", "Loch Chon Aqueduct No 3 (Former Glasgow Corporation Water "
                                    "Works), Dow of Chon", "aqueduct bridge carrying the Katrine aqueduct"), "bridge")
        self.assertEqual(self.place(m, "br_aqueduct", "pipeline bridge over the Calder and Hebble Navigation"),
                         "bridge")
        self.assertEqual(self.place(m, "br_moving", "Tomnahurich Swing Bridge", "swing bridge in Inverness"),
                         "swing-bridge")
        self.assertEqual(self.place(m, "br_moving", "Starks Bridge", "Grade II* listed canal lift bridge"),
                         "bascule-bridge")
        self.assertEqual(self.place(m, "bridge", "Middlesbrough Transporter Bridge", year=1911), "transporter-bridge")
        self.assertNotEqual(self.place(m, "in_power", "Former transporter bridge power house"), "transporter-bridge")
