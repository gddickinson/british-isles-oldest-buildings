"""One-off: the stones of Stonehenge as they survive, digitised from Anthony Johnson's plan (2007, "a computer
compilation of data from various surveys", Wikimedia Commons File:Stone_Plan.jpg, CC BY 3.0) in its coloured
version (File:Stone_Plan_Coloured.jpg, Nightdevil 2018, CC BY-SA 4.0) → plan_stones.json beside this file.

    python3 data/curated/stonehenge/prepare_plan.py PLAN.jpg [OVERLAY.png]

Needs Pillow, numpy and scipy (the system Python; the app's .venv does not need them). Each colour of the plan is a
class (sarsen, fallen sarsen, bluestone, fallen bluestone, sandstone); the hatching is closed, each patch traced
round (convex hull) and named by the stone of `STONES` whose centre (read off the plan by eye at 1876 px wide) lies
in it; touching stones drawn as one patch are split between their centres (`shared`). The overlay shows each stone
with its name to check. Metres from the plan's centre
cross, x east, y north (the plan has north up). Lintels in place are drawn on the plan as outlines only: the model
puts them on their uprights.
"""
import json
import re
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage
from scipy.spatial import ConvexHull

PX_PER_M = 95.8                 # scale bar: 0 at x 2498, 10 m at x 3456
CENTRE = (2120, 2125)           # the plan's centre cross
SHOWN = 4016 / 1876             # the centres below were read at 1876 px wide

# Stone number: centre on the plan at 1876 px wide (x right, y down).
STONES = {
    "1": (1555, 600), "2": (1625, 720), "3": (1665, 860), "4": (1675, 1000), "5": (1665, 1140), "6": (1605, 1280),
    "7": (1535, 1400), "8": (1515, 1590), "9a": (1340, 1630), "9b": (1390, 1700), "10": (1180, 1630),
    "11": (1055, 1680), "12": (905, 1730), "14": (690, 1480), "15": (620, 1360), "16": (410, 1380), "19": (175, 960),
    "120": (195, 880), "21": (365, 700), "22": (440, 575), "23": (545, 480), "25": (700, 310), "26": (915, 305),
    "127": (990, 280), "27": (1070, 318), "28": (1210, 335), "29": (1345, 400), "30": (1460, 485),
    "51": (1370, 1090), "52": (1290, 1175), "53": (1075, 1305), "54": (970, 1365), "55a": (735, 1260),
    "55b": (850, 1130), "56": (665, 1180), "57": (620, 940), "58": (685, 835), "59a": (885, 720), "59b": (965, 808),
    "59c": (995, 860), "60": (940, 600), "156": (825, 1025), "160a": (1030, 755), "160b": (1100, 820),
    "160c": (1160, 910), "80": (930, 1110),
    "31": (1425, 695), "32": (1488, 915), "150": (1500, 865), "32c": (1525, 1090), "32d": (1520, 1138),
    "32e": (1505, 1175), "33": (1488, 1225), "33e": (1338, 1422), "33f": (1288, 1435), "34": (1230, 1465),
    "35a": (1183, 1487), "35b": (1252, 1620), "36": (912, 1545), "37": (857, 1468), "38": (765, 1425),
    "39": (738, 1380), "40": (685, 1378), "40c": (542, 1283), "40g": (455, 1140), "41": (413, 1080), "41d": (483, 852),
    "42": (568, 700), "42c": (640, 612), "43": (688, 560), "44": (762, 676), "45": (815, 457), "46": (1168, 484),
    "47": (1237, 508), "48": (1275, 575), "49": (1348, 604), "61": (1330, 1023), "61a": (1237, 1098),
    "62": (1189, 1170), "63": (1128, 1215), "64": (984, 1255), "65": (911, 1237),
    "67": (762, 1085), "68": (730, 1087), "69": (711, 948), "70": (748, 883), "70a": (780, 812), "70b": (829, 771),
    "72": (945, 660),
}


def classes(im):
    r, g, b = (im[..., i].astype(int) for i in range(3))
    return {
        "sarsen": (r > 200) & (g < 70) & (b < 60),
        "sarsen_fallen": (r > 170) & (g > 80) & (g < 170) & (b > 60) & (b < 160) & (r - g > 50),
        "bluestone": (r < 60) & (g > 90) & (g < 160) & (b > 200),
        "bluestone_fallen": (r > 50) & (r < 150) & (g > 150) & (b > 210),
        "sandstone": (abs(r - g) < 14) & (abs(g - b) < 14) & (r > 140) & (r < 215),
    }


def split(patch, dark, seeds, xs, ys):
    """Which seed owns each pixel of a patch: a watershed from the stone centres that stops at the plan's outlines
    (touching stones are drawn with a line between them); nearest centre where the outline is broken."""
    if len(seeds) == 1:
        return np.zeros(len(xs), int)
    y0, y1, x0, x1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
    sub = patch[y0:y1, x0:x1]
    cost = np.where(dark[y0:y1, x0:x1], 255, 1).astype(np.uint8)
    markers = np.where(sub, 0, -1).astype(np.int16)
    for j, (_, x, y) in enumerate(seeds):
        markers[max(y - 6 - y0, 0):y + 7 - y0, max(x - 6 - x0, 0):x + 7 - x0] = j + 1
    markers[~sub] = -1
    got = ndimage.watershed_ift(cost, markers)[ys - y0, xs - x0] - 1
    near = np.stack([(xs - x) ** 2 + (ys - y) ** 2 for _, x, y in seeds]).argmin(0)
    return np.where(got >= 0, got, near)


def family_of(k):
    """Sarsens: the circle 1-30, its lintels 101-130, the trilithons 51-60 and their lintels; bluestones 31-49,
    61-72 and the bluestone lintel 150."""
    n = int(re.match(r"\d+", k).group())
    return "bluestone" if 31 <= n <= 49 or 61 <= n <= 72 or n == 150 else "sarsen"


def stone(k, kind, px, py, shared):
    pts = np.column_stack([px, py]).astype(float)
    hull = pts[ConvexHull(pts).vertices]
    return {"id": k, "kind": kind, "area_m2": round(len(px) / PX_PER_M ** 2, 2), "shared": shared,
            "outline": [to_metres(x, y) for x, y in hull], "_px": hull.tolist()}


def to_metres(x, y):
    return round((x - CENTRE[0]) / PX_PER_M, 2), round(-(y - CENTRE[1]) / PX_PER_M, 2)


def run(path, overlay=None):
    im = np.asarray(Image.open(path).convert("RGB"))
    centres = {k: (x * SHOWN, y * SHOWN) for k, (x, y) in STONES.items()}
    kinds = classes(im)
    stones = {}
    x80, y80 = centres.pop("80")                        # the Altar Stone, partly under 55b and 156: its grey pixels
    yy, xx = np.ogrid[:im.shape[0], :im.shape[1]]       # (grey elsewhere is anti-aliased text and lines)
    grey = kinds.pop("sandstone") & ((xx - x80) ** 2 + (yy - y80) ** 2 < (3 * PX_PER_M) ** 2)
    grey = ndimage.binary_opening(grey, np.ones((3, 3)))
    stones["80"] = stone("80", "sandstone", *np.nonzero(grey)[::-1], shared=True)
    dark = ndimage.binary_dilation(im.max(2) < 110)     # the outline drawn round each stone
    for family, members in (("sarsen", ("sarsen", "sarsen_fallen")),
                            ("bluestone", ("bluestone", "bluestone_fallen"))):
        kind_of = np.zeros(im.shape[:2], np.int8)       # 0 none, 1 standing, 2 fallen
        for i, k in enumerate(members):
            kind_of[kinds[k] & (kind_of == 0)] = i + 1
        mask = ndimage.binary_fill_holes(ndimage.binary_closing(kind_of > 0, np.ones((9, 9)), iterations=2))
        mask[600:1500, :650] = False                    # the north arrow
        mask[3300:, :1400] = False                      # the legend
        lab, n = ndimage.label(mask)
        _, (iy, ix) = ndimage.distance_transform_edt(~mask, return_indices=True)
        seeds = {}                                      # stone → its patch (centre snapped to the nearest patch)
        for k, (x, y) in centres.items():
            if family_of(k) != family:
                continue
            x, y = int(round(x)), int(round(y))
            sy, sx = iy[y, x], ix[y, x]
            if ((sx - x) ** 2 + (sy - y) ** 2) ** 0.5 <= 1.2 * PX_PER_M:
                seeds[k] = (lab[sy, sx], x, y)
        for comp in range(1, n + 1):
            here = [(k, x, y) for k, (c, x, y) in seeds.items() if c == comp]
            ys, xs = np.nonzero(lab == comp)
            if not here:
                if len(xs) > 400:
                    print("left out: an unnamed", family, "patch of", round(len(xs) / PX_PER_M ** 2, 2), "m² at",
                          to_metres(xs.mean(), ys.mean()))
                continue
            owner = split(lab == comp, dark, here, xs, ys)
            for j, (k, _, _) in enumerate(here):
                px, py = xs[owner == j], ys[owner == j]
                if len(px) >= 3:
                    votes = np.bincount(kind_of[py, px], minlength=3)[1:]
                    stones[k] = stone(k, members[int(votes.argmax())], px, py, shared=len(here) > 1)
    if overlay:
        img = Image.open(path).convert("RGB")
        d = ImageDraw.Draw(img)
        for s in stones.values():
            d.polygon([tuple(p) for p in s["_px"]], outline=(0, 160, 0), width=6)
            cx, cy = np.mean(s["_px"], 0)
            d.text((cx - 20, cy - 20), s["id"], fill=(0, 0, 0), font_size=60)
        img.resize((1400, round(1400 * img.height / img.width))).save(overlay)
    out = [{k: v for k, v in s.items() if k != "_px"} for s in sorted(stones.values(), key=lambda s: s["id"])]
    missing = sorted(set(STONES) - set(stones))
    (Path(__file__).parent / "plan_stones.json").write_text(json.dumps(
        {"source": "Anthony Johnson, Plan of the central Stone Structure at Stonehenge (2007), Wikimedia Commons "
                   "File:Stone_Plan.jpg, CC BY 3.0; coloured by Nightdevil (2018), File:Stone_Plan_Coloured.jpg, "
                   "CC BY-SA 4.0",
         "units": "metres from the plan's centre cross, x east, y north", "stones": out, "not_found": missing},
        indent=1))
    print(len(out), "stones;", "not found:", missing)


if __name__ == "__main__":
    run(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None)
