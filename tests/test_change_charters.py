"""Borough charters 1042-1216 (roadmap C7b1): Ballard's table of sources, read from the page images."""
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

    def test_totals(self):
        f = cc.facts(self.rows)
        self.assertEqual((f["charters"], f["boroughs"]), (323, 137))
        self.assertEqual(f["kinds"], {"crown": 234, "lay": 63, "church": 26})
        self.assertEqual(sum(sum(d.values()) for d in cc.per_decade(self.rows).values()), 323)

    def test_first_charters(self):
        first = {r[0]: r for r in cc.first_charters(self.rows)}
        self.assertEqual(first["London"][3], 1043)                  # Edward the Confessor, 1042-4
        self.assertEqual(first["Bristol"][3], 1164)
        self.assertAlmostEqual(first["Hythe"][2], 1.08, places=2)   # Hythe in Kent, not Hampshire
        self.assertEqual(first["Kilkenny"][5], 1)                   # italics: founded by a lesser lord
        self.assertNotIn("Elvet", first)                            # the prior's borough stands at Durham
        self.assertEqual(len({(r[1], r[2]) for r in first.values()}), len(first))

    def test_series(self):
        pts, rows = cc.series(self.rows)
        self.assertEqual(len(rows), 3)
        self.assertEqual(rows[0]["models"], ["charters_lay_1216", "charters_church_1216"])
        self.assertIn("323 charters to 137 towns", rows[0]["note"])
        self.assertEqual(dict(pts["charters_crown_1216"])[1200], 68)


if __name__ == "__main__":
    unittest.main()
