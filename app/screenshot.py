"""Screenshots of the app's pages with headless Chrome — for the GUI's "Save screenshot", the
README figures and checking layouts from the command line.

    python -m app.screenshot /map out.png [--width 1280 --height 800 --scale 2 --theme dark
                                           --click ".ml-toggle" --wait 6 --jpeg 80]

Pages are loaded inside /_shot, a frame of exactly the requested size (headless Chrome will not
make a window narrower than ~500 px, so phone widths need the frame), optionally after clicking
an element. Uses the running server when given --base, otherwise starts a temporary one.
"""
import argparse
import shutil
import socket
import subprocess
import tempfile
import threading
from contextlib import contextmanager
from pathlib import Path
from urllib.parse import urlencode

from bidb import config

CHROME_CANDIDATES = [
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Chromium.app/Contents/MacOS/Chromium",
    "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
    "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser",
    "google-chrome", "chromium", "chromium-browser", "microsoft-edge",
]
MIN_WINDOW = 520


def find_chrome():
    """Path of a Chromium-family browser (Settings can override it), or None."""
    custom = config.load_settings().get("chrome")
    for c in ([custom] if custom else []) + CHROME_CANDIDATES:
        if c and (Path(c).exists() or shutil.which(c)):
            return c if Path(c).exists() else shutil.which(c)
    return None


def frame_query(path, width, height, theme=None, click=None, wait=5):
    q = {"u": path, "w": width, "h": height, "wait": int(wait * 1000)}
    if theme:
        q["theme"] = theme
    if click:
        q["click"] = click
    return "/_shot?" + urlencode(q)


def capture(base, path, out, width=1280, height=800, scale=1, theme=None, click=None, wait=5,
            jpeg=None):
    """Write a PNG (or JPEG when jpeg=quality, via macOS sips) of `path` to `out`."""
    chrome = find_chrome()
    if not chrome:
        raise RuntimeError("No Chrome/Chromium/Edge found; set its path on the Settings page.")
    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    win_w = max(width, MIN_WINDOW)
    with tempfile.TemporaryDirectory() as prof:
        png = Path(prof) / "shot.png"
        subprocess.run([chrome, "--headless=new", f"--user-data-dir={prof}", "--disable-gpu",
                        "--hide-scrollbars", "--no-first-run", f"--window-size={win_w},{height}",
                        f"--force-device-scale-factor={scale}",
                        f"--virtual-time-budget={int((wait + 4) * 1000)}",
                        f"--screenshot={png}", base.rstrip("/") + frame_query(path, width, height, theme,
                                                                            click, wait)],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=120, check=False)
        if not png.exists():
            raise RuntimeError("Chrome did not produce a screenshot.")
        if win_w != width and shutil.which("sips"):   # the frame is centred: crop evenly to it
            subprocess.run(["sips", "-c", str(height * scale), str(width * scale), str(png)],
                           stdout=subprocess.DEVNULL, check=False)
        if jpeg and shutil.which("sips"):
            subprocess.run(["sips", "-s", "format", "jpeg", "-s", "formatOptions", str(jpeg), str(png),
                            "--out", str(out)], stdout=subprocess.DEVNULL, check=False)
        else:
            shutil.copy(png, out)
    return out


def _free_port():
    # Chrome refuses some ports (e.g. 5060/5061 SIP); ask the OS for an ephemeral one instead
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


@contextmanager
def temporary_server():
    from werkzeug.serving import make_server

    from .server import app
    import logging
    logging.getLogger("werkzeug").setLevel(logging.ERROR)        # no request log in the terminal
    port = _free_port()
    srv = make_server("127.0.0.1", port, app, threaded=True)
    t = threading.Thread(target=srv.serve_forever, daemon=True)
    t.start()
    try:
        yield f"http://127.0.0.1:{port}"
    finally:
        srv.shutdown()


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("path", help="page path, e.g. / or /map or /building/Q1049450?x=1")
    ap.add_argument("out", help="output .png (or .jpg with --jpeg)")
    ap.add_argument("--width", type=int, default=1280)
    ap.add_argument("--height", type=int, default=800)
    ap.add_argument("--scale", type=int, default=1, help="device pixel ratio (2 = retina)")
    ap.add_argument("--theme", choices=["light", "dark"])
    ap.add_argument("--click", help="CSS selector to click once the page has loaded")
    ap.add_argument("--wait", type=float, default=5, help="seconds to let the page load")
    ap.add_argument("--jpeg", type=int, help="save as JPEG at this quality (macOS sips)")
    ap.add_argument("--base", help="use a running server, e.g. http://127.0.0.1:5050")
    a = ap.parse_args()
    kw = dict(width=a.width, height=a.height, scale=a.scale, theme=a.theme, click=a.click, wait=a.wait,
              jpeg=a.jpeg)
    if a.base:
        print(capture(a.base, a.path, a.out, **kw))
    else:
        with temporary_server() as base:
            print(capture(base, a.path, a.out, **kw))


if __name__ == "__main__":
    main()
