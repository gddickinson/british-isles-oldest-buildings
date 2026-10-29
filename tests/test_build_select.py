"""Rerunning part of the build (bidb.build.select, --from / --to)."""
import unittest

from bidb import build

STEPS = [("Buildings", 1), ("Places and people", 2), ("Markets, works and infrastructure", 3), ("Sport", 4),
         ("Nations for places", 5), ("Building types", 6), ("Plans of places", 7), ("Stories", 8)]


class TestSelect(unittest.TestCase):
    def test_from_and_to(self):
        self.assertEqual([n for _, n in build.select(STEPS, "markets", "plans of")], [3, 4, 5, 6, 7])
        self.assertEqual([n for _, n in build.select(STEPS, "Sport")], [4, 5, 6, 7, 8])
        self.assertEqual(build.select(STEPS), STEPS)

    def test_unknown_stage(self):
        with self.assertRaises(SystemExit):
            build.select(STEPS, "nothing")


if __name__ == "__main__":
    unittest.main()
