"""Sharing the app on the home network: read-only for every computer but this one.

    GET  /api/share     {enabled, listening, port, urls}       (this computer only)
    POST /api/share     {"enabled": true|false} -> saved in settings.json, the app restarts on its new address
                        {"code": "new"|"off"}, {"trusted": "new"|"off"} -> share codes (no restart)

When sharing is on the server listens on every network interface (0.0.0.0) instead of 127.0.0.1, and
`guard` (run before every request) answers 403 to other computers for anything that changes something
(any method but GET/HEAD/OPTIONS) and for the pages and calls that belong to this computer (settings and
data locations, the folder browser, screenshots, setup, saving street maps for offline use).

Share codes (optional, Settings; roadmap S2): with a code set, another device must give it once (the address
with ?code=..., or the form shown instead of a page) before it sees anything; a cookie remembers it. A second,
"trusted" code gives that device full access, as if it were this computer.
"""
import hmac
import ipaddress
import os
import secrets
import re
import socket
import subprocess
import sys
import threading
import time

from flask import Blueprint, current_app, g, jsonify, request

from bidb import config

bp = Blueprint("lan", __name__)
SAFE = {"GET", "HEAD", "OPTIONS"}
LOCAL_ONLY = re.compile(r"^/(api/settings|api/screenshot|_shot|api/setup|setup|api/share|api/street_tiles)(/|$)")
MESSAGE = "Read-only: changes can be made only on the computer running the app."
COOKIE = "bidb_share"
OPEN = re.compile(r"^/(static/|sw\.js$|favicon)")       # what the code form itself may need
ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"            # no 0/O or 1/I
FORM = """<!doctype html><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Share code</title><style>body{font:16px system-ui,sans-serif;max-width:22rem;margin:15vh auto;padding:0 16px;
color:#222;background:#faf8f3}input,button{font:inherit;padding:.5rem;margin:.3rem 0;width:100%;box-sizing:border-box}
@media (prefers-color-scheme:dark){body{color:#eee;background:#1d1c1a}}</style>
<h1>British Isles Oldest Buildings</h1><p>{message}</p>
<form method="get"><input name="code" autocomplete="off" autocapitalize="characters" placeholder="Share code" autofocus>
<button>Open</button></form>"""


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


def new_code():
    return "".join(secrets.choice(ALPHABET) for _ in range(6))


def _same(given, code):
    return bool(given and code) and hmac.compare_digest(given.strip().upper().encode(), code.encode())


def access(local, given, settings):
    """'full' (this computer, or a device that gave the trusted code), 'read', or None (a share code is needed)."""
    if local or _same(given, settings.get("share_trusted_code")):
        return "full"
    code = settings.get("share_code")
    if not code or _same(given, code):
        return "read"
    return None


def full_access():
    """This request may do whatever this computer may (pages then show their controls)."""
    return getattr(g, "share_access", None) == "full"


def guard():
    typed = request.args.get("code")
    level = access(is_local(), typed or request.cookies.get(COOKIE), config.load_settings())
    g.share_access = level
    if typed and level and not is_local():
        g.share_cookie = typed.strip().upper()
    if level is None and not OPEN.match(request.path):
        if typed:
            time.sleep(1)                        # a wrong code: slow guessing down
        if request.path.startswith(("/api/", "/export")):
            return jsonify({"error": "A share code is needed: open the app's address in a browser first."}), 401
        msg = "That code is not right." if typed else \
            "Ask the person running the app for its share code (their Settings › Share on my home network)."
        return FORM.replace("{message}", msg), 401
    if blocked(request.method, request.path, level == "full"):
        return jsonify({"error": MESSAGE}), 403
    return None


def remember(response):
    """after_request: keep a share code given in the address for later visits."""
    code = getattr(g, "share_cookie", None)
    if code:
        response.set_cookie(COOKIE, code, max_age=365 * 86400, samesite="Lax", httponly=True)
    return response


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
    s = config.load_settings()
    return {"enabled": enabled(), "listening": listening, "port": port,
            "urls": [f"http://{a}:{port}" for a in addresses()] if listening or enabled() else [],
            "code": s.get("share_code"), "trusted": s.get("share_trusted_code")}


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
        body = request.get_json(silent=True) or {}
        codes = {name: new_code() if body[key] == "new" else None
                 for key, name in (("code", "share_code"), ("trusted", "share_trusted_code")) if key in body}
        if codes:                                # a new code or none: no restart needed
            config.save_settings(codes)
            return jsonify(status())
        on = bool(body.get("enabled"))
        config.save_settings({"share_on_network": True if on else None})
        restart(host_for(on), current_app.config.get("PORT", 5050))
        return jsonify({**status(), "enabled": on, "restarting": True})
    return jsonify(status())
