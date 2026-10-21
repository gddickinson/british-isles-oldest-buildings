"""Polite HTTP client with retries, a minimum request interval and a JSON disk cache."""
import hashlib
import json
import time

import requests

from . import progress, refresh
from .config import USER_AGENT, cache_dir

_session = requests.Session()
_session.headers.update({"User-Agent": USER_AGENT})
_last_call = {}


def _cache_path(key):
    return cache_dir() / (hashlib.sha1(key.encode()).hexdigest() + ".json")


def _throttle(host, min_interval):
    if host.endswith(("wikipedia.org", "wikidata.org", "wikimedia.org")):
        min_interval = max(min_interval, 1.0)     # Wikimedia API etiquette
    wait = _last_call.get(host, 0) + min_interval - time.time()
    if wait > 0:
        time.sleep(wait)
    _last_call[host] = time.time()


def cached(url, params=None, data=None, json_body=None, method="GET"):
    """The cached result of an earlier request_json call, or None (never downloads)."""
    path = _cache_path(json.dumps([method, url, params, data, json_body], sort_keys=True))
    return json.loads(path.read_text()) if path.exists() else None


def request_json(url, params=None, data=None, json_body=None, method="GET",
                 headers=None, min_interval=0.5, use_cache=True, retries=5, extract=None):
    """Return parsed JSON for a request, reading from / writing to the disk cache.

    extract: optional function applied to the response text (e.g. an HTML page) instead of
    JSON parsing; its (JSON-serialisable) result is what gets cached and returned."""
    key = json.dumps([method, url, params, data, json_body], sort_keys=True)
    path = _cache_path(key)
    if use_cache and path.exists() and not refresh.stale(path, url):
        progress.count(from_cache=True)
        return json.loads(path.read_text())
    progress.count(from_cache=False)

    host = requests.utils.urlparse(url).netloc
    delay = 2.0
    for attempt in range(retries):
        _throttle(host, min_interval)
        try:
            resp = _session.request(method, url, params=params, data=data, json=json_body,
                                    headers=headers, timeout=120)
            if extract and resp.status_code == 404:
                result = extract("")
                break
            if resp.status_code in (429, 500, 502, 503, 504):
                retry_after = resp.headers.get("Retry-After", "")
                time.sleep(float(retry_after) if retry_after.isdigit() else delay)
                delay *= 2
                continue
            resp.raise_for_status()
            result = extract(resp.text) if extract else resp.json()
            break
        except (requests.ConnectionError, requests.Timeout,
                requests.exceptions.ChunkedEncodingError, ValueError):
            if attempt == retries - 1:
                raise
            time.sleep(delay)
            delay *= 2
    else:
        raise RuntimeError(f"Giving up on {url} after {retries} attempts")

    if use_cache:
        cache_dir().mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(result))
    return result


def sparql(query):
    """Run a SPARQL query against Wikidata and return the bindings list."""
    from .config import SPARQL_URL
    res = request_json(SPARQL_URL, data={"query": query}, method="POST",
                       headers={"Accept": "application/sparql-results+json"},
                       min_interval=1.0)
    return res["results"]["bindings"]
