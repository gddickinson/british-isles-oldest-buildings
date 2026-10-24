"""Companies from the registers (roadmap C4b): SIC codes to industries, Table A8, Companies House and CRO counts."""
import tempfile
import unittest
import zipfile
from pathlib import Path

from bidb import change_registers as cr

M = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
R = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"


def _xlsx(path, rows):
    """A one-sheet workbook ("Table A8") with inline numbers and shared strings."""
    strings, xml_rows = [], []
    for i, row in enumerate(rows, 1):
        cells = []
        for col, v in zip("ABCDEFG", row):
            if isinstance(v, str):
                strings.append(v)
                cells.append(f'<c r="{col}{i}" t="s"><v>{len(strings) - 1}</v></c>')
            else:
                cells.append(f'<c r="{col}{i}"><v>{v}</v></c>')
        xml_rows.append(f'<row r="{i}">{"".join(cells)}</row>')
    with zipfile.ZipFile(path, "w") as z:
        z.writestr("xl/workbook.xml", f'<workbook xmlns="{M}" xmlns:r="{R}"><sheets>'
                                      f'<sheet name="Table A8" sheetId="1" r:id="rId1"/></sheets></workbook>')
        z.writestr("xl/_rels/workbook.xml.rels", '<Relationships xmlns="http://schemas.openxmlformats.org/package/'
                   '2006/relationships"><Relationship Id="rId1" Target="worksheets/sheet1.xml"/></Relationships>')
        z.writestr("xl/sharedStrings.xml", f'<sst xmlns="{M}">' + "".join(f"<si><t>{s}</t></si>" for s in strings)
                   + "</sst>")
        z.writestr("xl/worksheets/sheet1.xml", f'<worksheet xmlns="{M}"><sheetData>{"".join(xml_rows)}'
                                               "</sheetData></worksheet>")


class Registers(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.tmp = Path(self.dir.name)

    def tearDown(self):
        self.dir.cleanup()

    def test_sic_sector(self):
        name = lambda t: cr.SECTORS[cr.sic_sector(t)][0]
        self.assertEqual(name("11050 - Manufacture of beer"), "Food, drink and tobacco")
        self.assertEqual(name("18129 - Printing n.e.c."), "Publishing, print and media")
        self.assertEqual(name("64191 - Banks"), "Banks, finance and insurance")
        self.assertEqual(name("47110 - Retail sale in non-specialised stores"), "Shops and trade")
        self.assertEqual(name("41202 - Construction of domestic buildings"), "Making things")
        self.assertIsNone(cr.sic_sector("99999 - Dormant Company"))
        self.assertIsNone(cr.sic_sector("None Supplied"))

    def test_a8_financial_years(self):
        path = self.tmp / "a8.xlsx"
        _xlsx(path, [["Table A8: Historical data"], ["Year ending", "Total register", "Effective register",
                     "Incorporations", "Dissolved"], ["1939", 173300, 163900, 11100, 9200],
                     ["1986 - 87", 1066300, 867300, 117800, 84200], ["United Kingdom4"],
                     ["Notes"], ["1. Unless otherwise stated"]])
        self.assertEqual(cr.a8(path), {1939: (173300, 163900, 11100, 9200), 1987: (1066300, 867300, 117800, 84200)})

    def test_companies_house_counts_companies_act_companies(self):
        head = ["CompanyName", " CompanyNumber", "CompanyCategory", "IncorporationDate", "SICCode.SicText_1"]
        rows = [["A LTD", "1", "Private Limited Company", "11/09/2012", "62020 - IT consultancy"],
                ["B LTD", "2", "Private Limited Company", "01/01/2015", "99999 - Dormant Company"],
                ["GOLDSMITHS", "3", "Royal Charter Company", "01/01/1327", ""],
                ["C LLP", "4", "Limited Liability Partnership", "01/01/2012", "69201 - Accounting"]]
        path = self.tmp / "ch.zip"
        with zipfile.ZipFile(path, "w") as z:
            z.writestr("ch.csv", "\n".join(",".join(f'"{v}"' for v in r) for r in [head] + rows) + "\n")
        years, decades = cr.companies_house(path)
        self.assertEqual(dict(years), {2012: 1, 2015: 1})
        self.assertEqual(decades[2010][0], 2)
        self.assertEqual(sum(decades[2010][1:]), 1)          # the dormant company counts in no industry

    def test_cro_years(self):
        lines = ["company_num,company_status,company_reg_date,comp_dissolved_date",
                 "1,Normal ,2019-04-09,",
                 "2,Dissolved,2019-05-01,2021-02-25",
                 "3,Strike Off Listed,1753-01-01,",
                 "4,Struck Off,2020-01-01,",
                 "5,Normal,,"]
        path = self.tmp / "cro.zip"
        with zipfile.ZipFile(path, "w") as z:
            z.writestr("companies.csv", "\n".join(lines) + "\n")
        years, total, undated = cr.cro(path)
        self.assertEqual(years, {2019: [2, 0, 1], 2020: [1, 0, 0], 2021: [0, 1, 0]})
        self.assertEqual((total, undated), (5, 1))


if __name__ == "__main__":
    unittest.main()
