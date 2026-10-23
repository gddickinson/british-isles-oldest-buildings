"""Read single members of a large remote zip with HTTP range requests, so a 5 GB archive (HYDE) need not be
downloaded whole. Deflate members are inflated here; Deflate64 ones are re-wrapped as a one-member zip and
unpacked with Info-ZIP `unzip` (macOS's supports it).

    members(url) -> {name: info}       extract(url, info, dest) -> dest (the member's bytes on disk)
"""
import struct
import subprocess
import zlib
from pathlib import Path

import requests

from .config import USER_AGENT


def _get(url, start, end):
    r = requests.get(url, headers={"Range": f"bytes={start}-{end}", "User-Agent": USER_AGENT}, timeout=600)
    r.raise_for_status()
    return r.content


def _size(url):
    r = requests.get(url, headers={"Range": "bytes=0-0", "User-Agent": USER_AGENT}, timeout=60)
    r.raise_for_status()
    return r.url, int(r.headers["Content-Range"].split("/")[1])


def members(url):
    """The archive's central directory: {name: {off, csize, usize, meth, crc, url}} (zip64 aware)."""
    url, size = _size(url)
    tail = _get(url, max(0, size - 70000), size - 1)
    i = tail.rfind(b"PK\x05\x06")
    cd_size, cd_off = struct.unpack("<II", tail[i + 12:i + 20])
    j = tail.rfind(b"PK\x06\x07")
    if j >= 0:
        eocd64 = struct.unpack("<Q", tail[j + 8:j + 16])[0]
        cd_size, cd_off = struct.unpack("<QQ", _get(url, eocd64, eocd64 + 55)[40:56])
    cd, p, out = _get(url, cd_off, cd_off + cd_size - 1), 0, {}
    while cd[p:p + 4] == b"PK\x01\x02":
        meth = struct.unpack("<H", cd[p + 10:p + 12])[0]
        crc, csize, usize = struct.unpack("<III", cd[p + 16:p + 28])
        nl, el, cl = struct.unpack("<HHH", cd[p + 28:p + 34])
        off = struct.unpack("<I", cd[p + 42:p + 46])[0]
        name = cd[p + 46:p + 46 + nl].decode("utf-8", "replace")
        extra, q = cd[p + 46 + nl:p + 46 + nl + el], 0
        while q < len(extra):                       # zip64 sizes and offset
            hid, hl = struct.unpack("<HH", extra[q:q + 4])
            if hid == 1:
                vals, k = list(struct.unpack("<" + "Q" * (hl // 8), extra[q + 4:q + 4 + hl])), 0
                if usize == 0xFFFFFFFF:
                    usize, k = vals[k], k + 1
                if csize == 0xFFFFFFFF:
                    csize, k = vals[k], k + 1
                if off == 0xFFFFFFFF:
                    off = vals[k]
            q += 4 + hl
        out[name] = {"off": off, "csize": csize, "usize": usize, "meth": meth, "crc": crc, "url": url}
        p += 46 + nl + el + cl
    return out


def extract(m, dest):
    """Write member `m` (from `members`) to `dest`."""
    dest = Path(dest)
    head = _get(m["url"], m["off"], m["off"] + 29)
    nl, el = struct.unpack("<HH", head[26:30])
    start = m["off"] + 30 + nl + el
    data = _get(m["url"], start, start + m["csize"] - 1)
    if m["meth"] == 8:
        dest.write_bytes(zlib.decompressobj(-15).decompress(data))
    elif m["meth"] == 0:
        dest.write_bytes(data)
    else:                                           # Deflate64 (9) and others: let unzip do it
        name = dest.name.encode()
        lh = struct.pack("<IHHHHHIIIHH", 0x04034B50, 21, 0, m["meth"], 0, 0, m["crc"], m["csize"], m["usize"],
                         len(name), 0) + name
        ch = struct.pack("<IHHHHHHIIIHHHHHII", 0x02014B50, 21, 21, 0, m["meth"], 0, 0, m["crc"], m["csize"],
                         m["usize"], len(name), 0, 0, 0, 0, 0, 0) + name
        end = struct.pack("<IHHHHIIH", 0x06054B50, 0, 0, 1, 1, len(ch), len(lh) + len(data), 0)
        tmp = dest.with_suffix(".tmp.zip")
        tmp.write_bytes(lh + data + ch + end)
        try:
            subprocess.run(["unzip", "-o", "-q", str(tmp), "-d", str(dest.parent)], check=True)
        finally:
            tmp.unlink(missing_ok=True)
    return dest
