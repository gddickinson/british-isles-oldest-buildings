"""{{coord}} templates read by bidb.hoards.coord (Time Team digs, hoards; no network)."""
import unittest

from bidb.hoards import coord


class Coord(unittest.TestCase):
    def test_decimal(self):
        self.assertEqual(coord("{{coord|51.5|-0.12|type:event_region:GB_source:enwiki}}"), (51.5, -0.12))
        self.assertEqual(coord("{{Coord|51.1|  -1.2|}}"), (51.1, -1.2))

    def test_degrees_minutes_seconds(self):
        """The Time Team pages' {{coord|51|48|28|N|1|38|13|W}}: once read as 51°N 48°E (Kazakhstan)."""
        lat, lon = coord("{{coord|51|48|28|N|1|38|13|W|type:event_region:GB|}}")
        self.assertAlmostEqual(lat, 51.80778, 4)
        self.assertAlmostEqual(lon, -1.63694, 4)
        self.assertEqual(coord("{{coord|52|30|N|1|30|E|region:GB}}"), (52.5, 1.5))
        self.assertEqual(coord("{{coord|33|52|S|151|12|E}}"), (-33.0 - 52 / 60, 151.2))

    def test_none(self):
        self.assertIsNone(coord("no template here"))
        self.assertIsNone(coord("{{coord|display=inline}}"))


if __name__ == "__main__":
    unittest.main()
