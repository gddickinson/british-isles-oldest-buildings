"""3D model of Bryn Celli Ddu (roadmap SH3b), from `data/curated/models/bryn_celli_ddu.json` (bidb.models3d).

Placed by OpenStreetMap: the kerb ring (way 919723575, the edge of the final mound) and the covered passage (way
1367245454, which runs from the middle of the ring out to the north-east). The passage is set on that line at the
azimuth Lockyer measured (52°), its chamber end 1.2 m (half the chamber's width) out from the way's inner end.
Measurements are the research file's; what no reachable source gives is drawn and said so in `DERIVED`: the size of
the modern mound, the chamber as a regular octagon, the height of the kerb, the replica Pattern Stone's place behind
the chamber. The stones of the inner circle are not drawn: no published positions.
"""
import math

from . import model_geometry as G
from .models3d import cite, research

LAT, LON = 53.207725, -4.236067          # Coflein SH5076170185 (research: reference_point_grid)
AZ = 52.0                                # passage, looking out (Lockyer 1909)
DERIVED = [
    "The passage lies on the OpenStreetMap line of the covered passage, at the azimuth Lockyer measured (52°); its "
    "outer 3.4 m is unroofed, as now.",
    "The chamber is drawn as a regular octagon 2.4 m across with six uprights; its true outline (Hemp's plan) is not "
    "openly available.",
    "No source gives the modern mound's size: it is drawn just covering the chamber and the roofed passage.",
    "As built: the mound out to the kerb ring mapped on OpenStreetMap, 3.7 m high (Hemp's 'at least 12 ft'); the "
    "kerb's height is not published (drawn 1 m).",
    "The replica Pattern Stone is drawn 3 m behind the chamber; the stones of the inner circle are not drawn, since "
    "no positions are published.",
]


def _ways():
    res = G.request_json(G.OVERPASS, data={"data": "[out:json];(way(919723575);way(1367245454););out tags geom;"},
                         method="POST", min_interval=2)
    ways = {e["id"]: [G.local(p["lat"], p["lon"], LAT, LON) for p in e["geometry"]] for e in res["elements"]}
    ring = ways[919723575]
    return (ring[:-1] if ring[0] == ring[-1] else ring), ways[1367245454]


def spec():
    r = research("bryn_celli_ddu")
    f = r["facts"]
    ring, way = _ways()
    rc = G.centroid(ring)
    inner = min(way, key=lambda p: math.dist(p, rc))
    chamber_c = G.toward(inner, AZ, f["chamber_width_m"]["value"] / 2)
    half = f["chamber_width_m"]["value"] / 2
    length = f["passage_length_m"]["value"]
    pw = f["passage_width_height_m"]["value"]
    end = G.toward(chamber_c, AZ, half)                       # passage meets the chamber
    mouth = G.toward(end, AZ, length)
    octagon = G.polygon(chamber_c, half / math.cos(math.pi / 8), 8, start=AZ + 22.5)
    ch_h = f["chamber_height_m"]["value"]
    cites = lambda *keys: [c for k in keys for c in cite(r, f[k]["cites"])]        # noqa: E731
    el = {e["id"]: e for e in r["elements"]}
    passage = {"kind": "passage", "path": [list(mouth), list(end)], "width": pw["width_m"], "roof": pw["height_m"],
               "rock": "schist", "step": length / 5, "roof_gap": [0, 3.4], "title": "Passage",
               "note": f"{length} m long, the outer 3.4 m unroofed between the portal stones; about "
                       f"{pw['width_m']} m wide and {pw['height_m']} m high (Pennant, Anwyl).",
               "cites": cites("passage_length_m", "passage_width_height_m", "passage_azimuth_deg")}
    chamber = {"kind": "chamber", "outline": octagon, "h": ch_h, "rock": "schist", "step": 1.25,
               "open": [{"at": list(end), "width": pw["width_m"]}], "roof": {"kind": "capstone", "thickness": 0.5},
               "title": "Chamber", "note": "Polygonal, six large uprights with drystone walling, two capstones.",
               "cites": cites("chamber_width_m", "chamber_uprights", "chamber_capstones", "chamber_height_m")}
    pillar = {"kind": "stone", "outline": G.polygon(G.toward(chamber_c, 0, half * 0.62), 0.23, 9),
              "h": f["pillar_height_m"]["value"], "rock": "schist", "interior": True, "title": "The pillar",
              "note": el["pillar"]["stone"] + "; " + el["pillar"]["state"] + ".", "cites": cites("pillar_height_m")}
    ps = f["pattern_stone_size_mm"]["value"]
    pattern = {"kind": "stone", "c": list(G.toward(chamber_c, AZ + 180, 3)), "len": ps["width"] / 1000,
               "wid": ps["thickness"] / 1000, "az": AZ + 90, "h": ps["height"] / 1000, "rock": "sandstone",
               "status": "reconstructed", "title": "The Pattern Stone (cast)",
               "note": el["pattern_stone_replica"]["state"] + ".", "cites": cites("pattern_stone_size_mm")}
    gap_now = {"az": AZ, "width": pw["width_m"] + 0.2, "open": [[0, pw["height_m"]]]}
    ring_r = [round(v, 2) for v in G.radii(ring, rc, 2)]
    mouth_az = G.bearing(rc, mouth)
    built_mound = {"kind": "mound", "c": list(rc), "radii": ring_r, "h": f["original_mound_height_m"]["value"],
                   "kerb_h": 1.0, "p": 0.9, "kerb_rock": "schist",
                   "gap": {"az": mouth_az, "width": pw["width_m"] + 0.6, "open": [[0, pw["height_m"]]]},
                   "title": "The mound as built", "note": "Out to the kerb ring, 26 m across.",
                   "cites": cites("kerb_diameter_m", "original_mound_height_m")}
    now = [
        {"kind": "mound", "c": list(chamber_c), "r": half + length - 3.4 + 0.3, "h": ch_h + 0.9, "kerb_h": 0.05,
         "facade": {"from": AZ - 14, "to": AZ + 14, "rock": "schist", "h": pw["height_m"] + 0.45},
         "p": 0.7, "kerb_rock": "schist", "gap": gap_now, "title": "The modern mound",
         "note": "Rebuilt in 1928-29 over the passage and chamber only (size not published).",
         "cites": cites("modern_mound_extent")},
        passage, chamber, pillar, pattern,
        {"kind": "bank", "c": list(rc), "r": f["ditch_diameter_m"]["value"] / 2, "w": f["ditch_width_depth"]["value"]["width_m"],
         "h": -0.3, "gaps": [[mouth_az, 3.0]], "title": "The henge ditch", "note": "21 m across, about 5 m wide; silted.", "cites": cites("ditch_diameter_m", "ditch_width_depth")},
        {"kind": "bank", "c": list(rc), "r": sum(ring_r) / len(ring_r), "w": 1.6, "h": 0.25, "gaps": [[mouth_az, 3.0]], "title": "The kerb line",
         "note": "The ring mapped on OpenStreetMap, the edge of the final mound.", "cites": cites("kerb_diameter_m")},
    ]
    built = [built_mound, passage, chamber, {**pillar}]
    eye = G.toward(chamber_c, AZ + 180, half * 0.55)
    cams = {
        "overview": {"label": "Overview from the north-east", "from": [*G.toward(chamber_c, AZ, 30), 9], "to": [*chamber_c, 1]},
        "entrance": {"label": "Outside, facing the entrance", "from": list(G.toward(chamber_c, AZ, 16)), "to": [*chamber_c, 1.0], "fov": 50, "standing": True},
        "chamber": {"label": "In the chamber, facing the passage (crouching)", "from": [*eye, 0.75], "to": [*G.toward(chamber_c, AZ, 12), 0.55], "fov": 70, "standing": True},
        "above": {"label": "From above", "from": [chamber_c[0], chamber_c[1] - 0.01, 45], "to": [*chamber_c, 0], "fov": 40},
    }
    facts = G.facts(r, [
        ("passage_azimuth_deg", "The passage faces 51-52° from true north, towards the midsummer sunrise (Lockyer's readings)."),
        ("passage_length_m", "The passage is 8.4 m long, the outer 3.4 m unroofed."),
        ("passage_width_height_m", "The roofed passage is about 0.9 m wide and 1 m high."),
        ("chamber_width_m", "The chamber is about 2.4 m across (sources give 2-3 m)."),
        ("chamber_height_m", "The chamber is about 2.7 m high (Skinner 1802)."),
        ("pillar_height_m", "The free-standing pillar is 1.7 m high (or about 2 m)."),
        ("kerb_diameter_m", "The kerb of the final mound is 26 m across."),
        ("original_mound_height_m", "The original mound stood at least 3.7 m high."),
        ("ditch_diameter_m", "The earlier ditch is 21 m across."),
        ("modern_mound_extent", "The modern mound covers only the passage and chamber."),
    ], cite) + [{"text": t, "cites": []} for t in DERIVED]
    return {"name": "Bryn Celli Ddu", "record": r["record"], "lat": LAT, "lon": LON, "size": 400, "step": 1,
            "flatten": {"c": list(rc), "r": 15.5, "edge": 8},
            "shadow": {"half": 24, "centre": list(chamber_c)},
            "views": {"now": now, "built": built}, "built_year": -2999, "cams": cams,
            "events": ["summer_rise", "summer_set", "winter_rise"], "face": {"summer_rise": "chamber"},
            "start": {"event": "summer_rise", "after": 6,
                      "note": "Midsummer sunrise this year, a few minutes after the first gleam: the light runs down the passage into the chamber. Try “Lantern” to see inside, and Play."},
            "axis": [AZ], "axis_length": 80, "facts": facts, "about": [r["about"]],
            "built_label": "As built (c. 3000 BC)", "lantern": True, "axis_label": "Passage axis",
            "labels_label": "Labels"}
