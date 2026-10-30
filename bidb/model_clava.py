"""3D model of the Balnuaran of Clava cairns (roadmap SH4a), from `data/curated/models/hougue_clava.json` (site
"clava"): the north-east and south-west passage graves and the central ring cairn, each in its stone circle.

Centres from the OpenStreetMap cairn outlines (ways 41662528, 41662530, 41662532); sizes from Henshall, Fraser and
Piggott via the Highland HER and HES (the research file). Both passages are drawn on the line through the two passage
graves' centres (216.4°: Thom has them in line). As it is now the chambers and passages are open to the sky; as built
(about 2000 BC) the chambers are corbelled and the passages roofed under full cairns, so the midwinter sunset can be
watched down the passages. What had to be assumed is in `DERIVED`.
"""
import math

from . import model_geometry as G
from .models3d import cite, research

CAIRNS = {"ne": 41662528, "ring": 41662530, "sw": 41662532}
DERIVED = [
    "Both passages are drawn outward on the line through the two passage graves' centres mapped on OpenStreetMap "
    "(216.4°; Fraser gave the south-west passage 'S. 39° W.', 219°, magnetic or true not said). The north-east "
    "passage's length is not published in a reachable source: drawn as the south-west's (6 m).",
    "The stones of the circles are spaced evenly round each (their own positions are on Fraser's 1884 plans, not yet "
    "traced), graded from the tallest on the south-west to about 1 m on the north-east, as the circles are.",
    "As built, the cairns are drawn whole over corbelled chambers and roofed passages; how high the roofs were is not "
    "known (the chambers' walls stand 2.1 m).",
    "The ring cairn's three rays are drawn on Fraser's bearings (100°, 170°, 295°) as low strips 2 m wide.",
]


def spec():
    r = research("hougue_clava")
    S = r["sites"]["clava"]
    el = {e["id"]: e for e in S["elements"]}
    lat0, lon0 = S["reference_point"]["lat"], S["reference_point"]["lon"]
    res = G.request_json(G.OVERPASS, data={"data": "[out:json];(" + "".join(f"way({w});" for w in CAIRNS.values()) + ");out geom;"},
                         method="POST", min_interval=2)
    cent = {}
    for e in res["elements"]:
        pts = [G.local(p["lat"], p["lon"], lat0, lon0) for p in e["geometry"]]
        cent[next(k for k, v in CAIRNS.items() if v == e["id"])] = G.centroid(pts[:-1])
    AX = G.bearing(cent["ne"], cent["sw"])                      # outward from both passages, towards the SW
    ce = lambda e: cite(r, e.get("cites"))                     # noqa: E731
    now, built = [], []
    for key in ("ne", "sw"):
        e = el[f"{key}_cairn"]
        c = cent[key]
        R = e["kerb_diameter_m"]["value"] / 2
        ch = e["chamber"]
        chd = ch.get("diameter_m", ch.get("size_m"))["value"]
        rch = (sum(chd) / len(chd)) / 2
        wall = ch["wall_height_m"]["value"]
        ps = e.get("passage", {})
        plen = (ps.get("length_m") or {}).get("value", 6.0)
        pw = (ps.get("width_m") or {}).get("value", 0.7)
        ph = (ps.get("height_m") or {}).get("value", 1.2)
        end = G.toward(c, AX, rch)
        mouth = G.toward(end, AX, plen)
        poly = G.polygon(c, rch / math.cos(math.pi / 10), 10, start=AX + 18)
        name = e["name"]
        info = {"title": name, "note": e["kerb"] + ".", "cites": ce(e)}
        height = e["cairn_height_m"]["value"]
        chamber_now = {"kind": "chamber", "outline": poly, "h": wall, "rock": "gneiss", "step": 1.0, "roof": {"kind": "none"},
                       "open": [{"at": list(end), "width": pw}], **info}
        passage_now = {"kind": "passage", "path": [list(mouth), list(end)], "width": pw, "roof": ph, "rock": "gneiss", "step": plen / 5,
                       "roof_gap": [0, plen], **info}
        now += [{"kind": "bank", "c": list(c), "r": (rch + R) / 2 + 0.3, "w": R - rch, "h": min(height, 1.6), "surface": "cairn",
                 "gaps": [[AX, pw + 0.3]], **info}, chamber_now, passage_now]
        built += [{"kind": "mound", "c": list(c), "r": R, "h": height + 1.0, "kerb_h": 0.9, "p": 0.8, "surface": "cairn",
                   "kerb_rock": "gneiss", "gap": {"az": AX, "width": pw + 0.3, "open": [[0, ph]]}, **info},
                  {**chamber_now, "roof": {"kind": "corbel", "top": wall + 1.2, "rings": 6}},
                  {**passage_now, "roof_gap": None}]
        kerb = [{"kind": "stone", "c": [x, y], "len": 1.0, "wid": 0.45, "az": az, "rock": "granite",
                 "h": round(0.46 + 0.5 * (1 + math.cos(math.radians(G.bearing(c, (x, y)) - AX))) / 2, 2), **info}
                for x, y, az in G.along(G.polygon(c, R, 48), 48)]
        circ_r = R + 9.0
        circle = [{"kind": "stone", "c": list(G.toward(c, AX + k * 360 / 11, circ_r)), "len": 0.9, "wid": 0.45,
                   "az": AX + k * 360 / 11 + 90, "rock": "gneiss",
                   "h": round(1.0 + 1.3 * (1 + math.cos(math.radians(k * 360 / 11))) / 2, 2),
                   "title": f"{name}: stone circle", "note": str(e.get("circle", {}).get("stones", "")) + ".", "cites": ce(e)}
                  for k in range(11)]
        now += kerb + circle
        built += kerb + circle
    e = el["central_ring_cairn"]
    c = cent["ring"]
    a, b = e["kerb_m"]["value"]
    R = (a + b) / 4
    info = {"title": e["name"], "note": e["inner_kerb"] + "; " + e["kerb_note"] + ".", "cites": ce(e)}
    ring = [{"kind": "bank", "c": list(c), "r": R - 2.2, "w": 4.4, "h": e["cairn_height_m"]["value"], "surface": "cairn", **info}]
    ring += [{"kind": "stone", "c": [x, y], "len": 1.0, "wid": 0.4, "az": az, "h": 0.6, "rock": "granite", **info}
             for x, y, az in G.along(G.polygon(c, R, 44), 44)]
    ring += [{"kind": "stone", "c": [x, y], "len": 0.8, "wid": 0.25, "az": az, "h": 0.95, "rock": "sandstone", **info}
             for x, y, az in G.along(G.polygon(c, 3.0, 16), 16)]
    for brg in (100, 170, 295):
        a0, a1 = G.toward(c, brg, R + 0.5), G.toward(c, brg, e["circle"]["diameter_m"]["value"] / 2 - 0.5)
        ring.append({"kind": "stone", "c": [(a0[0] + a1[0]) / 2, (a0[1] + a1[1]) / 2], "len": math.dist(a0, a1), "wid": 2.0,
                     "az": brg, "h": 0.3, "base": 0, "rock": "cairn", "rough": 0.5, "title": "Ring cairn: a ray",
                     "note": e["rays"]["build"] + ".", "cites": ce(e)})
    cr = e["circle"]["diameter_m"]["value"] / 2
    ring += [{"kind": "stone", "c": list(G.toward(c, AX + k * 40, cr)), "len": 0.9, "wid": 0.45, "az": AX + k * 40 + 90,
              "rock": "gneiss", "h": round(0.5 + 1.8 * (1 + math.cos(math.radians(k * 40))) / 2, 2),
              "title": "Ring cairn: stone circle", "note": e["circle"]["tallest"] + ".", "cites": ce(e)} for k in range(9)]
    now += ring
    built += ring
    sw = cent["sw"]
    chamber_eye = G.toward(sw, AX + 180, 1.2)
    cams = {
        "overview": {"label": "Overview from the south-east", "from": [55, -75, 30], "to": [0, -5, 1]},
        "sw_chamber": {"label": "In the south-west cairn's chamber, facing the passage", "from": [*chamber_eye, 1.2], "to": [*G.toward(sw, AX, 40), 1.0], "fov": 60, "standing": True},
        "ne_chamber": {"label": "In the north-east cairn's chamber, facing the passage", "from": [*G.toward(cent["ne"], AX + 180, 1.2), 1.2], "to": [*G.toward(cent["ne"], AX, 60), 1.0], "fov": 60, "standing": True},
        "line": {"label": "Along the line of the cairns, facing south-west", "from": list(G.toward(cent["ne"], AX + 180, 25)), "to": [*G.toward(sw, AX, 80), 2], "fov": 45, "standing": True},
        "above": {"label": "From above", "from": [0, -0.01, 160], "to": [0, 0, 0], "fov": 50},
    }
    facts = [{"text": f"{el[k]['name']}: kerb {el[k]['kerb_diameter_m']['value']} m across, cairn about {el[k]['cairn_height_m']['value']} m high, chamber walls {el[k]['chamber']['wall_height_m']['value']} m.",
              "cites": ce(el[k])} for k in ("ne_cairn", "sw_cairn")] + \
        [{"text": f"The ring cairn: kerb about {a} by {b} m round an open space; its stone circle about {e['circle']['diameter_m']['value']} m across.", "cites": ce(e)}] + \
        [{"text": al["claim"], "cites": cite(r, al.get("cites"))} for al in S.get("alignment", [])[:2]] + \
        [{"text": t, "cites": []} for t in DERIVED]
    return {"name": "Balnuaran of Clava", "record": S.get("record"), "lat": lat0, "lon": lon0, "size": 500, "step": 2,
            "flatten": None, "shadow": {"half": 75, "centre": [0, -5]},
            "views": {"now": now, "built": built}, "built_year": -1999, "built_label": "As built (about 2000 BC)",
            "cams": cams, "events": ["winter_set", "summer_rise", "equinox_set"], "face": {"winter_set": "sw_chamber"},
            "start": {"event": "winter_set", "after": -8, "view": "built", "year": -1999,
                      "note": "Midwinter sunset about 2000 BC, as built: the passages face it, in line with each other. Try “Lantern” in the chambers, and “As it is now” for the open cairns."},
            "axis": [AX], "axis_length": 200, "axis_label": "The line of the passages", "lantern": True,
            "facts": facts, "about": [S.get("about", r.get("about", ""))], "labels_label": "Labels"}
