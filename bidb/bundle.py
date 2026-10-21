"""The bundled database as a GitHub Release asset (kept out of git: it outgrew GitHub's 50 MB advice).

    python -m bidb.bundle fetch      download data/<db>.sqlite.gz from the release in data/bundled.json
    python -m bidb.bundle release    package the current database and publish it as a new release
                                     (needs the GitHub CLI `gh`, signed in); updates data/bundled.json

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


def release(log=print):
    """Package the current database and publish it as a new GitHub release; update the manifest."""
    from .setup import package
    if not shutil.which("gh"):
        raise RuntimeError("The GitHub CLI `gh` is needed to publish a release.")
    package(log)
    repo = subprocess.run(["gh", "repo", "view", "--json", "nameWithOwner", "-q", ".nameWithOwner"],
                          capture_output=True, text=True, check=True).stdout.strip()
    existing = subprocess.run(["gh", "release", "list", "--limit", "200", "--json", "tagName", "-q", ".[].tagName"],
                              capture_output=True, text=True, check=True).stdout.split()
    day = time.strftime("%Y-%m-%d")
    tag, n = f"db-{day}", 2
    while tag in existing:
        tag, n = f"db-{day}-{n}", n + 1
    from .config import db_path
    import sqlite3
    conn = sqlite3.connect(db_path())
    counts = {t: conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0] for t in ("buildings", "places", "persons")}
    conn.close()
    notes = (f"Bundled database for a new installation ({day}): {counts['buildings']:,} buildings, "
             f"{counts['places']:,} places, {counts['persons']:,} people. `./run.sh` or the setup page downloads it; "
             "it is not needed when you build the database yourself.")
    subprocess.run(["gh", "release", "create", tag, str(BUNDLED), "--title", f"Database {day}", "--notes", notes],
                   check=True)
    MANIFEST.write_text(json.dumps({"repo": repo, "tag": tag, "asset": BUNDLED.name, "bytes": BUNDLED.stat().st_size,
                                    "sha256": sha256(BUNDLED), "date": day, **counts}, indent=1) + "\n")
    log(f"Released {tag}; commit data/bundled.json so new installations download it.")


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    if cmd == "fetch":
        fetch()
    elif cmd == "release":
        release()
    else:
        print(__doc__)
