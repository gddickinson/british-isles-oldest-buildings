"""Steam power (roadmap C5e2b2b2a): Kanefsky's horsepower of steam, water and wind as summarised by Crafts (2004),
quoted per figure in estimates.json."""
import unittest

from bidb import change_steam as cs


class Power(unittest.TestCase):
    def test_parts_add_to_the_printed_totals(self):
        self.assertEqual(cs.check(), [])

    def test_working_paper_figures_are_caught(self):
        t = cs.table()
        t["steam"][1830] = t["water"][1830] = 160000      # LSE WP 75/03 p. 17
        self.assertEqual(len(cs.check(t)), 1)

    def test_quotes(self):
        for p in cs.model()["points"]:
            self.assertIn(p["printed"], p["quote"])
            self.assertEqual(int(p["printed"].replace(",", "")), p["value"])

    def test_series(self):
        pts, rows = cs.series()
        self.assertEqual(sorted(pts), ["power_steam_gb", "power_water_gb", "power_wind_gb"])
        steam = {p[0]: p[1] for p in pts["power_steam_gb"]}
        self.assertEqual(steam, {1760: 5000, 1800: 35000, 1830: 165000, 1870: 2060000, 1907: 9659000})
        self.assertTrue(rows[0]["log"])
        self.assertTrue(all(r["style"] == "estimates" for r in rows))
        self.assertIn("165,000 each", rows[0]["note"])
        self.assertIn("98% of the total", rows[0]["note"])


if __name__ == "__main__":
    unittest.main()
