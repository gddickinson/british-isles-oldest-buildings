"""Tea duty 1847-1964 (C2d3, C2d3b2): the steps join up (each change starts from the rate before it), every row
cites a page of the Statistical Abstract or quotes Hansard, an Act or the Gazette, and the series ends at nil in 1964."""
import csv
import json
import unittest

from bidb import change_series as cs

DATA = cs.SRC / "data"


def rows(name):
    with open(DATA / name, newline="") as f:
        return list(csv.DictReader(f))


class TeaDuty(unittest.TestCase):
    def test_steps_join_up(self):
        for name in ("tea_duty_uk.csv", "tea_duty_empire_uk.csv"):
            values = [float(r["value"]) for r in rows(name)]
            years = [int(r["year"]) for r in rows(name)]
            self.assertEqual(years, sorted(years), name)
            # rows of one year come in pairs: old rate then new rate; the old rate is the last rate before it
            for i in range(1, len(values)):
                if years[i] == years[i - 1] and i >= 2 and years[i - 2] != years[i - 1]:
                    self.assertEqual(values[i - 1], values[i - 2], (name, years[i]))

    def test_span(self):
        full = cs.read_points(DATA / "tea_duty_uk.csv")
        self.assertEqual((full[0][0], full[0][1]), (1847, 26.25))
        self.assertEqual((full[-1][0], full[-1][1]), (1964, 0))
        empire = cs.read_points(DATA / "tea_duty_empire_uk.csv")
        self.assertEqual((empire[-1][0], empire[-1][1]), (1949, 0))

    def test_every_row_cites(self):
        for name in ("tea_duty_uk.csv", "tea_duty_empire_uk.csv"):
            for r in rows(name):
                page = r["edition"] and r["leaf"].isdigit() and r["page"].isdigit()
                quoted = any(k in r["note"] for k in ("HC Deb", "Finance Act", "London Gazette")) and "'" in r["note"]
                self.assertTrue(page or quoted, (name, r["year"]))

    def test_sources_known(self):
        sources = json.loads((cs.SRC / "sources.json").read_text())
        series = {s["id"]: s for s in json.loads((cs.SRC / "series.json").read_text())}
        for sid in ("tea_duty_uk", "tea_duty_empire_uk"):
            for src in series[sid]["sources"]:
                self.assertIn(src, sources)


if __name__ == "__main__":
    unittest.main()
