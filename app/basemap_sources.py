"""Download and cache the open data behind the offline map (data/cache/basemap/, not in git).

Natural Earth 10m (public domain) and GeoNames (CC BY 4.0) are the only sources.
"""
import csv
import io
import json
import zipfile

import requests

from bidb import progress, refresh
from bidb.config import CACHE_DIR, USER_AGENT

CACHE = CACHE_DIR / "basemap"
NE = "https://raw.githubusercontent.com/nvkelso/natural-earth-vector/v5.1.2/geojson/{}.geojson"
GEONAMES = "https://download.geonames.org/export/dump/{}.zip"
COUNTRY_CODES = ["GB", "IE", "IM", "JE", "GG"]
ADM0 = {"GBR", "IRL", "IMN", "JEY", "GGY"}
BOX = (-11.0, 49.0, 2.2, 61.2)            # west, south, east, north


def _get(url, name):
    CACHE.mkdir(parents=True, exist_ok=True)
    path = CACHE / name
    if not path.exists() or refresh.stale(path, url):
        r = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=300)
        r.raise_for_status()
        path.write_bytes(r.content)
    return path


def natural_earth(name):
    """Features of a Natural Earth 10m layer that touch the British Isles box."""
    data = json.loads(_get(NE.format(name), name + ".geojson").read_text())
    return [f for f in data["features"] if f.get("geometry") and _touches_box(f["geometry"])]


def _touches_box(geom):
    w, s, e, n = BOX
    stack = [geom["coordinates"]]
    while stack:
        c = stack.pop()
        if c and isinstance(c[0], (int, float)):
            if w <= c[0] <= e and s <= c[1] <= n:
                return True
        else:
            stack.extend(c)
    return False


GEONAMES_FIELDS = ["geonameid", "name", "asciiname", "alternatenames", "lat", "lon", "fclass",
                   "fcode", "country", "cc2", "admin1", "admin2", "admin3", "admin4",
                   "population", "elevation", "dem", "timezone", "modified"]


def geonames(code):
    """Rows of a GeoNames country dump (all feature classes)."""
    z = zipfile.ZipFile(_get(GEONAMES.format(code), f"geonames_{code}.zip"))
    text = z.read(f"{code}.txt").decode("utf-8")
    reader = csv.reader(io.StringIO(text), delimiter="\t", quoting=csv.QUOTE_NONE)
    return [dict(zip(GEONAMES_FIELDS, row)) for row in reader]


OVERPASS = "https://overpass-api.de/api/interpreter"


def overpass(query, name, pause=5):
    """Cached Overpass API result (OpenStreetMap, ODbL). Waits `pause` s before a live request."""
    import time
    CACHE.mkdir(parents=True, exist_ok=True)
    path = CACHE / f"osm_{name}.json"
    if path.exists() and not refresh.stale(path, OVERPASS):
        progress.count(from_cache=True)
        return json.loads(path.read_text())
    progress.count(from_cache=False)
    for attempt in range(4):
        time.sleep(pause * (attempt + 1))
        try:
            r = requests.post(OVERPASS, data={"data": query}, headers={"User-Agent": USER_AGENT},
                              timeout=400)
        except (requests.Timeout, requests.ConnectionError):
            continue                                     # busy server: wait longer and try again
        if r.status_code in (429, 502, 503, 504):
            continue
        r.raise_for_status()
        path.write_text(r.text)
        return r.json()
    raise RuntimeError(f"Overpass failed for {name}")


def osm_rivers(step=2.0):
    """Named rivers (waterway=river) in 2-degree tiles over the British Isles -> list of ways.
    Tiles that are entirely sea are skipped."""
    from bidb.land import near_land
    w, s, e, n = BOX
    ways = {}
    lat = s
    while lat < n:
        lon = w
        while lon < e:
            probe = [(lat + step * i / 4, lon + step * j / 4) for i in range(5) for j in range(5)]
            if not any(near_land(y, x, 10) for y, x in probe):
                lon += step
                continue
            q = (f"[out:json][timeout:180];way[waterway=river][name]({lat},{lon},{lat + step},{lon + step});"
                 "out geom;")
            for el in overpass(q, f"rivers{step:g}_{lat:g}_{lon:g}").get("elements", []):
                ways[el["id"]] = el
            lon += step
        lat += step
    return list(ways.values())


def osm_canals():
    """Named canals (waterway=canal) over the British Isles -> list of ways."""
    q = "[out:json][timeout:300];way[waterway=canal][name](49,-11,61.2,2.2);out geom;"
    return overpass(q, "canals").get("elements", [])


def osm_trails():
    """National walking routes (route=hiking, network=nwn): National Trails, Scotland's Great
    Trails, Irish National Waymarked Ways (relations with way geometry)."""
    q = "[out:json][timeout:300];relation[route=hiking][network=nwn](49,-11,61.2,2.2);out geom;"
    return overpass(q, "trails").get("elements", [])


HISTORIC_COUNTIES = "https://county-borders.co.uk/UKDefinitionA_WG84_Simplified.kmz"


def historic_counties():
    """Pre-1974 counties of Great Britain (Historic County Borders Project; free for any use with
    acknowledgement) -> [(name, [rings of [lon, lat]])] from the simplified KMZ."""
    import re as _re
    import xml.etree.ElementTree as ET
    z = zipfile.ZipFile(_get(HISTORIC_COUNTIES, "historic_counties_A.kmz"))
    root = ET.fromstring(z.read([n for n in z.namelist() if n.endswith(".kml")][0]))
    ns = {"k": "http://www.opengis.net/kml/2.2"}
    out = []
    for pm in root.iter("{http://www.opengis.net/kml/2.2}Placemark"):
        name = (pm.findtext("k:name", default="", namespaces=ns) or "").strip()
        if not name:
            for d in pm.iter("{http://www.opengis.net/kml/2.2}SimpleData"):
                if d.get("name", "").lower() in ("name", "county"):
                    name = (d.text or "").strip()
        rings = []
        for c in pm.iter("{http://www.opengis.net/kml/2.2}coordinates"):
            pts = [[float(v) for v in p.split(",")[:2]] for p in _re.split(r"\s+", (c.text or "").strip()) if p]
            if len(pts) > 3:
                rings.append(pts)
        if rings:
            out.append((name, rings))
    return out


def osm_stations():
    """Railway stations (incl. heritage lines) and bus stations with a name -> list of elements."""
    q = ('[out:json][timeout:300];(node[railway=station][name](49,-11,61.2,2.2);'
         'node[amenity=bus_station][name](49,-11,61.2,2.2);way[amenity=bus_station][name](49,-11,61.2,2.2););'
         'out center tags;')
    return overpass(q, "stations").get("elements", [])


def osm_parks():
    """National parks and Areas of Outstanding Natural Beauty / National Scenic Areas (relations)."""
    # designation=* catches parks named only in Welsh/Gaelic (Eryri, Llŷn) or without the
    # usual words (The Broads, Northern Ireland's "... AONB")
    q = ('[out:json][timeout:300];('
         'relation[boundary=national_park](49,-11,61.2,2.2);'
         'relation[boundary=protected_area][name~"National Park|Area of Outstanding Natural Beauty|'
         'National Landscape|National Scenic Area"](49,-11,61.2,2.2);'
         'relation[designation~"^(national_park|area_of_outstanding_natural_beauty|national_scenic_area)$"]'
         '(49,-11,61.2,2.2););out geom;')
    return overpass(q, "parks_designation").get("elements", [])
