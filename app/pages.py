"""HTML pages. Each page is a thin template; its data comes from the JSON API."""
from flask import Blueprint, abort, render_template, send_from_directory

from bidb import db, models3d
from bidb.config import ROOT

from .common import build_info, conn

bp = Blueprint("pages", __name__)
STATIC_MODE = False      # True when rendering the hosted static export


@bp.app_context_processor
def _globals():
    from flask import has_request_context
    from .lan import full_access
    # this computer (or a device with the trusted share code), not another one
    here = not STATIC_MODE and (not has_request_context() or full_access())
    return {"info": build_info(), "static_mode": STATIC_MODE, "this_machine": here,
            "can_edit": here and (ROOT / "data").exists(), "models3d": models3d.links(STATIC_MODE)}


@bp.route("/")
def index():
    return render_template("index.html", stats=db.stats(conn()), facets=db.FACETS, page="catalogue")


@bp.route("/building/<path:bid>")
def building_page(bid):
    b = db.get_building(conn(), bid)
    if not b:
        abort(404)
    return render_template("detail.html", b=b, page="catalogue")


@bp.route("/sw.js")
def service_worker():
    """The offline service worker, served from the root so it may cover every page."""
    resp = send_from_directory(ROOT / "app" / "static", "sw.js")
    resp.headers["Cache-Control"] = "no-cache"
    return resp


@bp.route("/history")
def history():
    return render_template("history.html", page="history")


@bp.route("/change")
def change():
    return render_template("change.html", page="change")


@bp.route("/oldest")
def oldest():
    return render_template("oldest.html", page="oldest")


@bp.route("/trades")
def trades():
    return render_template("trades.html", page="trades")


@bp.route("/stats")
def stats():
    return render_template("stats.html", facets=db.FACETS, page="stats")


@bp.route("/tours")
@bp.route("/trip")              # the old Trip planner is now "Your tour" on the Tours page
def tours():
    return render_template("tours.html", page="tours")


@bp.route("/quiz")
def quiz():
    return render_template("quiz.html", page="quiz")


@bp.route("/stories")
def stories():
    return render_template("stories.html", page="stories")


@bp.route("/compare")
def compare():
    return render_template("compare.html", page="compare")


@bp.route("/places")
def places():
    return render_template("places.html", page="places")


@bp.route("/map")
def explore_map():
    return render_template("map.html", page="map")


@bp.route("/people")
def people():
    return render_template("people.html", page="people")


@bp.route("/pronunciation")
def pronunciation():
    return render_template("pronunciation.html", page="pron")


@bp.route("/types")
def building_types():
    return render_template("types.html", page="types")


@bp.route("/things")
def things():
    return render_template("things.html", page="things")


@bp.route("/sky")
def sky():
    return render_template("sky.html", page="sky")


@bp.route("/stonehenge")
def stonehenge():
    return render_template("stonehenge.html", page="models",
                           m={"name": "Stonehenge", "record": "Q39671", "built_label": "As built (c. 2500 BC)",
                              "axis_label": "Solstice axis", "ghosts": "Mark lost stones (as built)"})


@bp.route("/models")
def models():
    """Every 3D model (roadmap SH3), built or still to come."""
    rows = [{**m, "ready": models3d.ready(m),
             "href": models3d.page_file(m) if STATIC_MODE else m.get("route", f"/model/{m['id']}")}
            for m in models3d.MODELS]
    from bidb.model_circles import known
    circles = [] if STATIC_MODE else sorted(({"id": k, **v} for k, v in known().items()), key=lambda c: c["name"])
    return render_template("models.html", page="models", models=rows, circles=circles)


@bp.route("/model/<mid>")
def model(mid):
    m = models3d.get(mid)
    if not m or m["id"] == "stonehenge" or not models3d.ready(m):
        abort(404)
    import json
    data = json.loads((models3d.OUT / f"model_{mid}.json").read_text())
    page = {"about": data.get("about", []), "built_label": data.get("built_label"), "lantern": data.get("lantern"),
            "axis_label": data.get("axis_label"), "ghosts": data.get("ghosts"), "labels_label": data.get("labels_label")}
    return render_template("model.html", page="models", m={**m, **page}, mid=mid)


@bp.route("/glossary")
def glossary():
    return render_template("glossary.html", page="glossary")


@bp.route("/data")
def data():
    return render_template("data.html", page="data")


@bp.route("/setup")
def setup_page():
    """First run: bundled database, existing data, or build from scratch (app/jobs_api.py)."""
    return render_template("setup.html", page="settings")


@bp.route("/settings")
def settings():
    return render_template("settings.html", page="settings")


@bp.route("/help")
def help_page():
    return render_template("help.html", page="help")


@bp.route("/help/img/<path:name>")
def help_image(name):
    """Screenshots in docs/img (shared with the README)."""
    from flask import send_from_directory
    return send_from_directory(ROOT / "docs" / "img", name)
