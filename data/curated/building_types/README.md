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
