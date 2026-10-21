"""First run and data locations from the command line (used by run.sh and the GUI setup page).

    python -m bidb.setup check       stop (exit 1) when a configured data folder is missing
    python -m bidb.setup data DIR    use the data in DIR (or DIR/UK_BUILDINGS_DATA); new cache folder there if none
    python -m bidb.setup unpack      unpack the bundled database if there is none (downloaded first from the
                                     GitHub release in data/bundled.json: bidb.bundle)
    python -m bidb.setup package     write data/<db>.sqlite.gz from the current one (publish: bidb.bundle release)
    python -m bidb.setup status      where everything is
"""
import gzip
import json
import shutil
import sqlite3
import sys
import time
from pathlib import Path

from . import config

BUNDLED = config.DATA_DIR / (config.DB_NAME + ".gz")
FOLDER = "UK_BUILDINGS_DATA"


def check():
    """[] or the problems with the configured data folders (checked before anything is created)."""
    try:
        config.require_locations()
        return []
    except config.DataLocationMissing as exc:
        return [str(exc)]


def status():
    db, cache = config.db_path(), config.cache_dir()
    from . import bundle
    b, m = (BUNDLED.stat() if BUNDLED.exists() else None), bundle.manifest()
    return {"db": str(db), "db_exists": db.exists(), "db_mb": round(db.stat().st_size / 1e6) if db.exists() else None,
            "cache": str(cache), "cache_exists": cache.is_dir(), "problems": check(),
            "bundled": ({"mb": round(m["bytes"] / 1e6), "date": m["date"], "release": m["tag"], "local": b is not None}
                        if m else {"mb": round(b.st_size / 1e6), "date": time.strftime("%Y-%m-%d", time.localtime(b.st_mtime)),
                                   "local": True} if b else None),
            "settings": config.load_settings()}


def find_data(path):
    """{"cache": folder or None, "database": folder or None} found in or under `path`."""
    base = Path(path).expanduser()
    if (base / FOLDER).is_dir():
        base = base / FOLDER
    found = {"cache": None, "database": None}
    for folder in (base / "cache", base):
        if folder.is_dir() and ((folder / "basemap").is_dir() or any(folder.glob("*.json"))):
            found["cache"] = folder
            break
    for folder in (base / "database", base, base.parent / "database"):
        if (folder / config.DB_NAME).exists():
            found["database"] = folder
            break
    return found


def use_data(path, create=True):
    """Point settings at the data under `path`. A database found there is used; otherwise the
    database stays where it is (fastest on the internal drive). Without a cache there, a new one is
    made at DIR/UK_BUILDINGS_DATA/cache (when `create`). -> lines describing what was set."""
    base = Path(path).expanduser()
    if not base.is_absolute():
        raise ValueError("Give a full path (starting with /).")
    if not base.is_dir():
        raise ValueError(f"{base} does not exist (is the drive plugged in?).")
    found = find_data(base)
    root = base if base.name == FOLDER else base / FOLDER
    done = []
    if found["database"]:
        config.save_settings({"db_dir": str(found["database"])})
        done.append(f"database: using {found['database'] / config.DB_NAME}")
    cache = found["cache"]
    if cache is None and create:
        cache = root / "cache"
        cache.mkdir(parents=True, exist_ok=True)
        done.append(f"download cache: new folder {cache}")
    elif cache is not None:
        done.append(f"download cache: using {cache}")
    if cache is not None:
        config.save_settings({"cache_dir": str(cache)})
    return done or [f"No data found in {base}."]


def unpack():
    """Unpack the bundled database where the app looks for it (only when there is none)."""
    db = config.db_path()
    if db.exists():
        return f"A database is already at {db}."
    if not BUNDLED.exists():
        from . import bundle
        bundle.fetch()                       # from the GitHub release named in data/bundled.json
    db.parent.mkdir(parents=True, exist_ok=True)
    tmp = db.with_suffix(".unpacking")
    with gzip.open(BUNDLED, "rb") as src, open(tmp, "wb") as out:
        shutil.copyfileobj(src, out, 1 << 20)
    tmp.replace(db)
    return f"Unpacked the bundled database ({db.stat().st_size / 1e6:.0f} MB) to {db}."


def package(log=print):
    """Write data/<db>.sqlite.gz from the current database (a consistent copy, even while in use)."""
    db = config.db_path()
    tmp = BUNDLED.with_name("package.tmp.sqlite")
    src, out = sqlite3.connect(db), sqlite3.connect(tmp)
    src.backup(out)
    out.execute("VACUUM")
    out.close()
    src.close()
    part = BUNDLED.with_suffix(".gz.part")
    with open(tmp, "rb") as f, gzip.open(part, "wb", compresslevel=9) as g:
        shutil.copyfileobj(f, g, 1 << 20)
    part.replace(BUNDLED)
    tmp.unlink()
    log(f"Packaged {db} -> {BUNDLED} ({BUNDLED.stat().st_size / 1e6:.0f} MB)")


def main(argv):
    cmd = argv[0] if argv else "status"
    try:
        if cmd == "check":
            problems = check()
            for p in problems:
                print(p, file=sys.stderr)
            return 1 if problems else 0
        if cmd == "data" and len(argv) > 1:
            for line in use_data(argv[1]):
                print(line)
            return 0
        if cmd == "unpack":
            print(unpack())
            return 0
        if cmd == "package":
            package()
            return 0
        if cmd == "status":
            print(json.dumps(status(), indent=1))
            return 0
    except (ValueError, OSError) as exc:
        print(exc, file=sys.stderr)
        return 1
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
