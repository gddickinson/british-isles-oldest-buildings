"""The stones of Stonehenge in the model's frame (bidb.stonehenge): metres from the centre of the stone plan, x east,
y north (true north), from the digitised plan (`data/curated/stonehenge/plan_stones.json`), OpenStreetMap for the
outliers (Heel, Slaughter and Station Stones, markers) and the researched record (`stones.json`).

    register(plan, osm)   the plan placed on the ground: rotation and shift onto the OSM stones (least squares)
    now(...)              the stones as they are: outline, state, height; lintels in place on their uprights
    built(...)            as thought complete (c. 2500 BC; bluestones as rearranged c. 2400-2200 BC): every circle
                          upright and lintel, the five trilithons (55 and 59 mirrored from 56 and 52 across the axis),
                          the bluestone circle and horseshoe filled at the spacing of the survivors; each piece says
                          whether it is `surviving`, `placed` (a known stone set up) or `restored` (a lost stone drawn)
"""
import math

AXIS = 49.57                     # azimuth of the axis (Lockyer and Penrose's survey, stones.json layout)
FALLEN_T = {"sarsen": 1.0, "bluestone": 0.6, "sandstone": 0.5}
LOW = {"stump": 0.3, "buried": 0.06, "fragment": 0.7}


def local(lat, lon, lat0, lon0):
    return ((lon - lon0) * 111320 * math.cos(math.radians(lat0)), (lat - lat0) * 110574)


def centroid(pts):
    return (sum(p[0] for p in pts) / len(pts), sum(p[1] for p in pts) / len(pts))


def rotate(p, theta, about=(0, 0)):
    c, s = math.cos(theta), math.sin(theta)
    x, y = p[0] - about[0], p[1] - about[1]
    return (about[0] + c * x - s * y, about[1] + s * x + c * y)


def register(plan, osm, lat0, lon0, iterations=12, within=2.5, turn=True):
    """Rotation (radians) and shift (m) taking plan metres onto OSM metres round lat0/lon0, matching each plan stone
    to the nearest OSM stone (iterated closest points from the offset of the two circles' centres, 2-D Procrustes);
    the residual of the matched pairs. turn=False fits the shift alone (the plan's north kept)."""
    P = [centroid(s["outline"]) for s in plan]
    Q = [centroid([local(a, b, lat0, lon0) for a, b in o["outline"]]) for o in osm if o["kind"] == "stone"]
    near = lambda pts: [p for p in pts if math.hypot(*p) < 22] or pts   # noqa: E731  the circle, not the outliers
    cp0, cq0 = centroid(near(P)), centroid(near(Q))
    theta, t = 0.0, (cq0[0] - cp0[0], cq0[1] - cp0[1])                 # start from the centres' offset
    for _ in range(iterations):
        pairs = []
        for p in P:
            q0 = rotate(p, theta)
            q0 = (q0[0] + t[0], q0[1] + t[1])
            q = min(Q, key=lambda q: (q[0] - q0[0]) ** 2 + (q[1] - q0[1]) ** 2)
            if math.dist(q, q0) < within:
                pairs.append((p, q))
        cp, cq = centroid([a for a, _ in pairs]), centroid([b for _, b in pairs])
        sxx = sum((a[0] - cp[0]) * (b[0] - cq[0]) + (a[1] - cp[1]) * (b[1] - cq[1]) for a, b in pairs)
        sxy = sum((a[0] - cp[0]) * (b[1] - cq[1]) - (a[1] - cp[1]) * (b[0] - cq[0]) for a, b in pairs)
        theta = math.atan2(sxy, sxx) if turn else 0.0
        rp = rotate(cp, theta)
        t = (cq[0] - rp[0], cq[1] - rp[1])
    res = [math.dist((rotate(a, theta)[0] + t[0], rotate(a, theta)[1] + t[1]), b) for a, b in pairs]
    return {"theta": theta, "shift": t, "pairs": len(pairs), "rms": math.sqrt(sum(r * r for r in res) / len(res))}


def fit_circle(points):
    """Least-squares circle (Kåsa) → (cx, cy, r)."""
    n = len(points)
    mx, my = centroid(points)
    u = [(x - mx, y - my) for x, y in points]
    suu = sum(a * a for a, _ in u); svv = sum(b * b for _, b in u); suv = sum(a * b for a, b in u)
    suuu = sum(a ** 3 for a, _ in u); svvv = sum(b ** 3 for _, b in u)
    suvv = sum(a * b * b for a, b in u); svuu = sum(b * a * a for a, b in u)
    det = suu * svv - suv * suv
    uc = (svv * (suuu + suvv) - suv * (svvv + svuu)) / (2 * det)
    vc = (suu * (svvv + svuu) - suv * (suuu + suvv)) / (2 * det)
    return mx + uc, my + vc, math.sqrt(uc * uc + vc * vc + (suu + svv) / n)


def azimuth(p, c=(0, 0)):
    return math.degrees(math.atan2(p[0] - c[0], p[1] - c[1])) % 360


def at(c, r, az):
    return (c[0] + r * math.sin(math.radians(az)), c[1] + r * math.cos(math.radians(az)))


def box(centre, along, width, depth):
    """Rectangle outline: `width` along the azimuth `along`, `depth` across it."""
    a, b = math.radians(along), math.radians(along + 90)
    ux, uy, vx, vy = math.sin(a), math.cos(a), math.sin(b), math.cos(b)
    return [(round(centre[0] + sx * width / 2 * ux + sy * depth / 2 * vx, 2),
             round(centre[1] + sx * width / 2 * uy + sy * depth / 2 * vy, 2))
            for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1))]


def mirror(p, c, axis=AXIS):
    """Reflection across the axis line through c."""
    a = math.radians(axis)
    ux, uy = math.sin(a), math.cos(a)
    x, y = p[0] - c[0], p[1] - c[1]
    d = x * ux + y * uy
    return (c[0] + 2 * d * ux - x, c[1] + 2 * d * uy - y)


def _kind(group):
    return "bluestone" if group.startswith("bluestone") else "sandstone" if group == "altar_stone" else "sarsen"


def _num(sid):
    digits = "".join(ch for ch in sid if ch.isdigit())
    return int(digits) if digits else 0


def now(plan, record, outliers):
    """The stones today. `plan`: id → outline (model metres); `record`: id → researched stone; `outliers`: id →
    outline or point (OSM). Lintels in place sit on their uprights, at the mean of their heights."""
    out = []
    for sid, rec in record.items():
        st = rec["state_now"]
        if st == "missing" or rec["group"].endswith("lintel") and st == "standing":
            continue
        outline = plan.get(sid) or outliers.get(sid)
        if outline is None:
            continue
        kind = _kind(rec["group"])
        if st in ("standing", "leaning"):
            h = rec.get("height_above_ground_m") or (2.0 if kind == "bluestone" else 4.1)
        else:
            h = LOW.get(st, FALLEN_T[kind])
        out.append({"id": sid, "group": rec["group"], "kind": kind, "state": st, "outline": outline, "h": h})
    tops = {s["id"]: s for s in out}
    for sid, rec in record.items():
        if rec["group"].endswith("lintel") and rec["state_now"] == "standing" and rec.get("rests_on"):
            a, b = (tops.get(x) for x in rec["rests_on"])
            if not a or not b:
                continue
            ca, cb = centroid(a["outline"]), centroid(b["outline"])
            trilithon = rec["group"].startswith("trilithon")
            length = math.dist(ca, cb) + (2.2 if trilithon else 1.0)
            base = (a["h"] + b["h"]) / 2
            a["h"] = b["h"] = base
            out.append({"id": sid, "group": rec["group"], "kind": "sarsen", "state": "in place", "h": 0.8 if not trilithon else 1.0,
                        "base": base, "outline": box(centroid([ca, cb]), azimuth(cb, ca), length, 1.0 if not trilithon else 1.1)})
    return out


def built(plan, record, outliers, dims):
    """The monument as thought complete; see the module note."""
    rec = record
    up = {k: plan[k] for k in plan if k.isdigit() and 1 <= int(k) <= 30 and rec.get(k, {}).get("state_now") == "standing"}
    cx, cy, r = fit_circle([centroid(o) for o in up.values()])
    c = (cx, cy)
    # Angle of each circle upright: a straight line through the standing ones' angles by number.
    pairs = [(int(k), (azimuth(centroid(o), c) - AXIS) % 360) for k, o in up.items()]
    n = len(pairs)
    mk = sum(k for k, _ in pairs) / n
    ma = sum(a for _, a in pairs) / n
    step = sum((k - mk) * (a - ma) for k, a in pairs) / sum((k - mk) ** 2 for k, _ in pairs)
    angle = lambda k: AXIS + ma + step * (k - mk)                              # noqa: E731
    ring_h = dims["sarsen_lintel_top_height_m"]["value"] - dims["sarsen_lintel_thickness_m"]["value"]
    width, depth = dims["sarsen_upright_width_m"]["value"], dims["sarsen_upright_thickness_m"]["value"]
    out = []
    for k in range(1, 31):
        sid = str(k)
        if sid in up:
            out.append({"id": sid, "group": "sarsen_upright", "kind": "sarsen", "status": "surviving",
                        "outline": up[sid], "h": ring_h})
        else:
            st = rec.get(sid, {}).get("state_now", "missing")
            out.append({"id": sid, "group": "sarsen_upright", "kind": "sarsen",
                        "status": "restored" if st == "missing" else "placed",
                        "outline": box(at(c, r, angle(k)), angle(k) + 90, width, depth), "h": ring_h})
    for k in range(1, 31):                       # lintel 1nn on uprights nn-1 and nn (101 on 30 and 1)
        a0, a1 = angle(k - 1 if k > 1 else 30) % 360, angle(k) % 360
        mid = (a0 + ((a1 - a0) % 360) / 2) % 360
        sid = str(100 + k)
        st = rec.get(sid, {}).get("state_now", "missing")
        out.append({"id": sid, "group": "sarsen_lintel", "kind": "sarsen",
                    "status": {"standing": "surviving", "missing": "restored"}.get(st, "placed"),
                    "arc": {"cx": round(cx, 2), "cy": round(cy, 2), "r": round(r, 2), "az": round(mid, 2),
                            "span": round(math.degrees(dims["sarsen_lintel_length_m"]["value"] / r), 2),
                            "depth": dims["sarsen_lintel_width_m"]["value"]},
                    "base": ring_h, "h": dims["sarsen_lintel_thickness_m"]["value"]})
    tri = {"51": "60", "52": "59", "53": "58", "54": "57", "56": "55"}
    tops = {"51": 5.0, "52": 5.0, "53": 5.2, "54": 5.2, "55": 6.5, "56": 6.5, "57": 5.2, "58": 5.2, "59": 5.0, "60": 5.0}
    shapes = {}
    for a, b in tri.items():
        for x, y in ((a, b), (b, a)):
            if x in plan and rec[x]["state_now"] == "standing":
                shapes[x] = (plan[x], "surviving")
            elif y in plan and rec[y]["state_now"] == "standing":
                shapes[x] = ([tuple(round(v, 2) for v in mirror(p, c)) for p in plan[y]][::-1], "placed")
    for sid, (outline, status) in sorted(shapes.items()):
        out.append({"id": sid, "group": "trilithon_upright", "kind": "sarsen", "status": status, "outline": outline,
                    "h": tops[sid]})
    for lid, (a, b) in (("152", ("51", "52")), ("154", ("53", "54")), ("156", ("55", "56")), ("158", ("57", "58")),
                        ("160", ("59", "60"))):
        ca, cb = centroid(shapes[a][0]), centroid(shapes[b][0])
        st = rec.get(lid, {}).get("state_now")
        out.append({"id": lid, "group": "trilithon_lintel", "kind": "sarsen",
                    "status": "surviving" if st == "standing" else "placed", "base": tops[a], "h": 0.8 if lid == "156" else 1.0,
                    "outline": box(centroid([ca, cb]), azimuth(cb, ca), math.dist(ca, cb) + 2.2, 1.1)})
    out += _bluestones(plan, rec, c)
    out += _outer(rec, outliers, c, dims)
    return out, {"centre": [round(cx, 2), round(cy, 2)], "radius": round(r, 2), "step": round(step, 3)}


def _bluestones(plan, rec, c):
    """Bluestone circle and horseshoe: survivors set up where they lie, gaps filled at the survivors' spacing."""
    out = []
    for group, h0 in (("bluestone_circle", 1.9), ("bluestone_horseshoe", 2.1)):
        have = {k: centroid(plan[k]) for k, v in rec.items() if v["group"] == group and k in plan}
        if group == "bluestone_horseshoe":
            for k, p in list(have.items()):              # the horseshoe is symmetric about the axis
                q = mirror(p, c)
                if all(math.dist(q, o) > 1.0 for o in have.values()):
                    have["m" + k] = q
        pts = list(have.values())
        if group == "bluestone_circle":
            cx, cy, r = fit_circle(pts)
            angles = sorted(azimuth(p, (cx, cy)) for p in pts)
            gaps = sorted((angles[(i + 1) % len(angles)] - angles[i]) % 360 for i in range(len(angles)))
            spacing = gaps[len(gaps) // 4] if gaps else 6                 # the closer-set survivors
            for a in [i * spacing for i in range(int(360 // spacing))]:
                q = at((cx, cy), r, a + angles[0])
                if all(math.dist(q, o) > 0.6 * r * math.radians(spacing) for o in pts):
                    have["r%d" % round(a)] = q
        for k, p in have.items():
            real = k in plan and not k.startswith(("m", "r"))
            st = rec.get(k, {}).get("state_now")
            h = rec.get(k, {}).get("height_above_ground_m") or h0
            if group == "bluestone_horseshoe":           # graded, tallest at the closed south-west end
                off = abs(((azimuth(p, c) - AXIS - 180) + 180) % 360 - 180)   # degrees from the south-west end
                h = rec.get(k, {}).get("height_above_ground_m") or round(2.5 - 0.7 * min(off, 90) / 90, 2)
            out.append({"id": k if real else "", "group": group, "kind": "bluestone",
                        "status": "surviving" if real and st == "standing" else "placed" if real else "restored",
                        "outline": plan[k] if real and st == "standing" else box(p, azimuth(p, c) + 90, 0.9, 0.55),
                        "h": round(h, 2)})
    return out


def _outer(rec, outliers, c, dims):
    """Altar Stone (standing on the axis inside the horseshoe: one view of its first position), Slaughter and Heel
    Stones upright, the Heel Stone's lost companion (stone hole 97), the four Station Stones."""
    heel = dims["heel_stone"]["value"]
    out = [{"id": "80", "group": "altar_stone", "kind": "sandstone", "status": "placed",
            "outline": box(at(c, 4.0, AXIS + 180), AXIS + 90, 1.0, 0.5), "h": 4.0}]
    for sid, h, size in (("95", 4.9, (2.1, 0.8)), ("96", heel["height_above_ground_m"], (2.4, 2.0)),
                         ("97", heel["height_above_ground_m"], (2.0, 1.6)), ("91", 2.7, (1.1, 0.8)),
                         ("92", 1.5, (1.1, 0.8)), ("93", dims["station_stone_93_height_m"]["value"], (1.1, 0.8)),
                         ("94", 1.5, (1.1, 0.8))):
        p = outliers.get(sid)
        if not p:
            continue
        st = rec.get(sid, {}).get("state_now")
        out.append({"id": sid, "group": rec.get(sid, {}).get("group", "outer"), "kind": "sarsen",
                    "status": "surviving" if st == "standing" else "restored" if st == "missing" else "placed",
                    "outline": p if len(p) > 2 and (st == "standing" or sid == "96") else
                    box(centroid(p), azimuth(centroid(p), c) + 90, *size),      # the Heel Stone keeps its own shape
                    "h": h})
    return out
