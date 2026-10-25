"""Occupations by sector (roadmap C5c): the ONS and CSO readers, the join at 1978, Keibek's quoted figures, the
written series."""
import csv
import json
import tempfile
import unittest
from pathlib import Path

from bidb import change_work as cw
from bidb.change_firms import DATA


def _tmp(text):
    f = tempfile.NamedTemporaryFile("w", suffix=".csv", delete=False)
    f.write(text)
    f.close()
    return Path(f.name)


def _series(sid):
    with open(DATA / f"{sid}.csv", newline="") as f:
        return {int(r["year"]): float(r["value"]) for r in csv.DictReader(f)}


class Readers(unittest.TestCase):
    def test_ons_figure_skips_the_war(self):
        p = _tmp('"Unit","%"\n"","Primary sector","Secondary sector","Tertiary sector"\n'
                 '"1938","9.62","34.03","56.36"\n"1939","","",""\n"1948","8.56","37.34","54.11"\n')
        self.assertEqual(cw.ons_figure(p), {1938: (9.62, 34.03, 56.36), 1948: (8.56, 37.34, 54.11)})

    def test_lms_shares(self):
        s = {c: {1978: 0.0} for cs in cw.LMS.values() for c in cs}
        s["jwr5"][1978], s["jwr7"][1978], s["jwt8"][1978] = 10, 30, 60
        s[cw.LMS_TOTAL] = {1978: 100, 1959: 90}             # years without every section left out
        self.assertEqual(cw.lms_shares(s), {1978: (10.0, 30.0, 60.0)})

    def test_cso_moves_mining_to_primary(self):
        head = '"Industrial Group","County","Sex","Year","VALUE"\n'
        rows = [("All Industries", 100), ("Agriculture", 50), ("Industry", 20), ("Mining", 2), ("Services", 30)]
        p = _tmp(head + "".join(f'"{g}","State","All Persons","1926","{v}"\n' for g, v in rows)
                 + '"Agriculture","Cork","All Persons","1926","9"\n')
        self.assertEqual(cw.cso(p), {1926: (52.0, 18.0, 30.0)})

    def test_cna26_leaves_out_not_stated(self):
        head = '"Age Group","Industrial Group","Sex","Year","VALUE"\n'
        rows = [("All industries", 110), (cw.NOT_STATED, 10), ("Agriculture, forestry and fishing", 8),
                ("Mining, quarrying and turf production", 2), ("Manufacturing industries", 15), ("Construction", 5),
                ("Electricity, gas and water supply", 0), ("Wholesale and retail trade", 70)]
        p = _tmp(head + "".join(f'"15 years and over","{g}","Both sexes","2002","{v}"\n' for g, v in rows)
                 + '"15 - 19 years","Construction","Both sexes","2002","3"\n')
        self.assertEqual(cw.cso_cna26(p), {2002: (10.0, 20.0, 70.0)})

    def test_f7040_splits_by_nace_order(self):
        head = '"Census Year","Means of Travel","Detailed Industrial Group","VALUE"\n'
        rows = [("Farming (0141)", 5), ("Mining support service activities (09)", 5), ("Dairy products (105)", 10),
                ("Other specialised construction activities (439)", 10), ("Motor trades (45)", 70),
                (cw.NOT_STATED, 7), ("Total at work", 107)]
        p = _tmp(head + "".join(f'"2022","All means of travel","{g}","{v}"\n' for g, v in rows)
                 + '"2022","Bicycle","Motor trades (45)","4"\n')
        self.assertEqual(cw.cso_f7040(p), {2022: (10.0, 20.0, 70.0)})

    def test_join_and_compare(self):
        fig = {1977: (3.3, 33.8, 62.9), 1978: (3.29, 33.37, 63.34)}
        now = {1978: (3.35, 33.43, 63.22), 1979: (3.22, 33.01, 63.77)}
        self.assertEqual(cw.joined(fig, now), {1977: fig[1977], 1978: now[1978], 1979: now[1979]})
        d, c0, c1 = cw.compare(fig, now)
        self.assertAlmostEqual(d, 0.12)
        self.assertEqual((c0, c1), (1978, 1978))


class Estimates(unittest.TestCase):
    def test_every_figure_is_in_its_quote(self):
        models = [m for m in json.loads(cw.ESTIMATES.read_text())["models"] if m["id"].startswith("work_")]
        self.assertEqual(len(models), 3)
        for m in models:
            for p in m["points"]:
                for v in (p["value"], p["low"], p["high"]):
                    if v is not None and not p["midpoint"]:
                        self.assertIn(f" {v}", p["quote"], (m["id"], p["year"]))
                if p["midpoint"]:                            # the range's ends are quoted
                    self.assertTrue(str(p["low"]) in p["quote"] and str(p["high"]) in p["quote"])
                    self.assertEqual(p["value"], (p["low"] + p["high"]) / 2)

    def test_sectors_add_up(self):
        est = cw.estimates()
        for i in range(len(est["primary"])):
            ys = {est[s][i][0] for s in cw.SECTORS}
            self.assertEqual(len(ys), 1)
            if ys.pop() > 1600:                              # Table 20 sums to 100 within rounding
                self.assertAlmostEqual(sum(est[s][i][1] for s in cw.SECTORS), 100, delta=0.15)


class Written(unittest.TestCase):
    def test_series(self):
        for s in cw.SECTORS:
            uk = _series(f"work_{s}_uk")
            self.assertEqual(min(uk), 1920)
            self.assertNotIn(1940, uk)
            self.assertIn(1978, uk)
        uk = {s: _series(f"work_{s}_uk") for s in cw.SECTORS}
        for y in uk["primary"]:
            self.assertAlmostEqual(sum(uk[s][y] for s in cw.SECTORS), 100, delta=0.05)
        self.assertLess(uk["primary"][2016], 2)
        ie = _series("work_primary_ie")
        self.assertEqual((min(ie), max(ie)), (1926, 2022))
        self.assertTrue({1996, 2002, 2006, 2011, 2016} <= set(ie))
        self.assertGreater(ie[1926], 50)
        self.assertLess(ie[2022], ie[1996])
        ie = {s: _series(f"work_{s}_ie") for s in cw.SECTORS}
        for y in ie["primary"]:
            self.assertAlmostEqual(sum(ie[s][y] for s in cw.SECTORS), 100, delta=0.05)


if __name__ == "__main__":
    unittest.main()
