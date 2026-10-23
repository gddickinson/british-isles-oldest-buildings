"""Build stage / CLI: bus stops and ferry terminals from NaPTAN (Department for Transport, OGL) -> table `stops`.

    python -m bidb.naptan            download (cached) and write the table
    python -m bidb.naptan --report   counts

NaPTAN lists every public transport access point in Great Britain (~436,000, most of them bus stops). The table
keeps the active bus stops (BCT) and ferry terminals (FTD, FER, FBT; one per name within 300 m). `near` gives a
record's nearest bus stops and ferry terminal for "Getting there" (rail stations come from the map's own
stations layer). Northern Ireland, Ireland and the Crown Dependencies are not in NaPTAN.
"""
import csv
import math
import sys
import time

import requests

from .config import USER_AGENT, cache_dir

URL = "https://naptan.api.dft.gov.uk/v1/access-nodes?dataFormat=csv"
BUS, FERRY = ("BCT",), ("FTD", "FER", "FBT")
ATTRIBUTION = "Contains NaPTAN data, Department for Transport, licensed under the Open Government Licence v3.0."
SCHEMA = """CREATE TABLE stops (atco TEXT PRIMARY KEY, name TEXT, locality TEXT, kind TEXT, lat REAL, lon REAL);
            CREATE INDEX stops_lat ON stops (lat)"""


def download(log=print):
    from . import refresh
    path = cache_dir() / "naptan" / "Stops.csv"
    if not path.exists() or refresh.stale(path, URL):
        path.parent.mkdir(parents=True, exist_ok=True)
        log("  downloading NaPTAN (~100 MB)")
        r = requests.get(URL, headers={"User-Agent": USER_AGENT}, timeout=600)
        r.raise_for_status()
        tmp = path.with_suffix(".tmp")
        tmp.write_bytes(r.content)
        tmp.replace(path)
    return path


def rows(path):
    """(atco, name, locality, kind, lat, lon) for active bus stops and ferry terminals."""
    ferries = []
    with open(path, newline="", encoding="utf-8-sig") as f:
        for r in csv.DictReader(f):
            kind = "bus" if r["StopType"] in BUS else "ferry" if r["StopType"] in FERRY else None
            if not kind or (r.get("Status") or "active").lower() not in ("active", "act"):
                continue
            try:
                lat, lon = float(r["Latitude"]), float(r["Longitude"])
            except (TypeError, ValueError):
                continue
            row = (r["ATCOCode"], (r.get("CommonName") or "").strip(), (r.get("LocalityName") or "").strip() or None,
                   kind, round(lat, 5), round(lon, 5))
            if kind == "bus":
                yield row
            elif not any(f[1] == row[1] and km(f[4], f[5], lat, lon) < 0.3 for f in ferries):
                ferries.append(row)
                yield row


def km(lat1, lon1, lat2, lon2):
    rad = math.pi / 180
    h = (math.sin((lat2 - lat1) * rad / 2) ** 2
         + math.cos(lat1 * rad) * math.cos(lat2 * rad) * math.sin((lon2 - lon1) * rad / 2) ** 2)
    return 12742 * math.asin(math.sqrt(min(1, h)))


def near(conn, lat, lon, bus_km=1.0, ferry_km=15.0, buses=2):
    """{"bus": [{name, locality, km}], "ferry": [{name, locality, km}]} near a point (empty without the table)."""
    if lat is None or not conn.execute("SELECT 1 FROM sqlite_master WHERE name = 'stops'").fetchone():
        return {"bus": [], "ferry": []}
    out = {}
    for kind, reach, n in (("bus", bus_km, buses), ("ferry", ferry_km, 1)):
        dlat, dlon = reach / 111, reach / (111 * max(0.2, math.cos(lat * math.pi / 180)))
        found = [(km(lat, lon, la, lo), name, loc) for name, loc, la, lo in conn.execute(
            "SELECT name, locality, lat, lon FROM stops WHERE kind = ? AND lat BETWEEN ? AND ? AND lon BETWEEN ? AND ?",
            (kind, lat - dlat, lat + dlat, lon - dlon, lon + dlon))]
        seen, picked = set(), []
        for d, name, loc in sorted(found):
            if d <= reach and name not in seen:      # a stop on each side of the road shares its name
                seen.add(name)
                picked.append({"name": name, "locality": loc, "km": round(d, 3)})
        out[kind] = picked[:n]
    return out


def run(log=print):
    from .db import connect
    t0 = time.time()
    path = download(log)
    conn = connect()
    conn.execute("PRAGMA busy_timeout = 120000")
    conn.execute("DROP TABLE IF EXISTS stops")
    conn.executescript(SCHEMA)
    conn.executemany("INSERT OR REPLACE INTO stops VALUES (?, ?, ?, ?, ?, ?)", rows(path))
    conn.commit()
    log(f"[{time.time() - t0:5.0f}s] stops: " + ", ".join(
        f"{n} {k}" for k, n in conn.execute("SELECT kind, COUNT(*) FROM stops GROUP BY 1")))


def report():
    from .db import connect
    print(dict(connect().execute("SELECT kind, COUNT(*) FROM stops GROUP BY 1").fetchall()))


if __name__ == "__main__":
    report() if sys.argv[1:] == ["--report"] else run()
