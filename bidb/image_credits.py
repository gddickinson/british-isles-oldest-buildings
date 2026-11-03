"""Build stage / CLI: author and licence of every Commons photo shown -> table `image_credits`.

    python -m bidb.image_credits             fetch (cached) and write the table
    python -m bidb.image_credits --report    counts by licence

Commons files are under their own licences (mostly CC BY / CC BY-SA), which ask for the author and the
licence to be named where the file is shown. The imageinfo API's extmetadata (Artist, LicenseShortName,
LicenseUrl) is read for every file in `buildings.image_page` and `places.image_page`, 50 titles per request
(cached in <cache>), and `credit` gives the caption text used by the detail views and the hosted copy.
Run again after the photo jobs (bidb.images_extra, bidb.photo_search) add photos.
"""
import html
import re
import sys
import time
from urllib.parse import unquote

from .db import connect
from .http import request_json

API = "https://commons.wikimedia.org/w/api.php"
BATCH = 50
PREFIX = "https://commons.wikimedia.org/wiki/File:"


def title(page):
    """'File:Buildwas Abbey 2.jpg' from a Commons file page URL, or None."""
    if not page or not page.startswith(PREFIX):
        return None
    return "File:" + unquote(page[len(PREFIX):]).replace("_", " ")


def plain(value, limit=120):
    """Text of an extmetadata HTML value: tags removed, entities read, spaces collapsed, shortened."""
    text = re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", value or ""))).strip()
    return text if len(text) <= limit else text[:limit - 1].rstrip() + "…"


def fetch(titles, log=print):
    """{title as asked: (artist, licence, licence URL)} for the files Commons knows."""
    out, titles = {}, sorted(set(titles))
    for i in range(0, len(titles), BATCH):
        part = titles[i:i + BATCH]
        data = request_json(API, data={
            "action": "query", "titles": "|".join(part), "prop": "imageinfo", "iiprop": "extmetadata",
            "iiextmetadatafilter": "Artist|LicenseShortName|LicenseUrl", "redirects": "1",
            "format": "json", "formatversion": "2"}, method="POST", min_interval=1.0)
        q = data.get("query", {})
        back = {}                                   # Commons' title -> the title asked for
        for kind in ("normalized", "redirects"):
            for m in q.get(kind, []):
                back[m["to"]] = back.get(m["from"], m["from"])
        for page in q.get("pages", []):
            info = (page.get("imageinfo") or [{}])[0].get("extmetadata", {})
            if info:
                asked = back.get(page["title"], page["title"])
                out[asked] = (plain(info.get("Artist", {}).get("value")),
                              plain(info.get("LicenseShortName", {}).get("value"), 60),
                              (info.get("LicenseUrl", {}).get("value") or "").strip())
        if (i // BATCH) % 100 == 0:
            log(f"  {min(i + BATCH, len(titles)):,} of {len(titles):,} files")
    return out


def run(log=print):
    t0 = time.time()
    conn = connect()
    conn.execute("PRAGMA busy_timeout = 120000")
    pages = {p for (p,) in conn.execute("SELECT image_page FROM buildings WHERE image_page IS NOT NULL "
                                        "UNION SELECT image_page FROM places WHERE image_page IS NOT NULL")}
    titles = {p: title(p) for p in pages if title(p)}
    found = fetch(titles.values(), log)
    rows = [(p, *found[t]) for p, t in titles.items() if t in found]
    conn.execute("DROP TABLE IF EXISTS image_credits")
    conn.execute("CREATE TABLE image_credits (page TEXT PRIMARY KEY, artist TEXT, licence TEXT, licence_url TEXT)")
    conn.executemany("INSERT INTO image_credits VALUES (?, ?, ?, ?)", rows)
    conn.commit()
    log(f"image credits: {len(rows):,} of {len(titles):,} files ({time.time() - t0:.0f} s)")
    return len(rows)


def credit(conn, page):
    """'Author · CC BY-SA 4.0' for a file page, or None (no table yet, or Commons gave nothing)."""
    if not page or not conn.execute("SELECT 1 FROM sqlite_master WHERE name = 'image_credits'").fetchone():
        return None
    row = conn.execute("SELECT artist, licence FROM image_credits WHERE page = ?", (page,)).fetchone()
    return (" · ".join(x for x in row if x) or None) if row else None


def credits(conn):
    """{file page: credit} for every file (the static export)."""
    if not conn.execute("SELECT 1 FROM sqlite_master WHERE name = 'image_credits'").fetchone():
        return {}
    return {p: " · ".join(x for x in (a, l) if x) for p, a, l in conn.execute(
        "SELECT page, artist, licence FROM image_credits") if a or l}


def report():
    conn = connect(readonly=True)
    for lic, n in conn.execute("SELECT licence, COUNT(*) FROM image_credits GROUP BY licence ORDER BY 2 DESC LIMIT 20"):
        print(f"{n:7,}  {lic}")
    none = conn.execute("SELECT COUNT(*) FROM image_credits WHERE COALESCE(artist, '') = ''").fetchone()[0]
    print(f"{none:,} files with no author given")


if __name__ == "__main__":
    report() if "--report" in sys.argv[1:] else run()
