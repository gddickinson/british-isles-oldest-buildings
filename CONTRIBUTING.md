# Contributing

Thank you for helping. Corrections to the data are as welcome as code.

## Fixing data
Most records come from **Wikidata**. If a date, location or type is wrong, the best fix is on
Wikidata itself (each record links to its item); it reaches this project at the next rebuild with
`--refresh wikidata`. For a fix that only makes sense here, open an issue with the record's name or
Wikidata id, what is wrong and a source. Reviewed date corrections live in
`data/curated/date_corrections.json` (each with evidence and a source).

## Reporting a problem
Open an issue with what you did, what you expected, what happened, and the page address (the app
keeps its filters in the URL, so the address usually reproduces it). A screenshot helps: Export →
Screenshot in the app.

## Working on the code
1. `./run.sh --bundled` gives you a working app with the bundled database in a minute or two.
2. Read `INTERFACE.md` first: it maps every module and how they connect.
3. Keep files under 500 lines; split a module before it grows past that.
4. Run the checks before a pull request:
   ```sh
   .venv/bin/python -m unittest discover tests      # unit tests
   node tests/ui_prefs_test.js                       # browser preference logic
   .venv/bin/python -m tests.ui_check --base http://127.0.0.1:5050   # every page loads
   node tests/ui_review.mjs --base http://127.0.0.1:5050             # full GUI review (maps, layers, …)
   ```
5. Update `INTERFACE.md` when you add or move a module, and the README / Help when a feature changes
   (`node docs/make_figures.mjs` regenerates the figures).

## Being kind to the data sources
The builder calls free public services (Wikidata, Wikipedia, Overpass, OSRM, OpenTopoData, the
heritage registers). Keep the rate limits and the disk cache in `bidb/http.py`, identify the app in
the user agent, and don't add parallel downloads. Respect each source's licence (`DATA_LICENSE.md`).
