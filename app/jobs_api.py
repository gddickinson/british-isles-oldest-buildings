"""Jobs and first-run setup.

    GET  /api/jobs               job list, refresh sources, current/last job status (+ log tail)
    POST /api/jobs/start         {"job", "options": {cutoff, no_places, no_stories, refresh_days, refresh_sources}}
    POST /api/jobs/stop          stop the running job
    GET  /api/setup              where the data is, the bundled database, problems
    POST /api/setup              {"action": "bundled"} | {"action": "use", "folder"} |
                                 {"action": "build", "cache_folder"?, "options"?}
Pages other than setup, settings and help redirect to /setup while there is no database.
"""
from pathlib import Path

from flask import Blueprint, jsonify, redirect, request

from bidb import config, refresh, setup

from . import jobs

bp = Blueprint("jobs_api", __name__)
OPEN_WITHOUT_DB = ("/setup", "/api/setup", "/api/jobs", "/api/settings", "/settings", "/help", "/static", "/sw.js")


@bp.before_app_request
def _need_setup():
    from .pages import STATIC_MODE
    if STATIC_MODE or request.path.startswith(OPEN_WITHOUT_DB) or config.db_path().exists():
        return None
    if request.path.startswith("/api/"):
        return jsonify(error="No database yet: open /setup", setup=True), 503
    return redirect("/setup")


@bp.route("/api/jobs")
def jobs_status():
    return jsonify(jobs={k: {"label": v[0], "about": v[1], "time": v[2]} for k, v in jobs.JOBS.items()},
                   order=list(jobs.JOBS),
                   sources={k: v[0] for k, v in refresh.SOURCES.items()}, status=jobs.status())


@bp.route("/api/jobs/start", methods=["POST"])
def jobs_start():
    body = request.get_json(force=True) or {}
    problems = jobs.start(body.get("job"), _options(body.get("options") or {}))
    return jsonify(ok=not problems, problems=problems, status=jobs.status()), (400 if problems else 200)


@bp.route("/api/jobs/stop", methods=["POST"])
def jobs_stop():
    problems = jobs.stop()
    return jsonify(ok=not problems, problems=problems), (400 if problems else 200)


def _options(o):
    out = {}
    if o.get("cutoff"):
        out["cutoff"] = int(o["cutoff"])
    for flag in ("no_places", "no_stories"):
        if o.get(flag):
            out[flag] = True
    if o.get("refresh_days") not in (None, ""):
        out["refresh_days"] = float(o["refresh_days"])
    out["refresh_sources"] = [s for s in o.get("refresh_sources") or [] if s in refresh.SOURCES]
    return out


@bp.route("/api/setup", methods=["GET", "POST"])
def setup_api():
    if request.method == "GET":
        return jsonify(setup.status())
    body = request.get_json(force=True) or {}
    action = body.get("action")
    try:
        if action == "bundled":
            from bidb import bundle
            if bundle.BUNDLED.exists():
                message = setup.unpack()
            else:                                # download first: a job, so the page can show progress
                problems = jobs.start("bundled")
                if problems:
                    return jsonify(ok=False, problems=problems), 400
                return jsonify(ok=True, job=True, message="Downloading the bundled database…", status=setup.status())
        elif action == "use":
            message = "; ".join(setup.use_data(body.get("folder") or "", create=False))
            if not config.db_path().exists():
                message += ". No database was found there: use the bundled one or build it."
        elif action == "build":
            folder = (body.get("cache_folder") or "").strip()
            if folder:
                p = Path(folder).expanduser()
                if not p.is_absolute():
                    raise ValueError("Give the cache folder as a full path (starting with /).")
                p.mkdir(parents=True, exist_ok=True)
                config.save_settings({"cache_dir": None if p == config.DEFAULT_CACHE_DIR else str(p)})
            problems = jobs.start("build", _options(body.get("options") or {}))
            if problems:
                return jsonify(ok=False, problems=problems), 400
            message = "The build has started."
        else:
            return jsonify(ok=False, problems=["Unknown action."]), 400
    except (ValueError, OSError) as exc:
        return jsonify(ok=False, problems=[str(exc)]), 400
    return jsonify(ok=True, message=message, status=setup.status())
