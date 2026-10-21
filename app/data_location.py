"""Where the bulky data lives, and moving it (Settings page -> /api/settings/location).

Two movable items:
  cache     data/cache: downloaded API responses, map sources, thumbnails (~2 GB)
  database  british_isles_buildings.sqlite (~150 MB; fastest on the internal drive)

A move copies to the new folder, verifies file count and bytes, switches settings.json to it and
only then deletes the old copy ("copy" keeps it). One job at a time, in a background thread.
"""
import os
import shutil
import tempfile
import threading
import time
from pathlib import Path

from bidb import config

ITEMS = {
    "cache": {"label": "Download cache", "key": "cache_dir",
              "about": "Saved responses from Wikidata, Wikipedia, the heritage registers and map "
                       "sources. Rebuilds read it instead of downloading again."},
    "database": {"label": "Database", "key": "db_dir",
                 "about": "The SQLite file the app reads. Keep it on a fast internal drive."},
}
_job = {"thread": None, "state": None}


def current(item):
    """Path of an item now (a folder for the cache, the file for the database)."""
    return config.cache_dir() if item == "cache" else config.db_path()


def default(item):
    return config.DEFAULT_CACHE_DIR if item == "cache" else config.DEFAULT_DB_PATH


def _tree_size(path):
    files = size = 0
    if path.is_file():
        return 1, path.stat().st_size
    for root, _, names in os.walk(path):
        for n in names:
            try:
                size += os.stat(os.path.join(root, n)).st_size
                files += 1
            except OSError:
                pass
    return files, size


def _sizes_cached(path, _memo={}):
    """(files, bytes), memoised for a minute: walking ~20k files takes a moment on a USB disk."""
    key = str(path)
    hit = _memo.get(key)
    if hit and time.time() - hit[0] < 60:
        return hit[1]
    val = _tree_size(path) if path.exists() else (0, 0)
    _memo[key] = (time.time(), val)
    return val


def _free(path):
    p = Path(path)
    while not p.exists() and p != p.parent:
        p = p.parent
    try:
        u = shutil.disk_usage(p)
        return {"free": u.free, "total": u.total}
    except OSError:
        return {"free": None, "total": None}


def _writable(path):
    """Really writable? (os.access says yes for NTFS drives that macOS mounts read-only)"""
    try:
        with tempfile.NamedTemporaryFile(dir=path, prefix=".bidb_write_test"):
            return True
    except OSError:
        return False


def volume_of(path):
    parts = Path(path).resolve().parts if Path(path).exists() else Path(path).parts
    return f"/Volumes/{parts[2]}" if len(parts) > 2 and parts[1] == "Volumes" else "/"


def volumes():
    """Mounted drives a user could store data on, with free space and whether they are writable."""
    out = [{"path": str(config.ROOT), "name": "This project folder", **_free(config.ROOT),
            "writable": _writable(config.ROOT)}]
    vroot = Path("/Volumes")
    if vroot.is_dir():
        for v in sorted(vroot.iterdir()):
            if v.name.startswith(".") or v.name.startswith("com.apple") or v.resolve() == Path("/"):
                continue
            if v.name in ("Recovery", "Preboot", "VM", "Macintosh HD"):
                continue
            out.append({"path": str(v), "name": v.name, **_free(v), "writable": _writable(v)})
    return out


def status():
    """Everything the Settings page shows about data locations."""
    items = {}
    for item, meta in ITEMS.items():
        path = current(item)
        folder = path if item == "cache" else path.parent
        files, size = _sizes_cached(path)
        items[item] = {**meta, "path": str(folder), "default": str(default(item) if item == "cache"
                                                                   else default(item).parent),
                       "is_default": path == default(item), "available": folder.is_dir(),
                       "files": files, "bytes": size, "volume": volume_of(folder), **_free(folder)}
    return {"items": items, "volumes": volumes(), "job": _job["state"],
            "settings_file": str(config.SETTINGS_FILE)}


def suggest(dest_root, item):
    """Where an item goes under a chosen drive/folder: <dest>/UK_BUILDINGS_DATA/cache etc."""
    p = Path(dest_root).expanduser()
    if p == config.ROOT or p == config.DATA_DIR:
        return default(item) if item == "cache" else default(item).parent
    if p.name == "UK_BUILDINGS_DATA" or p.name in ("cache", "database"):
        base = p if p.name == "UK_BUILDINGS_DATA" else p.parent
    else:
        base = p / "UK_BUILDINGS_DATA"
    return base / ("cache" if item == "cache" else "database")


def validate(item, dest):
    """Problems with moving `item` to folder `dest` ([] when fine)."""
    src = current(item)
    src_folder = src if item == "cache" else src.parent
    dest = Path(dest).expanduser()
    problems = []
    if not dest.is_absolute():
        problems.append("Choose a full path (starting with /).")
        return problems
    if dest.resolve() == src_folder.resolve():
        problems.append("The data is already there.")
    if item == "cache" and (str(dest.resolve()) + "/").startswith(str(src_folder.resolve()) + "/"):
        problems.append("The new folder cannot be inside the current one.")
    probe = dest
    while not probe.exists() and probe != probe.parent:
        probe = probe.parent
    if not _writable(probe):
        problems.append(f"{probe} is not writable.")
    _, size = _sizes_cached(src)
    free = _free(dest)["free"]
    if free is not None and size + 200_000_000 > free and volume_of(dest) != volume_of(src_folder):
        problems.append(f"Not enough free space: needs {size / 1e9:.2f} GB plus a margin, "
                        f"{free / 1e9:.2f} GB free.")
    target = dest / config.DB_NAME if item == "database" else dest
    if target.exists() and any(target.iterdir() if target.is_dir() else [True]):
        problems.append(f"{target} already exists and is not empty; choose an empty folder.")
    if _job["thread"] and _job["thread"].is_alive():
        problems.append("Another move is still running.")
    return problems


def start(item, dest, mode="move", busy=lambda: False):
    """Begin moving/copying in the background. Returns [] or a list of problems."""
    if item not in ITEMS or mode not in ("move", "copy", "use"):
        return ["Unknown item or mode."]
    if busy():
        return ["A rebuild is running; wait for it to finish."]
    dest = Path(dest).expanduser()
    if mode == "use":           # point at a folder that already holds the data (e.g. a copy made earlier)
        ok = (dest / config.DB_NAME).exists() if item == "database" else dest.is_dir()
        if not ok:
            return [f"No {ITEMS[item]['label'].lower()} found in {dest}."]
        _switch(item, dest)
        _job["state"] = {"item": item, "mode": mode, "dest": str(dest), "phase": "done",
                         "message": f"Now using {dest}."}
        return []
    problems = validate(item, dest)
    if problems:
        return problems
    _job["state"] = {"item": item, "mode": mode, "dest": str(dest), "phase": "starting",
                     "copied_files": 0, "copied_bytes": 0, "message": ""}
    _job["thread"] = threading.Thread(target=_run, args=(item, dest, mode), daemon=True)
    _job["thread"].start()
    return []


def _switch(item, dest):
    is_default = Path(dest) == (default(item) if item == "cache" else default(item).parent)
    config.save_settings({ITEMS[item]["key"]: None if is_default else str(dest)})


def _run(item, dest, mode):
    st = _job["state"]
    src = current(item)
    try:
        total_files, total_bytes = _tree_size(src)
        st.update(phase="copying", total_files=total_files, total_bytes=total_bytes)
        if item == "database":
            dest.mkdir(parents=True, exist_ok=True)
            _copy_file(src, dest / config.DB_NAME, st)
            pairs = [(src, dest / config.DB_NAME)]
        else:
            pairs = []
            for root, _, names in os.walk(src):
                out_dir = dest / os.path.relpath(root, src)
                out_dir.mkdir(parents=True, exist_ok=True)
                for n in names:
                    a, b = Path(root) / n, out_dir / n
                    _copy_file(a, b, st)
                    pairs.append((a, b))
        st["phase"] = "verifying"
        bad = [str(a) for a, b in pairs if not b.exists() or b.stat().st_size != a.stat().st_size]
        files, size = _tree_size(dest / config.DB_NAME if item == "database" else dest)
        if bad or files < total_files or size < total_bytes:
            raise RuntimeError(f"Verification failed ({len(bad)} files differ; {files}/{total_files} "
                               f"files, {size}/{total_bytes} bytes). The old copy is kept.")
        _switch(item, dest)
        if mode == "move":
            st["phase"] = "removing old copy"
            if item == "database":
                src.unlink()
            else:
                shutil.rmtree(src)
        st.update(phase="done", message=f"{'Moved' if mode == 'move' else 'Copied'} "
                                        f"{files:,} file{'s' if files != 1 else ''} ({size / 1e9:.2f} GB) to {dest}; "
                                        "now in use.")
    except Exception as exc:                      # report, keep the old location in use
        st.update(phase="failed", message=str(exc))


def _copy_file(a, b, st):
    shutil.copy2(a, b)
    st["copied_files"] += 1
    st["copied_bytes"] += a.stat().st_size
