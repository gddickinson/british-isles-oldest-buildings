"""3D model of Maeshowe, the Stones of Stenness and the Ring of Brodgar in one landscape (roadmap SH3e), from
`data/curated/models/orkney.json` (research file with one entry per site).

The origin is Maeshowe's mound (OpenStreetMap way 774967953). Maeshowe: the passage outward at Ruggles' 221°, the
chamber 4.6 m square, corbelled to 4.5 m, with its four corner buttresses; the ditch on its OSM outline. Stenness:
the stones on their OSM outlines, numbered by Ritchie's twelve positions 30° apart (Stone 2 at the large outline due
south, which puts Stones 7 and 8 either side of the north causeway, as Ritchie says), with his heights. Brodgar: no
stone is mapped or numbered in a reachable source, so its 60 stones are drawn evenly round the 103.6 m ring.
"""
import math

from . import model_geometry as G
from .models3d import cite, research

STONE_WAYS = [774960014, 774960015, 774960016, 774960017, 774960018, 774960019, 774960020, 774960021, 774960022, 774960023]
DERIVED = [
    "Maeshowe's passage is drawn straight, 15 m long, outward at 221° (Ruggles' mean axis of the inner passage), 0.9 m "
    "wide and 1.4 m high; the side cells are not drawn. Its ditch follows the OSM outline, 14 m wide.",
    "Stenness: Ritchie's numbers are given to the OSM stones by their twelve positions 30° apart, Stone 2 at the "
    "large outline due south; this puts Stones 7 and 8 either side of the north causeway, as he describes. Heights and "
    "breadths are Ritchie's; stumps below ground are drawn 0.2 m.",
    "Brodgar: no reachable source maps or numbers its stones; the 60 positions are drawn evenly round the ring, all "
    "standing 3.4 m (the published heights run 2.1-4.7 m) as built; in the view as it is now the 27 standing stones "
    "cannot be placed, so the ring is shown as built in both views.",
    "One directional light gives sharp shadows only round Maeshowe (for the sunbeam down its passage).",
]


def _osm(lat0, lon0):
    ids = "".join(f"way({w});" for w in STONE_WAYS + [774967953, 288905594])
    q = (f"[out:json];({ids}node(1293208753);node(5522405525);node(1291972590);node(5522411677);way(782724929););"
         "out tags geom;")
    res = G.request_json(G.OVERPASS, data={"data": q}, method="POST", min_interval=2)
    out = {}
    for e in res["elements"]:
        if e["type"] == "node":
            out[e["id"]] = G.local(e["lat"], e["lon"], lat0, lon0)
        else:
            pts = [G.local(p["lat"], p["lon"], lat0, lon0) for p in e["geometry"]]
            out[e["id"]] = pts[:-1] if pts[0] == pts[-1] else pts
    return out


def spec():
    r = research("orkney")
    S = r["sites"]
    mf, sf, bf = S["maeshowe"]["facts"], S["stenness"]["facts"], S["brodgar"]["facts"]
    me = {e["id"]: e for e in S["maeshowe"]["elements"]}
    se = {e["id"]: e for e in S["stenness"]["elements"]}
    be = {e["id"]: e for e in S["brodgar"]["elements"]}
    cf = lambda facts, *keys: [c for k in keys for c in cite(r, facts[k]["cites"])]        # noqa: E731
    ce = lambda e: cite(r, e.get("cites"))                                                  # noqa: E731
    lat0, lon0 = S["maeshowe"]["reference_point"]["lat"], S["maeshowe"]["reference_point"]["lon"]
    osm = _osm(lat0, lon0)
    mc = G.centroid(osm[774967953])
    lat = lat0 + mc[1] / 110574
    lon = lon0 + mc[0] / (111320 * math.cos(math.radians(lat0)))
    osm = {k: ([(x - mc[0], y - mc[1]) for x, y in v] if isinstance(v, list) else (v[0] - mc[0], v[1] - mc[1]))
           for k, v in osm.items()}
    # Maeshowe.
    AX = 221.0
    side, R = mf["chamber_side_m"]["value"], mf["mound_diameter_m"]["value"] / 2
    plen = mf["passage_length_m"]["value"]
    end = G.toward((0, 0), AX, side / 2)
    mouth = G.toward(end, AX, plen)
    sq = G.polygon((0, 0), side / 2 * math.sqrt(2), 4, start=AX + 45)
    flag = "flagstone"
    mound = {"kind": "mound", "c": [0, 0], "r": R, "h": mf["mound_height_m"]["value"], "kerb_h": 0.05, "p": 0.7,
             "facade": {"from": AX - 8, "to": AX + 8, "rock": flag, "h": 1.9},
             "gap": {"az": AX, "width": 1.1, "open": [[0, 1.4]]}, "title": "Maeshowe: the mound",
             "note": me["mound"]["material"] + ".", "cites": cf(mf, "mound_diameter_m", "mound_height_m")}
    passage = {"kind": "passage", "path": [list(mouth), list(end)], "width": 0.9, "roof": mf["passage_height_m"]["value"],
               "rock": flag, "step": 2.0, "roof_rough": 0.4, "title": "Maeshowe: the passage",
               "note": me["passage_inner"]["construction"] + ".",
               "cites": cf(mf, "passage_length_m", "passage_height_m", "passage_widths_ft", "passage_slab_length_ft")}
    chamber = {"kind": "chamber", "outline": [list(p) for p in sq], "h": mf["chamber_wall_vertical_m"]["value"], "rock": flag,
               "step": 1.2, "roof": {"kind": "corbel", "top": mf["chamber_height_m"]["value"], "rings": 9},
               "open": [{"at": list(end), "width": 0.9}], "title": "Maeshowe: the chamber",
               "note": me["chamber"]["roof"] + ".", "cites": cf(mf, "chamber_side_m", "chamber_height_m", "chamber_wall_vertical_m")}
    butt = [{"kind": "stone", "c": list(G.toward((0, 0), AX + 45 + 90 * k, side / 2 * math.sqrt(2) - 0.55)), "len": 0.9,
             "wid": 0.9, "az": AX + 45 + 90 * k, "h": 2.9, "rock": flag, "interior": True, "title": "Maeshowe: corner buttress",
             "note": me["buttresses"]["construction"] + ".", "cites": cf(mf, "buttress_size_ft")} for k in range(4)]
    ditch_r = sum(math.hypot(*p) for p in osm[288905594]) / len(osm[288905594]) - 7
    ditch = {"kind": "bank", "c": [0, 0], "r": ditch_r, "w": 14, "h": -0.6, "title": "Maeshowe: the ditch",
             "note": me["ditch"]["profile"] + ".", "cites": cf(mf, "ditch_width_m")}
    # Stenness: positions of the twelve stones, Stone 2 at the large outline due south.
    ring = osm[782724929]
    sc = G.centroid(ring)
    stones = {w: osm[w] for w in STONE_WAYS}
    big_s = min((w for w in stones if w not in (774960019, 774960021)),
                key=lambda w: abs(((G.bearing(sc, G.centroid(stones[w])) - 180 + 540) % 360) - 180))
    a2 = G.bearing(sc, G.centroid(stones[big_s]))
    # Each position to one stone, nearest first.
    pos_of, taken = {}, set()
    cand = sorted(((abs(((G.bearing(sc, G.centroid(pts)) - a2 - 30 * k + 540) % 360) - 180), w, k)
                   for w, pts in stones.items() if w not in (774960019, 774960021) for k in range(12)))
    for err, w, k in cand:
        if w not in pos_of and k not in taken:
            pos_of[w] = k
            taken.add(k)
    sten = []
    for w, pts in stones.items():
        c = G.centroid(pts)
        if w == 774960021:
            sten.append({"kind": "stone", "outline": [list(p) for p in pts], "h": 0.3, "base": 0, "rock": flag,
                         "title": "Stenness: the central hearth", "note": se["hearth"]["construction"] + ".", "cites": ce(se["hearth"])})
            continue
        if w == 774960019:
            sten.append({"kind": "stone", "outline": [list(p) for p in pts], "h": 0.45, "base": 0, "rock": flag,
                         "title": "Stenness: the slab of the 'dolmen'", "note": se["dolmen"]["now"] + ".", "cites": ce(se["dolmen"])})
            continue
        n = (pos_of[w] + 1) % 12 + 1
        e = se.get(f"stone_{n}", {})
        h = e.get("height_m", 0.2)
        sten.append({"kind": "stone", "c": list(c), "len": e.get("breadth_m", 1.0), "wid": e.get("thickness_m", 0.35),
                     "az": (G.bearing(sc, c) + 90) % 360, "h": h, "rock": flag, "label": str(n),
                     "status": "reconstructed" if e.get("restored") else None,
                     "title": f"Stenness: Stone {n}", "note": e.get("state", "") + ".", "cites": ce(e)})
    for node, key in [(1293208753, "watch_stone"), (5522405525, "barnhouse_stone")]:
        e = se[key]
        sten.append({"kind": "stone", "c": list(osm[node]), "len": 1.5 if key == "watch_stone" else 1.4,
                     "wid": e["thickness_m"], "az": 0, "h": e["height_m"], "rock": flag,
                     "title": "The Watch Stone" if key == "watch_stone" else "The Barnhouse Stone",
                     "note": e["position"] + ".", "cites": ce(e)})
    sten.append({"kind": "bank", "c": list(sc), "r": 22 + 2, "w": sf["ditch_width_m"]["value"], "h": -0.5,
                 "gaps": [[0, sf["causeway"]["value"]]], "title": "Stenness: the ditch", "note": "About 4 m wide, cut 1 m into rock.",
                 "cites": cf(sf, "ditch_width_m", "causeway")})
    # Brodgar: 60 stones evenly round the ring (positions not published), ditch with two causeways.
    bc = G.local(S["brodgar"]["reference_point"]["lat"], S["brodgar"]["reference_point"]["lon"], lat, lon)
    rr = bf["ring_diameter_m"]["value"] / 2
    brod = [{"kind": "stone", "c": list(G.toward(bc, i * 6 + 3, rr)), "len": 1.1, "wid": 0.35, "az": i * 6 + 93, "h": 3.4,
             "rock": flag, "title": "Ring of Brodgar: a stone", "note": be["ring"]["standing"] + " stand today, of perhaps 60.",
             "cites": cf(bf, "stones_original", "stones_standing", "stone_heights_m")} for i in range(60)]
    brod.append({"kind": "bank", "c": list(bc), "r": bf["ditch_diameter_m"]["value"] / 2, "w": bf["ditch_width_m"]["value"],
                 "h": -1.2, "gaps": [[315, bf["causeway_nw_width_m"]["value"]], [135, bf["causeway_se_width_m"]["value"]]],
                 "title": "Ring of Brodgar: the ditch", "note": be["ditch"]["profile"] + "; " + be["ditch"]["now"] + ".",
                 "cites": cf(bf, "ditch_diameter_m", "ditch_width_m", "ditch_depth_m")})
    brod.append({"kind": "stone", "c": list(osm[1291972590]), "len": 0.9, "wid": 0.35, "az": 0, "h": be["comet_stone"]["height_m"],
                 "rock": flag, "title": "The Comet Stone", "note": be["comet_stone"]["position"] + ".", "cites": ce(be["comet_stone"])})
    brod.append({"kind": "mound", "c": list(osm[5522411677]), "r": 20, "h": 6, "kerb_h": 0.05, "p": 0.8,
                 "title": "Salt Knowe", "note": be["salt_knowe"]["note"] + ".", "cites": ce(be["salt_knowe"])})
    now = [mound, passage, chamber, ditch] + butt + sten + brod
    eye = G.toward((0, 0), AX + 180, side / 2 - 0.6)
    cams = {
        "overview": {"label": "Maeshowe from the south-west", "from": [*G.toward((0, 0), AX + 15, 90), 30], "to": [0, 0, 3]},
        "chamber": {"label": "In Maeshowe's chamber, facing the passage", "from": [*eye, 1.1], "to": [*G.toward((0, 0), AX, 30), 0.9], "fov": 60, "standing": True},
        "entrance": {"label": "Outside Maeshowe, facing the entrance", "from": list(G.toward((0, 0), AX, 32)), "to": [0, 0, 1.2], "fov": 50, "standing": True},
        "stenness": {"label": "The Stones of Stenness", "from": [*G.toward(sc, 160, 40), 6], "to": [*sc, 2]},
        "brodgar": {"label": "The Ring of Brodgar", "from": [*G.toward(bc, 150, 95), 25], "to": [*bc, 1]},
        "landscape": {"label": "The landscape from above", "from": [-900, -1100, 900], "to": [-1300, 300, 0], "fov": 50},
    }
    facts = G.facts({"facts": mf}, [
        ("mound_diameter_m", "Maeshowe's mound is 35 m across and 7 m high."),
        ("passage_length_m", "Its passage is about 15 m long (sources differ) and up to 1.4 m high."),
        ("chamber_side_m", "The chamber is about 4.6 m square and 4.5 m high, corbelled above 1.4 m."),
    ], lambda _r, cites: cite(r, cites)) + G.facts({"facts": sf}, [
        ("tallest_stone_m", "The tallest stone at Stenness (Stone 2) is 5.7 m high."),
        ("stones_planned", "Twelve stones were planned there; ten or eleven at most were set up."),
    ], lambda _r, cites: cite(r, cites)) + G.facts({"facts": bf}, [
        ("ring_diameter_m", "The Ring of Brodgar is 103.6 m across."),
        ("stones_standing", "27 of its stones stand today, of perhaps 60."),
        ("ditch_depth_m", "Its rock-cut ditch was about 10 m wide and 4 m deep."),
    ], lambda _r, cites: cite(r, cites)) + \
        [{"text": a["claim"], "cites": cite(r, a.get("cites"))} for a in S["maeshowe"]["alignment"][:4]] + \
        [{"text": t, "cites": []} for t in DERIVED]
    return {"name": "Maeshowe, Stenness and Brodgar", "record": S["maeshowe"]["record"], "lat": lat, "lon": lon,
            "size": 5200, "step": 13, "flatten": {"c": [0, 0], "r": R + 2, "edge": 10},
            "shadow": {"half": 30, "centre": [0, 0]}, "views": {"now": now}, "cams": cams,
            "events": ["winter_set", "summer_rise", "equinox_set"], "face": {"winter_set": "chamber"},
            "start": {"sun": "set", "m": 11, "d": 30, "after": -10,
                      "note": "Sunset on 30 November, three weeks before midwinter, when the sun sets in line with Maeshowe's passage (221°): the light runs down it into the chamber. Press “Midwinter sunset” for the solstice (the sun then sets about 4° further south), Play at 1 minute a second, and “Lantern” to see inside."},
            "axis": [AX], "axis_length": 900, "axis_label": "Maeshowe's passage axis", "lantern": True,
            "facts": facts, "about": [r["about"]] + [S[k].get("about", "") for k in ("maeshowe", "stenness", "brodgar")],
            "labels_label": "Stone numbers (Stenness)"}
