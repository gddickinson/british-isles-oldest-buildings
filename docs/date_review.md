# Date review (2026-10-20)

The date check compares each record's date with independent evidence (the Wikipedia introduction, a
second source recorded in the date, or a referenced Wikidata date). On 2026-10-20 the 451 conflicts
were reviewed:

- **Checker noise removed** (≈300): years that were measurements ("693-acre", "487.7 ft"), sentences
  about fittings, saints, finds, collections, later houses on the site, styles, commemorations, and
  later dates for additions; ordinal parsing fixed ("thirty-seventh century", "17th-century").
- **Earlier origin** (67): the source dates the founding or the site earlier than the present
  building. Shown as its own status, not as a conflict.
- **Corrected** (56): the record's own Wikipedia introduction states another date for the building or
  its surviving fabric. Kept in `data/curated/date_corrections.json` with the sentence and source;
  date basis "Corrected (reviewed)", check status "Reviewed". Applied by the build, or
  `python -m bidb.date_corrections` on an existing database.
- **Remaining conflicts** (69): genuine disagreements between sources, listed below.

## Dates to fix at source

The previous date (mostly Wikidata *inception*, P571; for Jarlshof a Wikipedia list) was a modern event
(opening, listing, refurbishment) or far from what the record's own article states. Worth correcting
on Wikidata so other users benefit:

| Item | Building | Previous date | Article states |
|---|---|---|---|
| [Q5000477](https://www.wikidata.org/wiki/Q5000477) | Burrough Hill | 500 | early Iron Age |
| [Q5184822](https://www.wikidata.org/wiki/Q5184822) | Crewe Hall | 2026 | 1615–36 |
| [Q5313796](https://www.wikidata.org/wiki/Q5313796) | Dumfries House | 2008 | 1750s |
| [Q233579](https://www.wikidata.org/wiki/Q233579) | Dunadd | 501 | Iron Age |
| [Q5579300](https://www.wikidata.org/wiki/Q5579300) | Golden Cross | 1987 | 15th century |
| [Q1683532](https://www.wikidata.org/wiki/Q1683532) | Jarlshof | -200 | c. 2500 BC (earliest remains) |
| [Q764804](https://www.wikidata.org/wiki/Q764804) | Kenwood House | 1929 | late 17th century (remodelled 18th century) |
| [Q7069862](https://www.wikidata.org/wiki/Q7069862) | Nunnykirk Hall | 1977 | 19th century |
| [Q12064946](https://www.wikidata.org/wiki/Q12064946) | Orleans House Gallery | 1972 | 1710 |
| [Q2660524](https://www.wikidata.org/wiki/Q2660524) | Peel Castle | 1860 | 11th century |
| [Q1990172](https://www.wikidata.org/wiki/Q1990172) | Sherlock Holmes Museum | 1990 | 1815 |
| [Q7594011](https://www.wikidata.org/wiki/Q7594011) | St Leonards-Mayfield School | 1872 | 14th century (oldest buildings) |
| [Q2409878](https://www.wikidata.org/wiki/Q2409878) | The Bluecoat | 2008 | 1716–17 |
| [Q1670559](https://www.wikidata.org/wiki/Q1670559) | Vinquoy chambered cairn | -2000 | early 3rd millennium BC |

## Remaining conflicts

| Building | Nation | Catalogue date | Other source |
|---|---|---|---|
| [Adam and Eve](https://www.wikidata.org/wiki/Q15734109) | England | 1249 (Wikidata: 17th-century) | second source in the date gives 1601; the catalogue uses 1249 |
| [Aldenham Park](https://www.wikidata.org/wiki/Q26827885) | England | 1465 | Wikipedia introduction gives 1651 ("Aldenham Park, also known as Aldenham Hall, is a late 17th-century country house in Morville, near Bridgnorth, Shropshire, England which stands in 12 hectares of parkland."); the catal |
| [All Saints Church](https://www.wikidata.org/wiki/Q4729499) | England | 15th century | Wikipedia introduction gives 401 ("The church is thought to incorporate a small Romano-British basilica possibly built in the fifth century, though most of the current fabric is medieval."); the catalogue uses 1401 |
| [Althorp](https://www.wikidata.org/wiki/Q441079) | England | 1508 | Wikipedia introduction gives 1688 ("The house dates to 1688, replacing an earlier house that was once visited by Charles I."); the catalogue uses 1508 |
| [Balloch Castle](https://www.wikidata.org/wiki/Q3299192) | Scotland | 1809 | Wikipedia introduction gives 1001 ("Balloch was a property of the Lennox family from the 11th century, and the old castle was built in the 13th century."); the catalogue uses 1809 |
| [Beverston Castle](https://www.wikidata.org/wiki/Q4899641) | England | 1225 | Wikipedia introduction gives 1601 ("Several buildings on the 693-acre property, including five cottages and the 17th-century house with seven bedrooms, were in use as residences, however."); the catalogue uses 1225 |
| [Bourn Windmill](https://www.wikidata.org/wiki/Q17646352) | England | pre-1636 (Wikidata: 2022) | second source in the date gives 2022; the catalogue uses 1636 |
| [Brechin Cathedral](https://www.wikidata.org/wiki/Q2307632) | Scotland | 1012 (Wikidata: 13th century) | Wikipedia introduction gives 1201 ("Brechin Cathedral is a Scottish church building which dates from the 13th century."); the catalogue uses 1012 |
| [Castrum Anderitum](https://www.wikidata.org/wiki/Q943660) | England | 290s | Wikipedia introduction gives 1001 ("It was re-inhabited by Saxons and in the 11th century the Normans built a castle within the east end of the fort."); the catalogue uses 290 |
| [Cawdor Castle](https://www.wikidata.org/wiki/Q1051919) | Scotland | 1454 | Wikipedia introduction gives 1001 ("However, the story is highly fictionalised, and the castle itself, which is never directly referred to in Macbeth, was built many years after the life of the 11th-century King Macbeth. |
| [Chester Castle](https://www.wikidata.org/wiki/Q505858) | England | 1069 | Wikipedia introduction gives 1788 ("In the castle complex are the remaining parts of the medieval castle together with the neoclassical buildings designed by Thomas Harrison which were built between 1788 and 1813."); the |
| [Church of All Saints, Rudby](https://www.wikidata.org/wiki/Q17538103) | England | 14th century | Wikipedia introduction gives 1101 ("A church was probably built in Rudby in the 12th century."); the catalogue uses 1350 |
| [Church of St Andrew](https://www.wikidata.org/wiki/Q17533864) | England | 12th century | Wikipedia introduction gives 1301 ("The main fabric of the church dates back to the 14th century."); the catalogue uses 1150 |
| [Church of St Giles, Totternhoe](https://www.wikidata.org/wiki/Q5117417) | England | 13th century | Wikipedia introduction gives 1501 ("Constructed primarily from locally sourced Totternhoe Stone, the church's architectural evolution spans from the 14th to the 16th century."); the catalogue uses 1250 |
| [Church of St James](https://www.wikidata.org/wiki/Q17525789) | England | 11th century | Wikipedia introduction gives 1401 ("The Anglican Church of St James at Chipping Campden in the Cotswold District of Gloucestershire, England, was built in the 15th century incorporating an earlier Norman church."); the c |
| [Church of St James](https://www.wikidata.org/wiki/Q17529420) | England | 14th century | Wikipedia introduction gives 1840 ("The church was built using locally quarried magnesium limestone—the same famous quarry stone selected in 1840 for rebuilding the Palace of Westminster."); the catalogue uses 1350 |
| [Church of St Mary](https://www.wikidata.org/wiki/Q17538091) | England | 16th century | Wikipedia introduction gives 1201 ("A church was built in Thornton, probably in the 13th century."); the catalogue uses 1550 |
| [Church of St Owen, Bromham, Bedfordshire](https://www.wikidata.org/wiki/Q5117666) | England | 13th century | Wikipedia introduction gives 1601 ("The church is a 17th-century building and stands in a parkland setting."); the catalogue uses 1250 |
| [Church of St Peter and St Paul, Kilmersdon](https://www.wikidata.org/wiki/Q5117709) | England | 12th century | Wikipedia introduction gives 1401 ("The Anglican Church of St Peter and St Paul in Kilmersdon, Somerset, England, dates back to the Norman period, though much of the current structure was built during the 15th and 16th c |
| [Corbridge Bridge](https://www.wikidata.org/wiki/Q5169781) | England | 1674 | Wikipedia introduction gives 1201 ("Corbridge Bridge is a 17th-century stone bridge across the River Tyne at Corbridge, Northumberland, England, at the point where another structure, eventually a toll bridge, was constru |
| [Elsing Hall](https://www.wikidata.org/wiki/Q17534855) | England | 1470 | Wikipedia introduction gives 1201 ("Likely first built in the 13th century and home to Hugh Hastings I, it was extensively remodelled around 1852 by Thomas Jeckyll."); the catalogue uses 1470 |
| [Foss Dyke](https://www.wikidata.org/wiki/Q1412149) | England | c. AD 120 (Wikidata: 1671) | second source in the date gives 1671; the catalogue uses 120 |
| [Goodrich Castle](https://www.wikidata.org/wiki/Q5583571) | England | 11th century | Wikipedia introduction gives 1200 ("Goodrich Castle was probably begun by Godric of Mappestone after the Norman Conquest of England, initially as an earth and wooden fortification."); the catalogue uses 1001 |
| [Greensted Church](https://www.wikidata.org/wiki/Q2294625) | England | 845 (Wikidata: 11th century) | second source in the date gives 1001; the catalogue uses 845 |
| [Hadlow Castle](https://www.wikidata.org/wiki/Q5638005) | England | 1852 | Wikipedia introduction gives 1701 ("Hadlow Castle was an 18th-century country house in Hadlow, Kent, England, built in the fashionable Strawberry Hill 'Gothic' style."); the catalogue uses 1852 |
| [Hatfield Peverel Priory](https://www.wikidata.org/wiki/Q5681399) | England | 11th century | Wikipedia introduction gives 1765 ("The current house, in a park designed by Richard Woods in 1765 and built in 1769, stands on a rise of land overlooking the Chelmer valley."); the catalogue uses 1001 |
| [Holywood Priory](https://www.wikidata.org/wiki/Q5887234) | Northern Ireland | 7th century (Wikipedia list: c. 12th century) | second source in the date gives 1101; the catalogue uses 601 |
| [Iona Abbey](https://www.wikidata.org/wiki/Q198409) | Scotland | AD 563 (Wikipedia list: 1200-1220) | second source in the date gives 1200; the catalogue uses 563 |
| [Jew's Court](https://www.wikidata.org/wiki/Q3178465) | England | 12th century (claimed medieval synagogue) (Wikidata: 17th-century) | second source in the date gives 1601; the catalogue uses 1150 |
| [Kilkea Castle](https://www.wikidata.org/wiki/Q2969483) | Republic of Ireland | 1180 (Wikidata: 1426) | second source in the date gives 1426; the catalogue uses 1180 |
| [Langdon Abbey](https://www.wikidata.org/wiki/Q6485793) | England | 12th century | Wikipedia introduction gives 1501 ("The visible remains of the abbey are now confined to the extensive cellaring below the 16th-century house that occupies its site and small remains of a 17th-century ice house."); the c |
| [Malmesbury Abbey](https://www.wikidata.org/wiki/Q550064) | England | 7th century (Wikipedia list: c. 1180) | second source in the date gives 1180; the catalogue uses 601 |
| [Old Bushmills Distillery](https://www.wikidata.org/wiki/Q268267) | Northern Ireland | 1608 (licence) (Wikidata: 1784) | second source in the date gives 1784; the catalogue uses 1608 |
| [Paisley Abbey](https://www.wikidata.org/wiki/Q3018559) | Scotland | 1163 (Wikipedia list: Mid 15th century) | second source in the date gives 1401; the catalogue uses 1163 |
| [Quanterness](https://www.wikidata.org/wiki/Q2122220) | Scotland | 3250 BC | Wikipedia introduction gives -700 ("The dwelling was constructed around 700 BC."); the catalogue uses -3250 |
| [Quarr Abbey](https://www.wikidata.org/wiki/Q749713) | England | 1912 | Wikipedia introduction gives 1101 ("In the vicinity are a few remains of the original twelfth-century abbey."); the catalogue uses 1912 |
| [Quintin Castle](https://www.wikidata.org/wiki/Q7272441) | Northern Ireland | 1184 (Wikidata: 19th century) | second source in the date gives 1801; the catalogue uses 1184 |
| [Rochester Cathedral](https://www.wikidata.org/wiki/Q2635720) | England | 7th century (Wikipedia list: 1080) | second source in the date gives 1080; the catalogue uses 650 |
| [Romsey Abbey](https://www.wikidata.org/wiki/Q6137344) | England | 10th century (Wikipedia list: c. 1130) | second source in the date gives 1130; the catalogue uses 901 |
| [Sheep Heid Inn](https://www.wikidata.org/wiki/Q7492406) | Scotland | 1360 (Wikidata: 19th-century) | second source in the date gives 1801; the catalogue uses 1360 |
| [Sherborne Abbey](https://www.wikidata.org/wiki/Q1262119) | England | 705 (Wikidata: 10th century) | second source in the date gives 901; the catalogue uses 705 |
| [Sketrick Castle](https://www.wikidata.org/wiki/Q7534770) | Northern Ireland | Late 12th century (Wikidata: 16th century) | second source in the date gives 1501; the catalogue uses 1101 |
| [Smock Alley Theatre](https://www.wikidata.org/wiki/Q7545740) | Republic of Ireland | 1662 (Wikidata: 2012) | second source in the date gives 2012; the catalogue uses 1662 |
| [St Andrew's Church, Bramfield](https://www.wikidata.org/wiki/Q17527092) | England | 14th century | Wikipedia introduction gives 1101 ("It has a separate 12th-century tower standing in the church grounds."); the catalogue uses 1350 |
| [St Bartholomew's Hospital](https://www.wikidata.org/wiki/Q164946) | England | 1123 (Wikidata: 15th-century) | second source in the date gives 1401; the catalogue uses 1123 |
| [St Benedict's Church](https://www.wikidata.org/wiki/Q17524668) | England | 14th century | Wikipedia introduction gives 1001 ("The Anglican Church of St Benedict at Glastonbury within the English county of Somerset was built as a Norman chapel in the 11th century with substantial additions in the 15th and 19th |
| [St Botolph's Church, Boston](https://www.wikidata.org/wiki/Q7592685) | England | 1309 | Wikipedia introduction gives 1501 ("It has been referred to as "Boston Stump" since it was constructed in the 16th century."); the catalogue uses 1309 |
| [St Botolph's Church, Botolphs](https://www.wikidata.org/wiki/Q7592686) | England | 11th Century (Wikidata: 13th century) | second source in the date gives 1201; the catalogue uses 1001 |
| [St Ceinwen's Church](https://www.wikidata.org/wiki/Q17742738) | Wales | 12th century | Wikipedia introduction gives 801 ("The north chapel was added in 19th century as was the tower; gravestones of 9th and 11th centuries are built into the buttresses."); the catalogue uses 1101 |
| [St Giles in the Fields, Holborn](https://www.wikidata.org/wiki/Q3495322) | England | 1731 | Wikipedia introduction gives 1101 ("The church, named for St Giles the Hermit, began as the chapel of a 12th-century monastery and leper hospital in the fields between Westminster and the City of London and now gives its |
| [St Machar's Cathedral](https://www.wikidata.org/wiki/Q2380110) | Scotland | 1131 (Wikipedia list: 1440) | second source in the date gives 1440; the catalogue uses 1131 |
| [St Mary's Church](https://www.wikidata.org/wiki/Q17742126) | Wales | 18th century | Wikipedia introduction gives 1401 ("Newman describes the 15th-century steeple as "unique in South East Wales"."); the catalogue uses 1701 |
| [St Mary's Church, Reculver](https://www.wikidata.org/wiki/Q16932718) | England | 7th century | Wikipedia introduction gives 801 ("Viking attacks may have extinguished the church's religious community in the 9th century, although an early 11th-century record indicates that the church was then in the hands of a dean |
| [St Mary’s Church (Kidwelly)](https://www.wikidata.org/wiki/Q16857171) | Wales | 14th century | Wikipedia introduction gives 1114 ("1114 the church was burnt down in 1223 and most of the existing building dates from c."); the catalogue uses 1301 |
| [St Michael and All Angels Church, Mount Dinham, Exeter](https://www.wikidata.org/wiki/Q7594857) | England | 13th century | Wikipedia introduction gives 1867 ("The building in is the early Gothic style and was built to the designs of Major Rohde Hawkins, 1867–68."); the catalogue uses 1250 |
| [St Nicholas Shambles](https://www.wikidata.org/wiki/Q7594963) | England | 1196 | Wikipedia introduction gives 1001 ("The original nave and chancel probably dated from the 11th century."); the catalogue uses 1196 |
| [St Peirio's Church](https://www.wikidata.org/wiki/Q7595197) | Wales | 15th century | Wikipedia introduction gives 1801 ("One 19th-century writer said that it was "one of the humblest ecclesiastical buildings in Anglesey", and that there were "no architectural features in this church worthy of delineation |
| [St Peter's Church, Barton-upon-Humber](https://www.wikidata.org/wiki/Q7595214) | England | 9th (baptistery) and 10th centuries (Wikidata: 9th century) | second source in the date gives 801; the catalogue uses 10 |
| [St Winifred's Church](https://www.wikidata.org/wiki/Q7402316) | England | 12th century | Wikipedia introduction gives 995 ("It probably dates back as far as about 995, but extant records on the vicars only go back to the thirteenth century."); the catalogue uses 1150 |
| [Syningthwaite Priory](https://www.wikidata.org/wiki/Q16920786) | England | 1160 | Wikipedia introduction gives 1801 ("The rest of the building is post-Mediaeval, and the front range dates from the early 19th century."); the catalogue uses 1160 |
| [The Parish Church of St Nicholas](https://www.wikidata.org/wiki/Q17528755) | England | 11th century | Wikipedia introduction gives 1401 ("The church architecture dates from the Saxon period through to the 15th century."); the catalogue uses 1050 |
| [The Queen's College](https://www.wikidata.org/wiki/Q73094) | England | 1341 | Wikipedia introduction gives 1701 ("It is distinguished by its predominantly neoclassical architecture, primarily dating from the 18th century."); the catalogue uses 1341 |
| [Traquair House](https://www.wikidata.org/wiki/Q1307609) | Scotland | 1107 (claimed) (Wikidata: Circa 1492) | second source in the date gives 1492; the catalogue uses 1107 |
| [Westminster Abbey](https://www.wikidata.org/wiki/Q5933) | England | 10th century (Wikipedia list: Rebuilt 1245–1517) | second source in the date gives 1245; the catalogue uses 901 |
| [Wool House](https://www.wikidata.org/wiki/Q8033752) | England | 14th century (Wikidata: 1880) | second source in the date gives 1880; the catalogue uses 1400 |
| [Ye Olde Trip To Jerusalem](https://www.wikidata.org/wiki/Q5323585) | England | 1189 (Wikidata: 1650) | second source in the date gives 1650; the catalogue uses 1189 |
| [Ynyscedwyn Ironworks](https://www.wikidata.org/wiki/Q26877861) | Wales | 1612 | Wikipedia introduction gives 1872 ("The remaining structures were built in 1872 to house a planned steel mill."); the catalogue uses 1612 |
| [York Castle](https://www.wikidata.org/wiki/Q80637) | England | 1068 (Wikipedia list: 1265) | second source in the date gives 1265; the catalogue uses 1068 |
| [York Museum Gardens](https://www.wikidata.org/wiki/Q2883914) | England | 4th century (Wikidata: 1835) | second source in the date gives 1835; the catalogue uses 301 |

## Second review (2026-10-21): 69 → 2 conflicts
The 69 remaining conflicts were read against the full Wikipedia articles (now cached by `bidb.stories`).
- **9 corrected** (`data/curated/date_corrections.json`, evidence sentence kept): Aldenham Park (early
  17th century, not the 1465 purchase of the manor), Brechin Cathedral (13th century), St Michael and
  All Angels, Mount Dinham (1867–68), St Peter's, Barton-upon-Humber (9th-century baptistery), St Mary's,
  Nash (15th-century steeple), Greensted Church (dendrochronology 1063–1108), All Saints, Lydd (oldest
  section late 5th century), St James, Chipping Campden (Norman church c. 1180), St Mary's,
  Thornton-in-Craven (13th century).
- **58 kept** (`data/curated/date_confirmations.json`, a reason for each): the other source dates a
  later house, rebuilding, restoration, licence, or founding of the site, or comes from fiction
  (Macbeth at Cawdor). These now show as "Reviewed".
- **2 resolved 2026-10-21** (research track, `data/curated/evidence.json`): Althorp keeps c. 1508 (list entry
  1356626: "c.1508, for John Spencer, remodelled by Henry Holland 1789"; Wikipedia's 1688 is a later rebuilding
  phase); Hadlow Castle corrected from 1852 to "late 18th century (house, dismantled 1951); tower 1838–40"
  (list entry 1070451). No conflicts remain open.
