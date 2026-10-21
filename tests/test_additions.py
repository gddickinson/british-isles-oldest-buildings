"""On this day (calendars), timelines, long-distance stages, polylines, street-tile planning.
.venv/bin/python -m unittest discover tests"""
import unittest

from app import street_tiles
from bidb import timeline, tour_trails
from bidb.on_this_day import gregorian_to_julian
from bidb.tour_elevation import climb_descent, decode, encode, hilliness, sample


class Calendars(unittest.TestCase):
    def test_julian_dates_come_back(self):
        self.assertEqual(gregorian_to_julian(1066, 10, 20), (1066, 10, 14))      # Battle of Hastings
        self.assertEqual(gregorian_to_julian(1752, 9, 14), (1752, 9, 3))         # the calendar change


class Timeline(unittest.TestCase):
    def test_events_one_per_year_and_kind(self):
        entry = {"s": [["History", "The castle was first built in 1070. It was besieged in 1644. "
                                   "It was rebuilt in 1820 after a fire. Joan was burned at the stake in 1537."],
                       ["References", "Smith (1990) was published."]]}
        got = [(y, k) for y, k, _ in timeline.events(entry)]
        self.assertIn((1070, "built"), got)
        self.assertIn((1644, "war"), got)
        self.assertNotIn((1537, "fire"), got)
        self.assertFalse(any(y == 1990 for y, _ in got))


class Trails(unittest.TestCase):
    def test_stages_cover_the_route(self):
        stops = [(5, {"name": "A"}), (25, {"name": "B"}), (59, {"name": "C"})]
        days = tour_trails.stages(60, stops)
        self.assertEqual(len(days), 3)
        self.assertEqual(days[0]["stops"], ["A"])
        self.assertEqual(days[-1]["stops"], ["C"])


class Lines(unittest.TestCase):
    def test_polyline_round_trip_and_sampling(self):
        line = [[54.1, -3.2], [54.2, -3.0], [53.9, -2.5]]
        self.assertEqual(decode(encode(line)), line)
        self.assertEqual(len(sample(line, 10)), 10)
        self.assertEqual(hilliness(50, 20), "flat")
        self.assertEqual(hilliness(500, 20), "very hilly")
        self.assertEqual(hilliness(6, 1.2), "flat")

    def test_climb_ignores_noise(self):
        noisy = [10, 11, 10, 12, 10, 11, 12, 10, 11] * 10          # +-2 m wobble on a flat route
        self.assertEqual(climb_descent(noisy), (0.0, 0.0))
        self.assertEqual(climb_descent([0, 5, 10, 8, 20, 15]), (20.0, 5.0))


class StreetTiles(unittest.TestCase):
    def test_plan_counts_tiles_per_zoom(self):
        york = [53.95, -1.10, 53.97, -1.06]
        tiles = street_tiles.plan(york)
        self.assertTrue(all(street_tiles.MIN_ZOOM <= z <= street_tiles.MAX_ZOOM for z, _, _ in tiles))
        self.assertLess(len(tiles), 100)


if __name__ == "__main__":
    unittest.main()
