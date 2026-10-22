# Session log

## 2026-10-19 — initial build
- Goal: database of the UK's oldest buildings with a user-friendly GUI.
- Sources chosen: Wikidata (UK items, inception < 1500, class ⊂ architectural structure),
  Wikipedia "List of oldest buildings in the United Kingdom" (171 curated rows, flagged "Notable"),
  Wikipedia intros + lead images, Wikimedia Commons images (P18), postcodes.io reverse geocoding
  for nearest postcode / parish / district / county.
- Built `bidb/` pipeline (cached HTTP, SQLite + FTS5) and `app/` Flask GUI (gallery, table, map,
  detail modal, facets, CSV export).
- Fixes after first build: excluded 3,754 Wikidata "manor estate" land-holding items; stopped
  using P576 for status (it records the Dissolution for abbeys); added Wikipedia's Scotland list
  (header-aware table parser, {{circa}}/{{sort}} templates); name fallback for generic types.
- Result: see data/build_info.json; 5,7xx records (~290 on curated lists), 5,632 with coordinates, 5,404 with images,
  3,363 with Wikipedia intros. England 5,044 · Wales 341 · Scotland 265 · NI 26 · unknown 32.
- Verified the GUI with headless Chrome screenshots (gallery, table, map, detail page).
- Known gaps: Wikidata items without an inception date are missing (e.g. Westminster Hall);
  Scotland/NI under-represented; categories are keyword rules.

## 2026-10-19 — extended to the British Isles
- Scope now UK + Republic of Ireland + Isle of Man + Jersey + Guernsey (Wikidata P17 in
  `config.COUNTRIES`). Irish National Monuments (Q893802) included even without inception dates.
- Renamed package `ukb` → `bidb`, DB → `data/british_isles_buildings.sqlite`, GUI titles,
  CSV name, user agent. Project folder kept as `UK_buildings` (venv has absolute paths).
- New fields: Irish county (P131 chain → county of Ireland), Irish NM / SMR / NIAH IDs with links;
  new categories (round tower, ringfort, Irish tomb types, high crosses); Irish heritage grades.
- GUI default port changed 5000 → 5050 (macOS AirPlay Receiver occupies 5000).
- Result: 6,465 records — England 5,044 · Republic of Ireland 751 · Wales 341 · Scotland 262 ·
  NI 27 · Guernsey 3 · Isle of Man 3 · Jersey 2 · unknown 32. 6,384 with coordinates, 6,047 with
  images, 289 on curated lists, 536 undated (mostly Irish National Monuments such as Newgrange,
  Glendalough and the Rock of Cashel, whose Wikidata items have no inception date).
- Committed and pushed to a private GitHub repo (gddickinson/british-isles-oldest-buildings).

## 2026-10-19 — dates for undated (mostly Irish) monuments
- New build stage `date_fill.py`: 536 undated records → 334 dated from Wikipedia article text or
  infobox (evidence sentence stored), 73 typological estimates (`typology.py`), 129 still
  unrecorded. Some newly dated items fell after the 1500 cutoff and were dropped → 6,377 records.
- Text mining rules (`date_mining.py`) refined against spot checks: building sentences beat
  founding sentences; skip earlier-site / lifespan / relic / kingdom contexts; century ranges keep
  the first century; specific dates beat period words (Newgrange: "around 3100 BC").
- New columns `date_confidence`, `date_evidence`; "Date basis" facet; "≈" marker in GUI.
- Known imperfections: some dates refer to the site's first fortress/monastery rather than the
  surviving fabric (e.g. Rock of Cashel → 5th-century fortress); evidence is shown for checking.

## 2026-10-19 — GUI features 1-14, history, more categories, oldest of each type, hosted version
- Research subagents wrote `data/curated/history.json` (14 periods, 120 sourced events) and
  `data/curated/oldest_by_type.json` (48 types, 252 examples with claimed vs evidence dates).
- Categories expanded to 31 (`bidb/categories.py`) incl. public house/inn, hotel, school, library,
  almshouse/hospital, theatre, prison, railway, lighthouse, mill, bank, post office, market/shop,
  synagogue/mosque/meeting house; 8 colour groups (validated CVD-safe palette).
- New build stage `oldest_types.py`: per-type Wikidata queries (oldest 12 per type, only pre-1900
  accepted) + research merge (`postprocess.py`); research links to town articles are kept text-only.
  Researched claim replaces Wikidata date when Wikidata is >50 years later (e.g. Smock Alley).
- Date mining fixes: infobox `date` field dropped (photo dates), anniversaries skipped, wide
  ranges / period fields rank below specific dates, type estimate preferred over period-only text.
- App split into blueprints (api, tools, pages). Features: URL state + copy link, timeline view,
  colour-coded map + legend + map-area filter, nearby, date-basis badges, favourites/trip planner
  with route optimiser and GPX/KML, near place/postcode/me, compare, statistics dashboard,
  Commons galleries, corrections (`data/overrides.json`), gaps report, rebuild from GUI with diff.
- Pages: History, Oldest by type, Statistics, Trip planner, Compare, Data quality.
- Static export (`app/static_export.py` → dist/) for hosting as an Artifact: browser-side API
  (`static_api.js`), coastline basemap from Natural Earth (world-atlas 2.0.2), ~1,200 embedded
  thumbnails (external images are blocked in the artifact sandbox).
- Result: 6,950 records (658 oldest-of-type).

## 2026-10-19 (evening) — places, people, landmarks, registers
- New places layer (`places` table, Places page, catalogue map overlay): battles and sieges,
  archaeological sites, holy wells, hill figures, Roman roads, deserted villages, shipwrecks,
  registered parks and gardens, notable trees, industrial sites, finds and hoards, objects kept in
  buildings, commemorative plaques, and located history events. 58,360 places.
- Official registers (tested endpoints; see README): Historic England, HES, Cadw, NI HED, Irish SMR
  (selected classes); 32,536 added, 23,962 merged into Wikidata places/buildings at the same site.
  NIAH pre-1500 buildings (107) added to the catalogue. Jersey HER not used (no licence), Guernsey and
  Isle of Man registers not machine-readable; Open Plaques bulk API down (plaques from Wikidata).
- Landmarks (any date): Grade I, Category A, NI Grade A, World Heritage, widely known structures
  (>= 20 Wikipedia languages; settlements/streets filtered out), Crown Dependency heritage.
  2,528 early monuments with a photo/article joined the catalogue. Catalogue: 22,057 records.
- People page: 11,927 people, 14,766 links (buried/lived/born/died here, architect, founder,
  owner, commissioned, commemorated, took part); "named after" only for people born after 1000.
- History page map: 77 of 120 events placed (source article coordinates or
  data/curated/history_places.json).
- Periods after 1603 split into Stuart / Georgian / Victorian / Modern (13-step ramp).
- Fixes: overseas-territory records (Gibraltar, Falklands, Cyprus) removed by a land test;
  non-English label fallback for unlabelled items; type-based date estimates for monuments.
- Database committed gzipped (125 MB raw > GitHub limit). Static export now in <=9 MB shards;
  artifact republished (two publishes, version 4).
- Known gaps: ~10,300 landmark records have no construction date (England's register has none);
  people links are Wikidata's and include occasional errors (e.g. Joan of Arc "buried" at Winchester).

## 2026-10-20 — detailed offline map, references, photos, outlines, plans, historic maps
- Offline vector map (`app/basemap_build.py`, `static/basemap.js`): counties/council areas, national
  parks & AONBs, rivers & lakes, major roads, railways, ~46,700 cities/towns/villages, ~19,700
  landscape names, airports (~6.4 MB). Layer switcher on every main map; local GUI falls back to it
  when the online street map fails. New Map page (`/map`) with building groups, place layers and
  an offline town finder.
- References: Wikidata statement references for dates/designations/coordinates on 18,144 records;
  per-record "Sources & references" box; date check (Corroborated 1,932 / Referenced 3,842 /
  Single source 5,568 / Conflict 468 / Not dated 10,247) with a facet and a Data quality gap.
- Research files checked against their cited sources (`bidb/verify_research.py`): 303 of 372
  claims confirmed, 66 year not found in source, 3 sources unreachable (Data quality page,
  badges on the History page).
- Photos: Commons geosearch found 3,907 photos for 4,720 records without one (905 still missing).
- Outlines: 10,616 OSM building outlines (by wikidata tag); 236 Wikidata floor plans (P3311),
  shown on detail views and laid over the map (approximate fit to the outline).
- Historic maps: 14 layers (NLS OS six-inch/one-inch/Old Series/Bartholomew/Roy/Ireland/Isle of Man/
  Channel Islands, Gough Map, four Rumsey atlas maps via Allmaps) + 153 NLS town plans; 9 layers
  bundled as low-zoom WebP tiles (17 MB) for the hosted copy.
- Data fixes: non-building "widely known" landmarks removed; saints' "named after" links limited;
  non-object items filtered; register periods use the first listed period; overseas places dropped.
- ROADMAP.md created for future work.

## 2026-10-20 (later) — register dates, Open Plaques, Settings / Help / Export, data on an external drive
- Dates for undated Scottish and Welsh monuments from the HES portal and Cadw full-report
  descriptions (`bidb/register_dates.py`, ~4 h first fetch, cached): 5,300 records dated, evidence kept.
  Date mining ignores units (acres, metres, "N years old") and, new, dates after comparison words
  ("resemble", "modelled on", "inspired by", "elsewhere"): Rollright Stones had "c. 4800 BC" from
  a sentence about Danube long houses, The Shard "18th century" from Canaletto.
- Places: Open Plaques bulk API (19,756 plaques; merged with Wikidata plaques within 25 m) →
  77,729 places. People search in the catalogue box; references for people links and places.
- Maps: canals, National Trails layer, parks by designation, William Smith 1815, "historic maps of
  this place" from 4,436 Allmaps maps. Commons "Plans of" floor plans (+29). Floor plans load on
  demand in the hosted copy.
- GUI: top bar (⌘K quick search, Export, Help, theme, Settings), keyboard shortcuts, Settings page
  (appearance, defaults, recently viewed, backup/reset, **data location mover**, screenshot browser),
  Help guide with figures, exports CSV/JSON/GeoJSON/KML for buildings/places/people, screenshots
  (`python -m app.screenshot`; GUI Export menu), print styles. README rewritten with figures
  (`docs/make_figures.py`). Tests in `tests/`.
- Data location: `settings.json` (git-ignored) points the cache at
  an external drive (moved with the app's own mover: 25,974 files,
  1.92 GB, verified, old copy removed). Database stays on the
  internal drive (USB HDD is slow for random reads). Builds stop with a message if the drive is unplugged.
- Full cached rebuild: 22,046 records; date basis Recorded 8,084 / register 5,304 / Wikipedia 2,427 /
  type estimate 1,521 / not recorded 4,629; 10,506 outlines; 4,067 photos found by location.
- `images_extra places` stopped at 1,620 of 17,566 (resumable). Next: pronunciations task (ROADMAP).

## 2026-10-20 (evening) — pronunciations
- New build stage `python -m bidb.pronunciations` (also run by bidb.build): `pron_parse` reads the
  opening of each Wikipedia article (`{{IPAc-en}}`/`{{IPA-cen}}`, `{{IPA|xx}}`, `{{respell}}`,
  `{{langx}}` native names, footnotes, "locally"/US qualifiers, Irish dialects); `pron_sources`
  fetches openings (per-title store `<cache>/wiki_leads.json`, so reruns take seconds) and Wikidata
  P443 recordings / P898 IPA (languages of the isles only); towns from Wikidata P131.
- Result: 3,911 rows (2,050 IPA, 683 respellings, 1,141 recordings) for 613 buildings, 175 places,
  481 people and 1,798 towns; 19,000 records lie in a town with a pronunciation. Wikipedia rarely
  gives a building's pronunciation (566 of 8,747 building articles have any such template), so town
  lines carry most of the coverage. Varieties: English 1,680, Welsh 1,028 (705 recordings, mostly
  Lingua Libre / National Library of Wales), Irish, Cornish, Scottish Gaelic, Scots, Manx, local,
  British/American English, Shetland Scots, Jèrriais, older languages.
- GUI: line under names in detail views (▶ plays the Commons file, MP3 fallback for Safari),
  Pronunciation page (variety chips, search, export CSV/JSON), Data quality coverage + hard names
  without one, Settings toggles, Help section; hosted copy reads `data/pron.json` (not yet
  re-exported/republished).
- Parser fixes found on real data: infobox bold text, footnote pronunciations, partial alternatives
  ("-fahst"), foreign words in running text, etymologies ("from Latin camera"), second bold names,
  "also known as", person names (article title instead of birth name).

## 2026-10-20 (night) — hosted copy, Wiktionary pronunciations, native-name search, date review
- Hosted copy re-exported and republished (artifact version 12, 129 files, four publishes under
  64 MB). Fixed: historic tile packs were missing from the export after the cache moved to the external drive
  (`static_export` now reads `cache_dir()`).
- Places photo search restarted in the background (`images_extra places`, 36,957 places incl.
  Open Plaques; ~29 h, resumable; log `runs/images_places_2026-10-20.log`).
- Pronunciations: Wiktionary town entries (`bidb/pron_wiktionary.py`) with accent labels from the
  isles only (RP, Northern/Southern English, Scottish, Welsh north/south, Yorkshire, Scouse …):
  5,520 rows; 21,642 records lie in a town with a pronunciation. Catalogue search finds buildings by
  their Welsh/Gaelic/Irish names (`buildings_fts.other_names`, 450 buildings).
- Date conflicts reviewed (451 → 69): stricter check sentences (units, fittings, saints, finds,
  styles, later additions), parser fixes ("thirty-seventh century", "17th-century", decimals),
  "Earlier origin" status (67), 56 reviewed corrections with evidence. Report: `docs/date_review.md`
  (also lists Wikidata dates to fix at source).

## 2026-10-20 (evening) — map layers, faster hosted copy, stories and tours
- Map: "Minor roads" (OSM secondary/tertiary, from zoom 9) and "Streams" (named, from zoom 11)
  layers, off by default, in 1° tiles of compact integer steps (`app/basemap_tiled.py`).
- Places search uses other-language names (148 places). Historic England list entries are behind a
  Cloudflare bot check, so the 3,195 undated English entries cannot be dated from them.
- Hosted copy first load 72 MB → 22 MB: thumbnails, detail-only fields and outlines on demand.
- Stories (`bidb/stories.py`, `stories_parse.py`, `stories_db.py`): 11,177 full articles fetched
  (20 per request, cached as plain sections, 67 MB); 1,904 stories for 1,326 records after
  tightening rules (artworks, modern crimes, sport, popular culture left out; preceding sentence
  kept when a story starts "She…"/"Eventually…").
- Tours (`bidb/tours.py`, `tour_plan.py`, `tour_route.py`): 164 tours (53 walks, 48 bike rides,
  63 drives), all routed via OSRM; shorter radii after the first run (rides 50–100 km, drives
  250–475 km were too long); names from the largest nearby town; Roman theme limited to Britain;
  ferry waits detected (Orkney).
- Tours page with ready-made tours and "Your tour" builder (replaces the trip planner; ☆ now works
  for places too); Stories page; Help, README (figures stories.jpg, tours.jpg), INTERFACE updated.
- Tests: 41 Python (stories, tours, hosted split, tile encoding) + JS prefs checks.

## 2026-10-20 (night) — further additions F1–N4
- Roadmap section "Further additions" added and worked through; items needing the user (Wikidata
  account, Historic England request, API keys for Logainm / dúchas.ie, PAS / Ancient Tree Inventory
  access, island registers, sharing the hosted copy) are listed with what is needed.
- Stories: register descriptions as a source, `story_rejects.json`, rules for sport/film/modern
  sentences (1,757 stories). Read-aloud stories and "Listen to the tour".
- New tables: `on_this_day` (17,649; Julian dates converted back), `timeline` (45,875 events for
  8,034 buildings), `visiting` (OSM opening hours, fee, operator for 1,067 records).
- Tours: elevation (OpenTopoData, ~every 500 m), 82 long-distance and pilgrim ways with day stages
  (245 tours in all), follow mode, share links, nearest stations (4,400 stations, map layer).
- Maps: historic counties (Historic County Borders Project), Ireland six-inch (NLS, two editions,
  32 counties each), lakes layer (download running), street detail saved for offline (Protomaps;
  central York 39 tiles), raw OSM cache slimmed by ~280 MB.
- Irish and Manx records of AD 43–410 relabelled "Iron Age".
- App: installable (manifest, service worker), accessibility pass, light places index for the
  hosted copy, quiz page, browser checks `python -m tests.ui_check` (20 pages pass), 44 unit tests.

## 2026-10-21 — date review, legends and literature, maritime, industrial and Victorian, new map layers
- Date conflicts 69 → 2 (9 corrections, 58 confirmations in `data/curated/date_confirmations.json`).
- `bidb/lore_places.py`: 98 haunted places, 81 places of legend (incl. curated Avalon, Lyonesse,
  Cantre'r Gwaelod, Camelot candidates), 116 literary settings → group "Legends & literature".
- `bidb/maritime.py`: 1,850 maritime places (harbours, docks, shipyards, lighthouses, lifeboat
  stations, museum ships, shipbuilders) → group "Maritime heritage".
- `bidb/era_places.py`: 7,700 Industrial Revolution sites (railways by opening date, mills, mines,
  canals…) and ~790 Victorian public buildings → "Industrial heritage" / "Victorian era".
- Tours: themes literary (with writers' homes and graves), maritime, industrial, Victorian: 298 tours.
- Map layers (OSM, tiled): lakes incl. big lakes mapped as relations (first run missed them: "out tags
  geom" drops relation members), walking routes, cycle routes, Roman roads, buried rivers; route
  relations clipped to tiles ("out geom(bbox)"), Overpass timeouts retried.


## 2026-10-21 (later) — installation, data location, jobs with progress, refresh (I1–I7)
- `run.sh`: checks configured data folders before anything else (no folder created on an unplugged
  drive); `--data DIR`, `--bundled`, `--build`, `--port`. Without a database the app opens on `/setup`
  (bundled database / existing data / build from scratch).
- `bidb/progress.py` + `app/jobs.py`: long jobs (build, photos, footprints, map layers, hosted export,
  package) run detached and report stages, items, downloads vs cache hits and an estimate from the
  last run's stage times (`runs/job_status.json`, `runs/stage_times.json`). Tested in a fresh copy:
  the job survived the GUI being killed and was picked up on restart; Stop works (SIGINT can arrive
  ignored when the GUI runs in the background, so jobs install their own handlers and are stopped
  with SIGTERM); a `kill -9`'d job shows "Stopped unexpectedly".
- `bidb/refresh.py`: rebuild with `--refresh-days N` and/or `--refresh wikidata,osm,…` (also in the
  GUI rebuild options); applies to `request_json`, Overpass and file downloads, and restarts the
  per-title Wikipedia stores.
- `bidb/setup.py`: `check`, `status`, `data DIR`, `unpack`, `package`. The old `/api/rebuild` is
  replaced by `/api/jobs`.
- `data/british_isles_buildings.sqlite-journal` no longer tracked.
- Roadmap: underground works (U1–U2) and historic war construction (X1–X3) added for later.
- Tests: 58 unit tests (14 new in `tests/test_jobs.py`), 20/20 pages.
- Photo search for places finished (24,917 on the first pass, 2,834 for the new maritime/era places);
  bundled database repackaged (57 MB); hosted copy re-exported and republished (versions 27–30;
  250 files, 243 MB; unchanged map, help and vendor files left as they were).
- Bundled database moved out of git into a GitHub Release (`db-2026-10-21`, 57 MB):
  `bidb/bundle.py` (`fetch` with `gh`/token and SHA-256 check, `release`), `data/bundled.json`
  committed; the setup page downloads it as a job with progress; `run.sh --bundled` and
  `bidb.setup unpack` fetch it when missing. Tested from a fresh copy (download 2 s, unpack 1 s).
  Old copies remain in git history (repository pack ~225 MB); rewriting history was not done.
- Fix: maps in pop-ups (catalogue, places, people) were grey or partly drawn for records without a
  building outline (e.g. Alan Stevenson House): the map was made while the pop-up was hidden and only
  the outline path resized it. `Basemap.attach` now watches every map's box (ResizeObserver) and
  redraws it on the same centre. Hosted copy updated (version 31).
- "🗺 Show on the map" on building and place detail views: the Map page opens at zoom 17 on the record
  with a ring and its name (`?lat&lon&z&mark`, places also `&places=<group>` to switch that layer on);
  on the Map page itself it closes the pop-up and flies there.
- Fix: the Map page showed grey instead of land and sea with the offline map: the saved-street layer
  (Protomaps) painted its flavour's background over every tile; background now off.

## 2026-10-21 (evening) — extensive GUI review
- New `tests/ui_review.mjs` (+ driver `tests/cdp.mjs`, Chrome DevTools Protocol, no dependencies): every
  page and its maps, pop-ups, search ranking, 14 interactions, all 19 offline layers, 9 overlays over the
  street map, online and dark backgrounds, all 17 historic maps + town plans, all 11 places layers, mobile
  widths, exports; JS errors and failed requests per check; screenshots. Final: 113/113 local,
  90/90 hosted copy (served from dist/).
- Bugs found and fixed:
  - ☰ Layers: ticking an overlay or switching background threw "save is not a function" (the
    "Save this area" button variable shadowed the save helper, since 96f8b5c) — layer choices did nothing.
  - Overlays were unavailable over the online street map; borders, parks, routes, trails, Roman roads,
    buried rivers and stations now draw over it too.
  - Gough and Smith historic maps blank: warper.wmflabs.org not responding; historic maps now fall back
    to the bundled tiles (new `/historic_tiles` route) after 8 s, with a note; others say the server is down.
  - Overlapping town plans darkened each other: opacity now on the historic pane.
  - Station / town labels overlapped: collision check reserves each label's width and height.
  - Searching ranked anything mentioning the words before the named record ("Mary Rose" → Capture of
    Roxburgh): name matches now come first (`db.name_rank`, static `nameRank`), chosen order within.
  - "Show on the map" ring now SVG so its pulse animates.
- Hosted copy version 33.
- Satellite background (local app): Esri World Imagery (max native zoom 18) with Esri's place and
  border labels; third choice in ☰ Layers and in Settings; overlays marked online draw over it; falls
  back to the offline map if its tiles fail. Review checks `background_satellite` and `_switch` added.

## 2026-10-21 (night) — going public
- LICENSE (MIT), DATA_LICENSE.md, CONTRIBUTING.md, CITATION.cff; Help credits for screenshots;
  README rewritten (current numbers, features, 22 figures from `docs/make_figures.mjs`, setup, data
  updates, how it works, testing, licences, caveats).
- `bidb/nation_geo.py` (build stage "Nations for places"): 31,287 of 31,291 places without a nation
  now have one (8,675 from Wikidata P131, the rest by location with a border rule).
- Tour hilliness: noise filter (3 m) and a 20 m floor; tours rebuilt (flat 106, gently rolling 54,
  hilly 41, very hilly 8).
- Personal drive and machine references removed; git history squashed to a single commit; database
  release recreated on it; repository topics added.

## 2026-10-21 (late night) — museums on the roadmap; underground, military heritage and museums built
- Roadmap: new section "Museums, galleries and collections" (MU1–MU4), placed after the war construction.
- U1–U2 `bidb/underground.py` (build stage after era_places) → places group "Underground" (2,237): tube,
  subway and metro stations (292) and closed "ghost" stations (24; Wikidata closing dates, with
  `still_open` overrides for Charing Cross and Wapping; note Wikidata Q55654238 means "in use"), tunnels,
  shelters and bunkers, caves, mines, ice houses, grottoes, catacombs, sewers;
  `data/curated/underground_sites.json` (38 notable works outside the queried classes). Existing places of
  these kinds move to the group with the new label (their kind stays, so their own stage can rebuild them).
  Map layer "Underground railways & tunnels" (OSM railway=subway and railway/canal/road tunnels, 1.4 MB).
- X1–X3 `bidb/military.py` → "Military heritage" (9,186): 32 Saxon burhs (`data/curated/burhs.json`, from
  the Burghal Hidage table), Martello towers, forts from 1500 (Device and Palmerston Forts named), batteries,
  barracks, pillboxes, radar and sound mirrors, 718 airfields, 83 POW camps, 7,095 war memorials. Map layer
  "Pillboxes, bunkers & trenches" (3,710 OSM points). GHQ Line has no coordinates on Wikidata.
- MU1/MU3 `bidb/museums.py` → "Museums & collections" (4,414; 588 more are catalogue buildings): museums by
  type (art, historic house, military, transport/maritime, science/industry), closed ones marked, libraries
  and archives; "Kept here" objects per museum (916 in 253 museums; 461 new "Object in a museum" places,
  attached to the building when the museum is in the catalogue); 112 finds link to their museum.
- Tour themes: Underground, Coastal defences, Military heritage, Museums & galleries. Colours g12–g14,
  icons, Help text, Places page subtitle.
- Tests: `tests/test_place_stages.py` (stage kind keys must not collide: each stage deletes its own kinds);
  ui_check pages for the new groups and museum views.
- Follow-on stages rerun: nations for 13,919 new places, stories 2,407 (was ~1,900), 344 tours (new: 10
  underground, 11 coastal defences, 9 military, 14 museums & galleries), visiting information for 2,423
  records (was 1,067), pronunciations. Places now 104,136.
- Fixes: tour titles for the new themes (KeyError; test added for every theme); `/places#<id>` links never
  opened their place (the page rewrote its URL before reading the hash) — older bug, fixed.
- Checks: 70 unit tests; ui_check 24/24 pages (test server on port 5051); ui_review layers + places 52/52.
- Published: pushed to GitHub; database release `db-2026-10-21-2` (62 MB; `data/bundled.json`); hosted copy
  re-exported and republished (versions 37–38, 25 changed files, 103 MB in two publishes). README updated.
- Not done: MU2 (Mapping Museums), MU4 opening hours beyond OSM, stop lines drawn as lines.

## 2026-10-21 (night, continued) — bridges, Mapping Museums, Domesday, paintings
- `bidb/place_stage.py`: the group stages (underground, military, museums, bridges) share query,
  subclass_items, rows_for and write (catalogue buildings stay; kinds of the other group stages are
  `protected` and never move). Refactor checked: same counts as before (1,849/401, 9,184/2, 4,366/48).
- B1–B2 `bidb/bridges.py` → "Bridges": 13,502 bridges on Wikidata by type; 12,688 new places, 334 regrouped,
  471 in the catalogue; tour theme (17 tours). Colour g15, icon, help.
- MU2 `bidb/mapping_museums.py`: Mapping Museums Data, September 2021 (Birkbeck, CC BY 4.0,
  doi:10.18743/DATA.00171, credit in DATA_LICENSE.md): 4,191 museums; 2,883 matched Wikidata museums
  (subject, governance, accreditation, size, opened/closed shown on their page), 566 catalogue buildings,
  742 added (122 closed).
- S1 `bidb/domesday.py` (in part): 17,742 records in one of 13,232 settlements with an OpenDomesday ID
  (Wikidata P3118); line in "Getting there"; `data/domesday.json` when hosted. Open Domesday's API returns 404,
  so no households/mills/landholders.
- S2 `bidb/depictions.py` + `static/then.js` (Wikidata part): 3,095 paintings, prints and drawings (before
  1950) of 898 buildings and places, repeated impressions of one print dropped; "Then" gallery in detail views
  (a list of links when hosted).
- S4 checked: Canmore has 320,000+ sites and no clear licence on the download; left for a decision.
- Follow-on stages rerun: stories 2,438, tours 362, pronunciations 7,732, visiting. Places 117,566.
- Checks: 77 unit tests; ui_check 26/26; ui_review places layers 15/15; static export reviewed (pages,
  pop-ups, places 42/42 after a rerun: one connection reset from the local test file server).
- Not published yet: GitHub push, hosted copy and database release wait for the user.

## 2026-10-21 (night, continued) — excavations and hoards; publish
- `bidb/digs.py`: 604 excavated sites on Wikidata (P793 archaeological excavation with dates, P4345 directors,
  P61 discoverers) and 205 Time Team digs (Wikipedia series pages; location, coordinates, year, summary) →
  group "Excavations" (540 new places) and table `excavations` ("Excavated:" line on 864 buildings and
  places; a Time Team dig within 300 m of a catalogue building counts for it). Tour theme "Archaeology & digs".
- `bidb/hoards.py`: Wikipedia's lists of hoards in Great Britain and Ireland, 102 hoards with find-spots (78 new,
  24 already Wikidata finds), period, year found, contents, museum; `museums.save_names` keeps a
  `museum_names` table so later stages can link finds to museums (163 linked).
- Portable Antiquities Scheme checked: finds.org.uk is behind a Cloudflare check; public find-spots are
  generalised (1 km / parish) by design. Left as a data request (ROADMAP D3).
- Follow-on stages rerun: places 118,184, stories 2,443, tours 368, paintings 3,111, Domesday 17,935 records.
- Fixes: excavation spans without an end year; hoard find-spot line breaks; "Year found" label;
  Wikipedia/Mapping Museums sources linked as "Source".
- `places_geo.json` (hosted light index) reached 17 MB, over the artifact's 16 MB per-file limit: labels and groups
  now stored once and indexed, coordinates to 5 decimals → 10.8 MB (`app/static_places.py`, `static_places.js`).
- Published: GitHub (main), database release `db-2026-10-21-3` (69 MB), hosted copy version 39 (39 changed files,
  61 MB, one publish). Static review 27/27.



## 2026-10-21 (late) — research track started
- R0 `data/curated/evidence.json` + `bidb/evidence.py` (validate, `--check` re-fetches each source and looks for the
  exact quote, `data/evidence_check.json`), `/api/evidence`, `static/evidence.js` (Evidence in detail views, list on
  the Data quality page), hosted export `data/evidence.json`; `tests/test_evidence.py`.
- R1 Althorp: c. 1508 kept (Historic England list entry 1356626 via British Listed Buildings; Wikipedia's "1688"
  rests on Jones 1829). Hadlow Castle: corrected from Wikidata's 1852 to late C18 house / tower 1838–40 (list entry
  1070451). 6 of 6 quotes found by the checker. Date checks: no conflicts left (Reviewed 125).
- R2 first batch: research entries whose year was not found in the cited source. `verify_research` now counts a
  researched claim (evidence.json `research` key, all quotes found) as "evidenced". 25 claims added (32 quotes,
  all found); corrections in `oldest_by_type.json` (Royal Hospital Kilmainham 1679–1687, Lancaster Castle prison
  1196, Winchester City Mill 1744) and `history.json` (brochs c. 300 BC). Verification: confirmed 306,
  evidenced 20, year-missing 42, unreachable 4 (was 303 / 0 / 66 / 3).

## 2026-10-21 (late, continued) — research track R2
- All 69 research entries whose year was not in the cited source reviewed against full articles, listing texts
  (British Listed Buildings reproductions of NHLE / HES descriptions, HES scheduling SM90022) and a primary source
  (Tacitus, Agricola 24, Project Gutenberg 7524). evidence.json: 71 claims, 85 quotes, all found by the checker;
  51 kept, 12 corrected, 8 open. Corrections in oldest_by_type.json / history.json; 12 sources replaced.
- Verification: confirmed 325, evidenced 38, year-missing 9, unreachable 0 (start of the track: 303 / 0 / 66 / 3).
- `oldest_types.refresh_claims` rewrites catalogue "oldest of its type" notes from the research file (246 notes);
  corrected dates reach the catalogue on the next build.
- Mistake caught and fixed: a wrong list-entry number (Pharos) and an over-generous "kept" verdict (Glenturret).


## 2026-10-21 (night) — catalogue dates, R2b, R3 first pass
- Catalogue dates follow the research file without a rebuild: `refresh_claims` also rewrites research-sourced dates
  (71) with regional periods; reviewed date corrections for Brixworth (late 8th/early 9th c.), Castle of Old Wick
  (14th c.), Royal Hospital Kilmainham (1679–87), and from list descriptions Chichester Cross (c. 1500), Eling Tide
  Mill (mid C18), Ye Olde Fighting Cocks (C16), Bingley Arms (1738), Ye Olde Salutation Inn (C16), Merthyr Synagogue
  (1872–5) — 75 corrections in all.
- Build bug fixed: research examples whose Wikidata item is outside the structure classes but in the catalogue anyway
  (curated list) became a second "research-only" record (Knap of Howar, Skara Brae, Hanse House, Merton College
  Library, Chetham's, North Foreland, New Lanark, Jordans). `build.py` now annotates the existing record; the 8
  duplicates were merged in the current database.
- R2b: the 9 open claims settled (6 kept incl. Annals of Ulster U950.7 for the round towers, 3 corrected).
  `verify_research.source_text`: replies under 200 characters ("no scraping") count as unreachable.
- R3/R5: `bidb/listings.py` reads list descriptions (British Listed Buildings for England, both layouts; HES/Cadw);
  102 claims quoting them, plus Bede I.26 for St Martin's. 9 corrections where the listing contradicts a legend.
  evidence.json: 174 claims, 212 quotes (211 found; Ballycopeland's Geograph source refuses scripts).
  Verification: confirmed 322, evidenced 49, unreachable 1, year-missing 0. Tests: 84 pass.

## 2026-10-22 — research track R3 completed, R4
- R3 second pass: the 88 oldest-of-type examples without evidence researched (four parallel research agents; every
  quote re-checked by `bidb.evidence` before merging): NIAH (Ireland), the NI HED register, HES, Cadw/Coflein, Manx
  National Heritage, British Listed Buildings, Survey of London / VCH (BHO), institutions' own pages. 67 kept,
  18 corrected, 3 open (details in ROADMAP R3). Innerpeffray settled, Stokesay explained. Five researched examples
  listed under two types share their claim (cloned with the second research key).
- Catalogue dates: 16 R4 dates and 23 R3 dates added to `date_corrections.json` (114 in all) where the record's own
  date came from Wikidata or article mining and described something else (a weir, a founding firm, Syon House…).
- Build fix: research entries sharing one Wikipedia article (both Ewelme entries) — the second was dropped; it now
  becomes a research-only record. God's House, Ewelme added to the current database (22,039 records).
- R4: 40 early churches/monasteries against Bede, the Anglo-Saxon Chronicle, Lives of the Abbots, Annals of Ulster,
  Electronic Sawyer charters, Asser, VCH: 26 kept, 5 corrected, 9 open; 16 dates sharpened or corrected.
- `bidb/domesday_entries.py` (new; build stage after Domesday): Open Domesday place pages (they answer again; the
  Open Domesday id holds the grid reference) for the 2,717 settlements of churches, abbeys and cathedrals →
  table `domesday_entries`; the Domesday line in detail views now says "with a church and a priest (Sussex 1,1)" and
  links the place page (local and hosted). "church lands" are not churches (regex fixed, test).
- `bidb.evidence.check` paces the NI register (empty pages when asked quickly).
- Domesday entries: 2,717 settlements, 906 with a church or priest; of 296 religious records dated before 1086 in a
  Domesday settlement, 124 have a church or priest recorded there; 290 dated 1086–1199 sit where Domesday already
  records one. Shares kept ("0.5 church"); "church lands" and the notes' "1/4 church" not counted (tests).
- Evidence: 307 claims, 542 quotes, 541 found (Ballycopeland's Geograph source refuses scripts). Verification:
  confirmed 295, evidenced 76, unreachable 1. Tests: 86 pass; UI checks building_domesday (new), building_evidence,
  data_evidence pass.
