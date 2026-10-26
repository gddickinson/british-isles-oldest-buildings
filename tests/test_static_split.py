"""Hosted export: rows split into first-load fields and on-demand files; minor-road encoding.
.venv/bin/python -m unittest discover tests"""
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from app import basemap_tiled, static_export


class LazySplit(unittest.TestCase):
    def test_thumbs_details_outlines_move_out(self):
        rows = [{"id": "Q1", "name": "B", "year_start": 1200, "image_thumb": "x", "sources": "[]",
                 "footprint": "[[0,0]]", "lat": 1, "lon": 2, "category_group": "Domestic"},
                {"id": "Q2", "name": "A", "year_start": -3000, "refs": "[1]"}]
        thumbs = {"Q1": "data:image/webp;base64,AAA"}
        with tempfile.TemporaryDirectory() as tmp, mock.patch.object(static_export, "DIST", Path(tmp)):
            (Path(tmp) / "data").mkdir()
            meta = static_export._split_lazy(rows, thumbs)
            details = json.loads((Path(tmp) / "data" / meta["detail_shards"][0]).read_text())
            outlines = json.loads((Path(tmp) / "data" / meta["outline_shards"][0]).read_text())
            got_thumbs = json.loads((Path(tmp) / "data" / meta["thumb_shards"][rows[0]["t"]]).read_text())
        self.assertNotIn("image_thumb", rows[0])
        self.assertNotIn("sources", rows[0])
        self.assertNotIn("footprint", rows[0])
        self.assertEqual(got_thumbs["Q1"], thumbs["Q1"])
        self.assertEqual(details["Q1"]["sources"], "[]")
        self.assertEqual(details["Q2"]["refs"], "[1]")
        self.assertEqual(outlines["Q1"]["footprint"], "[[0,0]]")
        self.assertNotIn("t", rows[1])                      # no thumbnail: has_image is false


class MinorRoads(unittest.TestCase):
    def test_encode_steps(self):
        self.assertEqual(basemap_tiled._encode([[-1.0, 51.0], [-1.0001, 51.0002], [-1.0001, 51.0002]]),
                         [-10000, 510000, -1, 2])

    def test_join_end_to_end(self):
        a, b, c = [[0, 0], [1, 0]], [[2, 0], [1, 0]], [[5, 5], [6, 6]]
        joined = basemap_tiled._join([a, b, c])
        self.assertIn([[0, 0], [1, 0], [2, 0]], joined)
        self.assertEqual(len(joined), 2)


if __name__ == "__main__":
    unittest.main()


class PlaceIndex(unittest.TestCase):
    def test_shard_hash_matches_browser(self):
        import subprocess
        from app.static_places import shard_of
        ids = ["Q42", "Q126713899", "pio-ruthin-school", "hed-12345", "mm-é-museum", "x"]
        src = Path("app/static/static_places.js").read_text()
        body = src[src.index("const idHash"):src.index("const SHARDS")]
        js = f"const window = {{}}; const INDEX = {{shards: 16}}; {body}; console.log(JSON.stringify({json.dumps(ids)}.map(shardOf)))"
        got = json.loads(subprocess.run(["node", "-e", js], capture_output=True, text=True, check=True).stdout)
        self.assertEqual(got, [shard_of(i) for i in ids])

    def test_cells_and_objects(self):
        from app.static_places import write_index
        rows = [{"id": "a", "name": "A", "lat": 51.5, "lon": -0.1, "kind": "x", "kind_label": "Mill", "kind_group": "G"},
                {"id": "b", "name": "B", "lat": 51.6, "lon": -1.2, "kind_label": "Mill", "kind_group": "G",
                 "building_id": "Q1"},
                {"id": "c", "name": "C", "kind_label": "Hoard", "kind_group": "H"}]
        with tempfile.TemporaryDirectory() as tmp:
            write_index(rows, Path(tmp))
            ix = json.loads((Path(tmp) / "places_index.json").read_text())
            cell = json.loads((Path(tmp) / "pcells" / "51_-2.json").read_text())
        self.assertEqual(ix["cells"], {"51_-2": 2})
        self.assertEqual([r[0] for r in cell], ["a", "b"])
        self.assertEqual(ix["objects"]["Q1"][0][0], "b")
        self.assertEqual(ix["nowhere"][0][:2], ["c", "C"])
