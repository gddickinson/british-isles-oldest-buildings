"""The bundled database as a GitHub Release asset (kept out of git: it outgrew GitHub's 50 MB advice).

    python -m bidb.bundle fetch      download data/<db>.sqlite.gz from the release in data/bundled.json
    python -m bidb.bundle release    package the current database and publish it as a new release
                                     (needs the GitHub CLI `gh`, signed in); updates data/bundled.json.
                                     Draft first, upload with retries, checked against GitHub's SHA-256,
                                     then published; an interrupted run carries on with its draft

data/bundled.json (committed) names the release tag, asset, size, date and SHA-256; downloads are
checked against it. The repository is private, so downloading needs GitHub access: the GitHub CLI
(`gh auth login`) or a token in GH_TOKEN / GITHUB_TOKEN; a public repository needs neither.
"""
import hashlib
import json
import os
import shutil
import subprocess
import sys
import time

import requests

from . import progress
from .config import DATA_DIR, DB_NAME, USER_AGENT

MANIFEST = DATA_DIR / "bundled.json"
BUNDLED = DATA_DIR / (DB_NAME + ".gz")


def manifest():
    try:
        return json.loads(MANIFEST.read_text())
    except (OSError, ValueError):
        return None


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def is_current():
    """The local .gz exists and matches the manifest."""
    m = manifest()
    return BUNDLED.exists() and (m is None or (BUNDLED.stat().st_size == m["bytes"] and sha256(BUNDLED) == m["sha256"]))


def _token():
    for k in ("GH_TOKEN", "GITHUB_TOKEN"):
        if os.environ.get(k):
            return os.environ[k]
    if shutil.which("gh"):
        out = subprocess.run(["gh", "auth", "token"], capture_output=True, text=True)
        if out.returncode == 0 and out.stdout.strip():
            return out.stdout.strip()
    return None


def fetch(log=print):
    """Download the bundled database named in the manifest (skipped when the local copy matches)."""
    m = manifest()
    if m is None:
        raise FileNotFoundError(f"No {MANIFEST.name}: this copy of the app has no bundled database release.")
    if is_current():
        log(f"Bundled database already here ({BUNDLED.stat().st_size / 1e6:.0f} MB).")
        return
    headers, token = {"User-Agent": USER_AGENT}, _token()
    if token:                                   # private repository: the API asset URL with a token
        headers["Authorization"] = f"Bearer {token}"
        api = f"https://api.github.com/repos/{m['repo']}/releases/tags/{m['tag']}"
        r = requests.get(api, headers=headers, timeout=60)
        r.raise_for_status()
        asset = next(a for a in r.json()["assets"] if a["name"] == m["asset"])
        url, headers["Accept"] = asset["url"], "application/octet-stream"
    else:
        url = f"https://github.com/{m['repo']}/releases/download/{m['tag']}/{m['asset']}"
    log(f"Downloading {m['asset']} ({m['bytes'] / 1e6:.0f} MB) from release {m['tag']}")
    part = BUNDLED.with_suffix(".gz.part")
    with requests.get(url, headers=headers, stream=True, timeout=120) as r:
        if r.status_code == 404 and not token:
            raise PermissionError("The release could not be downloaded: the repository is private. Sign in with "
                                  "`gh auth login` or set GH_TOKEN, then try again.")
        r.raise_for_status()
        done, t0 = 0, time.time()
        with open(part, "wb") as f:
            for chunk in r.iter_content(1 << 20):
                f.write(chunk)
                done += len(chunk)
                progress.items(done, m["bytes"])
        log(f"Downloaded {done / 1e6:.0f} MB in {time.time() - t0:.0f} s")
    if part.stat().st_size != m["bytes"] or sha256(part) != m["sha256"]:
        part.unlink()
        raise ValueError("The download does not match data/bundled.json (size or SHA-256); nothing was changed.")
    part.replace(BUNDLED)


API = "https://api.github.com"
UPLOADS = "https://uploads.github.com"
ATTEMPTS = 5


class _Reader:
    """The file as an upload body with a length (GitHub needs Content-Length) that reports progress."""
    def __init__(self, path):
        self.f, self.size, self.done = open(path, "rb"), path.stat().st_size, 0

    def __len__(self):
        return self.size

    def read(self, n=-1):
        block = self.f.read(1 << 16 if n is None or n < 0 else min(n, 1 << 16))
        self.done += len(block)
        progress.items(self.done, self.size)
        return block

    def close(self):
        self.f.close()


def _github(method, url, token, **kw):
    r = requests.request(method, url, headers={"Authorization": f"Bearer {token}", "User-Agent": USER_AGENT,
                                               "Accept": "application/vnd.github+json", **kw.pop("headers", {})},
                         timeout=kw.pop("timeout", 60), **kw)
    r.raise_for_status()
    return r.json() if r.content else None


def _draft(repo, token, day, notes, log):
    """The draft release for today left by an interrupted run, else a new one (tag db-<day>[-n])."""
    releases = _github("GET", f"{API}/repos/{repo}/releases?per_page=100", token)
    for rel in releases:
        if rel["draft"] and rel["tag_name"].startswith(f"db-{day}"):
            log(f"Carrying on with draft release {rel['tag_name']}")
            return rel
    tags, tag, n = {r["tag_name"] for r in releases}, f"db-{day}", 2
    while tag in tags:
        tag, n = f"db-{day}-{n}", n + 1
    return _github("POST", f"{API}/repos/{repo}/releases", token,
                   json={"tag_name": tag, "name": f"Database {day}", "body": notes, "draft": True})


def _upload(repo, rel, token, path, digest, log):
    """Upload the asset, retrying after a dropped upload (slow connections: GitHub gives up on a stalled
    body with HTTP 408); a half-uploaded or mismatching asset is removed first. Returns the asset."""
    url = f"{API}/repos/{repo}/releases/{rel['id']}/assets"
    for attempt in range(1, ATTEMPTS + 1):
        for a in _github("GET", url, token):
            if a["name"] == path.name:
                if a["state"] == "uploaded" and a["size"] == path.stat().st_size and a.get("digest") == digest:
                    return a
                _github("DELETE", a["url"], token)
        body, t0 = _Reader(path), time.time()
        log(f"Uploading {path.name} ({body.size / 1e6:.0f} MB), attempt {attempt} of {ATTEMPTS}")
        try:
            a = _github("POST", f"{UPLOADS}/repos/{repo}/releases/{rel['id']}/assets", token, data=body,
                        params={"name": path.name}, headers={"Content-Type": "application/gzip"}, timeout=(60, 900))
            log(f"Uploaded in {time.time() - t0:.0f} s ({body.size / 1e3 / max(time.time() - t0, 1):.0f} KB/s)")
            return a
        except requests.RequestException as e:
            log(f"Upload failed after {time.time() - t0:.0f} s: {e}")
            if attempt < ATTEMPTS:
                time.sleep(min(30 * attempt, 120))
        finally:
            body.close()
    raise RuntimeError(f"The upload failed {ATTEMPTS} times; draft release {rel['tag_name']} is kept and the next "
                       "`python -m bidb.bundle release` carries on with it.")


def release(log=print):
    """Package the current database and publish it as a new GitHub release; update the manifest.
    Draft release -> upload with retries -> size and SHA-256 checked against GitHub's -> published."""
    from .setup import package
    token = _token()
    if not shutil.which("gh") or not token:
        raise RuntimeError("Publishing a release needs the GitHub CLI `gh`, signed in (or a token in GH_TOKEN).")
    package(log)
    repo = subprocess.run(["gh", "repo", "view", "--json", "nameWithOwner", "-q", ".nameWithOwner"],
                          capture_output=True, text=True, check=True).stdout.strip()
    day = time.strftime("%Y-%m-%d")
    from .config import db_path
    import sqlite3
    conn = sqlite3.connect(db_path())
    counts = {t: conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0] for t in ("buildings", "places", "persons")}
    conn.close()
    notes = (f"Bundled database for a new installation ({day}): {counts['buildings']:,} buildings, "
             f"{counts['places']:,} places, {counts['persons']:,} people. `./run.sh` or the setup page downloads it; "
             "it is not needed when you build the database yourself.")
    digest = "sha256:" + sha256(BUNDLED)
    rel = _draft(repo, token, day, notes, log)
    asset = _upload(repo, rel, token, BUNDLED, digest, log)
    asset = _github("GET", asset["url"], token)
    if asset["size"] != BUNDLED.stat().st_size or asset.get("digest", digest) != digest:
        _github("DELETE", asset["url"], token)
        raise ValueError(f"GitHub's copy does not match ({asset['size']} bytes, {asset.get('digest')}); it was "
                         f"removed and draft release {rel['tag_name']} kept.")
    log("GitHub's copy matches: " + ("SHA-256 " + digest[7:19] + "…" if asset.get("digest") else "size (no digest given)"))
    _github("PATCH", f"{API}/repos/{repo}/releases/{rel['id']}", token, json={"draft": False, "make_latest": "true"})
    MANIFEST.write_text(json.dumps({"repo": repo, "tag": rel["tag_name"], "asset": BUNDLED.name,
                                    "bytes": BUNDLED.stat().st_size, "sha256": digest[7:], "date": day, **counts},
                                   indent=1) + "\n")
    log(f"Released {rel['tag_name']}; commit data/bundled.json so new installations download it.")


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    if cmd == "fetch":
        fetch()
    elif cmd == "release":
        release()
    else:
        print(__doc__)
