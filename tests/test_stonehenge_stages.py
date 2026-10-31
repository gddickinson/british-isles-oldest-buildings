"""Stonehenge by stages (SH2a): the ditch found in a ground model, the Aubrey Holes numbered and turned onto marked
holes, the five stages built from the research file, and its quotes' sources."""
import math
import unittest

from bidb import stonehenge_layout as L
from bidb import stonehenge_stages as G


def henge(cx=0.5, cy=-1.5, r=54.0):
    """A sloping field with a ditch 2 m deep and a bank inside it, centred on cx, cy."""
    def h(x, y):
        d = math.hypot(x - cx, y - cy)
        ditch = -2 * max(0.0, 1 - ((d - r) / 2.2) ** 2)
        bank = 1.5 * max(0.0, 1 - ((d - (r - 6)) / 2.8) ** 2)
        return 100 + 0.01 * x - 0.02 * y + ditch + bank
    return h


class StagesTest(unittest.TestCase):
    def test_ditch_ring(self):
        fit = G.ditch_ring(henge())
        self.assertAlmostEqual(fit["centre"][0], 0.5, delta=0.2)
        self.assertAlmostEqual(fit["centre"][1], -1.5, delta=0.2)
        self.assertAlmostEqual(fit["radius"], 54.0, delta=0.2)
        self.assertAlmostEqual(fit["bank_crest"], 48.0, delta=0.5)

    def test_aubrey_numbering(self):
        lat0, lon0 = 51.1788, -1.8262
        centre, first = (1.0, -2.0), 52.0
        # Holes 26-32 marked where a circle numbered clockwise from `first` puts them, as tiny squares in lat/lon.
        feats = []
        for n in range(26, 33):
            x, y = L.at(centre, 43.2, first + (n - 1) * 360 / 56)
            lat, lon = lat0 + y / 110574, lon0 + x / (111320 * math.cos(math.radians(lat0)))
            feats.append({"name": "Aubrey Hole", "ref": str(n), "outline": [(lat, lon)]})
        holes, fit = G.aubrey(centre, {"origin": (lat0, lon0), "features": feats}, 43.2)
        self.assertEqual(len(holes), 56)
        self.assertAlmostEqual(fit["first_azimuth"], first, delta=0.05)
        self.assertLess(fit["rms_m"], 0.05)
        # Clockwise: hole 2 lies a 56th of a turn on from hole 1.
        a1, a2 = (L.azimuth(holes[k][1:], centre) for k in (0, 1))
        self.assertAlmostEqual((a2 - a1) % 360, 360 / 56, places=6)

    def test_stages(self):
        out = G.stages({"centre": [0.0, 0.0], "radius": 15.4}, {"origin": (51.1788, -1.8262), "features": []}, henge())
        st = out["stages"]
        self.assertEqual([s["id"] for s in st], ["1", "2", "3", "4", "5"])
        self.assertEqual(sorted(s["year"] for s in st), [s["year"] for s in st])       # in time order, all BC
        self.assertTrue(all(s["year"] < 0 for s in st))
        self.assertEqual(sum(e["kind"] == "aubrey" for e in st[0]["extra"]), 56)
        pits = [e["id"] for e in st[4]["extra"]]
        self.assertEqual(sum(p.startswith("Y") for p in pits), 30)
        self.assertEqual(sum(p.startswith("Z") for p in pits), 29)
        self.assertNotIn("Z8", pits)
        for s in st:
            self.assertTrue(s["cites"], s["id"])
            e = s["earth"]
            self.assertLess(e["ditch_r"] - e["ditch_w"] / 2 - e["bank_gap"] - e["bank_w"], 49)
        self.assertEqual(G.problems(), [])


if __name__ == "__main__":
    unittest.main()
