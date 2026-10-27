# Building types: sources and licences (roadmap BT1)

`lineage.json` (houses and defence), `lineage_religious.json` and `lineage_agricultural.json` hold the types and
their sourced links (read together; links may cross files) (checked by `python -m bidb.building_types`, quotes
by `--quotes` → `data/building_types_check.json`). The hierarchy of types and their definitions come from the
FISH Thesaurus of Monument Types (`bidb/fish_types.py`); the links between types are not in any thesaurus and
each cites its sources with an exact quote.

## Licence check (2026-10-25)

| Source | Licence | How used |
|---|---|---|
| FISH Thesaurus of Monument Types v29 (Historic England, 24 April 2026; CSV zip from heritage-standards.org.uk) | Open Government Licence v3.0: the scheme's RDF at heritagedata.org states `cc:license https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/`, `cc:attributionName Historic England` | Backbone: 5,105 preferred terms, 3,192 non-preferred, 18 top concepts (17 function classes and MONUMENT <BY FORM>), 848 terms under more than one broader term; scope notes quoted as definitions. Wikidata P14369 links 172 classes to it (as of 2026-10-25). |
| FISH Building Materials and Components (same release, cached) | OGL v3.0 (same publisher and site) | For BT3 (materials and techniques). |
| Getty Art & Architecture Thesaurus | Open Data Commons Attribution 1.0 ("All Getty Vocabulary data is free to use under the terms of the Open Data Commons Attribution License (ODC-By) 1.0") | Terms beyond the isles (BT2 if needed); Wikidata P1014 links ~32,800 classes. |
| Wikipedia (English) | CC BY-SA 4.0 | Short exact quotes as the cited source of a link (each article cites the books: Brunskill, Pevsner, King and Alcock, Summerson...). |
| Historic England publications (Introductions to Heritage Assets, listing selection guides) | Not stated as OGL; historicengland.org.uk answers scripts with 403 | Cite by title and page with a short quote; checks marked unreachable. |
| Suffolk Heritage Explorer (and other HERs) | © the county council; read on line | Short quotes for single buildings (e.g. a chimney inserted into a cross passage). |
| Brunskill, Pevsner, Summerson and other books | © their authors and publishers | Cited with page and short quote only; not copied. |

## Coverage found

- Catalogue classes (Wikidata P31 labels in `buildings.classes`) matched to a FISH term by label alone: 18,638 of
  27,400 uses (68.0%). The rest are mostly synonyms or Wikidata-only classes ("built structure" 2,249, "terrace
  house" 1,019, "archaeological site" 581, "English country house" 530, "historic house museum" 389): BT2 needs an
  alias table. Bare words can match a non-preferred term of an unrelated concept ("hall" is a non-preferred term of
  Church hall), so BT2 should prefer full labels.
- Not in FISH: prodigy house, blackhouse, Device Fort (FISH: artillery castle, 1481-1561), polygonal fort, Scottish
  baronial (a style), Irish ringfort (FISH has the Cornish "round").

## First families (BT1b)

Houses (round houses, longhouses, hall houses, chimneyed houses, manor and country houses) and defence (castles,
fortified houses and towers, artillery fortification): 33 types (5 of them "abroad", the source of an influence),
29 links (descent 11, variant 7, influence 6, replacement 3, convergence 1, revival 1; documented 21, probable 5,
disputed 3), 76 quotes, all found in their sources. Disputed: the Cornish rounds and the Severnside shell keeps,
crusader castles and the concentric plan, the Irish tower house from the hall house (Finan) or from Scotland.
Probable, stated as such: the lobby-entry house from the hall house with a chimney inserted by the cross passage
(single buildings described, no general account found), the double pile replacing it (a Cumbrian source).

## Religious and farm buildings (BT1c1, 2026-10-25)

`lineage_religious.json`: 20 types (the Roman basilica, churches, religious houses, early Christian Ireland,
nonconformist meeting houses; one abroad: the reformed Benedictine houses of the Continent), 17 links.
`lineage_agricultural.json`: 12 types (barns, gin gang, oast house, dovecote, laithe house; one abroad: the Roman
columbarium), 11 links, two of them from the house and castle families (longhouse → laithe house, tower keep →
dovecote). All 65 types and 57 links: 170 quotes, all found. Disputed: the minster hypothesis (Blair; Cambridge
and Rollason), a Roman or Norman start for dovecotes. Probable, stated as such: Gallarus from the clochán ("may
derive"), dovecotes after castle nest-holes (the order is sourced, the descent is not), the laithe house and the
Irish round tower as convergences (no source links their origins). Not in FISH: clochán, corbelled oratory, Irish
round tower, Commissioners' church, the ecclesiological church. Wikipedia's lists of listed buildings hold their
descriptions in tables that the plain-text extract leaves out, so they cannot be quoted for a check.

## Commercial, industrial and transport (BT1c2, 2026-10-25)

`lineage_commercial.json`: 24 types (inns and public houses, markets and exchanges, shops and banks; abroad: the
Antwerp bourse, the covered passages of Paris), 18 links. `lineage_industrial.json`: 22 types (watermills,
windmills, textile mills, iron making, kilns; abroad: Roman watermills, Persian horizontal windmills, the Piedmont
silk-throwing mills, the Walloon blast furnace), 16 links. `lineage_transport.json`: 17 types (bridges, turnpikes,
waterways, railways; abroad: Roman aqueducts), 12 links; railway station → railway hotel crosses into the
commercial file. All 128 types and 103 links: 305 quotes, all found; every Wikipedia locator checked against the
section the quote stands in. Disputed: whether the vertical windmill borrowed from the Persian horizontal one
("unclear"), whether the shopping arcade came from Paris (Palais-Royal 1784) or was as early here (Oxford's Covered
Market 1774, Burlington Arcade 1819). Probable, stated as such: the alehouse taking the Roman tavern's place (no
continuity shown), coaching inn → railway hotel (each half sourced, the replacement not stated), market house →
market hall (order from FISH's dates), shop → bank (the goldsmith bankers' business, not the building), stepping
stones → clapper bridge (form and word), river navigation → canal (the Sankey Brook Navigation, one case).
FISH notes: its TUNNEL KILN is a coal-fired lime kiln, so the pottery industry's gas tunnel kiln has no FISH id;
the buttercross is a non-preferred term of MARKET CROSS; not in FISH: cast-iron bridge, the Roman taberna.

## Civic, education, health and welfare, recreational (BT1c3a, 2026-10-25)

Researched in parallel, one file per domain, each reviewed before it was kept:
`lineage_civic.json` 23 types (2 abroad: the town halls of the Continent, Eastern State Penitentiary), 19 links;
`lineage_education.json` 23 types (2 abroad: the Madras pial schools, Paris and Bologna), 18 links;
`lineage_health.json` 25 types (3 abroad: the Hôpital Lariboisière, Les Invalides, Brehmer's sanatorium), 23 links;
`lineage_recreation.json` 25 types (1 abroad: the Italian court theatre), 20 links. 288 more quotes.
All 224 types and 183 links: documented 138, probable 28, disputed 17.
Disputed: whether guildhalls began as guild halls (FISH) or as the town's hall (Wikipedia); whether Millbank followed
Bentham's panopticon, and whether the panopticon shaped the radial prisons ("was not … a panopticon"); Leach's
chantry-school thesis; the college quadrangle from the cloister (Mob Quad plain, without arcades); the monastic or
leper-house origin of the medieval hospital (Gordon); the first cottage hospital (Cranleigh 1859 or earlier
dispensaries with beds); the first sanatorium (Brehmer or Bodington, 1836); the inn-yard theory of the playhouse;
Perran Round as a reused Iron Age round or built as a plen-an-gwary (Jenner).
Probable, stated as such: shire hall → county hall, watch house → police station, fire engine house → fire station,
prison hulk → separate-system prison, house of correction and gaol (convergence); Bethlem's galleries → the corridor
asylum, Lariboisière → the pavilion plan in Britain, the Scottish poorhouse and the union workhouse (convergence),
Bart's and St Thomas's → the voluntary hospitals; the bear garden and Roman amphitheatre → the playhouse,
Restoration → Georgian playhouse, grandstand → football ground (influence only: a grandstand is one side of a ground).
Changed on review: chained library → public library is influence ("forerunner"), not descent.
Not in FISH (own sources): tolbooth, tholsel, panopticon, separate-system prison, cathedral and chantry schools,
academic hall, red-brick university, chained and Carnegie libraries, pavilion hospital, echelon-plan asylum, parish
workhouse, Irish workhouse, Scottish poorhouse, the playhouse types (FISH has only THEATRE), song-and-supper room.
Left for later: charity, dame and Sunday schools, hedge schools → Irish national schools (sourced; FISH's "national
school" is the English National Society's), plate-glass universities, custom houses, assize courts, houses of
industry, the York Retreat, Turkish baths, the lido.

## Periods of use, structure and plan form (BT1c3b, 2026-10-26)

Every one of the 224 types has `period`: `text` (what the years are and how sure), `from` (first known example;
for types abroad, in their own country; BC negative), `flourish` [from, to] where sources say when most were built
(68 types), and `to` (last built, 170) or `ongoing: true` (still built, 54). `structure` (66) and `plan` (100) only
where a source states them for the type, not a single building. Each is backed by a source marked
`"about": ["period" | "structure" | "plan"]`; `python -m bidb.building_types` checks this (`period_problems`) and
`--file lineage_x.json [--quotes PATH]` checks one file. 850 quotes added: 1,443 of 1,443 found.

What the years are: many "to" years are the latest example a source names (railway hotel 1937, pleasure pier 1957,
aisled barn 1771), or the end of use or a law (alehouse 1869, voluntary and fever hospitals 1948, union workhouse
1930, moot 1747), not a known last building; the text says which. Approximate years ("c.", "by the 13th century")
are said so. Disagreements are given in the text: cottage hospital (first 1818, 1827, 1842 or 1859), sanatorium
(Bodington 1836 or Brehmer 1854), echelon asylum (Coney Hill 1883 or Claybury 1893), lobby-entry house (16th or
late 17th century), oast house (17th century or 1750 at Golford). Left out because the checker cannot read them:
Historic England pages (refuse scripts), Canmore, a 2015 Hampshire PDF dating a Winchester Wealden house to 1340,
Asylum Projects (Cloudflare). Weakest: the clochán's end (corbelling into the 1950s, not clocháns as such), the
Persian windmill's (no source), the dispensary as ongoing (FISH's room for medicines in a hospital).

## Records and places mapped to the types (BT2a, 2026-10-26)

`aliases.json`, read by `bidb/type_map.py` (`python -m bidb.type_map [--report]`, also a build stage after the
place stages) → table `type_map`. A record's Wikidata classes are tried in order: the class names a type; a
curated alias (Wikidata labels FISH lacks: "English country house", "London Underground station"); its FISH
concept is a type's; the nearest broader FISH concept that is a type's. The most specific type found stays
(motte-and-bailey, not castle as well). 21 types carry a FISH concept wider than themselves (THEATRE for the
Georgian playhouse, HOSPITAL for the medieval hospital, WORKHOUSE for the union workhouse): `within_period` lets
FISH find them only for records begun within their period of use, so a theatre of 1900 is not a Georgian
playhouse. `nations` limits the Scottish and Irish types. A record no class types may match a name rule on the
head of its name (before the first comma: "Gate Piers, Baldoon Castle" is not a castle), within listed
categories, or its category (Cathedral, Hotel); these, and places typed by kind, need a start year within a
century of the type's period when the year is known (the Iron Age "Clinch Castle" stays untyped). Places: their
own type label (register types split at " - ": "Castle - tower house"), name rules for their kind, or the kind
(banks, market crosses, police stations); `skip_kinds` (objects, plaques, finds, events, clubs, firms) are never
typed.

Result: 10,805 of 22,508 catalogue records (48.0%) and 27,401 places typed, to 123 of the 203 types in the isles.
How: FISH concept 6,193, type name 2,849, alias 1,275, name rule 340, broader concept 113, category 35. The rest
were reviewed (`not_in_tree`, 438 labels): too general ("built structure" 2,170, "building" 1,302, "house" 828) or
kinds the tree does not have yet: town houses (terrace house 1,006, tenement, townhouse, mews, cottage, villa),
prehistoric and Roman monuments (hillforts and forts about 1,000, barrows, stone circles, standing stones, cairns,
Roman villas), chapels (161), gatehouses (185), stables and carriage houses, lighthouses, friaries, palaces,
museums, and the general windmill, school, hospital and prison. 80 types have no example yet: mostly narrow types
(Wealden house, lobby-entry house, the asylum and school variants, the playhouses) that Wikidata does not class;
BT2b looks for them by name and description.

## Per type: counts, examples and the earliest surviving example (BT2b, 2026-10-26)

`bidb/type_stats.py` (`python -m bidb.type_stats [--report] [--type ID]`; `/api/types`, `/api/type/<id>`,
`/api/types_of/<id>`) reads table `type_map`: per type the records and places, dated examples oldest first, counts
by nation and century, map points, and the earliest surviving example: the earliest dated example of which the type
is the primary one (a castle later used as a town hall is no early town hall), catalogue records before places,
not demolished, not dated by an estimate from its building type, and not "too early".

**The 80 types with no example.** `aliases.json` `texts` (75 rules, each reviewed match by match): patterns on the
name, short description and first two sentences of the Wikipedia extract ("is a 16th-century Device Fort", "a
Wealden hall house", "tower keep castle", "Palmerston fort", "chapel of ease to", "round-tower church"), for records
none of whose classes finds a type or whose type the rule `refines` (castle → tower keep, barn → aisled barn);
limited to categories, and to listed kinds for places, because loose rules matched railway stations ("Bath Spa"),
locks on a navigation, brickworks, moated sites at "Brick Kiln Farm", holy wells with corbelled roofs and buildings
on Royal Exchange Square. Register type labels are now split at ";" and ":" as well as " - " ("Prehistoric
domestic and defensive: hut circle, roundhouse"), and five labels aliased (hut circles → roundhouse, "meeting place,
thingstead, moot hill" → moot, Device and Palmerston forts). Result: 174 of the 203 isles types have examples (was
123), 10,812 records and 28,528 places typed; text rules type 68 records and 703 places.
Rules tried and dropped: "university college" (UCL 1826, Durham 1832 and modern colleges are not the civic
university colleges of 1851-1949), "great tower" (college and manor towers), "pump room" for spas (the Bath
colonnades are parts of a pump room). Still with no example (29): round, lobby-entry house, bank barn, hay barn,
laithe house, Victorian town hall, prison hulk, panopticon, Roman taberna, alehouse, drovers' inn, ragged school,
Scottish parish school, academic hall, university college, pavilion hospital, echelon asylum, Scottish poorhouse,
bottle kiln, gas tunnel kiln, inn-yard theatre, cockpit, indoor, Restoration playhouses, song-and-supper room, Roman
basilica, Commissioners' church, ship's chain cable, flash lock: searched by name and description, and found only on
plaques (ragged schools, a bottle kiln, Commissioners' churches), as place names (Laithe, Cockpit) or as a vanished
building's site.

**Found in review and fixed (BT2a errors).** The `nations` limits named "Ireland", but the database says "Republic of
Ireland", so the tholsel and the Irish union workhouse never matched in the state (`problems` now checks nation
names); the "...Station" name rule typed 24 lifeboat, power, radar and fire stations as railway stations.

**Too early.** 521 examples (of about 39,000 typed records and places) begin more than a century before their type's first known date; they are
listed by `--report`, flagged in `/api/type/<id>` and never the earliest example. Reviewed: mostly an older building
in a later use (medieval inns now pubs and hotels, 63 and 40; theatres and a market hall now cinemas; medieval
houses now country houses or farmhouses, 187 and 40, often dated by the first building on the site), the site's
earliest phase (priories and parish churches on early minster sites, Roman forts under Pevensey and Cardiff
castles), coarse register periods (brochs dated "Iron Age" from 400 BC, 31) and wrong classes (hillforts classed
as castles on Wikidata: Caerau, Twmbarlwm, Castell Dinas Brân). No reviewed example was right and kept, so
`early_ok` is empty. Found on the way: Irish SMR tower houses in townlands named Rath... or ...cashel are dated
600, the year an early medieval ringfort or cashel would get (fixed: the type estimate read "Rath" in the townland).

## More types: prehistoric and Roman, houses, estate, settlement, general types (BT1d, 2026-10-26)

Five research agents in parallel, one new file each, every file reviewed here; 87 types, 126 links, 680 quotes (all
found; 2,123 in all). George's decision: structures people built and used join the tree (tombs, ceremonial
monuments, hillforts, Roman forts, villas, temples, town walls); single standing stones, rock art, carved stones and
finds stay in the archaeology groups.
- `lineage_prehistoric.json` (24 types, 30 links): chambered tomb with long barrow, passage, portal, court (court
  cairn and Clyde tomb are one type) and wedge tombs; round barrow (bowl, bell, disc as one), round cairn; cursus,
  henge, stone circle; hillfort, promontory fort, dun, ringfort, cashel, crannog, souterrain, fogou; Roman fort,
  Saxon Shore fort, Roman villa, Romano-Celtic temple, Roman town wall. Disputed: henge and stone circle (a regional
  form of henge, or distinct). Probable: hillfort → castle and Romano-Celtic temple → church (sites reused, not the
  design), Roman villa → country house (revival through Palladio, not from Roman Britain).
- `lineage_houses.json` (17, 22): medieval town house, terraced house, by-law terrace, back-to-back, tenement,
  aristocratic townhouse, mews, cottage, estate cottage, Palladian villa (abroad), villa, semi-detached house,
  clergy house, manse, royal and bishop's palaces, dower house. FISH lacks the Scottish tenement and the cottage.
- `lineage_estate.json` (19, 16): gatehouse with castle, monastic and Tudor gatehouses and the gatehouse keep; gate
  lodge, stable, coach house, orangery (and the Continental orangery), glasshouse, conservatory, palm house,
  landscape park, folly, ice house (Italian ice stores abroad), mausoleum (classical mausolea abroad).
- `lineage_settlement.json` (19, 21): chapel, nonconformist and Methodist chapels, friary and Augustinian friary,
  town wall and gate, Pharos of Alexandria (abroad), Roman lighthouse, lighthouse, offshore lighthouse, warehouse,
  dock warehouse, factory, distillery, grain distillery, cabinet of curiosities, museum, municipal museum. Changed
  on review: municipal museum → public library is influence (probable), not convergence.
- `lineage_general.json` (8, 37): windmill, mill, school, hospital, prison, theatre, bridge, pier: the parents of
  the specific types (variant links, documented where FISH files the form under the general concept), for
  catalogue classes that name only the family. Hospital and theatre share their FISH concept with the medieval
  hospital and the Georgian playhouse; `type_map` gives the concept to the period-limited type when the year fits.

Weak, stated in each period's text: ends that are a reign, a law or the latest example named (palm house 1901,
gate lodge and coach house "early 20th century", Roman lighthouse 410); "ongoing" palaces are still used, not
still built; the mausoleum dates from Castle Howard (1729, "first free-standing" since Rome), though earlier
church-attached mausolea are in the catalogue (De Grey 1614). Left out: walled garden, summerhouse, garden temple,
lighthouse keeper's house, council house, a general house type, tower (Wikidata's class too mixed), fort.

**Mapping (BT2).** `type_map` now lets a general type give way to its forms (variant links), lets text and name
rules refine a general type or a use, ranks uses (`secondary`: museum, school, hospital, theatre, prison) after the
building's own type (Balmoral a country house, Arnol a blackhouse), and maps a shared FISH concept to several types.
19 class aliases (terrace house, thatched cottage, castrum, court cairn, Clyde tomb, the hillfort forms, school,
hospital, theatre, museum and mill buildings...), `roman-villa` in `within_period` (FISH Villa covers Georgian
villas), 12 text rules (castle and monastic gatehouses, gate lodges, Methodist chapels, palm houses, fogous, Saxon
Shore forts, rock lighthouses, Roman town walls, back-to-backs, merchants' houses, dock warehouses; gatehouse and
lighthouse rules on the name only, reviewed match by match). Result: 15,713 of 22,508 records (69.8%, was 48.0%)
and 58,753 places (was 28,528) typed; 247 of 285 isles types with examples, 220 with an earliest surviving example.
357 records changed primary type at first: general types beating specific ones (grammar school → school, 90) were
regressions and are fixed; 192 changes remain, mostly right (26 hillforts classed as castles on Wikidata, 23
friaries, promontory forts) or Wikidata's own errors (Dryslwyn Castle classed a contour fort; the Royal Academy of
Music a "conservatory"). Too early: 813 (was 504), reviewed by type: the site's earlier phase (Neolithic
enclosures under hillforts, long barrows beside round barrows), coarse register periods (Scottish duns "Prehistoric",
2000 BC), museums in old buildings; none kept. Still with no example (38): the earlier 29 less those now found, and
Tudor gatehouse, gatehouse keep, by-law terrace, semi-detached house, grain distillery, municipal museum, cabinet of
curiosities, Roman lighthouse: narrow types Wikidata does not class.

## Materials and techniques (BT3a, 2026-10-26)

`materials_stone.json` (stone, mortar and render: 22), `materials_earth_timber.json` (earth, timber: 18),
`materials_brick.json` (brick and tile: 20), `materials_roofs.json` (coverings and roof structures: 19),
`materials_modern.json` (glass, iron and steel, concrete, cements: 20), checked by `python -m bidb.building_materials`
(quotes by `--quotes` → `data/building_materials_check.json`). 99 materials and techniques, 51 links (documented 39,
probable 11, disputed 1: did the brick tax drive builders to mathematical tiles, or were the tiles older and taxed
too?), 978 quotes, all found. 73 carry a FISH concept from the Building Materials (`eh_tbm`) or Components
(`eh_com`) thesaurus, same release and licence (OGL v3.0, stated on each scheme's pages at heritagedata.org).
151 named examples, Wikidata ids checked against the catalogue (one corrected: the chapel of St Nicholas at
Coggeshall, not the abbey).

What the years mean is written in each period's text. Many first dates are the earliest a source names, or a
stand-in for a period ("43 stands for Roman"); where the use is surely older the period carries `earlier: true`
(queen-post roof 1753, wooden shingles 1400, straw thatch 1500, weatherboarding 1600, gritstone 1804, stucco 1811),
so charts should not draw them as beginnings. Disagreements are in the texts and notes: the age of Purbeck marble
(Cretaceous, Wikipedia; filed under the Jurassic Portland stone by FISH) and of Caen stone, when brick-making
revived (12th or 13th century), cavity walls (rare 18th-century examples or a 19th-century reintroduction),
Ditherington (1795 or 1797), Ravenhead (1773 or 1786), who made "true" Portland cement, cruck origins and their
absence in the east (two carpentry traditions or coppicing).

Reviewed here: two links defined in two files merged (timber framing → brick, lime mortar → Portland cement);
lead → Lake District slate dropped (one building, Westminster Hall, not a general change).
Left out for want of a dated source: copper roofs, mansard, tie-beam and common-rafter roofs, heather, marram
and rope thatch, Valentia slate as its own entry, wychert, the sub-forms of crucks, English garden wall bond,
London stock brick, limewash, cobble walling, Cornish and Welsh granite; brutalism is a style, not a material.

## Records and places linked to materials (BT3b, 2026-10-26)

`material_aliases.json`, read by `bidb.material_map` (build stage "Materials", after the stories stage, whose
article cache it reads) → table `material_map`, summed by `bidb.material_stats`. Three sources per record or place:
Wikidata P186 (5,357 isles items with coordinates have one, mostly statues; 59 material items mapped, 41 reviewed
and left out in `not_in_list`: generic stone, sandstone, limestone, granite, marble, wood, concrete, roof tile, lead,
bronze), the cached register descriptions (HES whole, 6,133 records; Cadw Period and History only, 226; NIAH notes,
107) and the cached Wikipedia article (25,672 titles; else the extract). Text is read sentence by sentence by 95
term rules: the term itself, a building word near it where the term alone is ambiguous (`cue`: "brick" near built,
walls, roof, church...), words that drop it nearby (fonts, tombs, statues, gates, balusters, kilns, quarries, bells,
"unlike"), sections skipped by heading (Churchyard, Geology, Location, Monuments, Collections...) and register
sentences about boundary walls, gatepiers and gardens. The matching sentence is kept as evidence.

First run reviewed five samples per material and source (829 lines): fixed rubble as debris, jetties at docks,
post-holes of fences, cruck barns in museums, interior fittings (cast-iron balusters and ranges, Memel pine
panelling, a Reader's Chair of oak), the plate glass universities, "of mud and silt", "square panel" in register
elevations, signal box frames, towns (burhs) and registered parks whose articles describe the buildings in them
(those kinds left out). A random sample of 30 Wikipedia links after the fixes: about 28 right.

Result: 8,477 of 22,508 records (37.7%; register 15,571 links, Wikipedia 5,818, Wikidata 207) and 2,352 places
linked, 24,957 links to 92 of the 99 materials (none for machine-made, colliery and clay-lump brick, window,
cylinder and float glass, Kilkenny marble). Most common: sash windows 3,848, ashlar 3,467, rubble 3,150, slate 2,668,
brick 2,522, plate glass 1,795 (HES glazing), harling 896. A text names the materials of every phase, so 901 links
whose building was begun over a century before the material's first date are flagged "too early" (sash windows in
tower houses, brick repairs to Norman churches); the earliest example of a material is the earliest standing,
non-estimated record begun in or after its first date (90 materials have one). Some earliest examples show catalogue
dating errors instead (Waterloo Bridge 748, Liverpool Street station 600, Battersea Power Station 400, an NIAH house
"c. 188"): an emergent task in the roadmap.

## Tramways, funiculars, inclines and signal boxes (BT1d, 2026-10-26)

Six types added to `lineage_transport.json` (47 quotes, all found; 2,179 in all), from Wikipedia and the FISH scope
notes: plateway (L-section cast-iron plates, Curr c. 1787 to about 1830; the Welsh tramroads), street tramway
(Birkenhead 1860; the last city system, Glasgow, closed 1962; revival from Manchester Metrolink 1992), funicular or
cliff railway (one type with FISH 92051: the thesaurus keeps CLIFF RAILWAY apart, but most British funiculars are
cliff railways; Scarborough 1875), railway inclined plane (Peak Forest Tramway 1796; Bowes Railway's last inclines
closed 1974), canal inclined plane (Dukart's Canal, Tyrone, 1777; Foxton 1900 the last built) and signal box (London
& Croydon Railway 1843). Links: wagonway → plateway (descent) → railway (replacement), wagonway ⇢ street tramway
(influence, probable: the name and the mineral lines), railway → funicular (variant), railway incline ⇢ funicular
(influence, probable), pound lock → canal incline (replacement, probable: Foxton was planned to replace its locks),
railway ⇢ signal box (influence). `aliases.json`: text rules ahead of the railway rule (signal box on the name or
short description; funicular, cliff railway, cliff lift, inclinator, cable tramway; inclines, with canal inclines
told apart by canal or lock words; electric, horse or street tramways; plateway, plate rail, tramroad), Cadw's
"Tramroad" and "Incline" labels, and a staircase-lock rule that overrides Wikidata's "canal inclined plane" class on
Bingley Five Rise Locks. The wagonway name rule no longer takes tramroads. Result: 434 places typed or retyped (370
signal boxes, 22 funiculars, 20 plateways, 18 inclines, 3 street tramways); records 15,717, places 59,375; 253 of 291
isles types with examples.
