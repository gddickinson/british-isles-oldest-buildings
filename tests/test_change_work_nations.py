"""Work by sector in Scotland and Ireland (roadmap C5c2c1): Booth's appendices read, checked and grouped; Ireland joined to
the state's census shares after a break."""
import csv
import json
import unittest

from bidb import change_work_ew as ew
from bidb import change_work_nations as wn
from bidb.change_firms import DATA


class Booth(unittest.TestCase):
    def test_every_printed_sum_agrees(self):
        for nation in wn.BOOTH:
            self.assertEqual(ew.check_booth(ew.load_booth(wn.BOOTH[nation])), [], nation)

    def test_pages(self):
        pages = {"sc": {("431", "418"), ("432", "419")}, "irl": {("435", "422"), ("436", "423")}}
        for nation, path in wn.BOOTH.items():
            with open(path, newline="") as f:
                self.assertEqual({(r["leaf"], r["page"]) for r in csv.DictReader(f)}, pages[nation])

    def test_shares(self):
        self.assertEqual(ew.booth_shares(wn.load("sc"))[1881], (23.08, 44.18, 32.74))
        self.assertEqual(ew.booth_shares(wn.load("irl"))[1841], (54.07, 30.81, 15.13))

    def test_left_out(self):
        self.assertEqual(wn.left_out(wn.load("irl"))[1861], 9.8)


class Written(unittest.TestCase):
    def test_ireland_joined_after_a_break(self):
        s = wn.series(wn.load("irl"), {1926: (53.6, 13.0, 33.4)})
        self.assertEqual([y for y, _ in s["primary"]], [1841, 1851, 1861, 1871, 1881, 1926])
        rows = {r["id"]: r for r in json.loads((DATA.parent / "series.json").read_text())}
        self.assertEqual(rows["work_irl_primary"]["breaks"][0][0], 1926)
        self.assertEqual(rows["work_irl_primary"]["models"], ["work_irl_secondary", "work_irl_tertiary"])
        self.assertNotIn("breaks", rows["work_sc_primary"])

    def test_written_csv(self):
        with open(DATA / "work_sc_tertiary.csv", newline="") as f:
            pts = {int(r["year"]): float(r["value"]) for r in csv.DictReader(f)}
        self.assertEqual(pts, {1841: 26.15, 1851: 25.39, 1861: 28.81, 1871: 29.85, 1881: 32.74})


if __name__ == "__main__":
    unittest.main()
