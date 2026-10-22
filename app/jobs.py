"""Long jobs started from the GUI, run detached so they outlive the GUI (app/jobs_api.py).

Each job runs as `python -m app.jobs run <name> [options JSON]` in its own session (closing the
GUI or its terminal does not stop it), writes runs/job_<name>.log and reports through
bidb.progress (runs/job_status.json), which the GUI reads to show progress and to re-attach when
reopened. One job at a time; stopping sends SIGTERM to the job's process group (handled as Ctrl-C).
"""
import json
import os
import signal
import subprocess
import sys
import time

from bidb import progress, refresh
from bidb.config import ROOT

# name: (label, what it does, rough time with a warm cache)
JOBS = {
    "build": ("Rebuild the database", "Buildings, places and people (every place group, the researched oldest lists), "
              "pronunciations, Domesday, tree-ring dates, stories, timelines, tours, on this day and visiting information.",
              "minutes with a warm cache; many hours from scratch"),
    "photos": ("Find photos", "Wikimedia Commons photos near records that have none (buildings, then places).",
               "about 1 s per record without a photo"),
    "footprints": ("Outlines and floor plans", "Building outlines from OpenStreetMap and floor plans from "
                   "Wikidata and Commons.", "about an hour"),
    "maplayers": ("Offline map layers", "Coastline, roads, rivers, towns, stations, historic counties and the "
                  "tiled layers (minor roads, streams, lakes, walking and cycle routes, Roman roads, buried "
                  "rivers).", "hours from scratch (OpenStreetMap)"),
    "export": ("Hosted copy", "The static site in dist/ (publishing it stays a separate step).", "a few minutes"),
    "package": ("Package the database", "data/british_isles_buildings.sqlite.gz from the current database "
                "(publishing it for new installations: python -m bidb.bundle release).", "about a minute"),
    "bundled": ("Get the bundled database", "Download the bundled database from the project's GitHub release "
                "and unpack it.", "a minute or two"),
}


def steps(name, opts):
    """[(stage name, function)] for a job."""
    if name == "build":
        from bidb import build
        return build.stages(int(opts.get("cutoff") or build.CUTOFF_YEAR), not opts.get("no_places"),
                            True, not opts.get("no_stories"))
    if name == "photos":
        from bidb import images_extra
        return [("Photos for buildings", lambda: images_extra.run("buildings")),
                ("Photos for places", lambda: images_extra.run("places"))]
    if name == "footprints":
        from bidb import footprints
        return [("Outlines and floor plans", footprints.run)]
    if name == "maplayers":
        from . import basemap_build, basemap_tiled
        return [("Base map", basemap_build.main)] + [
            (f"Layer: {layer}", lambda layer=layer: basemap_tiled.build(layer)) for layer in basemap_tiled.LAYERS]
    if name == "export":
        from . import static_export
        return [("Hosted copy", static_export.export)]
    if name == "package":
        from bidb import setup
        return [("Package the database", setup.package)]
    if name == "bundled":
        from bidb import bundle, setup
        return [("Download", bundle.fetch), ("Unpack", lambda: print(setup.unpack()))]
    raise KeyError(name)


def log_path(name):
    return progress.RUNS / f"job_{name}.log"


def status(lines=20):
    st = progress.read()
    path = st.get("log")
    if path and os.path.exists(path):
        with open(path, errors="replace") as f:
            st["tail"] = [ln.rstrip("\n") for ln in f.readlines()[-lines:]]
    if st.get("job") in JOBS:
        st["label"] = JOBS[st["job"]][0]
    st["now"] = time.time()
    return st


def running():
    return progress.read().get("state") == "running"


def start(name, opts=None):
    """Start a job in the background -> [] or a list of problems."""
    opts = opts or {}
    if name not in JOBS:
        return [f"Unknown job {name}."]
    if running():
        return ["Another job is still running; wait for it or stop it first."]
    from bidb.setup import check
    problems = check()
    if problems:
        return problems
    if name not in ("build", "maplayers", "bundled") and not _db_exists():
        return ["There is no database yet: build it or use the bundled one first."]
    progress.RUNS.mkdir(exist_ok=True)
    log = open(log_path(name), "w")
    proc = subprocess.Popen([sys.executable, "-u", "-m", "app.jobs", "run", name, json.dumps(opts)], cwd=ROOT,
                            stdout=log, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL, start_new_session=True)
    progress.placeholder(name, proc.pid, [n for n, _ in _names(name, opts)], log_path(name), opts)
    return []


def _names(name, opts):
    try:
        return steps(name, opts)
    except Exception:                       # the job itself will report the problem
        return [(JOBS[name][0], None)]


def _db_exists():
    from bidb.config import db_path
    return db_path().exists()


def stop():
    st = progress.read()
    if st.get("state") != "running":
        return ["No job is running."]
    try:
        os.killpg(os.getpgid(st["pid"]), signal.SIGTERM)
    except ProcessLookupError:
        return ["The job had already stopped."]
    return []


def _interrupt(*_):
    raise KeyboardInterrupt


def _run(name, opts):
    refresh.set_rule(opts.get("refresh_days"), opts.get("refresh_sources") or [])
    if refresh.active():
        print(f"refresh: {refresh.describe()}", flush=True)
    for sig in (signal.SIGTERM, signal.SIGINT):     # SIGINT may arrive ignored when the GUI runs in the background
        signal.signal(sig, _interrupt)
    progress.run_stages(name, steps(name, opts), log_path(name),
                        {**opts, "refresh": refresh.describe()})


if __name__ == "__main__":
    if len(sys.argv) >= 3 and sys.argv[1] == "run":
        try:
            _run(sys.argv[2], json.loads(sys.argv[3]) if len(sys.argv) > 3 else {})
        except KeyboardInterrupt:
            print("Stopped.", flush=True)
            sys.exit(130)
    else:
        print(__doc__)
