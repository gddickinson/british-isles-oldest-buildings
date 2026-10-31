"""Stonehenge by stages (roadmap SH2a), read by bidb.stonehenge: the five stages of Darvill, Marshall, Parker Pearson
and Wainwright 2012 with what stood at each, from the researched file `data/curated/stonehenge/stages.json` (every
number quoted) and the model's own data.

    ditch_ring(height)     the henge ditch fitted in the LiDAR ground: the lowest point every 3° (away from the
                           entrance, the road and the Avenue), a circle fitted to them → centre, radius, bank crest
    aubrey(centre, osm)    the 56 Aubrey Holes on a 43.2 m circle round the enclosure's centre (Lawson: the same
                           centre), numbered clockwise from the north-east entrance, turned to the seven holes marked on
                           OpenStreetMap (26-32)
    claims(), problems()   the research file's quotes as evidence claims (`python -m bidb.stonehenge --quotes`) and
                           citations of sources it does not list
    stages(...)            per stage: dates, the year its sky is shown for, what was built, the pieces of the completed
                           monument standing then (by group), the earthwork, holes, posts and stones of its own
"""
import json
import math
import os

from . import stonehenge_layout as L
from .config import ROOT

HERE = os.path.join(ROOT, "data", "curated", "stonehenge")
SKIP = ((25, 75), (150, 200), (300, 340))       # entrance and Avenue, south entrance, the old road's verge
EAST_RECUT = (0, 180)                           # Hawley dug out the eastern half of the ditch in the 1920s


def research():
    with open(os.path.join(HERE, "stages.json")) as f:
        return json.load(f)


def claims():
    from .models3d import _cites as cites_in
    r = research()
    by = {}
    for c in cites_in({k: v for k, v in r.items() if k != "sources"}):
        s = r["sources"].get(c["source"])
        if s and s.get("url"):
            by.setdefault(c["source"], []).append({"title": s["title"], "url": s["url"], "quote": c["quote"],
                                                   "kind": "reference"})
    return [{"id": f"model-stonehenge-stages-{k}", "record": r.get("record"), "name": "Stonehenge", "field": "model",
             "claim": "the stages of the 3D model of Stonehenge", "verdict": "documented", "sources": v}
            for k, v in by.items()]


def problems():
    from .models3d import _cites as cites_in
    r = research()
    return [f"stages: unknown source {c['source']}" for c in cites_in({k: v for k, v in r.items() if k != "sources"})
            if c["source"] not in r["sources"]]


def _value(r, key):
    return r["facts"][key]["value"]


def ditch_ring(height, r0=44, r1=62):
    """Lowest point of the ditch along each azimuth (today's LiDAR, metres from the model's origin) → circle."""
    pts, crest = [], []
    for az in range(0, 360, 3):
        if any(a <= az <= b for a, b in SKIP):
            continue
        prof = [(r / 4, height(*L.at((0, 0), r / 4, az))) for r in range(r0 * 4, r1 * 4 + 1)]
        if any(h is None for _, h in prof):
            continue
        (ra, ha), (rb, hb) = prof[0], prof[-1]
        flat = [(r, h - (ha + (hb - ha) * (r - ra) / (rb - ra))) for r, h in prof]     # take away the slope
        low = min(flat, key=lambda p: p[1])
        top = max((p for p in flat if p[0] < low[0]), key=lambda p: p[1])
        pts.append(L.at((0, 0), low[0], az))
        crest.append(top[0])
    cx, cy, r = L.fit_circle(pts)
    crest.sort()
    return {"centre": [round(cx, 2), round(cy, 2)], "radius": round(r, 2), "bank_crest": round(crest[len(crest) // 2], 2),
            "points": len(pts)}


def aubrey(centre, osm, radius, count=56):
    """Hole positions [(n, x, y)] numbered clockwise; the first hole's azimuth fitted to the OSM holes."""
    step = 360 / count
    marked = [(int(f["ref"]), L.centroid([L.local(a, b, *osm["origin"]) for a, b in f["outline"]]))
              for f in osm["features"] if f["name"] == "Aubrey Hole" and (f.get("ref") or "").isdigit()]
    offs = [((L.azimuth(p, centre) - (n - 1) * step + 180) % 360) - 180 for n, p in marked]
    first = sum(offs) / len(offs) % 360 if offs else 55.5
    holes = [(n, *L.at(centre, radius, first + (n - 1) * step)) for n in range(1, count + 1)]
    miss = [math.dist(p, holes[n - 1][1:]) for n, p in marked]
    return holes, {"first_azimuth": round(first, 2), "marked": len(marked),
                   "rms_m": round(math.sqrt(sum(m * m for m in miss) / len(miss)), 2) if miss else None}


def _ring(centre, r, n, start, d, kind, prefix, skip=()):
    return [{"kind": kind, "id": f"{prefix}{k + 1}", "x": round(x, 2), "y": round(y, 2), "d": d}
            for k in range(n) if k + 1 not in skip
            for x, y in [L.at(centre, r, start + k * 360 / n)]]


def _cites(r, *keys):
    src = r["sources"]
    out = []
    for k in keys:
        item = r["facts"].get(k) or next((e for e in r["elements"] if e["id"] == k), None) or {}
        for c in item.get("cites", [])[:2]:
            s = src.get(c["source"])
            if s:
                out.append({"title": s["title"], "url": s["url"], "quote": c["quote"]})
    return out


def stages(ring, osm, height):
    """The stages for stonehenge.json. ring: the sarsen ring of the completed model; osm: {origin, features}."""
    r = research()
    fit = ditch_ring(height)
    centre = tuple(fit["centre"])
    holes, hfit = aubrey(centre, osm, _value(r, "aubrey_circle_radius_m"))
    sc = tuple(ring["centre"])
    qr = _value(r, "qr_diameters_m")
    y, z = _value(r, "y_holes"), _value(r, "z_holes")
    axis = L.AXIS
    # The north-east half of the Q and R circles (the known double arc), a setting every 9° (40 if complete).
    arc = [a for a in range(0, 360, 9) if abs(((a - axis + 180) % 360) - 180) <= 85 and abs(((a - axis + 180) % 360) - 180) > 4]
    qr_stones = [{"kind": "bluestone", "id": "", "x": round(p[0], 2), "y": round(p[1], 2), "d": 0.6, "h": 2.0, "turn": a}
                 for a in arc for rad in (qr["Q_outer"] / 2, qr["R_inner"] / 2) for p in [L.at(sc, rad, a)]]
    central = [{"kind": "bluestone", "id": "", "x": round(p[0], 2), "y": round(p[1], 2), "d": 0.55, "h": 1.8,
                "turn": a} for a in range(0, 360, 15) for p in [L.at(L.at(sc, 1.5, axis + 180), 5, a)]]
    earth = {"centre": list(centre), "ditch_r": fit["radius"], "ditch_w": _value(r, "ditch_width_max_m"),
             "bank_w": 5.5, "bank_gap": 1.0, "counter_w": 3.0}
    ne, south = {"az": 44, "w": _value(r, "entrance_ne_width_m")}, {"az": _value(r, "entrance_s_azimuth_deg"),
                                                                     "w": _value(r, "entrance_s_width_m")}
    ne2 = dict(ne, az=axis)
    aub = [{"kind": "aubrey", "id": f"AH{n}", "x": round(x, 2), "y": round(yy, 2),
            "d": _value(r, "aubrey_hole_size_m")["diameter"]} for n, x, yy in holes]
    yz = (_ring(sc, y["diameter_m"] / 2, y["count"], axis + 6, 1.4, "pit", "Y")
          + _ring(sc, z["diameter_m"] / 2, 30, axis + 6, 1.6, "pit", "Z", skip=(8,)))
    full = ["sarsen_upright", "sarsen_lintel", "trilithon_upright", "trilithon_lintel", "altar_stone",
            "station_stone", "slaughter_stone", "heel_stone", "heel_stone_companion"]
    return {
        "ditch_fit": fit, "aubrey_fit": hfit, "avenue": {"axis": axis, "ditch_gap": 21.5, "corridor": 12,
                                                         "from": fit["radius"] + 3},
        "stages": [
            {"id": "1", "name": "Stage 1: the enclosure", "dates": "c. 3000-2620 BC", "year": -2949,
             "what": "A circular ditch dug in segments, its chalk heaped into a bank inside (about 1.9 m high when new) "
                     "with a main entrance in the north-east and a smaller one in the south; the 56 Aubrey Holes "
                     "round the inside of the bank, holding bluestones or timber posts; cremation burials. Stone 97 "
                     "may have stood outside the entrance.",
             "earth": dict(earth, depth=1.8, bank_h=1.9, counter_h=0, chalk=1.0, entrances=[ne, south]),
             "groups": ["heel_stone_companion"], "extra": aub, "aubrey": True,
             "cites": _cites(r, "enclosure_overall_diameter_m", "inner_bank_height_m", "aubrey_count",
                             "aubrey_circle_radius_m", "aubrey_numbering", "entrance_s_azimuth_deg")},
            {"id": "2", "name": "Stage 2: the sarsens and a double bluestone arc", "dates": "c. 2620-2480 BC",
             "year": -2549,
             "what": "The five trilithons, the sarsen circle with its lintels, the Altar Stone, the Station Stones and "
                     "the Heel Stone; the bluestones, perhaps taken from the Aubrey Holes, set in pairs in the Q and R "
                     "holes, a double arc known only in the north-east half (whether it ran right round is "
                     "disputed; Cleal et al. put it before the sarsens). The entrance was widened onto the axis.",
             "earth": dict(earth, depth=1.2, bank_h=1.5, counter_h=0, chalk=0.35, entrances=[ne2, south]),
             "groups": full, "extra": qr_stones,
             "cites": _cites(r, "qr_diameters_m", "qr_extent", "station_stones")},
            {"id": "3", "name": "Stage 3: the Avenue", "dates": "c. 2480-2280 BC", "year": -2379,
             "what": "The Q and R arcs taken down; a small bluestone circle inside the horseshoe (perhaps the stones "
                     "of Bluestonehenge by the Avon; its size and number here are a guess); stones D and E removed "
                     "from the entrance; the ditch re-cut, its spoil perhaps the small outer bank; the Avenue's banks "
                     "and ditches built along the solstice axis towards the River Avon.",
             "earth": dict(earth, depth=1.4, bank_h=1.5, counter_h=0.5, chalk=0.5, entrances=[ne2, south]),
             "groups": full, "extra": central, "avenue": True,
             "cites": _cites(r, "avenue", "central_bluestone_circle", "enclosure")},
            {"id": "4", "name": "Stage 4: the bluestone circle and oval", "dates": "c. 2280-2020 BC", "year": -2149,
             "what": "The bluestones rearranged into a circle between the sarsen circle and the trilithons and an "
                     "oval inside the trilithons (later made a horseshoe): the arrangement the completed model shows.",
             "earth": dict(earth, depth=1.0, bank_h=1.3, counter_h=0.4, chalk=0.0, entrances=[ne2, south]),
             "groups": None, "extra": [], "avenue": True,
             "cites": _cites(r, "bluestone_circle_and_oval")},
            {"id": "5", "name": "Stage 5: the Y and Z holes", "dates": "c. 2020-1520 BC (Y and Z holes 1630-1520 BC)",
             "year": -1574,
             "what": "Two rings of pits dug round the sarsen circle, 30 Y holes and 30 Z holes (Z8 never found), and "
                     "left open; perhaps for bluestones never set in them. Axe and dagger carvings on the sarsens.",
             "earth": dict(earth, depth=0.8, bank_h=1.0, counter_h=0.3, chalk=0.0, entrances=[ne2, south]),
             "groups": None, "extra": yz, "avenue": True,
             "cites": _cites(r, "y_holes", "z_holes", "y_z_holes")},
        ],
        "debate": [{"claim": d["claim"], "cites": [{"quote": c["quote"], "title": r["sources"][c["source"]]["title"],
                                                     "url": r["sources"][c["source"]]["url"]}
                                                    for c in d.get("cites", []) if c["source"] in r["sources"]]}
                   for d in r.get("debate", [])],
    }
