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

## 2026-10-23 — Oldest pubs: James Wright's list (Guardian, 23 Oct 2026)
- Wright (buildings archaeologist, for Historic England) names the George Inn, Norton St Philip as England's
  oldest pub and lists 12 medieval inns; none of the two dozen "oldest pub" claimants is close.
- Research file (`oldest_by_type.json`, Inn / coaching inn): all 12 as examples, with sources; claimants'
  notes (Fighting Cocks, Bingley Arms, Trip to Jerusalem, Skirrid) give Wright's verdict. 19 evidence claims
  (Guardian quotes, VAG tree-ring notes, list entries, Morning Advertiser 2024), 16 date corrections.
- Dates: George Inn 1375 (late C14; front and roof 1430–32); New Inn 1432 (tree-ring, was 1450); Angel and
  Royal 1375 (list entry, was Wikidata's 1301; Wright c. 1450); Mermaid Inn 1475 (was the claimed 1156);
  Skirrid 1650 (was the claimed 1110); Old George, Salisbury 1366 and Red Lion, Colchester 1470 (both had no year).
- 8 pubs added without a rebuild (`bidb/research_add.py`): Bull Ludlow, King's Head Shrewsbury (1403–04 by
  tree-ring; the Guardian's 1426/1430–31 are the database's dates for Wyle Cop buildings), White Hart Hook,
  George Dorchester-on-Thames, Angel Andover, King's Head Aylesbury, Saracen's Head Southwell, George Odiham;
  George & Pilgrims, Glastonbury was in the catalogue and got its date and note. Research entries may carry a
  `wikidata` key (build and `refresh_claims` use it).
- `bidb.dendro`: "hotel", "public", "pub", "tavern" no longer distinguish a name (4 new matches: Saracen's
  Head, King's Head). Not matched: White Hart Hook (the VAG grid reference is ~105 km out) and George Odiham
  (322 m, over the 300 m limit for saints' names); their dates name the tree-ring dates anyway.
- Detail views: pubs with a Domesday line say it is the place, not the inn (no pubs are in Domesday Book).
- Evidence check: sources without a URL are "no link" (not "unreachable"); quotes cited to the VAG DOI are
  checked in the downloaded database (29 of 29 checkable quotes found).
- Tests 140 OK. Database backup before the changes in the session scratchpad. Hosted copy and bundled
  database not updated.

## 2026-10-23 (later) — Tree-ring-dated buildings, Irish pub claimants
- `bidb/dendro_add.py`: 1,510 VAG entries felled before 1500 matched no catalogue record (Wikidata gives most listed
  buildings no date, so the build never saw them). Matched to Wikidata items within 400 m: the first pass (catalogue
  rules only) was about a third wrong in a sample (house numbers, barn vs farmhouse, East vs West Hele, Red Cross vs
  Red Lion, a church chest), so `plausible` filters candidates first; 489 matches, 466 structures, 5 streets taken
  out → 461 added (230 houses, 37 manor houses, 31 churches, 23 inns and pubs...). Dated by the earliest felling, the
  middle of ranges wider than ten years ("1315-15+20" → 1317). `data/dendro_items.json` keeps them through rebuilds.
  Tree-ring matches: 594 → 1,048 catalogue buildings.
- Pubs among them: Royal George, Cottingham (1262), Saracen's Head, Thame, White Hart, Newark (1312/3), Old Bell,
  Henley (1325), Queen's Head, Crowmarsh, White Hart Bocking, George Colchester, Lad in the Lane, Swan Sutton
  Valence, Swan Sible Hedingham, Bell Inn Nottingham, Bear Henley, Black Lion Southfleet, Luttrell Arms, Chequers
  Chipping Norton, Swan Kingsclere, Black Boy Bewdley, Spotted Dog, White Hart Spalding, Lamb Farnham. Not found on
  Wikidata: Buck's Head, Church Stretton (1287–1312), Cross Keys, Leicester, Crown, Chiddingfold.
- Brazen Head, Dublin: 1198 (Wikidata, the pub's claim) → 1754 (present building; inn first named 1668). Kyteler's
  Inn, Kilkenny: 1201 → c. 1275 (NIAH: built as a house, an inn after 1449, rebuilt c. 1625). Both research
  examples with evidence claims (quotes found). `research_add.mark_existing` also replaces a Wikidata-query type.
- Hosted copy: 850 embedded thumbnails (was 1,100); the change layers had taken the export to 258 MiB. Republished as
  versions 60–64 (five batches, all 486 files, 11 old thumbnail shards removed): 251.8 MiB, 22,508 records. Static
  GUI review (pages, pop-ups, search): every check passed (two failures were the local test server starting late).
- Tests 142 OK (2 new for dendro_add). Database backups in the session scratchpad.

## 2026-10-23 (evening) — C2d2b1: tea retained for home consumption, 1846–1938
- C2d2b split: C2d2b1 (totals after 1865, done) and C2d2b2 (18th-century published estimates; needs the books).
- Read from the page images of the quantity tables "Articles retained for home consumption": No. 26 table 17
  pp. 46–47 (1865–78), No. 41 table 28 p. 72 (1879), No. 42 table 29 p. 76 (1880–83), No. 46 table 30 p. 83
  (1884–92), No. 48 table 30 p. 81 (1893–96), No. 59 table 42 pp. 162–163 (1897–1909), No. 69 table 36 pp. 102–103
  (1910–24), No. 83 table 286 pp. 406–407 (1925–38, thousand lb). Blurred digits (1891 in No. 42; 1896–97 in No. 46)
  settled from the next edition. Overlaps agree (1864, 1879–83, 1887, 1891, 1893–1900, 1910–11, 1924) except 1865:
  No. 13 97,834,874 lb, No. 26 97,834,600 (latest used).
- `tea_retained_uk`: 93 years, 46.7 million lb (1846) → 305.5 (1913) → 277.4 (1917) → 388.0 (1919) → 487.7 (1932,
  duty-free) → 431.8 (1938). Notes: Irish Free State out from 1 April 1923; 1929–32 imports less re-exports.
- Check: total ÷ per head gives a smooth population except 1919 (44.7 million against 46–47 either side; not
  explained, both figures clearly printed) and 1938: the printed 10.18 lb per head would need 42.4 million people;
  the total gives ≈ 9.1 lb. Kept as printed with a note on "Tea drunk per person" (with ≈ 9.1, the 1934–38 mean is
  9.25 lb, close to the Ministry of Food's 9.3 — suggestive, not proof). Wartime editions (Nos. 84–88) carry no
  such table.
- Tests 142 OK; ui_check `change_tea` now also requires "432 million in 1938". Hosted copy not updated.
- Next: C2d2b2 (needs the books), C2d3 (duty and prices, from the same scans), or C3.

## 2026-10-23 (late) — C2d3: tea prices and tea duty
- "Price of imported tea" (`tea_price_uk`, d. a lb, 1865–1919): the Abstract's "Average prices of the undermentioned
  articles imported", read from the page images of No. 27 p. 104 (1865–67), No. 30 pp. 108–109 (1868–82), No. 45
  p. 154 (1883), No. 46 pp. 156–157 (1884–96), No. 59 pp. 272–273 (1897–1904), No. 66 pp. 266–267 (1905–19). Overlaps
  (1868–72, 1884–90, 1897–98, 1905–11) agree to the hundredth of a penny. 1865–70 "from computed values", 1871 on "from
  declared values". 19.88d in 1865 → 12.58 (1882) → 7.20 (1902) → 9.18 (1914) → 16.05 (1919). Before 1865 only prices
  by country (No. 13 p. 37: China, India, Japan); from No. 67 only India and Ceylon / China — neither joined.
- "Duty on tea" (`tea_duty_uk`, full rate) with the Empire rate (`tea_duty_empire_uk`) as a second line, drawn as steps
  (two rows in the year of a change): 6d (tariff 31 May 1874, No. 21 p. 15; also May 1875 and Aug. 1889 by OCR) → 4d
  1 May 1890 (No. 50 p. 20) → 6d 6 Mar. 1900 → 8d 20 Apr. 1904 → 6d 1 July 1905 → 5d 14 May 1906 (No. 59 pp. 15–18) →
  8d 18 Nov. 1914 → 1s 22 Sept. 1915 (No. 70 pp. 127, 129) → Empire preference from 2 June 1919 (p. 132; five-sixths in
  the 1 July 1921 tariff, No. 67 p. 34) → "reduced by one-third" 15 May 1922 → "by one-half" 5 May 1924 (No. 70 pp. 136,
  138) → repealed 22 Apr. 1929 (No. 82 p. 411 note b) → 4d / 2d 20 Apr. 1932 → 6d / 4d 22 Apr. 1936 → 8d / 6d 27 Apr.
  1938 (No. 83 pp. 203, 207, 209). The Empire rate for 1922–29 is not printed in the editions read (left as a dotted gap);
  No. 68 omits its tariff. Before 1874: the 1865 cut is listed without rates, so not shown.
- Leads left as C2d3b: the 1930s "Tea—Indian average, London Auctions" wholesale price (No. 83), prices by origin
  1908–22, duty before 1874 and after 1938.
- Tests 142 OK; ui_check `change_tea` also requires both new graphs. Hosted copy not updated.
- Next: C2d4, C2d3b, or C3 (guilds, exchanges and trading houses).

## 2026-10-23 (night) — C2d4: tea after 1974, tea rationing
- Defra Family Food datasets, "UK - household purchases" (UKHHcons_17Sep26.ods, OGL), sheet Household_quantity, code
  304 Tea: 51 years of g a person a week, 1974–2024/25 (calendar years to 2000 and 2006–2015, financial years shown at
  the year they begin; 2015-16 left out as it overlaps 2015). Converted to lb a year (× 365.25/7 / 453.59) →
  `change/data/tea_household_uk.csv` (published grams kept) → series `tea_household_uk`, a third line on "Tea drunk per
  person". 67.6 g in 1974 = 7.78 lb, matching MAFF's supplies figure (7.8) for the same year; 36.2 g (4.2 lb) in 2000;
  20.7 g (2.4 lb) in 2024-25. Household purchases only (no eating out); Defra notes diary surveys under-report.
- Event "Tea rationed" (1940–1952), source `hansard_tea_rationing` (Open Parliament Licence): HC Deb 18 July 1940
  vol 363 c471 (two ounces a week), HC Deb 22 October 1952 vol 505 c1013 ("since tea has been de-rationed"). Exact
  start and end days are not in the passages found (secondary sources: 8 July 1940; 3 or 5 October 1952), so the text
  says July 1940 and autumn 1952.
- 101 series, 48 events, 77 sources. Tests 142 OK; ui_check `change_tea` also requires "Family Food" and "Tea rationed".
  Graph checked in a screenshot. Hosted copy not updated.
- Next: C3 (guilds, exchanges and trading houses), or C2d3b; C2d2b2 still needs the books.

## 2026-10-23 (night, later) — C3a: guild houses, halls, exchanges and livery companies as places
- C3 split: C3a (places, done), C3b (researched oldest of each, with evidence), C3c (people; halls of the unplaced
  companies).
- New `bidb/livery.py`, read by bidb.trade_works: Wikipedia's "Livery company" precedence table (114 companies:
  order, trade, year charter granted with the source the table cites) and "List of mottos and halls of the livery
  companies" (hall, motto), plus Wikidata's 116 livery-company items. A company sits at its hall (the hall's article
  or, for unlinked halls, an item with exactly that English label; in London for a City company, so the Sheffield
  Cutlers' Hall is not taken for the London one; never the company's own item), else at its own coordinates or P159 /
  P466. 41 of 117 placed (13 at their hall, `extra.hall_ref` links the hall's place or catalogue building); 76 without
  a hall or one with no coordinates have no place.
- trade_works kinds: `tr_guild` (guild house Q1961493, livery hall Q98034180, cloth hall Q977382: 50 places), `tr_bourse`
  (stock exchange, firms left out: 1, the London Stock Exchange), `tr_merchant` (merchant's house: 6), `tr_livery` (41).
  bidb.institutions no longer makes guild houses town halls (1 moved). Places 173,680 → 173,773.
- The two Wikipedia tables differ (Grocers 1428 charter vs 1345 "establishment"; Drapers 1364 vs 1361): the charter
  table is used and labelled so; left for C3b. Found: medieval guildhalls in the catalogue are "House / domestic"
  (Data quality item added).
- Place detail: Order of precedence, Trade, Charter granted (linked to its source), Hall (linked), Motto. Tests 147 OK
  (5 new, tests/test_livery.py); ui_check places_livery and places_guildhalls pass. Hosted copy not updated.
- Next: C3b.

## 2026-10-23 (night, last) — C3b: the oldest guilds, companies, exchanges and banks
- New list `guilds` in bidb.oldest_lists (`data/curated/trade/guilds.json`, kinds `gu_*`, group "Markets & trade"): 70
  entries in 8 categories (guildhall or livery hall 15, livery company 9, merchant guild outside London 7, trading company
  8, exchange 8, coffee house 6, bank 12, merchant's house or trading post 5). 62 carry their own sources (Wikipedia
  articles and the Weavers' Company history page); all 136 quotes found by `bidb.evidence --check --new`, read with the
  checker's own `source_text` while researching. Eight are shown from other lists (`listed_in`): Lavenham Guildhall, Royal
  Exchange, Child & Co., C. Hoare & Co, Bank of Scotland (trade), Garraway's (tea), Exeter Guildhall and Guildhall, London
  (civic, already there).
- Settled from C3a: Grocers founded 1345 (Pepperers 1180), charter 1428; Drapers founded 1361, charter 1364 — both
  Wikipedia tables right, for different events. Weavers recorded 1130 (Pipe Roll), charter 1155. Open (5): Saddlers'
  Anglo-Saxon origin, Merchant Company of Edinburgh "at least 1260", Merchant Adventurers 1407, Queen's Lane Coffee House
  (only on its site since 1970), Martins Bank's 1563 tradition.
- 29 entries (companies, most banks) have no single standing place and no coordinates: `lists()` now marks entries
  `placed: false` when neither a building nor a place has their id, and the Oldest page shows them unlinked. Places
  173,773 → 173,786 (13 new); 15 are catalogue buildings.
- Tests 148 OK (new: unplaced companies are not links); ui_check `oldest_guilds` added and passing; section checked in a
  screenshot. Hosted copy not updated.
- Next: C3c (people of the halls and companies), or C4.

## 2026-10-23 (night, after C3b) — C3c: people of the guilds, companies and banks
- Found: none of the 7,642 Markets & trade places had linked people; the people stage of bidb.places_build runs before
  bidb.trade_works and bidb.oldest_lists add them (also true of Maritime, Military, Museums, Sport…: Data quality item).
- New stage `bidb/trade_people.py` (build stage after oldest_checks; `--report`): bidb.people's place roles plus Member
  (P463), Worked for (P108) and "Master, governor or officer" (P39 positions whose P2389 / P642 / P361 is the
  organisation, and P488, P169, P1037, P3320). Market towns and places on a settlement's item left out (Kirkby
  Lonsdale market had 19 people born in the town). 329 links, 294 people (people 11,927 → 12,193), 117 places; 123
  links referenced. Bank of England 81 (governors, Chief Cashiers, directors; staff incl. Theresa May and Rachel
  Reeves, both of whom worked there), London Stock Exchange 16, Cutlers in Hallamshire 15 (Master Cutlers), Stationers
  11, Drapers 10.
- `people.prepare` (moved from places_build.people_stage, shared): people with no English name now dropped before the
  per-role trim (the old order left 91 links to missing people; they go at the next places build). `link_references`:
  a source with no English label is shown as "Wikidata source Q…" linked to its item (29 rewritten in the database).
- Halls of the unplaced companies, `livery.osm_halls`: OSM objects in London named as the mottos table names the hall,
  whose addr:street is one the table gives; plaques and memorials dropped; one match only. Checked on 9 companies
  already placed by Wikidata: all within ~25 m. Placed Mercers' Hall (Ironmonger Lane) and Plaisterers' Hall (1 London
  Wall): companies placed 41 → 43 of 117. Only 10 of the 76 had a hall named; the others are not on OSM so.
- Bug from C3a fixed: trade_works wrote its three groups in turn, and a place whose kind moved between groups was
  regrouped by one write and deleted by the next (Plymouth Gin Distillery was missing from the database). The stage
  now clears all its own kinds first, and a merchant's house with another use takes that kind (the distillery, 1793).
- Rerunning trade_works showed that the committed database had already lost, for its places, the date precision and 52
  reviewed corrections of oldest_checks, the researched dates oldest_lists writes onto existing places, and their
  nations (only 59 of 7,642 trade places had one). Reran oldest_lists → oldest_checks → nation_geo → trade_people:
  8,530 precisions and 52 corrections back; places with a nation 147,207 → 173,732. Data quality item added.
- Tests 155 OK (7 new, tests/test_trade_people.py: OSM street check, targets, write keeps other links and people,
  references, merchant's house yields). ui_check `places_livery_people` and `people_officers` added. Hosted copy not
  updated; the release database (db-2026-10-22-4) predates C3a–C3c.
- Next: C4 (firms through time), or the Data quality item on people of the later place groups.

## 2026-10-23 (night, last) — Published: hosted copy version 66, database release db-2026-10-23
- Hosted copy: `python -m app.static_export` (22,508 records, 173,789 places, 12,193 people; 252.1 MiB, 486 files);
  209 files changed (103 MB: place shards and location cells, people, evidence, oldest lists, quiz, change series,
  oldest.js, render_places.js), none added or removed. Published as versions 65 and 66 (two batches of ~51 MB) after
  listing the published files (the service refuses to replace files this session has not read or listed). Sizes of
  the published files checked against `dist/`. Static GUI review (pages, pop-ups, search, places) 52/52 after
  rerunning one check that the local Python server had dropped.
- Database release db-2026-10-23 (102 MB, SHA-256 31c5f66c…; 22,508 buildings, 173,789 places, 12,193 people),
  marked Latest; `data/bundled.json` updated. `bidb.bundle release` packaged it but `gh release create` failed twice
  with HTTP 408 (upload stalled on a ~100 KB/s uplink); uploaded instead with curl to a draft release (1,193 s),
  GitHub's asset digest matched the local SHA-256, then published. Data quality item added to make `release` do this.
- Found while checking the hosted copy: 46 Time Team digs at whole-degree positions in Russia and Kazakhstan (the
  coordinate parser takes the latitude's minutes as longitude). Data quality item added; not fixed.

## 2026-10-24 — Time Team coordinates and the release command fixed
- Time Team: `{{coord}}` was read as its first two numbers, so the 45 digs given in degrees/minutes/seconds
  (`{{coord|51|48|28|N|1|38|13|W}}`) sat in Russia and Kazakhstan. New `hoards.coord` (decimal or DMS with N/S/E/W;
  digs and hoards both use it; hoards had no DMS positions, none moved). The 4 specials abroad are left out (ids of
  the others unchanged). Reran bidb.digs then bidb.nation_geo: 201 digs, all with a nation; excavation rows 865 → 916
  (correctly placed digs now fall within 300 m of catalogue buildings). Places 173,789 → 173,785.
- Bug found on the way: rerunning bidb.digs deleted its own 335 excavated places (they were in `places`, so counted
  as already in the database and not rewritten, then the stage's write removed its kinds). It now ignores its own
  kinds when looking for existing items; rerun restored all 335.
- `bidb.bundle release` rewritten: draft release via the API (today's draft reused after an interrupted run), upload
  to uploads.github.com with Content-Length and progress, up to 5 attempts with backoff (a stalled/half asset is
  deleted first), size and SHA-256 compared with GitHub's asset digest, then published as Latest and the manifest
  written. Checked read-only against the live API (draft flags, asset state, digest = manifest). Not yet run for real.
- Noticed, not fixed: places_fts has two duplicate rows (Q11753150 Point of Ayr Lighthouse, Q729006 Chatham).
- Tests 163 OK (tests/test_digs.py 3, tests/test_bundle.py 5). Hosted copy and release not updated.

## 2026-10-24 — C4a: firms through time (Wikidata)
- C4 split: C4a (Wikidata firms: map layer and graphs, done), C4b (CRO and Companies House registers, pending).
- New `bidb/change_firms.py` (`python -m bidb.change_firms`, then `bidb.change_series`): 28,421 Wikidata items (companies
  and subclasses, items directly of class business or enterprise; in the isles by P17, incl. historical states, or by
  head office), queried through QLever. Not firms, left out by class name: parish councils (3,090) and other councils,
  NHS trusts, colonial, learned and text-publication societies, railway lines, brands, websites, software…
- Map layer "Firms open" (Change over time panel on the Map page, `layers/firms.json`, 590 KB): 11,895 dated firms with
  a position, coloured by nine industries (keyword rules on the classes, else stated industry P452, else the name;
  3,327 say nothing); 10,928 placed at their head office, spread by up to ~1 km; 2,371 with a closing year. 813 open
  in 1850, 9,147 in 2020. `change_layers.js`: a `spans` dot can carry a legend entry (6th value); the closed colour is
  the legend's last entry (stations unchanged).
- Graphs (default off, theme Prosperity and work): "Firms founded per decade" 1600–2020 (14,541 dated firms; second
  line: of these, closed), and three by industry (making / food and drink / mining; finance / transport / shops;
  publishing and media / services). Founded per decade: 13 in the 1690s, 101 in the 1800s, 453 in the 1900s, 2,370 in
  the 2000s. Notes state the survivorship bias, the few closing years, and national branches carrying the parent's
  founding year. Source `wikidata_firms` added to `change/sources.json`.
- Checked in headless Chrome (layer, legend, note, counts at 1850 and 2020; no page errors); ui_check `change_firms`
  added. Tests 167 OK (tests/test_change_firms.py 4). Hosted copy and release not updated.
- Next: C4b (CRO and Companies House as more lines on the graphs), or C5.

## 2026-10-24 — C4b: companies from the registers
- New `bidb/change_registers.py` (`python -m bidb.change_registers`, then `bidb.change_series`): Companies House Table A8
  (xlsx read with the stdlib), Companies House basic data (2.8 GB CSV streamed from the 494 MB zip; Companies Act
  companies only, as A8 counts: no LLPs, partnerships, CIOs, Royal Charter bodies, whose dates go back to 1327) and
  Ireland's CRO records (47 MB zip; the SQL API refuses functions such as `extract`). Downloads kept in
  `<cache>/registers/` on FANTOM (~540 MB); only yearly counts are committed (16 CSVs).
- Six graphs (default off, Prosperity and work), separate from the C4a graphs because the registers count ~100× the
  Wikidata firms: companies incorporated per year (GB/UK 1939–2026, with dissolved and with each year's companies still
  on the register: 5,063 of 1980's 69,400), companies on the register (173,300 in 1939 → 5,479,045 in 2025-26), Ireland
  registered / dissolved (from 1960; earlier dissolved companies mostly absent) / still registered, and three graphs of
  live UK companies by decade founded and industry (SIC divisions → the C4a industries). Sources `companies_house_a8`,
  `companies_house_basic`, `cro_companies` in change/sources.json; DATA_LICENSE.md rows (CRO's CC BY statement).
- Change over time: 127 series. Checked in headless Chrome (screenshots of the three new rows of graphs); ui_check
  `change_registers` added; map, change_firms, change_tea still pass. Tests 171 OK (tests/test_change_registers.py 4).
- Hosted copy and release not updated.
- Next: C5 (trade and work graphs), or C2d2b2 / C2d3b (tea before 1846, more tea prices).

## 2026-10-24 — C5a: patents per year
- C5 split: C5a patents (done), C5b overseas trade, C5c occupations, C5d prices and wages, C5e shipping, steam, banks
  and what C5a left (pending).
- New `bidb/change_patents.py` (`python -m bidb.change_patents`, then `bidb.change_series`), IPO sources only (OGL):
  the archived ipo.gov.uk number tables (1617–1852 first number per decade, 1852–1915 applications and grants, first
  number per year 1916–1981 and 1979–2012), the monthly statistics 1995–2025 and Facts and figures 2019 and 2025.
  Downloads in `<cache>/registers/` (~600 KB). `change_registers.xlsx_rows` takes a `cols` argument (Table 1 runs to K).
- Graphs (default off, Prosperity and work): "Patents granted per year" 1617–2025 (England and Wales to 1852; period
  averages at mid-period, 1853–1915 yearly, specifications published 1917–1978, IPO grants from 1995) with
  applications filed and European patents granted for the UK by the EPO; "Patent applications published per year"
  1979–2025. 1916 left out (earlier applications still published under old numbers: only 2,811); no grant counts
  1979–94. Checks: published 2011 from the numbers 10,124 against 10,043 in Facts and figures; the 2019 and 2025
  editions agree for 2016–19 (≤5 apart); monthly sums against Facts and figures within 0.1% (grants identical).
- Bottomley (2014) England/Scotland/Ireland 1700–1851 not drawn (OWID gives no licence; C1 verdict "quote figures");
  his England 1800–04 total (440) equals the IPO numbers' (440). Cited in the note.
- Sources `ipo_patent_numbers`, `ipo_patents_1852_1915`, `ipo_monthly_stats`, `ipo_facts_figures` in
  change/sources.json; DATA_LICENSE.md rows. Change over time: 131 series.
- Checked in headless Chrome (both graphs drawn, no page errors); ui_check `change_patents` added; change_registers,
  change_tea and map still pass. Tests 175 OK (tests/test_change_patents.py 4). Hosted copy and release not updated.
- Next: C5b (overseas trade: Federico–Tena, ONS, CSO).

## 2026-10-24 — Published: hosted copy version 68, database release db-2026-10-24
- Database release db-2026-10-24 (102 MB; 22,508 buildings, 173,785 places, 12,193 people) with the rewritten
  `bidb.bundle release`: draft, one upload in 7 s, GitHub's SHA-256 matched, published as Latest; `data/bundled.json`
  committed. First real run of the new release command: worked first time.
- Hosted copy: `python -m app.static_export` (252.8 MiB, 449 files). Against version 66: 38 location cells removed (the
  Time Team digs that had sat in Russia and Kazakhstan), 1 added (the C4a firms layer), 39 changed (place shards,
  location cells, buildings index, excavations, quiz, change series and layers, change_layers.js; 87 MB). Published
  as versions 67 and 68 (two batches of ~43 MB, removals in the first) after listing the published files; sizes of
  the updated files checked against `dist/`.

## 2026-10-24 — C5b1: overseas trade totals
- C5b split: C5b1 totals (done), C5b2 main goods and re-exports (Statistical Abstract scans, HMRC API), C5b3 before 1800
  (Davis, Schumpeter, Mitchell quoted) pending.
- New `bidb/change_trade.py` (`python -m bidb.change_trade`, then `bidb.change_series`). Downloads in
  `<cache>/registers/trade_*` (~0.8 MB): Federico-Tena UK and Ireland workbooks (+ the Ireland notes PDF), ONS IKBK,
  IKBL, IKBH, BOKG, YBHA (the ONS answers 429 to quick requests: retried after 20 s), CSO TSA01, OWID's CEPII export
  shares.
- Five graphs (default off, Prosperity and work): UK trade 1800-1938 at 1913 prices; Irish Free State 1922-38 at 1913
  prices; UK exports and imports since 1948 (chained volumes; reference year 2024 found as the year IKBK = IKBH);
  goods exports as a share of GDP (CEPII UK and Ireland, ONS UK; the ONS line is 1.0 points from CEPII's on
  average); Ireland's trade 1930-2025 in euro. Not joined across eras. Check: Federico-Tena's 1930-38 Irish exports
  in dollars over the CSO's in pounds give 3.14-4.96 $ to the pound, so the two series differ in more than the
  exchange rate; said in the note. Federico-Tena's 1922-23 Irish figures are far below 1924's; their notes do not
  explain, said in the note.
- Sources `federico_tena_uk`, `federico_tena_ireland`, `ons_trade_volumes`, `cso_tsa01`, `cepii_exports_gdp` in
  change/sources.json; DATA_LICENSE.md rows. Change over time: 142 series.
- Checked in headless Chrome (screenshot of the five graphs; a graph draws three lines at most, so the Irish Free State
  got its own); ui_check `change_trade` added; change_patents, change_registers, change_tea and map still pass. Tests
  179 OK (tests/test_change_trade.py 4). Hosted copy and release not updated.
- Next: C5b2 (main goods from the Statistical Abstract), or C5c (occupations by sector).

## 2026-10-24 — C5b2a: overseas trade at the prices of the time, 1854-1938
- C5b2 split: C5b2a values (done), C5b2b the main goods (and UK produce exports 1840-53), C5b2c HMRC's API (pending).
- The Statistical Abstract's summary table (imports, United Kingdom produce, foreign and colonial produce = re-exports,
  total exports; net imports or total trade) read from the page images of Nos. 16 (p. 13), 18 (p. 17), 30 (p. 33),
  33 (p. 41), 46 (p. 53), 59 (p. 69), 70 (p. 281) and 83 (p. 368) → `data/curated/change/data/trade_abstract_uk.csv`
  (edition, leaf, page, table per year; latest edition read used). Every row checked by its own two sums: all 85 pass.
  Overlaps agree except revisions (1870, 1885, 1898) and No. 18's misprinted 1868 imports (294,460,214; the row's own
  total and No. 30 give 294,693,608). Image leaf = OCR page index; image file `page/n<leaf-1>` as before.
- New `bidb/change_trade_values.py` (load, check, series, write) → series `sa_trade_imports_uk`, `_exports_uk`,
  `_reexports_uk` (graph "Overseas trade at the prices of the time, 1854-1938", £ million) and
  `sa_trade_reexport_share_uk` ("Re-exports, share of all exports": 16% in 1854, 25.6% in 1863, 17.3% in 1913, 5.8% in
  1918, 11.6% in 1938). Prefix `sa_trade_` so bidb.change_trade's rewrite of `trade_*` leaves them alone. Source
  `stat_abstract_trade_uk`; DATA_LICENSE.md row. Change over time: 146 series.
- Two causes written from memory into the notes (American cotton in 1863, wartime controls) were taken out before commit.
- Checked in headless Chrome (screenshot of both graphs); ui_check `change_trade_values` added; change_trade,
  change_tea and map still pass. Tests 182 OK (tests/test_change_trade_values.py 3). Hosted copy and release not updated.
- Next: C5b2b (main goods from the same scans), or C5c (occupations by sector).

## 2026-10-24 — C5b2b1: the main exports by value, 1868-1911
- C5b2b split: C5b2b1 exports 1868-1911 (done), C5b2b2 the same goods 1854-67 and 1912-38, C5b2b3 the main imports and
  UK produce 1840-53 (pending).
- The "declared value of principal articles of British and Irish produce exported" tables read from the page images:
  No. 30 table 31 pp. 74-81 (1868-82), No. 45 table 37 (its 1883 column, pp. 106-114), No. 46 table 37 pp. 108-117
  (1884-98), No. 59 table 49 pp. 198-209 (1897-1911, the new classification). 1,947 printed figures in
  `data/curated/change/data/trade_goods_abstract_uk.csv` (row, year, value, edition, leaf, page, table, note).
- Checks: every printed total against its parts (cotton, linen, wool, iron and steel, coal, machinery, other textiles);
  the misreadings they caught were re-read on enlarged crops. Figures with no printed total (coal before 1897, yarns,
  machinery to 1898, No. 59's totals) were each found printed the same in at least two other editions' OCR text.
  Printing slips: No. 30 tinned plates 1878 (732,378: the "2," missing), No. 45 woollen stuffs 1883 (7,867,834;
  Nos. 33-44 print 7,687,834); 1883 wool parts stay £10 below the total (No. 33 prints hosiery + other 10 higher).
  Blurred figures in No. 46 taken from No. 45's print of the same row (noted per figure).
- No. 59's classes brought back to the old totals: coal = Total of Coal &c.; cotton manufactures = piece goods + other
  manufactures (waste from worked cotton separate from 1908, left out); wool manufactures = total less flocks, waste,
  tops, yarn and alpaca yarn; iron and steel without old iron; machinery without sewing machines. For 1897-98, given
  in both No. 46 and No. 59, every good agrees to the pound. The tables' own grand totals 1868-84 equal C5b2a's.
- New `bidb/change_trade_goods.py`, nine series `sa_goods_*` in three graphs (default off, Prosperity and work):
  "Textile exports, 1868-1911", "Coal, iron and machinery exports, 1868-1911", "Main exports, share of all UK
  exports, 1868-1911". Source `stat_abstract_goods_uk`; DATA_LICENSE.md row extended. Change over time: 155 series.
- An electrical-machinery clause in the note was wrong (it was counted with other machinery before 1903, not left
  out) and was corrected before commit.
- Checked in headless Chrome (screenshots of the graphs, no page errors); ui_check `change_trade_goods` added;
  change_trade_values, change_trade, change_tea and map still pass. Tests 187 OK (tests/test_change_trade_goods.py 5).
  Hosted copy and release not updated.
- Next: C5b2b2 (1854-67 and 1912-38 for the same goods), or C5c (occupations by sector).
