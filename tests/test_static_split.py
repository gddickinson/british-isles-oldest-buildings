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
