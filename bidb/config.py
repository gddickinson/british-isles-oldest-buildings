"""Project-wide settings: paths, cutoff year and external endpoints."""
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"          # small committed files (curated research, overrides, build info)
DB_NAME = "british_isles_buildings.sqlite"
DEFAULT_CACHE_DIR = DATA_DIR / "cache"
DEFAULT_DB_PATH = DATA_DIR / DB_NAME
# Machine-specific settings (git-ignored), written by the GUI's Settings page:
#   {"cache_dir": "/Volumes/MyDrive/UK_BUILDINGS_DATA/cache", "db_dir": "...", "chrome": "..."}
SETTINGS_FILE = ROOT / "settings.json"


class DataLocationMissing(RuntimeError):
    """A configured data folder is not available (e.g. its external drive is unplugged)."""


_settings = {"mtime": None, "value": {}}


def load_settings():
    """settings.json as a dict (re-read when the file changes)."""
    try:
        mtime = SETTINGS_FILE.stat().st_mtime
    except OSError:
        return {}
    if mtime != _settings["mtime"]:
        try:
            _settings["value"] = json.loads(SETTINGS_FILE.read_text())
        except ValueError:
            _settings["value"] = {}
        _settings["mtime"] = mtime
    return dict(_settings["value"])


def save_settings(values):
    """Merge values into settings.json (None removes a key); written atomically."""
    cur = load_settings()
    cur.update(values)
    cur = {k: v for k, v in cur.items() if v is not None}
    tmp = SETTINGS_FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(cur, indent=2))
    os.replace(tmp, SETTINGS_FILE)
    return cur


def cache_dir():
    """Folder of downloaded API responses and map sources (data/cache unless moved)."""
    v = load_settings().get("cache_dir")
    return Path(v) if v else DEFAULT_CACHE_DIR


def db_path():
    """The SQLite database (data/ unless moved)."""
    v = load_settings().get("db_dir")
    return Path(v) / DB_NAME if v else DEFAULT_DB_PATH


def require_locations():
    """Stop early (before any download) when a configured data folder is unavailable, so a build
    never silently starts a fresh cache on the internal drive while the external drive is unplugged."""
    for key, path in (("cache_dir", cache_dir()), ("db_dir", db_path().parent)):
        if key in load_settings() and not path.is_dir():
            raise DataLocationMissing(
                f"The data folder {path} is not available (is the drive plugged in?). Plug it in, "
                f"or choose another location on the Settings page / edit {SETTINGS_FILE.name}.")


# Resolved once per process for the command-line tools; the web server calls the functions.
CACHE_DIR = cache_dir()
DB_PATH = db_path()

# Buildings whose earliest recorded construction date is before this year are included.
CUTOFF_YEAR = 1500

USER_AGENT = ("BritishIslesOldestBuildingsDB/1.0 "
              "(https://github.com/gddickinson/british-isles-oldest-buildings; python-requests)")
SPARQL_URL = "https://query.wikidata.org/sparql"
WIKIDATA_API = "https://www.wikidata.org/w/api.php"
WIKIPEDIA_API = "https://en.wikipedia.org/w/api.php"
POSTCODES_API = "https://api.postcodes.io"
COMMONS_FILEPATH = "https://commons.wikimedia.org/wiki/Special:FilePath/"
COMMONS_FILE_PAGE = "https://commons.wikimedia.org/wiki/File:"

CURATED_LIST_PAGE = "List_of_oldest_buildings_in_the_United_Kingdom"
# Curated Wikipedia lists merged into the database (rows flagged as "notable")
CURATED_LIST_PAGES = [CURATED_LIST_PAGE, "List_of_oldest_buildings_in_Scotland"]

# Wikidata anchors
Q_UK = "Q145"
# Sovereign states / Crown Dependencies of the British Isles -> display name for the nation facet
COUNTRIES = {"Q145": "United Kingdom", "Q27": "Republic of Ireland", "Q9676": "Isle of Man",
             "Q785": "Jersey", "Q25230": "Guernsey"}
# Designations whose items are included even without an inception date (all are historic sites)
UNDATED_DESIGNATIONS = {"Q893802": "national monument of Ireland"}
Q_IRISH_COUNTY = "Q179872"
Q_ARCH_STRUCTURE = "Q811979"
Q_BUILDING = "Q41176"
NATIONS = {"Q21": "England", "Q22": "Scotland", "Q25": "Wales", "Q26": "Northern Ireland"}
