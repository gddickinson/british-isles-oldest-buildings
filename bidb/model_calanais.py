"""3D model of the Calanais (Callanish) Standing Stones (roadmap SH3d), from `data/curated/models/calanais.json`.

Every stone stands where OpenStreetMap maps it (49 ways tagged historic=stone, positions only). The ring is found by
fitting: the 13 stones 5-7.5 m from a centre 0.8 m east of the stone nearest it, the monolith (Stone 29, 0.8 m west of
the ring's centre: Ashmore). The rest are grouped by their direction from the ring: the avenue to the north, the
east, south and west rows. Heights: the monolith 4.8 m, the ring stones their published average 3 m; most other stones
have no published height and are drawn 2 m (`DERIVED`). The view "before 1857" buries them in the 1.5 m of peat
cleared that year. The moon at the major standstill rises out of the "Sleeping Beauty" hills over the real skyline.
"""
import math

from . import model_geometry as G
from . import osgrid
from .models3d import cite, research

DERIVED = [
    "Positions are the 49 stones mapped on OpenStreetMap (one per standing stone, the Pontings' count of 48 and Stone "
    "33a); their shapes are not mapped, so each is drawn as a slab 1 m long and 0.35 m thick, set along its row or round "
    "the ring.",
    "The ring stones are drawn at their published average height (3 m); the monolith 4.8 m, 1.5 m wide and 0.3 m thick "
    "with its broad faces north and south. No height is published for most avenue and row stones: they are drawn 2 m.",
    "Stones are numbered only where certain (the monolith, Stone 29); the others are named by group.",
    "The chambered cairn is drawn as a low cairn 6.4 m long between the monolith and the east of the ring, its chamber "
    "four uprights 1.1 m high; its roof is not known.",
    "Before 1857: the peat (1.5 m) is drawn as a level surface over the whole site.",
]


def _stones():
    lat0, lon0 = osgrid.to_latlon("NB 21301 32992")
    els = G.osm(lat0, lon0, 200, ["[historic=stone]", "[historic=standing_stone]", "[historic=menhir]"])
    pts = [G.centroid([G.local(a, b, lat0, lon0) for a, b in e["points"]]) for e in els]
    best = None
    for i in range(-150, 151):                     # the centre with the most stones 5.2-7.2 m from it
        for j in range(-50, 351):
            c = (i * 0.1, j * 0.1)
            ds = [math.dist(p, c) for p in pts]
            score = sum(5.2 < d < 7.2 for d in ds) + 3 * sum(d < 1.5 for d in ds)
            if best is None or score > best[0]:
                best = (score, c)
    mono = min(pts, key=lambda p: math.dist(p, best[1]))
    centre = (mono[0] + 0.8, mono[1])               # the monolith is 0.8 m west of the ring's centre
    lat = lat0 + centre[1] / 110574
    lon = lon0 + centre[0] / (111320 * math.cos(math.radians(lat0)))
    local = [(p[0] - centre[0], p[1] - centre[1]) for p in pts]
    return lat, lon, local, (mono[0] - centre[0], mono[1] - centre[1])


def groups_of(pts):
    """Each stone (metres from the ring's centre) → its part of the monument: the monolith (nearest the centre), the
    ring (the 13 next nearest), then by direction: the avenue to the north, the east, south and west rows, and the
    stones within 10 m of the centre that are in none of them (Stones 9 and 35)."""
    order = sorted(range(len(pts)), key=lambda i: math.hypot(*pts[i]))
    out = {order[0]: "monolith", **{i: "ring" for i in order[1:14]}}
    for i in order[14:]:
        d, az = math.hypot(*pts[i]), G.bearing((0, 0), pts[i])
        if az > 330 or az < 30:
            g = "avenue"
        elif 55 <= az <= 115:
            g = "east"
        elif 165 <= az <= 195:
            g = "south"
        elif 245 <= az <= 295:
            g = "west"
        else:
            g = "outlier"
        on_line = g == "avenue" or (g == "south" and abs(pts[i][0]) < 2.5) or (g == "east" and abs(pts[i][1]) < 2.5)
        out[i] = g if on_line or d >= 10 else "outlier"
    return [out[i] for i in range(len(pts))]


TITLES = {"ring": "Ring stone", "avenue": "Avenue stone", "east": "East row stone", "south": "South row stone",
          "west": "West row stone", "outlier": "Outlying stone"}


def spec():
    r = research("calanais")
    f = r["facts"]
    el = {e["id"]: e for e in r["elements"]}
    cites = lambda *keys: [c for k in keys for c in cite(r, f[k]["cites"])]        # noqa: E731
    lat, lon, pts, mono = _stones()
    groups = {}
    for p, g in zip(pts, groups_of(pts)):
        groups.setdefault(g, []).append(p)
    # Direction of each row (the line through its stones), for setting the slabs along it.
    def row_az(ps):
        if len(ps) < 2:
            return 0.0
        a, b = max(((p, q) for p in ps for q in ps), key=lambda t: math.dist(*t))
        return G.bearing(a, b)
    rock = "gneiss"
    stones = [{"kind": "stone", "c": list(mono), "len": f["monolith_width_m"]["value"], "wid": f["monolith_thickness_m"]["value"],
               "az": 90, "h": f["monolith_height_m"]["value"], "rock": rock, "label": "29", "title": "The central monolith (Stone 29)",
               "note": el["stone_29"]["note"] + ".", "cites": cites("monolith_height_m", "monolith_width_m", "monolith_faces", "monolith_offset_m")}]
    note_for = {"ring": "One of the 13 stones of the ring (Stones 41-53), on average 3 m high.",
                "avenue": "One of the 19 stones of the avenue running north from the ring, 83 m long.",
                "east": "One of the east row's five stones; Stone 33a, found fallen in the peat in 1977, was set up again in 1982.",
                "south": "One of the south row's five stones, which with the monolith point due north.",
                "west": "One of the west row's four stones.", "outlier": "An outlying stone."}
    cite_for = {"ring": ("ring_stone_height_m", "ring_diameter_m"), "avenue": ("avenue_length_m",),
                "east": ("east_row_length_m",), "south": ("south_row_length_m",), "west": ("west_row_length_m",),
                "outlier": ("stones_standing",)}
    for g, ps in groups.items():
        if g == "monolith":
            continue
        az = row_az(ps) if g in ("avenue", "east", "south", "west") else None
        for p in ps:
            a = (G.bearing((0, 0), p) + 90) % 360 if g == "ring" else az if az is not None else G.bearing((0, 0), p)
            h = f["ring_stone_height_m"]["value"] if g == "ring" else 2.0
            stones.append({"kind": "stone", "c": [round(v, 2) for v in p], "len": 1.0, "wid": 0.35, "az": round(a, 1),
                           "h": h, "rock": rock, "title": TITLES[g], "note": note_for[g], "cites": cites(*cite_for[g])})
    cairn_c = G.toward(mono, 90, 2.6)
    cairn = [{"kind": "mound", "c": list(cairn_c), "r": f["cairn_length_m"]["value"] / 2, "h": 0.7, "kerb_h": 0.25, "p": 0.6,
              "surface": "cairn", "kerb_rock": "gneiss", "title": "The chambered cairn",
              "note": el["cairn"]["chamber"] + ".", "cites": cites("cairn_length_m")}]
    for k in range(4):
        cairn.append({"kind": "stone", "c": list(G.toward(cairn_c, 45 + 90 * k, 0.9)), "len": 0.9, "wid": 0.25,
                      "az": 135 + 90 * k, "h": 1.1, "rock": rock, "title": "The chambered cairn",
                      "note": el["cairn"]["chamber"] + ".", "cites": cites("cairn_length_m")})
    now = stones + cairn
    peat = {"kind": "mound", "c": [0, 40], "r": 150, "h": f["peat_depth_m"]["value"], "kerb_h": f["peat_depth_m"]["value"],
            "p": 0.01, "surface": "grass", "kerb_rock": "cairn", "title": "The peat",
            "note": "Peat about 1.5 m deep, cleared from round the stones in 1857.", "cites": cites("peat_depth_m")}
    before = stones + [peat]
    av = groups.get("avenue", [])
    north = max(av, key=lambda p: p[1]) if av else (0, 80)
    cams = {
        "overview": {"label": "Overview from the south-east", "from": [38, -38, 16], "to": [0, 22, 1]},
        "avenue": {"label": "Down the avenue, facing the ring (south)", "from": [north[0] - 3, north[1] - 6], "to": [0, 0, 2], "fov": 45, "standing": True},
        "ring_se": {"label": "At the head of the avenue, facing the Sleeping Beauty (south-east)", "from": [2.5, 11], "to": [70, -60, 4], "fov": 60, "standing": True},
        "south": {"label": "From the north end of the avenue, facing south", "from": [north[0], north[1] + 4], "to": [0, -30, 3], "fov": 55, "standing": True},
        "above": {"label": "From above", "from": [0, 24.99, 150], "to": [0, 25, 0], "fov": 45},
    }
    facts = G.facts(r, [
        ("stones_standing", "49 stones stand today; one estimate of the original number is 80."),
        ("monolith_height_m", "The central monolith (Stone 29) is 4.8 m high (4.7-4.8 m)."),
        ("ring_diameter_m", "The ring is about 11.4-13.4 m across, flattened on the east."),
        ("ring_stone_height_m", "The ring stones average 3 m high, up to 3.5 m."),
        ("avenue_length_m", "The avenue is 83.2 m long."),
        ("rock", "All are of the local Lewisian gneiss."),
        ("peat_depth_m", "About 1.5 m of peat was cleared from round the stones in 1857."),
    ], cite) + [{"text": a["claim"], "cites": cite(r, a.get("cites"))} for a in r["alignment"][:2] + r["alignment"][5:6]] + \
        [{"text": t, "cites": []} for t in DERIVED]
    return {"name": "Calanais", "record": r["record"], "lat": lat, "lon": lon, "size": 600, "step": 2,
            "shadow": {"half": 70, "centre": [0, 30]},
            "views": {"now": now, "built": before}, "built_year": 1856, "built_label": "Before 1857 (in the peat)",
            "cams": cams, "events": ["summer_moon", "winter_moon", "summer_rise", "winter_set", "equinox_set"],
            "face": {"summer_moon": "ring_se", "winter_moon": "south"},
            "start": {"event": "summer_moon", "year": 2025, "after": 40,
                      "note": "The full moon nearest midsummer 2025, a major standstill year: it rises out of the Sleeping Beauty hills to the south-east and skims low along them. Press Play at 10 minutes a second."},
            "axis": [0, 180], "axis_length": 120, "axis_label": "True north-south (the south row and monolith)",
            "facts": facts, "about": [r["about"]], "labels_label": "Stone numbers"}
