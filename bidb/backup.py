"""Backups of what git does not hold: python -m bidb.backup [--force] [--keep N] [--list] [--install | --uninstall]

Each run writes <backup_dir>/<date-time>/ (backup_dir from settings.json, e.g. a folder on an external drive):
  british_isles_buildings.sqlite.gz   a consistent snapshot (SQLite's backup API, safe while the app is running)
  settings.json                       data locations of this computer
  runs/*.json                         review outputs (date recheck, listing review, NHLE check...)
  MANIFEST.json                       sizes and SHA-256 of each file, the database's row counts
A run is skipped when the database and settings have not changed since the last backup; the newest `keep`
backups are kept (default 10). When the drive is not mounted the run does nothing and says so.

`--install` adds a launchd job (~/Library/LaunchAgents) that runs a backup every day at 13:00 and at login,
logging to runs/backup.log. Restore: gunzip the .sqlite.gz to data/british_isles_buildings.sqlite (app stopped).

The download cache is not copied: it is large, already on the external drive, and can be downloaded again.
"""
import gzip
import hashlib
import json
import plistlib
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import time
from pathlib import Path

from .config import ROOT, SETTINGS_FILE, db_path, load_settings

LABEL = "com.bidb.backup"
PLIST = Path.home() / "Library" / "LaunchAgents" / f"{LABEL}.plist"
KEEP = 10
MIN_FREE = 2 * 1024 ** 3          # leave at least 2 GB free on the drive


def backup_dir():
    v = load_settings().get("backup_dir")
    return Path(v) if v else None


def _sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def _fingerprint():
    """What decides whether a new backup is needed: the database's and settings' size and mtime."""
    parts = []
    for p in (db_path(), Path(str(db_path()) + "-wal"), SETTINGS_FILE):
        try:
            st = p.stat()
            parts.append([p.name, st.st_size, int(st.st_mtime)])
        except OSError:
            pass
    return parts


def backups(dest=None):
    """Existing backups, oldest first."""
    dest = dest or backup_dir()
    if not dest or not dest.is_dir():
        return []
    return sorted(p for p in dest.iterdir() if p.is_dir() and (p / "MANIFEST.json").exists())


def _counts(path):
    conn = sqlite3.connect(path)
    out = {}
    for table in ("buildings", "places", "persons"):
        try:
            out[table] = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        except sqlite3.Error:
            pass
    conn.close()
    return out


def run(force=False, keep=KEEP, log=print):
    dest = backup_dir()
    if not dest:
        log("No backup_dir in settings.json; nothing done.")
        return None
    if not dest.parent.is_dir():                     # the drive is not mounted
        log(f"{dest.parent} is not available (drive unplugged?); nothing done.")
        return None
    dest.mkdir(exist_ok=True)
    fp = _fingerprint()
    old = backups(dest)
    if old and not force:
        last = json.loads((old[-1] / "MANIFEST.json").read_text())
        if last.get("fingerprint") == fp:
            log(f"Unchanged since {old[-1].name}; nothing done.")
            return None
    if shutil.disk_usage(dest).free < MIN_FREE + db_path().stat().st_size:
        log(f"Not enough free space on {dest}; nothing done.")
        return None

    t0 = time.time()
    name = time.strftime("%Y-%m-%d_%H%M")
    tmp = dest / (name + ".partial")
    shutil.rmtree(tmp, ignore_errors=True)
    tmp.mkdir()
    with tempfile.TemporaryDirectory() as work:
        snap = Path(work) / "snapshot.sqlite"
        src = sqlite3.connect(f"file:{db_path()}?mode=ro", uri=True)
        dst = sqlite3.connect(snap)
        src.backup(dst)
        dst.close()
        src.close()
        counts = _counts(snap)
        with open(snap, "rb") as f, gzip.open(tmp / (db_path().name + ".gz"), "wb", compresslevel=6) as g:
            shutil.copyfileobj(f, g, 1 << 20)
    if SETTINGS_FILE.exists():
        shutil.copy2(SETTINGS_FILE, tmp / SETTINGS_FILE.name)
    reviews = sorted((ROOT / "runs").glob("*.json"))
    if reviews:
        (tmp / "runs").mkdir()
        for p in reviews:
            if p.stat().st_size < 50 * 1024 ** 2:
                shutil.copy2(p, tmp / "runs" / p.name)
    files = {str(p.relative_to(tmp)): {"bytes": p.stat().st_size, "sha256": _sha256(p)}
             for p in sorted(tmp.rglob("*")) if p.is_file()}
    manifest = {"made": time.strftime("%Y-%m-%d %H:%M:%S"), "source": str(db_path()), "counts": counts,
                "fingerprint": fp, "files": files}
    (tmp / "MANIFEST.json").write_text(json.dumps(manifest, indent=1))
    final = dest / name
    shutil.rmtree(final, ignore_errors=True)
    tmp.rename(final)
    # a backup that cannot be read back is no backup: the database copy must decompress
    with gzip.open(final / (db_path().name + ".gz"), "rb") as g:
        while g.read(1 << 22):
            pass
    for p in backups(dest)[:-keep] if keep > 0 else []:
        shutil.rmtree(p)
        log(f"removed old backup {p.name}")
    size = sum(f["bytes"] for f in files.values())
    log(f"Backup {final} ({size / 1e6:.0f} MB, {counts}) in {time.time() - t0:.0f}s")
    return final


def install(hour=13):
    """A launchd job: a backup every day at `hour`:00 and at login (missed runs happen at the next wake)."""
    PLIST.parent.mkdir(parents=True, exist_ok=True)
    plist = {"Label": LABEL,
             "ProgramArguments": [str(ROOT / ".venv" / "bin" / "python"), "-m", "bidb.backup"],
             "WorkingDirectory": str(ROOT),
             "StartCalendarInterval": {"Hour": hour, "Minute": 0},
             "RunAtLoad": True,
             "StandardOutPath": str(ROOT / "runs" / "backup.log"),
             "StandardErrorPath": str(ROOT / "runs" / "backup.log"),
             "LowPriorityIO": True, "Nice": 10}
    (ROOT / "runs").mkdir(exist_ok=True)
    subprocess.run(["launchctl", "unload", str(PLIST)], capture_output=True)
    PLIST.write_bytes(plistlib.dumps(plist))
    subprocess.run(["launchctl", "load", str(PLIST)], check=True)
    print(f"Installed {PLIST}: daily at {hour}:00 and at login; log runs/backup.log")


def uninstall():
    subprocess.run(["launchctl", "unload", str(PLIST)], capture_output=True)
    PLIST.unlink(missing_ok=True)
    print(f"Removed {PLIST}")


def main(argv):
    if "--install" in argv:
        return install()
    if "--uninstall" in argv:
        return uninstall()
    if "--list" in argv:
        for p in backups():
            m = json.loads((p / "MANIFEST.json").read_text())
            print(p.name, f"{sum(f['bytes'] for f in m['files'].values()) / 1e6:.0f} MB", m.get("counts"))
        return None
    keep = int(argv[argv.index("--keep") + 1]) if "--keep" in argv else KEEP
    print(time.strftime("[%Y-%m-%d %H:%M] "), end="", flush=True)
    return run(force="--force" in argv, keep=keep)


if __name__ == "__main__":
    main(sys.argv[1:])
