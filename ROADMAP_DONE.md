# ROADMAP — finished sections

Sections of [`ROADMAP.md`](ROADMAP.md) whose items are all done, kept for reference.

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

## Going public (2026-10-21)
- [x] MIT licence for the code; `DATA_LICENSE.md` with every source's licence and credit, third-party
      code; `CONTRIBUTING.md`; `CITATION.cff`; screenshot credits in Help.
- [x] README rewritten for the current version with new figures (`docs/make_figures.mjs`, real browser:
      satellite, historic map, tours, setup, jobs).
- [x] Personal references trimmed; history squashed to one commit; topics added.
- [x] Nation for 31,287 places that had none (`bidb/nation_geo.py`: Wikidata P131, else location).
- [x] Hilliness: climb counts changes of 3 m or more; under 20 m in all is flat (short town walks
      were rated hilly from terrain-model noise).

## Sharing (added 2026-10-22)
- [x] S1 Share on the home network (`app/lan.py`, Settings › Share on my home network, `./run.sh --lan`): the server
      listens on every interface; other computers are read-only (any change, settings, screenshots, setup and saved
      street maps refused by the server; their pages hide those controls); addresses and a QR code in Settings; the
      app restarts itself on its new address.
- [x] S2 (2026-10-22) Share codes: a code for other devices (form or ?code=, cookie), a trusted code for full access.
- [x] S3 (2026-10-22) `./serve_dist.sh [--to HOST]` serves `dist/` here or copies it to another machine and serves it
      there (not started on the Mac mini: George's call).

