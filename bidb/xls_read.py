"""Cell values of an old Excel .xls workbook (BIFF8 inside an OLE2 compound file), stdlib only.

Enough for spreadsheets of values: shared strings (SST, across CONTINUE records), LABELSST, LABEL, NUMBER, RK,
MULRK and cached FORMULA results (numbers and strings); formats, dates and styles are not read (a date is its
serial number: `excel_date`). `sheets(path)` gives {sheet name: rows as lists}; read by bidb.church_survey.
"""
import datetime
import struct
from pathlib import Path

FREE, END = 0xFFFFFFFF, 0xFFFFFFFE


def _stream(data, name="Workbook"):
    """The named stream of a compound file (regular sectors; a workbook is never in the mini stream)."""
    if data[:8] != b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1":
        raise ValueError("not an OLE2 compound file")
    size = 1 << struct.unpack_from("<H", data, 30)[0]
    n_fat, dir_start = struct.unpack_from("<I", data, 44)[0], struct.unpack_from("<I", data, 48)[0]
    difat_start, n_difat = struct.unpack_from("<II", data, 68)
    sector = lambda i: data[512 + i * size: 512 + (i + 1) * size]
    difat = list(struct.unpack_from("<109I", data, 76))
    while n_difat and difat_start not in (FREE, END):
        s = sector(difat_start)
        difat += struct.unpack_from("<%dI" % (size // 4 - 1), s)
        difat_start, n_difat = struct.unpack_from("<I", s, size - 4)[0], n_difat - 1
    fat = []
    for i in difat[:n_fat]:
        fat += struct.unpack("<%dI" % (size // 4), sector(i))

    def chain(start):
        out, i, seen = [], start, set()
        while i not in (FREE, END) and i < len(fat) and i not in seen:
            seen.add(i)
            out.append(sector(i))
            i = fat[i]
        return b"".join(out)
    directory = chain(dir_start)
    for off in range(0, len(directory), 128):
        n = struct.unpack_from("<H", directory, off + 64)[0]
        if directory[off: off + max(n - 2, 0)].decode("utf-16-le") in (name, "Book"):
            start, length = struct.unpack_from("<II", directory, off + 116)
            return chain(start)[:length]
    raise ValueError("no workbook stream")


def _records(wb):
    pos = 0
    while pos + 4 <= len(wb):
        rid, n = struct.unpack_from("<HH", wb, pos)
        yield pos, rid, wb[pos + 4: pos + 4 + n]
        pos += 4 + n


class _Segments:
    """Bytes of a record and its CONTINUE records; strings split across them restart with a flags byte."""
    def __init__(self, parts):
        self.parts, self.i, self.pos = parts, 0, 0

    def _next(self):
        if self.pos >= len(self.parts[self.i]):
            self.i, self.pos = self.i + 1, 0

    def read(self, n):
        out = b""
        while n:
            self._next()
            part = self.parts[self.i]
            take = part[self.pos: self.pos + n]
            out, self.pos, n = out + take, self.pos + len(take), n - len(take)
        return out

    def chars(self, cch, high):
        out = []
        while cch:
            if self.pos >= len(self.parts[self.i]):
                self._next()
                high = self.read(1)[0] & 1
            avail = (len(self.parts[self.i]) - self.pos) // (2 if high else 1)
            take = min(cch, avail)
            raw = self.read(take * (2 if high else 1))
            out.append(raw.decode("utf-16-le" if high else "latin-1"))
            cch -= take
        return "".join(out)


def _string(seg):
    cch, flags = struct.unpack("<HB", seg.read(3))
    runs = struct.unpack("<H", seg.read(2))[0] if flags & 8 else 0
    ext = struct.unpack("<I", seg.read(4))[0] if flags & 4 else 0
    text = seg.chars(cch, flags & 1)
    seg.read(4 * runs + ext)
    return text


def _rk(v):
    num = (v >> 2) - (1 << 30 if v & 0x80000000 else 0) if v & 2 else \
        struct.unpack("<d", struct.pack("<Q", (v & 0xFFFFFFFC) << 32))[0]
    return num / 100 if v & 1 else float(num)


def sheets(path):
    """{sheet name: rows}, each row a list of cell values (str or float; "" where empty)."""
    wb = _stream(Path(path).read_bytes())
    recs = list(_records(wb))
    bound, sst = [], []
    for k, (pos, rid, body) in enumerate(recs):
        if rid == 0x0085:
            cch, flags = body[6], body[7]
            name = body[8: 8 + cch * 2].decode("utf-16-le") if flags & 1 else body[8: 8 + cch].decode("latin-1")
            bound.append((struct.unpack_from("<I", body)[0], body[5], name))
        elif rid == 0x00FC:
            parts = [body[8:]]
            for _, r2, b2 in recs[k + 1:]:
                if r2 != 0x003C:
                    break
                parts.append(b2)
            seg = _Segments(parts)
            sst = [_string(seg) for _ in range(struct.unpack_from("<I", body, 4)[0])]
    by_pos = {pos: k for k, (pos, _, _) in enumerate(recs)}
    out = {}
    for start, kind, name in bound:
        if kind != 0:                     # worksheets only (not charts or macros)
            continue
        cells, pending = {}, None
        for _, rid, body in recs[by_pos[start] + 1:]:
            if rid == 0x000A:
                break
            if rid == 0x00FD:
                r, c, _, i = struct.unpack_from("<HHHI", body)
                cells[r, c] = sst[i]
            elif rid == 0x0203:
                r, c, _, v = struct.unpack_from("<HHHd", body)
                cells[r, c] = v
            elif rid == 0x027E:
                r, c, _, v = struct.unpack_from("<HHHI", body)
                cells[r, c] = _rk(v)
            elif rid == 0x00BD:
                r, c = struct.unpack_from("<HH", body)
                for j in range((len(body) - 6) // 6):
                    cells[r, c + j] = _rk(struct.unpack_from("<I", body, 6 + 6 * j)[0])
            elif rid == 0x0204:
                r, c = struct.unpack_from("<HH", body)
                cells[r, c] = _string(_Segments([body[6:]]))
            elif rid == 0x0006:
                r, c = struct.unpack_from("<HH", body)
                if body[12:14] == b"\xff\xff":
                    pending = (r, c) if body[6] == 0 else None       # a string result follows in STRING
                else:
                    cells[r, c] = struct.unpack_from("<d", body, 6)[0]
            elif rid == 0x0207 and pending:
                cells[pending] = _string(_Segments([body]))
                pending = None
        rows = []
        for (r, c), v in cells.items():
            while len(rows) <= r:
                rows.append([])
            row = rows[r]
            row.extend([""] * (c + 1 - len(row)))
            row[c] = v
        out[name] = rows
    return out


def excel_date(serial):
    """A 1900-system serial day number as a date."""
    return datetime.date(1899, 12, 30) + datetime.timedelta(days=int(serial))
