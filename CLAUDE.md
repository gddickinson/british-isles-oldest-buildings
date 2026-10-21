# British Isles Oldest Buildings

Project folder is still named `UK_buildings` (renaming it would break `.venv`); the package is `bidb`.

@INTERFACE.md

- Python env: `.venv/` (flask 3.0.3, requests 2.32.3). Run with `.venv/bin/python`.
- Rebuild data: `.venv/bin/python -m bidb.build` (cached; `rm -rf data/cache` for fresh data).
- Run GUI: `./run.sh` → http://127.0.0.1:5050
- Keep files under 500 lines; update INTERFACE.md and SESSION_LOG.md with structural changes.
