"""Historic map layers (georeferenced tiles), shared by the GUI and app.historic_build.

Each layer: key, label, date, coverage bounds [W, S, E, N], zooms, attribution, one or more online
tile URLs (tried in order for the bundled copy; all drawn online), and the zoom range bundled into
the hosted copy (None = online only). Endpoints tested 2026-10-20.
"""
NLS = "https://mapseries-tilesets.s3.amazonaws.com/"
ALLMAPS = "https://allmaps.xyz/maps/{id}/{{z}}/{{x}}/{{y}}.png"
NLS_ATTR = 'Historic map: <a href="https://maps.nls.uk/">National Library of Scotland</a> (CC-BY)'
RUMSEY_ATTR = ('<a href="https://www.davidrumsey.com/">David Rumsey Map Collection</a>, '
               'David Rumsey Map Center, Stanford Libraries (CC BY-NC-SA 3.0); georeferencing: Allmaps')
GB = [-8.3, 49.7, 2.2, 61.0]
IRELAND = [-10.8, 51.2, -5.3, 55.6]
ISLES = [-11.2, 49.4, 2.9, 61.0]

LAYERS = [
    {"key": "os6inch", "label": "OS six-inch, Great Britain", "date": "1888–1913", "bounds": GB,
     "max": 17, "urls": [NLS + "os/6inchsecond/{z}/{x}/{y}.png"], "attr": NLS_ATTR, "bundle": None},
    {"key": "os1inch", "label": "OS one-inch 2nd edition, Great Britain", "date": "1890s–1900s",
     "bounds": GB, "max": 16, "urls": [NLS + "1inch_2nd_ed/{z}/{x}/{y}.png"], "attr": NLS_ATTR, "bundle": None},
    {"key": "bartholomew", "label": "Bartholomew half-inch, Great Britain", "date": "1897–1907",
     "bounds": GB, "max": 15, "urls": [NLS + "bartholomew_great_britain/{z}/{x}/{y}.png"],
     "attr": NLS_ATTR, "bundle": [5, 9]},
    {"key": "oldseries", "label": "OS Old Series one-inch, England & Wales", "date": "1805–74",
     "bounds": [-6.2, 49.7, 2.2, 55.95], "max": 9, "urls": [NLS + "os/one-inch-old-series-all/{z}/{x}/{y}.png"],
     "attr": NLS_ATTR, "bundle": [5, 9]},
    {"key": "roy", "label": "Roy Military Survey of Scotland", "date": "1747–55",
     "bounds": [-7.85, 54.4, -0.95, 59.1], "min": 5, "max": 14,
     "urls": [NLS + "roy/highlands/{z}/{x}/{y}.png", NLS + "roy/lowlands/{z}/{x}/{y}.png"],
     "attr": NLS_ATTR + "; Roy Military Survey © British Library", "bundle": [5, 10]},
    {"key": "ireland1inch", "label": "OS one-inch 1st edition, Ireland", "date": "1850s–90s",
     "bounds": [-10.8, 51.2, -4.9, 55.6], "max": 16, "urls": [NLS + "os/ireland_1inch_1st_hills/{z}/{x}/{y}.png"],
     "attr": NLS_ATTR, "bundle": [5, 9]},
    {"key": "irelandbart", "label": "Bartholomew quarter-inch, Ireland", "date": "1940",
     "bounds": IRELAND, "max": 12, "urls": [NLS + "ireland/bartholomew/{z}/{x}/{y}.png"], "attr": NLS_ATTR,
     "bundle": None},
    {"key": "isleofman", "label": "OS six-inch, Isle of Man", "date": "1860s–70s",
     "bounds": [-4.95, 53.98, -4.28, 54.5], "max": 17, "urls": [NLS + "os/six-inch-isle-of-man/{z}/{x}/{y}.png"],
     "attr": NLS_ATTR, "bundle": None},
    {"key": "channel", "label": "OS two-inch, Channel Islands", "date": "c. 1900",
     "bounds": [-2.75, 49.1, -1.96, 49.55], "max": 15, "urls": [NLS + "channel-islands/two-inch/{z}/{x}/{y}.png"],
     "attr": NLS_ATTR, "bundle": None},
    {"key": "gough", "label": "Gough Map", "date": "c. 1360", "bounds": [-6.32, 49.5, 1.8, 59.0], "max": 9,
     "urls": ["https://warper.wmflabs.org/maps/tile/252/{z}/{x}/{y}.png"],
     "attr": 'Gough Map (Bodleian Library, public domain); georeferencing: '
             '<a href="https://warper.wmflabs.org/maps/252">Wikimaps Warper</a>', "bundle": [5, 8]},
    {"key": "smith", "label": "William Smith geological map", "date": "1815",
     "bounds": [-5.8, 49.9, 1.8, 55.9], "max": 12,
     "urls": ["https://warper.wmflabs.org/maps/tile/150/{z}/{x}/{y}.png"],
     "attr": '"Strata of England and Wales", William Smith 1815 (Yorkshire Museum, public domain); '
             'georeferencing: <a href="https://warper.wmflabs.org/maps/150">Wikimaps Warper</a>', "bundle": [5, 8]},
    {"key": "romana", "label": "Britannia Romana (historical atlas)", "date": "Roman Britain",
     "bounds": [-6.02, 49.7, 1.74, 55.27], "max": 10, "urls": [ALLMAPS.format(id="c8e62470ddd87013")],
     "attr": RUMSEY_ATTR, "bundle": [5, 8]},
    {"key": "anglosaxon", "label": "Kingdoms of the Anglo-Saxons (historical atlas)", "date": "c. 600–800",
     "bounds": [-6.15, 49.86, 1.8, 55.82], "max": 10, "urls": [ALLMAPS.format(id="d2244e7f51d79d80")],
     "attr": RUMSEY_ATTR, "bundle": [5, 8]},
    {"key": "isles900", "label": "The British Isles in 900 (historical atlas)", "date": "c. 900",
     "bounds": [-11.03, 49.45, 2.84, 59.61], "max": 10, "urls": [ALLMAPS.format(id="e6c3c849b608b349")],
     "attr": RUMSEY_ATTR, "bundle": [5, 8]},
    {"key": "ortelius", "label": "Britannicarum Insularum (Ortelius type)", "date": "16th century",
     "bounds": [-10.17, 49.92, 3.17, 60.69], "max": 10, "urls": [ALLMAPS.format(id="179246068dd62545")],
     "attr": RUMSEY_ATTR, "bundle": [5, 8]},
]
TOWN_PREFIXES = ["towns/", "os/town-england/", "town_england/"]
