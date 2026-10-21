"""Commemorative plaques from Open Plaques (openplaques.org; data released into the public domain).

The bulk API answers bounding-box queries with id, position and inscription only; boxes that
hit the result limit are split in four. Plaques get the first line of their inscription as
a name ("Frank Budgen") and link to the plaque's Open Plaques page.
"""
import re

from .http import request_json
from .place_records import blank

API = "https://openplaques.org/plaques.json"
PAGE = "https://openplaques.org/plaques/{}"
LIMIT = 20000
BOX = (49.0, -11.0, 61.2, 2.2)        # south, west, north, east
GENERIC_START = re.compile(r"^(here|on this site|near this|in this|this (?:house|building|plaque|site)|"
                           r"in (?:a|the) house|at this|site of|from this)\b", re.I)


def _box(s, w, n, e, log, depth=0):
    rows = request_json(API, params={"box": f"[{n},{w}],[{s},{e}]", "limit": LIMIT}, min_interval=1.0)
    if len(rows) < LIMIT or depth > 4:
        return rows
    ms, mw = (s + n) / 2, (w + e) / 2
    log(f"  open plaques: splitting box {s},{w},{n},{e}")
    return [r for sub in ((s, w, ms, mw), (s, mw, ms, e), (ms, w, n, mw), (ms, mw, n, e))
            for r in _box(*sub, log, depth + 1)]


LIFESPAN = re.compile(r"^(.{3,60}?\(?\s*(?:c\.\s*)?\d{4}\s*[-–]\s*(?:c\.\s*)?\d{2,4}\s*\)?)")


def name_for(inscription):
    """'James Hudson Taylor (1832- 1905) Founder of ...' -> 'Plaque: James Hudson Taylor (1832- 1905)'."""
    text = re.sub(r"\s+", " ", inscription or "").strip(" ,.;:")
    if not text:
        return "Commemorative plaque"
    m = LIFESPAN.match(text)
    if m and not GENERIC_START.match(text):
        head = m.group(1)
    else:
        first = re.split(r"(?<=[a-z)])\.\s|\n", (inscription or "").strip(), maxsplit=1)[0]
        first = re.sub(r"\s+", " ", first).strip(" ,.;:")
        weak = len(first) < 6 or re.search(r"\b(of|to|the|in|by|and)$", first, re.I)
        head = text if weak or GENERIC_START.match(first) and len(first) < 25 else first
    head = head.strip()
    return "Plaque: " + (head if len(head) <= 70 else head[:67].rsplit(" ", 1)[0] + "…")


def plaques(log=print):
    """Place records for every Open Plaques plaque in the British Isles box."""
    s, w, n, e = BOX
    seen, out = set(), []
    step = 4.0
    lat = s
    while lat < n:
        lon = w
        while lon < e:
            for r in _box(lat, lon, min(lat + step, n), min(lon + step, e), log):
                if r["id"] in seen or r.get("latitude") is None:
                    continue
                seen.add(r["id"])
                text = (r.get("inscription") or "").strip()
                out.append(blank(f"OP{r['id']}", "plaque", name_for(text),
                                 description=text[:600] or None, lat=r["latitude"], lon=r["longitude"],
                                 url=PAGE.format(r["id"]), source="Open Plaques"))
            lon += step
        lat += step
    log(f"open plaques: {len(out)} plaques")
    return out
