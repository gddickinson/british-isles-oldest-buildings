"""Sun and moon on the horizon (bidb.sky) and its browser mirror (app/static/sky.js)."""
import json
import shutil
import subprocess
import unittest
from pathlib import Path

from bidb import sky

ROOT = Path(__file__).resolve().parent.parent


class SkyTest(unittest.TestCase):
    def test_obliquity(self):
        self.assertAlmostEqual(sky.obliquity(2000), 23.4393, places=3)
        self.assertAlmostEqual(sky.obliquity(-3000), 24.02, places=1)     # larger in the Neolithic

    def test_azimuths(self):
        # Stonehenge, midsummer sunrise over a flat horizon: about 49°; a little further north 4,500 years ago
        now = sky.event_azimuth(51.1789, "sun", "summer_solstice", "rise")
        self.assertAlmostEqual(now, 49.2, delta=0.3)
        self.assertLess(sky.event_azimuth(51.1789, "sun", "summer_solstice", "rise", year=-2500), now)
        # sunset mirrors sunrise; the equinox sun rises a little north of east (refraction, upper limb)
        self.assertAlmostEqual(sky.event_azimuth(53.7, "sun", "winter_solstice", "set"),
                               360 - sky.event_azimuth(53.7, "sun", "winter_solstice", "rise"))
        self.assertTrue(88 < sky.event_azimuth(53.7, "sun", "equinox", "rise") < 90)
        # far enough north the southern moon of a major standstill never rises; at Callanish it skims the south
        self.assertIsNone(sky.azimuth(70.5, -29.2, "rise", "moon"))
        self.assertTrue(195 < sky.event_azimuth(58.2, "moon", "major_south", "set", year=-2900) < 210)

    def test_inverse(self):
        for az in (50, 90, 130):
            dec = sky.declination_of(52, az)
            self.assertAlmostEqual(sky.azimuth(52, dec), az, places=6)

    def test_dates(self):
        jd = sky.julian_day(2026, 10, 29)
        self.assertEqual(sky.calendar_date(jd), (2026, 10, 29))
        self.assertEqual(sky.calendar_date(sky.next_sun_event("winter_solstice", jd)), (2026, 12, 21))
        self.assertEqual(sky.calendar_date(sky.next_sun_event("summer_solstice", jd)), (2027, 6, 21))
        self.assertEqual(sky.calendar_date(sky.next_sun_event("equinox", jd)), (2027, 3, 20))
        self.assertEqual(sky.calendar_date(sky.next_standstill("major", sky.julian_day(2020, 1, 1)))[0], 2025)
        self.assertAlmostEqual(sky.sun_declination(sky.julian_day(2026, 6, 21) + 0.5), 23.44, delta=0.01)

    def test_problems(self):
        good = {"id": "x", "name": "X", "lat": 51, "lon": -1, "body": "sun", "event": "winter_solstice",
                "rise_set": "set", "verdict": "established", "claim": "c",
                "sources": [{"title": "t", "url": "u", "quote": "q"}]}
        self.assertEqual(sky.problems([good]), [])
        bad = dict(good, event="midsummer", verdict="disputed", sources=[{"title": "t"}])
        self.assertEqual(len(sky.problems([bad, bad])), 7)    # event, views, source twice; duplicate id
        self.assertEqual(sky.problems(), [])                  # the researched file

    @unittest.skipUnless(shutil.which("node"), "node not installed")
    def test_browser_mirror(self):
        script = (ROOT / "app" / "static" / "sky.js").read_text() + """
            const out = [];
            for (const [lat, body, ev, rs, y] of INPUT) out.push(Sky.eventAzimuth(lat, body, ev, rs, y));
            out.push(Sky.declinationOf(52, 60), Sky.sunDeclination(2461000.5), Sky.nextSunEvent("samhain", 2461342.5),
                     Sky.nextStandstill("minor", 2461342.5));
            console.log(JSON.stringify(out));"""
        cases = [(51.18, "sun", "summer_solstice", "rise", 2000), (53.7, "sun", "winter_solstice", "set", -3100),
                 (58.2, "moon", "major_south", "set", -2900), (57.0, "moon", "minor_north", "rise", 2000),
                 (55.0, "sun", "imbolc", "rise", 500)]
        script = f"const INPUT = {json.dumps(cases)};\n" + script
        js = json.loads(subprocess.run(["node", "-e", script], capture_output=True, text=True, check=True).stdout)
        py = [sky.event_azimuth(*c) for c in cases] + [sky.declination_of(52, 60), sky.sun_declination(2461000.5),
              sky.next_sun_event("samhain", 2461342.5), sky.next_standstill("minor", 2461342.5)]
        for a, b in zip(js, py):
            self.assertAlmostEqual(a, b, places=6)


if __name__ == "__main__":
    unittest.main()
