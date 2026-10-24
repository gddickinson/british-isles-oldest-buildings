"""Overseas trade (roadmap C5b1): Federico-Tena workbooks, ONS and CSO CSVs, Our World in Data shares."""
import tempfile
import unittest
from pathlib import Path

from bidb import change_trade as ct
from tests.test_change_registers import _xlsx


class Trade(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.d = Path(self.dir.name)

    def tearDown(self):
        self.dir.cleanup()

    def test_ft(self):
        path = self.d / "ft.xlsx"
        _xlsx(path, [["Ireland"], ["", "Current boundaries", "", "", "1913 boundaries"], ["", "(millions 1913 $)"],
                     ["", "Imports ", "Exports", "", "Imports ", "Exports"], ["1921", "", ""],
                     ["1922", 109.4, 68.2, "", 50.1, 7.0], ["1923", 209.8, 90.0]])
        self.assertEqual(ct.ft(path, "Table A8"), {1922: (109.4, 68.2), 1923: (209.8, 90.0)})

    def test_ons_and_reference_year(self):
        path = self.d / "ikbk.csv"
        path.write_text('"Title","Total Trade (TT): WW: Exports: BOP: CVM: SA"\n"CDID","IKBK"\n"Important notes",\n'
                        '"2023","850"\n"2024","882"\n"2024 Q1","220"\n"2024 JAN","70"\n')
        cvm = ct.ons(path)
        self.assertEqual(cvm, {2023: 850.0, 2024: 882.0})
        self.assertEqual(ct.reference_year(cvm, {2023: 870.0, 2024: 882.0}), 2024)

    def test_cso(self):
        path = self.d / "tsa01.csv"
        path.write_text('﻿"STATISTIC","Statistic Label","TLIST(A1)","Year","C02196V02652","State","UNIT","VALUE"\n'
                        '"TSA01C1","Total Imports","1930","1930","-","State","Euro Thousand","72091"\n'
                        '"TSA01C2","Total Exports","1930","1930","-","State","Euro Thousand","57068"\n'
                        '"TSA01C3","Trade Surplus (Exports Minus Imports)","1930","1930","-","State","Euro Thousand","-15022"\n'
                        '"TSA01C1","Total Imports","1931","1931","-","State","Euro Thousand","64072"\n')
        self.assertEqual(ct.cso(path), {1930: (72091.0, 57068.0)})        # 1931 has no exports row

    def test_owid_and_share(self):
        path = self.d / "owid.csv"
        path.write_text("Entity,Code,Year,Value of global merchandise exports as a share of GDP\n"
                        "Ireland,IRL,1926,25.99\nUnited Kingdom,GBR,1948,13.2\nUnited Kingdom,GBR,1949,14.0\n")
        self.assertEqual(ct.owid(path, "United Kingdom"), {1948: 13.2, 1949: 14.0})
        self.assertEqual(ct.share({1948: 1665, 1950: 1}, {1948: 11383, 1949: 5}), {1948: 14.63})


if __name__ == "__main__":
    unittest.main()
