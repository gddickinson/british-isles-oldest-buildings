"""British Isles Oldest Buildings - Flask web GUI: python -m app.server -> http://127.0.0.1:5050

Blueprints: api (data JSON), export_api (CSV/JSON/GeoJSON/KML), places_api (places, people),
tools (geocode, images, edits), jobs_api (rebuild and other jobs, first-run setup), settings_api (data location, screenshots), pron_api
(pronunciations), pages (HTML).
"""
from flask import Flask

from .api import bp as api_bp
from .common import close_conn
from .export_api import bp as export_bp
from .jobs_api import bp as jobs_bp
from .pages import bp as pages_bp
from .places_api import bp as places_bp
from .pron_api import bp as pron_bp
from .settings_api import bp as settings_bp
from .stories_api import bp as stories_bp
from .street_api import bp as street_bp
from .tools import bp as tools_bp
from .tours_api import bp as tours_bp

app = Flask(__name__)
app.teardown_appcontext(close_conn)
for bp in (jobs_bp, api_bp, export_bp, places_bp, pron_bp, stories_bp, street_bp, tours_bp, tools_bp, settings_bp, pages_bp):
    app.register_blueprint(bp)


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=5050)
    ap.add_argument("--host", default="127.0.0.1")
    a = ap.parse_args()
    app.run(host=a.host, port=a.port, debug=False, threaded=True)
