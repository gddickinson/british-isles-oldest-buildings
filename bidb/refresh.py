"""Refreshing the download cache: which cached responses to fetch again.

A rebuild normally reads every earlier download from the cache. A refresh fetches some again:
  days     cached responses older than this many days
  sources  only responses from these sources (keys of SOURCES)
Both together: responses from those sources that are older than that. Set with
`python -m bidb.build --refresh-days 30 --refresh wikidata,osm` or the Data page; passed on to child
processes in the BIDB_REFRESH environment variable ("days=30;sources=wikidata,osm").
A response fetched again is written back to the cache, so an interrupted refresh resumes.
"""
import os
import time
from urllib.parse import urlparse

# source key: (label, host suffixes)
SOURCES = {
    "wikidata": ("Wikidata (items, queries)", ("wikidata.org",)),
    "wikipedia": ("Wikipedia and Wiktionary (articles, intros, pronunciations)", ("wikipedia.org", "wiktionary.org")),
    "commons": ("Wikimedia Commons (photos, floor plans)", ("commons.wikimedia.org", "upload.wikimedia.org")),
    "registers": ("Heritage registers and Open Plaques", ("arcgis.com", "hes.scot", "historicenvironment.scot",
                                                          "datamap.gov.wales", "azurewebsites.net", "archaeology.ie",
                                                          "buildingsofireland.ie", "openplaques.org")),
    "osm": ("OpenStreetMap (map layers, routes, stations, visiting)", ("overpass-api.de", "openstreetmap.de")),
    "postcodes": ("postcodes.io (addresses)", ("postcodes.io",)),
    "maps": ("Other map sources (Natural Earth, GeoNames, county borders, elevation)",
             ("githubusercontent.com", "geonames.org", "county-borders.co.uk", "opentopodata.org")),
}
_rule = {"days": None, "sources": set(), "since": time.time()}


def set_rule(days=None, sources=()):
    """Turn a refresh on for this process and its children (days=None and no sources: off)."""
    bad = set(sources) - set(SOURCES)
    if bad:
        raise ValueError(f"Unknown sources: {', '.join(sorted(bad))} (choose from {', '.join(SOURCES)})")
    _rule.update(days=days, sources=set(sources), since=time.time())
    if days is None and not sources:
        os.environ.pop("BIDB_REFRESH", None)
    else:
        os.environ["BIDB_REFRESH"] = ";".join(
            ([f"days={days}"] if days is not None else []) + ([f"sources={','.join(sorted(sources))}"] if sources else [])
            + [f"since={_rule['since']:.0f}"])


def _from_env():
    for part in os.environ.get("BIDB_REFRESH", "").split(";"):
        k, _, v = part.partition("=")
        if k == "days" and v:
            _rule["days"] = float(v)
        elif k == "sources" and v:
            _rule["sources"] = {s for s in v.split(",") if s in SOURCES}
        elif k == "since" and v:
            _rule["since"] = float(v)


def active():
    return _rule["days"] is not None or bool(_rule["sources"])


def source_of(host):
    host = host.lower()
    return next((k for k, (_, hosts) in SOURCES.items() if host.endswith(hosts)), None)


def stale(path, url_or_host, saved_at=None):
    """True when the cached file `path` (from this URL or host) should be fetched again."""
    if not active():
        return False
    host = urlparse(url_or_host).netloc if "://" in url_or_host else url_or_host
    if _rule["sources"] and source_of(host) not in _rule["sources"]:
        return False
    saved = saved_at if saved_at is not None else path.stat().st_mtime
    if _rule["days"] is None:
        return saved < _rule["since"]          # sources only: everything fetched before the refresh began
    return time.time() - saved > _rule["days"] * 86400


def describe():
    if not active():
        return "off"
    what = ", ".join(sorted(_rule["sources"])) or "all sources"
    return f"{what}" + (f", older than {_rule['days']:g} days" if _rule["days"] is not None else "")


_from_env()
