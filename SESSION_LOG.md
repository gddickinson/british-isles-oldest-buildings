# Session log

Entries before 2026-10-21 are in [`SESSION_LOG_2026-10-19.md`](SESSION_LOG_2026-10-19.md).

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

## 2026-10-22 (afternoon) — R4b, tree-ring dates, sanity check, nature, graves, markets, works, infrastructure
- README updated and pushed (research results). Research agents (11 in all, every quote re-checked before merging).
- R7 sanity check of the 100 oldest records: 72 kept, 18 corrected (Avebury c. 2900 BC, Hembury, Chestnuts, Bryn
  Celli Ddu, Carrowkeel, Carrowmore, Knap of Howar c. 3300 BC…), 10 open; record problems in docs/date_review.md.
  Caerau kept at its Neolithic enclosure (consistent with Hembury and the Trundle).
- R4b manor houses: 19 of 30 corrected (Domesday manor dates given as house dates). Lives of Wilfrid and Guthlac.
- R6 `bidb/dendro.py` + `bidb/osgrid.py`: VAG Dendrochronology Database (ADS) matched to 592 buildings; 13 dates
  corrected from the timbers; "Tree-ring dated:" line in detail views (local and hosted, `/api/dendro/<id>`).
  Matching: the record's own distinctive words in the entry, or "town + kind" names; street names stripped; tests.
- R8 `bidb/oldest_lists.py`: researched lists nature (60), graves (75), trade (70), infra (72) → places, evidence
  claims (generated, read by `evidence.load`), the Oldest page (`/api/oldest_lists`, hosted `oldest_lists.json`),
  plus the earliest dated places per kind of the new groups (unchecked).
- New place stages `bidb/burials.py` (7,939 in "Graves & burial grounds") and `bidb/trade_works.py` ("Markets &
  trade" 7,511, "Infrastructure & utilities" 15,170, Industrial heritage now 12,334); `place_stage.direct_items`.
  Two new place-group colours (--g17…--g20). First burials run moved 217 archaeology places into graves; reverted
  and archaeology places now never move there.
- Date corrections: 164 in all. Places: 152,558 (was 118,184). Evidence: 714 claims, 1,312 quotes.
- GUI restarted for review on port 5050. Asked the user before opening it to the home network (it binds 127.0.0.1;
  jobs, settings and corrections would be open to every machine).

## 2026-10-22 (evening) — publish, sharing on the home network
- Hosted copy over the 256 MiB per-version limit (281 MB): place rows now leave out the label/group of their kind,
  the Wikidata id/address when they repeat the id and the source "Wikidata" (rebuilt in static_places.js), and
  extracts are trimmed to 400 characters → 250.7 MiB. VA55 CSV is Windows-1252 ("1672 ± 9", no U+FFFD).
  Published as versions 46–50 (old shards places_9/10 removed). DB release db-2026-10-22-2.
- Sharing (`app/lan.py`, `static/share.js`, Settings section, Help, README, `run.sh --lan`, `app.server --lan`):
  read-only guard for non-loopback clients (tests/test_lan.py, 6 tests; ui_check settings_share); restart by
  exec after closing inherited fds (werkzeug's socket is inheritable: "Address already in use" otherwise).
  Sharing is off; nothing was opened to the network during testing (test client and a loopback-only restart).

## 2026-10-22 — README and figures refreshed
- All figures in `docs/img` retaken (`node docs/make_figures.mjs`); new: `evidence.jpg` (Canterbury Cathedral:
  evidence, tree-ring dates, Domesday), `oldest_lists.jpg`, `places_graves.jpg`, `sharing.jpg`. Map layers now
  around York (Roman roads mapped there), tours on the Cambridge walk, jobs cropped (`clip` option). `setup.jpg`
  kept (needs a second copy with no database).
- Fixes seen in the figures: researched-list cards on the Oldest page squeezed into the photo column
  (`.ex.text`); Places summary named the new groups; rebuild job description; nation "Ireland" in the
  oldest lists → "Republic of Ireland" (10 places).
- README: new figures and captions, 20 place groups, research and tree-ring counts, 103 tests, sharing bullet.
  Help: oldest lists, evidence and sharing figures. Tests 103 OK; ui_check 35/35.

## 2026-10-22 — Sport and leisure; ten quizzes
- `bidb/sports.py` (build stage after trade_works): sports venues (subclasses of sports venue + lidos, baths,
  bowling greens, tennis courts) and clubs/teams (at their home ground, P115, when they have no coordinates;
  national teams left out), names refining loose classes (`refine`) → group "Sport & leisure" (5,495 places:
  2,126 football clubs, 333 rugby, 311 golf, 250 rowing/sailing, 204 racecourses and circuits, 139 GAA clubs…).
  `place_stage.query/rows_for` take a `coord` pattern. Group registered (place_kinds, render_places, static_places, --g21).
- Researched list `data/curated/oldest_sport.json` (76 entries, 8 categories; 51 kept, 15 open, 10 corrected),
  quotes checked: 141/141 after dropping 5 newspaper/club sources that refuse scripts and fixing one quote.
  `oldest_lists.run` now gives the researched age to places other stages keep (previously only regrouped ones).
  `python -m bidb.evidence --check --new` checks only claims the last check has not seen: 1,452 of 1,453 found.
- Quizzes: `app/quiz_api.py` (`/api/quiz`, `/api/quiz_pool`; `data/quiz.json` in the hosted copy),
  `static/quiz_kinds.js` (period, which is older, oldest of four, put in order, county, say the name, whose story,
  when did it happen, how old is it, mixed; easy/hard), `static/quiz.js` (menu, best per quiz and level, review).
  Story text is masked before escaping. Played every quiz at both levels in Chrome: no errors.
- Tests 108 OK (tests/test_sports.py); ui_check 40/40. README, Help, INTERFACE, figures updated.

## 2026-10-22 — Public institutions
- `bidb/institutions.py` (build stage after sports): subclasses of university/college, hospital/asylum/clinic,
  prison, courthouse, police station, fire/ambulance station, post office, town hall/government building,
  village hall/almshouse/workhouse/orphanage, school → group "Public institutions" (8,311 places). Schools: of
  ~29,800 on Wikidata only those founded before 1900 (George's choice; 1,113 kept). Registered as the 22nd group.
- Researched list `data/curated/oldest_civic.json` (80 entries; 46 kept, 26 open, 8 corrected: Ruthin School
  closed 2026, Barnes Cross pillar box 1859, Machynlleth Parliament House c. 1470, Southwell Workhouse…);
  207/207 quotes found at install; five true catalogue ids restored after the install script's name test.
  Evidence: 870 claims, 1,658 of 1,660 quotes found (Ballycopeland; Antrim courthouse's NI register page now
  returns the site menu, the other source holds).
- README, Help, INTERFACE, figure places_institutions; tests 110 OK, ui_check 42/42.

## 2026-10-22 — Release, hosted copy, README
- Database release db-2026-10-22-4 (81 MB). Hosted copy trimmed to 242 MiB (place descriptions and extracts
  300 characters, floor plans 480 px q55 WebP: 22 → 7 MB) and published as versions 52–53; static review
  22/22 and every quiz played on the static copy. The trimming is in the export only.
- Fixes found while redoing the figures: Wikipedia extracts with the IPA dropped ("(; born…", "()") tidied
  (`enrich.tidy_extract`, 495 texts fixed in the DB; tests/test_tidy_extract.py); the pronunciation guide
  showed duplicate rows (same name, variety and pronunciation from two records) and counted them in the
  variety chips (server and hosted); jargon in researched claims ("QID is the …") reworded.
- Figures: new catalogue_landmarks (hero), then (paintings), data_quality, pron_welsh; people (buried here),
  palette (with a search), detail (1000 px), setup (current, typical path), jobs (crop follows the scroll);
  `pronunciation.jpg` dropped. Chrome refuses ports 5060/5061: the setup copy runs on 5071.
- README rewritten: features with figures, getting started, a page-by-page guide, how it was made (pipeline,
  dates, research, Claude Code), how it is maintained (jobs, commands, releases, hosted copy, tests),
  sources, caveats. Checked rendered with GitHub's Markdown API: 29 figures, none broken; the database
  badge removed (the private repository's releases are invisible to shields.io).

## 2026-10-22 — N5 checks, hosted places index, wrecks, bus stops, old Welsh names, time slider
- N5 (`bidb/oldest_checks.py`, build stage after oldest_lists): 8,937 of 23,120 Wikidata dates in the six newer groups
  are only to the decade or century (precision via wbgetentities: the query service was rate-limited to 1 request/min
  during an outage); they now read "between 1800 and 1839" / "19th century" / "1830s" and are not candidates. Four
  research agents (and one extra round) reviewed the 422 candidates against Wikipedia, list entries (British Listed
  Buildings), NIAH and club histories: 283 kept, 92 corrected, 32 dropped, 15 open
  (`data/curated/oldest_places_review.json`); 375 claims with quotes, all found by `bidb.evidence --check --new`.
  Findings: market towns dated by settlement not charter; shops that are houses with later shopfronts; GAA grounds
  dated by rebuilds; Wikidata's classes miss the oldest hospitals/universities/almshouses (the researched lists have them).
- Hosted copy places index: location cells (`data/pcells/`, 1°×2°) + `places_index.json` + 16 id-hash shards;
  `places_geo.json` gone. Detail view ~1–2 MB instead of 18 MB; a place ~6 MB instead of 77. Static review 103/103
  after limiting cell requests to six at a time (Python's test server reset connections at 100).
- Share codes (S2, `app/lan.py`): code form / `?code=` + cookie; trusted code = full access (pages show controls).
  The auto-mode classifier refused a scripted edit of the access-control code; done with reviewed edits instead.
- National Scenic Areas: all 40 from the Scottish Government ProtectedSites layer (OSM had 2).
- Shipwrecks (`bidb/wrecks.py`): Canmore FORM='WRK' (3,768 after dropping obstructions) + Wreck Inventory of Ireland
  CSV (3,564 with positions); offshore ones take the nearest building's nation, far-Atlantic Irish ones Ireland.
- NaPTAN (`bidb/naptan.py`): 340,902 bus stops, 524 ferry terminals → table `stops`; `/api/stops`; hosted
  `stops.json` for catalogue buildings; "Getting there" shows 🚏 and ⛴️.
- Old Welsh place-name forms (`bidb/welsh_names.py`, RCAHMW WFS, 11,504 forms with a headname): 4,824 records linked
  (town, locality part or name within 10 km); detail line "Old forms of the name" (Chepstow: castellum Gwent 1069).
- Bike ride surfaces (`bidb/tour_surface.py`): Overpass `around` on the route in pieces of 40 points (long lines came
  back empty), nearest way every 200 m → % paved / unpaved / traffic-free.
- Through time (`static/time_slider.js`): year slider on the Map page with histogram, Play and era historic maps;
  places map rows now carry year_start (hosted cells too).
- `serve_dist.sh` (S3): serve dist/ here or `--to HOST` (free-space check); not started on the Mac mini.
- Checked and not done: OS Old Series full detail (NLS tiles stop at z9; MapTiler key), Saxton/Speed (no tiles),
  OSNI six-inch (NLS Ireland six-inch already covers NI), OS Open data (OSM covers it), CRT assets (no dates),
  Victorian listed buildings by date (register layers have none). Roadmap section "Time slider and change over time"
  added (T2 more historic maps, T3 dated network/change data, T4 texts: Gutenberg, Internet Archive, BHO, ADS).
- Photos and floor plans (`bidb/photo_search.py`): a first name-only search matched namesakes (Villa Park, Denver) and
  street maps; reverted (39 plans, 26 photos) and redone: plans only inside the building's own Commons category tree,
  photos found by name only when geotagged within 3 km.

## 2026-10-22 — Change over time (roadmap E1–E5)
- Year slider can be hidden (× / 🕰 Through time, remembered per browser).
- New roadmap section "People and environment through time" (E1–E5). Three research agents catalogued ~90 sources
  (people and settlements, climate and atmosphere, land, farming, industry and geology), checked every download URL
  and licence, and made tidy extracts (scratchpad, not in git). Curated into `data/curated/change/`: 50 openly
  licensed series from 32 sources and 32 dated events, each with its citation. Unverified figures in the event
  lists were checked (1665 bills of mortality 68,596; 1953 flood 307 dead in England) or reworded (1607 flood
  500–2,000, Storegga "about 8,150 years ago"; the 1740–41 famine percentage dropped).
- `bidb/change_series.py` → `app/static/data/change/series.json` (264 KB); `static/change_charts.js` (graphs),
  `change_panel.js` (Map page panel), `change_page.js` + `/change` page; DATA_LICENSE lists every source.
- Left out for licence: Bank of England millennium data (Broadberry et al.), Armagh, SILSO, Shennan sea-level points.
- The laptop disk was nearly full (1.6 GB free; not this project's files); removed old scratch copies (~0.6 GB).
- Next: E3 map layers (HYDE grids per period with the slider, GHSL, CORINE, geology, coalfields), E5 notes.
- E3 map layers: `bidb/remote_zip.py` reads single grids out of HYDE 3.2.1's 5.3 GB archive by range requests;
  `bidb/change_layers.py` crops popd and cropland for 29 dates (4000 BC–2017) and draws Mercator-row palette PNGs
  (58 maps, 132 KB); `bidb/change_geology.py` merges BGS (GB) and GSI/GSNI (Ireland) bedrock by period (2.1 MB)
  and the coalfields; `static/change_layers.js` adds the "Map layer" chooser to the panel. Checked in Chrome
  (people per km² at 1300 follows the slider; geology legend and sources).
- Plan search finished: 290 found, 38 reverted (museum objects, town prospects, French "premier plan", garden sign
  photos, plans of other buildings), 252 kept; `MAP_LIKE` extended. Bike surfaces for 55 of 56 rides.
- Hosted copy republished as version 59 (four batches; 333 files changed, 6 removed): 253 MiB, 479 files. To stay
  under the limits the HYDE maps are packed per variable (2 files, not 58), plans 420 px WebP q45, 1,100
  thumbnails. Static GUI review 103/103.

## 2026-10-23 — Change over time: the remaining layers (E3) and analysis notes (E5)
- E3: `bidb/change_rasters.py` draws seven more layers from grids prepared once with GDAL (script and README in
  `data/curated/change/layers/`; raw downloads in the scratchpad, not in git): built-up land 1975/2020 (GHSL),
  land cover 2000–2018 (CORINE, nine groups; the 1990 map has no Great Britain and is left out), tree cover from
  pollen in 1° squares (REVEALS, 25 windows), ancient woodland (England, Wales, Scotland's "ancient" classes; share
  of each cell), farmland grades (England), superficial deposits (GB), towns and cities by size 700–2000 (Buringh,
  dots). ~500 KB in all. The chooser groups layers "through time" and "the land"; time layers are hidden before
  they start; dots use an SVG renderer (the map's canvas did not paint new dots until it moved).
- Fixed: the Map page's "buildings begun per century" graph had no points, so the panel threw an error whenever it
  opened with that graph chosen.
- E5: two research agents wrote 19 notes with 50 quotes (Neolithic boom and bust, woodland clearance, Late Bronze
  Age, AD 536, medieval warmth and the Little Ice Age, building and plague, the Great Famine, the Black Death, the
  1690s in Scotland, 1740 in Ireland, Laki, the Irish Great Famine, coal and CO₂, Britain as first emitter,
  greenhouse gases since 1750, towns and smoke, the woodland low point, the 1952 smog, warming and sea level), both
  sides where scholars disagree. Each quote was checked against the fetched text; I re-fetched 17 and found 16 (the
  Ludlow 2013 page is now behind a bot check). `data/curated/change/notes.json`, checked by `bidb.change_series`;
  shown on `/change` ("What the graphs show together") and, for the slider's year, in the Map panel.
- One research agent sent George's email address to the Unpaywall API as its contact parameter while looking up an
  article; it was not repeated.

## 2026-10-23 (later) — E6: more layers, competing estimates, temperatures
- George asked for the first batch of layers and "all the rest", with estimates for missing dates and models compared.
- Graphs: `models` (other estimates of the same measure on one axis, the reference palette's first three slots),
  `style: estimates` (published figures as dots with error bars, labelled per point), and dotted stretches where a
  measured series has no figures (read as ≈). A research agent collected 287 published figures (41 models) for the
  years before statistics: England 1086–1801, Scotland, Ireland (whole island), coal before 1853, urban share, Irish
  woodland, markets and fairs → `data/curated/change/estimates.json` (quote and page for each); spot-checked 3 quotes.
- Found and fixed: coal output and jobs had lost 1942–2010 (footnote digits in the spreadsheet's year column); the
  Map panel's "begun per century" graph had no points.
- Temperatures: yearly mean for England, Wales, Scotland, Northern Ireland (Met Office, 1884–), Republic of Ireland
  (CRU CY, 1901–), with Luterbacher/Xoplaki's European reconstruction averaged per country (1500–1900) and an estimate
  from Central England back to 1659 (r 0.92–0.99, ±1.96 sd band; `prepare_temperatures.py`); the world vs 1850–1900
  from HadCRUT5, PAGES 2k and Temp12k.
- Layers: HYDE pasture/grazing and built-up area; GHS-POP 1975–2020; CRU TS decade temperature and rainfall vs
  1901–1930 (HadUK-Grid files need a CEDA login); night lights 1992–2024; Hansen tree cover lost 2001–2024; railway
  stations (Wikidata) and OpenHistoricalMap railway/canal lines by date; Ireland's counties at each census (CSO
  FY001); the BRITICE-CHRONO ice sheet and coast every 1,000 years from 31 ka (own window east to 9°E for Doggerland).
  Bug on the way: warping ETOPO to EPSG:4326 applied the geoid→ellipsoid shift (+56 m), turning the Irish Sea into
  land; `-novshiftgrid` fixed it. Time layers have their own date list (deep time before the slider's 4000 BC).
- Left out: Open Domesday data and the 1930s Land Utilisation Survey (non-commercial licences), Vision of Britain
  (bulk reuse needs permission), KK10 (PANGAEA bot check), HYDE 3.5 (non-commercial). E&W census by registration
  district has no open boundaries yet.
- George turned on Settings › Share on my home network (so the ui_check `settings_share` page now fails as expected).
- Graphs beside the map: "Buildings and places on the map, standing at each date" (begun by then and not yet closed,
  one sorted sweep), and "Homes in England, counted and estimated": dwellings counted from 1801 with an estimate
  before (England's population ÷ the average household, 4.44 before 1750 and 4.81 after, Boulton after Laslett;
  band between the two). New graphs that are on by default now join a browser's saved choice once.
- CRU TS yearly grids finished (1901–2025, 0.5°): decade temperature and rainfall maps against 1901–1930, and yearly
  temperature for the Isle of Man, Jersey and Guernsey from their nearest CRU land cell, with the same reconstruction
  and estimate from Central England (r 0.93–0.96) as the other countries.

## 2026-10-23 — plan: trade, enterprise and innovation
- George asked for trades, guilds, trading houses, markets (the stock market among them), firms and innovations to be
  fleshed out, drawing on his tea_explorer project. Planned as roadmap section "Trade, enterprise and innovation"
  (C1–C9): source research, tea as the first worked trade (tea_explorer's firms and history as leads, each fact to be
  sourced and quoted), guild/exchange/trading-house places, firms through time (map layer + graphs), trade and work
  graphs with estimates, innovations, laws and institutions as events, one story page per trade, GUI.
- ROADMAP.md was over 500 lines: sections with every item done moved to ROADMAP_DONE.md; E3/E6 entries condensed
  (E6 now done, its leftovers blocked by licence or access); status refreshed.
- SESSION_LOG.md split the same way: entries before 2026-10-21 → SESSION_LOG_2026-10-19.md.

## 2026-10-23 — C1: sources for trade, enterprise and innovation
- Three research agents (firms and institutions; economic series; innovations and laws) checked 72 sources: licence
  with a verbatim quote, URLs (HTTP status on the day), years, regions, size, items served and a verdict →
  `data/curated/trade/sources.json` + README (best source per item, what to ask, gaps); `bidb/trade_sources.py`
  checks the file (tests in `tests/test_trade_sources.py`). Use 32, quote figures 17, link only 8, ask 12, left out 3.
- I re-fetched the licence text of legislation.gov.uk, the CRO register and the Federico–Tena dataset (all as quoted)
  and CDPA 1988 s.163 (Crown copyright in a published work: 50 years from publication), now quoted for the
  Statistical Abstract scans.
- Findings: Wikidata's "business" class includes pubs, schools and parish councils (C4 needs a class allow-list);
  several QIDs assumed in the brief were wrong (correct ones in the README); the Bank of England millennium dataset
  is for personal or internal non-commercial use only and has no bank counts; IPO's historical patent pages are gone
  from gov.uk (read via the Wayback Machine); UCL's Legacies of British Slavery refuses scripts.
- One agent downloaded ~105 MB against the 50 MB limit (Bank of England workbook, a 66 MB CSO table by mistake);
  deleted. No personal data was sent to any service.
- Next: C1b (user: permission requests), then C2 (tea as the first worked trade).

## 2026-10-23 — plan: building types as a family tree
- George asked for a reference page classifying every type of building and construction like species, with their
  evolutionary links, charts of development over time, materials and techniques, and generated examples (possibly
  from his building-gen). Planned as roadmap section "Building types: a family tree of building" (BT1–BT7);
  building-gen (MIT, 4 of 29 types implemented, glTF) to be used only where checked as accurate, labelled as an
  illustration.
- ROADMAP.md was at 500 lines: the finished research-track items R0–R8 moved to ROADMAP_DONE.md.

## 2026-10-23 — C2a: tea firms and tea events
- C2 split into C2a (firms and events, done), C2b (imports and duty graph, hand transcription) and C2c (tea places).
- tea_explorer's 44 firms and history text used as leads only. 16 British and Irish tea merchants and firms and 4
  tea-room chains, each placed at its first shop where the source names it (otherwise the town, said so in
  `location`), with 1–3 sources and exact quotes → `data/curated/trade/tea.json`, read as list `tea` by
  bidb.oldest_lists (kinds `tea_firm`, `tea_room` in "Markets & trade"; 18 places, 18 evidence claims; section "The
  tea trade" on the Oldest page). Twinings and Fortnum & Mason stay in the trade list (`listed_in`), so the tea list
  shows them without a second place.
- Verdicts: Jacksons of Piccadilly 1700 is the firm's tradition (open; the Survey of London only has its 1935 shop
  front at No. 171); Fortnum & Mason stays at c.1770 (corrected earlier). tea_explorer's "first Ceylon tea export
  1873" is 1875 in the source. Tetley's and Taylors' founding towns are not in the sources; placed at Huddersfield
  and Harrogate with that said.
- 15 tea events 1657–1998 in `change/events.json` (Garway's 1657, first advertisement 1658, Catherine of Braganza
  1662, first Company import 1669, London tea auctions 1679–1998, Tea Act 1773, Commutation Act 1784, packet tea
  1826, end of the monopoly 1834, Assam tea 1839, A.B.C. 1864, Great Tea Race 1866, Ceylon tea 1875, tea bags 1953).
- Every quote was checked against the fetched article text while writing and again by `bidb.evidence --check --new`
  (all 47 found). Grace's Guide refuses scripts; firm websites gave nothing quotable.
- Tests: oldest-list ids unique apart from `listed_in` entries, which must resolve (140 tests OK); ui_check pages
  `oldest_tea`, `places_tea`, `change_tea`. Restarted the GUI server on port 5050 to load the new list.
- Next: C2b (tea imports and duty graph) or C2c (tea places).

## 2026-10-23 — C2c: tea places
- Tea list gained a third kind, `tea_trade` (coffee houses, auctions, docks and ships of the tea trade): Garraway's
  Coffee House (1657; burnt 1748), Tom's Coffee House in Devereux Court (Twining's start, 1706), East India House
  (1648–1861; tea auctions in Leadenhall Street from 1679), the London Commercial Sale Rooms in Mincing Lane
  (1834–1998), East India Docks (1806–1967) and Cutty Sark (1869); tea rooms Miss Cranston's Crown Luncheon Room
  (Argyle Street, 1878) and the Willow Tearooms (1903). 28 entries in `tea.json`, 24 claims; all quotes found.
- East India Docks and Cutty Sark stay in Maritime heritage (protected kinds) and the Willow Tearooms stays a
  catalogue building; all three show in the tea list. The Horniman Museum is an era_places place (not protected), so it
  was not added: it would have moved into Markets & trade.
- Caught on the way: two details I had written from memory (Garraway's "rebuilt; closed 1866", the docks' 1967
  closing) were checked against the articles; the first had no source and was removed, the second is now quoted.
- Next: C2b (tea imports and duty graph from the Statistical Abstract scans), then C3.

## 2026-10-23 — C2b: tea drunk per person, 1864–1938
- OCR text of every Statistical Abstract volume to 1975 (76 items, 106 MB) cached in `<cache>/stat_abstract/`
  (with each item's hOCR search text and page index, so a regex finds the page; page images by leaf).
- The per-head table ("retained for home consumption per head of the total population") read from 13 page images
  in six editions; every figure compared with the OCR digits and, where editions overlap (1864–70, 1876–83,
  1891–98, 1910–14, 1924–37), with another edition. Editions revise earlier years by up to 0.03 lb after a census
  (1878: 4.66 → 4.64; 1897: 5.81 → 5.79); the latest edition read is used.
- New graph "Tea drunk per person" (Prosperity and work; source `stat_abstract_uk`): 3.00 lb in 1864, 5.02 in
  1887, 6.07 in 1900, 6.89 in 1914, 8.68 in 1919, 10.53 in 1932, 10.18 in 1938. None for 1915–18 ("cannot be
  stated"); Great Britain and Northern Ireland from 1923; 1929–32 duty-free (retained imports).
- The 1846–1865 edition has no per-head table (totals only), so the official per-head series starts in 1864;
  earlier years, the 18th century, duty, prices and the modern end are left as C2d.
- Next: C2d or C3 (guilds, exchanges and trading houses).

## 2026-10-23 — C2d1: tea supplies per head, 1941–1974
- C2d split into C2d1 (modern end to 1974, done), C2d2 (before 1864), C2d3 (duty and prices), C2d4 (after 1974).
- The OCR of the post-war tables garbles the tea row, so it was read from the page images (archive.org
  `page/n<leaf>_w2000.jpg`, leaf from each item's `_page_numbers.json`) of the Annual Abstract's "Estimated food
  supplies per head of population" (Ministry of Food, then MAFF): No. 88 p. 195 (1941–50), No. 92 p. 179
  (1945–54), No. 97 p. 176 (1949–59), No. 107 p. 209 (1959–69), No. 112 p. 238 (1964–74). Each row read again from
  an enlarged crop.
- Overlaps agree apart from footnoted revisions: civilian → total population from 1948 (1949: 8.1 → 8.3, 1950:
  8.4 → 8.5), 1954 9.6 → 9.7, 1959 9.6 → 9.7, and the 1971-census revision (1965: 8.9 → 9.0). Latest edition used.
- New series `tea_supplies_uk` shown as a second line on "Tea drunk per person" (not joined to it: a different
  measure, 9.3 lb for 1934–38 against the Board of Trade's 9.5). 8.1 lb in 1941, 7.0 in 1943, 10.1 in 1956, 7.5 in 1973.
- Rationing dates (1940–52) were written from memory into the note and taken out again: still no citable source.
- Tests 140 OK; ui_check `change_tea` now also requires the Ministry of Food line. Hosted copy not updated.
- Next: C2d2/C2d3, or C3 (guilds, exchanges and trading houses).

## 2026-10-23 — C1b dropped; C2d2a: tea before 1864
- C1b (permission emails) dropped at George's request: the roadmap now names open stand-ins or quoted published
  figures wherever an "ask" source was the best one (C3 livery companies, C4 closed firms, C5 occupations, trade,
  prices, steam power and patents, C7 slavery); the README's "To ask" list is kept for later.
- C2d2 split: C2d2a done, C2d2b (before 1846: quoted 18th-century estimates; totals after 1865) left open.
- The 1852–1870 volume (Nos. 14–18) has the first table "Retained for Home Consumption, per Head of the Total
  Population" (No. 14, pp. 42–43, leaves 46–47): tea 2.00 lb in 1852, 2.14, 2.24, 2.28, 2.26, 2.45, 2.58, 2.67,
  2.67, 2.69, 2.70, 2.90 in 1863; 1864–66 (3.00, 3.29, 3.42) equal the figures already used. Read from the page
  images (tea row cropped at full size); the OCR of Nos. 15–18 gives the same figures for the years they cover.
- New graph "Tea retained for home consumption", UK 1846–1865 (million lb), from the 1846–1865 volume: No. 8
  p. 21 (leaf 25) for 1846–50 and No. 13 pp. 38–39 (leaves 472–473) for 1851–65; the overlapping years in No. 9
  and No. 13 agree to the pound. 46.7 million lb in 1846, 97.8 million in 1865. Page images are `page/n<leaf-1>`.
- Nothing before 1852 per head: the Abstract's yearly UK population table (No. 49 in the 1852–1870 volume) also
  starts in 1852, and the 1846–1865 volume has none for the whole UK, so no per-head figure was made up.
- A duty history (rates 1853–65) went into the new graph's note from memory and was taken out again before commit.
- Tests 140 OK; ui_check `change_tea` now also requires the new graph. Hosted copy not updated.
- Next: C2d2b, C2d3 (duty and prices), or C3.
