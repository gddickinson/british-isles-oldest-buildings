"""Build stage / CLI: hoards from Wikipedia's lists -> places "Finds & treasures" (run after the museum stages).

    python -m bidb.hoards            parse (cached) and add
    python -m bidb.hoards --report   counts

"List of hoards in Great Britain" and "List of hoards in Ireland" (CC BY-SA): each row gives the
hoard, its date, the place of discovery with coordinates, the year it was found, where it is now
and what it contains; the section says the period. Hoards already among the places (Wikidata
finds with the same article) are left as they are; the rest become places of kind "hoard",
linked to the museum that holds them (bidb.museums.link_finds). The Portable Antiquities Scheme's
database would add Treasure cases but cannot be read by a script (bot check, 2026-10-21).
"""
import argparse
import json
import re
import time
from urllib.parse import quote

from . import place_stage
from .config import WIKIPEDIA_API
from .dates import parse_text_year
from .db import connect
from .http import request_json
from .place_records import blank
from .wikipedia_list import _LINK, _cells, _strip_wikitext

PAGES = ["List of hoards in Great Britain", "List of hoards in Ireland"]
KINDS = ("hoard",)
GROUP = "Finds & treasures"
_COORD = re.compile(r"\{\{\s*coord\s*\|([^}]*)\}\}", re.I)


def coord(text):
    """(lat, lon) from the first {{coord}} in text: decimal ({{coord|51.5|-0.1}}) or degrees, minutes and
    seconds with hemispheres ({{coord|51|30|N|0|7|W}}, {{coord|51|30|15|N|0|7|5|W}}); None when there is none."""
    m = _COORD.search(text or "")
    if not m:
        return None
    parts = [p.strip() for p in m.group(1).split("|")]
    hemi = [i for i, p in enumerate(parts) if p.upper() in ("N", "S", "E", "W")]

    def num(p):
        return float(p) if re.fullmatch(r"-?\d+(\.\d+)?", p) else None
    try:
        if len(hemi) >= 2:
            i, j = hemi[:2]
            lat = sum(num(p) / 60 ** k for k, p in enumerate(parts[:i]))
            lon = sum(num(p) / 60 ** k for k, p in enumerate(parts[i + 1:j]))
            return (-lat if parts[i].upper() == "S" else lat, -lon if parts[j].upper() == "W" else lon)
        lat, lon = num(parts[0]), num(parts[1])
    except (TypeError, IndexError):
        return None
    return (lat, lon) if lat is not None and lon is not None else None


def wikitext(title):
    res = request_json(WIKIPEDIA_API, params={"action": "parse", "page": title, "prop": "wikitext",
                                              "format": "json", "formatversion": 2, "redirects": 1})
    return res.get("parse", {}).get("wikitext", "")


def _slug(s):
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")


def parse(text, page):
    """[{name, title, period, date, lat, lon, place, found, now_in, contents}] from one list page."""
    out = []
    for section in re.split(r"\n==(?!=)", "\n" + text):
        heading = section.split("==", 1)[0].strip() if "==" in section.split("\n", 1)[0] else ""
        period = re.sub(r"\s*hoards?$", "", heading, flags=re.I)
        for table in re.findall(r"\{\|.*?\n\|\}", section, flags=re.S):
            for row in table.split("\n|-")[1:]:
                cells = _cells(row)
                if len(cells) < 7 or cells[0].startswith("!"):
                    continue
                name_cell, _, date, place, found, where, contents = cells[:7]
                where_ll = coord(place)
                if not where_ll:
                    continue
                link = _LINK.search(name_cell)
                name = _strip_wikitext(name_cell)
                now = [m.group(2) or m.group(1) for m in _LINK.finditer(where)][:1] or (
                    [_strip_wikitext(where).split(",")[0]] if _strip_wikitext(where) else [])
                out.append({"name": name, "title": link.group(1).strip() if link else None, "period": period,
                            "date": _strip_wikitext(date) or None, "lat": where_ll[0], "lon": where_ll[1],
                            "place": re.sub(r"(,\s*)+", ", ", _strip_wikitext(re.sub(r"<br\s*/?>", ", ", re.sub(
                                r"<small>.*?</small>", "", place, flags=re.S))).replace("\n", ", ")).strip(", ") or None,
                            "found": _strip_wikitext(found) or None, "now_in": now,
                            "contents": re.sub(r"\s+", " ", _strip_wikitext(contents.replace("<br", "; <br")))[:500] or None,
                            "page": page})
    return out


def build(log=print):
    rows = [h for page in PAGES for h in parse(wikitext(page), page)]
    recs = {}
    for h in rows:
        pid = "hoard-" + _slug(h["name"])
        extra = {"found_at": [h["place"]] if h["place"] else [], "now_in": h["now_in"]}
        if h["found"]:
            extra["found"] = h["found"]
        recs.setdefault(pid, blank(
            pid, "hoard", h["name"], type=f"{h['period']} hoard" if h["period"] else "Hoard", lat=h["lat"], lon=h["lon"],
            description=h["contents"], date_text=h["date"], year_start=parse_text_year(h["date"] or ""),
            locality=h["place"], wikipedia_title=h["title"], source="Wikipedia",
            url="https://en.wikipedia.org/wiki/" + quote(h["page"].replace(" ", "_")),
            extra=json.dumps(extra, ensure_ascii=False)))
    log(f"  hoards: {len(rows)} rows, {len(recs)} hoards")
    return list(recs.values())


def run(log=print):
    from .museums import link_finds
    t0 = time.time()
    conn = connect()
    conn.execute("PRAGMA busy_timeout = 120000")
    recs = build(log)
    conn.execute("DELETE FROM places_fts WHERE id IN (SELECT id FROM places WHERE kind = 'hoard')")
    conn.execute("DELETE FROM places WHERE kind = 'hoard'")
    have = {t for (t,) in conn.execute("SELECT wikipedia_title FROM places WHERE wikipedia_title IS NOT NULL")}
    have |= {t for (t,) in conn.execute("SELECT wikipedia_title FROM buildings WHERE wikipedia_title IS NOT NULL")}
    new = [r for r in recs if not r["wikipedia_title"] or r["wikipedia_title"] not in have]
    from .enrich import wikipedia_intros
    intros = wikipedia_intros([r["wikipedia_title"] for r in new if r.get("wikipedia_title")])
    for r in new:
        got = intros.get(r.get("wikipedia_title") or "") or {}
        r["wikipedia_extract"] = (got.get("extract") or "")[:900] or None
        r["image_thumb"] = got.get("image")
    place_stage.insert(conn, new)
    linked = link_finds(conn)
    conn.commit()
    log(f"[{time.time() - t0:5.0f}s] hoards: {len(new)} new, {len(recs) - len(new)} already among the places; "
        f"{linked} finds linked to their museum")


def report(log=print):
    log(json.dumps(dict(connect().execute("SELECT type, COUNT(*) FROM places WHERE kind = 'hoard' GROUP BY 1")
                        .fetchall()), indent=1))


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--report", action="store_true")
    a = ap.parse_args()
    report() if a.report else run()


if __name__ == "__main__":
    main()
