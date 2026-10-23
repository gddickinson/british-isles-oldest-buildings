"""Change-over-time map layers: HYDE archive member names, palette PNGs, geology period mapping."""
import json
import struct
import unittest
import zlib

from bidb import change_geology as cg
from bidb import change_layers as cl


class HydeLayers(unittest.TestCase):
    def test_member_names_follow_the_archive_layout(self):
        self.assertEqual(cl.member("popd", -4000), "baseline/asc/4000BC_pop/popd_4000BC.asc")
        self.assertEqual(cl.member("cropland", 1300), "baseline/asc/1300AD_lu/cropland1300AD.asc")
        self.assertEqual(cl.member("popd", 0), "baseline/asc/0AD_pop/popd_0AD.asc")

    def test_png_is_a_valid_palette_image_with_mercator_rows(self):
        rows = [[None, 0.1, 3]] + [[1, 1, 1]] * 142 + [[600, 30, None]]      # the window's 144 rows, north first
        data = cl.png(rows, cl.LAYERS["popd"]["edges"], cl.LAYERS["popd"]["colors"], scale=2)
        self.assertEqual(data[:8], b"\x89PNG\r\n\x1a\n")
        w, h, depth, ctype = struct.unpack(">IIBB", data[16:26])
        self.assertEqual((w, h, depth, ctype), (3, 288, 8, 3))
        i = data.index(b"IDAT")
        raw = zlib.decompress(data[i + 4:i + 4 + struct.unpack(">I", data[i - 4:i])[0]])
        first, last = raw[1:4], raw[-3:]
        self.assertEqual(list(first), [0, 0, 2])          # no data, below the first edge, 2–5 class
        self.assertEqual(list(last), [8, 5, 0])           # 500+, 25–50, no data

    def test_cell_area_shrinks_northwards(self):
        self.assertGreater(cl.cell_km2(49), cl.cell_km2(60))
        self.assertAlmostEqual(cl.cell_km2(50), 9.27 * 5.96, delta=1.0)


class Geology(unittest.TestCase):
    def test_irish_age_brackets_take_the_older_period(self):
        self.assertEqual(cg.gsi_period("Palaeozoic, Upper Devonian - Carboniferous"), "Devonian")
        self.assertEqual(cg.gsi_period("Palaeozoic - Mesozoic, Permian - Triassic"), "Permian")
        self.assertEqual(cg.gsi_period("Neoproterozoic, Dalradian Supergroup"), "Precambrian")
        self.assertEqual(cg.gsi_period("Cenozoic, Palaeogene, Oligocene"), "Palaeogene")
        self.assertEqual(cg.gsi_period("Caledonian (Silurian - Devonian)"), "Silurian")

    def test_bgs_periods(self):
        self.assertEqual(cg.bgs_period({"period": "CARBONIFEROUS", "era": "PALAEOZOIC"}), "Carboniferous")
        self.assertEqual(cg.bgs_period({"period": None, "era": "NEOPROTEROZOIC"}), "Precambrian")
        self.assertEqual(cg.bgs_period({"period": None, "era": None}), "Intrusions and undivided")

    def test_layers_file_lists_every_layer_with_a_source(self):
        meta = json.loads((cl.OUT / "layers.json").read_text())["layers"]
        self.assertEqual({l["id"] for l in meta}, {"hyde_popd", "hyde_cropland", "geology", "coalfields"})
        for l in meta:
            for s in l.get("sources") or [l["source"]]:
                self.assertTrue(s["citation"] and s["licence"] and s["url"], l["id"])
        pack = json.loads((cl.OUT / "layers" / "hyde_popd.json").read_text())
        self.assertEqual(sorted(int(y) for y in pack), cl.YEARS)
        self.assertTrue(all(v.startswith("data:image/png;base64,") for v in pack.values()))


if __name__ == "__main__":
    unittest.main()
