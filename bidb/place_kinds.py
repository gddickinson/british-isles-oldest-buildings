"""Places of interest that are not (or not only) buildings: what to fetch and how to group it.

Each kind is selected from Wikidata by class (optionally with subclasses), designation or a
bounding box, and grouped into eight colour groups for the map. QIDs verified against Wikidata
English labels (October 2026).
"""

# Fixed order = fixed colour slot on maps and charts
PLACE_GROUPS = ["Battles & sieges", "Archaeological sites", "Lost places", "Parks, gardens & trees",
                "Industrial heritage", "Finds & treasures", "Plaques & people", "History events",
                "Legends & literature", "Maritime heritage", "Victorian era", "Underground",
                "Military heritage", "Museums & collections"]

# Prehistoric / early monument types. Items with a photo or a Wikipedia article join the main
# building catalogue; the rest are shown as "Archaeological sites" places.
ARCH_ROOTS = {
    "Q744099": "Hillfort", "Q1935728": "Stone circle", "Q2330559": "Standing stone",
    "Q1035294": "Henge", "Q1652352": "Long barrow", "Q2046325": "Round barrow",
    "Q585490": "Chambered cairn", "Q82137": "Broch", "Q91818": "Dun", "Q91759": "Crannog",
    "Q137937": "Souterrain", "Q92383": "Ringfort", "Q1666255": "Pictish stone",
    "Q2016147": "Ogham stone", "Q373661": "Cup and ring mark", "Q1211146": "Rock art",
    "Q918230": "Roman villa", "Q92062": "Motte-and-bailey castle",
}

# geo: how the item is tied to the British Isles
#   country     - P17 is one of the British Isles jurisdictions
#   located     - P17, or a location (P276) in one of them; coordinates may come from the location
#   discovered  - location of discovery (P189) in one of them (finds)
#   box         - coordinates inside the British Isles bounding box (trees have no P17)
# require: "media" keeps only items with a photo or an English Wikipedia article
KINDS = [
    {"key": "battle", "label": "Battle", "group": "Battles & sieges",
     "classes": ["Q178561"], "subclasses": True, "geo": "located", "date": ["P585", "P580"]},
    {"key": "siege", "label": "Siege", "group": "Battles & sieges",
     "classes": ["Q188055"], "subclasses": False, "geo": "located", "date": ["P585", "P580"]},
    {"key": "archaeology", "label": "Archaeological site", "group": "Archaeological sites",
     "classes": list(ARCH_ROOTS), "subclasses": True, "geo": "country", "date": ["P571"],
     "per_class": True},
    {"key": "holy_well", "label": "Holy well", "group": "Archaeological sites",
     "classes": ["Q1371047"], "subclasses": True, "geo": "country", "date": ["P571"]},
    {"key": "hill_figure", "label": "Hill figure", "group": "Archaeological sites",
     "classes": ["Q2918952"], "subclasses": True, "geo": "country", "date": ["P571"]},
    {"key": "roman_road", "label": "Roman road", "group": "Archaeological sites",
     "classes": ["Q194029"], "subclasses": False, "geo": "country", "date": ["P571"]},
    {"key": "deserted_village", "label": "Deserted village", "group": "Lost places",
     "classes": ["Q21751582", "Q350895"], "subclasses": True, "geo": "country",
     "date": ["P571", "P576"]},
    {"key": "shipwreck", "label": "Shipwreck", "group": "Lost places",
     "classes": ["Q852190"], "subclasses": False, "geo": "country", "require": "media",
     "date": ["P576", "P571"]},
    {"key": "park_garden", "label": "Registered park or garden", "group": "Parks, gardens & trees",
     "designations": ["Q26789527", "Q111987264", "Q97819899", "Q76199821"], "geo": "country",
     "date": ["P571"]},
    {"key": "tree", "label": "Notable tree", "group": "Parks, gardens & trees",
     "classes": ["Q10884"], "subclasses": True, "geo": "box", "date": ["P571"]},
    {"key": "industrial", "label": "Industrial site", "group": "Industrial heritage",
     "classes": ["Q820477", "Q1342377", "Q12284", "Q474", "Q181348", "Q44377", "Q10832530",
                 "Q185187", "Q38720", "Q59772", "Q628155"],
     "subclasses": False, "geo": "country", "require": "media", "date": ["P571"],
     "per_class": True},
    {"key": "find", "label": "Find or hoard", "group": "Finds & treasures",
     "classes": None, "geo": "discovered", "date": ["P575", "P571"]},
    {"key": "plaque", "label": "Commemorative plaque", "group": "Plaques & people",
     "classes": ["Q721747", "Q885849"], "subclasses": True, "geo": "country",
     "date": ["P571"]},
]
KIND_LABEL = {k["key"]: k["label"] for k in KINDS}
KIND_LABEL.update({"object": "Object in a building", "event": "History event",
                   "scheduled": "Scheduled or recorded monument"})
KIND_GROUP = {k["key"]: k["group"] for k in KINDS}
KIND_GROUP.update({"object": "Finds & treasures", "event": "History events",
                   "scheduled": "Archaeological sites"})
# added after the places build by bidb.lore_places
KIND_LABEL.update({"haunted": "Reportedly haunted place", "legend": "Place of legend", "holywell": "Holy well",
                   "literary": "Literary place"})
KIND_GROUP.update({k: "Legends & literature" for k in ("haunted", "legend", "holywell", "literary")})
# added by bidb.maritime
KIND_LABEL.update({"harbour": "Harbour or port", "dock": "Dock or wharf", "shipyard": "Shipyard or slipway",
                   "ropewalk": "Ropewalk", "customhouse": "Custom house", "lighthouse": "Lighthouse",
                   "lifeboat": "Lifeboat station", "naval": "Naval base or dockyard", "museumship": "Museum ship",
                   "shipbuilder": "Shipbuilder"})
KIND_GROUP.update({k: "Maritime heritage" for k in ("harbour", "dock", "shipyard", "ropewalk", "customhouse",
                                                    "lighthouse", "lifeboat", "naval", "museumship", "shipbuilder")})
# added by bidb.era_places
KIND_LABEL.update({"mill": "Mill or factory", "mine": "Mine or quarry", "ironworks": "Ironworks or foundry",
                   "canal": "Canal, lock or aqueduct", "railway": "Railway station, viaduct or tunnel",
                   "engine": "Engine house, pumping station or works", "kiln": "Kiln",
                   "ironbridge": "Iron or suspension bridge", "warehouse": "Warehouse or brewery",
                   "victorian_public": "Victorian public building",
                   "victorian_leisure": "Victorian pier, glasshouse or tram depot", "victorian_style": "Victorian building"})
KIND_GROUP.update({k: "Industrial heritage" for k in ("mill", "mine", "ironworks", "canal", "railway", "engine", "kiln",
                                                      "ironbridge", "warehouse")})
KIND_GROUP.update({k: "Victorian era" for k in ("victorian_public", "victorian_leisure", "victorian_style")})
# added by bidb.underground
KIND_LABEL.update({"tube": "Underground or metro station", "ghost": "Disused underground station", "tunnel": "Tunnel",
                   "shelter": "Shelter or bunker", "cave": "Cave or cavern", "ug_mine": "Mine", "icehouse": "Ice house",
                   "grotto": "Grotto", "catacomb": "Catacomb, crypt or vault", "sewer": "Sewer, cistern or water tunnel",
                   "ug_railway": "Underground railway"})
KIND_GROUP.update({k: "Underground" for k in ("tube", "ghost", "tunnel", "shelter", "cave", "ug_mine", "icehouse",
                                              "grotto", "catacomb", "sewer", "ug_railway")})

# British Isles bounding box (south, west, north, east): drops overseas territories
BOX = (49.1, -11.0, 61.1, 2.1)

# Find classes that are not artefacts (fossils, taxa, elements, people, ogham stones handled above)
FIND_EXCLUDE_ROOTS = ["Q16521", "Q11344", "Q5", "Q40614", "Q2016147", "Q106602575",
                      "Q839954", "Q2159241", "Q85869058", "Q75913269", "Q104450895"]


def in_box(lat, lon):
    s, w, n, e = BOX
    return lat is not None and s <= lat <= n and w <= lon <= e
# added by bidb.military
KIND_LABEL.update({"burh": "Saxon burh", "tower": "Martello or defensive tower", "fort": "Fort or fortification",
                   "battery": "Gun or anti-aircraft battery", "barracks": "Barracks, drill hall or camp",
                   "pillbox": "Pillbox or anti-tank defence", "radar": "Radar station, sound mirror or signal station",
                   "airfield": "Military airfield", "powcamp": "Prisoner-of-war camp", "defenceline": "Defence or stop line",
                   "memorial": "War memorial"})
KIND_GROUP.update({k: "Military heritage" for k in ("burh", "tower", "fort", "battery", "barracks", "pillbox", "radar",
                                                    "airfield", "powcamp", "defenceline", "memorial")})
# added by bidb.museums
KIND_LABEL.update({"museum": "Museum", "artmuseum": "Art museum or gallery", "housemuseum": "Historic house museum",
                   "milmuseum": "Military museum", "transmuseum": "Transport or maritime museum",
                   "scimuseum": "Science, natural history or industry museum", "library": "Library or archive",
                   "kept": "Object in a museum"})
KIND_GROUP.update({k: "Museums & collections" for k in ("museum", "artmuseum", "housemuseum", "milmuseum", "transmuseum",
                                                        "scimuseum", "library")})
KIND_GROUP["kept"] = "Finds & treasures"
