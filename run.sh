#!/bin/sh
# Start the British Isles Oldest Buildings GUI.   ./run.sh [--data DIR] [--bundled] [--build] [--port N]
#   --data DIR   use the data in DIR (or DIR/UK_BUILDINGS_DATA): database and/or download cache; a new
#                cache folder is made there if it has none (saved in settings.json for next time)
#   --bundled    download (GitHub release) and unpack the bundled database if there is none yet
#   --build      build the database in this terminal first (otherwise the setup page offers it)
# Without a database the app opens on its setup page: bundled database, existing data, or a fresh build.
cd "$(dirname "$0")" || exit 1
PORT=${PORT:-5050}; DATA=; BUNDLED=; BUILD=
while [ $# -gt 0 ]; do
  case "$1" in
    --data) DATA=$2; shift 2 ;;
    --port) PORT=$2; shift 2 ;;
    --bundled) BUNDLED=1; shift ;;
    --build) BUILD=1; shift ;;
    -h|--help) sed -n 2,7p "$0"; exit 0 ;;
    *) echo "Unknown option: $1 (see ./run.sh --help)"; exit 2 ;;
  esac
done
[ -d .venv ] || { python3 -m venv .venv && .venv/bin/pip install -q -r requirements.txt; } || exit 1
PY=.venv/bin/python
if [ -n "$DATA" ]; then $PY -m bidb.setup data "$DATA" || exit 1; fi
# a configured folder on a drive that is not plugged in: stop before anything is created
$PY -m bidb.setup check || exit 1
if [ -n "$BUNDLED" ]; then $PY -m bidb.setup unpack || exit 1; fi
if [ -n "$BUILD" ]; then $PY -m bidb.build || exit 1; fi
echo "Open http://127.0.0.1:$PORT"
exec $PY -m app.server --port "$PORT"
