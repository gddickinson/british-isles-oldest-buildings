"""3D models built from published dimensions alone (roadmap SH4c), from `data/curated/models/old_plans.json`: six
round towers (part kind "tower", app/static/model_tower.js) and four brochs (part kind "broch", model_broch.js), each
at its catalogue record's position, with what had to be assumed listed on the page. The modules model_rt_<name> and
model_broch_<name> call `round_tower(key)` and `broch(key)`.
"""
import math
import re
import sqlite3

from .config import db_path
from .models3d import cite, research

FT = 0.3048
DIRS = {"north": 0, "north-east": 45, "east": 90, "south-east": 135, "south": 180, "south-west": 225, "west": 270, "north-west": 315}


def ft(text):
    """'9 ft 3 in' → metres (the first measurement in the text)."""
    m = re.search(r"(\d+(?:\.\d+)?)\s*ft(?:\s*(\d+(?:\.\d+)?)\s*in)?", str(text))
    return round((float(m.group(1)) + (float(m.group(2)) / 12 if m.group(2) else 0)) * FT, 2) if m else None


def _site(group, key):
    r = research("old_plans")
    s = r["sites"][group][key]
    row = sqlite3.connect(db_path()).execute("select lat, lon from buildings where id = ?", (s["record"],)).fetchone()
    cites = [c for f in s["facts"].values() for c in cite(r, f.get("cites"))]
    return r, s, row[0], row[1], cites


def _facts(r, s):
    out = []
    for k, f in s["facts"].items():
        v = f.get("value")
        if isinstance(v, dict):
            v = ", ".join(f"{a.replace('_', ' ')} {b}" for a, b in v.items())
        out.append({"text": f"{k.replace('_m', '').replace('_deg', '').replace('_ft', '').replace('_', ' ').capitalize()}: {v}"
                    + (f" ({f['note'][:150]})" if f.get("note") else ""), "cites": cite(r, f.get("cites"))})
    return out


def _spec(name, s, lat, lon, parts, cams, facts, derived, about, view_label=None, cut=None):
    out = {"name": name, "record": s["record"], "lat": lat, "lon": lon, "size": 300, "step": 2,
           "flatten": {"c": [0, 0], "r": 12, "edge": 8}, "shadow": {"half": 25, "centre": [0, 0]},
           "views": {"now": parts}, "cams": cams, "events": ["summer_rise", "winter_set", "equinox_rise", "summer_set"],
           "start": {"m": 6, "d": 21, "t": 600}, "facts": facts + [{"text": t, "cites": []} for t in derived],
           "about": [about], "labels_label": "Labels"}
    if cut:
        out["views"]["built"] = cut
        out["built_label"] = view_label
    return out


def round_tower(key):
    r, s, lat, lon, cites = _site("round_towers", key)
    f = {k: v.get("value") for k, v in s["facts"].items()}
    derived = []
    h = f["height_m"]
    if f.get("diameter_m"):
        d = f["diameter_m"]
    elif f.get("circumference_ft"):
        d = round(f["circumference_ft"] * FT / math.pi, 2)
        derived.append(f"Diameter {d} m from the published circumference of {f['circumference_ft']} ft.")
    elif ft(f.get("diameter_ft")):
        d = ft(f["diameter_ft"])
    else:
        d = 4.9
        derived.append("The diameter is not published in a reachable source: drawn 4.9 m.")
    door = f.get("door") if isinstance(f.get("door"), dict) else {}
    sill = door.get("sill_above_ground_m") or f.get("door_sill_above_ground_m") or (door.get("sill_above_ground_ft") or 0) * FT or 3.5
    dh = door.get("height_m") or f.get("door_height_m") or (door.get("height_ft") or 0) * FT or 1.6
    az = door.get("azimuth_deg") or f.get("door_azimuth_deg") or DIRS.get(door.get("faces"), None)
    if az is None:
        az = 90
        derived.append("The door's direction is not published: drawn facing east.")
    cap_text = str(f.get("cap") or f.get("top") or "")
    if "spire" in cap_text:
        cap = {"kind": "spire", "h": 5.5}
    elif "crenel" in cap_text:
        cap = {"kind": "crenel", "h": 0.8}
    elif "flat" in cap_text or "no cap" in cap_text:
        cap = {"kind": "flat", "h": 0}
    else:
        cap = {"kind": "cone", "h": round(d * 1.05, 1)}
    shaft = round(h - cap["h"], 1) if cap["kind"] in ("cone", "spire") else h
    derived.append(f"The shaft is drawn {shaft} m high under a {cap['kind']} {cap['h']} m high (published total {h} m), "
                   f"tapering to 82% of its base width; windows are drawn one per storey under the top, facing round.")
    storeys = f.get("storeys")
    n = int(re.match(r"\d+", str(storeys)).group()) if storeys and re.match(r"\d+", str(storeys)) else 5
    windows = [{"z": sill + (shaft - sill) * (i + 1) / (n + 1), "az": (az + 90 * (i + 1)) % 360} for i in range(n - 1)]
    windows += [{"z": shaft - 1.4, "az": (az + a) % 360, "h": 0.9} for a in (0, 90, 180, 270)]
    part = {"kind": "tower", "c": [0, 0], "h": shaft, "d_base": d, "d_top": round(d * 0.82, 2), "plinth": 0.4, "cap": cap,
            "door": {"sill": sill, "h": dh, "w": 0.6, "az": az}, "windows": windows,
            "rock": "granite" if "granite" in str(f.get("material", "")) else "flagstone",
            "title": s["name"], "note": str(f.get("cap") or f.get("top") or ""), "cites": cites}
    cams = {"overview": {"label": "From the door's side", "from": [*_toward(az, 28), 4], "to": [0, 0, h / 2]},
            "foot": {"label": "At the foot, looking up", "from": [*_toward(az, 6)], "to": [0, 0, h], "fov": 70, "standing": True}}
    return _spec(s["name"], s, lat, lon, [part], cams, _facts(r, s), derived, s.get("about", s["name"]))


def _toward(az, d):
    return [round(d * math.sin(math.radians(az)), 2), round(d * math.cos(math.radians(az)), 2)]


def broch(key):
    r, s, lat, lon, cites = _site("brochs", key)
    f = {k: v.get("value") for k, v in s["facts"].items()}
    derived = []
    if f.get("diameters_m"):
        ext, court = f["diameters_m"]["external"], f["diameters_m"]["internal"]
    elif f.get("diameter_ft"):
        ext, court = f["diameter_ft"]["overall"] * FT, f["diameter_ft"]["court"] * FT
    elif isinstance(f.get("diameter_m"), dict):
        ext, court = f["diameter_m"]["overall"], f["diameter_m"]["court"]
    else:
        ext, court = f["diameter_m"], f["court_diameter_m"]
    hv = f.get("height_m") or f.get("height")
    nums = [float(x) for x in re.findall(r"(\d+(?:\.\d+)?)\s*m\b", str(hv))] if not isinstance(hv, (int, float)) else [hv]
    h = nums[0] if nums else (ft(hv) or 5.0)
    gal = f.get("galleries")
    ng = gal if isinstance(gal, int) else int(re.match(r"\d+", str(gal)).group()) if re.match(r"\d+", str(gal)) else \
        {"two": 2, "three": 3, "four": 4}.get(str(gal).split()[0], 2)
    z0 = 3.0
    step = max(1.6, (h - z0 - 0.4) / max(1, ng))
    galleries = [[round(z0 + i * step, 2), round(z0 + i * step + step - 0.25, 2)] for i in range(ng) if z0 + i * step + step - 0.25 < h - 0.2]
    ent = f.get("entrance", {})
    az = DIRS.get(ent.get("faces"), 270)
    derived += [f"The outer face is drawn tapering to 85% of its base width; galleries {len(galleries)} evenly from 3 m up "
                "(their own levels are on the old plans, not yet read); the stair is drawn a quarter turn per gallery.",
                f"The entrance faces {ent.get('faces', 'west')} ({az}°), 1.0 m wide and 1.6 m high unless published."]
    part = {"kind": "broch", "c": [0, 0], "h": h, "r_base": ext / 2, "r_top": round(ext / 2 * 0.85, 2), "court_r": court / 2,
            "solid_h": z0, "galleries": galleries, "gallery_w": 0.8,
            "entrance": {"az": az, "width": ent.get("width_m", 1.0), "h": ent.get("height_m", 1.6)},
            "stair": {"az0": (az - 90) % 360, "z0": 1.5, "z1": h - 0.4, "turn": 90 * max(1, len(galleries)), "width": 0.75},
            "ledges": [x * FT for x in f["scarcements_ft"]] if f.get("scarcements_ft") else ([f["scarcement_m"]] if f.get("scarcement_m") else []),
            "rock": "flagstone", "title": s["name"], "note": str(f.get("galleries", "")), "cites": cites}
    cams = {"overview": {"label": "From the entrance side", "from": [*_toward(az + 20, 30), 8], "to": [0, 0, h / 2]},
            "court": {"label": "In the court, looking up", "from": [0.5, -1.0], "to": [-0.5, 1.5, h], "fov": 75, "standing": True},
            "cut": {"label": "Facing the cutaway", "from": [*_toward(az + 145, 26), h * 0.7], "to": [0, 0, h / 2]}}
    return _spec(s["name"], s, lat, lon, [part], cams, _facts(r, s), derived, s.get("about", s["name"]),
                 "Cutaway (a quarter of the wall left out)", [{**part, "cut": [(az + 100) % 360, (az + 190) % 360]}])
