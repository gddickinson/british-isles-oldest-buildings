"""Shared by the passage-tomb models (roadmap SH4a: Loughcrew Cairn T, Knowth, Dowth, Carrowkeel Cairn G, La Hougue
Bie): a mound or cairn on its OpenStreetMap outline, a kerb of slabs round it, and passages running in from the kerb
(straight, or bent where measured) to chambers that are cruciform, round or rectangular, corbelled or capstoned; the
ground levelled under the mound; cameras in each chamber facing out down its passage.
"""
import math

from . import model_geometry as G


def outline(way, lat0, lon0):
    """An OSM way's outline in metres round (lat0, lon0)."""
    res = G.request_json(G.OVERPASS, data={"data": f"[out:json];way({way});out geom;"}, method="POST", min_interval=2)
    pts = [G.local(p["lat"], p["lon"], lat0, lon0) for p in res["elements"][0]["geometry"]]
    return pts[:-1] if pts[0] == pts[-1] else pts


def chamber_outline(kind, start, az_in, length, width, recess=None):
    """Chamber outline from the passage's inner end `start`, running in at az_in: "rect", "round" or "cruciform"
    (three recesses of `recess` m deep, 1.4 m wide unless given as [depth, width])."""
    to = lambda a, b: [round(v, 2) for v in G.toward(G.toward(start, az_in, a), az_in + 90, b)]   # noqa: E731
    if kind == "round":
        c = G.toward(start, az_in, length / 2)
        return [list(p) for p in G.polygon(c, length / 2 / math.cos(math.pi / 10), 10, start=az_in + 180 + 18)]
    hw = width / 2
    if kind == "rect":
        return [to(0, -hw), to(length, -hw), to(length, hw), to(0, hw)]
    d, rw = (recess if isinstance(recess, (list, tuple)) else (recess or length * 0.3, 1.4))
    core = length - d
    a1, a2 = max(0.2, core / 2 - rw / 2), core / 2 + rw / 2
    ab = [(0, -hw), (a1, -hw), (a1, -hw - d), (a2, -hw - d), (a2, -hw), (core, -hw), (core, -rw / 2), (length, -rw / 2),
          (length, rw / 2), (core, rw / 2), (core, hw), (a2, hw), (a2, hw + d), (a1, hw + d), (a1, hw), (0, hw)]
    return [to(a, b) for a, b in ab]


def tomb(c, pts, height, kerb_h, passages, kerb_count, rock="greywacke", title="The mound", note="", cites=None,
         surface="grass", roofed=True, facade=None):
    """Parts of a passage tomb. passages: [{mouth (point on the kerb), legs: [(azimuth outward, length), ...] from
    the mouth inward, width, roof, rise, chamber: {kind, length, width, h, top, recess}, title, note, cites}]."""
    radii = G.radii(pts, c, 2)
    parts = []
    gaps = []
    for p in passages:
        path, d, fl = [list(p["mouth"])], 0.0, [0.0]
        total = sum(L for _, L in p["legs"])
        for az, L in p["legs"]:
            nxt = G.toward(path[-1], (az + 180) % 360, L)
            d += L
            path.append([round(v, 2) for v in nxt])
            fl.append(p.get("rise", 0) * d / total)
        az_in = (p["legs"][-1][0] + 180) % 360
        ch = p["chamber"]
        out = chamber_outline(ch["kind"], path[-1], az_in, ch["length"], ch.get("width", ch["length"]), ch.get("recess"))
        roof = ({"kind": "corbel", "top": ch["top"], "rings": 8} if ch.get("top") else {"kind": "capstone", "thickness": 0.5}) \
            if roofed else {"kind": "none"}
        info = {"title": p.get("title", "Passage"), "note": p.get("note", ""), "cites": p.get("cites", [])}
        parts.append({"kind": "passage", "path": path, "floor": fl, "width": p["width"], "roof": p["roof"], "rock": rock,
                      "step": p.get("step", 1.2), "roof_gap": p.get("roof_gap"), "roof_rough": p.get("roof_rough", 0.6), **info})
        parts.append({"kind": "chamber", "outline": out, "floor": p.get("rise", 0), "h": ch["h"], "rock": rock, "step": 1.1,
                      "roof": roof, "open": [{"at": path[-1], "width": p["width"]}],
                      "title": ch.get("title", "Chamber"), "note": ch.get("note", ""), "cites": ch.get("cites", info["cites"])})
        gaps.append({"az": G.bearing(c, p["mouth"]), "width": p["width"] + 0.4, "open": p.get("open", [[0, p["roof"] if not isinstance(p["roof"], list) else p["roof"][0]]])})
    mound = {"kind": "mound", "c": list(c), "radii": radii, "h": height, "kerb_h": kerb_h, "p": 0.75, "surface": surface,
             "kerb_rock": "cairn", "gaps": gaps, "title": title, "note": note, "cites": cites or []}
    if facade:
        mound["facade"] = facade
    parts.insert(0, mound)
    for x, y, az in G.along(pts, kerb_count, inset=-0.3):
        parts.append({"kind": "stone", "c": [x, y], "len": max(1.0, 0.9 * 2 * math.pi * (sum(radii) / len(radii)) / kerb_count),
                      "wid": 0.45, "az": az, "h": max(0.8, kerb_h * 0.9), "rock": rock, "title": "Kerbstone",
                      "note": f"One of the {kerb_count} kerbstones.", "cites": cites or []})
    return parts, gaps


def chamber_cam(passage, label, eye=1.5, fov=60):
    """A standing camera at the back of a passage's chamber, facing out along the passage."""
    path = passage["path"]
    az_out = G.bearing(path[-1], path[-2])
    back = G.toward(path[-1], (az_out + 180) % 360, 1.0)
    return {"label": label, "from": [*back, passage["floor"][-1] + eye], "to": [*G.toward(path[-1], az_out, 40), passage["floor"][-1] + 1.0],
            "fov": fov, "standing": True}
