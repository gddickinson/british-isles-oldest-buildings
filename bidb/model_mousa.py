"""3D model of the Broch of Mousa (roadmap SH3g), from `data/curated/models/mousa.json` (bidb.models3d).

The tower is the "broch" part of app/static/model_broch.js: 13.3 m high, 15 m across at the base and 12 m at the top,
the court 6.1 m across, solid to 3 m and hollow above with six galleries (Thomas's levels from Paterson's 1919
survey), the two ledges at 2.1 and 3.7 m, the entrance passage, the stair. The second view is a cutaway: a quarter of
the wall left out so the galleries and stair show. Derived values are listed in `DERIVED`.
"""
from .models3d import cite, research
from . import model_geometry as G

DERIVED = [
    "The outer face is drawn as a straight batter from 15 m across at the base to 12 m at the top (the real profile "
    "is a concave curve); the court as a cylinder 6.1 m across.",
    "Above the solid base (3 m) the galleries are drawn 0.9 m wide midway through the wall, on Thomas's levels from "
    "Paterson's survey (approximate; the highest lies above the surviving top and is left out).",
    "The entrance faces 277°, the bearing of the column of openings over it (273-281°); it is 1.2 m wide and 1.63 m "
    "high. The three cells, the recesses and the later wheelhouse are not drawn.",
    "The stair starts on the north-east (the openings over its door, 42-50°) 1.5 m up and is drawn turning 330° "
    "clockwise up to the wall-head; the number of its steps and its true course are not published.",
]


def spec():
    r = research("mousa")
    f = r["facts"]
    el = {e["id"]: e for e in r["elements"]}
    cites = lambda *keys: [c for k in keys for c in cite(r, f[k]["cites"])]        # noqa: E731
    h = f["height_m"]["value"]
    gals = []
    for gd in f["gallery_dimensions"]["value"]:
        z0, z1 = gd["floor_above_ground_m"], gd["floor_above_ground_m"] + gd["height_m"]
        if z1 < h - 0.3:
            gals.append([round(z0, 2), round(z1, 2)])
    ent = el["entrance_passage"]
    tower = {"kind": "broch", "c": [0, 0], "h": h, "r_base": f["external_diameter_base_m"]["value"] / 2,
             "r_top": f["external_diameter_top_m"]["value"] / 2, "court_r": f["internal_diameter_m"]["value"] / 2,
             "solid_h": f["solid_base_height_m"]["value"], "galleries": gals, "gallery_w": 0.9,
             "entrance": {"az": 277, "width": ent["width_m"], "h": ent["height_m"]},
             "stair": {"az0": 46, "z0": 1.5, "z1": h - 0.4, "turn": 330, "width": 0.85},
             "ledges": el["scarcements"]["heights_m"], "rock": "flagstone", "title": "The Broch of Mousa",
             "note": f["hollow_wall"]["value"] + "; " + f["stone"]["value"] + ".",
             "cites": cites("height_m", "external_diameter_base_m", "internal_diameter_m", "hollow_wall", "gallery_count")}
    cutaway = {**tower, "cut": [100, 190]}
    cams = {
        "overview": {"label": "From the south-east", "from": [*G.toward((0, 0), 145, 30), 9], "to": [0, 0, 6]},
        "court": {"label": "In the court, looking up", "from": [0.5, -1.2], "to": [-0.5, 1.5, 12], "fov": 75, "standing": True},
        "galleries": {"label": "The galleries and stair (cutaway)", "from": [*G.toward((0, 0), 145, 14), 8], "to": [0, 0, 7], "fov": 55},
        "sea": {"label": "From the shore, facing the entrance", "from": list(G.toward((0, 0), 277, 25)), "to": [0, 0, 5], "fov": 55, "standing": True},
    }
    facts = G.facts(r, [
        ("height_m", "The tower stands 13.3 m high."),
        ("external_diameter_base_m", "It is 15 m across at the base."),
        ("external_diameter_top_m", "And 12 m across at the top."),
        ("internal_diameter_m", "The court inside is about 6.1 m across."),
        ("solid_base_height_m", "The wall is solid to about 3 m."),
        ("hollow_wall", "Above, inner and outer walls tied by slab floors make the galleries."),
        ("gallery_count", "There are six galleries."),
        ("stone", "It is built of local sandstone flags laid dry."),
        ("date_built", "It was built about 300 BC (sources range from 300 BC to AD 150)."),
    ], cite) + [{"text": el["stair"]["start"] + "; " + el["stair"]["rise"] + ".", "cites": cite(r, el["stair"].get("cites"))},
                {"text": el["storm_petrels"]["note"], "cites": cite(r, el["storm_petrels"].get("cites"))}] + \
        [{"text": t, "cites": []} for t in DERIVED]
    return {"name": "Mousa Broch", "record": r["record"], "lat": f["position"]["value"]["lat"], "lon": f["position"]["value"]["lon"],
            "size": 400, "step": 2, "flatten": {"c": [0, 0], "r": 9, "edge": 6}, "shadow": {"half": 22, "centre": [0, 0]},
            "views": {"now": [tower], "built": [cutaway]}, "built_label": "Cutaway (a quarter of the wall left out)",
            "cams": cams, "events": ["summer_set", "summer_rise", "winter_rise", "equinox_set"],
            "start": {"m": 6, "d": 21, "t": 600, "view": "built",
                      "note": "Midsummer morning; the cutaway shows the galleries and the stair inside the double wall. Switch to “As it is now” for the whole tower."},
            "facts": facts, "about": [r["about"]], "labels_label": "Labels", "lantern": True}
