import copy
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from bidb import building_types, evidence

SRC = {"title": "Hall house", "author": "Wikipedia", "kind": "reference", "url": "https://x/hall",
       "locator": "lead", "quote": "a public hall"}
GOOD = {
    "types": [
        {"id": "hall", "name": "Hall house", "family": "Hall houses", "domain": "Domestic", "fish": "70943"},
        {"id": "wealden", "name": "Wealden house", "family": "Hall houses", "domain": "Domestic", "fish": "71335"},
        {"id": "abroad", "name": "Somewhere else", "family": "Abroad", "domain": "Domestic", "fish": None,
         "abroad": True},
    ],
    "links": [
        {"id": "hall>wealden", "from": "hall", "to": "wealden", "kind": "variant", "confidence": "documented",
         "claim": "c", "sources": [SRC]},
        {"id": "abroad>hall", "from": "abroad", "to": "hall", "kind": "influence", "confidence": "disputed",
         "claim": "c", "sources": [SRC], "views": ["yes", "no"]},
    ],
}


class BuildingTypesTest(unittest.TestCase):
    def test_good(self):
        self.assertEqual(building_types.validate(GOOD), [])

    def test_problems(self):
        d = copy.deepcopy(GOOD)
        d["links"][0]["kind"] = "ancestor"
        d["links"][1]["views"] = ["yes"]
        d["links"].append({"id": "wealden>nowhere", "from": "wealden", "to": "nowhere", "kind": "descent",
                           "confidence": "probable", "claim": "c", "sources": [dict(SRC, quote="")]})
        d["types"].append({"id": "lonely", "name": "L", "family": "F", "domain": "D"})
        bad = building_types.validate(d)
        for text in ("kind 'ancestor'", "disputed without two views", "unknown type 'nowhere'",
                     "source without title, quote", "lonely: neither a FISH concept", "lonely: not in any link"):
            self.assertTrue(any(text in b for b in bad), (text, bad))

    def test_descent_loop(self):
        d = copy.deepcopy(GOOD)
        d["links"].append({"id": "wealden>hall", "from": "wealden", "to": "hall", "kind": "descent",
                           "confidence": "probable", "claim": "c", "sources": [SRC]})
        self.assertTrue(any("loop" in b for b in building_types.validate(d)))

    def test_tree_and_claims(self):
        self.assertEqual(building_types.family_tree(GOOD)["Domestic"]["Hall houses"], ["hall", "wealden"])
        self.assertEqual([c["id"] for c in building_types.claims(GOOD)], ["link:hall>wealden", "link:abroad>hall"])

    def test_quote_check_writes_its_own_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "check.json"
            with mock.patch("bidb.verify_research.source_text", return_value="A house with a PUBLIC hall."), \
                    mock.patch("bidb.evidence.time.sleep"):
                out = evidence.check(log=lambda *_: None, claims=building_types.claims(GOOD), path=path)
            self.assertEqual(out["link:hall>wealden"]["sources"], ["quote-found"])
            self.assertEqual(json.loads(path.read_text()).keys(), out.keys())

    def test_load_merges_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            a, b = copy.deepcopy(GOOD), {"types": [{"id": "barn", "name": "Barn", "family": "Barns",
                                                    "domain": "Agricultural", "fish": "68547"}],
                                         "links": [dict(GOOD["links"][0], id="hall>barn", to="barn")]}
            (Path(tmp) / "lineage.json").write_text(json.dumps(a))
            (Path(tmp) / "lineage_agricultural.json").write_text(json.dumps(b))
            with mock.patch.object(building_types, "PATH", Path(tmp) / "lineage.json"):
                data = building_types.load()
            self.assertEqual([t["id"] for t in data["types"]], ["hall", "wealden", "abroad", "barn"])
            self.assertEqual(building_types.validate(data), [])

    def test_curated_file(self):
        if building_types.PATH.exists():
            self.assertEqual(building_types.validate(building_types.load()), [])

    def test_curated_domains(self):
        if building_types.PATH.exists():
            domains = set(building_types.family_tree(building_types.load()))
            self.assertLessEqual({"Domestic", "Defence", "Religious", "Agricultural", "Commercial", "Industrial",
                                  "Transport"}, domains)


if __name__ == "__main__":
    unittest.main()
