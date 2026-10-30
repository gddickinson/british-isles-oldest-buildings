"""bidb.xls_read on a small BIFF8 workbook built here, and bidb.church_survey's matching rule."""
import struct
import tempfile
import unittest
from pathlib import Path

from bidb import church_survey, xls_read

END, FREE = 0xFFFFFFFE, 0xFFFFFFFF


def rec(rid, body):
    return struct.pack("<HH", rid, len(body)) + body


def compound(stream):
    """A compound file holding one stream named Workbook (512-byte sectors: FAT, directory, then the stream)."""
    stream += b"\0" * (-len(stream) % 512)
    n = max(len(stream) // 512, 8)
    stream += b"\0" * (n * 512 - len(stream))
    fat = [0xFFFFFFFD, END] + [3 + i for i in range(n - 1)] + [END]
    fat += [FREE] * (128 - len(fat))
    head = bytearray(512)
    head[:8] = b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1"
    struct.pack_into("<HHHHH", head, 24, 0x3E, 3, 0xFFFE, 9, 6)
    struct.pack_into("<IIIIIIIII", head, 40, 0, 1, 1, 0, 4096, END, 0, END, 0)
    struct.pack_into("<109I", head, 76, *([0] + [FREE] * 108))

    def entry(name, kind, start, size):
        e = bytearray(128)
        raw = (name + "\0").encode("utf-16-le")
        e[:len(raw)] = raw
        struct.pack_into("<HB", e, 64, len(raw), kind)
        struct.pack_into("<III", e, 68, FREE, FREE, FREE)
        struct.pack_into("<IQ", e, 116, start, size)
        return bytes(e)
    directory = entry("Root Entry", 5, END, 0) + entry("Workbook", 2, 2, len(stream)) + b"\0" * 256
    return bytes(head) + struct.pack("<128I", *fat) + directory + stream


def workbook():
    rk_int = lambda v: ((v << 2) | 2) & 0xFFFFFFFF
    rk_cents = lambda v: (v << 2) | 3
    sheet = (rec(0x0809, b"\0" * 16)
             + rec(0x00FD, struct.pack("<HHHI", 0, 0, 0, 0))                 # A1: shared string 0, split
             + rec(0x00FD, struct.pack("<HHHI", 0, 1, 0, 1))
             + rec(0x0203, struct.pack("<HHHd", 1, 0, 0, 52.33))
             + rec(0x027E, struct.pack("<HHHI", 1, 1, 0, rk_int(-7)))
             + rec(0x00BD, struct.pack("<HHHIHIH", 2, 0, 0, rk_int(80), 0, rk_cents(1234), 1))
             + rec(0x0204, struct.pack("<HHHHB", 3, 2, 0, 4, 0) + b"Norf")
             + rec(0x0006, struct.pack("<HHH", 4, 0, 0) + struct.pack("<d", 2.5) + b"\0" * 6)
             + rec(0x0006, struct.pack("<HHH", 4, 1, 0) + b"\0\0\0\0\0\0\xff\xff" + b"\0" * 6)
             + rec(0x0207, struct.pack("<HB", 2, 0) + b"ok")
             + rec(0x0205, struct.pack("<HHHBB", 5, 0, 0, 7, 1))                # #DIV/0!: left empty
             + rec(0x000A, b""))
    first = struct.pack("<HB", 13, 0) + b"Abbots "                             # 13 chars, 7 here...
    rest = b"\x01" + "Ripto".encode("utf-16-le") + "n".encode("utf-16-le")    # ...6 in UTF-16 after CONTINUE
    second = struct.pack("<HB", 5, 0x08) + struct.pack("<H", 1) + b"St An" + b"\0" * 4   # a rich run
    bound = lambda pos: rec(0x0085, struct.pack("<IBB", pos, 0, 0) + struct.pack("<BB", 6, 0) + b"Survey")
    head = rec(0x0809, b"\0" * 16) + bound(0)
    globals_ = rec(0x00FC, struct.pack("<II", 2, 2) + first) + rec(0x003C, rest + second) + rec(0x000A, b"")
    pos = len(head) + len(globals_)
    return rec(0x0809, b"\0" * 16) + bound(pos) + globals_ + sheet


class XlsRead(unittest.TestCase):
    def test_cells(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "t.xls"
            p.write_bytes(compound(workbook()))
            rows = xls_read.sheets(p)["Survey"]
        self.assertEqual(rows[0], ["Abbots Ripton", "St An"])
        self.assertEqual(rows[1], [52.33, -7.0])
        self.assertEqual(rows[2], [80.0, 12.34])
        self.assertEqual(rows[3], ["", "", "Norf"])
        self.assertEqual(rows[4], [2.5, "ok"])
        self.assertEqual(rows[5:], [])

    def test_not_compound(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "t.xls"
            p.write_bytes(b"PK\3\4 not an xls")
            with self.assertRaises(ValueError):
                xls_read.sheets(p)

    def test_excel_date(self):
        self.assertEqual(str(xls_read.excel_date(38311)), "2004-11-20")


class SurveyMatch(unittest.TestCase):
    def test_saint_or_village_decides(self):
        r = {"village": "Acle", "dedication": "St Edmund", "lat": 52.6370, "lon": 1.5470}
        recs = [{"name": "Church of St Edmund", "dedication": "Edmund the Martyr", "lat": 52.6375, "lon": 1.5475},
                {"name": "Methodist chapel", "dedication": "", "lat": 52.6372, "lon": 1.5468}]
        self.assertIs(church_survey.match([r], recs)[0][1], recs[0])
        # a lone church nearby of another saint and place is not taken (a grid reference slip)
        self.assertEqual(church_survey.match([r], recs[1:]), [])
        far = dict(recs[0], lat=52.66)
        self.assertEqual(church_survey.match([r], [far]), [])

    def test_axis_difference(self):
        self.assertEqual(church_survey._diff(91, 89), 2)
        self.assertEqual(church_survey._diff(179, 1), -2)


if __name__ == "__main__":
    unittest.main()
