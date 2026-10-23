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

## Research track: original sources and evidence (R0–R8, 2026-10-21/22)
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
