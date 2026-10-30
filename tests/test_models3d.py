"""3D models (SH3): the registry and links, ground levelled under a mound, research quotes as claims (no network)."""
import json
import unittest
from unittest import mock

from bidb import models3d


class Models3DTest(unittest.TestCase):
    def test_registry(self):
        ids = [m["id"] for m in models3d.MODELS]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertTrue(models3d.ready(models3d.get("stonehenge")))
        self.assertEqual(models3d.links()["Q39671"], "/stonehenge")
        self.assertEqual(models3d.links(static=True)["Q39671"], "stonehenge.html")
        for m in models3d.MODELS:
            if models3d.ready(m) and m["id"] != "stonehenge":
                self.assertEqual(models3d.links()[m["record"]], f"/model/{m['id']}")

    def test_flatten(self):
        grid = [[float(i + j) for j in range(21)] for i in range(21)]     # a slope, 2 m cells, centre (0, 0)
        level = models3d.flatten_grid(grid, 2, {"c": [0, 0], "r": 6, "edge": 4})
        self.assertAlmostEqual(grid[10][10], level)
        self.assertAlmostEqual(grid[10][12], level)                        # 4 m from the centre: flat
        self.assertEqual(grid[0][0], 0.0)                                  # far corner untouched
        self.assertAlmostEqual(level, 20, delta=0.5)                       # the ring round a plane averages its centre

    def test_despike(self):
        alt = [50] * 20
        alt[7], alt[8], alt[9] = 282, 770, 548                             # Calanais's bad terrain pixel at 340°
        alt[15] = 120                                                      # a small real rise stays
        out = models3d.despike(alt)
        self.assertEqual(out[6:11], [50] * 5)
        self.assertEqual(out[15], 120)

    def test_claims(self):
        fake = {"name": "X", "record": "Q1", "sources": {"a": {"title": "A", "url": "https://a"}, "b": {"title": "B"}},
                "facts": {"r_m": {"value": 1, "cites": [{"source": "a", "quote": "one"}, {"source": "b", "quote": "two"}]}},
                "elements": [{"id": "s1", "cites": [{"source": "a", "quote": "three"}, {"source": "zz", "quote": "?"}]}]}
        with mock.patch.object(models3d, "research", return_value=fake):
            claims = models3d.claims("x")
            self.assertEqual(len(claims), 1)                               # b has no URL, zz is unknown
            self.assertEqual([s["quote"] for s in claims[0]["sources"]], ["one", "three"])
            self.assertEqual(models3d.problems("x"), ["x: unknown source zz"])

    def test_research_files(self):
        for path in models3d.HERE.glob("*.json"):
            json.loads(path.read_text())
            self.assertEqual(models3d.problems(path.stem), [], path.name)


if __name__ == "__main__":
    unittest.main()
