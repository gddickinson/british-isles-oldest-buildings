"""3D model of Woodhenge and the Southern Circle at Durrington Walls (roadmap SH3f), from
`data/curated/models/durrington.json` (one entry per site).

The origin is Woodhenge's centre (SU 1506 4337; OpenStreetMap way 36970076 agrees within 1.5 m). Its six oval rings
(Wainwright and Longworth 1971, Table XXI: diameters, post counts, post and posthole sizes) are drawn on long axes at
Thom's azimuths, with the posts spaced evenly round each (their own positions are in Cunnington's 1929 plan, not
reachable). The Southern Circle has no published grid reference: it is placed 27.4 m north-west of the south-east
entrance of Durrington Walls (Wainwright), the entrance taken as the middle of the gap in the bank mapped on
OpenStreetMap (a circle fitted to the bank's arcs, 227 m in radius). Its Phase 2 rings (Table II) are drawn with the
3.8 m entrance in ring 2A on the henge's axis (123°30′). Ground: the Environment Agency's 1 m LiDAR, which shows
the henge bank. No post survives, so heights are scaled from the posthole depths (`DERIVED`).
"""
import math

from . import model_geometry as G
from . import osgrid
from .models3d import cite, research

HENGE_BANK = [42278421, 42278422, 42278423, 422737533, 422737535, 377344132]
AXES = {"A": 44, "B": 44, "C": 47, "F": 47, "D": 48.5, "E": 48.5}       # Thom's survey (Musson)
HEIGHT_PER_DEPTH = 7.5 / 1.7         # Wikipedia's 7.5 m above ground for the deepest holes (ring C, 1.7 m)
HENGE_AXIS = 123.5
DERIVED = [
    "Woodhenge: each ring is an ellipse of its published long and short diameters on Thom's axis (44°, 47°, 48.5°); "
    "the posts are spaced evenly round it, since their own positions are only on Cunnington's 1929 plan.",
    "No post survives, so their heights are not known: they are drawn in proportion to the depth of their holes, "
    "the deepest (Woodhenge ring C, 1.7 m) at the 7.5 m Wikipedia gives; this puts the Southern Circle's ring 2E at "
    "about 10 m, near Wainwright's 10.5 m for a roofed building. Whether either was roofed is debated.",
    "The Southern Circle is placed 27.4 m north-west of the henge's south-east entrance, taken as the middle of the "
    "gap in the bank mapped on OpenStreetMap; that puts it about 160 m from Woodhenge (Wikipedia says 70 m). Only "
    "its Phase 2 rings are drawn, posts spaced evenly at the presumed counts, the entrance on the henge's axis.",
    "As it is now, Woodhenge's postholes are marked by concrete posts about 0.9 m high; nothing marks the Southern "
    "Circle.",
]


def _henge(lat0, lon0):
    res = G.request_json(G.OVERPASS, data={"data": "[out:json];(" + "".join(f"way({i});" for i in HENGE_BANK) + ");out geom;"},
                         method="POST", min_interval=2)
    pts = [G.local(p["lat"], p["lon"], lat0, lon0) for e in res["elements"] for p in e["geometry"]]
    n = len(pts)
    sx, sy = sum(p[0] for p in pts) / n, sum(p[1] for p in pts) / n
    best = None
    for i in range(-60, 61):
        for j in range(-60, 61):
            c = (sx + i * 2, sy + j * 2)
            ds = [math.dist(p, c) for p in pts]
            m = sum(ds) / n
            v = sum((d - m) ** 2 for d in ds)
            if best is None or v < best[0]:
                best = (v, c, m)
    _, c, rad = best
    azs = sorted(G.bearing(c, p) for p in pts)
    k = max((k for k in range(n) if 90 < azs[k] < 200), key=lambda k: (azs[(k + 1) % n] - azs[k]) % 360)
    gap = (azs[k] + ((azs[(k + 1) % n] - azs[k]) % 360) / 2) % 360
    return c, rad, gap


def ellipse_points(c, a, b, az, n, start=0.0):
    """n points evenly in angle round an ellipse of semi-axes a (along az) and b."""
    out = []
    for k in range(n):
        t = 2 * math.pi * (k + start) / n
        u, v = a * math.cos(t), b * math.sin(t)
        x = c[0] + u * math.sin(math.radians(az)) + v * math.cos(math.radians(az))
        y = c[1] + u * math.cos(math.radians(az)) - v * math.sin(math.radians(az))
        out.append((round(x, 2), round(y, 2)))
    return out


def spec():
    r = research("durrington")
    W, Sc = r["sites"]["woodhenge"], r["sites"]["southern_circle"]
    wf = W["facts"]
    we = {e["id"]: e for e in W["elements"]}
    se = {e["id"]: e for e in Sc["elements"]}
    cf = lambda facts, *keys: [c for k in keys for c in cite(r, facts[k]["cites"])]       # noqa: E731
    lat, lon = osgrid.to_latlon("SU 1506 4337")
    hc, hr, gap = _henge(lat, lon)
    entrance = G.toward(hc, gap, hr)
    sc = G.toward(entrance, 315, 27.4)
    posts, markers = [], []
    for ring in "ABCDEF":
        e = we[f"ring_{ring}"]
        h = round(e["avg_posthole_depth_m"] * HEIGHT_PER_DEPTH, 1)
        for x, y in ellipse_points((0, 0), e["diameter_NE_SW_m"] / 2, e["diameter_NW_SE_m"] / 2, AXES[ring], e["posts"]):
            info = {"title": f"Woodhenge: ring {ring}", "cites": cite(r, e.get("cites")),
                    "note": f"Ring {ring} of six: {e['posts']} posts about {e['avg_post_diameter_m']} m thick in holes "
                            f"{e['avg_posthole_depth_m']} m deep (averages)."}
            posts.append({"kind": "post", "c": [x, y], "d": e["avg_post_diameter_m"], "h": h, **info})
            markers.append({"kind": "post", "c": [x, y], "d": 0.3, "h": 0.9, "rock": "concrete", **info,
                            "note": "Concrete marker (about 3 ft high) of a posthole of " + info["title"][11:] + "."})
    sp = []
    sizes = Sc["facts"]["phase2_post_diameters_cm"]["value"]
    for i, ring in enumerate(["2A", "2B", "2C", "2D", "2E", "2F"]):
        e = se[ring]
        n = e.get("posts_presumed") or e["posts_excavated"]
        h = round(e["avg_posthole_depth_m"] * HEIGHT_PER_DEPTH, 1)
        for k in range(n):
            az = HENGE_AXIS + 360 * (k + 0.5) / n
            if ring == "2A" and abs(((az - HENGE_AXIS + 540) % 360) - 180) < (Sc["facts"]["entrance_m"]["value"]["width_m"] / 2) / e["radius_m"] * 180 / math.pi:
                continue
            sp.append({"kind": "post", "c": [round(v, 2) for v in G.toward(sc, az, e["radius_m"])], "d": sizes[i] / 100, "h": h,
                       "title": f"Southern Circle: ring {ring}", "cites": cite(r, e.get("cites")),
                       "note": f"Phase 2 ring {ring}: about {n} posts (presumed), {sizes[i]} cm across in holes {e['avg_posthole_depth_m']} m deep."})
    ent = Sc["facts"]["entrance_m"]["value"]
    for side, d in ((-1, ent["post_22_diameter_m"]), (1, ent["post_23_diameter_m"])):
        az = HENGE_AXIS + side * (ent["width_m"] / 2 + d / 2) / se["2A"]["radius_m"] * 180 / math.pi
        sp.append({"kind": "post", "c": [round(v, 2) for v in G.toward(sc, az, se["2A"]["radius_m"])], "d": d,
                   "h": round((ent["post_22_depth_m"] if side < 0 else ent["post_23_depth_m"]) * HEIGHT_PER_DEPTH, 1),
                   "title": f"Southern Circle: entrance post {22 if side < 0 else 23}", "cites": cf(Sc["facts"], "entrance_m"),
                   "note": "The two great posts of the south-east entrance in ring 2A."})
    cairn = {"kind": "stone", "c": [0, 0], "len": 1.2, "wid": 0.6, "az": AXES["C"] + 90, "h": 0.35, "rock": "cairn",
             "title": "Woodhenge: the child's grave", "note": we["central_grave"]["what"] + ".", "cites": cite(r, we["central_grave"].get("cites"))}
    now = markers + [cairn]
    built = posts + sp
    cams = {
        "overview": {"label": "Woodhenge from the south-west", "from": [-45, -50, 18], "to": [0, 0, 3]},
        "centre": {"label": "In Woodhenge, facing the midsummer sunrise", "from": [-3, -3], "to": [*G.toward((0, 0), 48, 60), 3], "fov": 60, "standing": True},
        "southern": {"label": "In the Southern Circle, facing the midwinter sunrise", "from": list(G.toward(sc, HENGE_AXIS + 180, 3)), "to": [*G.toward(sc, HENGE_AXIS, 60), 3], "fov": 60, "standing": True},
        "both": {"label": "Both circles from above", "from": [sc[0] / 2 - 60, sc[1] / 2 - 160, 140], "to": [sc[0] / 2, sc[1] / 2, 0], "fov": 50},
    }
    facts = G.facts({"facts": wf}, [
        ("rings_count", "Woodhenge: six concentric oval rings of postholes, A (outermost) to F."),
        ("outer_ring_max_m", "The outer ring is 44.1 m by 39.6 m."),
        ("largest_ring_C_posts", "Ring C held the largest posts, 16 of them."),
        ("post_height_above_ground_m", "Published estimates of the posts' height above ground differ: 7.5 m, 24 ft, 6 m."),
        ("timber", "The posts were of oak (some birch)."),
    ], lambda _r, c: cite(r, c)) + G.facts({"facts": Sc["facts"]}, [
        ("max_diameter_m", "The Southern Circle's outer ring (Phase 2) is 38.9 m across."),
        ("entrance_m", "Its entrance, 3.8 m wide, faces south-east between two great posts."),
        ("roof_height_if_roofed_m", "If it was a roofed building, Wainwright had it 10.5 m high at ring 2E."),
    ], lambda _r, c: cite(r, c)) + [{"text": a["claim"], "cites": cite(r, a.get("cites"))} for a in W["alignment"][:1] + Sc["alignment"][:2]] + \
        [{"text": t, "cites": []} for t in DERIVED]
    return {"name": "Woodhenge and Durrington Walls", "record": W["record"], "lat": lat, "lon": lon, "ground": "ea",
            "size": 800, "step": 2, "shadow": {"half": 120, "centre": [sc[0] / 2, sc[1] / 2]},
            "views": {"now": now, "built": built}, "built_year": -2499, "built_label": "As built (c. 2500 BC)",
            "cams": cams, "events": ["summer_rise", "winter_rise", "summer_set", "winter_set"],
            "face": {"summer_rise": "centre", "winter_rise": "southern"},
            "start": {"event": "summer_rise", "after": 20, "view": "built", "year": -2499,
                      "note": "Midsummer sunrise in about 2500 BC, as built: the long axes of Woodhenge's rings point towards it. Press “Midwinter sunrise” for the Southern Circle's entrance, and switch to “As it is now” for the concrete markers."},
            "axis": [47], "axis_length": 300, "axis_label": "Woodhenge's axis (Thom, rings C and F)",
            "facts": facts, "about": [r["about"]], "labels_label": "Labels"}
