"""Borough charters 1042-1307 (roadmap C7b1, C7b2): the tables of sources of both volumes, read from the page images."""
import unittest

from bidb import change_charters as cc


class Charters(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows = cc.load()

    def test_checks_pass(self):
        self.assertEqual(cc.check(self.rows), [])

    def test_dates(self):
        self.assertEqual(cc.years("1157-85"), (1157, 1185, 1))
        self.assertEqual(cc.years("1154-8"), (1154, 1158, 1))
        self.assertEqual(cc.years("1087-1107"), (1087, 1107, 1))
        self.assertEqual(cc.years("1118-68 (3)"), (1118, 1168, 3))
        self.assertEqual(cc.years("1205 (May 29)"), (1205, 1205, 1))
        self.assertEqual(cc.years("c. 1175"), (1175, 1175, 1))
        self.assertEqual(cc.years("After 1212"), (1212, 1212, 1))
        self.assertEqual(cc.years("1154-89 (R)"), (1154, 1189, 1))
        self.assertEqual(cc.years("1228 (b)"), (1228, 1228, 1))
        self.assertEqual(cc.years("?1296"), (1296, 1296, 1))
        self.assertEqual(cc.years("1230?"), (1230, 1230, 1))
        self.assertEqual(cc.years("1272-c. 74"), (1272, 1274, 1))
        self.assertEqual(cc.years("1241-c. 1286"), (1241, 1286, 1))
        self.assertEqual(cc.years("1254 (Fine)"), (1254, 1254, 1))
        with self.assertRaises(ValueError):
            cc.years("Do.")

    def test_bad_rows_are_caught(self):
        rows = [dict(r) for r in self.rows]
        rows[0]["first"], rows[0]["last"] = 1185, 1157
        rows[1]["style"] = "capitals" if rows[1]["style"] != "capitals" else "roman"   # Andover printed two ways
        rows[2]["place"] = "Nowhere"
        self.assertEqual(len(cc.check(rows)), 3)

    def test_kinds(self):
        self.assertEqual(cc.kind("Henry II"), "crown")
        self.assertEqual(cc.kind("John (to Wm. Briwerr)"), "crown")
        self.assertEqual(cc.kind("John, Count of Mortain"), "lay")
        self.assertEqual(cc.kind("Odo, Bp. of Bayeux"), "church")
        self.assertEqual(cc.kind("Henry, Abbot of Fécamp"), "church")
        self.assertEqual(cc.kind("Walter de Lacy"), "lay")
        self.assertEqual(cc.kind("Henry III (to Prior)"), "crown")
        self.assertEqual(cc.kind("Edward son of Henry III"), "lay")         # the Lord Edward
        self.assertEqual(cc.kind("Richard, king of the Romans"), "lay")     # earl of Cornwall
        self.assertEqual(cc.kind("Jordan Bishop"), "lay")                   # a surname
        self.assertEqual(cc.kind("Gilbert dean of Cloyne"), "church")
        self.assertEqual(cc.kind("Mayor and community"), "other")
        self.assertEqual(cc.kind(""), "other")

    def test_totals(self):
        f = cc.facts(self.rows)
        self.assertEqual((f["v1"], f["v2"], f["charters"], f["boroughs"]), (329, 532, 861, 261))
        self.assertEqual(f["kinds"], {"crown": 621, "lay": 177, "church": 51})
        self.assertEqual((f["other"], f["john"], f["henry3"], f["edward1"]), (12, 99, 235, 117))
        self.assertEqual(sum(sum(d.values()) for d in cc.per_decade(self.rows).values()), 861)
        v1 = cc.load(path_1923=None)
        self.assertEqual(sum(r["count"] for r in v1), 329)              # 323 + 8 printed, 2 dated again in 1923
        self.assertEqual(sum(r["count"] for r in cc.load(path_1923=None, appendix=None)), 321)

    def test_appendix(self):
        app = [r for r in self.rows if r["table"] == "charters_ballard_1913_appendix"]
        self.assertEqual((len(app), {r["volume"] for r in app}), (8, {1}))
        self.assertEqual({r["style"] for r in self.rows if r["borough"] == "Hartlepool" and r["volume"] == 1},
                         {"roman", "italics"})                          # printed two ways, checked per table

    def test_volumes(self):
        v2 = [r for r in self.rows if r["volume"] == 2]
        self.assertEqual(min(r["year"] for r in v2), 1216)               # Helmsley c. 1186-1227 kept at 1216
        self.assertEqual(max(r["year"] for r in self.rows if r["volume"] == 1), 1216)
        oxf = [r for r in v2 if r["borough"] == "Oxford (University)" and r["date"] == "1301 (b)"]
        self.assertEqual(oxf[0]["year"], 1305)                           # footnote: "Should be 1305"
        self.assertEqual({r["date"] for r in self.rows if r["borough"] == "Rathmore"}, {"1215-57"})

    def test_first_charters(self):
        first = {r[0]: r for r in cc.first_charters(self.rows)}
        self.assertEqual(first["London"][3], 1043)                  # Edward the Confessor, 1042-4
        self.assertEqual(first["Bristol"][3], 1164)
        self.assertAlmostEqual(first["Hythe"][2], 1.08, places=2)   # Hythe in Kent, not Hampshire
        self.assertEqual(first["Kilkenny"][5], 1)                   # italics: founded by a lesser lord
        self.assertNotIn("Elvet", first)                            # the prior's borough stands at Durham
        self.assertEqual(first["Kingston upon Hull"][3], 1299)       # Edward I, first in the second volume
        self.assertEqual(first["Skinburness"][3], 1300)              # Wavermouth, the same port (critical note)
        self.assertAlmostEqual(first["Berwick"][1], 55.77, places=2) # Berwick-upon-Tweed
        self.assertNotIn("Rathcool", first)
        self.assertAlmostEqual(first["Rathcoole"][2], -6.47, places=2)   # the archbishop of Dublin's, co. Dublin
        self.assertEqual(first["Hartlepool"][3], 1173)               # appendix: Adam de Brus, 1162-85
        self.assertEqual(first["Torksey"][3], 1165)                  # appendix only
        self.assertEqual(len({(r[1], r[2]) for r in first.values()}), len(first))

    def test_series(self):
        pts, rows = cc.series(self.rows)
        self.assertEqual(len(rows), 3)
        self.assertEqual(rows[0]["models"], ["charters_lay", "charters_church"])
        self.assertEqual(rows[0]["breaks"][0][0], 1216)
        self.assertIn("861 charters to 261 towns", rows[0]["note"])
        self.assertEqual(dict(pts["charters_crown"])[1200], 68)
        self.assertEqual(dict(pts["charters_crown"])[1250], 86)

if __name__ == "__main__":
    unittest.main()
