# ROADMAP

Future work for British Isles Oldest Buildings, kept between sessions. Newest decisions first in
each section; tick items off (and move them to SESSION_LOG.md) when done.

## Status (2026-10-20)
- Catalogue 22,046 records (pre-1500 buildings, oldest of each type, landmarks of any date);
  77,729 places of interest (incl. 19,362 Open Plaques); 11,927 people. Download cache on an
  external drive (Settings → Data location); database on the internal drive.
  Hosted copy republished 2026-10-21 (version 26: legends, maritime, industrial, Victorian, new map
  layers; tiles packed per layer, floor plans as WebP; 248 files, 243 MB). Before that version 20 (stories, tours, minor roads and streams, lazy
  loading; 393 files, 233 MB, five publishes; files no longer exported are removed with null); republish changed files only (compare checksums of `dist/` before and after the export). Local GUI on port 5050; hosted copy at
  https://claude.ai/artifact/4H8rfcGGxSJki91SrNFTPv (private; republish with
  `python -m app.static_export` then the Artifact tool, in batches under 64 MB).
- Offline map (`app/basemap_build.py`): counties, roads, rail, rivers, parks, towns, landscape names,
  airports; Map page; building outlines and floor plans; references and date checks per record;
  research files checked against their sources (`python -m bidb.verify_research`).

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
- [ ] Major streams at high zoom.
- [x] National Trails (OSM `route=hiking network=nwn`) as an optional layer, 2026-10-20.
- [ ] Historic county boundaries (pre-1974) as an alternative to modern council areas
      (e.g. Historic County Borders Project, check licence).
- [ ] Offline map detail stops around zoom 13; consider vector tiles (PMTiles, protomaps) for
      street-level offline detail if the hosted size budget allows.
- [x] Parks queried by `designation=*` too: Eryri, the Broads, Llŷn, Anglesey, NI AONBs added.
- [ ] Most Scottish National Scenic Areas are not mapped in OSM; use the NatureScot NSA
      dataset (OGL) if wanted.

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
- [ ] OS Old Series at full detail via Allmaps (`allmaps.xyz/{z}/{x}/{y}.png?url=` NLS
      old-series.json annotation; ~5 s per tile, opt-in).
- [ ] Ireland six-inch by county (NLS `os/<county>`, `_2nd`; 32 layers grouped, bounds from
      metadata.json). Edition dates to confirm in the NLS viewer.
- [ ] Pre-warp Saxton (1579, CC0) and Speed (1611) national maps with GDAL (gdal_translate GCPs →
      gdalwarp -t_srs EPSG:3857 -tps) for the hosted copy; starter GCPs in the research notes.
- [x] "Historic maps of this place" on detail views (`app/historic_allmaps.py`, 4,436 maps).
      The bulk file has no titles; NLS maps link to the library record. Titles would need one
      IIIF manifest request per map.
- [x] William Smith geological map 1815 (Warper 150), bundled z5–8.
- [ ] Northern Ireland historic six-inch (OSNI OpenData, OGL): ~400 MB zips per county; crop and
      tile if wanted.
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
- [ ] Hosted copy: opening a detail view loads all places (50 MB) for the "related" panel; a small
      places location index would avoid that.
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
- [ ] Tours: elevation and surface for bike rides (as in cycle_routes), opening times / ticketed
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
- [ ] Ship launches and shipwrecks (Wikidata ships built at isles yards; wreck sites, licence check
      for the UKHO / Historic England wreck data).
- [ ] Victorian listed buildings beyond Wikidata (Historic England / HES / Cadw registers by date).

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
- [ ] S4 (checked 2026-10-21: Canmore's map index holds 320,000+ sites, downloadable from the HES portal or a WFS;
      the CKAN entries say "No Licence Provided", an older Canmore map service record says OGL; confirm with HES.
      At that size it needs a choice: all sites, or only those with a period/description not already in Places)
      Canmore (Scotland) and Coflein (Wales) site records: undesignated sites and descriptions
      (OGL via the official map services; check).
- [ ] S5 List of Historic Place Names of Wales (OGL): old name forms with dates, for pronunciation and history.
- [ ] S6 NaPTAN (OGL): bus stops and ferry terminals for "Getting there".
- [ ] S7 OS Open data (Open Names, Open Rivers, Open Roads, Open Greenspace; OGL): offline map layers.
- [ ] S8 Canal & River Trust open data: locks, bridges, aqueducts, tunnels with dates (industrial, U2).
- [ ] S9 For war construction (X1–X3): IWM War Memorials Register, Defence of Britain (Archaeology
      Data Service), Commonwealth War Graves cemeteries.
- [ ] S10 For underground works (U1): TfL open data (stations, lines; free key) with Wikidata dates.
- [ ] S11 For shipwrecks: Historic England / Canmore wreck records, Irish Wreck Inventory (not the
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
