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

## 2026-10-24 — C5b2b2a: the main exports by value back to 1854
- C5b2b2 split: C5b2b2a 1854-67 (done), C5b2b2b 1912-38 (pending).
- Read from the page images (leaf = OCR page index, image `page/n<leaf-1>`): No. 16 table 21 pp. 60-66 (1854-55) and
  No. 18 table 26 pp. 68-75 (1856-67), both in item `annual-abstract-of-statistics-gb_1852-1870_14-18`; the editions
  C5b2a used for the same years. 458 figures appended to `data/curated/change/data/trade_goods_abstract_uk.csv`.
- Checks: every printed total (cotton, linen, wool, iron and steel) agrees with its parts; the tables' grand totals
  equal C5b2a's summary figures 1854-69; every figure without a total (coal, yarns, machinery, tin plates) is printed
  the same in at least one other edition's OCR. The one total that failed (iron 1867, short by 500,000) was a worn
  "8" in railroad iron: 4,861,129 (total and Nos. 19-30), noted in the readings file.
- Definitions at the 1868 join, checked on the scans: No. 18 lists tin plates under tin, so they are added to iron and
  steel (No. 30's "tinned plates" for 1868 = No. 18's tin plates, 2,092,868); No. 22 says manufactures of steel were
  "Included with Hardwares and Cutlery previous to 1862", and No. 18 never shows them, so they count from 1868
  (£0.36-0.47m in 1862-67, Nos. 22 and 24; not added); coal before 1868 is coals, cinders and culm, the fuel row
  starting in No. 19 (1857 on), kept to No. 16/18 for one definition before 1868 (1868: 5,352,525 vs 5,437,922).
- `bidb/change_trade_goods.py`: new row names (iron_wrought, iron_barrail, iron_hoopswrought, tin_plates), tin plates
  in `old_goods`, graph titles from the years ("Textile exports, 1854-1911" ...), notes on the join; the cotton note's
  lowest point now counts from 1868 (1854 was both first and lowest) and gives 1861 → 1862 (46.9 → 36.8 £m), without
  a cause. Source `stat_abstract_goods_uk` citation and DATA_LICENSE.md row extended.
- Checked in headless Chrome (screenshot of the three graphs); ui_check `change_trade_goods` (pattern now 1854-1911),
  `change_trade_values`, `change_trade`, `map` pass. Tests 187 OK. Hosted copy and release not updated.
- Next: C5b2b2b (1912-38 from Nos. 70-83), or C5c (occupations by sector).

## 2026-10-24 — C5b2b2b: the main exports by value 1912-38
- Read from the page images (leaf = OCR page index, image `page/n<leaf-1>`): No. 70 table 212 pp. 334-345
  (1911-25) and No. 83 table 288 pp. 410-421 (1924-38), the editions C5b2a used. 1,614 figures appended to
  `data/curated/change/data/trade_goods_abstract_uk.csv` as rows `n70_*` / `n83_*`, plus No. 70's grand totals
  (`n70_all`, equal to C5b2a's UK produce 1911-25; No. 83's £'000 totals agree too).
- These tables print no totals. Every figure was searched for in the OCR text of Nos. 60-92 (digits only, OCR
  punctuation ignored): all but the 1911 column (No. 59 ends there, checked below) and mostly 1937-38 were found in
  another edition; the rest were read again from enlarged crops. Two settled from other editions: No. 70's blurred
  1922 wool hosiery (3,890,469 in Nos. 71-74) and No. 83's 1932 worsted mixed tissues, printed "1,661," (1,661,907 in
  Nos. 79-82); noted per figure.
- The classification of 1920 brought back to the old totals (`c20_goods`), and the overlaps explained to the pound:
  1911 against No. 59 (No. 59 kept for 1911): cotton +841,010 (hosiery and gloves 619,486 moved to apparel; waste from
  worked cotton 1,460,496 in other cotton manufactures, shown in Class II only from 1920), wool +8,570 (flocks in other
  woollen manufactures; wool hosiery added back from apparel), iron -2,196 (old rails), machinery -469,774 (road
  locomotives not shown; rail locomotives added from vehicles), coal, yarns and linen equal. 1924-25, No. 70 against
  No. 83 (No. 83 used): iron -411,689 / -381,646 and machinery +1,981,217 / +1,841,590 (boilers and boiler-house plant
  gathered under machinery; railway axles, tyres and wheels, a vehicles row in No. 83, added back to iron);
  `C20_KNOWN` holds these, `overlap` fails on anything else.
- `bidb/change_trade_goods.py`: `c20_goods`, `C20_*` row lists, the No. 70 total check, notes for 1912-38 (definitions
  at both joins, war years and the Irish Free State from April 1923, values for 1913 and the peaks, no causes), region
  "all Ireland to March 1923". Source `stat_abstract_goods_uk` citation and DATA_LICENSE.md row extended. Graphs now
  1854-1938: cotton 126.5 £m in 1913, 401.4 in 1920, 49.4 in 1938; coal 120.3 in 1920, 20.5 in 1926, 40.7 in 1938;
  textiles 17.0% of exports of UK produce in 1938.
- Checked in headless Chrome (screenshot of the graphs); ui_check `change_trade_goods` (pattern 1854-1938),
  `change_trade_values`, `change_trade`, `map` pass. Tests 189 OK (2 new in tests/test_change_trade_goods.py).
  Hosted copy and release not updated.
- Next: C5b2b3 (main imports 1854-1938, UK produce 1840-53), or C5c (occupations by sector).

## 2026-10-24 — C5b2b3a: the main imports by value 1854-1911
- C5b2b3 split: C5b2b3a values 1854-1911 (done), C5b2b3b 1912-38 (Nos. 70, 83), C5b2b3c quantities, C5b2b3d UK
  produce exports 1840-53.
- Read from the page images (leaf = OCR page index, image `page/n<leaf-1>`): No. 16 table 11 pp. 26, 30 (1854-55),
  No. 18 table 16 pp. 32-39 (1856-67), No. 30 table 22 pp. 46-53 (1868-82), No. 45 table 28 pp. 68-78 (1883),
  No. 46 table 28 pp. 70-81 (1884-98), No. 59 table 41 pp. 140-145 (1897-1911), and No. 62 table 39 p. 142 for 1904
  grain (No. 59's column is lost in the binding). 1,496 figures in new
  `data/curated/change/data/trade_imports_abstract_uk.csv`. OCR page index downloaded for No. 62's item.
- Checks: every printed total agrees with its parts (corn in Nos. 16-46, raw sugar and timber in Nos. 16/18, No. 59's
  grain and flour, wood and timber, wool); every figure without a total found printed in another edition's OCR (whole
  numbers only now: the old substring search let 348,338 match 2,348,338). Settled: No. 30 prints 1868 other corn
  1,981,558 (Nos. 14-26: 1,981,553, which makes its total agree); 1875 raw sugar and 1863 raw sugar cut at the page
  edge (other editions and the total); No. 46's 1885 teak 348,338 (Nos. 45, 48: 648,338) and 1884 hewn 303,936 (Nos.
  43-45: 303,966); 1886 sawn fir 7,813,046 is right (No. 48's page; the OCR reads 8).
- Definitions at the joins: No. 59's grain minus rice, rice meal and farinaceous = the old "Total of Corn" less lentils
  (with seeds to April 1902): 1897 -46,919, 1898 -57,855; wool = sheep's + alpaca etc. + flocks (No. 46's "other kinds
  and flocks" = No. 59's alpaca + flocks exactly), 1898 sheep's wool revised +149,713 in No. 59; sugar = refined +
  raw (molasses, glucose out); timber = hewn (with teak, pit props) + sawn + staves (mahogany, furniture woods out).
  Nos. 40-42 print 1883 hewn and sawn equal to No. 45's parts. Later editions (Nos. 19-22) give 1866-67 timber
  ~0.36 million above No. 18 (no footnote found); No. 18 kept, gap in the note.
- New `bidb/change_trade_imports.py`, nine series `sa_imports_*` in three graphs (default off, Prosperity and work):
  "Food imports, 1854-1911", "Raw material imports, 1854-1911", "Main imports, share of all imports, 1854-1911".
  Source `stat_abstract_imports_uk`; DATA_LICENSE.md row extended. Change over time: 164 series.
- Two phrases written from memory (wheat price halving, cotton prices fourfold) were removed from the notes before
  commit; the notes give only the Abstract's figures.
- Checked in headless Chrome (screenshot of the three graphs); ui_check `change_trade_imports` added,
  `change_trade_goods`, `change_trade_values`, `map` pass. Tests 194 OK (tests/test_change_trade_imports.py 5).
  Hosted copy and release not updated.
- Next: C5b2b3b (imports 1912-38 from Nos. 70 and 83), or C5c (occupations by sector).

## 2026-10-24 — C5b2b3b: the main imports by value 1912-38
- Read from the page images (leaf = OCR page index, image `page/n<leaf-1>`; images cached in
  `<cache>/stat_abstract_img/`): No. 70 table 206 pp. 304-309 (leaves 318-323, 1911-25) and No. 83 table 285
  pp. 392-397 (leaves 414-419, 1924-38). 441 figures appended to
  `data/curated/change/data/trade_imports_abstract_uk.csv` (rows `n70_*`, `n83_*`): wheat, barley, oats, maize,
  wheat meal and flour; refined and unrefined sugar; tea; raw cotton (and unmanufactured waste from 1920); sheep's
  and lambs' wool; wood and timber (No. 70: sawn soft, pit props, other; No. 83: sawn hard, sawn soft, planed or
  dressed, pit props, other).
- No totals printed. 399 figures found printed the same in another edition's OCR (whole numbers). Of the other 42 (25 of 1929-37, 16 of 1938, and 1911 unrefined sugar = No. 59's beet + cane),
  the 1929-37 ones were checked on No. 82's page images (pp. 397, 399, 401, same table 285): all agree; the
  near-misses in other editions' OCR were OCR slips (oats 1933 1,206,558, read 1,206,568/658; refined sugar 1936
  248,651, read 238,651/218,651). 1938 (printed in No. 83 only) read again from enlarged crops; noted per figure.
- Joins: 1911 in No. 70 equals No. 59 in every shared row (wheat, barley, oats, maize, flour, refined sugar,
  unrefined = beet + cane, tea, raw cotton, sheep's wool, sawn fir, pit props, wood total). The 1920 classification
  drops peas, beans, rye, lentils and other meals (-3,229,254 in 1911), alpaca and flocks (-395,477) and counts
  mahogany and furniture woods with timber (+2,047,148): `C20_KNOWN`, stated in the notes; 1911 kept from No. 59.
  1924-25: Nos. 70 and 83 agree to the pound in every good. Cotton: raw with linters and waste to 1919 (1919 one
  figure), raw without linters + waste from 1920. Wool includes noils to 1919 (footnote).
- `bidb/change_trade_imports.py`: `c20_goods`, `C20_GRAIN`, `C20_WOOD`, `C20_KNOWN`, `overlap` over all three
  joins; notes give 1913 and the peaks, the breaks, and the Irish Free State from April 1923; region "all Ireland to
  March 1923". Source citation (Nos. 70, 82, 83) and DATA_LICENSE.md row extended. Graphs now 1854-1938: grain and
  flour 215.5 £m in 1920, 67.7 in 1938; raw cotton 256.5 in 1920, 29.1 in 1938; food 12.8% of imports in 1938.
- Checked in headless Chrome (screenshot of the graphs); ui_check `change_trade_imports` (pattern 1854-1938),
  `change_trade_goods`, `change_trade_values`, `map` pass. Tests 195 OK (1 new). Hosted copy and release not updated.
- Next: C5b2b3c (quantities of the same imports), C5b2b3d (UK produce exports 1840-53), or C5c (occupations).

## 2026-10-24 — C5b2b3c1: the main imports by quantity, 1868-1911
- C5b2b3c split: C5b2b3c1 1868-1911 (done), C5b2b3c2 1854-67 (Nos. 16, 18), C5b2b3c3 1912-38 (Nos. 70, 83).
- Read from the page images (leaf = image `page/n<leaf-1>`; for No. 30 the OCR page index runs one leaf off,
  so pages were found by their printed page numbers): No. 30 table 21 leaves 516-521 (pp. 40-45), No. 45 table 27
  leaves 62, 68, 70 (pp. 58, 64, 66; 1883 column), No. 46 table 27 leaves 332-341 (pp. 60-69), No. 59 table 40 leaves
  136-141 (pp. 124-129), No. 62 table 38 leaf 134 (p. 126, 1904 grain, lost in No. 59's binding). 1,019 figures in
  new `data/curated/change/data/trade_quantities_abstract_uk.csv` (rows `q_*` old tables, `q59_*` No. 59).
- Checks: every total of corn agrees with its parts (1890's printed total has a worn digit, 155,6?0,973: the parts
  and the OCR of five other volumes give 155,620,973). Every figure found printed the same in another edition's OCR
  text (whole numbers, editions covering the year; the hocr page indexes of Nos. 43-44 and 47-48 downloaded); the
  rest read on other pages: 1883 teak and other wool on No. 44 p. 66, 1896 other corn on No. 48 p. 59; 1898 sheep's
  wool is printed 694,701,454 in No. 48 and No. 59 against No. 46's 689,446,139 (a revision, as found for its value).
  Value ÷ quantity, year by year per row, as a check on the readings: smooth everywhere; the jumps are real ones that
  move several rows together (sugar -30% in 1884 in all four rows; 1905's sugar dearer).
- Units: No. 59 prints 1911's raw cotton in centals of 100 lb ("Stated in Centals of 100 lbs. in 1911, and in Cwts.
  in prior years"); converted in `tons`. Pit props are inside hewn fir to 1900, a row of their own from 1901.
- Joins: No. 59 against No. 46 (1897-98) equal in cotton, sugar, tea and timber; grain differs by lentils (-170,264
  and -189,780 cwt, matching the value differences), wool by 1898's revision. No. 44's 1882 column (sheep's 484.9 +
  other kinds and flocks 5.2 million lb) is 1.1 million lb above No. 30's one wool row: stated in the note.
- New `bidb/change_trade_quantities.py`; 12 series `sa_qty_*` in five graphs (default off, Prosperity and work): "Food
  imports by weight", "Raw cotton and wool imported by weight", "Timber imported", "Food import prices" and "Raw
  material import prices" (value per unit as an index, 1900 = 100; the charts draw at most three lines, so prices are
  two graphs). Source `stat_abstract_qty_uk`; DATA_LICENSE.md row extended. Change over time: 176 series.
- A timber-load definition written from memory was taken out of the note before commit.
- Checked in headless Chrome (screenshots of the five graphs); ui_check `change_trade_quantities` added,
  `change_trade_imports`, `change_trade_values`, `change_trade_goods`, `map` pass. Tests 201 OK
  (tests/test_change_trade_quantities.py 6). Hosted copy and release not updated.
- Next: C5b2b3c2 (quantities 1854-67), C5b2b3c3 (1912-38), C5b2b3d (UK produce exports 1840-53), or C5c.

## 2026-10-24 — C5b2b3c2: the main imports by quantity, 1854-67
- Read from the page images (leaf = OCR page index, image `page/n<leaf-1>`, cached in `<cache>/stat_abstract_img/`):
  No. 16 table 10 leaves 272, 276 (pp. 20, 24; 1854-55), No. 18 table 15 leaves 534-541 (pp. 24-31; 1856-67), and
  No. 19 table 15 leaves 28-29, 32-33 of the 1857-74 volume (pp. 24-25, 28-29; 1857-67). 384 figures appended to
  `data/curated/change/data/trade_quantities_abstract_uk.csv` (rows `qe_*` for Nos. 16/18; No. 19 under the `q_*`
  names of No. 30, whose rows it matches).
- Units: the corn rows are in cwt as in No. 30, but Nos. 16 and 18 give only wheat, barley, oats, maize and wheat
  flour: no other kinds of corn, no other meal, no total. No. 19 is the first edition with the full table and a
  total of corn (every year's total agrees with its parts), so grain starts in 1857. Nothing else in Nos. 16/18 gives
  all corn (the countries table is wheat and flour).
- Timber: No. 18 gives 6.3-8.5% less than No. 19 every year 1857-67 (1857 sawn 1,316,275 vs 1,478,114 loads; hewn
  with teak 1,210,926 vs 1,228,907; staves the same); No. 18's 1868 is also below No. 30, while No. 19's 1868 equals
  No. 30's in every row. Timber quantities therefore start in 1857 too; the cause is not stated in the Abstract.
- Sugar, tea and wool are printed the same in Nos. 18 and 19 for 1857-67; raw cotton is revised in No. 19 by up to
  0.09%. So 1854-56 for those four come from Nos. 16 and 18 (`early_overlap` enforces this).
- Prices (value ÷ quantity) to 1867 use the quantities of the values' editions (Nos. 16/18; grain from No. 19),
  since the computed values of No. 18 go with its own quantities. No. 16 has no teak quantity though its values
  include teak (noted).
- Checks: every printed total of Nos. 16, 18, 19 agrees with its parts except No. 16's 1854 hewn timber, printed
  1,216,920 (also in other editions of the 1846-65 and 1852-70 volumes) where the parts make 1,216,209, as one
  edition of the 1846-65 volume prints (`SLIPS`). 371 of 384 figures found printed the same on another page of the
  OCR (new page-level check excluding the source page); 1858 barley, hewn and sawn timber confirmed on No. 20's own
  pages (leaves 150, 154); the 1857 figures No. 19 alone prints and No. 18's teak read again from enlarged crops.
- `bidb/change_trade_quantities.py`: `early_goods`, `price_goods`, `early_overlap`, `SLIPS`, `_fields` (per-good
  first years in the notes); graphs now "... 1854-1911", "Timber imported, 1857-1911". Source citation and
  DATA_LICENSE.md row extended; tests 203 OK (2 new); ui_check `change_trade_quantities` (patterns updated),
  `change_trade_imports`, `change_trade_values`, `change_trade_goods`, `map` pass; screenshot checked. Hosted copy
  and release not updated.
- Next: C5b2b3c3 (quantities 1912-38 from Nos. 70 and 83), C5b2b3d (UK produce exports 1840-53), or C5c.

## 2026-10-25 — C5b2b3c3: the main imports by quantity, 1912-38
- Read from the page images already cached for the values (the quantity line sits above each £ line): No. 70
  table 206 leaves 318-323 (pp. 304-309, 1911-25) and No. 83 table 285 leaves 414-419 (pp. 392-397, 1924-38). 410
  figures appended to `data/curated/change/data/trade_quantities_abstract_uk.csv` (rows `q70_*`, `q83_*`; 1936-38
  timber kept as printed in standards and fathoms, rows `*_std`, `*_fathom`).
- No totals printed. Each figure was searched in the OCR of the editions covering its year (Nos. 71-83, own page
  excluded): all but 23 found. Four No. 70 figures were found on No. 71's pages (leaves 336-337, page index and images
  downloaded), which showed my first readings wrong (bold italic 2/3 read as 8: 1919 sawn softwood 4,296,639, 1921
  pit props 1,296,925, 1924 pit props 3,004,269, 1920 raw cotton 18,972,224); five were found on No. 82's cached pages
  (pp. 397, 401); the 14 of 1938 (No. 83 only) were read again from enlarged crops, and No. 83's own OCR agrees for 13.
- Units: raw cotton and wool in centals of 100 lb (No. 70), tea and wool in thousand lb (No. 83). The unmanufactured
  cotton waste row (from 1920) is headed "centals" in No. 70 but "cwts." in Nos. 73-83 for the same figures; cwt used
  and stated.
- Joins (`c20_overlap`): 1911 in No. 70 equals No. 59 in every shared row; the 1920 classification leaves out the other
  grains and meals (-7,692,616 cwt, 3.9%), alpaca and flocks (-8,835,533 lb, 1.1%); 1924-25 Nos. 70 and 83 agree within
  the rounding of thousand lb and centals. Grain's value per cwt in 1911 differs by -0.6% on the new definition.
- Timber: from 1912 the Abstract gives quantities only of sawn softwood and pit props (hewn, other sawn, staves and
  furniture woods by value alone): 8.28 of 9.46 million loads in 1911, and their value per load 89% of all timber's.
  So they are a second line in "Timber imported, 1857-1934" (new series `sa_qty_softwood_uk`, 1911-34) and the timber
  price index goes on with theirs, linked at 1911. Breaks stated: planed softwood and sleepers inside sawn softwood to
  1914 (footnote), other pitwood inside pit props to 1934, standards of 165 cu ft and fathoms of 216 cu ft from 1936
  (the Abstract gives no size for a load, so the line ends in 1934).
- `bidb/change_trade_quantities.py` (415 lines): `c20_goods`, `c20_overlap`, `softwood_values`, `C20_KNOWN`,
  `ROUNDING`; raw cotton in centals from 1911; region "all Ireland to March 1923" as for the values. Graphs now
  1854-1938: raw cotton 1,253 thousand tons in 1912, 568 in 1938; grain and flour 10,381 in 1913, 9,417 in 1938; tea
  235 in 1938; grain price index 78 in 1931 (the lowest), 116 in 1938. Source citation (Nos. 70, 71, 82, 83) and
  DATA_LICENSE.md row extended; Change over time: 177 series.
- Tests 205 OK (2 new); ui_check `change_trade_quantities` (patterns updated), `change_trade_imports`,
  `change_trade_values`, `change_trade_goods`, `map` pass; screenshot of the graphs checked. Hosted copy and release
  not updated.
- Next: C5b2b3d (UK produce exports 1840-53 from Nos. 8 and 13), C5b2c (HMRC since 1996) or C5c (occupations).

## 2026-10-25 — C5b2b3d: the main exports 1846-53
- The roadmap asked for 1840-53 from Nos. 8 and 13, but the earliest scanned volume holds Nos. 8-13 (1846-65); No. 8
  begins at 1846 (Nos. 1-7 are not in the collection), so the series now starts in 1846.
- Read from the page images (file `n<edition>_<leaf>.jpg` in `<cache>/stat_abstract_img/`, image `page/n<leaf-1>`;
  in this volume the OCR page index runs one leaf ahead of the image): No. 8 table 18 p. 36 (leaf 40, 1846-53) and
  table 15 p. 30 (leaf 34, total declared value of British and Irish produce exported). 248 figures + 8 totals
  appended to `data/curated/change/data/trade_goods_abstract_uk.csv`; new row names `cotton_cambric`,
  `iron_wroughtall` (old iron inside), `tin_pewter` (tin plates and tin and pewter ware), `iron_oldin`.
- Checks: all 32 printed totals (cotton, iron and steel, linen, wool) agree with their parts; every 1847-53 figure
  printed the same on No. 9's p. 36 (leaf 112); 1846 read again from 2× crops; No. 8's 1854 column (p. 37) equals
  No. 16's in every good; total exports 1848-53 equal the totals printed in No. 10's table 19 and No. 13's table 17.
- Iron and steel: No. 8 has no separate old iron or tin plates. Tin plates from No. 10 p. 52 (1848; leaf 200) and
  No. 11 p. 52 (1849-50; leaf 290) and No. 13 p. 60 (1851-53; leaf 494); old iron from Nos. 11 and 13 (1849-53),
  whose wrought iron + old iron = No. 8's wrought iron of all kinds. 1846-47 keep old iron and take the tin and
  pewter line (about 1% high), 1848 keeps old iron (0.7%); `EARLY = 1849` and `old_goods` raise if old iron is
  missing from 1849 on. Stated in the metals note.
- Shares 1846-53 use No. 8's total (the summary table in change_trade_values begins in 1854 because imports had no
  real values before then). Graphs: "Textile exports, 1846-1938" (cotton 25.6 £m in 1846, 22.7 in 1848, 32.7 in
  1853), "Coal, iron and machinery exports, 1846-1938", textiles 63.2% of exports in 1846, 50.8% in 1853.
- Source citation (Nos. 8-13), DATA_LICENSE.md, INTERFACE.md updated; tests 206 OK (1 new); ui_check
  `change_trade_goods` (pattern updated), `change_trade_values`, `change_trade_imports`, `change_trade_quantities`,
  `map` pass; screenshot of the graphs checked. Hosted copy and release not updated.
- Next: C5b2c (HMRC since 1996), C5b3 (before 1800, needs the books) or C5c (occupations).


## 2026-10-25 — C5b2c: the main goods since 2000 (HMRC)
- New `bidb/change_trade_hmrc.py` (262 lines): HMRC's uktradeinfo OTS API (OGL) with OData `$apply`: per year one
  request sums value and net mass by HS heading over the headings needed (`GOODS`, `RANGES`), one more sums all goods
  by month and flow (`complete` requires all 12 months of EU and non-EU imports and exports). Requests 6 s apart via
  `bidb.http` (cached on FANTOM). The API's data begin in January 2000: 1996-99 return nothing, so the roadmap's 1996
  became 2000; 2026 has 8 months and is left out.
- Totals: exports 195.0 bn in 2000, 364.4 bn in 2025; imports 234.2 → 606.1 bn (2022: 635.2 bn, ONS goods imports
  about 634 bn). Shares are of all goods less non-monetary gold (7108: 61.8 bn exported, 116.9 bn imported in 2025).
  Suppression checked for 2024: within these headings only ferro-alloys (7202) are flagged, and their values are
  still in the sums.
- 21 series, 8 graphs beside the Statistical Abstract ones: textile exports (cotton 241.9 → 122.0 £m), coal, iron and
  machinery exports (machinery 36,644 → 84,328 £m), main exports' share (textiles 0.29% → 0.10%; coal, iron and
  machinery 20.9% → 25.4%), food imports (grain 304 → 1,409 £m), raw material imports (raw cotton 22.9 → 2.2 £m),
  main imports' share, food imports by weight (grain 2,672 → 6,026 kt; tea 156 → 110), raw cotton and wool by weight
  (raw cotton 18.7 → 0.73 kt, 971 thousand tons in 1913). Notes give the headings used, what differs from the
  Abstract (re-exports included, made-up textiles left out), the 2021 Intrastat → customs break, and 1913/1938 values.
  A first note wrongly called raw cotton 1913's largest import (grain and flour 77.7 £m > cotton 70.6); corrected.
- Source `hmrc_ots` in change/sources.json; trade/sources.json years corrected; DATA_LICENSE.md, INTERFACE.md
  updated; tests 209 OK (3 new); ui_check `change_trade_hmrc` (new), `change_trade_goods`, `change_trade_imports`,
  `change_trade_quantities`, `map` pass; screenshot of the graphs checked. Hosted copy and release not updated.
- Next: C5b2d (1939-99 to join the eras; hosted copy), C5b3 (before 1800, needs the books) or C5c (occupations).

## 2026-10-25 — C5b2d1: the main goods 1938-1952 by group
- C5b2d split into four parts (roadmap): the Internet Archive collection holds the Annual Abstract to No. 135 (1999),
  but trade tables change classification (1920 groups to No. 90; SITC from No. 91), so 1938-52 first.
- Read from the page images (`<cache>/stat_abstract_img/n<edition>_<leaf>.jpg`; the archive's `page/nX` is leaf X+1):
  No. 84 tables 215/217/219 (pp. 178-182), No. 88 tables 217/219/221 (pp. 207-211), No. 89 tables 208/209/211 and
  No. 90 tables 207/208/210 (pp. 196-199). 858 figures in `data/curated/change/data/trade_groups_abstract_uk.csv`.
- Checks: every edition's five class totals equal its printed totals of imports and exports (within rounding; No. 84
  prints whole millions). Editions revise earlier years (e.g. machinery 1938: 57.9 in No. 84, 57.2 from No. 88; No. 90
  moves 0.5-1.8 £m into wool for 1946-51), so each year comes from the latest edition printing it. The goods used are
  printed the same in another edition (1939-40 confirmed in Nos. 85 and 86's OCR) or were read again from 2x crops
  (No. 90, 1946-52).
- New `bidb/change_trade_groups.py` (235 lines): 15 series, 6 graphs (textiles, coal/iron/machinery, export shares,
  main imports, import shares, all imports and exports), 1938 compared with the Statistical Abstract in each note.
  Cotton goods 34.2 £m in 1943, 209.4 in 1951; machinery 27.9 → 421.7 £m 1943-52; coal 42.3 £m in 1939, 2.7 in 1947.
  A first draft of a note gave the Korean War as the cause of the 1951 peak without a source; removed.
- Source `annual_abstract_groups_uk`, DATA_LICENSE.md row (public domain: published 1947-53), INTERFACE.md; tests
  213 OK (4 new); ui_check `change_trade_groups` (new), `change_trade_hmrc`, `change_trade_goods`,
  `change_trade_imports`, `change_trade_values`, `map` pass; screenshot of the graphs checked. Hosted copy and release
  not updated.
- Next: C5b2d2 (1953-~1977, SITC tables from No. 91).

## 2026-10-25 — C5b2d2a: the main goods 1958-1974 by SITC (R) division
- Edition ranges found from the OCR (Nos. 91-114 cached in `<cache>/stat_abstract/`): No. 91 begins SITC (1954),
  No. 101 SITC (R); each edition prints nine years (No. 104: 1958-66, No. 108: 1962-70, No. 112: 1966-74).
  C5b2d2 split: No. 102 and earlier leave out precious stones (1958 imports 3,747.5 against No. 104's 3,833.5 £m),
  so 1953-57 is C5b2d2b.
- Read from the page images (`<cache>/stat_abstract_img/n<edition>_<leaf>.jpg`): No. 104 tables 270-271 (leaves
  236-238, pp. 222-224), No. 108 tables 272-273 (leaves 260-262, pp. 244-246), No. 112 tables 303-304 (leaves 303-305,
  pp. 285-287). Every division of every section: 3,294 figures in `data/curated/change/data/trade_sitc_abstract_uk.csv`.
- Checks: divisions against section totals (rounding allowed per part), sections against the total and the 5-8
  subtotal: all pass but 1969 fuel imports (printed 906.5, parts 906.2, in Nos. 108 and 112; crop checked; `KNOWN`).
  Overlaps: imports 1962-65 in Nos. 104 and 108 and both sides 1966-69 in Nos. 108 and 112 equal in every figure
  (No. 108 puts furniture imports in "other"); only each edition's last year is revised.
- Exports: re-exports counted with exports from 1970 and restated back to 1962 in Nos. 108 and 112; No. 104 is UK
  produce only, used for 1958-61. 1962: 4,062.3 with re-exports, 3,904.6 without.
- New `bidb/change_trade_sitc.py` (240 lines): 15 series, 6 graphs (textiles, coal/iron/machinery, export shares,
  main imports, import shares, totals). Textiles 7.7% of exports in 1958, 4.5% in 1974; coal 31.4 £m → 14.0 in 1967;
  machinery 773.8 → 4,213.0 £m; cereals, sugar, coffee/tea/cocoa 13.6% of imports in 1958, 5.6% in 1974.
- Source `annual_abstract_sitc_uk`, DATA_LICENSE.md row (public domain: published 1967-75), INTERFACE.md; tests 218
  OK (5 new); ui_check `change_trade_sitc` (new), `change_trade_groups`, `change_trade_hmrc`, `change_trade_goods`,
  `map` pass; screenshot of the graphs checked. Hosted copy and release not updated.
- Nos. 113 (1976) onwards are still Crown copyright under the 50-year rule: 1975+ needs the OGL question (C5b2d3).
- Next: C5b2d2b (1953-57: No. 102 and the original SITC of Nos. 91-100).

## 2026-10-25 — C5b2d2b: the main goods 1953-1957 by the classes of the original SITC
- Nos. 99 (1962: 1953-61) and 100 (1963: 1954-62) print imports and exports by the Board of Trade's classes (A-E) and
  divisions of the original SITC; read from the page images (`<cache>/stat_abstract_img/n99_220-221`,
  `n100_220-221`): every division, 1,890 figures in `data/curated/change/data/trade_classes_abstract_uk.csv`.
- Checks: every division against its class total and the classes (with class E's two lines) against the total, all
  pass; 1954-60 identical in Nos. 99 and 100 on both sides (only No. 99's 1961 first estimate revised).
- No. 102 (SITC (R) without precious stones) not used: the series take 1953-57 on the classes basis and change basis
  once, at 1958; the notes give 1958 both ways (No. 100 against No. 104): coal, wood, coffee-tea-cocoa equal, the
  other goods within 2%; imports 3,747.5 against 3,833.5 and exports 3,176.2 against 3,249.8 £m, mostly precious stones.
  Exports 1956-57 include Lend-Lease silver repayments (22.4, 7.1 £m; footnote to No. 100's table 258).
- New `bidb/change_trade_classes.py` (74 lines), read by `change_trade_sitc.run`; the 15 `aas_` series now run
  1953-1974 with both sources; notes rewritten for the join. Textiles 12.7% of exports in 1953; coal 69.8 £m in 1953.
- Hardening: the sum checks (`change_trade_sitc.near`, shared) allowed half a unit per part, 1.2 for class D's 23
  parts, so a misread of 1.0 passed; now capped at ~4 standard deviations of the rounding (0.59 for 23 parts; the
  largest real residual is 0.3). All SITC (R) readings still pass.
- Source `annual_abstract_classes_uk`, DATA_LICENSE.md row (public domain: published 1962-63), INTERFACE.md; tests 223
  OK (4 new); ui_check `change_trade_sitc` (spans now 1953-1974) and `change_trade_groups` pass; screenshot checked.
  Hosted copy and release not updated.
- Next: C5b2d3 (1975/1978-1999; the OGL question for Nos. 113 onwards first).

## 2026-10-25 — C5b2d3: the main goods 1962-2024 as shares, from the Growth Lab (public domain)
- The OGL question for Annual Abstract No. 113 (1976) onwards: The National Archives makes the OGL the default licence
  for Crown copyright and says re-use under the old waiver (which included "headline statistics") moves to the OGL,
  but nothing found says plainly that whole HMSO tables from before 2010 are covered. George chose "a source that is
  clearly OK for us to use", without asking permission. ONS's MRETS (OGL) starts only in 1997.
- Source: the Growth Lab at Harvard University's International Trade Data (SITC, Rev. 2), Harvard Dataverse
  doi:10.7910/DVN/H8SFD2, CC0 1.0 (UN Comtrade reconciled with partners' reports; the Atlas asks for citation).
  `sitc_country_product_year_2.csv` (50 MB) in `<cache>/growthlab/`. In US dollars, so shares only.
- New `bidb/change_trade_atlas.py` (155 lines): 9 series `gl_*_uk`, 1962-2024, shares of all goods but non-monetary
  gold (97: 12.2% of exports and 9.2% of imports in 2024, at most 2.34% before 1980; a hand-written "under 0.2%" in
  the first draft of the note was wrong and is now computed). Same divisions as the `aas_` graphs, machinery = Rev. 2's
  71-77 (27.0% against the official 27.3% in 1962). Mean differences from the Annual Abstract's shares 1962-1974:
  textiles +0.52, coal +0.01, iron +0.08, machinery -0.12, cereals -0.35, sugar -0.02, coffee-tea-cocoa +0.06, wood
  -0.26, fibres -0.02 points; every year within 1.5 points (tested). Textiles 7.2% of exports in 1962, 3.7% in 1975,
  1.9% in 1999, 0.8% in 2024; machinery 27.0, 29.3, 36.2, 28.2%; cereals 5.1, 2.9, 0.6, 1.2% of imports.
- Found while checking the screenshot: `change_charts.draw` draws at most three lines, so the 1938-52 timber line and
  the 1953-74 wood and textile-fibre lines were never drawn. Those graphs are split (timber; wood and fibres), and
  `change_series.check` now refuses a graph with more than `MAX_MODELS` (2) other lines. `change_registers._download`
  takes a cache folder.
- Source `growth_lab_sitc2`, DATA_LICENSE.md row, INTERFACE.md; tests 225 OK (3 new); ui_check `change_trade_atlas`
  (new), `change_trade_sitc`, `change_trade_groups`, `change_trade_hmrc`, `map` pass; screenshots checked (every line
  drawn). Hosted copy and release not updated.
- Next: C5b2d4 (join the eras 1846-2025, breaks marked; hosted copy and release).

## 2026-10-25 — C5b2d4: the main goods 1846-2024 as one line across the eras, breaks marked
- New `bidb/change_trade_joined.py` (165 lines): four joined share series `tj_*_uk` (an `era` column says which era
  each year comes from): textiles and coal/iron/machinery of exports 1846-2024, grain and raw cotton/wool/wood of
  imports 1854-2024; Statistical Abstract to 1938, Annual Abstract groups 1939-52, divisions 1953-74, Growth Lab
  1975-2024. Two graphs (exports, imports), each with the second line as its comparison.
- Decision: HMRC (2000-) not joined; its headings are far narrower than the SITC divisions (textiles 0.29% against
  1.6% in 2000) and the Growth Lab keeps the divisions to 2024. Shares only: values are at the prices of the time and
  the Growth Lab's in dollars.
- Breaks: new series field `breaks` ([[first year on the new definition, text]]), checked by
  `change_series.check_breaks`; `change_charts` starts the line again there with a dotted mark and names the break
  on hover; the /change page lists them under the graph. 1912, 1923, 1939, 1953, 1958, 1962 (exports), 1975; the
  year before on both definitions where two eras give it (1938 textiles 17.0/16.2%; 1974 4.5/4.9%).
- Results: textiles 63.2% of exports in 1846, 31.9% in 1913, 17.0% in 1938, 4.5% in 1974, 1.9% in 1999, 0.8% in
  2024; coal, iron and machinery 12.0, 27.0, 30.2, 29.3, 38.1, 29.7%; grain 14.3% of imports in 1854, 1.2% in 2024.
- Tests 231 OK (6 new); ui_check `change_trade_joined` (new) and the other trade checks pass; screenshot checked.
- Hosted copy version 69: six changed files (series.json, change_charts.js, change_page.js, map.css, buildings.json,
  quiz.json), 252.9 of 256 MiB; hosted files checked by SHA-256 against dist/; static page checks 22/22. No new
  release: the database is unchanged since db-2026-10-24.
- Next: C5b3 (before 1800: Davis, Schumpeter, Mitchell quoted as estimate dots; needs the books' pages).

## 2026-10-25 — C5b3 blocked; C5c1: occupations by sector 1381-2026
- C5b3 (trade before 1800 from Davis 1962, Schumpeter 1960, Mitchell 1988): none of the books is on the Internet
  Archive (searched by title and author, lending copies included) and Davis's article is behind JSTOR, so it stays
  open as blocked, like C2d2b2.
- New `bidb/change_work.py` (181 lines): three graphs in "Prosperity and work", the share of people in work in
  farming, fishing and mining / making and building / services, mining with farming throughout.
  - UK: ONS "Long-term trends in UK employment: 1861 to 2018" Figure 2a (OGL; from the BoE Millennium dataset)
    1920-38 and 1948-77, then workforce jobs by SIC 2007 section from the LMS time series (JWR5-JWR9, JWS2, JWT8,
    DYDC; the yearly figure is June) 1978-2026. Over 1978-2016 the two differ by at most 0.25 points (tested), so
    they are joined without a break mark; 1939-47 dotted (`gap` 5).
  - Ireland: CSO CNNL1 census counts 1926-1996, mining moved from "Industry" to the primary sector (0.1-1%).
  - Dots: Keibek 2017 (Cambridge PhD, open PDF, all rights reserved; DOI 10.17863/CAM.8960, checked: a DOI first
    written from memory was wrong and was corrected) quoted per figure in `estimates.json`: Table 20 (men and women
    20+, England and Wales 1601-1851, printed p.159), Table 22 (1381, Smith's range, men) and Table 23 (c.1525, the
    mean of Keibek's reworked muster lists and the coroners' reports, men). Test: every figure appears in its quote.
- Not used: Shaw-Taylor, Sugden & You 2019 (both sexes 1710-1911; marked "not to be cited without the written
  permission of the authors"); OWID's farming share before 1980 (Broadberry & Gardner benchmarks at rounded years,
  agriculture only); Shaw-Taylor & Wrigley 2014 and Broadberry et al. 2015 (not open).
- Results: farming, fishing and mining 57.8% in 1601, 27.5% in 1851, 14.3% of UK workers in 1920, 1.2% in 2026;
  making and building 33.5% in 1601, 47.7% in 1701, UK peak 40.1% in 1966, 14.0% in 2026; services 8.7% in 1601,
  29.9% in 1851, 51.5% in 1920, 84.8% in 2026. Ireland: primary 53.6% in 1926, 10.7% in 1996.
- Sources `ons_longterm_employment`, `ons_workforce_jobs`, `cso_cnnl1`, `est_work_keibek2017`; DATA_LICENSE.md rows,
  INTERFACE.md; tests 238 OK (7 new); ui_check `change_work` (new), `change_trade_joined`, `change_trade` pass;
  screenshot checked (dots 1381-1851, UK line from 1920, Ireland from 1926). Hosted copy and release not updated.
- Next: C5c2 (1861-1911 censuses by sector; Ireland after 1996) or C5d (prices and real wages: ONS RPI 1800-).

## 2026-10-25 — C5c2 split; C5c2a: Ireland's occupations by sector carried on to 2022
- C5c2 split: the 1861-1911 censuses mean reading page images and regrouping the census orders (dealers into
  services) for three nations, so they are C5c2b (England and Wales, from the 1911 Summary Tables' Table 64 for
  1881-1911) and C5c2c (Scotland, Ireland); the ONS article has no sector shares before 1920 (checked its figures).
- `bidb/change_work.py` (243 lines): `cso_cna26` (censuses 2002-2016) and `cso_f7040` (2011-2022, detailed NACE groups
  split at 09 and 43, checked to add up to the total at work), industry not stated left out; `compare_ie`: the two
  agree within 0.40 points in 2011 and 2016; 2022 from F7040. Notes and the facts give 2022.
- Results (Ireland): primary 10.7% in 1996, 6.8% in 2002, 5.4% in 2006, 4.0% in 2022; making and building 26.6% in
  1996, 26.1% in 2006, 17.4% in 2011 (construction 215,184 → 90,357; manufacturing 243,182 → 193,080; the LFS QLF03
  shows the same fall), 18.6% in 2022; services 62.7% in 1996, 77.4% in 2022.
- Not used: the LFS (yearly from 1998, but mining is inside B-E); Northern Ireland on its own (in the UK line; the
  charts draw at most three lines).
- Source `cso_census_industry`, DATA_LICENSE.md row, INTERFACE.md; tests 240 OK (2 new, the written-series test now
  expects 1926-2022); ui_check `change_work` (now looks for 1926-2022), `change_trade_joined`, `map` pass; screenshot
  checked. Hosted copy and release not updated.
- Next: C5c2b (England and Wales 1861-1911 from the census reports) or C5d (prices and real wages).

## 2026-10-25 — C5c2b split; C5c2b1: England and Wales at the censuses of 1881-1911
- C5c2b split: 1881-1911 from the 1911 Summary Tables (done, C5c2b1); 1861 and 1871 from their own reports (C5c2b2).
- Source: Census of England and Wales 1911, Summary Tables (Cd. 7929, 1915; public domain), Internet Archive
  `censusofenglandw1911grea`. The OCR of the occupation tables is unusable, so read from the page images
  (`page/n<leaf>_w2000.jpg`; leaves found from the hOCR search text): Table 65 on leaves 283, 285, 287 (pp. 274-278),
  Table 64 on leaf 281 (p. 272, printed sideways, by sex).
- `data/curated/change/data/work_census_ew.csv` (316 figures, edition/leaf/page/table, notes on three cells). New
  `bidb/change_work_ew.py` (156 lines): `check` tests the 22 orders against the total occupied, the lines of orders
  XX and XXII against their order, and Table 64's food, tobacco and drink lines (males + females) against Table 65's
  lines. It found three misreadings, all corrected: order I 1911 (289,261, read 239,261), defence 1901 (168,238;
  the persons figure is smudged, the order has no women) and greengrocers 1901 women (11,927); chocolate and grocers
  1901 women are misprinted and were rebuilt from the under-15 and over-15 columns. All sums now agree.
- Grouping: farming, fishing and mining = orders VII-IX; making and building = X-XXI less dealers + engine drivers;
  services = I-VI + dealers (metals and machines, drapers; food, tobacco and drink dealers and inns from Table 64,
  the census's own maker/dealer headings: butchers and bakers (dealers) to services, millers, curers, bread makers,
  brewers, maltsters, distillers to making) + general shopkeepers, pawnbrokers, costermongers. Left out: general
  labourers and order XXII's "others" (6.1% in 1881, 2.8% in 1911). 1881-91 brackets (millers with corn dealers,
  cocoa makers with grocers, tobacco makers with tobacconists...) shared out as in 1901.
- Results (England and Wales): farming, fishing and mining 18.2% (1881), 16.4%, 14.7%, 15.0% (1911); making and
  building 42.6, 41.9, 43.3, 41.7%; services 39.2, 41.7, 42.0, 43.3%.
- `change_work`: the census points join Keibek's dots (`with_census`; the graphs already draw three lines), label
  "England and Wales (Keibek; census)", source `census_ew_1911`, notes and facts give 1881 and 1911.
- Tests 248 OK (8 new); ui_check `change_work` (now looks for the censuses), `change_trade_joined`, `map` pass;
  screenshot checked. Hosted copy and release not updated.
- Next: C5c2b2 (1861 and 1871 from their own reports) or C5d (prices and real wages).

## 2026-10-25 — C5c2b2: England and Wales 1861 and 1871 from Booth (1886)
- The 1861 and 1871 reports' occupation tables are not on the Internet Archive (searched: only the 1861 population
  tables, 1871 Vols I-II and the 1881 Vols I and III). Used instead Charles Booth, "Occupations of the people of the
  United Kingdom, 1801-81" (J. Statistical Society 49, 1886; public domain; `s4833id1397560`, Wellcome copy),
  Appendix B (1) pp. 414-415 (page images n427-428): England and Wales's self-supporting population 1841-1881 in
  thousands by Booth's sections, the censuses regrouped on one classification with dealers apart.
- `work_booth_ew.csv` (210 figures); `change_work_ew.check_booth`: every manufacture, transport and public service
  subtotal, industrial service, industry and self-supporting total adds up exactly in all five years.
- Grouping as for the census: primary = agriculture, fishing, mining; secondary = building, manufacture; services =
  transport, dealing, commercial, public and professional, domestic; left out = general labour, property owning and
  independent, indefinite. Booth's 1881 (18.19/41.35/40.46) is within 1.28 points of the 1911 tables' 1881
  (18.23/42.59/39.18; Booth moves more dealers out of making); his 1851 (27.1/41.3/31.6) meets Keibek's 1851
  (27.5/42.6/29.9). Only 1861 and 1871 drawn: 24.1/41.3/34.6 and 20.5/41.2/38.3. The dots now run 1851, 1861, 1871,
  1881...1911 with no gap.
- Source `booth_1886`, DATA_LICENSE.md row, INTERFACE.md; tests 252 OK (4 new); ui_check `change_work` (now looks for
  Booth), `change_trade_joined` pass; screenshot checked. Hosted copy and release not updated.
- Lead noted in the roadmap: Booth's Appendix B (2) and (3) give Scotland and Ireland 1841-1881 the same way (C5c2c).
- Next: C5c2c (Scotland and Ireland 1841-1911: Booth to 1881, then the census reports) or C5d (prices and real wages).

## 2026-10-25 — C5c2c split; C5c2c1: Scotland and Ireland 1841-1881 from Booth
- Booth (1886) Appendix B (2) Scotland (pp. 418-419, page images n431-432) and B (3) Ireland (pp. 422-423, n435-436),
  read into `work_booth_sc.csv` and `work_booth_ir.csv` (210 figures each); `check_booth` passes for every year.
- New `bidb/change_work_nations.py` (100 lines), called from change_work.run (`write(..., extra=)`): graphs "Work by
  sector: Scotland, 1841-1881" and "Work by sector: Ireland, 1841-2022", the three sectors as lines (`gap` 10; Ireland
  breaks at 1926: the whole island to 1881, the 26 counties from 1926, from the CSO tables already read).
- Results: Scotland farming, fishing and mining 31.1% (1841), 30.1, 27.8, 26.0, 23.1% (1881); making and building
  42.7-44.5%; services 26.1% to 32.7%. Ireland 54.1, 54.1, 48.3, 46.2, 46.4%; making and building 30.8% to 20.1%;
  services 15.1% to 33.5%. Left out (general labour, independent, indefinite): Scotland 5.5-13.4%, Ireland 4.9-10.2%.
- Tests 258 OK (6 new); ui_check `change_work`, `change_work_nations` (new), `change_trade_joined` pass; screenshots
  of both graphs checked. The app on port 5050 had stopped during the session (screenshots taken with a temporary
  server). Hosted copy and release not updated.
- Next: C5c2c2 (Scotland and Ireland 1891-1911 from the census reports) or C5d (prices and real wages).

## 2026-10-25 — C5c2c2 split; C5c2c2a: Scotland at the censuses of 1901 and 1911
- Searched the Internet Archive: Scotland's 1911 report Vol. II (`b32177264_0004`, Cd. 6896) has Table D1, every
  occupation line for 1911 and 1901 by sex with the intercensal change; the 1901 report's occupation volumes are empty
  stubs; the 1891 report is there (`tenthdecennialce0002vari`). Ireland has no 1911 General Report online (the four
  province volumes are), but the 1891 and 1901 General Reports are.
- Table D1 (leaves 86-97, pp. lxxv-lxxxvi) read from the page images into `work_census_sc.csv`: 397 lines, 1901
  braces on the first line of their `bracket`, italic repeats (lines 96, 159, 201, 301, 369-372 printed beside the
  lines they were joined with in 1901) counted once. Every line agrees with its printed change; males add exactly to
  the printed totals, females of 1911 too; females of 1901 add to 97 fewer than the printed 591,624 (`KNOWN`).
- New `bidb/change_work_sc.py` (125 lines): every dealer to services (as Booth), order XXII line by line, only general
  labourers left out (2.8%, 1.7%). Scotland: farming, fishing and mining 19.0% (1901), 19.1% (1911); making and
  building 43.6%, 41.7%; services 37.4%, 39.2%. `change_work_nations` draws them after Booth's 1841-1881 with a break
  at 1901; graph now "Work by sector: Scotland, 1841-1911". Source `census_sc_1911`, DATA_LICENSE.md row, INTERFACE.md.
- Tests 266 OK (8 new); ui_check `change_work_nations` (now looks for the 1901 break), `change_work`,
  `change_trade_joined` pass; screenshot of the graph checked. Hosted copy and release not updated.
- Next: C5c2c2b (Scotland 1891), C5c2c2c (Ireland 1891-1911).

## 2026-10-25 — C5c2c2b: Scotland at the census of 1891
- Census of Scotland 1891, Vol. II, Part II (C. 7134, 1893; `tenthdecennialce0002vari`): the summary of occupations
  for all Scotland (classes and orders p. 2, sub-orders p. 3, occupations pp. 4-9; leaves 41-48) read from the page
  images into `work_census_sc_1891.csv` (330 rows: 80 printed sub-order totals, 49 dealer-free sub-orders whole, 201
  lines of class V with a kind). Every sub-order adds to its printed total, the sub-orders to the five class totals.
- New `bidb/change_work_sc_1891.py` (115 lines). Grouped as 1901-1911 line for line; six lines joining makers and
  dealers shared out as in 1901 (furniture 7% dealers, clothes 93%, provisions 46%, bakers and confectioners 34%,
  tobacco 37%, platelayers vs navvies 52%). Scotland 1891: farming, fishing and mining 19.8%, making and building
  42.7%, services 37.5%; general labourers left out 3.7%. Drawn between breaks at 1891 and 1901.
- Source `census_sc_1891`, DATA_LICENSE.md row, INTERFACE.md. Tests 271 OK (5 new); ui_check `change_work_nations`,
  `change_work` pass; screenshot checked. Hosted copy and release not updated.
- Next: C5c2c2c (Ireland 1891-1911).

## 2026-10-25 — C5c2c2c scoped (Ireland 1891-1911), not started
- Ireland kept the 1881 classification to 1911, so dealers need the line tables. Found: the 1901 General Report's
  Table 91 (1891 and 1901 by sub-order, pp. 398-401) and Table 20 (all lines, males from p. 117, then females); the
  1891 General Report; for 1911 only the four province volumes. Split in the roadmap into C5c2c2c1-c4 with page
  locations and the definitional traps (students in class I in 1891, farmers' relatives, general labourers).

## 2026-10-25 — C5c2c2c1: Ireland 1891 and 1901 by sub-order (Table 91)
- Census of Ireland 1901, General Report (Cd. 1190, `op1254515-1001`), Table 91 pp. 398 and 400 (page images n443,
  n445, `page/n<N>_w2400.jpg`, served at 1,200 px but legible when cropped and enlarged): all ages, persons, males and
  females, 1891 and 1901, for the 6 classes, 24 orders and 80 sub-orders → `work_census_ir_t91.csv` (114 rows).
- New `bidb/change_work_ir.py` (95 lines): `check` tests persons = males + females on every row and every order,
  class and total in all six columns. All agree but one printed figure: board and lodging, women 1901, printed 5,570,
  is 5,572 by the facing page's age columns (240 + 5,332), by persons and by the order total (`KNOWN`, kept as printed
  in the CSV).
- Figures: occupied (classes I-V) 2,145,729 (1891), 1,963,817 (1901); agricultural class 936,759 and 876,062;
  industrial class 656,410 and 639,413; general labourers (22.2) 133,082 and 139,272; "literary and scientific
  persons" (mostly students) 93,280 and 8,378.
- Not drawn yet: class V's orders join makers and dealers. DATA_LICENSE.md row, INTERFACE.md. Tests 276 OK (5 new).
- Next: C5c2c2c2 (1901 occupation lines, Table 20 of the same report, males from p. 117, image n162).

## 2026-10-25 — C5c2c2c2-c4: Ireland's occupation lines 1891, 1901, 1911; Ireland drawn 1891-1911
- 1901: Table 20 of the General Report (Cd. 1190). The page views (`page/n<N>`) crop the left-hand pages at the gutter
  and cut off the occupation names; the uncropped scans are file N+1 of `op1254515-1001_images.zip`, fetched with
  `bidb.remote_zip`. 1891: Table 19 of the General Report (C. 6780, `op1252985-1001`). 1911: no General Report online,
  so the four province volumes (`op1256115`-`op1256118`), Summary Tables XIX (classes, sub-orders) and XX (lines).
- Read by eye from the page images (tesseract tried on the 1911 pages: names and figures too unreliable). Only the
  sub-orders that mix sectors were read line by line (orders 8-23 and the students of 3.5): 1,762 lines in
  `work_census_ir_lines.csv`; every sub-order equals its printed total for each sex, year and province, and the 1911
  provinces add to Ireland's 4,390,219 persons. The lines needed no correction.
- New `bidb/change_work_ir_1911.py` (75 lines); `change_work_ir` gains the lines, `check_lines`, `sectors`, `shares`,
  `left_out`. Ireland: farming, fishing and mining 48.2% (1891), 47.4% (1901), 46.4% (1911); making and building 21.8,
  21.8, 21.3%; services 30.1, 30.8, 32.3%; general labourers left out 5.8, 6.0, 8.2%. Drawn on "Work by sector:
  Ireland, 1841-2022" between breaks at 1891 and 1926. Sources `census_ir_1891`, `census_ir_1901_lines`,
  `census_ir_1911`; DATA_LICENSE.md rows; INTERFACE.md.
- Tests 283 OK (7 new); ui_check `change_work_nations`, `change_work` pass; screenshot of the Ireland graph checked.
  Hosted copy and release not updated.
- Next: C5d (prices and real wages).

## 2026-10-25 — C5d: prices since 1800 and real wages
- New `bidb/change_prices.py`: ONS CDKO (long-run RPI 1800-2025, OGL) → "Prices since 1800", drawn on a new log axis
  (`log: true` in series.json; `change_charts.js` draws log10 and labels "log scale").
- New `bidb/change_wages.py`: real wage rates from two indexes read from page images, the Board of Trade's 1879-1912
  (Sixteenth Abstract of Labour Statistics, Cd. 7131, p. 82; both printed means recomputed; 1911's mean without
  agriculture printed 99.83 for 99.80, `KNOWN`) and the Ministry of Labour's weekly rates 1924-1938 (Statistical
  Abstract No. 83, table 138, quarterly, averaged), each over the RPI; and ONS AWE KAB9 2000-2025 at 2025 prices.
  British Labour Statistics: Historical Abstract (1971) is only a restricted lending copy; Phelps Brown–Hopkins is on
  JSTOR: left as C5d2.
- Sources `ons_cdko`, `bot_labour_abstract_16`, `stat_abstract_wages_uk`, `ons_kab9`; DATA_LICENSE.md, INTERFACE.md.
  Tests 289 OK (6 new); screenshots of both graphs checked. Hosted copy and release not updated.

## 2026-10-25 — C5e1: shipping registered and built, 1884-1938
- New `bidb/change_shipping.py`: merchant fleet registered (Statistical Abstract No. 46 table 60, No. 59 table 70,
  No. 70 table 191, No. 83 table 269) and ships built (No. 59 table 71, No. 70 table 192, No. 83 table 270), read
  from page images; every row's parts add to its printed total, and the overlapping years of consecutive editions
  agree. Ships built before 1897 left out (the earlier table excludes ships for foreigners). Source
  `stat_abstract_shipping_uk`. The older multi-volume scans' page views did not match their OCR leaf numbers, so
  shipping before 1884 is left to C5e2 with steam power, banks and Irish patents.
- Tests 292 OK (3 new).

## 2026-10-25 — C6: innovations and firsts
- `data/curated/trade/innovations.json`: 36 inventions, discoveries and firsts (1701 Tull's seed drill to 1996 Dolly),
  placed where made, tried or first used, each with Wikipedia quotes fetched and checked (45 of 45 found by
  `bidb.evidence --check --new`); 5 marked open. New list `innovations` in bidb.oldest_lists, new place group
  "Innovations & firsts" (place_kinds, render_places.js, static_places.js, `--g23` in style.css); `made_at` titles
  resolved to Wikidata ids and linked to the building or place (`link_made_at`, 15 of 36), shown in place details
  as "Made or first used at". Places written to the DB by `python -m bidb.oldest_lists` (36 new).
- Tests 294 OK (2 new); ui_check `innovations` (new), `oldest_civic` pass. Hosted copy and release not updated.

## 2026-10-25 — C7: laws and institutions as cited events
- 25 events appended to `data/curated/change/events.json` (`topic: law`, `trade` tag for C8), each with an exact
  quote from its Wikipedia article, every quote checked against the article text when written. The slave trade and
  abolition treated plainly: Liverpool's first slave ship (1699), Bristol's trade 1700-1807 (an estimated 500,000
  people carried), the 1807 and 1833 Acts and the £20 million paid to owners.
- Tests 296 OK (2 new); ui_check `law_events` (new) passes.

## 2026-10-25 — C8: trade stories
- `data/curated/trade/stories.json` (10 trades) and `bidb/trade_stories.py` (check, events with innovations, places
  by kind or whole-word name match restricted to trade-related groups, buildings without prehistoric/Roman/forts,
  people via person_links, export); `app/trades_api.py` (`/api/trades`, `/api/trade/<id>`), page `/trades`
  (`templates/trades.html`, `static/trades.js`, styles in pages.css), nav link, hosted copy (`trades.json` from
  static_tours, routes in static_api.js, page in static_export PAGES).
- Every note quote (30) checked against its Wikipedia article text; intro facts trimmed to what the notes, events,
  innovations and graphs support. First version matched words with LIKE and caught "Drummond" for "rum" and long
  barrows in "Plantation" woods: now regex whole words and trade-related place groups only.
- Tests 300 OK (4 new); ui_check `trades` (new) passes; screenshot of the sugar and slavery story checked.

## 2026-10-25 — C9: trade stories through the GUI
- Change over time: line of links to the ten stories; each law event and each graph used by a story links to it.
- Detail views: "Trade and industry here" (`static/trade_here.js`, `/api/trade_here/<id>`, `trade_stories.here`:
  stories a record belongs to, innovations made there; a building where a story's invention was made joins the
  story, e.g. Cromford Mill → cotton).
- Map page: "Trade" select and `?trade=<id>` ring a story's places and buildings (kept in the address as the map
  moves); the Trades page links to it. Quiz: "Which came first?" from the 36 innovations and 25 trade laws.
  Export menu on the Trades page: places and buildings (CSV, JSON, GeoJSON, KML), timeline (CSV, JSON).
- Help: section "Trades and industries" with two new figures (`node docs/make_figures.mjs trades trade_here`).
- Hosted copy: `trades.json` written by static_tours (checked into a scratch folder: 0.57 MB); static routes for
  trades, trade and trade_here. Hosted copy and release not republished.
- ui_check: new `trades_change`, `trade_here`, `trade_map`, `quiz_first` pass.
- Full checks: unit tests OK (302), JS checks pass, ui_check 71/72: `settings_share` fails because this computer's
  settings.json has `share_on_network: true` (the check expects sharing off; it fails the same without these changes).

## 2026-10-25 — BT1a, BT1b: building types, the thesaurus and the first families
- BT1 split into BT1a (licences, thesaurus), BT1b (first families with sourced links), BT1c (the other families,
  periods, earliest examples).
- Licence check (`data/curated/building_types/README.md`): FISH Thesaurus of Monument Types v29 OGL v3.0 (stated in
  its RDF at heritagedata.org), Getty AAT ODC-By 1.0; Historic England's publications not stated as OGL, and
  historicengland.org.uk answers scripts with 403. FISH, Building Materials and Components zips cached in
  `<cache>/fish/` (FANTOM). DATA_LICENSE.md row added.
- New `bidb/fish_types.py`: concepts, non-preferred terms, polyhierarchy (848 terms under more than one broader term),
  related terms, lookup; `--report`: catalogue class uses with a FISH concept by label alone 18,638 of 27,400 (68.0%).
- New `bidb/building_types.py` and `data/curated/building_types/lineage.json`: 33 types, 29 links (houses and
  defence), 76 quotes, all found in their sources (`--quotes` → `data/building_types_check.json`).
  `evidence.check` takes `claims` and `path` so both files share one checker.
- Tests 311 OK (9 new: `test_fish_types`, `test_building_types`). No GUI change yet (BT4).

## 2026-10-25 — BT1c1: religious and farm building types
- BT1c split into BT1c1 (religious, agricultural), BT1c2 (commercial, industrial, transport), BT1c3 (civic and the
  rest, periods of use for every type); the earliest catalogue example per type moves to BT2.
- New `data/curated/building_types/lineage_religious.json` (20 types, 17 links) and `lineage_agricultural.json`
  (12 types, 11 links); `building_types.load` merges every `lineage*.json` (links cross files: longhouse → laithe
  house, tower keep → dovecote). Now 65 types, 57 links (documented 43, probable 9, disputed 5).
- `python -m bidb.building_types --quotes`: 170 of 170 quotes found (FISH scope notes and Wikipedia).
  Disputed: the minster hypothesis; Roman or Norman dovecotes.
- Tests 312 OK (1 new: merged files). No GUI change (BT4).

## 2026-10-25 — BT1c2: commercial, industrial and transport building types
- New `data/curated/building_types/lineage_commercial.json` (24 types, 18 links: inns and pubs, markets and
  exchanges, shops and banks), `lineage_industrial.json` (22 types, 16 links: watermills, windmills, textile mills,
  iron making, kilns), `lineage_transport.json` (17 types, 12 links: bridges, turnpikes, waterways, railways).
  Now 128 types, 103 links (documented 81, probable 15, disputed 7).
- `python -m bidb.building_types --quotes`: 305 of 305 quotes found (Wikipedia and FISH scope notes). Wikipedia
  locators checked by script against the section each quote stands in (46 first guesses corrected to the real
  subsection).
- Disputed: the vertical windmill from the Persian horizontal one; the shopping arcade from Paris or as early in
  Britain. Seven links probable, each saying what the sources do and do not show.
- Tests 313 OK (1 new: every planned domain present). No GUI change (BT4).

## 2026-10-25 — BT1c3a: civic, education, health and recreational building types; Glossary page; hosted copy v71
- BT1c3 split into BT1c3a (the four domains' types and links, done) and BT1c3b (periods of use, structure and plan
  form for every type). Four research agents wrote one file each (`lineage_civic.json` 23 types / 19 links,
  `lineage_education.json` 23 / 18, `lineage_health.json` 25 / 23, `lineage_recreation.json` 25 / 20); each file
  reviewed here: chained library → public library made influence ("forerunner"), grandstand → football ground made
  influence. `python -m bidb.building_types --quotes`: 224 types, 183 links, 593 of 593 quotes found.
- Glossary page `/glossary` (George's request): new `bidb/glossary.py` and `data/curated/glossary.json` (88 curated
  terms: designations, dating and date checks, architecture, archaeology, registers, app terms; 27 of them FISH scope
  notes, OGL, the indexing advice stripped) + the 13 periods + 181 building types with a definition = 282 terms;
  `/api/glossary`, `static/glossary.js` (search, group chips, A-Z, see-also links, Find in the catalogue), nav link,
  Help links to it, hosted `data/glossary.json`. Tests: `test_glossary` (4), ui_check `glossary`, `glossary_see`.
- Hosted copy versions 70-71: 9 new and 194 changed files (96 MB in two batches; the C6-C9 trade work had not been
  published), 458 files, 254.0 MiB; sizes checked against `dist/`; static GUI review 24/24 pages (glossary, trades
  added to `tests/ui_review.mjs`). The database has changed since db-2026-10-24 (C6 innovation places, C3c people); no
  new release made.
- Tests 317 OK. GUI restarted (shares on the home network: settings.json has `share_on_network: true`).
- Next: BT1c3b (periods of use for every type).

## 2026-10-26 — BT1c3b: periods of use, structure and plan form for every building type
- Schema and check first (`bidb/building_types.py`): `period` {text, from, flourish?, to | ongoing}, `structure`,
  `plan`; sources carry `about` (period / structure / plan); `period_problems` (years in order, to or ongoing, a
  source for each); `--file lineage_x.json [--quotes PATH]` for one file (`summary` names other files' types by id).
- Six research agents in parallel (houses and defence; religious and farm; commercial; industrial and transport;
  civic and health; education and recreation), each file checked by its agent and reviewed here: no type, link or
  quote lost, 850 quotes added. All 224 types: flourish 68, to 170, ongoing 54, structure 66, plan 100.
  `python -m bidb.building_types --quotes`: 1,443 of 1,443 quotes found.
- Changed in review: canal from the Foss Dyke (c. AD 120, "no consensus", Wikipedia) rather than Exeter 1564;
  grammar school ongoing (the 2017 Sevenoaks annexe is the first new one in decades). The agents moved several
  earlier years (artillery castle 1481-1561 from FISH, martello tower to 1857 at Pembroke Dock, tide mill from
  Killoteran in the 6th century, cotton mill 1741, gin gang to 1868, bear garden to 1614...); each move is quoted.
  Weak years and disagreements listed in `data/curated/building_types/README.md`.
- Tests 318 OK (1 new: `test_periods`; the curated-file test now includes the period check). No GUI change (BT4).
- Next: BT2 (map catalogue records and place kinds to the types).

## 2026-10-26 — BT2a: catalogue records and places mapped to the building types
- BT2 split into BT2a (mapping, done) and BT2b (per-type counts, map, dated examples, earliest surviving example,
  API); emergent BT1d (types the mapping showed missing: town houses, chapels, gatehouses, lighthouses, general
  parents, and a decision on prehistoric monuments).
- New `bidb/type_map.py` (build stage "Building types", after "Nations for places") and
  `data/curated/building_types/aliases.json` → table `type_map` (entity, source, type, via, label, primary).
  Classes by type name, alias, FISH concept, nearest broader FISH concept that is a type's; most specific kept.
- Found in review and fixed: 21 types carry a FISH concept wider than the type (THEATRE → Georgian playhouse,
  HOSPITAL → medieval hospital), now matched through FISH only within their period (`within_period`); name rules
  matched parts of buildings ("Gate Piers, Baldoon Castle") → head of the name only; an Iron Age "Clinch Castle"
  → name, category and kind matches need a year within a century of the type's period; objects kept in a building
  inherited its type (Henry IV's tomb a cathedral) → no inheritance, non-building place kinds skipped; canal
  aqueducts are not railway viaducts; Irish-type round towers and tolbooths not limited to one nation.
- Result: 10,805 of 22,508 records (48.0%) and 27,401 places typed, to 123 of 203 isles types; 438 leftover labels
  reviewed (too general, or no such type yet). 80 types have no example yet (BT2b).
- Tests 325 OK (7 new: `test_type_map`). No GUI change (BT4).
- Next: BT2b.

## 2026-10-26 — BT2b: per-type counts, examples and earliest surviving examples; 51 more types with examples
- New `bidb/type_stats.py` (summary, detail, earliest, too-early check, types of one record) and `app/types_api.py`
  (`/api/types`, `/api/type/<id>`, `/api/types_of/<id>`; ~0.1 s each). No build stage: it reads `type_map`.
- The 80 types with no example: `bidb/type_map.py` gained text rules (`texts` in aliases.json: name, short
  description, first two sentences of the extract; categories / place kinds, `refines`, `slack`) and splits register
  labels at ";" and ":". First drafts matched far too widely (1,894 matches: railway stations for "spa", locks for
  "Navigation", brickworks, holy wells with corbelled roofs); limited and reviewed match by match → 75 rules, 68
  records and 703 places. 174 of 203 isles types now have examples (was 123); 29 still none (README lists them).
- BT2a bugs fixed: nation limits said "Ireland" (database: "Republic of Ireland"), now checked by `problems`; the
  "...Station" name rule typed 24 lifeboat, power and radar stations as railway stations.
- Earliest surviving example for 152 types; prefers the type's primary records (Hertford Castle, used as a town
  hall, gave way to Totnes Guildhall 1206). 521 examples "too early", reviewed by type: later use (pubs, hotels,
  cinemas, country houses), first phase of the site, coarse register periods, wrong Wikidata classes; none kept.
- Emergent: Irish SMR tower houses in "Rath..."/"...cashel" townlands dated 600.
- Tests 330 OK (5 new: `test_type_stats` 3, text rules and label parts in `test_type_map`). No GUI page yet (BT4);
  the hosted copy does not answer `/api/types` yet (BT7).
- Next: BT1d (more types for what could not be typed) or BT3.

## 2026-10-26 — Irish SMR dates; BT1d: prehistoric and Roman, houses, estate, settlement and general types
- Irish SMR places in townlands named Rath... or ...cashel were dated 600: `places_build.estimate_dates` read the type
  estimate from the whole name ("Church, Rath"); SMR places now use the class only, friars' houses get the friary
  range. Applied to the database (78 re-estimated, 30 undated); too-early type examples 521 → 504. `test_typology`.
- BT1d: George chose to put built prehistoric and Roman structures in the tree (standing stones, rock art, carved
  stones left out). Five research agents in parallel, one new lineage file each (prehistoric and Roman 24 types,
  houses 17, estate 19, settlement 19, general 8): 87 types, 126 links, 680 quotes, all found. Reviewed here: the
  duplicate Roman town wall link and Roman villa settled between agents; municipal museum → public library made
  influence, not convergence. One agent reported that its first 10 Wikipedia API calls sent George's email in the
  User-Agent header (its own requests, not the project's code, whose user agent has no email).
- `bidb/type_map.py`: a FISH concept may map to several types (general hospital and theatre share theirs with the
  medieval hospital and Georgian playhouse; the period-limited type wins when the year fits); general types give way
  to their forms (variant links); text and name rules refine general types and uses; `secondary` uses (museum,
  school, hospital, theatre, prison) rank after the building's own type. First run made 357 primary-type changes,
  among them regressions (grammar school → school 90, Balmoral → museum); after the fixes 192 changes, reviewed.
- aliases.json: 19 class aliases, `roman-villa` in `within_period`, `secondary`, 12 text rules reviewed match by
  match (gatehouse and rock-lighthouse rules on the name only; `[^\w|]` so patterns do not cross into the
  description); `not_in_tree` 438 → 341.
- Result: 15,713 of 22,508 records (69.8%, was 48.0%), 58,753 places (was 28,528); 247 of 285 isles types with
  examples, 220 with an earliest surviving example; too early 813, reviewed (earlier phases of sites, coarse
  register periods), none kept.
- Tests 335 OK (5 new: `test_typology` 2, `TestGeneralTypes` 3). No GUI change (BT4); hosted copy not updated.
- Next: BT3 (materials and techniques) or BT4 (the /types page).

## 2026-10-26 — BT3a: materials and techniques of building, sourced
- BT3 split (only 500 of 22,508 records have a Wikidata material): BT3a the curated file (done), BT3b records and
  places linked to materials (P186, article text, register descriptions), BT3c materials on detail views and type pages.
- `bidb/fish_types.py`: `concepts(scheme)` also reads the FISH Building Materials (232 terms, `eh_tbm`) and
  Components (1,403, `eh_com`) thesauri of the cached v29 release; both OGL v3.0 (checked on heritagedata.org).
- New `bidb/building_materials.py` (checker: groups, kinds, FISH ids per scheme, periods via the new
  `building_types.period_errors`, regions/technology/geology/examples each backed by a source `about` it, building
  type ids, links with the lineage rules, `earlier` flag; `--quotes`). `tests/test_building_materials.py` (7).
- Five research agents in parallel, one file each (stone and mortar, earth and timber, brick and tile, roofs,
  glass/iron/steel/concrete): 99 entries, 51 links, 978 quotes, all found (`data/building_materials_check.json`).
- Reviewed here: Wikidata ids of the 151 examples against the catalogue (Coggeshall chapel id corrected); two links
  defined in two files merged; lead → Lake District slate dropped (one building); `earlier: true` added for six
  first dates that are only the earliest named (queen-post roof 1753 the worst: no source dates a medieval one).
- Tests 342 OK. No GUI change (BT3c/BT4); hosted copy not updated.
- Next: BT3b (records linked to materials).

## 2026-10-26 — BT3b: records and places linked to materials and techniques
- New `bidb/material_text.py` (term rules on sentences: cue words near ambiguous terms, `ignore` and `near` windows,
  register sentences about boundary walls and gardens skipped, Wikipedia sections skipped by heading),
  `bidb/material_map.py` (build stage "Materials" after the stories: Wikidata P186 via QLever, cached HES/Cadw/NIAH
  descriptions, cached Wikipedia articles → table `material_map` with the evidence sentence; `--report`) and
  `bidb/material_stats.py` (per material: counts, by nation and century, too-early flags, earliest example).
  Curated `data/curated/building_types/material_aliases.json`: 59 Wikidata material items, 41 left out, 95 term rules.
- Only 5,357 isles items have P186 (mostly statues); most links come from the HES descriptions and Wikipedia.
  Reviewed five samples per material and source (829 lines) and fixed the false matches (rubble as debris, dock
  jetties, fence post-holes, museum crucks, interior fittings, plate glass universities, towns and parks); 30 random
  Wikipedia links after: about 28 right. The run went from 4.3 to 2.5 minutes with a single prefilter pattern.
- Result: 8,477 of 22,508 records (37.7%) and 2,352 places, 24,957 links to 92 of 99 materials; 901 links flagged
  too early (later phases), 90 materials with an earliest example (begun in or after the material's first date).
- Emergent: catalogue dates mined from quantities (Waterloo Bridge 748, Liverpool Street 600, Battersea Power
  Station 400, an NIAH "c. 188"); generic stones (sandstone, limestone, granite...) have no BT3a entry.
- Tests 351 OK (9 new: `test_material_map`). No GUI or API change (BT3c/BT4); hosted copy not updated.
- Next: BT3c (materials on detail views and type pages, with BT4) or the catalogue date check.

## 2026-10-26 — Catalogue dates mined from quantities (emergent from BT3b)
- New `bidb/date_recheck.py`: the text-mined (and type-estimated, and undated) records of the existing database dated
  again by the build's own `date_fill` step from the download cache; changes to `runs/date_recheck.json`, `--apply`
  writes them (a rebuild would drop the photo, plan and outline jobs' work). Database backed up first.
- Rechecking the 2,368 "Wikipedia article" dates with today's code found more than the quantities: "mid-15th century"
  had stopped matching altogether (the hyphen look-behind sat after the qualifier), "c1460" and "AD 75" were never
  read, and HES's scanned "l8th century" and the register normaliser's own "of C14" → "of14th" gave years like 701.
- `date_mining`: bare numbers under 1000 need "c.", an era or an introducing word; more units, thousands separators,
  ordinals, ages, grid references; life dates "(d. 655)" skipped, no sentence break after "d."/"b."/"c."/"fl.";
  "510±70 BC"; "the 550s"; double qualifiers ("Early-mid", "mid to late") keep the first; "Grade I listed" no longer
  trips the skip word "listed" (but "made a Grade II Listed Building on 17 May 1994" still does). Tried and
  reverted: pottery/sherd as skip words (pottery is how most forts are dated).
- Result: 156 dates changed over two passes, all reviewed line by line; 25 the miner still gets wrong (the
  article's earliest date belongs to a neighbouring building, a find or a later event) added to
  `data/curated/date_corrections.json` with quotes, all found in the cached articles (Waterloo Bridge 1937, Liverpool
  Street 1874, Battersea 1929, Brands Hatch 1926, Commando Memorial 1952, Hammerwood Park 1792...); St Seachnall's
  Church left undated (`year_start: null`, newly allowed). NIAH typo records niah-20000033 and niah-21903502
  removed and kept out of the build. Timeline table rebuilt (45,805 events).
- Emergent: seven new date-check conflicts between Wikidata dates and introductions the check can now read
  (Sheffield Cathedral, Woodchester Roman Villa, Ormesby Hall...), for the date review.
- Tests 356 OK (5 new in `test_date_mining`). No GUI change; hosted copy and bundled release not updated.
- Next: BT3c with BT4 (the /types page).

## 2026-10-26 — BT4a: the page /types (family tree, type and material pages), BT3c1
- BT4 split into BT4a (the local page, done) and BT4b (the hosted copy, with BT7); BT3c into BT3c1 (materials on the
  detail views, type pages and material pages, done here) and BT3c2 (a material's region over the geology layer).
- New `bidb/type_pages.py` (tree, type page, materials, material page, types here) and five endpoints in
  `app/types_api.py` (`/api/type_tree` kept until the database file changes: 2 s of counting, then 2 ms).
- New page `/types` (nav "Building types"): `types_tree.js` draws every type as a row on the Map slider's non-linear
  time axis, the period of use as a bar (thick while flourishing), the earliest surviving example as a dot, the links
  as branches at the later type's first date (colour by kind; dashed disputed, faint probable; links between domains
  only on hover, else long lines crossed the whole chart); families fold, domain chips, search, link kinds as
  checkboxes. `types_view.js`: per type and per material, the FISH definition, period, structure, plan, materials,
  family links with claims/views/quoted sources, earliest surviving example, begun per century, by nation, map,
  dated examples (materials: with the evidence sentence), sources. `types_here.js`: detail views of records and
  places say "This is a Wealden house (Hall houses): see its family" and list the materials found.
- Fixed: `glossary.ADVICE` cut 52 FISH scope notes at "house with" ("Use with" matched case-insensitively mid-word);
  the Glossary page had the same truncations.
- Checked in headless Chrome: tree (light, dark), Wealden house, brick at 390 px, The Wealden Hall's detail view.
  Nav link hidden in the hosted copy until BT4b.
- Emergent: register-period dates ("Prehistoric domestic and defensive") count as real dates for the earliest
  surviving example (Roundhouse: a HES place dated -2000).
- Tests 362 OK (6 new `test_type_pages`, 1 in `test_glossary`); ui_check types, type_page, material_page,
  types_here OK. Hosted copy not updated.
- Next: BT5 (charts: types in use through time, materials by century) or BT4b with BT7.

## 2026-10-26 — BT5: charts of building types and materials through time
- New `bidb/type_charts.py` (`spread`, `chains`, `centuries`), `app/static/types_time.js` (`TypeTime`), endpoint
  `/api/material_centuries`; `type_pages.type_page` now carries `chains` and `spread`.
- /types has a third tab "Through time" (`?tab=time&year=`): types in use per domain at each date (one area per
  domain on the Map slider's non-linear axis, counted in the browser from the tree's periods; hover gives every
  domain's count; a year lists the types in use then, 79 in 1300, 98 in 1500) with "Show the map at this year" →
  `/map?year=`, which now switches the Map page's slider on at that year (`TimeSlider.setYear`); and materials by
  century begun (heatmap of 91 materials, each row against its own busiest century, the first known date ticked).
- Type pages: "What came before and what came next" (descent, replacement and revival lines; forms such as the
  Wealden house show their general type's lines; 207 of 311 types have some) and "Spread across the isles"
  (counties with a dated example by each date, first example per county: motte and bailey 63 counties).
- Seen: century-only dates pile up at 1001, 1101… in the spread chart (noted under it); Clackmannan Tower is year
  1301 with date text "Late 14th century" (catalogue date to check with the date review).
- Checked in headless Chrome: the tab (light), motte and bailey's page, /map?year=1300, the tab at 390 px dark
  (labels moved above the rows on narrow screens).
- Tests 370 OK (4 new `test_type_charts`); ui_check types_time, type_chains and the other /types pages OK.
  Hosted copy not updated (BT4b).
- Next: BT4b with BT7 (hosted copy of /types, Help, figures, quiz questions), or the register-period dates as
  earliest examples.

## 2026-10-26 — Register-period dates no longer earliest examples; railway lines typed
- `type_stats.estimated` counts "(register period)" dates (HES, Cadw and NI register places dated only by a
  representative year of their period, e.g. "Prehistoric" = -2000) as estimates, so they are never a type's earliest
  surviving example (also in the spread chart and for materials, which use the same test); `too_early` no longer
  flags them (108 of 808 flags were these: 70 duns, 13 brochs).
- Seven types changed: round-house, longhouse, fulling-mill, pottery-kiln, cursus now have none (215 types with an
  earliest example, was 220); lock-up → Former Lockup 1823; railway → see below. No material changed.
- Reviewing railway: lines (`in_rail`, `ino_rail`) were untyped. Two text rules in `aliases.json` on the name
  ("… Railway / Line / Rail Road", names with Signal or Box left out), `slack: 0`: 198 lines railways from 1825, 9
  wagonways before (Wollaton 1604, Tanfield 1725, Middleton 1758, Surrey Iron 1803, Swansea and Mumbles 1807…).
  The earliest railway is now the Waterloo & City line, which was dated 1864 from a sentence about another line:
  reviewed correction to 1894 (work began 18 June 1894; opened 1898), 207 corrections.
- The type-map rerun also moved three records after earlier date corrections (Richborough, AD 85: Roman fort, no
  longer Saxon Shore fort; Abbey Gateway, Banff Old Town Hall).
- Emergent: catalogue records rank before places for the earliest example, so the Stockton and Darlington Railway
  (1825, place) loses to the 1894 line; tramways, funiculars, inclines and signal boxes have no type.
- Tests 367 OK (1 new in `test_type_stats`; HEAD had 366, the 370 of the last entry was a miscount); ui_check of the
  six /types pages OK. The running GUI needs a restart for the new code. Hosted copy not updated.
- Next: BT4b with BT7 (hosted copy of /types, Help, figures, quiz questions).

## 2026-10-26 — BT4b: /types in the hosted copy
- New `app/static_types.py` and `app/static/static_types.js` (hooked into `static_api.js` as `STATIC_TYPES`): the
  family tree, "Through time", all 311 type pages and 99 material pages, and the types and materials of each detail
  view now work in the hosted copy; the "Building types" nav link is shown there.
- Compact format, 21 files, 5.8 MB (the full local data would be ~28 MB): catalogue records by id, filled in from the
  rows the browser already holds; places as [id, name, year, date, county, nation]; place map points as integer steps
  of 1/1000° (dots link to the Map page there); family links once; 40/25 examples per type/material (the list says
  "40 of 822 shown"; `material_stats.detail` now gives `dated` so local material pages say so too); the detail views
  give materials and how they were found but not the evidence sentence.
- Room, with nothing lost: tour route lines Douglas-Peucker at ~4 m (`static_tours.ROUTE_TOL`, 3.2 → 2.1 MB);
  common link starts of places as `~<n>:` (`static_places.URL_PREFIXES`, expanded in `static_places.js` from meta);
  4,293 register texts that only say "no description yet" left out (`NO_DESCRIPTION`). Without these the copy was
  257.6 MiB.
- Checked against `dist/` served locally in headless Chrome: tree, type page (Wealden house), "Through time" 1300,
  motte and bailey (map with records and places, spread, lines), brick, a building's and an Irish SMR place's detail
  views (link expanded correctly). Local ui_check of the four /types pages OK.
- Hosted copy republished as versions 72-74 (three batches, 130 changed files, 151 MB: the catalogue data changed too
  since version 71): 253.0 MiB, 487 files.
- Tests 372 OK (5 new `test_static_types`; `test_static_split` follows the hash's move to `STATIC_ID_HASH`).
- Next: BT7 (Help page section and figures for /types, quiz questions "which type came first?", "name the type").

## 2026-10-26 — BT7: building types in the quiz and the Help page
- Two new quizzes (13 in all): "Which type came first?" (two isles types by first known date from the family tree,
  400 years apart, 60 on Hard, Hard mostly within one domain) and "Name the type" (a photographed catalogue record
  by its main type, up to 4 records for each of 187 types; wrong answers from other domains, on Hard the same domain
  but another family, as the forms of one family, e.g. castle and concentric castle, can all be right). The pool gets
  `types` (`quiz_api.types`: 285 kinds, 604 photos, 176 KB in data/quiz.json); new `tests/test_quiz_types.py`.
- Help: new section "Building types" (family tree, type and material pages, Through time) with three new figures
  (`types_tree`, `type_page`, `types_time`, in `docs/make_figures.mjs`); the quiz paragraph lists all thirteen (it had
  left out "Which came first?"); quiz_menu figure regenerated.
- ui_check: quiz_typefirst, quiz_nametype, help_types added and passing (against a fresh server on port 5072; the
  GUI on 5050 runs older code until restarted).
- Hosted copy version 75 (9 changed files: quiz data and scripts, Help page and four figures): 490 files. Checked
  `dist/` served locally in headless Chrome: both new quizzes draw questions, no errors.
- Tests 374 OK. Next: BT6 (generated examples) or BT3c2 (material regions over the geology layer), or the open
  emergent items (generic stones, tramways and funiculars).

## 2026-10-26 — Qualified centuries in list dates (Clackmannan Tower)
- Emergent item from BT5: Clackmannan Tower had year 1301 with the date text "Late 14th century".
  `dates.parse_text_year` (Wikipedia list dates, hoards, research claims) ignored qualifiers. It now reads them as
  the text miner does: `dates.century_start` moved from `date_mining` and shared (mid +33, late or second half +50,
  late BC +66; the first qualifier counts, "early to mid-18th century" → 1701).
- `bidb.date_recheck` gains `listed` (records dated from a Wikipedia list whose date text has a qualified century;
  a list date no longer earlier than Wikidata's gives way to it, as records.build_record does) and `hoards`.
  Applied: Clackmannan Tower and Crichton Castle 1351, Lauriston Castle 1251, Oxford Castle 1034, Glasgow Cathedral
  1134, Culross Abbey 1217 (Wikidata; the list's "Late 13th century" is 1251); 43 hoards (Trewhiddle 851...).
  Sketrick Castle kept (in date_confirmations.json). Date checks recomputed: still 7 conflicts.
- Tests 376 OK (2 new in `test_date_mining`). Hosted copy not updated (6 records, 43 places).
- Next: the open emergent items (seven date-check conflicts, earliest railway ranking, tramways, generic stones),
  BT3c2 (material regions over the geology layer) or BT6.

## 2026-10-26 — Earliest examples: structure places rank with records
- Emergent item from the register-period fix: the earliest railway was the Waterloo & City line (1894) because
  `type_stats.earliest` took catalogue records before places. Now, for a type with more places than records, places
  of the structure groups (Military heritage, Infrastructure & utilities, Bridges, Maritime heritage, Underground)
  dated to the year ("1805", "opened 27 September 1825") rank with the records (`structure_place`).
- Simulated over all types first: eight would change if every place group counted, but hospitals, fire stations,
  theatres and works carry the founding date of the organisation (Manchester Royal Infirmary 1752, Carron Company
  1759, Chiltern Firehouse 1889), so only the structure groups count. Three changed: railway → Stockton and
  Darlington Railway 1825, Martello tower → Dymchurch 1805, polygonal fort → Fort Brockhurst 1858.
- Type pages say when the earliest example is a place ("whether it still stands is not recorded").
- Tests 377 OK (1 new in `test_type_stats`); ui_check of the four /types pages OK (server on port 5073). The running
  GUI needs a restart. Hosted copy not updated (3 earliest examples).
- Next: tramways and funiculars, generic stones (BT3a research), BT3c2 or BT6.

## 2026-10-26 — Tramways, funiculars, inclines and signal boxes as building types
- Emergent item from BT2b: ~430 railway places (370 signal boxes, cliff railways, tramways, inclines) had no type.
  Six new types in `lineage_transport.json`, each with a sourced period and structure (47 quotes from Wikipedia and
  the FISH scope notes, all found by the quote check; merged into `data/building_types_check.json`, 2,179 of 2,179):
  plateway 1787-1830, street tramway 1860- (Birkenhead; Glasgow last city system 1962; Metrolink 1992), funicular or
  cliff railway 1875- (one type), railway inclined plane 1796-1974, canal inclined plane 1777-1900, signal box 1843-.
  Seven sourced links (wagonway → plateway → railway; railway → funicular as a form; pound lock → canal incline...).
  317 types, 316 links.
- `aliases.json`: seven text rules ahead of the generic railway rule, Cadw's "Tramroad"/"Incline" labels, a
  staircase-lock rule that overrides Wikidata's wrong "canal inclined plane" class on Bingley Five Rise Locks; the
  wagonway name rule no longer takes tramroads (Surrey Iron Railway and the Mumbles line are now plateways).
  Dry run against the table before writing it: stations and tram stops whose articles mention trams, tramroad bridges,
  the Severn Tunnel, the Lickey Incline (locomotive-worked) and a target railway were caught and left out.
- Result: 434 places typed or retyped; records 15,717, places 59,375; 253 of 291 isles types with examples, 219 with
  an earliest surviving example (funicular: Scarborough Spa lift, begun 1873; signal box: High Street, Lincoln 1874;
  plateway: Surrey Iron Railway 1803; street tramway: Douglas Bay Horse Tramway 1876).
- Tests 379 OK (2 new in `test_type_map`, on the curated rules); ui_check of the six /types pages OK on a fresh
  server (port 5074); funicular type page checked by screenshot. The running GUI needs a restart. Hosted copy not
  updated (the /types data and quiz pool will pick the new types up at the next export).
- Next: tramroad bridges (new emergent item), generic stones (BT3a research), BT3c2 or BT6.

## 2026-10-26 — Bridge places typed; canal aqueducts, swing, bascule and transporter bridges
- Emergent item "tramroad bridges untyped" was wider: 980 bridge places had no building type (597 railway bridges,
  all 169 aqueducts and 91 swing or bascule bridges, 121 early crossings) because the kind labels of bidb.bridges
  ("Railway viaduct or bridge") match no class. `aliases.json` `place_kinds`: br_rail, br_early, br_moving and
  br_aqueduct default to the general bridge type (name and text rules still refine them).
- Four new forms of bridge in `lineage_transport.json`, each with a sourced period and structure (35 quotes,
  2,216 of 2,216 found by the quote check): canal aqueduct 1761- (Barton Aqueduct; Kelvin 1790; cast-iron troughs
  1796; Falkirk Wheel aqueduct 2002; no FISH concept: AQUEDUCT also covers water channels), swing bridge 1786-
  (Oxford Canal's Banbury-Oxford length; Seán O'Casey 2005, Scale Lane 2013), bascule or lifting bridge 1786-
  (canal lift bridges and drawbridges; Tower Bridge 1886-94; Gull Wing Bridge 2024), transporter bridge 1905-1917
  (Widnes-Runcorn to Warrington). Four variant links from bridge. 321 types, 320 links.
- Text rules for the four (canal aqueducts need a canal or navigation word; transporter-bridge power houses and
  Glen Etive's box transporters left out) and a name rule for canal aqueducts named only "X Aqueduct"; reviewed
  exclusions: pipe bridges, the Loch Katrine water aqueducts (Tom and Eas, Loch Chon), Flash Road (New River), the
  River Wey aqueducts, Sawley (a pipe bridge). Class aliases: navigable aqueduct, drawbridge.
- `type_map.CLOSED`: kind labels ending "(gone or closed)" (bridges, institutions, sports, trade_works stages) are
  read without it: 95 closed schools and 21 bridges typed.
- Dry run before writing: 1,224 primary types changed (856 to bridge, 117 canal aqueducts, 100 swing, 46 bascule,
  5 transporter, 95 schools; Tower Bridge now bascule first). Records typed 15,729 (69.9%), places 60,506; 257 of
  295 isles types with examples, 223 with an earliest surviving example (Luggie Aqueduct 1775, Leith Swing Bridge,
  Turnbridge Lift Bridge 1865, Newport Transporter Bridge).
- Tests 380 OK (new `TestBridgeRules`); ui_check of the /types pages + new `type_bridge` 7/7 on a fresh server
  (port 5075); canal aqueduct page checked by screenshot. The running GUI needs a restart. Hosted copy not updated.
- Next: generic stones (BT3a research), BT3c2 (material regions over the geology layer) or BT6.

## 2026-10-26 — Generic stones for BT3 (sandstone, limestone, granite, marble...)
- Emergent item from BT3b: the common stones had no materials entry, so 153 sandstone, 151 granite, 87 limestone and
  29 marble P186 items and thousands of register sentences ("Sandstone rubble with ashlar dressings") were left out.
- New `data/curated/building_types/materials_stones.json`: 15 entries, each with a FISH concept where one exists, a
  sourced period, regions, technology and geology (127 quotes from Wikipedia and the FISH scope notes, all found;
  merged into `data/building_materials_check.json`, 1,105 of 1,105): sandstone -3980 (Coldrum's sarsens, radiocarbon
  3980-3800 BC), limestone -3650 (West Kennet), granite -3500 (Brownshill dolmen), marble 75 (Fishbourne), chalk and
  clunch 1110 (Hyde Abbey), whinstone 1101 (St Giles'), Coade stone 1769-1840, Magnesian Limestone 1220 (York
  Minster), sarsen, York stone, Reigate stone 1001-1960, Ketton 1501, Ancaster 1096, Heavitree 1350-1899 (its article
  contradicts itself on Triassic vs Permian, so no bedrock period), Hopton Wood 1687-2006. The one end date with no
  source (sarsen 1900) was taken out before writing. 23 links: limestone, sandstone, granite and marble → the 19
  named stones (Purbeck and Kilkenny marble from both limestone and marble); Coade stone → precast concrete.
- `material_map.general_of`: materials marked `general: true` give way to their named variants (a Bath stone church
  is not also limestone). The first version used every variant link and the dry run showed rubble falling from
  3,148 to 1,344 links (rubble → ashlar is a variant); limited to `general` materials, rubble, slate and flint stay
  as they were. `building_materials` validates the field.
- `material_aliases.json`: 17 P186 items moved from `not_in_list` (Cornish granite → granite, Carrara → marble); 15
  text rules, reviewed on two dry runs (marble only for columns, shafts, facings and walls, never fittings, fonts,
  monuments or murals; limestone not for landscapes, kilns and caves; York stone not for paving; chalk not for hill
  figures; sarsen not "chose not to use"); `skip_sentence` also skips "FORMER WALLED GARDEN" and the like.
- Result: sandstone 1,874 links, limestone 570, granite 505, marble 145, whinstone 96, chalk 56, Magnesian 38,
  sarsen 35, Heavitree 27; records linked 8,475 → 8,879, places 2,352 → 2,621. Earliest examples: West Kennet
  (limestone, sarsen), Brownshill dolmen (granite), Traquair House (whinstone), Assembly Rooms (Coade stone).
- Tests 383 OK (new `test_specific_stone_kept`, `TestGenericStones`); ui_check of the /types pages + new
  `material_stone` 8/8 (port 5076); limestone page checked by screenshot. The running GUI needs a restart. Hosted
  copy not updated.
- Left open (roadmap): marble's earliest is a Chester amphitheatre mural sentence; Hopton Wood has no examples;
  greensand, ironstone, lias, Bargate, Pennant and Collyweston have no entry.
- Next: BT3c2 (material regions over the geology layer), the stones left open, or BT6.

## 2026-10-26 — BT3c2: a material's bedrock on its page's map
- The material pages of /types now shade the rock a material comes from under its dots and count how many of its
  examples stand on it (new `app/static/types_geology.js`, `TypeGeology`).
- First version drew the curated bedrock periods from the "Change over time" layer; it showed the period layer cannot
  serve igneous stones (it dates granite by when it cooled: Dartmoor "Carboniferous", Aberdeen "Ordovician"; granite 2 of
  505 examples on "Intrusions"). Downloaded the BGS Geology 625k shapefile (OGL, 16 MB, `<cache>/bgs625k/`) and
  dissolved its bedrock once by period range and the kinds of building rock each unit names
  (`data/curated/change/layers/prepare_rocks.py`, GDAL and shapely from the flika env; 11,244 polygons → 68 features;
  `bidb.change_geology` → `app/static/data/change/rocks.json`, 1.3 MB): limestone and dolostone, chalk, sandstone,
  mudstone/pelite/slate, felsic intrusions, dolerite and basalt. BGS 625k includes Northern Ireland.
- Units were first keyed by their oldest period: Bath stone came out at 9% because the Lias Group round Bath runs
  Triassic to Jurassic. Now each unit keeps its period range (p, q) and matches any period in it: 30%.
- 25 materials name their rocks (new field `rock`, checked by `building_materials.validate` against `ROCKS`; Caen stone
  [] = quarried abroad, "no bedrock drawn"). Ireland is drawn by period only (the Irish layer has ages only).
- `change_geology.build` now replaces its layers where they stand in layers.json (it used to move geology and
  coalfields to the end of the Change page's chooser).
- Shares on it: Cotswold stone 81%, gritstone 72%, chalk 71%, limestone 43%, Magnesian 39%, Kentish rag 37%, Bath
  30%, red sandstones 27%, granite and whinstone 20%, Portland 5%, Welsh slate 2% (stones that travelled far).
- Tests 385 OK (new `RockTest`); ui_check of the /types pages + new `material_bedrock`, `material_abroad` 8/8 (port
  5077); Bath stone and granite maps checked by screenshot. Help (Building types) and DATA_LICENSE updated. The
  running GUI needs a restart. Hosted copy not updated (rocks.json adds 1.3 MB; 2.5 MiB is free).
- Next: Ireland's rock kinds (new emergent item), the stones left open, or BT6.

## 2026-10-27 — Ireland's rock kinds on the material maps (BT3c2)
- The material pages drew Ireland by period only (the Irish bedrock layer had ages only). Downloaded the GSI/GSNI
  Bedrock Geology 1:500k shapefile (data.gov.ie, CC BY 4.0 / OGL, 7 MB, `<cache>/gsi500k/`): each unit names its
  rocks ("Argillaceous dark-grey bioclastic limestone, subsidiary shale"). `prepare_rocks.py` now has `bgs` and
  `gsi` modes; `gsi_kinds` matches the six kinds as whole words in the rock part of the name (metamorphic gneiss,
  schist, quartzite and meta-dolerite left out as for BGS; rhyolite left out of felsic as a lava; shale with
  mudstone), `gsi_periods` keeps the age bracket as a period range. 3,257 polygons → 33 features, 495 KB.
- `change_geology.build` merges both files into `rocks.json` (1.7 MB, features tagged `s`); `types_geology.js`
  draws rock kinds in all Ireland and counts examples over the UK and Ireland (no longer "in the UK" only).
  Limestone: 280 of 546 mapped examples (51%) stand on it (was 43% of the British ones).
- Tests 385 OK; ui_check material pages + new `material_ireland` (granite) on port 5078; limestone map checked by
  screenshot. The running GUI needs a restart. Hosted copy not updated (rocks.json +0.45 MB; 2.5 MiB free).
- Next: the stones left open (greensand, ironstone, lias, Bargate, Pennant, Collyweston), or BT6.

## 2026-10-27 — Getting the repository ready to be public
- Checked for going public: no passwords, tokens or keys in any commit, `settings.json` never committed, no
  personal paths (home folder, FANTOM, the mini) in files or history; the 135 commits carry George's Gmail
  address (left as it is; rewriting history was not asked for); history 34 MB, largest file 3 MB.
- README and `bidb/bundle.py` no longer say the repository is private (a token is still used when present, for
  private forks). `LICENSE` is plain MIT again so GitHub detects it (the note on data licences moved to the README).
- CI: `.github/workflows/tests.yml` (Python 3.11, requirements.txt, unit tests, `node tests/ui_prefs_test.js`). On a
  clean checkout two tests needed the database: `test_trade_stories.Here` now skips when there is no `places`
  table, `test_lan` accepts any status but 401/403 for a trusted code (503 with no database). 385 OK, 1 skipped there.
- Issue templates (`.github/ISSUE_TEMPLATE/`: wrong data with a source and whether it is wrong upstream, missing
  record, bug) and labels "data correction", "missing record".
- GitHub Pages: `app.static_export --full-pages` keeps `index.html` a whole document (the claude.ai host wants it
  stripped); the nav's Tours link was `/trip` in every exported page (now `tours.html`, also for the hosted copy).
  Checked under a sub-path (`/british-isles-oldest-buildings/`) with headless Chrome: catalogue, map, types load,
  no 404s. The site (268 MB) is release asset `site.tar.gz` on `site-2026-10-27` (94 MB, SHA-256 checked against
  GitHub's), deployed by `.github/workflows/pages.yml`; db-2026-10-24 kept as Latest. Turning Pages on (Settings ›
  Pages › Source: GitHub Actions) was left to George: it publishes a public site, and a private repository needs
  a paid plan for it.
- `dist/` is now the full-pages build; run `app.static_export` without the flag before republishing the claude.ai
  hosted copy (it is 255.5 MiB of 256).
- George made the repository public (2026-10-27). The bundled database downloads without sign-in (checked); the
  setup page no longer says the release needs GitHub access; roadmap status and A6 (Pages, when wanted) updated.
  Pages workflow left run-by-hand only.
- GitHub Pages switched on (source: GitHub Actions) at George's request; the Pages workflow deployed
  `site-2026-10-27` (run 40534647606); https://gddickinson.github.io/british-isles-oldest-buildings/ checked: pages,
  scripts and data files 200, map drawn in headless Chrome. Address set as the repository's website and linked at
  the top of the README.

## 2026-10-27 — Oldest things: a new page of researched oldest recipes, books, songs, laws, games, customs, objects
- George asked for a page of other historic items (e.g. the oldest recipes), with categories researched and filled.
- New `bidb/oldest_things.py`: eight themes with 4-5 categories each (`THEMES`), one file per theme in
  `data/curated/things/`, entries in the oldest-lists style (claim, evidence, verdict, nation, `where` with role
  kept/made/held/found, sources with exact quotes); `validate`, `claims`, `index`; `--file` checks one file
  (used by the research rounds), `--check` writes `data/things_check.json`.
- Research by four agents in parallel (food + customs, writing + law, music + media, games + objects), each
  validating with `--file` until every quote was found. Abbots Bromley Horn Dance was in both customs and music,
  kept in customs. 113 entries: food 13, writing 17, music 13, law 16, games 14, customs 14, objects 14, media 12;
  74 kept, 10 corrected (haggis's earliest recipes are English, Bushmills' 1608 licence is not the company's
  start, the Trinity College harp is not Brian Boru's, the Lanark Silver Bell is c. 1608-17 not 1160, Up Helly Aa
  is Victorian...), 29 open. Full check: 332 of 332 quotes found. Spot-checked six claims against their quotes.
- Page /things (`app/templates/things.html`, `app/static/things.js`, styles in pages.css): theme chips, search,
  nation, by category or oldest first, map fitted to the entries shown (click a place name to find it), sources
  with quotes and check results; `/api/things`; nav "Oldest things"; hosted copy `data/things.json`; Help section.
- Tests 389 OK (new `test_oldest_things`); ui_check `things`, `things_search` and neighbours 5/5 (port 5079); light
  and dark screenshots checked.

## 2026-10-27 — Quiz and tours brought up to date
- Quiz (15 quizzes): new "Oldest things" (the claim of an entry of /things: which is it? easy from other themes,
  hard from the same) and "What is it built of?" (`quiz_api.materials`: photographed records with materials found in
  the register text or on Wikidata, not the looser Wikipedia sentences; walls first, `BUILT_OF`; windows left out;
  wrong answers never one of the record's materials or related to them by a family link; hard from the same group
  and kind). The first try asked a Biel chapel about wrought iron (its ironwork), hence walls first. The oldest things
  also join "How old is it?" and, from AD 43, "Which came first?"; the "Oldest things" prompt no longer shows the
  category (it gave the answer away). New `tests/test_quiz_materials.py`.
- Tours: themes trade (Markets & trade, Innovations & firsts, markets, shops, banks), sport, civic (Public
  institutions, schools, almshouses and hospitals, civic buildings), graves; titles (the first run stopped on a
  missing title before writing anything); 407 tours (39 new: trade 13, sport 8, civic 10, graves 5; graves found one
  walk only, roadmap). The builder's "Suggest a tour" offers them (it reads the server's themes).
- `tour_surface` kept its Overpass answers by tour id: a regenerated tour with the same id and a new route would
  take the old route's surfaces. Now keyed by a digest of the route's points too. Surfaces of the 63 bike rides are
  being fetched again in the background (Overpass slow, ~3.5 min a ride; 2 done at commit): rides without one
  show no surface line until it finishes.
- Tests all OK; ui_check quiz pages (things, material, first, nametype) and tours (with new `tour_trade`) pass;
  screenshots of both new quizzes and the trade tours checked. Demo site not updated yet.

## 2026-10-27 — Accuracy and safety warnings
- README: final section "Important: how this was made, and how far to trust it" (linked in Contents): everything
  generated automatically by scripts and AI and unchecked by hand; where the data comes from and how dates, types
  and materials are found; what the quote check proves (the source says those words) and what it does not (that
  the source is right or the claim follows), the verdicts; tours are computer-made, untested suggestions, with the
  hazards, access rights by nation and what to check before going.
- Help: new section "Accuracy and safety" (`#accuracy`, in the contents) and a safety paragraph in Tours; Tours
  page: a note above both tabs with "Before you go" (`.tour-warning` in tours.css), linking to Help.
- `static_export._rewrite` now also rewrites page links with an anchor (`/help#accuracy` → `help.html#accuracy`).
- ui_check `tour_warning`, `help_accuracy` and neighbours 6/6 (port 5083); dark-mode screenshot checked.

## 2026-10-27 — Bike-ride surfaces and demo site
- `bidb.tour_surface` rerun after the tours were regenerated (cache now keyed by route): surfaces for all 63 cycle
  tours (51 in the first pass, ~4.4 h; 12 needed one or two more passes after Overpass failures).
- Demo site republished from release `site-2026-10-27-4` (Pages workflow run 40596033853); old site releases
  `site-2026-10-27` and `-2` deleted; `db-2026-10-24` kept as Latest.

## 2026-10-27 — C6b: Wikidata inventions in the isles
- New `bidb/innovations_wd.py`, run inside the oldest_lists stage: a narrow QLever query (inventor P61 + place of
  discovery P189 or creation P1071, no class tree; seconds, where the first C6b query timed out). Wikidata places few
  inventions: 16 kept (a place in the isles with its own coordinates, not a whole nation; finds, fossils, museum objects
  and the 36 researched innovations left out; "mechanical computer" and Salter's duck reviewed out in `SKIP`).
  Kind "Invention or discovery (Wikidata)" in Innovations & firsts, described as unchecked Wikidata statements; 10
  linked to their place (Broom Bridge, King's College London, University of Manchester...). Five (electron, proton,
  neutron, xenon, Hamilton scale) had been "finds" from places_build; the stage now replaces those rows.
- Written into the existing database with only this step (rerunning a whole stage undoes later stages), then
  `bidb.nation_geo` (nations for the 16). Detail views label `inventors` "Invented or discovered by".
- Tests 394 OK (new `test_innovations_wd`); ui_check places OK; card checked in a screenshot. Demo site and hosted
  copy not updated (the database changed: next release).

## 2026-10-27 — C2d3b1: later tea prices
- C2d3b split: C2d3b1 prices (done), C2d3b2 duty before 1874 and after 1938 (pending: the Annual Abstracts from
  No. 84 print no tariff; needs the Finance Acts).
- New graph "Wholesale price of tea" (`tea_auction_uk`): "Tea—Indian average, London Auctions" from the Board of
  Trade's wholesale prices table, read from the page images of No. 78 (table 156, pp. 224-225: 1913, 1920-33) and
  No. 83 (table 192, pp. 258-259: 1924-38); overlapping years equal. 14.06d. a lb in 1913, 25.23 in 1923, 10.24 in
  1932, 19.44 in 1938; 1914-19 not printed (`gap: 2`, drawn dotted). No. 77's OCR misreads 1922 (22.98; page 22.93).
- "Price of imported tea" now carries tea from India and Ceylon and from China (No. 68 table 49 pp. 218-219,
  1908-22) as two more lines (`models`); India within 0.5d. of all tea 1908-19; China 39.80d. in 1918 as printed.
- Tea trade story shows the new graph. New `tests/test_tea_prices.py`; ui_check `change_tea` now requires the
  wholesale graph. Tests 397 OK; ui_check change_tea, trades OK; light and dark screenshots checked. Hosted copy not
  updated.

## 2026-10-27 — C2d3b2: tea duty 1847-1964
- "Duty on tea" now runs 1847-1964 (was 1874-1938). Before 1874 from the Budget debates in Hansard (historic-hansard
  and the Hansard search API; the Victorian Customs and Revenue Acts carry no text on legislation.gov.uk): 2s. 2¼d.
  (26¼d.) in 1847 and 1852, 1s. 10d. 1853, 1s. 6d. 1854, 1s. 9d. 1855, 1s. 5d. 1857, 1s. 1863, 6d. 1865. After 1938:
  Hansard 22 June 1949 gives the rates then as 8d. foreign and 6d. Empire (so unchanged through the war); Finance
  Act 1949 s. 1 (enacted text, OGL) 2d. on foreign tea, Empire tea free from 7 April 1949; Hansard 22 July 1963 on the
  No. 4 Order making it a protective duty; London Gazette 17 Dec. 1963 (issue 43185 p. 10290): the No. 11 Order
  removed the import duties on tea from 1 January 1964. Every row quotes its source (`note` column).
- Three new sources (`hansard_tea_duty`, `finance_act_1949_tea`, `london_gazette_1963_tea`), 119 in all; notes of both
  series rewritten. New `tests/test_tea_duty.py` (steps join up, span, every row cites); ui_check `change_tea`
  now requires the 1847 and 1964 ends. Tests 401 OK; ui_check change_tea, trades OK; graph checked in a screenshot.
- Left as C2d3b3: tea prices by country before 1865 (Abstract No. 13). Hosted copy not updated.
