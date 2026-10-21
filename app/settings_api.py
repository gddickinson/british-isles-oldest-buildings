"""Settings that live on this machine (not in the browser): data locations, the browser used for
screenshots, and the screenshot service itself.

    GET  /api/settings                    data locations, drives, free space, server info
    POST /api/settings                    {"chrome": path}   (empty string = auto-detect)
    POST /api/settings/location/check     {"item", "dest"} -> suggested folder + problems
    POST /api/settings/location           {"item", "dest", "mode": move|copy|use} -> starts a job
    GET  /api/settings/browse?path=       sub-folders, for the folder picker
    GET  /api/screenshot?path=&w=&h=&scale=&theme=&click=   PNG of a page (headless Chrome)
    GET  /_shot?u=&w=&h=&theme=&click=    the page in a frame of exactly w x h (used by screenshots)
"""
import os
import platform
import sys
import tempfile
from pathlib import Path

from flask import Blueprint, abort, jsonify, render_template, request, send_file

from bidb import config

from . import data_location, screenshot
from .common import build_info

bp = Blueprint("settings_api", __name__)


def _rebuild_running():
    from .jobs import running
    return running()


@bp.route("/api/settings", methods=["GET", "POST"])
def settings():
    if request.method == "POST":
        body = request.get_json(force=True) or {}
        if "chrome" in body:
            path = (body["chrome"] or "").strip()
            if path and not Path(path).exists():
                return jsonify(ok=False, problems=[f"{path} does not exist."]), 400
            config.save_settings({"chrome": path or None})
    chrome = screenshot.find_chrome()
    return jsonify(ok=True, data=data_location.status(), chrome=chrome,
                   chrome_custom=config.load_settings().get("chrome"),
                   server={"python": sys.version.split()[0], "platform": platform.platform(terse=True),
                           "project": str(config.ROOT), "build": build_info(),
                           "rebuild_running": _rebuild_running()})


@bp.route("/api/settings/location/check", methods=["POST"])
def location_check():
    body = request.get_json(force=True) or {}
    item = body.get("item")
    if item not in data_location.ITEMS or not body.get("dest"):
        abort(400)
    dest = data_location.suggest(body["dest"], item)
    return jsonify(dest=str(dest), problems=data_location.validate(item, dest))


@bp.route("/api/settings/location", methods=["GET", "POST"])
def location():
    if request.method == "POST":
        body = request.get_json(force=True) or {}
        item, mode = body.get("item"), body.get("mode", "move")
        dest = body.get("dest") or ""
        if mode != "use" and dest:
            dest = str(data_location.suggest(dest, item)) if body.get("suggest", True) else dest
        problems = data_location.start(item, dest, mode, busy=_rebuild_running)
        if problems:
            return jsonify(ok=False, problems=problems), 400
    return jsonify(ok=True, job=data_location._job["state"])


@bp.route("/api/settings/browse")
def browse():
    """Sub-folders of a folder (default: /Volumes), for choosing a data location."""
    path = Path(request.args.get("path") or "/Volumes").expanduser()
    if not path.is_dir():
        abort(404)
    try:
        dirs = sorted(d.name for d in path.iterdir() if d.is_dir() and not d.name.startswith("."))
    except PermissionError:
        dirs = []
    return jsonify(path=str(path), parent=str(path.parent) if path != path.parent else None,
                   dirs=dirs[:300], writable=os.access(path, os.W_OK))


@bp.route("/api/screenshot")
def take_screenshot():
    page = request.args.get("path", "/")
    if not page.startswith("/") or page.startswith("//"):
        abort(400)
    num = lambda k, d, lo, hi: max(lo, min(hi, int(request.args.get(k) or d)))
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "shot.png"
        try:
            screenshot.capture(request.host_url, page, out, width=num("w", 1280, 320, 3840),
                               height=num("h", 800, 300, 4000), scale=num("scale", 1, 1, 3),
                               theme=request.args.get("theme") or None,
                               click=request.args.get("click") or None, wait=num("wait", 5, 1, 20))
        except RuntimeError as exc:
            return jsonify(ok=False, problems=[str(exc)]), 503
        data = out.read_bytes()
    name = (page.strip("/").replace("/", "_").split("?")[0] or "catalogue")
    from io import BytesIO
    return send_file(BytesIO(data), mimetype="image/png", as_attachment=True,
                     download_name=f"british_isles_{name}.png")


@bp.route("/_shot")
def shot_frame():
    return render_template("shot.html")
