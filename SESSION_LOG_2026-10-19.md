# Session log — 2026-10-19 to 2026-10-20

Earlier entries of [`SESSION_LOG.md`](SESSION_LOG.md).

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

