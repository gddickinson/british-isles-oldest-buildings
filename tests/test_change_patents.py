"""Patents per year (roadmap C5a): the IPO's number tables, the 1852-1915 table and Facts and figures Table 1."""
import tempfile
import unittest
from pathlib import Path

from bidb import change_patents as cp
from tests.test_change_registers import _xlsx


def _page(cells):
    return "<table><tr>" + "".join(f"<td>{c}</td>" for c in cells) + "</tr></table>"


class Patents(unittest.TestCase):
    def test_old_series(self):
        page = _page(["Year", "Earliest Patent No", "Year", "Earliest Patent No", "1640", "No 124/1640", "1770",
                      "No 949/1770", "1650", "*", "1780", "No 1243/1780", "1660", "No 128/1660", "1700", "No 365/1700",
                      "1710", "No 396/1709**", "1720", "No 425/1720", "1850", "No 12918/1850", "1852", "No 14359/1852***"])
        rows = cp.old_series(page)
        self.assertEqual(dict(rows)[1650], None)
        self.assertEqual(dict(rows)[1710], 397)                   # the last of 1709, so 1710-19 starts after it
        self.assertEqual(dict(rows)[1852], 14360)
        periods = dict(cp.per_period(rows))
        self.assertEqual(periods[1650], 0.2)                      # 1640-59: the Commonwealth's patents unnumbered
        self.assertEqual(periods[1704], 3.2)                      # 1700-09: 32 patents
        self.assertEqual(periods[1714], 2.8)
        self.assertEqual(periods[1850], round(1442 / 2.75, 1))    # to 1 October 1852

    def test_yearly_1852(self):
        page = _page(["Year", "Applications", "Cumulative Total", "Granted*", "Cumulative Total",
                      "1852/3", "4256", "4256", "2384", "2384", "1884", "17110", "142723", "9984", "92599"])
        self.assertEqual(cp.yearly_1852(page), {1853: (4256, 2384), 1884: (17110, 9984)})

    def test_first_numbers(self):
        page = _page(["Year", "Patent No", "2009", "GB2450674", "20010", "GB2461328", "2011", "GB2471446",
                      "2012", "GB2481570"])
        firsts = cp.first_numbers(page)
        self.assertEqual(sorted(firsts), [2009, 2010, 2011, 2012])
        self.assertEqual(cp.published(firsts)[2011], 10124)
        self.assertNotIn(2012, cp.published(firsts))

    def test_summary(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "ff.xlsx"
            _xlsx(path, [["Intellectual Property Right", "", "2011", "2012", "2013"],
                         ["Patents1", "Applications", 22256, 23229, 22936],
                         ["", "Publications", 10043, 10653, 11021],
                         ["", "Grants", 7173, 6864, 5235],
                         ["Trade marks2", "Applications", 41044, 43873, 50331]])
            out = cp.summary(path, "Table A8")
        self.assertEqual(out[2012], {"applications": 23229, "publications": 10653, "grants": 6864})


if __name__ == "__main__":
    unittest.main()
