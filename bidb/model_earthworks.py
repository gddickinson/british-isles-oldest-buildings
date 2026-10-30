"""3D models of four earthworks from the Environment Agency's 1 m LiDAR (roadmap SH4b), from
`data/curated/models/earthworks.json`: Avebury (the henge in the ground model, its stones from OpenStreetMap), Silbury
Hill, Maiden Castle and the Uffington White Horse with its hillfort and Dragon Hill. The ground model is the monument:
banks, ditches, ramparts and mounds as the survey measured them (bare earth: buildings and trees left out). The modules
model_avebury, model_silbury, model_maiden_castle and model_uffington call these.
"""
import math

from . import model_geometry as G
from .models3d import cite, research

STONE_TAGS = ["[historic=standing_stone]", "[historic=menhir]", "[megalith_type=menhir]", "[natural=bare_rock]", "[natural=stone]"]


def _site(key):
    r = research("earthworks")
    s = r["sites"][key]
    ref = s.get("reference_point") or s.get("reference_position")
    return r, s, ref["lat"], ref["lon"]


def _facts(r, s, n=12):
    """The site's facts as page lines: name, value and unit, with their quoted sources."""
    out = []
    for k, f in list(s["facts"].items())[:n]:
        v = f.get("value")
        if isinstance(v, (dict, list)):
            v = ", ".join(f"{a}: {b}" for a, b in v.items()) if isinstance(v, dict) else "-".join(map(str, v))
        unit = f.get("unit", "")
        out.append({"text": f"{k.replace('_m3', '').replace('_m', '').replace('_', ' ').capitalize()}: {v}{' ' + unit if unit and unit not in str(v) else ''}"
                            + (f" ({f['note'][:160]})" if f.get("note") else ""), "cites": cite(r, f.get("cites"))})
    return out


def _spec(name, s, lat, lon, size, step, parts, cams, facts, derived, events=("summer_rise", "winter_set", "winter_rise", "summer_set", "equinox_rise")):
    return {"name": name, "record": s["record"], "lat": lat, "lon": lon, "ground": "ea", "size": size, "step": step,
            "shadow": {"half": min(size / 2, 220), "centre": [0, 0]}, "views": {"now": parts}, "cams": cams,
            "events": list(events), "start": {"m": 6, "d": 21, "t": 600},
            "facts": facts + [{"text": t, "cites": []} for t in derived + [
                "The ground is the Environment Agency's 1 m LiDAR terrain model (bare earth: buildings and trees are "
                "left out), averaged to " + f"{step} m."]],
            "about": [s.get("about", "")], "labels_label": "Labels"}


def avebury():
    r, s, lat, lon = _site("avebury")
    f = s["facts"]
    hv = f["outer_circle_stone_height_m"]["value"]
    nums = [float(x) for x in (hv if isinstance(hv, list) else str(hv).replace("–", "-").split("-"))]
    h_default = sum(nums) / len(nums)                    # the middle of the published range
    parts = []
    for e in G.osm(lat, lon, 260, STONE_TAGS):
        if len(e["points"]) < 4:
            continue
        pts = [G.local(a, b, lat, lon) for a, b in e["points"]][:-1]
        area = abs(sum(pts[i - 1][0] * pts[i][1] - pts[i][0] * pts[i - 1][1] for i in range(len(pts)))) / 2
        small = area < 2
        parts.append({"kind": "stone", "outline": [[round(x, 2), round(y, 2)] for x, y in pts], "h": 1.0 if small else round(h_default, 1),
                      "rock": "sandstone", "title": "A stone (or a marker)" if small else "A stone",
                      "note": f"Mapped on OpenStreetMap ({e['id']}); " + ("a small outline: a small stone or one of the concrete pillars marking a lost stone."
                              if small else f"drawn at the published average height of the outer circle's stones ({h_default:.1f} m)."),
                      "cites": cite(r, f["outer_circle_stone_height_m"].get("cites"))})
    cams = {"overview": {"label": "From the south-west", "from": [-260, -300, 120], "to": [0, 0, 0]},
            "inside": {"label": "In the southern inner circle, facing north", "from": [-40, -60], "to": [0, 120, 3], "fov": 65, "standing": True},
            "bank": {"label": "On the bank, south-east", "from": [*G.toward((0, 0), 140, 195), 6], "to": [0, 0, 1], "fov": 60, "standing": True},
            "above": {"label": "From above", "from": [0, -0.01, 650], "to": [0, 0, 0], "fov": 45}}
    return _spec("Avebury", s, lat, lon, 900, 2, parts, cams, _facts(r, s, 16),
                 [f"{len(parts)} stones or markers are drawn on their OpenStreetMap outlines; none is numbered there, so "
                  "they cannot be told apart by name; outlines under 2 m² are drawn 1 m high (small stones or concrete "
                  "pillars), the rest at the outer circle's published average height."])


def silbury():
    r, s, lat, lon = _site("silbury")
    cams = {"overview": {"label": "From the south", "from": [30, -320, 40], "to": [0, 0, 18]},
            "top": {"label": "On the summit, facing north", "from": [0, 0, 1.6], "to": [0, 200, -10], "fov": 70, "standing": True},
            "above": {"label": "From above", "from": [0, -0.01, 500], "to": [0, 0, 0], "fov": 45}}
    return _spec("Silbury Hill", s, lat, lon, 700, 2, [], cams, _facts(r, s, 14), [])


def maiden_castle():
    r, s, lat, lon = _site("maiden_castle")
    cams = {"overview": {"label": "From the south-west", "from": [-700, -520, 220], "to": [0, 0, 0]},
            "east": {"label": "The eastern entrance", "from": [520, -40, 4], "to": [0, 0, 20], "fov": 55, "standing": True},
            "above": {"label": "From above", "from": [0, -0.01, 1100], "to": [0, 0, 0], "fov": 50}}
    return _spec("Maiden Castle", s, lat, lon, 1400, 3, [], cams, _facts(r, s, 11), [])


def uffington():
    r, s, lat, lon = _site("uffington")
    cams = {"overview": {"label": "From the north (the Vale)", "from": [0, 650, 140], "to": [0, 0, 0]},
            "horse": {"label": "Above the horse", "from": [0, 70, 60], "to": [0, 0, 0], "fov": 55},
            "above": {"label": "From above", "from": [0, -0.01, 700], "to": [0, 0, 0], "fov": 50}}
    return _spec("Uffington White Horse", s, lat, lon, 1000, 2, [], cams, _facts(r, s, 17),
                 ["The horse's chalk lines are cut only shallowly and show faintly, if at all, in the 1 m ground "
                  "model; its OpenStreetMap outline is not drawn (it runs north-south, against the published "
                  "north-east to south-west)."])
