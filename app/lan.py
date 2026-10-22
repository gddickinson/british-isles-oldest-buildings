"""Sharing the app on the home network: read-only for every computer but this one.

    GET  /api/share     {enabled, listening, port, urls}       (this computer only)
    POST /api/share     {"enabled": true|false} -> saved in settings.json, the app restarts on its new address

When sharing is on the server listens on every network interface (0.0.0.0) instead of 127.0.0.1, and
`guard` (run before every request) answers 403 to other computers for anything that changes something
(any method but GET/HEAD/OPTIONS) and for the pages and calls that belong to this computer (settings and
data locations, the folder browser, screenshots, setup, saving street maps for offline use).
"""
import ipaddress
import os
import re
import socket
import subprocess
import sys
import threading
import time

from flask import Blueprint, current_app, jsonify, request

from bidb import config

bp = Blueprint("lan", __name__)
SAFE = {"GET", "HEAD", "OPTIONS"}
LOCAL_ONLY = re.compile(r"^/(api/settings|api/screenshot|_shot|api/setup|setup|api/share|api/street_tiles)(/|$)")
MESSAGE = "Read-only: changes can be made only on the computer running the app."


def is_local(addr=None):
    """True for a request from this computer (loopback)."""
    addr = addr if addr is not None else request.remote_addr
    try:
        ip = ipaddress.ip_address((addr or "").removeprefix("::ffff:"))
    except ValueError:
        return False
    return ip.is_loopback


def blocked(method, path, local):
    """Whether a request is refused (other computers: read-only, and nothing of this computer's own)."""
    return not local and (method not in SAFE or bool(LOCAL_ONLY.match(path)))


def guard():
    if blocked(request.method, request.path, is_local()):
        return jsonify({"error": MESSAGE}), 403
    return None


def enabled():
    return bool(config.load_settings().get("share_on_network"))


def host_for(lan=None):
    """The address to listen on: every interface when sharing, else this computer only."""
    return "0.0.0.0" if (enabled() if lan is None else lan) else "127.0.0.1"


def addresses():
    """This computer's address on the home network and its local (Bonjour) name."""
    out = []
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("192.0.2.1", 9))          # a documentation address: no packet is sent
            out.append(s.getsockname()[0])
    except OSError:
        pass
    name = None
    if sys.platform == "darwin":
        try:
            name = subprocess.run(["scutil", "--get", "LocalHostName"], capture_output=True, text=True,
                                  timeout=3).stdout.strip()
        except (OSError, subprocess.SubprocessError):
            name = None
    name = name or socket.gethostname().split(".")[0]
    if name:
        out.append(f"{name}.local")
    return [a for a in out if a and not a.startswith("127.")]


def status():
    port = current_app.config.get("PORT", 5050)
    listening = current_app.config.get("HOST", "127.0.0.1") not in ("127.0.0.1", "localhost", "::1")
    return {"enabled": enabled(), "listening": listening, "port": port,
            "urls": [f"http://{a}:{port}" for a in addresses()] if listening or enabled() else []}


def restart(host, port, delay=1.0):
    """Start this server again on `host` (after the reply has been sent)."""
    def go():
        time.sleep(delay)
        os.closerange(3, 4096)        # the listening socket is inheritable (werkzeug): free the port for the new run
        os.execv(sys.executable, [sys.executable, "-m", "app.server", "--port", str(port), "--host", host])
    threading.Thread(target=go, daemon=True).start()


@bp.route("/api/share", methods=["GET", "POST"])
def share():
    if request.method == "POST":
        on = bool((request.get_json(silent=True) or {}).get("enabled"))
        config.save_settings({"share_on_network": True if on else None})
        restart(host_for(on), current_app.config.get("PORT", 5050))
        return jsonify({**status(), "enabled": on, "restarting": True})
    return jsonify(status())
