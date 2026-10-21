"""Building categories: (category, keywords) checked in order against Wikidata class labels.

Order matters: specific types ('public house', 'almshouse', 'gatehouse') must come before the
generic words they contain ('house'), and museums after castles (many castles are museums).
"""

CATEGORY_RULES = [
    ("Prehistoric monument", ["portal tomb", "court tomb", "wedge tomb", "passage tomb",
                              "megalithic tomb", "ogham stone", "chambered cairn", "long barrow",
                              "barrow", "dolmen", "quoit", "stone circle", "henge", "passage grave",
                              "megalith", "cromlech", "standing stone", "tomb", "burial", "cairn",
                              "souterrain", "rock art", "cup and ring", "cup-and-ring"]),
    ("Prehistoric dwelling", ["hillfort", "hill fort", "promontory fort", "ringfort", "ring fort",
                              "cashel", "rath", "broch", "roundhouse",
                              "wheelhouse", "crannog", "dun ", "neolithic settlement",
                              "prehistoric settlement", "farmstead"]),
    ("Roman structure", ["roman fort", "roman villa", "roman", "pharos", "mithraeum",
                         "amphitheatre"]),
    ("Cathedral", ["cathedral", "minster"]),
    ("Abbey / monastery", ["abbey", "priory", "monastery", "round tower", "monastic site", "friary",
                           "nunnery", "convent", "cloister", "chapter house", "preceptory",
                           "grange"]),
    ("Synagogue / mosque / meeting house", ["synagogue", "mosque", "meeting house", "quaker",
                                            "friends meeting"]),
    ("Church / chapel", ["church", "chapel", "kirk", "oratory", "chantry", "place of worship",
                         "religious building", "baptistery"]),
    ("Public house / inn", ["public house", "pub", "inn", "tavern", "coaching inn", "alehouse",
                            "bar"]),
    ("Hotel", ["hotel"]),
    ("Almshouse / hospital", ["almshouse", "hospital", "infirmary", "leper", "lazar house",
                              "hospice"]),
    ("School / college", ["school", "college", "university", "academy", "grammar school"]),
    ("Library", ["library"]),
    ("Theatre / entertainment", ["theatre", "cinema", "concert hall", "music hall", "opera house",
                                 "assembly rooms", "playhouse"]),
    ("Prison", ["prison", "gaol", "jail"]),
    ("Railway", ["railway station", "train station", "station building", "railway viaduct",
                 "viaduct", "engine shed", "railway"]),
    ("Lighthouse", ["lighthouse"]),
    ("Mill", ["windmill", "watermill", "water mill", "tide mill", "mill"]),
    ("Post office", ["post office"]),
    ("Bank / office", ["bank", "office building", "office"]),
    ("Observatory / science", ["observatory", "laboratory"]),
    ("Market / shop", ["market hall", "market cross", "market", "shop", "store", "arcade"]),
    ("Civic building", ["town hall", "moot hall", "guildhall", "guild hall", "tolbooth",
                        "courthouse", "shire hall", "custom house", "exchange"]),
    ("Castle / fortification", ["castle", "keep", "tower house", "fortification", "fortified",
                                "fort", "fortress", "bastle", "gatehouse", "town wall",
                                "city wall", "city gate", "barbican", "motte", "peel tower",
                                "pele", "defensive", "tower"]),
    ("Palace / manor house", ["palace", "manor", "hall house", "great hall", "country house",
                              "mansion", "hall", "bishop's palace"]),
    ("House / domestic", ["house", "cottage", "dwelling", "residential", "farmhouse", "townhouse",
                          "vicarage", "rectory", "wealden", "tenement", "terrace"]),
    ("Museum", ["museum", "gallery"]),
    ("Agricultural / industrial", ["barn", "dovecote", "granary", "farm", "kiln", "forge",
                                   "warehouse", "factory", "brewery", "distillery", "works",
                                   "glasshouse", "greenhouse"]),
    ("Bridge / infrastructure", ["bridge", "causeway", "aqueduct", "canal", "dam", "well",
                                 "conduit", "road", "harbour", "quay", "pier"]),
    ("Cross / carved stone", ["high cross", "celtic cross", "pictish stone", "carved stone",
                              "cross slab", "cross"]),
    ("Ruin / archaeological site", ["ruin", "archaeological", "site"]),
]

CATEGORY_ORDER = [c for c, _ in CATEGORY_RULES] + ["Other structure"]

# Eight colour groups for maps and charts (fixed order = fixed colour slot); rest -> "Other"
CATEGORY_GROUPS = [
    ("Religious", ["Cathedral", "Abbey / monastery", "Church / chapel",
                   "Synagogue / mosque / meeting house", "Cross / carved stone"]),
    ("Fortification", ["Castle / fortification"]),
    ("Prehistoric", ["Prehistoric monument", "Prehistoric dwelling"]),
    ("Domestic", ["Palace / manor house", "House / domestic"]),
    ("Roman", ["Roman structure"]),
    ("Commercial & civic", ["Public house / inn", "Hotel", "Market / shop", "Civic building",
                            "Bank / office", "Post office"]),
    ("Institutions & culture", ["School / college", "Library", "Almshouse / hospital",
                                "Theatre / entertainment", "Prison", "Museum",
                                "Observatory / science"]),
    ("Industry & transport", ["Mill", "Agricultural / industrial", "Bridge / infrastructure",
                              "Railway", "Lighthouse"]),
]
GROUP_ORDER = [g for g, _ in CATEGORY_GROUPS] + ["Other"]
_GROUP_OF = {c: g for g, cats in CATEGORY_GROUPS for c in cats}


def group_for(category):
    return _GROUP_OF.get(category, "Other")
