"""Thumbnails for the hosted version: download small Commons images for a priority subset and
pack them as data URIs into JSON shards (the artifact sandbox blocks external images)."""
import base64
import hashlib
import json
import re
import time

import requests

from bidb.config import CACHE_DIR, USER_AGENT

THUMB_DIR = CACHE_DIR / "thumbs"
WIDTH = 250
SHARD_BYTES = 12_000_000


def small_url(url):
    url = re.sub(r"width=\d+", f"width={WIDTH}", url)
    return re.sub(r"/(\d+)px-", f"/{WIDTH}px-", url)


def priority(rows, limit):
    have = [r for r in rows if r.get("image_thumb")]
    have.sort(key=lambda r: (not (r.get("curated") or r.get("oldest_of_type")),
                             r.get("year_start") is None, r.get("year_start") or 0))
    return have[:limit]


def fetch_all(rows, limit=1200, log=print):
    """{id: data URI} for up to `limit` priority rows (cached on disk, ~1 request/s)."""
    return _fetch([(r["id"], small_url(r["image_thumb"])) for r in priority(rows, limit)], log, "thumbnails")


def fetch_plans(rows, width=600, log=print):
    """{id: data URI} of every record's floor plan (Wikidata P3311) for the hosted copy."""
    from urllib.parse import quote
    items = [(r["id"], f"https://commons.wikimedia.org/wiki/Special:FilePath/"
                       f"{quote(r['plan_image'].replace(' ', '_'))}?width={width}")
             for r in rows if r.get("plan_image")]
    return _fetch(items, log, "floor plans", webp=True)


PLAN_WEBP = (55, 480)          # quality, width: floor plans (line drawings) stay legible; the hosted copy is 256 MiB at most


def _as_webp(path, quality=PLAN_WEBP[0], width=PLAN_WEBP[1]):
    """A WebP copy (made with cwebp at `quality`, no wider than `width`; cached next to the original), or None."""
    import shutil
    import subprocess
    out = path.with_name(f"{path.stem}_q{quality}w{width}.webp")
    if not out.exists() and shutil.which("cwebp"):
        subprocess.run(["cwebp", "-quiet", "-q", str(quality), "-resize", str(width), "0", str(path), "-o", str(out)],
                       check=False, capture_output=True)
    return out if out.exists() else None


def _fetch(items, log, what, webp=False):
    THUMB_DIR.mkdir(parents=True, exist_ok=True)
    s = requests.Session()
    s.headers["User-Agent"] = USER_AGENT
    out, fetched = {}, 0
    for rid, url in items:
        path = THUMB_DIR / (hashlib.sha1(url.encode()).hexdigest() + ".jpg")
        if not path.exists():
            try:
                resp = s.get(url, timeout=60)
                if resp.status_code == 429:
                    time.sleep(10)
                    resp = s.get(url, timeout=60)
                if resp.status_code != 200 or not resp.headers.get("content-type", "").startswith("image/"):
                    continue
                path.write_bytes(resp.content)
                fetched += 1
                time.sleep(1.0)
            except requests.RequestException:
                continue
        small = _as_webp(path) if webp else None          # floor plans (line drawings) shrink well
        if small:
            out[rid] = "data:image/webp;base64," + base64.b64encode(small.read_bytes()).decode()
            continue
        mime = "image/png" if path.read_bytes()[:4] == b"\x89PNG" else "image/jpeg"
        out[rid] = f"data:{mime};base64," + base64.b64encode(path.read_bytes()).decode()
    log(f"{what}: {len(out)} embedded ({fetched} downloaded now)")
    return out


def write_shards(thumbs, dest_dir, stem="thumbs", max_bytes=SHARD_BYTES, index=None):
    """Split {id: data URI or dict} into JSON files under max_bytes; returns the file names.
    index: optional dict filled with {id: shard number} (for loading one shard on demand)."""
    names, shard, size = [], {}, 0
    for bid, uri in thumbs.items():
        n = len(uri) if isinstance(uri, str) else len(json.dumps(uri, ensure_ascii=False))
        if size + n > max_bytes and shard:
            names.append(_dump(shard, dest_dir, len(names), stem))
            shard, size = {}, 0
        shard[bid] = uri
        size += n + len(bid) + 6
        if index is not None:
            index[bid] = len(names)
    if shard:
        names.append(_dump(shard, dest_dir, len(names), stem))
    return names


def _dump(shard, dest_dir, i, stem):
    name = f"{stem}_{i}.json"
    (dest_dir / name).write_text(json.dumps(shard, ensure_ascii=False, separators=(",", ":")))
    return name
