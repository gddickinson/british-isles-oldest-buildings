#!/bin/zsh
# Serve the static export (dist/, from `python -m app.static_export`) on the home network from an always-on
# machine (roadmap S3). The static copy needs no Python packages and no database: any web server will do.
#
#   ./serve_dist.sh                 serve dist/ here on port 8080 (every interface)
#   ./serve_dist.sh --port 9000
#   ./serve_dist.sh --to HOST       copy dist/ to HOST:~/worker/bidb_site/ (rsync over ssh) and serve it there
#                                   in the background (log: ~/worker/bidb_site/serve.log)
#   ./serve_dist.sh --stop HOST     stop the server on HOST
set -e
cd "$(dirname "$0")"
PORT=8080
HOST=""
STOP=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    --port) PORT="$2"; shift 2 ;;
    --to) HOST="$2"; shift 2 ;;
    --stop) STOP="$2"; shift 2 ;;
    *) echo "unknown option $1"; exit 1 ;;
  esac
done

if [[ -n "$STOP" ]]; then
  ssh "$STOP" 'pkill -f "http.server.*bidb_site" && echo stopped || echo "not running"'
  exit 0
fi

[[ -f dist/index.html ]] || { echo "No dist/: run .venv/bin/python -m app.static_export first"; exit 1; }

if [[ -z "$HOST" ]]; then
  echo "Serving dist/ on http://$(ipconfig getifaddr en0 2>/dev/null || hostname):$PORT (Ctrl-C stops)"
  exec python3 -m http.server "$PORT" --directory dist
fi

need=$(du -sk dist | cut -f1)
free=$(ssh "$HOST" "df -k ~ | tail -1 | awk '{print \$4}'")
if (( free - need < 150 * 1024 * 1024 )); then
  echo "Not copying: $HOST would have less than 150 GB free"; exit 1
fi
ssh "$HOST" 'mkdir -p ~/worker/bidb_site/dist'
rsync -a --delete dist/ "$HOST:worker/bidb_site/dist/"
ssh "$HOST" "pkill -f 'http.server.*bidb_site' || true; cd ~/worker/bidb_site && \
  nohup /usr/bin/python3 -m http.server $PORT --directory ~/worker/bidb_site/dist > serve.log 2>&1 &"
echo "Serving on http://$(ssh "$HOST" 'scutil --get LocalHostName 2>/dev/null || hostname -s').local:$PORT"
echo "Stop it with ./serve_dist.sh --stop $HOST"
