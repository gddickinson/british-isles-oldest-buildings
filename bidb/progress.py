"""Progress of a long job (build, photos, map layers…), shared with the GUI through a status file.

runs/job_status.json holds the job's name, process id, stages (with the time each took last
time, for the estimate), the current stage, items done within it, downloads vs cache hits, and the
outcome. The GUI reads it (app/jobs.py), so a job keeps reporting after the GUI is closed and
reopened. Stage times are kept in runs/stage_times.json.

    progress.run_stages("build", [("Buildings", fn), ("Places", fn2)])
    progress.items(done, total)          # inside a long loop
    progress.count(from_cache)           # called by bidb.http for each request
"""
import json
import os
import time
import traceback

from .config import ROOT

RUNS = ROOT / "runs"
STATUS = RUNS / "job_status.json"
TIMES = RUNS / "stage_times.json"
_state = None
_last_write = [0.0]


def _write(force=False):
    if _state is None or (not force and time.time() - _last_write[0] < 1.0):
        return
    _last_write[0] = time.time()
    _state["updated"] = time.time()
    RUNS.mkdir(exist_ok=True)
    tmp = STATUS.with_name(f"job_status.{os.getpid()}.tmp")
    tmp.write_text(json.dumps(_state))
    tmp.replace(STATUS)


def _times():
    try:
        return json.loads(TIMES.read_text())
    except (OSError, ValueError):
        return {}


def begin(job, stage_names, log_file=None, options=None):
    """Start reporting for this process."""
    global _state
    last = _times().get(job, {})
    _state = {"job": job, "pid": os.getpid(), "started": time.time(), "log": str(log_file) if log_file else None,
              "options": options or {}, "stages": [{"name": n, "expected": last.get(n), "took": None} for n in stage_names],
              "index": -1, "stage_started": None, "items": None, "downloads": 0, "cached": 0,
              "message": "", "finished": None, "ok": None}
    _write(force=True)


def placeholder(job, pid, stage_names, log_file=None, options=None):
    """Status for a job another process has just started (it takes over within a second)."""
    last = _times().get(job, {})
    RUNS.mkdir(exist_ok=True)
    STATUS.write_text(json.dumps({
        "job": job, "pid": pid, "started": time.time(), "log": str(log_file) if log_file else None,
        "options": options or {}, "stages": [{"name": n, "expected": last.get(n), "took": None} for n in stage_names],
        "index": -1, "stage_started": None, "items": None, "downloads": 0, "cached": 0, "message": "Starting…",
        "finished": None, "ok": None, "updated": time.time()}))


def stage(name):
    """Move on to the named stage (closing the previous one)."""
    if _state is None:
        return
    _close_stage()
    names = [s["name"] for s in _state["stages"]]
    _state["index"] = names.index(name) if name in names else _state["index"] + 1
    _state.update(stage_started=time.time(), items=None, message="")
    _write(force=True)


def _close_stage():
    i = _state["index"]
    if 0 <= i < len(_state["stages"]) and _state["stage_started"]:
        _state["stages"][i]["took"] = round(time.time() - _state["stage_started"], 1)


def items(done, total):
    if _state is not None:
        _state["items"] = [done, total]
        _write()


def note(message):
    if _state is not None:
        _state["message"] = str(message)[:300]
        _write()


def count(from_cache):
    if _state is not None:
        _state["cached" if from_cache else "downloads"] += 1
        _write()


def end(ok, message=""):
    if _state is None:
        return
    _close_stage()
    _state.update(finished=time.time(), ok=ok, message=message)
    _write(force=True)
    if ok:                                   # remember stage times for the next estimate
        times = _times()
        times[_state["job"]] = {s["name"]: s["took"] for s in _state["stages"] if s["took"] is not None}
        RUNS.mkdir(exist_ok=True)
        TIMES.write_text(json.dumps(times, indent=1))


def run_stages(job, steps, log_file=None, options=None):
    """Run [(stage name, function), …] in order, reporting each; re-raises a failure after recording it."""
    begin(job, [n for n, _ in steps], log_file, options)
    try:
        for name, fn in steps:
            stage(name)
            print(f"== {name}", flush=True)
            fn()
    except BaseException as exc:            # includes KeyboardInterrupt / SystemExit from a stop
        end(False, "Stopped." if isinstance(exc, KeyboardInterrupt) else
            f"{type(exc).__name__}: {exc}" if str(exc) else type(exc).__name__)
        if not isinstance(exc, (KeyboardInterrupt, SystemExit)):
            traceback.print_exc()
        raise
    end(True, "Finished.")


def read():
    """The status file, with "state": running / finished / failed / died (stopped without saying so) / none."""
    try:
        st = json.loads(STATUS.read_text())
    except (OSError, ValueError):
        return {"state": "none"}
    if st.get("finished"):
        st["state"] = "finished" if st.get("ok") else "failed"
    else:
        st["state"] = "running" if alive(st.get("pid")) else "died"
    return st


def alive(pid):
    if not pid:
        return False
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    try:                                     # a finished child not yet reaped by its parent is a zombie
        import subprocess
        out = subprocess.run(["ps", "-o", "stat=", "-p", str(pid)], capture_output=True, text=True).stdout
        return bool(out.strip()) and not out.strip().startswith("Z")
    except OSError:
        return True
