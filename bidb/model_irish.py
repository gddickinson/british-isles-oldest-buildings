"""3D models of four Irish passage tombs (roadmap SH4a), from `data/curated/models/irish_tombs.json`: Loughcrew Cairn T
(the equinox sunrise on the backstone), Knowth (two passages, the west one bent, on Prendergast and Ray's measured
azimuths), Dowth (two tombs on the west side, the midwinter sunset into Dowth South) and Carrowkeel Cairn G (its
roof-box and the midsummer sunset). Mounds on their OpenStreetMap outlines, centred on the SMR points; each tomb by
bidb.model_tombs. The modules model_loughcrew_t, model_knowth, model_dowth and model_carrowkeel_g call these.
"""
from . import model_geometry as G
from .model_tombs import chamber_cam, outline, tomb
from .models3d import cite, research

COMMON = ["Passages are drawn running in from the kerb at their published azimuths (derived where marked in the "
          "research file); floors level unless a rise is published; chambers from their published sizes, recesses 1.4 m "
          "wide; kerbstones spaced evenly round the mapped outline at the published count."]


def _site(key):
    r = research("irish_tombs")
    s = r["sites"][key]
    f = s["facts"]
    cf = lambda *k: [c for x in k for c in cite(r, f[x]["cites"])]                       # noqa: E731
    ref = f["reference_point"]["value"]
    return r, s, f, cf, ref["lat"], ref["lon"]


def _spec(name, record, lat, lon, parts, cams, extra_facts, derived, about, events, face, start, axis, size=500, step=2, half=40, radius=40):
    return {"name": name, "record": record, "lat": lat, "lon": lon, "size": size, "step": step,
            "flatten": {"c": [0, 0], "r": radius, "edge": 12}, "shadow": {"half": half, "centre": [0, 0]},
            "views": {"now": parts}, "cams": cams, "events": events, "face": face, "start": start,
            "axis": axis, "axis_length": 150, "axis_label": "Passage axis", "lantern": True,
            "facts": extra_facts + [{"text": t, "cites": []} for t in derived + COMMON], "about": about,
            "labels_label": "Labels"}


def loughcrew():
    r, s, f, cf, lat, lon = _site("loughcrew_t")
    pts = outline(61742829, lat, lon)
    az = f["passage_azimuth_deg"]["value"]
    R = G.radius_at(pts, (0, 0), az)
    w, L = f["passage_width_m"]["value"], f["passage_length_m"]["value"]
    p = {"mouth": G.toward((0, 0), az, R), "legs": [(az, L)], "width": w, "roof": 1.4, "step": 1.0,
         "chamber": {"kind": "cruciform", "length": 3.6, "width": f["central_chamber_width_m"]["value"], "h": 1.6,
                     "top": f["central_chamber_height_m"]["value"], "recess": 1.2, "title": "The chamber",
                     "note": "Cruciform; on the equinox mornings the sun lights the decorated backstone C8.", "cites": cf("central_chamber_width_m", "central_chamber_height_m")},
         "title": "The passage", "note": f"About {L} m long and {w} m wide.", "cites": cf("passage_length_m", "passage_width_m", "passage_azimuth_deg")}
    parts, _ = tomb((0, 0), pts, f["cairn_height_m"]["value"], 1.2, [p], f["kerb_stones"]["value"], title="Cairn T",
                    note=f"About {f['cairn_diameter_m']['value']} m across and {f['cairn_height_m']['value']} m high.",
                    cites=cf("cairn_diameter_m", "cairn_height_m", "kerb_stones"), surface="cairn")
    cams = {"overview": {"label": "From the east", "from": [*G.toward((0, 0), az + 20, 55), 16], "to": [0, 0, 3]},
            "chamber": chamber_cam(parts[1], "In the chamber, facing the passage"),
            "above": {"label": "From above", "from": [0, -0.01, 90], "to": [0, 0, 0], "fov": 45}}
    facts = [{"text": a["claim"], "cites": cite(r, a.get("cites"))} for a in s["alignment"][:2]]
    return _spec("Loughcrew Cairn T", s["record"], lat, lon, parts, cams, facts,
                 ["The chamber is drawn 3.6 m deep with recesses 1.2 m deep, under a corbelled roof 3.05 m high (the "
                  "SMR's figure); the passage roof 1.4 m (not published)."],
                 [s.get("about", "")], ["equinox_rise", "summer_rise", "winter_rise"], {"equinox_rise": "chamber"},
                 {"event": "equinox_rise", "after": 45, "note": "An equinox morning, about 45 minutes after sunrise: the light comes down the passage onto the backstone. Try Play at 1 minute a second."},
                 [az], radius=20, half=22)


def knowth():
    r, s, f, cf, lat, lon = _site("knowth")
    pts = outline(264536965, lat, lon)
    e_az = f["east_passage_azimuth_deg"]["value"]
    wa = f["west_passage_azimuths_deg"]["value"]
    ec, wc = f["east_chamber"]["value"], f["west_chamber"]["value"]
    e_len = f["east_tomb_length_m"]["value"] - ec["n_s"]
    w_len = f["west_tomb_length_m"]["value"] - wc["length"]
    east = {"mouth": G.toward((0, 0), e_az, G.radius_at(pts, (0, 0), e_az)), "legs": [(e_az, e_len)], "width": 1.0, "roof": 1.6,
            "chamber": {"kind": "cruciform", "length": ec["n_s"], "width": ec["e_w"] - 2 * 1.6, "h": 2.0, "top": ec["apex_height"],
                        "recess": 1.6, "title": "The eastern tomb's chamber", "note": "Cruciform, with a corbelled vault 6.1 m high.", "cites": cf("east_chamber")},
            "title": "The eastern passage", "note": f"{f['east_tomb_length_m']['value']} m from the kerb to the back of the chamber; azimuth {e_az}°.",
            "cites": cf("east_tomb_length_m", "east_passage_azimuth_deg")}
    west = {"mouth": G.toward((0, 0), wa["outer_outwards"], G.radius_at(pts, (0, 0), wa["outer_outwards"])),
            "legs": [(wa["outer_outwards"], 26.7), (wa["inner_outwards"], max(1.0, w_len - 26.7))], "width": 0.9, "roof": 1.5,
            "rise": f["west_passage_floor_rise_m"]["value"],
            "chamber": {"kind": "rect", "length": wc["length"], "width": wc["width"], "h": wc["height"],
                        "title": "The western tomb's chamber", "note": "Undifferentiated, little wider than the passage.", "cites": cf("west_chamber")},
            "title": "The western passage", "note": "Bends by 19°40′ 26.7 m in from the kerb (Prendergast and Ray).",
            "cites": cf("west_tomb_length_m", "west_passage_azimuths_deg", "west_passage_floor_rise_m")}
    md = f["mound_dimensions_m"]["value"]
    parts, _ = tomb((0, 0), pts, md["height"], 1.3, [east, west], f["kerb_stones"]["value"], title="The great mound",
                    note=f"About {md['n_s']} m by {md['e_w']} m and {md['height']} m high.", cites=cf("mound_dimensions_m", "kerb_stones"))
    cams = {"overview": {"label": "From the south-east", "from": [80, -90, 35], "to": [0, 0, 4]},
            "east": chamber_cam(parts[1], "In the eastern chamber, facing the passage"),
            "west": chamber_cam(parts[3], "In the western chamber, facing the passage"),
            "above": {"label": "From above", "from": [0, -0.01, 170], "to": [0, 0, 0], "fov": 45}}
    facts = [{"text": a["claim"], "cites": cite(r, a.get("cites"))} for a in s["alignment"][:3]]
    return _spec("Knowth", s["record"], lat, lon, parts, cams, facts,
                 ["The passages' roofs (1.5-1.6 m) and widths (0.9-1 m) are not published per passage; the western "
                  "passage's floor rises evenly by its published 0.72 m."],
                 [s.get("about", "")], ["equinox_rise", "equinox_set", "summer_rise", "winter_set"], {"equinox_rise": "east", "equinox_set": "west"},
                 {"event": "equinox_set", "after": -10, "note": "An equinox evening. Prendergast and Ray found neither passage aligned on the equinox: the outer western passage takes the setting sun about 4 March and 9 October."},
                 [e_az, wa["outer_outwards"]], radius=48, half=55)


def dowth():
    r, s, f, cf, lat, lon = _site("dowth")
    pts = outline(264536947, lat, lon)
    n_az = f["north_passage_azimuth_deg"]["value"]
    s_az = 225.0
    n_m, s_m = 255.0, 221.0                       # mouths 34° apart on the kerb: 25 m apart (derived)
    nc, sc = f["north_chamber"]["value"], f["south_chamber"]["value"]
    north = {"mouth": G.toward((0, 0), n_m, G.radius_at(pts, (0, 0), n_m)), "legs": [(n_az, f["north_passage_length_m"]["value"])],
             "width": 0.9, "roof": 1.6,
             "chamber": {"kind": "cruciform", "length": 4.5, "width": 2.4, "h": 2.4, "top": nc["roof_height"], "recess": 1.4,
                         "title": "Dowth North: the chamber", "note": "Cruciform.", "cites": cf("north_chamber")},
             "title": "Dowth North: the passage", "cites": cf("north_passage_length_m", "north_passage_azimuth_deg")}
    south = {"mouth": G.toward((0, 0), s_m, G.radius_at(pts, (0, 0), s_m)), "legs": [(s_az, f["south_passage_length_m"]["value"])],
             "width": 0.9, "roof": 1.5,
             "chamber": {"kind": "round", "length": sc["diameter"], "h": 2.0, "top": 3.0,
                         "title": "Dowth South: the chamber", "note": f"Round, about {sc['diameter']} m across, {sc['orthostats']} orthostats; a recess to the right.",
                         "cites": cf("south_chamber", "south_recess")},
             "title": "Dowth South: the passage", "cites": cf("south_passage_length_m")}
    parts, _ = tomb((0, 0), pts, f["mound_height_m"]["value"], 1.4, [north, south], f["kerb_stones"]["value"], title="The mound",
                    note=f"About {f['mound_diameter_m']['value']} m across and {f['mound_height_m']['value']} m high.",
                    cites=cf("mound_diameter_m", "mound_height_m", "kerb_stones"))
    cams = {"overview": {"label": "From the west", "from": [-85, -40, 35], "to": [0, 0, 5]},
            "south": chamber_cam(parts[3], "In Dowth South, facing the passage"),
            "north": chamber_cam(parts[1], "In Dowth North, facing the passage"),
            "above": {"label": "From above", "from": [0, -0.01, 160], "to": [0, 0, 0], "fov": 45}}
    facts = [{"text": a["claim"], "cites": cite(r, a.get("cites"))} for a in s["alignment"][:2]]
    return _spec("Dowth", s["record"], lat, lon, parts, cams, facts,
                 ["Dowth South's azimuth is not published in a reachable source: drawn at 225° (south-west); the two "
                  "passage mouths are set 25 m apart on the western kerb. Dowth North's passage is drawn at the OPW's "
                  "8.2 m (Wikipedia gives up to 18.2 m) and its chamber 4.5 by 2.4 m with recesses."],
                 [s.get("about", "")], ["winter_set", "summer_rise", "equinox_set"], {"winter_set": "south"},
                 {"event": "winter_set", "after": -60, "note": "Midwinter afternoon, about an hour before sunset: the sun's light enters Dowth South. Press Play at 1 minute a second."},
                 [s_az, n_az], radius=44, half=50)


def carrowkeel():
    r, s, f, cf, lat, lon = _site("carrowkeel_g")
    pts = outline(541508806, lat, lon)
    az = f["entrance_azimuth_deg"]["value"]
    ch = f["chamber"]["value"]
    L = f["tomb_length_m"]["value"] - ch["length"]
    p = {"mouth": G.toward((0, 0), az, G.radius_at(pts, (0, 0), az)), "legs": [(az, L)], "width": 0.8, "roof": 1.0,
         "chamber": {"kind": "cruciform", "length": ch["length"] + 1.0, "width": ch["width"], "h": 1.4, "top": ch["height"],
                     "recess": 0.9, "title": "The chamber and its three cells", "note": "Cruciform: a chamber with cells left, right and at the end.",
                     "cites": cf("chamber", "cells_m")},
         "title": "The entrance and roof-box", "note": "A roof-box over the entrance lets the setting sun in around midsummer.",
         "cites": cf("tomb_length_m", "entrance_azimuth_deg")}
    parts, _ = tomb((0, 0), pts, f["cairn_height_m"]["value"], 1.6, [p], 30, rock="sandstone", title="Cairn G",
                    note=f"About {f['cairn_diameter_m']['value']} m across and {f['cairn_height_m']['value']} m high.",
                    cites=cf("cairn_diameter_m", "cairn_height_m"), surface="cairn")
    cams = {"overview": {"label": "From the north-west", "from": [*G.toward((0, 0), az + 15, 35), 10], "to": [0, 0, 1.5]},
            "chamber": chamber_cam(parts[1], "In the chamber, facing the entrance", eye=1.1),
            "above": {"label": "From above", "from": [0, -0.01, 60], "to": [0, 0, 0], "fov": 45}}
    facts = [{"text": a["claim"], "cites": cite(r, a.get("cites"))} for a in s["alignment"][:2]]
    return _spec("Carrowkeel Cairn G", s["record"], lat, lon, parts, cams, facts,
                 ["The entrance is drawn at 308° from Macalister's 1911 compass bearing of 328° with an assumed magnetic "
                  "variation of 20° W. The roof-box is not drawn: its size is not published, so the light here comes "
                  "through the entrance alone. The kerb is drawn as 30 slabs; its count is not published."],
                 [s.get("about", "")], ["summer_set", "winter_rise", "equinox_set"], {"summer_set": "chamber"},
                 {"event": "summer_set", "after": -25, "note": "A midsummer evening before sunset: the sun shines in through the roof-box."},
                 [az], size=300, radius=11, half=14)
