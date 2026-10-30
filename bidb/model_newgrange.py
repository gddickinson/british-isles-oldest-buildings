"""3D model of Newgrange (roadmap SH3c), from `data/curated/models/newgrange.json` (bidb.models3d).

Placed by OpenStreetMap: the mound outline (way 25696157), the passage entrance (node 5335472272) and the five
standing stones of the Great Circle mapped in front of it. Measurements are the research file's (Claire O'Kelly's
guide, Ray 1989, the 2024 Winter Solstice Research Report, Hensey 2017); what no reachable source gives is drawn and
said so in `DERIVED`: the passage straight on the middle of Ray's light window, the chamber's outline from its two
overall sizes and the recess depths, the facade's length, the roof-box as a channel over the first roof slabs.
"""
import math

from . import model_geometry as G
from .models3d import cite, research

LAT, LON = 53.6947345, -6.4755388        # SMR ME019-045 (research: reference_point)
ENTRANCE = (53.6944932, -6.475224)        # OSM node 5335472272
AXIS = 134.3                              # outward: the sun azimuth at which the beam culminated, 20 Dec 2020
DERIVED = [
    "No measured axis of the passage is published in a reachable source: it is drawn straight, outward at 134.3°, "
    "the sun's azimuth when the beam culminated (reached furthest) on 20 December 2020 (2024 report); the real "
    "passage is sinuous. The beam can enter while the sun is between 133°49′ and 137°29′ (Ray).",
    "The passage floor rises evenly by 2 m. The doorway is 1.5 m high; the first roof slab (RS1) lies level 2.0-2.35 m "
    "above the entrance floor to 3 m in, and RS2 and the roof behind it 0.2 m higher: the slit (18-22 cm) through "
    "which the nearly level sunbeam passes over RS1. The roof is 2.4 m above the floor 6 m in and 3.6 m at RS17; 17 "
    "roof slabs. The roof-box is drawn as a channel 0.25 m wide over RS1 from the facade to the slit.",
    "The cruciform chamber is drawn from its overall size (5.2 m from the passage to the back of the end recess, "
    "6.5 m across the side recesses) and the recess depths of 1903 (east 2.36 m, end 2.29 m, west 1.02 m); the "
    "recesses are drawn 1.6 m wide. Its corbelled vault rises to 6 m.",
    "The quartz facade (3 m high) is drawn over the front of the mound, 55° either side of the entrance; its length "
    "is not published. The 97 kerbstones are spaced evenly round the outline, 1.2 m high; K22-K46, still buried, "
    "are left out of the view as it is now.",
    "The five Great Circle stones mapped on OpenStreetMap are drawn 2 m high (the four tallest are 2-2.5 m).",
]


def _osm():
    res = G.request_json(G.OVERPASS, data={"data": "[out:json];(way(25696157);node(around:150,53.6944,-6.4752)[historic=menhir];"
                                                    "node(around:150,53.6944,-6.4752)[megalith_type=menhir];);out tags geom;"},
                         method="POST", min_interval=2)
    outline, stones = None, []
    for e in res["elements"]:
        if e["type"] == "way":
            pts = [G.local(p["lat"], p["lon"], LAT, LON) for p in e["geometry"]]
            outline = pts[:-1] if pts[0] == pts[-1] else pts
        else:
            stones.append((e["id"], G.local(e["lat"], e["lon"], LAT, LON)))
    return outline, sorted(set(stones))


def spec():
    r = research("newgrange")
    f = r["facts"]
    cites = lambda *keys: [c for k in keys for c in cite(r, f[k]["cites"])]        # noqa: E731
    el = {e["id"]: e for e in r["elements"]}
    outline, menhirs = _osm()
    cm = G.centroid(outline)
    mouth = G.local(*ENTRANCE, LAT, LON)
    IN = (AXIS + 180) % 360
    length, width = f["passage_length_m"]["value"], f["passage_width_m"]["value"]
    end = G.toward(mouth, IN, length)
    rise = f["floor_rise_m"]["value"]
    on = lambda d, lat=0.0: G.toward(G.toward(mouth, IN, d), IN + 90, lat)            # noqa: E731
    floor = lambda d: rise * d / length                                                # noqa: E731
    # Heights above the entrance floor (derived, see DERIVED): the doorway 1.5 m high under its lintel; RS1 level at
    # 2.0-2.35 m to 3 m in; RS2 and the roof behind it 0.2 m higher (the slit, 18-22 cm, through which the nearly
    # level sunbeam passes over RS1); 2.4 m above the floor 6 m in; 3.6 m at RS17.
    RS1_LO, RS1_HI, SLIT, BOX = 2.0, 2.35, 0.22, 3.0
    rel = lambda d, z: round(z - floor(d), 3)                                            # noqa: E731
    roof_at = [(0, 1.5), (0.5, 1.5), (0.52, rel(0.52, RS1_LO)), (BOX - 0.01, rel(BOX, RS1_LO)),
               (BOX + 0.01, rel(BOX, RS1_HI + SLIT)), (6, 2.4), (length, f["passage_height_m"]["value"]["last_roofslab_RS17"])]
    path = [list(on(d)) for d, _ in roof_at]
    passage = {"kind": "passage", "path": path, "floor": [floor(d) for d, _ in roof_at], "width": width,
               "roof": [h for _, h in roof_at], "rock": "greywacke", "step": length / f["passage_roofslabs"]["value"],
               "roof_gap": [BOX - 0.02, BOX + 0.02], "roof_rough": 0.15, "title": "The passage",
               "note": f"{length} m long, about {width} m wide; 22 orthostats on the west side, 21 on the east; the floor rises about 2 m to the chamber.",
               "cites": cites("passage_length_m", "passage_width_m", "passage_orthostats", "floor_rise_m", "passage_height_m")}
    # The roof-box: side walls on RS1 leaving a channel 0.22 m wide and the slit's height, roofed by the box's front
    # roofstone (the decorated "false lintel"), from the facade to RS2.
    box = []
    for lat in (-0.425, 0.425):
        box.append({"kind": "stone", "c": list(on(BOX / 2, lat)), "len": BOX, "wid": 0.6, "az": IN, "h": SLIT + 0.05,
                    "base": RS1_HI, "rock": "greywacke", "interior": True, "rough": 0, "title": "The roof-box",
                    "note": el["roof-box"]["state"], "cites": cites("roofbox_size_m", "roofbox_slit", "roofbox_setback_m")})
    box.append({"kind": "stone", "c": list(on(BOX / 2)), "len": BOX + 0.3, "wid": 1.6, "az": IN, "h": 0.3,
                "base": RS1_HI + SLIT, "rock": "greywacke", "rough": 0.2, "title": "The roof-box and its decorated lintel",
                "note": f["roofbox_lintel"]["value"] + ".", "cites": cites("roofbox_size_m", "roofbox_lintel")})
    # The cruciform chamber in axis coordinates (a inward from the passage end, b to the right, i.e. east).
    L, Wd = f["chamber_size_m"]["value"]["length_entrance_to_back_of_end_recess"], f["chamber_size_m"]["value"]["width_west_to_east_recess"]
    dep = f["recess_depth_ft"]["value"]
    east, north, west = dep["east"] * 0.3048, dep["north"] * 0.3048, dep["west"] * 0.3048
    core_w = Wd - east - west
    L0, hw, rw = L - north, core_w / 2, 0.8
    a1, a2 = (L0 - 1.6) / 2, (L0 + 1.6) / 2
    ab = [(0, -hw), (a1, -hw), (a1, -hw - west), (a2, -hw - west), (a2, -hw), (L0, -hw), (L0, -rw), (L, -rw),
          (L, rw), (L0, rw), (L0, hw), (a2, hw), (a2, hw + east), (a1, hw + east), (a1, hw), (0, hw)]
    to_xy = lambda a, b: [round(v, 2) for v in G.toward(G.toward(end, IN, a), IN + 90, b)]      # noqa: E731
    chamber = {"kind": "chamber", "outline": [to_xy(a, b) for a, b in ab], "floor": rise,
               "h": f["recess_height_m"]["value"][0], "rock": "greywacke", "step": 1.1,
               "roof": {"kind": "corbel", "top": f["chamber_height_m"]["value"], "rings": 9},
               "open": [{"at": list(end), "width": width}], "title": "The chamber",
               "note": "Cruciform, with three recesses and a corbelled vault about 6 m high under a single capstone; the vault is original.",
               "cites": cites("chamber_size_m", "chamber_height_m", "recess_height_m", "recess_depth_ft")}
    basins = []
    for key, (a, b), size in [("basin_west", ((a1 + a2) / 2, -hw - west / 2), el["basin_west"]["size_m"]),
                              ("basin_east_lower", ((a1 + a2) / 2, hw + east / 2), el["basin_east_lower"]["size_m"]),
                              ("basin_north", (L0 + north / 2, 0), el["basin_north"]["size_m"])]:
        basins.append({"kind": "stone", "c": to_xy(a, b), "len": size[0], "wid": size[1], "az": IN, "h": 0.35, "z": rise,
                       "base": 0, "rock": "granite", "interior": True, "title": "Basin stone",
                       "note": f"{el[key]['recess']} recess: {el[key].get('shape', el[key].get('state', ''))}.",
                       "cites": cite(r, el[key].get("cites"))})
    # Mound, kerb, facade.
    gap_az = G.bearing(cm, mouth)
    mound = {"kind": "mound", "c": list(cm), "radii": G.radii(outline, cm, 2), "h": f["mound_height_m"]["value"],
             "kerb_h": f["kerbstone_height_m"]["value"], "p": 0.75, "surface": "grass", "kerb_rock": "cairn",
             "facade": {"from": gap_az - 55, "to": gap_az + 55, "rock": "quartz", "h": f["facade_height_m"]["value"]},
             "gap": {"az": gap_az, "width": 1.4, "open": [[0, 1.5], [RS1_HI, RS1_HI + SLIT]]}, "title": "The mound",
             "note": f"About 79-85 m across and 11 m high (sources give 11-13 m); {f['cairn_material']['value']}.",
             "cites": cites("mound_max_diameter_m", "mound_height_m", "cairn_material", "facade_height_m", "facade_material")}
    # K1 at the entrance, numbered clockwise seen from above (K2 to the west of it, K97 to the east).
    pts = G.along(outline, f["kerbstone_count"]["value"], inset=-0.3)
    a0 = G.bearing(cm, mouth)
    half_step = 180 / len(pts)
    pts.sort(key=lambda q: (G.bearing(cm, q[:2]) - a0 + 360 + half_step) % 360)
    kerbs = []
    for num, (x, y, az) in enumerate(pts, 1):
        e = el.get(f"K{num}", {})
        kerbs.append({"kind": "stone", "c": [x, y], "len": 2.5, "wid": 0.45, "az": az,
                      "h": f["kerbstone_height_m"]["value"], "rock": "greywacke", "label": f"K{num}", "num": num,
                      "title": e.get("name", f"Kerbstone K{num}"),
                      "note": e.get("state", "One of the 97 kerbstones laid end to end round the mound."),
                      "cites": cites("kerbstone_count", "kerbstone_length_m")})
    circle = [{"kind": "stone", "outline": G.polygon(c, 0.55, 7, start=i * 13), "h": 2.0, "rock": "greywacke",
               "title": "Great Circle stone", "note": el["great_circle"].get("numbering", ""),
               "cites": cite(r, el["great_circle"].get("cites"))} for i, (_, c) in enumerate(menhirs)]
    door = {"kind": "stone", "c": list(on(-0.35)), "len": 1.5, "wid": 0.3, "az": IN + 90, "h": 1.55, "rock": "greywacke",
            "title": "The closing stone", "note": el["doorstone"]["state"], "cites": cite(r, el["doorstone"].get("cites"))}
    door_now = {**door, "c": list(G.toward(on(-0.6), IN + 90, 1.6)), "status": "reconstructed"}
    common = [mound, passage, chamber] + box + basins
    now = common + [k for k in kerbs if not 22 <= k["num"] <= 46] + circle + [door_now]
    built = common + kerbs + circle + [door]
    for k in kerbs:
        k.pop("num", None)
    ch = to_xy(L0 / 2 + 0.6, 0)
    cams = {
        "overview": {"label": "Overview from the south-east", "from": [*G.toward(cm, AXIS + 18, 120), 28], "to": [*cm, 4]},
        "entrance": {"label": "Outside, facing the entrance and roof-box", "from": list(on(-14)), "to": [*on(0), 2.0], "fov": 50, "standing": True},
        "chamber": {"label": "In the chamber, facing the passage", "from": [*ch, rise + 1.5], "to": [*on(0), 1.9], "fov": 60, "standing": True},
        "floor": {"label": "In the chamber, the floor where the beam falls", "from": [*to_xy(L - 0.4, 0.3), rise + 1.6], "to": [*to_xy(0.5, 0), rise], "fov": 65, "standing": True},
        "above": {"label": "From above", "from": [cm[0], cm[1] - 0.01, 140], "to": [*cm, 0], "fov": 45},
    }
    facts = G.facts(r, [
        ("mound_max_diameter_m", "The mound is 79-85 m across."),
        ("mound_height_m", "The mound is 11 m high (sources give 11-13 m)."),
        ("kerbstone_count", "97 kerbstones surround it."),
        ("passage_length_m", "The passage is 18.9 m long (24 m with the chamber)."),
        ("floor_rise_m", "Its floor rises about 2 m from the entrance to the chamber."),
        ("roofbox_slit", "The roof-box slit is 20-25 cm wide and 18-22 cm high."),
        ("chamber_height_m", "The corbelled vault of the chamber is about 6 m high."),
        ("passage_azimuth_deg", "Sunlight can reach the chamber when the sun is between azimuths 133°49′ and 137°29′ (Ray)."),
    ], cite) + [{"text": a["claim"], "cites": cite(r, a.get("cites"))} for a in r["alignment"][:3]] + \
        [{"text": t, "cites": []} for t in DERIVED]
    return {"name": "Newgrange", "record": r["record"], "lat": LAT, "lon": LON, "size": 600, "step": 2,
            "flatten": {"c": list(cm), "r": 44, "edge": 14}, "shadow": {"half": 48, "centre": list(cm)},
            "views": {"now": now, "built": built}, "built_year": -3199, "cams": cams,
            "events": ["winter_rise", "summer_rise", "equinox_rise"], "face": {"winter_rise": "chamber"},
            "start": {"event": "winter_rise", "after": 7,
                      "note": "Midwinter sunrise this year, a few minutes after the first gleam: the beam comes through the roof-box, up the passage and onto the chamber floor. Try Play at 1 minute a second, and “Lantern” to see inside."},
            "axis": [AXIS], "axis_length": 140, "facts": facts, "about": [r["about"]],
            "built_label": "As built (c. 3200 BC)", "lantern": True, "axis_label": "Light window (middle)",
            "labels_label": "Kerbstone numbers"}
