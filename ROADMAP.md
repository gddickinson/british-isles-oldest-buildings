# ROADMAP

Future work for British Isles Oldest Buildings, kept between sessions. Newest decisions first in
each section; tick items off (and move them to SESSION_LOG.md) when done.

## Status (2026-10-22)
- Catalogue 22,039 records; 173,657 places of interest in 22 groups (latest: shipwrecks); 11,927 people;
  517 floor plans; "Change over time": 50 cited series, 32 events, 4 map layers; 870 researched claims (1,660 quotes,
  1,658 found). Database release db-2026-10-22-4 (81 MB). Download cache on an external drive.
- Hosted copy https://claude.ai/artifact/4H8rfcGGxSJki91SrNFTPv (private), version 59: 253 MiB of the
  256 MiB limit, 479 of 511 files (place texts cut to 300 characters, floor plans 420 px WebP q45,
  1,100 thumbnails; the local app keeps everything). Republish changed files only: checksum `dist/` before and after `python -m
  app.static_export`, publish in batches under 64 MB, removed files with null, removals first.
- Figures: `node docs/make_figures.mjs` (app running); the setup figure needs a copy with no data
  (`git archive HEAD | tar -x -C <dir>`, run on port 5071).

## Data quality and references
- [x] Reviewed the 451 date-check conflicts (2026-10-20, `docs/date_review.md`): checker noise
      removed, new status "Earlier origin" (67), 56 reviewed corrections with evidence
      (`data/curated/date_corrections.json`, `python -m bidb.date_corrections`), 69 genuine
      conflicts left for research.
- [ ] Research the 69 remaining conflicts (`docs/date_review.md`) against primary sources (listing
      texts, county histories) and add entries to `date_corrections.json` where settled.
- [ ] Fix the Wikidata dates listed in `docs/date_review.md` at source (needs a Wikidata account).
- [ ] Review research entries marked "year not found in source" (Data quality page); add a better
      source or correct the claim in `data/curated/*.json`.
- [x] HES portal and Cadw full-report descriptions → dates (`bidb/register_dates.py`), 2026-10-20.
- [ ] Remaining undated landmarks (mostly England, ~3,900; Isle of Man ~330): mine full Wikipedia
      articles (one request each), NI Historic Buildings `Date_Const` (joined by HB number).
      England's register has no dates anywhere machine-readable, and list-entry pages sit behind a
      Cloudflare bot check (checked 2026-10-20), so the 3,195 undated English entries with an NHLE
      number need Historic England's help (bulk text) or manual work.
- [x] References for people links (shown as "source: …") and for Wikidata places (dates,
      designations), 2026-10-20.
- [ ] Known Wikidata errors to fix at source: Joan of Arc "place of burial" = Winchester Cathedral
      (statue, not grave).
- [x] German fallback labels rewritten ("Court Tomb von Doon" → "Doon court tomb"), 2026-10-20.

## Images
- [x] Commons geosearch for records without a photo (`python -m bidb.images_extra`).
- [ ] Run the same for Wikidata places and Open Plaques (`python -m bidb.images_extra places`;
      ~2.8 s per place, ~35k places: several sessions; results are cached, so re-runs resume).
      Register monuments (~32k) are not included yet.
      (Places run stopped at 1,620 of 17,566 on 2026-10-20; resumes from the cache.)
- [ ] Geograph Britain and Ireland API directly (needs an API key; CC BY-SA) for remote sites.
- [ ] Commons category (P373) galleries are only fetched live in the local GUI; consider caching
      the first image per category for the hosted copy.
- [ ] People portraits are not embedded in the hosted copy (external images are blocked there).

## Maps
- [x] Canals (OSM `waterway=canal`, dashed) added to the rivers layer; French rivers removed.
- [x] Minor roads (OSM secondary/tertiary, B roads) as an optional layer (off by default), loaded
      in 1° tiles from zoom 9, 2026-10-20.
- [x] Major streams at high zoom (named streams in 1° tiles, `streams/`).
- [x] National Trails (OSM `route=hiking network=nwn`) as an optional layer, 2026-10-20.
- [x] Historic county boundaries (pre-1974): Historic County Borders Project layer (`historic_counties.json`).
- [ ] Offline map detail stops around zoom 13; consider vector tiles (PMTiles, protomaps) for
      street-level offline detail if the hosted size budget allows.
- [x] Parks queried by `designation=*` too: Eryri, the Broads, Llŷn, Anglesey, NI AONBs added.
- [x] All 40 Scottish National Scenic Areas from the Scottish Government's ProtectedSites layer (OGL), 2026-10-22.

## Floor plans and outlines
- [x] Building outlines from OSM ways/relations tagged with the catalogue's Wikidata ID.
- [x] Floor plans from Wikidata P3311, laid over the outline (approximate fit).
- [x] Commons "Plans of <building>" categories (`bidb/commons_plans.py`): +29 plans named as plans.
- [ ] Proper georeferencing of plans (control points; Allmaps annotations) instead of stretching
      the image to the outline's bounding box.

## Historic maps
Done: NLS layers (six-inch, one-inch, Bartholomew, Old Series overview, Roy, Ireland one-inch,
Isle of Man, Channel Islands, 153 town plans), Gough Map (Warper 252), Rumsey atlas maps via
Allmaps; hosted copy bundles low-zoom WebP tiles of 9 layers (one JSON pack per layer: an artifact version holds at most 511 files).
- [ ] OS Old Series at full detail: checked 2026-10-22, the NLS tile store has it only to zoom 9 (zoom 12+ 404) and
      the detailed NLS viewer uses MapTiler (key); no published Allmaps annotation found. Needs NLS's annotation.
- [x] Ireland six-inch by county (NLS, first edition and later revision, 32 counties incl. Northern Ireland; M3).
- [ ] Pre-warp Saxton (1579, CC0) and Speed (1611) national maps with GDAL (gdal_translate GCPs →
      gdalwarp -t_srs EPSG:3857 -tps) for the hosted copy; starter GCPs in the research notes. Checked 2026-10-22:
      no ready-made tiles anywhere (Allmaps' index has no titles; the BL Georeferencer needs a login), so GCPs by hand.
- [x] "Historic maps of this place" on detail views (`app/historic_allmaps.py`, 4,436 maps).
      The bulk file has no titles; NLS maps link to the library record. Titles would need one
      IIIF manifest request per map.
- [x] William Smith geological map 1815 (Warper 150), bundled z5–8.
- [x] Northern Ireland historic six-inch: covered by the NLS Ireland six-inch layers (M3). OSNI's own sheets
      (OpenDataNI, OGL, 1829–62, georeferenced JPG + world file in 37–750 MB zips) only if a second scan is wanted.
- Not usable: Tailte Éireann historic maps (referer-locked, licensed to public bodies);
  David Rumsey Georeferencer tiles (need sign-in); NLS MapTiler layers (need a key).

## Places and people
- [x] Open Plaques (public domain): ~19,700 plaques by bounding box (`bidb/openplaques.py`);
      names from the inscription. Erected dates and subjects need one request per plaque.
- [ ] Jersey HER (Arches JSON API) has periods and descriptions but no stated licence: ask
      JerseyHER@jerseyheritage.org before using.
- [ ] Isle of Man registered buildings (pabc.gov.im blocks scripted access): ask for a CSV.
- [ ] Guernsey protected monuments/buildings: PDF lists without coordinates (geocode by parish).
- [ ] Portable Antiquities Scheme findspots (licence and coordinate precision limits apply).
- [ ] Ancient Tree Inventory (Woodland Trust) for notable trees; check licence.

## GUI
- [x] Search people names from the catalogue search box (people_text in FTS), 2026-10-20.
- [x] Floor plans load on demand in the hosted copy (one 3 MB shard per detail view; −54 MB).
- [x] Hosted copy first load 72 MB → 22 MB: thumbnails (600 KB files, oldest first), detail-only
      fields and building outlines are fetched on demand, 2026-10-20.
- [x] Hosted copy places index (2026-10-22): location cells (`data/pcells/`) and 16 id shards; a detail view fetches
      ~1–2 MB instead of 18 MB, opening a place ~6 MB instead of 77.
- [x] Settings page (appearance, catalogue/map defaults, recently viewed, shortcuts, data
      location mover, screenshot browser, backup/reset), Help guide with figures, top-bar Export
      menu (CSV/JSON/GeoJSON/KML, screenshots, print), ⌘K quick search, keyboard shortcuts,
      2026-10-20.
- [ ] Settings in the hosted copy are per-browser only (no data location / screenshots there);
      screenshots there could use html2canvas if wanted.
- [x] Mobile layout review (375 px): Map page, layer switcher and detail view wrap correctly,
      2026-10-20. (Headless Chrome's minimum window width makes 390 px screenshots look cut off;
      check inside a 375 px iframe instead.)

## Pronunciations (added 2026-10-20)
How names are said, for buildings, places, people and the towns they lie in, with regional and
language varieties. Built 2026-10-20: `bidb/pronunciations.py` (stage of bidb.build), tables
`pronunciations` + `pron_towns`, Pronunciation page, box under names in detail views, CSV/JSON
export, coverage on the Data quality page, hosted copy via `data/pron.json`.
- [x] Schema, sources (Wikipedia lead `{{IPAc-en}}` / `{{IPA|xx}}` / `{{respell}}` / `{{langx}}` incl.
      footnotes; Wikidata P443 recordings incl. Lingua Libre Welsh place names, P898 IPA), varieties
      (qualifiers "locally"/US/Scottish; Welsh, Scottish Gaelic, Irish + Munster/Connacht/Ulster,
      Manx, Scots, Cornish, Jèrriais), GUI, export, coverage report.
- [x] English Wiktionary for town names (`bidb/pron_wiktionary.py`): +1,600 entries, regional
      varieties (RP, Northern/Southern English, Scottish, Welsh north/south, Yorkshire, Scouse…),
      2026-10-20.
- [x] Native-name search: other-language names in the catalogue's full-text index (450 buildings;
      accents ignored in the hosted copy too), 2026-10-20.
- [x] Places search (Places page) uses other-language names too (148 places, e.g. "Blàr na Léine"), 2026-10-20.
- [ ] Logainm.ie (Irish placenames database, has audio for Irish names; check licence/API) and
      Ainmean-Àite na h-Alba (Gaelic place names) for towns without a Wikipedia pronunciation.
- [ ] Hard-looking names without any pronunciation are listed on the Data quality page: research
      them (sources first) or add them to the Wikipedia article / Wikidata.
- [ ] Hosted copy: recordings open on Commons (external media are blocked in the sandbox).

## Stories and tours (added 2026-10-20)
- [x] Stories from full Wikipedia articles (`bidb/stories.py`): 1,904 stories for 1,326 records in four
      themes (ghosts & the supernatural, legends & myths, folklore & customs, curious history); detail
      views, Stories page with map, catalogue filter, hosted copy (`data/stories.json`), 2026-10-20.
- [x] Ready-made tours (`bidb/tours.py`): 164 walks, bike rides and drives (highlights, ghosts &
      legends, prehistoric, castles, early churches, Roman), routed with OSRM (routing.openstreetmap.de),
      ferry crossings noted, 2026-10-20.
- [x] Tour builder (replaces the trip planner): ☆ buildings and places, walk/cycle/drive, round trip,
      best order (nearest neighbour + 2-opt), suggest a tour (place/postcode/location/map centre, time,
      theme), stops along the way, saved tours, GPX/KML, Google Maps directions, print, 2026-10-20.
- [ ] Stories: more sources (Historic England / HES "folklore" in list texts, Irish Folklore
      Commission Schools' Collection at duchas.ie (check licence), Wikidata "reportedly haunted").
- [ ] Stories rules: legends inside "History" sections are sometimes ordinary history with the
      word "legendary"; a reviewed list of false hits (like `date_corrections.json`) if needed.
- [x] Tours: surface for bike rides (2026-10-22, `bidb/tour_surface.py`: % paved, unpaved, traffic-free from OSM ways;
      OSRM itself returns no surface). Opening times / ticketed
      sites, public transport to walk starts, multi-day touring routes with overnight stops.
- [ ] Hosted copy: builder routes are straight-line estimates (external services are blocked there).
- [ ] Period labels: Irish records of AD 43–410 are labelled "Roman Britain" (period is set from the
      date alone); Ireland's Iron Age continues to c. AD 400.


## Further additions (planned 2026-10-20; worked through 2026-10-20)
Stories and history
- [x] F1 More story sources: tales in the HES / Cadw register descriptions already cached (6 stories,
      OGL). Wikidata "reportedly haunted" is a list, not a class: covered by the Wikipedia categories.
- [ ] F1b dúchas.ie Schools' Collection: API needs a key (user to register); licence appears to be
      non-commercial: check before use.
- [x] F2 "On this day" (History page): 17,649 dated events; Julian dates converted back (Hastings 14 Oct).
- [x] F3 Timeline per building: 45,875 events for 8,034 buildings (`bidb/timeline.py`).
- [x] F4 Story review list `data/curated/story_rejects.json`, plus rules (sport, film, modern sentences).
- [x] F5 Audio: 🔊 read-aloud on stories, "Listen to the tour".
Tours
- [x] T1 Elevation profile and hilliness (OpenTopoData EU-DEM 25 m, ~every 500 m; climbs understated).
- [x] T2 82 long-distance and pilgrim ways with sights along the path and ~20 km day stages.
- [x] T3 Visiting information from OSM (operator, opening hours, fee, wheelchair): 1,067 records.
- [x] T4 Railway, heritage-railway, metro and bus stations (4,400): map layer, "Getting there".
- [x] T5 📍 Follow (next stop, distance, direction, visited); saved tours and opened records work
      offline in the installed local app.
- [x] T6 Share link for your own tour (stops in the URL).
Data quality
- [x] D1 Irish and Manx period labels: "Iron Age" for AD 43–410 (48 buildings, 1,352 places).
- [ ] D2 Undated English entries: ask Historic England for bulk list texts (user; site blocks scripts).
- [x] D3a Research the 69 date conflicts: 9 corrected, 58 kept with reasons, 2 open (Althorp,
      Hadlow Castle), 2026-10-21 (`docs/date_review.md`).
- [ ] D3b Fix 14 Wikidata dates at source (user's Wikidata account).
- [x] D4 Lakes, lochs and reservoirs layer (OSM, tiled, filled, relations included), 2026-10-21.
- [x] D5 Raw OSM cache slimmed (minor roads 413 → 208 MB, streams 208 → 132 MB; `slim_cache`).
Maps
- [x] M1 Historic counties (pre-1974, Historic County Borders Project, free with acknowledgement).
- [x] M2 Street detail offline for saved areas (Protomaps vector tiles, zoom 10–15, local app).
      A whole-isles street map is several GB and not suited to the hosted copy.
- [x] M3 Ireland six-inch, first edition and later revision (NLS, 32 counties each, incl. NI).
- [ ] M4 Georeferenced floor plans: needs control points placed by hand (Allmaps editor).
App and hosted copy
- [x] A1 Light places index (`data/places_geo.json`) for building pages in the hosted copy.
- [x] A2 Installable app: manifest, icon, service worker (local GUI).
- [x] A3 Accessibility: contrast checked (all ≥ 4.5:1), visible focus, dialog focus, labels, live counts.
- [x] A4 Browser checks of every page: `python -m tests.ui_check` (20 pages).
- [ ] A5 Share the hosted copy (user, from the page's Share menu).
New content
- [ ] N1 Portable Antiquities Scheme (CC BY, precise findspots need registered access) and Ancient
      Tree Inventory (Woodland Trust, access on request): user to ask.
- [ ] N2 Isle of Man, Guernsey, Jersey registers (data requests, user).
- [ ] N3 Logainm.ie (CC BY 4.0; API key from the Gaois Developer Hub, user to register); Ainmean-Àite
      na h-Alba (no open API found).
- [x] N4 Quiz: "Guess the period".

## More layers and places (planned 2026-10-21)
Paths and trails
- [x] P1 (2026-10-21: regional and local walking route relations, 4,437 lines; individual footpaths not yet) Walking paths and trails: OSM footpaths and bridleways (highway=footway/path/bridleway with
      a name or designation=public_footpath/bridleway), regional and local walking routes
      (route=hiking network=rwn/lwn); tiled like minor roads, from zoom 12.
- [x] P2 (2026-10-21: NCN and regional cycle routes, 6,945 lines; tour routing on them not yet) Cycle tracks and trails: OSM cycleways (highway=cycleway, cycleway=track), National Cycle
      Network and regional routes (route=bicycle network=ncn/rcn); a layer, and route choice for
      bike tours (prefer cycle routes).
- [x] P3 (2026-10-21: OSM Roman roads, 1,036 lines; drove roads, salt ways, corpse roads to add) Ancient and lost trails: Roman roads (OSM historic=roman_road; Wikidata; Margary numbers),
      drove roads, salt ways, corpse roads, ancient trackways (Ridgeway, Icknield Way, Sweet Track),
      pilgrim routes no longer walked; layer + stories.
Water
- [x] W1 (2026-10-21: named culverted rivers and streams, 28,747 lines; notes on London's lost rivers to add) Lost and buried rivers and streams: culverted rivers (OSM tunnel=culvert / waterway with
      historic or covered tags), London's lost rivers (Fleet, Tyburn, Westbourne, Effra…), other
      cities' buried rivers (Wikipedia "subterranean rivers" categories); a dashed layer with notes.
Places of the imagination
- [x] L1 (2026-10-21: 81 places of legend; more Irish/Welsh myth sites to add) Mythical places from legends and ancient history: Camelot candidates, Avalon, Lyonesse,
      Cantre'r Gwaelod, Tír na nÓg sites, Arthurian and Fenian sites, holy wells and fairy forts,
      places in the Mabinogion and Irish sagas (Wikidata: "legendary place" / "mythical location"
      with a location in the isles; Wikipedia lists); claims shown as claims.
- [x] L2 (2026-10-21: 98 haunted places + stories; tour theme) Haunted houses and places: Wikipedia "Reportedly haunted locations" categories and lists,
      Wikidata items; merged with existing stories (ghost theme), a map layer and tour theme.
- [x] L3 (2026-10-21: 116 literary settings, writers' homes/graves in 6 literary tours) Places of importance from literature: settings and real places in novels, poems and plays
      (Wikidata "narrative location" P840 for works, "located in fictional universe"), writers'
      houses and graves (existing people links), literary trails; a "Literary places" theme for
      tours and stories.

## Maritime, industrial and Victorian (added 2026-10-21)
- [x] Maritime heritage (`bidb/maritime.py`): harbours and ports, docks and wharves, shipyards and
      slipways, ropewalks, custom houses, lighthouses, lifeboat stations, naval bases, museum ships,
      shipbuilding firms (Wikidata) as a places group; "Maritime heritage" tours, 2026-10-21.
- [x] Industrial Revolution and Victorian era (`bidb/era_places.py`): mills, mines, ironworks, canals,
      railways (opening dates), engine houses, kilns, iron bridges, warehouses (1700–1914) and Victorian
      public buildings, piers, glasshouses and Victorian-style buildings (1837–1901); tours, 2026-10-21.
- [x] Shipwrecks (2026-10-22, `bidb/wrecks.py`): 3,768 Canmore wreck records and 3,564 from the Wreck Inventory of
      Ireland. Still open: ship launches (Wikidata ships built at isles yards); England's full wreck record is not open
      data (only the 57 protected wrecks and 1,842 WWI losses). Original note: (Wikidata ships built at isles yards; wreck sites, licence check
      for the UKHO / Historic England wreck data).
- [ ] Victorian listed buildings beyond Wikidata: checked 2026-10-22: the register map layers (NHLE, HES, Cadw) carry no
      construction date (Cadw only the listing date); would need every list text (D2).

## Installation, data location and maintenance jobs (planned 2026-10-21)
- [x] I1 (2026-10-21) `run.sh` checks the configured data folders first (no `mkdir` on an unplugged drive) and
      takes `--data DIR` (use or create `DIR/UK_BUILDINGS_DATA/{cache,database}`), `--build`
      (build in the terminal) and `--port`.
- [x] I2 (2026-10-21) First-run setup page in the GUI when there is no database: use the bundled database, use an
      existing data folder, or build from scratch (choosing where the ~3 GB download cache goes).
- [x] I3 (2026-10-21: stage bar weighted by last run, items, downloads/cache hits, time left) Build progress: stage k of n with a bar weighted by the previous run's stage times, items
      within long stages, downloads vs cache hits, elapsed and estimated time left.
- [x] I4 (2026-10-21: tested closing and reopening the GUI, stop, killed job) Jobs run detached (own session): closing the GUI or its terminal does not stop them; the
      GUI re-attaches on reopening (status file + process id), can stop a job, and reports a job
      that died.
- [x] I5 (2026-10-21: --refresh-days / --refresh; per-title Wikipedia stores restart too) Refresh: rebuild with downloads older than N days, or from chosen sources (Wikidata,
      Wikipedia, Commons, registers, OSM, postcodes), fetched again; the rest from the cache.
- [x] I6 (2026-10-21) GUI buttons for the other jobs: photos, footprints and floor plans, offline map layers,
      hosted export, package the database for sharing.
- [x] I7 (2026-10-21: journal untracked; bundled database now a GitHub Release asset, data/bundled.json) Stop tracking `data/british_isles_buildings.sqlite-journal`; refresh the shipped
      `british_isles_buildings.sqlite.gz` (a "package" job, so local rebuilds don't dirty git).

## Underground works (planned 2026-10-21; after I1–I7)
- [x] U1 (2026-10-21: 292 tube/subway/metro stations, 24 ghost stations, map layer "Underground railways &
      tunnels" from OSM railway=subway and tunnels; places group "Underground", tours) Underground railways and stations: London Underground, Glasgow Subway, Tyne and Wear Metro and
      Liverpool/Merseyrail tunnels; stations with opening dates (Wikidata), disused and "ghost" stations
      (e.g. Aldwych, British Museum, Down Street), lines as a map layer (OSM railway=subway, tunnels).
- [x] U2 (2026-10-21: 569 tunnels, 154 shelters/bunkers/ROC posts, 177 caves, 278 mines, 626 ice houses, 111
      grottoes, catacombs, Bazalgette's sewers; `data/curated/underground_sites.json`. Still to do: deep shelters
      and reservoirs beyond the curated list, cellars) Other major underground construction: railway, canal and road tunnels (Thames Tunnel, Box,
      Standedge, Severn, Channel Tunnel), sewers and storm drains (Bazalgette's system), water tunnels
      and reservoirs, mines and caverns, Victorian and wartime deep shelters, bunkers and ROC posts,
      cellars, catacombs and ice houses; places group "Underground", tour theme, stories.

## Historic war construction (planned 2026-10-21; after the underground works)
- [x] X1 (2026-10-21: 32 burhs of the Burghal Hidage, 135 Martello/defensive towers, 251 forts from 1500 incl.
      Device and Palmerston Forts, 223 batteries, 429 barracks/drill halls) Defences through the ages: hillforts and Roman forts are in already; add Saxon burhs,
      Martello towers, Palmerston forts, coastal batteries, Napoleonic and Victorian barracks and signal
      stations (Wikidata, heritage registers by type).
- [x] X2 (2026-10-21: 146 pillboxes/anti-tank works, 72 radar/sound mirrors, 718 airfields, 83 POW camps,
      7,095 war memorials; 3,710 OSM pillboxes, bunkers, gun emplacements and trenches as a map layer.
      Defence of Britain data not used yet) Twentieth-century military works: First and Second World War pillboxes, anti-tank lines and
      stop lines, anti-aircraft and searchlight batteries, sound mirrors, radar stations (Chain Home),
      airfields, naval dockyards and boom defences, POW camps, Cold War bunkers and ROC posts
      (Wikidata, OSM historic=bunker/pillbox, Defence of Britain data where the licence allows).
- [x] X3 (2026-10-21: group, layer of OSM defences, tours "Coastal defences" and "Military heritage". Stop
      lines as drawn lines still to do: only the Taunton Stop Line has a point on Wikidata) Places group "Military heritage" with periods, a map layer for defensive lines, a tour theme
      ("Coastal defences", "Stop lines") and stories.

## Bridges (planned 2026-10-21; before MU2)
- [x] B1 (2026-10-21: 13,502 bridges on Wikidata, 12,688 new places + 334 regrouped; 471 in the catalogue) Bridges as a places group "Bridges": every bridge on Wikidata in the isles (road, foot, railway
      viaducts, aqueducts, packhorse and clapper bridges, swing/bascule/transporter, suspension and
      cable-stayed), by type, with opening years; the 724 bridges in the catalogue stay there; iron
      bridges, viaducts and aqueducts from the industrial and Victorian stages move to this group.
- [x] B2 (2026-10-21) A "Bridges" tour theme (walks, rides, drives).

## Research track: original sources and evidence (started 2026-10-21)
Substantiate claims from original and published sources, never silently. Every researched claim goes in
`data/curated/evidence.json` with its sources (kind: primary / listing / secondary / reference), where in each
(locator) and an exact short quote; `python -m bidb.evidence --check` fetches each source again and confirms the
quote is there; verdicts (kept / corrected / open) feed `date_corrections.json` / `date_confirmations.json`.
Detail views show "Evidence"; the Data quality page lists every claim. Sources that cannot be fetched by a script
(paywalled books, Historic England list pages, archives in person) are cited with a locator and marked unreachable.
- [x] R0 Evidence file, checker, app display, tests (2026-10-21).
- [x] R1 The two open date conflicts: Althorp (c. 1508 kept: list entry 1356626) and Hadlow Castle (corrected to
      late C18 house, tower 1838–40: list entry 1070451). No date conflicts remain.
- [x] R2 (2026-10-21) The 69 research entries whose year was not found in the cited source: 60 settled with
      quoted evidence (51 kept, 12 corrected incl. earlier batches: Royal Hospital Kilmainham 1679–87, Lancaster
      Castle prison 1196, Winchester City Mill 1744, brochs c. 300 BC, Knap of Howar c. 3800 BC, Greensted Church
      timbers 1053+, Brixworth late 8th/early 9th c., Castle of Old Wick 14th c., Arnol Blackhouse c. 1880, Merchants'
      Warehouse 1823…); 12 sources replaced (wrong article or unreadable) by listing texts and better articles.
      Verification then: 325 confirmed, 38 evidenced, 9 open.
- [x] R2b (2026-10-21) The 9 left open: Duke Humfrey's 1488 (Bodleian Library), Hereford chained library 1611
      (Thornton), Ballyhaunis 1987, Escomb 7th c. (list entry 1292122: "C7"; 670–690), Irish round towers c. 950
      (Annals of Ulster U950.7, the bell-house of Slane: primary), Ballycopeland c. 1790 (Geograph after McCutcheon;
      the site refuses scripts, so "unreachable"); corrected: Chichester Cross c. 1500 (listing), Eling Tide Mill mid
      C18 (listing), Glenturret 1763. Catalogue dates now follow the research file without a rebuild
      (`refresh_claims`); 8 researched examples that were in the catalogue twice are merged (build fixed).
- [x] R3 (2026-10-21/22) Every researched oldest-of-type example now has quoted evidence. First pass: 102 claims
      quoting list descriptions (`bidb/listings.py`) and 9 legends corrected (Ye Olde Fighting Cocks C16 not 793,
      Bingley Arms 1738 not 953, Ye Olde Trip late C17 not 1189, …). Second pass (2026-10-22): the 88 remaining
      examples (Ireland: NIAH; Northern Ireland: HED register; Scotland: HES; Wales: Cadw/Coflein; Isle of Man; England
      without a list id in the data, and the 6 pages with another layout), each quote checked by script. 67 kept,
      18 corrected, 3 open. Corrections include Sean's Bar c. 1725 (claimed c. 900; NIAH 15000331), Smock Alley
      Theatre 1735 rebuild, Marsh's Library 1701–3 (1707 is the Act), Dublin Pearse 1884, St James's Gate c. 1800
      vat houses, Kilkea Castle 15th c., The Old Inn Crawfordsburn mid C19 (claimed 1614; not listed), Old Bushmills
      1784 (1608 is a district licence), King's College Chapel Aberdeen 1500, Fortnum & Mason c. 1770 (1707 has "no
      supporting evidence", Survey of London), Fitzwilliam 1837–43, Ewelme School c. 1450, Hemingford Grey c. 1150,
      Devil's Bridge C15/early C16, Vicar's Pele c. 1400, Albert Dock 1841–5. Innerpeffray settled (books from 1680,
      formal foundation 1691); Stokesay kept (listing's "c1391" a slip). Open: Woodenbridge Hotel 1608, Grace Neill's
      1611 (both only tradition), Fossdyke's Roman date. 23 further catalogue dates fixed where the record's own date
      (Wikidata / article mining) was for something else (Forth and Clyde Canal "800", Wool House "1966", Syon
      conservatory "1547" = Syon House, Somerset House "1630", Exeter Ship Canal "1270" = the weir, …).
      Notes: some records' list ids point at a scheduling or a park entry rather than the building (Bourn Windmill,
      Royal Observatory, Syon conservatory, Royal Hospital Chelsea, Tarr Steps, Aydon); the evidence cites the right
      entries. Build fix: two research entries sharing one Wikipedia article (Ewelme) both get records.
- [x] R4 (2026-10-22) Earliest churches and monasteries from primary sources: 40 early foundations checked against
      Bede (Gutenberg, Sellar), the Anglo-Saxon Chronicle (Avalon / Gutenberg, Ingram), Bede's Lives of the Abbots,
      the Annals of Ulster (CELT), charters (Electronic Sawyer, with the scholarly view of each charter's
      authenticity), Asser, list descriptions and the VCH (British History Online). 26 kept, 5 corrected, 9 open;
      16 dates sharpened or corrected: Reculver 669 (ASC), Wearmouth 674 (Bede), Ripon c. 660, Malmesbury 675,
      Hartlepool before c. 649, Gilling after 651, Selsey 681, Worcester see 680, Evesham c. 701, Winchcombe 798,
      Old Minster 643 (ASC), Rochester 604 (Bede II.3), Glastonbury by c. 680 (charters to Abbot Hæmgils, not 712),
      St Mary in Castro c. 1000 (not 7th c.), Deerhurst 8th c., Bradford-on-Avon 10th c. Open where only later
      tradition gives the date (Abingdon, Pershore, Tewkesbury, Wareham, Folkestone, Leominster, Repton, Candida
      Casa) and Brixworth (listing C7 vs reviewed late C8/early C9).
      Domesday entries (`bidb/domesday_entries.py`): Open Domesday place pages for the settlements of every church,
      abbey and cathedral (churches, priests, households, Phillimore reference) → shown in the Domesday line of
      detail views; `--report` lists early churches with a church or priest in 1086 and later-dated ones where
      Domesday already records a church (possible earlier origin).
      Still possible: Eddius's Life of Wilfrid and Felix's Life of Guthlac (no script-readable text found), VCH
      parish histories for manors, dendrochronology reports.
- [x] R4b (2026-10-22) Manor houses (Victoria County History + list entries): 30 English manor houses dated
      1000–1300 checked; the suspicion held: 19 dates were the Domesday manor or an earlier building, not the house
      (Melford Hall 1559 not 1065, Hughenden 1738 not 1086, Ugbrooke, Icomb Place, Treasurer's House York, Sherborne
      Castle…). Lives of saints: Eddius's Life of Wilfrid (Colgrave 1927, Internet Archive text) for Ripon and
      Hexham; the Old English Life of Guthlac (Goodwin 1848) for Repton (now kept) and Crowland.
- [x] R6 (2026-10-22) Tree-ring dates (`bidb/dendro.py`): the Vernacular Architecture Group's Dendrochronology
      Database (ADS; 4,879 dated entries) matched by grid reference (`bidb/osgrid.py`) and name to 592 catalogue
      buildings (1,129 dates), shown as "Tree-ring dated:" in detail views. `--report` lists catalogue dates later
      than a building's own timbers: 13 corrected (Harlowbury c. 1220 not "1884", Godinton c. 1390 not "1991", The
      Commandery 1465 not "1977", Duff House 1735 not "1995", Tudor Tavern Taunton 1320s, Llwyn-celyn 1419,
      Sizergh Castle pre-C15 hall not "1920", …); the rest are separate buildings of an estate or earlier fabric.
- [x] R7 (2026-10-22) Sanity check of the 100 oldest records: 72 kept, 18 corrected, 10 open, many with
      radiocarbon/Bayesian dates (Gathering Time; Bayliss et al.). Dates mined from Wikipedia sentences about other
      things are gone: Avebury c. 2900 BC (not 4250), Hembury and Chestnuts no longer "fifth millennium BC", Bryn
      Celli Ddu c. 3070 BC, Knap of Howar's stone houses c. 3300 BC (PSAS 2025), Wayland's Smithy 3590 BC, Wor Barrow
      3670 BC. Record problems (duplicates, wrong county, wrong type) listed in docs/date_review.md.
- [x] R8 (2026-10-22) Researched "oldest" lists of things that are not buildings (`bidb/oldest_lists.py`, 277
      entries, each with sources and quotes): nature (60: Fortingall Yew, Lewisian gneiss, Rhynie chert, Happisburgh
      footprints, Giant's Causeway…), graves (75: Aveline's Hole, Roman tombstones, the Latinus and Catamanus stones,
      the oldest dated headstones, Bunhill Fields, Kensal Green…), trade (70: markets and fairs by charter, market
      buildings, the oldest shops and firms — Lock & Co 1726 not 1676, Borough Market first recorded 1276 —,
      manufacturers, industrial works) and infrastructure (72: the Post and Sweet Tracks, Roman roads, the New River,
      waggonways, the first canals, docks, gasworks, pillar boxes). Shown on the Oldest page and as places.
- [~] R5 Historic England list texts behind the bot check: cite by list entry number (reproductions such as British
      Listed Buildings can be checked by script). `bidb/listings.py` reads them (both page layouts); used for R3.

## Archaeology: digs and treasure (added 2026-10-21)
- [x] D1 Excavations (`bidb/digs.py`): 604 excavated sites on Wikidata (dated excavations, directors of fieldwork,
      discoverers) and 205 Time Team digs (Wikipedia series pages) → group "Excavations" (540 new places) and an
      "Excavated:" line on 864 buildings and places; tour theme "Archaeology & digs".
- [x] D2 Hoards (`bidb/hoards.py`): Wikipedia's lists of hoards in Great Britain and Ireland (102 with find-spots;
      78 new, 24 already Wikidata finds), linked to their museum.
- [ ] D3 Portable Antiquities Scheme / Treasure reports: public records give find-spots to 1 km or parish only, and
      finds.org.uk blocks scripts (Cloudflare check, 2026-10-21): needs a data request (user item, as N1).
- [ ] D4 Archaeology Data Service excavation index (England) and Canmore/Coflein events (licence check first).

## Museums, galleries and collections (planned 2026-10-21; after the war construction)
Places that keep interesting historical objects, and what they keep.
- [x] MU1 (2026-10-21: 4,414 places: museums by type, art galleries, libraries and archives, closed ones
      marked; 588 museums are catalogue buildings and stay there, without a museum note yet) Museums and galleries as a places group "Museums & collections": museums of every kind
      (national, local, regimental, open-air, historic-house, transport, science, folk), art galleries,
      libraries and archives with historic collections (record offices, cathedral and college
      libraries), treasuries and university collections (Wikidata classes with subclasses; opening and
      closing years). Museums that are already catalogue buildings (castles, houses) stay there and get
      a "Museum" note instead.
- [x] MU2 (2026-10-21: CC BY 4.0 confirmed, doi:10.18743/DATA.00171; 2,883 matched Wikidata museums, 566 catalogue
      buildings, 742 added, 122 of them closed; `bidb/mapping_museums.py`) Mapping Museums database (Birkbeck, ~4,000 UK museums open 1960–present, incl. closed ones,
      with type, governance, subject and accreditation; check licence, believed CC BY 4.0): merge with
      Wikidata by name and location; closed museums shown as such.
- [x] MU3 (2026-10-21: 916 objects in 253 museums; 67 finds link to their museum) "Kept here": notable objects held by each museum (Wikidata P195 collection / P276 location,
      e.g. Lewis chessmen, Sutton Hoo helmet, Book of Kells, Mappa Mundi), shown on its page; finds and
      hoards already in Places link to the museum that holds them ("Now kept at" → the museum record).
- [ ] MU4 (tour theme "Museums & galleries" done 2026-10-21; opening hours come from the visiting stage
      where OSM has them) Visiting: opening hours, fee and website from OSM (existing `visiting` stage), Art UK and
      collection-search links (link only); a "Museums & galleries" tour theme (town walks), stories.

## More sources (planned 2026-10-21)
Each item starts with a licence and access check (record the result here); copyrighted sources are
linked, never copied. Suggested order: S1, S2, S3, S4, then the rest.
- [x] S1 (2026-10-21, in part: "recorded in Domesday Book" on every record whose settlement or town has an
      OpenDomesday settlement ID on Wikidata, P3118, CC0; `bidb/domesday.py`. Open Domesday's API returns 404
      and its place pages need a grid reference, so households, mills and landholders are not shown: ask the
      maintainer for a data dump (user item)) Open Domesday (opendomesday.org, CC BY-SA, API): places in Domesday Book (1086) with
      households, mills, churches, landholders; "mentioned in Domesday" on towns and buildings.
- [x] S2 (2026-10-21, Wikidata part: artworks depicting a building or place, made before 1950, "Then" in detail
      views, `bidb/depictions.py`; Photochrom prints and Flickr Commons still to do) Historic images: paintings and prints of buildings via Wikidata "depicts" (P180; public
      domain on Commons), Library of Congress Photochrom prints (1890s colour views; public domain),
      Flickr Commons (e.g. National Library of Ireland Lawrence collection; no known restrictions);
      "Then" gallery in detail views.
- [ ] S3 Geograph API (CC BY-SA): photos for records still without one (more than the Commons copies).
- [ ] S4 (2026-10-22: each Canmore record carries LICENCE "Open Government Licence"; 314,401 terrestrial + 25,913
      maritime points at inspire.hes.scot CANMORE/Canmore_Points MapServer, FID paging; too large for the hosted copy
      as places, so local-only or as links) (checked 2026-10-21: Canmore's map index holds 320,000+ sites, downloadable from the HES portal or a WFS;
      the CKAN entries say "No Licence Provided", an older Canmore map service record says OGL; confirm with HES.
      At that size it needs a choice: all sites, or only those with a period/description not already in Places)
      Canmore (Scotland) and Coflein (Wales) site records: undesignated sites and descriptions
      (OGL via the official map services; check).
- [x] S5 (2026-10-22, `bidb/welsh_names.py`) Old forms of Welsh place names with dates on 4,824 records.
- [x] S6 (2026-10-22, `bidb/naptan.py`) NaPTAN bus stops and ferry terminals in "Getting there" (Great Britain).
- [ ] S7 OS Open data (Open Names, Open Rivers, Open Roads, Open Greenspace; OGL): checked 2026-10-22 (downloads API,
      no key; 40 MB–1 GB). The OSM layers already cover the same ground; only worth it for Greenspace if wanted.
- [ ] S8 Canal & River Trust open data: checked 2026-10-22: asset layers (1,722 locks, 6,915 bridges, 329 aqueducts,
      58 tunnels; OGL) have no construction dates; "Canals over time" (44 canals: opened, closed, restored) is for T3.
- [ ] S9 For war construction (X1–X3): IWM War Memorials Register, Defence of Britain (Archaeology
      Data Service), Commonwealth War Graves cemeteries.
- [ ] S10 For underground works (U1): TfL open data (stations, lines; free key) with Wikidata dates.
- [x] S11 (Canmore and the Irish inventory done 2026-10-22) For shipwrecks: Historic England / Canmore wreck records, Irish Wreck Inventory (not the
      licensed UKHO data).
- [ ] S12 People: links to the Dictionary of Irish Biography and Dictionary of Welsh Biography via
      Wikidata IDs (no copied text).
- [ ] S13 Link-only references on detail views: British History Online (VCH), Survey of London,
      Dictionary of Irish Architects, Art UK, Lost Heritage, Subterranea Britannica / Disused Stations,
      Megalithic Portal, Vision of Britain (short quotes only; non-commercial terms).
- [ ] S14 Ask (user item): local Historic Environment Records (Heritage Gateway), Church of England
      Church Heritage Record, National Trust / English Heritage / Cadw opening times.

## Going public (2026-10-21)
- [x] MIT licence for the code; `DATA_LICENSE.md` with every source's licence and credit, third-party
      code; `CONTRIBUTING.md`; `CITATION.cff`; screenshot credits in Help.
- [x] README rewritten for the current version with new figures (`docs/make_figures.mjs`, real browser:
      satellite, historic map, tours, setup, jobs).
- [x] Personal references trimmed; history squashed to one commit; topics added.
- [x] Nation for 31,287 places that had none (`bidb/nation_geo.py`: Wikidata P131, else location).
- [x] Hilliness: climb counts changes of 3 m or more; under 20 m in all is flat (short town walks
      were rated hilly from terrain-model noise).

## Nature, graves, markets, works and infrastructure (added 2026-10-22)
- [x] N1 "Nature & deep time" places group: the researched oldest natural things (trees, woods, rocks, fossils,
      early human traces, natural wonders); notable trees among them move here.
- [x] N2 "Graves & burial grounds" (`bidb/burials.py`): 7,900 cemeteries, churchyards, war cemeteries, tombs and chest
      tombs, mausolea and graves from Wikidata, plus the researched oldest graves; prehistoric burial monuments stay
      with archaeology.
- [x] N3 "Markets & trade" and "Infrastructure & utilities" (`bidb/trade_works.py`), and more "Industrial heritage":
      market halls, crosses, corn exchanges, shops, banks, inns, market towns (7,500); mills, factories, manufacturers,
      breweries, works, quarries, shipyards at any date (+4,100); roads, milestones, reservoirs, dams, weirs, sea walls,
      canals and locks, railway lines, signal boxes, power stations, airports (15,200).
- [x] N4 The Oldest page lists the researched oldest of each (with verdicts) and the earliest dated places of each
      kind in these groups (Wikidata dates, marked as unchecked).
- [x] N5 (2026-10-22, `bidb/oldest_checks.py`) Earliest dated places of the new groups: 8,937 of 23,120 Wikidata dates
      are only to the decade/century (now shown so, not candidates); 422 candidates reviewed with sources and quotes
      (283 kept, 92 corrected, 32 dropped, 15 open); finding: Wikidata's classes miss the oldest hospitals, universities,
      almshouses (St Bartholomew's, Oxford, St Cross) — the researched lists cover them.
- [ ] N6 Woodland Trust Ancient Tree Inventory (licence to be asked), Canmore for Scottish burial grounds.

## Sharing (added 2026-10-22)
- [x] S1 Share on the home network (`app/lan.py`, Settings › Share on my home network, `./run.sh --lan`): the server
      listens on every interface; other computers are read-only (any change, settings, screenshots, setup and saved
      street maps refused by the server; their pages hide those controls); addresses and a QR code in Settings; the
      app restarts itself on its new address.
- [x] S2 (2026-10-22) Share codes: a code for other devices (form or ?code=, cookie), a trusted code for full access.
- [x] S3 (2026-10-22) `./serve_dist.sh [--to HOST]` serves `dist/` here or copies it to another machine and serves it
      there (not started on the Mac mini: George's call).

## Time slider and change over time (added 2026-10-22, George's idea)
A slider over years on the Map page: what was built (and what had gone) by a chosen year, with networks and
historic maps of the period. Feasible now for dated things (catalogue, places with opening/closing years, railways,
canals, bridges, stations); the limits (only what survives or is recorded; founding date, not later growth;
built-up area and ordinary roads have no years in OSM) to be stated on the page.
- [x] T1 (2026-10-22, `static/time_slider.js`) Slider on the Map page: buildings and places with start year ≤ Y (and closing year > Y), counts histogram,
      play button; historic map layer switching with the era (Saxton/Speed → Roy → OS first edition → revisions).
- [ ] T2 Investigate more historic maps: county maps (Saxton, Speed, Morden, Greenwood, Bryant), Ogilby's road
      strips (1675), estate, enclosure and tithe maps (Tithe Survey c.1840: The Genealogist / county projects),
      Goad fire-insurance plans, OS 25-inch and later editions, Bartholomew half-inch editions, Irish Down Survey
      (1650s, TCD), Taylor and Skinner's roads of Ireland (1778), Roy Military Survey of Scotland (have), Blaeu atlas
      of Scotland (1654, NLS), British Library and Bodleian georeferenced collections; licence and tile access each.
- [ ] T3 Investigate dated network and change data for the slider:
      CAMPOP "Transport, urbanization and economic development in England and Wales c.1670–1911" (railways, canals,
      navigable rivers, turnpike roads with opening years; Cambridge Group, check licence); Martí-Henneberg / Cobb
      railway atlas data; Canal & River Trust "canals over time" (opened, closed, restored); Wikidata railway lines
      and stations with opening/closing dates; Disused Stations; turnpike trust acts; GB Historical GIS / A Vision
      of Britain through Time (parish and town populations 1801–2011, boundaries; licence); Irish census 1821–;
      Domesday (1086, have) and the 1377 poll tax / 1524 lay subsidy for medieval town sizes; Historic Towns Atlas
      and Atlas of Historic Towns (Ireland); GHSL / HYDE built-up area (1975–, and modelled earlier).
- [ ] T4 Investigate texts as sources of dates and change: Project Gutenberg and Internet Archive (county
      histories, Defoe's Tour 1724–27, Leland's Itinerary, Camden's Britannia, Cobbett's Rural Rides, Bradshaw's
      guides, Lewis's Topographical Dictionaries 1831–49, Groome's Ordnance Gazetteer of Scotland, Wilson's Imperial
      Gazetteer 1870–72), British History Online (VCH, Survey of London), Archaeology Data Service reports and
      journals (open access), county archaeological society transactions (often on Internet Archive / BHL),
      theses (EThOS/CORE), OpenAlex/CORE APIs for open papers; extract dated statements per place with quotes
      (as the evidence track does) and keep licences per text.

## People and environment through time (added 2026-10-22, George's idea)
Graphs and map layers of how people and the land changed together: population and settlements, the built
environment, farming, woodland and land cover, industry and energy, climate and the atmosphere, and the other
way round (geology, soils, coast, climate shocks, plague and famine shaping where and how people lived).
Each graph and layer can be switched on and off, follows the Map page's year slider (T1), and cites its data
source (and any analysis it repeats) with the licence. Only openly licensed data, or published figures quoted
with their citation; estimates for early periods are marked as modelled, with their uncertainty where given.
- [x] E1 Research the sources (2026-10-22, three research agents; ~90 candidate sources): per series and layer the
      publisher, citation, licence (+ quote), years, resolution, download URL (all HTTP 200 on 2026-10-22) →
      `data/curated/change/sources.json`. Left out for licence: Bank of England millennium dataset (Broadberry et al.
      population, GDP, wages), Wrigley–Schofield, de Vries, Armagh temperatures, SILSO sunspots, Shennan sea-level
      database, Broadberry land use, Warde energy, enclosure acts. Gaps: open urban share before 1950, real wages,
      enclosure, canal/railway length, iron, coal before 1853, Irish farming before 1926 (PDF only).
- [x] E2 (2026-10-22: 50 series, 32 cited events, `bidb/change_series.py`) Time series (national, England / Scotland / Wales / Ireland where possible): population (Domesday,
      1377 poll tax, Wrigley–Schofield 1541–1871, censuses 1801/1821–), share living in towns, numbers of towns
      and cities by size, GDP per head (Bank of England "A millennium of macroeconomic data"), life expectancy,
      buildings and places begun per decade (from this catalogue), coal output, CO₂ emissions; Central England
      temperature (1659–), England and Wales rainfall (1766–), CO₂ and methane (ice cores + Mauna Loa), sea
      level (Newlyn, etc.), volcanic and solar forcing, woodland cover, farmland and livestock, notable floods,
      droughts, famines, plagues and storms (dated events with sources).
- [x] E3 (2026-10-23: built-up land 1975/2020 (GHSL), land cover 2000–2018 (CORINE), pollen tree cover 9500 BC–1935 in 1° squares, ancient woodland, farmland grades (England), superficial deposits (GB), towns and cities by size 700–2000 as dots (Buringh), `bidb/change_rasters.py`; HYDE 3.3 to 2023 still needs a browser download. 2026-10-22: HYDE population density and cropland at 29 dates following the slider (132 KB of PNGs),
      bedrock geology by period for all the isles, coalfields; `bidb/change_layers.py`, `change_geology.py`.
      To do: GHSL built-up 1975/2020, CORINE 2000–2018, pollen tree-cover cells, ancient woodland, land grades,
      superficial geology, HYDE 3.3 to 2023 (browser download), Buringh/Reba city sizes as dots by date.
      Research done: HYDE 3.2 crops tested, 1,275 grids ≈ 25 MB gzipped, 4 key variables ≈ 6 MB; HYDE 3.3
      needs a browser download; GHSL 1975/2020, CORINE 2000–2018, KK10, pollen cells, BGS/GSI bedrock, coalfields,
      ALC prepared in the research scratchpad) Map layers by year (driven by the slider): HYDE gridded population, cropland, pasture and built-up
      area (10000 BC–today), GHSL built-up area (1975–), plus fixed layers that explain the pattern: bedrock and
      superficial geology (BGS), soils / agricultural land, coalfields, ancient woodland, land below sea level and
      lost coast; legend and source line on each.
- [x] E4 (2026-10-22: panel on the Map page + page `/change`) "Change over time" panel: stacked small graphs with a shared year axis and a marker at the slider's
      year; each toggled, with units, uncertainty bands, and a source link; also a page of its own with notes.
- [~] E6 (2026-10-23, George: "all the rest", with estimates for missing dates and models compared) More layers and
      estimates. Done: HYDE pasture/grazing and built-up area; people per km² 1975–2020 (GHS-POP); railway stations by
      opening year (Wikidata; closures recorded for only a tenth); graphs that put other models on the same axis, published
      estimates as dots with error bars (England 1086–1801, Scotland, Ireland before 1821, coal before 1853, the urban
      share, Irish woodland, markets and fairs; `estimates.json`), dotted gaps read as estimates; yearly temperature for
      each country and the globe (measured, a 1500–1900 reconstruction, and an estimate from CET). To do: decade climate
      maps (CRU TS; HadUK-Grid files now need a CEDA login), ice-sheet retreat and past coastlines (deep-time dates),
      night lights, forest change since 2000, Domesday 1086, census populations by county, railway lines with dates,
      1930s land use. Blocked for now: KK10 (PANGAEA bot check), HYDE 3.3 (browser download).
- [x] E5 (2026-10-23: 19 notes from the Neolithic boom and bust to the 1952 smog and rising seas, 50 quotes from published research, each with link and locator, both sides where scholars disagree; on the Change over time page and, for the slider's year, in the Map panel; `data/curated/change/notes.json`) Analysis notes (cited): what the series show together (e.g. building booms against population and
      prosperity, the Little Ice Age and harvest failures, the Black Death, enclosure, the coal age and CO₂),
      quoting published research rather than our own inference where it makes a causal claim.
