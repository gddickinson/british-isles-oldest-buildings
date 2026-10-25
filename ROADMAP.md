# ROADMAP

Future work for British Isles Oldest Buildings, kept between sessions. Newest decisions first in
each section; tick items off (and move them to SESSION_LOG.md) when done. Sections with every item done
are moved to [`ROADMAP_DONE.md`](ROADMAP_DONE.md).

## Status (2026-10-25)
- Catalogue 22,508 records; 173,789 places in 22 groups; 12,193 people; 517 floor plans; "Change over time": 250
  series, 48 events, 23 map layers, 19 notes; 894 researched claims (with the 24 of the tea list). Release db-2026-10-24 (102 MB).
- Hosted copy https://claude.ai/artifact/4H8rfcGGxSJki91SrNFTPv (private), version 69 (2026-10-25, after C5b2d4):
  252.9 of 256 MiB, 449 of 511 files. Republish changed files only: checksum `dist/` before and after
  `python -m app.static_export`, batches under 64 MB, removals (null) first; list the files first (the service refuses
  to replace files this session has not read or listed).
- Figures: `node docs/make_figures.mjs` (app running); the setup figure needs a copy with no data
  (`git archive HEAD | tar -x -C <dir>`, run on port 5071).

## Trade, enterprise and innovation (planned 2026-10-23, George's idea)
How trades, guilds, trading companies, markets and exchanges (the stock market among them), firms and their
technologies shaped where people lived and worked, their towns, communities and government. Builds on the Markets
& trade and Industrial heritage places, the oldest shops, banks and markets, and the markets, fairs, coal and income
graphs, and on George's tea_explorer (`~/Documents/GitHub/tea_explorer`: tea history, 44 tea firms with founding
years and towns), used read-only. Its texts carry no citations, so they are leads: each fact used gets a source,
locator and quote. Rules as E1–E6: open licences or quoted published figures; estimates marked, models compared.
- [x] C1 (2026-10-23, three research agents: 72 sources in `data/curated/trade/sources.json`, summary and gaps in its
      README, checked by `python -m bidb.trade_sources`; use 32, quote figures 17, link only 8, ask 12, left out 3)
      Best finds: Wikidata 28,419 firms (48% with founding year and place; needs a class allow-list), Ireland's CRO
      register (CC BY, incl. dissolved), Companies House Table A8 1939–, Federico–Tena trade 1800–1938 (CC BY), the
      Statistical Abstract 1840–1938 scans (out of copyright; tea, shipping, banks), IPO patents 1852–1915 (OGL),
      legislation.gov.uk Acts. Not open: the Bank of England millennium dataset, CAMPOP tables, Kanefsky's engines.
- [-] C1b Dropped (2026-10-23, George: no permission emails for now). The 12 "ask" sources stay listed in the
      README for later; the plan below uses only open data and published figures quoted with page and quote. Where
      an asked source was the best one, the open stand-in is named in the item (C4, C5, C7, C8).
- [x] C2a (2026-10-23) Tea firms and events: 16 merchants and firms and 4 tea-room chains (Jacksons 1700 [firm's
      tradition, open], Twinings and Fortnum & Mason kept in the trade list, Horniman's 1826, Tetley 1837, Bewley's,
      Brooke Bond, Lipton, Whittard, Taylors, Mazawattee, Thompson's, Barry's, Typhoo, Clipper, Ahmad; Kardomah, A.B.C.,
      Lyons, Bettys) at their first shop where the source names it → `data/curated/trade/tea.json`, list `tea` of
      bidb.oldest_lists (places in "Markets & trade", 18 evidence claims, section on the Oldest page); 15 dated tea
      events 1657–1998 in `change/events.json` (theme Prosperity and work, `topic: tea`, citation with quote). All 47
      quotes found by `bidb.evidence --check`. tea_explorer's 1873 Ceylon date corrected to 1875 by the source.
- [x] C2b (2026-10-23) Graph "Tea drunk per person", UK 1864–1938 (lb a year), read from the page images of six
      Statistical Abstract editions (edition, leaf, page per figure in `change/data/tea_per_head_uk.csv`; each
      checked against the OCR and the overlapping years of another edition; the latest edition read is used, as
      editions revised earlier years by up to 0.03 lb after each census). 3.0 lb in 1864, 6.9 in 1914, 10.2 in 1938;
      none for 1915–18; Ireland out from 1923.
- [x] C2d1 (2026-10-23) The modern end to 1974: the Ministry of Food's (later MAFF's) "Estimated food supplies per
      head of population", tea row, read from the page images of five Annual Abstracts (Nos. 88, 92, 97, 107, 112;
      edition, leaf, page per figure in `change/data/tea_supplies_uk.csv`), each row checked on an enlarged crop and
      against the overlapping years of another edition → series `tea_supplies_uk` (source `maff_food_supplies`), a
      second line on "Tea drunk per person" (a different measure: 9.3 lb for 1934–38 against 9.5 in the Board of
      Trade series). 8.1 lb in 1941, 7.0 in 1943, 10.1 in 1956 (the peak), 7.5 in 1973. None for 1939–40.
- [x] C2d2a (2026-10-23) Tea before 1864 from the earliest Abstracts: per head 1852–1863 from the first per-head
      table (No. 14, 1852–1866, pp. 42–43; 1864–66 match the later editions already used, and Nos. 15–18 agree in
      their OCR), added to "Tea drunk per person" (2.00 lb in 1852, 2.90 in 1863); new graph "Tea retained for home
      consumption", UK 1846–1865 in million lb (No. 8 p. 21 and No. 13 pp. 38–39; 1851–60 agree), 46.7 → 97.8.
      The Abstract prints no per-head figure before 1852 and no yearly UK population before 1852, so none was made.
- [x] C2d2b1 (2026-10-23) "Tea retained for home consumption" continued to 1938 from the quantity tables of Nos. 26,
      41, 42, 46, 48, 59, 69 and 83 (page images; edition, leaf, page per figure). Overlaps agree except 1865 (274 lb).
      102.3 million lb in 1866, 202.4 in 1891, 305.5 in 1913, 277.4 in 1917, 388.0 in 1919, 487.7 in 1932, 431.8 in 1938.
      Found on the way: the printed 1938 per-head figure (10.18 lb) does not fit the same edition's total (≈ 9.1 lb);
      kept as printed, with a note.
- [ ] C2d2b2 Tea before 1846: 18th-century imports (1.2 million lb 1721 → 24 million 1801) and smuggling (4–7.5
      million lb before 1784) as published estimates quoted with page (Schumpeter 1960, Mitchell 1988, Mui & Mui).
      Needs page access to those books (not open; check the Internet Archive lending copies first).
- [x] C2d3 (2026-10-23) Graphs "Price of imported tea" (average value per lb before duty, 1865–1919, from the Abstract's
      average-price tables in Nos. 27, 30, 45, 46, 59, 66; computed values to 1870, declared values from 1871; 19.9d → 7.2d
      in 1902 → 16.1d in 1919) and "Duty on tea" (steps at each dated change, 1874–1938, from the tariffs of 1874 and 1921
      and the tables of taxes reduced or increased; Empire rate from 1919 as a second line, none printed for 1922–29).
      Edition, leaf and page per row in `change/data/tea_price_uk.csv`, `tea_duty_uk.csv`, `tea_duty_empire_uk.csv`.
- [ ] C2d3b Later and earlier tea prices and duty: "Tea—Indian average, London Auctions" (wholesale, No. 83 and the
      1930s editions; a different measure), prices by origin (India and Ceylon, China) 1908–1922 (Nos. 67–68), the duty
      before 1874 (the Abstract lists the 1865 cut without rates; needs the tariff Acts or another quoted source) and
      after 1938 (wartime editions).
- [x] C2d4 (2026-10-23) Tea after 1974: Defra's Family Food "UK - household purchases" (OGL; code 304 Tea, g a person a
      week, National Food Survey 1974–2000, then EFS/LCFS to 2024-25) → series `tea_household_uk` (lb a year), a third
      line on "Tea drunk per person": 7.8 lb in 1974 (MAFF supplies: 7.8), 4.2 in 2000, 2.4 in 2024-25; tea drunk away
      from home not included. Event "Tea rationed" 1940–1952 cited to Hansard (18 July 1940 c471: two ounces a week;
      22 Oct 1952 c1013: "since tea has been de-rationed"). Neither passage gives the first or last day (secondary
      sources say 8 July 1940 and 3 or 5 October 1952), so the event says "July 1940" and "autumn 1952". Not used:
      HMRC HS 0902 imports (a fourth measure), Defra's eating-out tea (in cups, not weight).
- [x] C2c (2026-10-23) Tea places, kind `tea_trade` "Coffee house, auction, dock or ship of the tea trade": Garraway's
      (1657), Tom's Coffee House where Twining began (1706), East India House (1648–1861, auctions from 1679), the
      London Commercial Sale Rooms in Mincing Lane (1834–1998), East India Docks (stays in Maritime heritage), Cutty
      Sark (stays a museum ship); tea rooms: Miss Cranston's Crown Luncheon Room (1878), the Willow Tearooms (1903,
      a catalogue building). Left for later: the Sultaness Head (no article), Domus Dei (Catherine's tea, 1662; no
      article found), the Horniman Museum (an era_places place; not taken into the list); tea rationing 1940–52
      now cited (C2d4).
- [x] C3a (2026-10-23) Guild houses, livery and cloth halls, stock exchanges, merchants' houses and livery companies as
      places in "Markets & trade" (bidb.trade_works + new bidb.livery): 50 halls (Wikidata guild house, livery hall,
      cloth hall; no longer town halls in bidb.institutions), the London Stock Exchange, 6 merchants' houses, and 41 of
      117 livery companies placed (13 at their hall, linked from the company's page) with order of precedence, trade,
      charter year (Wikipedia's precedence table and the source it cites), hall and motto. 76 companies have no place
      (no hall, or a hall without coordinates on Wikidata). 267 other trade items are catalogue buildings.
- [x] C3b (2026-10-23) The researched oldest of each: list `guilds` of bidb.oldest_lists (`data/curated/trade/guilds.json`,
      70 entries, 62 with their own sources, all 136 quotes found by `bidb.evidence --check`; 8 shown from the trade,
      tea and civic lists): guildhalls and livery halls (St Mary's Coventry 1340-42, Merchant Adventurers' York 1357-61,
      Merchant Taylors' site 1347, Apothecaries' the oldest extant City hall), livery companies (Weavers 1130/1155,
      Loriners' ordinances 1261, Fishmongers 1272; Grocers founded 1345 and chartered 1428, Drapers 1361 and 1364: both
      table dates right for different events), merchant guilds outside London (Preston 1179, Dublin 1192, Bristol,
      Edinburgh, Shrewsbury, Hostmen, Cutlers), trading companies (Staple 1319 to Hudson's Bay 1670), exchanges, coffee
      houses (Oxford 1650, Pasqua Rosée 1652), banks (Martins' 1563 tradition, open; Child 1664 to Bank of Ireland 1783),
      merchants' houses and trading posts (Steelyard 1282, Southampton c.1290, Hanse House 1475). 5 left open (Saddlers'
      Anglo-Saxon origin, Edinburgh 1260, Merchant Adventurers 1407, Queen's Lane, Martins). 29 companies have no
      standing place: listed on the Oldest page without a link. Glasgow Stock Exchange is a catalogue building (not missing).
      Counting houses: none with a source found; left to C3c/C8.
- [x] C3c (2026-10-23) People of the Markets & trade places, new stage bidb.trade_people (after oldest_checks; the
      people stage of places_build runs before these places exist, so none had any): the place roles plus Member
      (P463), Worked for (P108) and Master, governor or officer (positions of the organisation: Governor of the Bank
      of England, Masters of the Drapers, Brewers, Cordwainers, Ironmongers and Apothecaries, Prime Warden of the
      Goldsmiths, Master Cutler; chairperson, CEO, director, board member). 329 links, 294 people, at 117 places
      (Bank of England 81, London Stock Exchange 16, Cutlers in Hallamshire 15, Stationers 11, Drapers 10; 99 links at
      21 livery companies); 123 carry a Wikidata reference. Market towns and places on a settlement's item (Kirkby
      Lonsdale market) left out. Halls of the unplaced companies: only 10 of the 76 have a hall named in the mottos
      table; Mercers' Hall and Plaisterers' Hall placed from OpenStreetMap (name and street must agree; the plaque
      for the earlier Plaisterers' halls left out; checked against 9 halls placed by Wikidata, all within ~25 m), so
      43 of 117 companies placed. The rest (Clothworkers', Furniture Makers', Launderers', Farmers & Fletchers, Air
      Pilots House, the Gunmakers' Proof House) are not on OSM by that name and street; Insurers' Hall is closed. The
      29 guild-list entries with no standing place (East India Company…) cannot show people.
- [x] C4a (2026-10-24) Firms through time from Wikidata (new `bidb/change_firms.py`, through QLever: WDQS times out on
      the subclass tree): companies and items directly of class business or enterprise in the isles or with their head
      office there, 28,421 items; 3,090 parish councils, other councils, NHS trusts, colonial and learned societies,
      railway lines, brands, websites… left out by class name. Map layer "Firms open" (kind `spans`, coloured by nine
      industries from the classes, stated industry P452 or the name: making 1,697, publishing and media 2,019, transport
      and utilities 1,140, finance 900, shops 502, mining 494, food and drink 398, services 1,418, not stated 3,327):
      11,895 dated firms with a position, 10,928 of them at their head office (spread up to ~1 km), 2,371 with a closing
      year; 813 open in 1850, 9,147 in 2020. Four graphs (default off): firms founded per decade 1600–2020 (14,541
      dated firms; with "of these, closed" as a second line) and three by industry. Survivorship bias, the few closing
      years and national branches carrying the parent's founding year ("Merck (United Kingdom)" 1668) stated in the notes.
- [x] C4b (2026-10-24) Companies from the registers (new `bidb/change_registers.py`), six graphs of their own (default
      off, Prosperity and work), not more lines on the C4a graphs: the registers count about a hundred times the
      Wikidata firms (5.7 million incorporations in the ten years to 2019-20 against 2,370 Wikidata firms founded in the 2000s), which would
      flatten them. "Companies incorporated per year" (Table A8, GB 1939–2008-09, UK from 2009-10; 11,100 in 1939,
      69,400 in 1980, 815,277 in 2025-26), with dissolved and "of each year's, still on the register in 2026" (Companies
      House basic data, Companies Act companies only as in A8: 5,063 of 1980's 69,400 survive); "Companies on the
      register" (173,300 in 1939, 5,479,045 in 2025-26; effective register as a second line); "Companies registered per
      year: Ireland" (CRO, 827,850 records: registered, dissolved from 1960, still registered; dissolved companies
      before the 1960s mostly missing, CC BY attribution in the note); and three "Companies alive today by decade
      founded" by industry (SIC divisions mapped onto the C4a industries; 4,901,090 live companies, 276,382 dormant
      or with no code). Not done: Ireland by industry (NACE on only 32% of CRO records), the CRO SQL API (functions
      such as `extract` not allowed; the 47 MB zip is read instead). Companies House's dissolved companies (API key)
      not used.
- [ ] C5 Trade and work graphs (with estimates and models compared), split 2026-10-24 into C5a–C5e below. Rules for all
      parts: open data or published figures quoted with page; estimates before the statistics marked; open or quoted
      stand-ins for the sources not asked for (not the CAMPOP tables, the Bank of England dataset, Clark, Allen, GPIH,
      MeasuringWorth, or Kanefsky's engines database or its GIS).
- [x] C5a (2026-10-24) Patents per year from the IPO alone (new `bidb/change_patents.py`, OGL): graph "Patents granted
      per year", England and Wales to 1852 then the UK: the old law's patents per decade (five years from 1800) from the
      first number of each period (3.6 a year in 1617–29, 0.2 in 1640–59 when the Commonwealth's were never numbered,
      88 in 1800–04, 524 in 1850–52), the 1852–1915 table (2,384 granted in 1852/3, 3,962 in 1883, 9,984 in 1884),
      specifications published 1917–1978 from the first number of each year (9,319 in 1917, 39,550 in 1978), and grants
      by the IPO 1995–2025 (monthly statistics; 2025 from Facts and figures); applications filed (1853–1915, 1995–2025)
      and European patents granted for the UK by the EPO (37,294 in 1995, 109,124 in 2024; more than the IPO's every
      year) as lines beside it. Graph "Patent applications published per year" 1979–2025 (numbers to 2010, Facts and
      figures 2019 and 2025 after; overlaps agree within 1%). No grant counts 1979–94 (the old series' publications
      end and the 1977 Act's grants are not in the number tables). Bottomley (2014) for England, Scotland and Ireland
      1700–1851: OWID gives no licence, so cited in the note, not drawn (his England 1800–04 = 440, the IPO numbers' 440).
- [x] C5b1 (2026-10-24) Overseas trade totals from open data (new `bidb/change_trade.py`), five graphs (default off,
      Prosperity and work): "Overseas trade, 1800-1938 (at 1913 prices)" (Federico-Tena, CC BY: UK imports 95 million $
      in 1800, 3,206 in 1913, 4,048 in 1938; exports peak 2,566 in 1913, 1,557 in 1938), the Irish Free State 1922-38
      on its own graph (1922-23 far below 1924; the database does not say why), "Overseas trade since 1948" (ONS
      IKBK/IKBL chained volumes at 2024 prices: exports £52 bn in 1948, £893 bn in 2025), "Goods exported, share of the
      economy" (CEPII via OWID, UK 1827-2014 and Ireland 1926-2014, with the ONS's BOKG/YBHA 1948-2025: 1.0 points
      from CEPII on average; services 57% of UK exports in 2025) and "Overseas trade: Ireland" (CSO TSA01, € million,
      1930-2025; exports above imports every year since 1985). Eras not joined: different measures, and over 1930-38
      Federico-Tena's dollars against the CSO's pounds give 3.14-4.96 $ to the pound, so they differ in more than the
      exchange rate. Re-exports not separate in any of these (C5b2).
- [x] C5b2a (2026-10-24) Trade at the prices of the time, 1854-1938 (new `bidb/change_trade_values.py`): imports, exports of
      UK produce and re-exports from the Statistical Abstract's summary table, read from the page images of Nos. 16, 18, 30,
      33, 46, 59, 70 and 83 (`change/data/trade_abstract_uk.csv`); all 85 rows pass their own sums. Graphs "Overseas trade
      at the prices of the time, 1854-1938" (imports £152 million in 1854, £769 million in 1913, £1,933 million in 1920,
      £920 million in 1938) and "Re-exports, share of all exports" (16% in 1854, 25.6% in 1863, 17.3% in 1913, 5.8% in
      1918, 11.6% in 1938). No. 18 misprints 1868's imports (294,460,214; its own total gives 294,693,608, as No. 30).
      The Abstracts' real (computed) values of imports begin in 1854, so nothing earlier is drawn.
- [x] C5b2b1 (2026-10-24) The main exports of UK produce by value, 1868-1911 (new `bidb/change_trade_goods.py`): coal,
      cotton, woollen and worsted, linen (yarn and manufactures), iron and steel, machinery, read from the page images of
      Nos. 30 (1868-82), 45 (1883), 46 (1884-98) and 59 (1897-1911) → `change/data/trade_goods_abstract_uk.csv` (1,947
      printed figures, edition, leaf, page, table each). Every printed total checked against its parts (one known £10
      gap: 1883 wool, where No. 33's hosiery + other makes it agree); figures without a total found printed the same in
      two or more other editions; No. 59's new classification brought back to the old totals (1897-98 agree to the
      pound). Graphs "Textile exports, 1868-1911" (cotton 67.7 → 118.6 £m, lowest 63.8 in 1893; wool 25.8, 38.5 in
      1872, 31.8; linen 9.4 → 9.1), "Coal, iron and machinery exports, 1868-1911" (coal 5.4 → 42.1 in 1907 → 38.5;
      iron and steel 17.3 → 46.6 in 1907; machinery 4.7 → 29.2) and "Main exports, share of all UK exports" (textiles
      57.3% → 35.1%, cotton 37.7% → 26.1%, coal, iron and machinery 15.3% → 24.5%). Printing slips found: No. 30's 1878
      tinned plates (732,378 for 2,732,378), No. 45's 1883 woollen stuffs (7,867,834 for 7,687,834).
- [x] C5b2b2a (2026-10-24) The same goods 1854-67 from No. 16 (table 21, 1854-55) and No. 18 (table 26, 1856-67), the
      editions C5b2a used, so the shares use the same totals: 458 printed figures; every printed total agrees with its
      parts, the tables' grand totals equal C5b2a's, and every figure without a total is printed the same in another
      edition. One worn figure: No. 18's 1867 railroad iron (4,361,129 on the page; the total and Nos. 19-30 give
      4,861,129). Definitions at the 1868 join: tin plates (under tin before 1868) added to iron and steel;
      manufactures of steel were "included with Hardwares and Cutlery previous to 1862" (No. 22) and are not in No. 18,
      so they count from 1868 (£0.36-0.47m a year 1862-67); coal is coals, cinders and culm before 1868 (no patent fuel:
      5.35 against No. 30's 5.44 million for 1868). Cotton and linen agree in both editions for 1868; wool manufactures
      differ by 0.2%, wool yarn by 2.6%. Graphs now 1854-1911 (cotton 31.7 £m in 1854, 46.9 in 1861, 36.8 in 1862;
      textiles 48.9% of UK produce exported in 1854).
- [x] C5b2b2b (2026-10-24) The same goods 1912-38 from No. 70 (table 212, 1911-25) and No. 83 (table 288, 1924-38),
      the editions C5b2a used: 1,614 figures (rows `n70_*`, `n83_*`) plus No. 70's grand totals, which equal C5b2a's.
      Neither table prints totals, so every figure was found in another edition's OCR (Nos. 71-82) or, where none
      prints it (mostly 1937-38), read again from an enlarged crop; No. 83 prints 1932 worsted tissues incomplete
      ("1,661,"; Nos. 79-82: 1,661,907). The 1920 classification brought back to the old totals and every overlap
      explained to the pound: 1911 (No. 59 vs No. 70) cotton +0.84m (hosiery and gloves to apparel, waste from
      worked cotton in other manufactures to 1919), wool +8,570 (flocks; wool hosiery added back), iron -2,196 (old
      rails), machinery -0.47m (road locomotives not shown; rail locomotives counted from vehicles); 1924-25 (No. 70
      vs No. 83) iron -0.41m and machinery +1.98m (boilers gathered under machinery; axles, tyres and wheels added
      back to iron). Graphs now 1854-1938 (cotton 126.5 £m in 1913, 401.4 in 1920, 49.4 in 1938; coal 120.3 in 1920,
      20.5 in 1926; textiles 17.0% of UK produce exported in 1938).
- C5b2b3 The main imports (raw cotton, wool, grain and flour, sugar, tea, timber; values and quantities) from the
      same scans 1854-1938; UK produce exports 1840-53 (declared values) from Nos. 8 and 13. Split 2026-10-24:
- [x] C5b2b3a (2026-10-24) The main imports by value 1854-1911 (new `bidb/change_trade_imports.py`), read from the
      page images of Nos. 16 (1854-55), 18 (1856-67), 30 (1868-82), 45 (1883), 46 (1884-98) and 59 (1897-1911; 1904
      grain from No. 62, the column lost in the binding) → `change/data/trade_imports_abstract_uk.csv` (1,496 printed
      figures). Every printed total agrees with its parts (corn, raw sugar and timber in Nos. 16/18, No. 59's grain,
      wood and wool); every other figure printed the same in another edition. Settled from other editions: No. 30's
      1868 other corn (1,981,558; 1,981,553 makes its total agree), 1875 raw sugar (cut at the page edge), No. 46's
      1884 hewn timber and 1885 teak. No. 59 brought back to the old definitions: 1897-98 agree except lentils (with
      seeds in No. 59 until April 1902: 0.05-0.06 million) and 1898's sheep's wool (revised +0.15 million). Graphs
      "Food imports, 1854-1911" (grain and flour 21.8 £m in 1854, 79.1 in 1909, 71.8 in 1911; sugar; tea), "Raw
      material imports, 1854-1911" (raw cotton 20.2 → 78.2 in 1864 → 71.2; wool 6.5 → 33.4; timber 11.1 → 23.8) and
      "Main imports, share of all imports" (food 24.6% → 16.4%; raw cotton, wool and timber 24.8%, 38.4% in 1864,
      18.9%). Timber in later editions (Nos. 19-22) runs ~0.36 million above No. 18 for 1866-67, unexplained; No. 18
      kept (the summary table's edition), the gap stated in the note.
- [x] C5b2b3b (2026-10-24) The same imports 1912-38 from No. 70 (table 206, pp. 304-309, 1911-25) and No. 83
      (table 285, pp. 392-397, 1924-38): 441 printed figures (rows `n70_*`, `n83_*`). No totals printed: 399 figures
      found printed the same in another edition's OCR (Nos. 71-82); 25 of 1929-37 confirmed on No. 82's own pages
      (pp. 397-401), where the OCR was garbled (e.g. oats 1933: OCR 1,206,568, page 1,206,558); 1911 unrefined sugar = No. 59's beet + cane; 1938 (No. 83 only)
      read again from enlarged crops. Joins: 1911 No. 70 equals No. 59 in every shared row; the 1920 classification
      drops peas, beans, rye, lentils and other meals (grain -3.23 £m in 1911), alpaca and flocks (wool -0.40) and
      adds the furniture woods (timber +2.05), stated in the notes; 1924-25 Nos. 70 and 83 agree to the pound in
      every good (No. 83's five timber rows = No. 70's three). Cotton is raw with linters and waste to 1919, raw
      without linters + waste from 1920. Graphs now 1854-1938: grain and flour 77.7 £m in 1913, 215.5 in 1920, 67.7
      in 1938; raw cotton 70.6, 256.5 (1920), 29.1; food 14.9% of imports in 1913, 12.8% in 1938.
- C5b2b3c Quantities of the same imports (cwt, lb, loads) 1854-1938, beside the values. Split 2026-10-24:
- [x] C5b2b3c1 (2026-10-24) Quantities 1868-1911 (new `bidb/change_trade_quantities.py`), read from the page images
      of No. 30 (table 21, pp. 40-45), No. 45 (table 27, its 1883 column), No. 46 (table 27, pp. 60-69) and No. 59
      (table 40, pp. 124-129; 1904 grain from No. 62's table 38, p. 126) → `change/data/trade_quantities_abstract_uk.csv`
      (1,019 printed figures). Every total of corn agrees with its parts (1890's worn digit from its parts and five
      other volumes); every figure printed the same in another edition's OCR, or read on No. 44's page (1883 teak and
      other wool) or No. 48's (1896 other corn). No. 59 against No. 46 for 1897-98: equal except lentils (-170,264 and
      -189,780 cwt, as in the values) and 1898's sheep's wool, revised +5,255,315 lb (No. 48 prints the revision).
      No. 59 gives 1911's raw cotton in centals of 100 lb (footnote). Value ÷ quantity runs smoothly year to year in
      every row (the check for misreadings); sugar fell about 30% in 1884 in all four rows together. Graphs (default
      off): "Food imports by weight" (grain and flour 3,350 thousand tons in 1868, 10,460 in 1903, 9,862 in 1911;
      sugar 626 → 1,898; tea 69 → 154), "Raw cotton and wool imported by weight" (cotton 593 → 1,066 in 1907 → 985;
      wool 113 → 359), "Timber imported" (4.13 → 9.46 million loads), and the value per unit as an index (1900 = 100):
      "Food import prices" (grain 189 in 1868, 86 in 1894, 117 in 1911; sugar 195, 79 in 1902; tea 226, 84 in 1902)
      and "Raw material import prices" (cotton 178, 69 in 1898, 138; wool 151, 80 in 1901; timber 107, 79 in 1887).
      No. 44 gives 1882's wool 1.1 million lb above No. 30 (other kinds and flocks counted from 1883).
- [x] C5b2b3c2 (2026-10-24) Quantities 1854-67 from No. 16 (table 10, pp. 20, 24; 1854-55), No. 18 (table 15,
      pp. 24-31; 1856-67) and No. 19 (table 15, pp. 24-25, 28-29; 1857-67): 384 printed figures. The corn rows are in
      cwt as later, but Nos. 16 and 18 print only wheat, barley, oats, maize and wheat flour (no other kinds or meal,
      6.8% of the total in 1857, and no total), so grain comes from No. 19, the first edition with the full table, and
      begins in 1857. No. 18 gives 6.3-8.5% less timber than No. 19 for every year 1857-67 (mostly sawn; staves the
      same; unexplained), and No. 19's 1868 equals No. 30's in every row, so timber also begins in 1857; sugar, tea
      and wool are the same in Nos. 18 and 19, raw cotton up to 0.09% lower, so those four go back to 1854. Prices to
      1867 use the values' own editions' quantities (Nos. 16 and 18; grain No. 19). Every printed total agrees except
      No. 16's 1854 hewn timber (1,216,920, also in other editions; the parts make 1,216,209); 371 figures printed the
      same in another edition's OCR, 1858's barley and timber on No. 20's page, the rest (1857 in No. 19, No. 18's
      teak) read again from enlarged crops. Graphs now 1854-1911 (timber 1857-1911): raw cotton 396 thousand tons in
      1854, 234 in 1862; cotton price index 98 in 1854, 376 in 1864; grain price 177 in 1857, 202 in 1867.
- [x] C5b2b3c3 (2026-10-25) Quantities 1912-38 from No. 70 (table 206, pp. 304-309, 1911-25) and No. 83 (table 285,
      pp. 392-397, 1924-38): 410 printed figures (rows `q70_*`, `q83_*`), on the same pages as the values (a quantity
      line above each £ line). No totals printed: every figure found printed the same in another edition's OCR, or read
      on No. 71's pages (four first readings corrected there: bold italic 2s and 3s read as 8s) or No. 82's, or (1938)
      read again from enlarged crops. Units: raw cotton and wool in centals of 100 lb, No. 83's tea and wool in thousand
      lb, cotton waste (from 1920) in cwt (No. 70 heads the row in centals; Nos. 73-83 cwt for the same figures). Joins:
      1911 in No. 70 equals No. 59 in every shared row; the 1920 classification leaves out the other grains and meals
      (3.9% of 1911's grain by weight), alpaca and flocks (1.1% of wool); 1924-25 Nos. 70 and 83 agree within the
      rounding. Timber: from 1912 only sawn softwood and pit props have quantities (8.28 of 9.46 million loads in 1911),
      drawn as a second line 1911-34 (planed softwood and sleepers inside sawn softwood to 1914; from 1936 standards and
      fathoms, with no loads given); the timber price index goes on with theirs, linked at 1911 (their value per load
      89% of all timber's). Graphs now 1854-1938: raw cotton 1,253 thousand tons in 1912, 568 in 1938; grain and flour
      10,381 in 1913, 9,417 in 1938; softwood 9.90 million loads in 1913, 2.08 in 1918, 8.53 in 1934.
- [x] C5b2b3d (2026-10-25) The main exports 1846-53 from No. 8 (table 18, p. 36; the earliest edition scanned, so
      not 1840): 248 printed figures, all 32 printed totals agree with their parts, every 1847-53 figure printed the
      same on No. 9's p. 36, 1846 (No. 8 alone) read again from an enlarged crop; No. 8's 1854 column equals No. 16's
      in every good. All exports of UK produce 1846-53 from No. 8's table 15 (the summary table of values begins in
      1854), printed the same in Nos. 10 and 13 (1848-53), for the shares. No. 8 prints tin plates only with tin and
      pewter ware and old iron only inside wrought iron: tin plates from No. 10 (1848) and Nos. 11 and 13, old iron
      from Nos. 11 and 13 (1849-53); before then iron and steel keeps the wider lines (about 1% high in 1846-47, 0.7%
      in 1848; stated). Graphs now 1846-1938: cotton 25.6 £m in 1846, 22.7 in 1848, 32.7 in 1853; iron and steel 4.8
      → 12.0; coal 1.0 → 1.6; textiles 63.2% of UK produce exported in 1846, 50.8% in 1853. The rest of the export
      side before 1846 (Nos. 1-7) is not in the Internet Archive collection.
- [x] C5b2c (2026-10-25) The modern end from HMRC's Overseas Trade Statistics (uktradeinfo API, OGL; bidb.change_trade_hmrc):
      the API's data begin in January 2000 (nothing for 1996-99), so 2000-2025, every year checked for all 12 months
      of the four flows (2026 stops at August). One paced `$apply` request per year sums value and net mass by HS
      heading; the goods of the Abstract graphs on the nearest modern headings (stated per note: yarns and woven
      fabrics only, made-up goods being classed by article; iron and steel chapters 72-73 without scrap; machinery
      chapter 84 without sewing machines, with motors, generators, transformers and rail locomotives; grain without
      rice; raw cotton without waste). Shares of all goods less non-monetary gold (61.8 bn exported, 116.9 bn imported
      in 2025). 21 series, 8 graphs beside the 1846-1938 ones; notes compare 1913 and 1938. Re-exports cannot be
      separated; the 2021 change from Intrastat to customs declarations for GB-EU trade is stated. Textiles 0.29% of
      goods exported in 2000, 0.10% in 2025 (31.9% in 1913); raw cotton 18.7 thousand tonnes imported in 2000, 0.73
      in 2025 (971 thousand tons in 1913); grain and flour 2,672 → 6,026 thousand tonnes.
- C5b2d The years between: 1939-1999 main goods (Annual Abstract of Statistics) to join the two eras; the hosted copy
      and release updated with the C5b2 graphs. Split 2026-10-25 (the collection has every edition to No. 135, 1999, but
      for Nos. 117, 121-123 and 127-129; `annualabstractof1981grea`, `annualabstractof1995unse` and
      `annualabstractof1999grea` are other scans):
- [x] C5b2d1 (2026-10-25) 1938-1952 by the Board of Trade's 1920 groups (new `bidb/change_trade_groups.py`), read from
      Nos. 84 (1935-46; 1939-40 only here), 88, 89 and 90 (the last on this classification; No. 91 uses SITC): 858
      figures, every edition's class totals checked against its printed totals; editions revise earlier years, so each
      year comes from the latest edition that prints it; the goods used are printed the same in another edition (1939-40
      in Nos. 85 and 86) or were read again from enlarged crops (No. 90). Groups are wider than the Abstract's articles
      (1938 on both: grain and flour 74.4 against 67.7 £m, cotton goods 49.7 against 49.4); linen, sugar and tea have no
      group. 15 series, 6 graphs: cotton goods 34.2 £m in 1943, 209.4 in 1951; machinery 27.9 → 421.7 £m 1943-52; coal
      exports 42.3 £m in 1939, 2.7 in 1947; cotton and wool 16.2% of exports in 1938, 10.7% in 1952; all exports 471.4 →
      2,549.6 £m. 1942-45 leave out munitions traded by government departments.
- C5b2d2 1953-~1977 from the SITC tables (Nos. 91 onwards). Split 2026-10-25: No. 101 (1964) moves to SITC (R);
      Nos. 104 onwards include precious stones in every year (in the accounts from 1965, estimated before) while
      No. 102 and earlier leave them out (1958 imports 3,747.5 against 3,833.5 £m, nearly all in division 66); Nos.
      108 onwards count re-exports with exports (from 1970, restated back to 1962).
- [x] C5b2d2a (2026-10-25) 1958-1974 by SITC (R) division (new `bidb/change_trade_sitc.py`), read from Nos. 104
      (1958-66), 108 (1962-70) and 112 (1966-74): every division of every section, 3,294 figures; every division checked
      against its section's total and every section against the grand total (one misprint, 1969 fuel imports, 906.5
      against parts of 906.2 in both editions); imports 1962-65 (Nos. 104/108) and both sides 1966-69 (Nos. 108/112)
      equal figure for figure, so each year from the latest of the three; exports of UK produce to 1961, with
      re-exports from 1962 (1962: 3,904.6 against 4,062.3 £m; coal unchanged, machinery 1,086.6 against 1,110.5). 15
      series, 6 graphs: textile yarn and fabrics 250.6 £m in 1958, 745.8 in 1974 (7.7% → 4.5% of exports); coal 31.4
      → 14.0 in 1967; machinery (71-72) 773.8 → 4,213.0; cereals 225.4 → 593.0; sugar 101.4, 173.0 in 1963, 368.9 in
      1974; oil imports 1,678.3 → 4,533.3 £m 1973-74. Nos. 113 (1976) onwards are still in Crown copyright under the
      50-year rule (No. 113 out of it from 2027): 1975 and later need the OGL question settled (C5b2d3).
- [x] C5b2d2b (2026-10-25) 1953-1957 by the Board of Trade's classes and divisions of the original SITC (new
      `bidb/change_trade_classes.py`, joined to the `aas_` series by `change_trade_sitc`), read from Nos. 99 (1953-61,
      tables 262-263, leaves 220-221) and 100 (1954-62, tables 261-262, leaves 220-221): every division, 1,890 figures,
      each checked against its class total and the classes against the total, all agreeing; 1954-60 equal figure for
      figure in the two editions (only No. 99's 1961 revised), so 1953 from No. 99, 1954-57 from No. 100. No. 102 was
      not needed: one change of basis at 1958, given in the notes from No. 100 against No. 104: coal (31.4), wood
      (140.5) and coffee-tea-cocoa (194.4) equal, cereals 226.6/225.4, textiles 254.2/250.6, machinery 787.5/773.8 £m;
      imports 3,747.5/3,833.5 and exports 3,176.2/3,249.8, mostly precious stones (division 66). Exports 1956-57
      include Lend-Lease silver repaid to the United States (22.4, 7.1 £m). Results: textiles 324.8 £m in 1953 (12.7%
      of exports); coal 69.8 → 14.0 £m 1953-67; machinery 569.9 → 4,213.0 £m 1953-74; textile fibres 390.8 £m in 1953,
      246.8 in 1958. The sum checks now allow at most ~4 standard deviations of the rounding (`near`), so a misread
      unit in a class of 23 divisions is caught.
- [x] C5b2d3 (2026-10-25) 1975-1999 as shares, from a public-domain source (George, 2026-10-25: "Use a source that is
      clearly OK for us to use. I don't wish to ask for permission at this time"). The Annual Abstract from No. 113
      (1976) is in Crown copyright for 50 years, and The National Archives' pages do not say plainly that older HMSO
      tables fall under the OGL (only that the old waiver's "headline statistics" do); ONS's MRETS starts in 1997.
      Used instead: the Growth Lab at Harvard University's International Trade Data (SITC, Rev. 2), CC0, UN Comtrade
      reconciled with partners' reports, in US dollars, so shares only (new `bidb/change_trade_atlas.py`), 1962-2024 on
      the same divisions (machinery as Rev. 2's 71-77), shares of all goods but non-monetary gold (97: 12.2% of exports
      in 2024, at most 2.34% before 1980). Against the Annual Abstract on 1962-1974 the mean differences are at most
      0.52 points (textiles; machinery -0.12, cereals -0.35, wood -0.26) and under 1.5 points in every year (tested).
      Results: textiles 7.2% of exports in 1962, 3.7% in 1975, 1.9% in 1999, 0.8% in 2024; machinery 27.0, 29.3, 36.2,
      28.2%; cereals 5.1% of imports in 1962, 2.9% in 1975, 0.6% in 1999, 1.2% in 2024. Goods not classified by kind
      (91-96) reach 12.1% of exports in 2011. Hardening: the charts draw at most three lines, so timber (1938-52) and
      wood and textile fibres (1953-74) were never drawn; those graphs now split, and bidb.change_series refuses a
      graph with more than two other lines (`MAX_MODELS`).
- [x] C5b2d4 (2026-10-25) Join the eras (new `bidb/change_trade_joined.py`): four lines 1846-2024 as shares (values
      cannot be joined: prices of the time, and the Growth Lab's are dollars), textiles and coal/iron/machinery of
      exports (from 1846), grain and raw cotton/wool/wood of imports (from 1854); each year from one era: Statistical
      Abstract to 1938, Annual Abstract groups 1939-52 and divisions 1953-74, Growth Lab 1975-2024 (`era` column).
      HMRC 2000- not joined (decision: its nearest headings of the old articles are far narrower than the divisions,
      textiles 0.29% of exports in 2000 against the Growth Lab's 1.6%; the Growth Lab keeps the same divisions to
      2024). Breaks marked (`breaks`, drawn as dotted marks where the line starts again, named on hover and listed
      under the graph; checked by `change_series.check_breaks`): 1912, 1923 (Irish Free State), 1939, 1953, 1958,
      1962 (exports, re-exports), 1975, with the year before on both definitions where two eras give it (1938 textiles
      17.0/16.2%, grain 7.4/8.1%; 1974 textiles 4.5/4.9%, coal-iron-machinery 29.3/30.0%). Results: textiles 63.2% of
      exports in 1846, 31.9% in 1913, 17.0% in 1938, 4.5% in 1974, 1.9% in 1999, 0.8% in 2024; coal, iron and
      machinery 12.0, 27.0, 30.2, 29.3, 38.1, 29.7%; grain 14.3% of imports in 1854, 10.1% in 1913, 1.2% in 2024; raw
      cotton, wool and wood 24.8%, 18.0%, 0.8%. Hosted copy version 69 (six changed files, 252.9 of 256 MiB). No new
      release: the database is unchanged since db-2026-10-24 (the graphs ship with the code).
- [ ] C5b3 Before 1800: Davis 1962, Schumpeter 1960 and Mitchell 1988 quoted per figure as estimate dots (needs the
      books' pages; `estimates.json`). Blocked (checked 2026-10-25): none of the three is on the Internet Archive,
      not even as a lending copy, and Davis 1962 (Economic History Review) is behind JSTOR. Needs a library copy of
      the pages, or another open source for 18th-century trade (as with C2d2b2).
- [x] C5c1 (2026-10-25) Occupations by sector 1381-2026 (new `bidb/change_work.py`): three graphs, "Working in
      farming, fishing and mining", "... making and building", "... services", mining with farming throughout (as
      the ONS and Keibek count it). UK: ONS long-term trends Figure 2a (OGL, from the Bank of England's Millennium
      dataset) 1920-1938 and 1948-1977, workforce jobs by SIC section (LMS series, June) 1978-2026; the two differ by
      at most 0.25 points over 1978-2016. Ireland: CSO CNNL1 at each census 1926-1996 (mining moved from industry).
      Dots: Keibek 2017 (open thesis, all rights reserved, quoted per figure in `estimates.json`): men and women
      1601-1851 (Table 20), men only for 1381 (Smith's range) and c.1525 (muster lists and coroners' reports).
      Results: primary 57.8% in 1601, 27.5% in 1851, 14.3% of UK workers in 1920, 1.2% in 2026; making and building
      33.5% in 1601, 47.7% in 1701, UK peak 40.1% in 1966, 14.0% in 2026; services 8.7% in 1601, 51.5% in 1920, 84.8%
      in 2026; Ireland primary 53.6% in 1926, 10.7% in 1996. Not used: OWID's farming share (its UK points before 1980
      are Broadberry & Gardner's at rounded years, agriculture only); Shaw-Taylor, Sugden & You 2019 (both sexes
      1710-1911: "not to be cited without the written permission of the authors"); Shaw-Taylor & Wrigley 2014 and
      Broadberry et al. 2015 (not open; Keibek's tables 22-23 print Broadberry's 1381 and 1522 figures beside the
      ones used).
- [x] C5c2a (2026-10-25) Ireland carried on to 2022 (`bidb/change_work.py`): CSO CNA26 (censuses 2002-2016 by
      industrial group) and F7040 (2011-2022 by detailed NACE group, usually resident and present), industry not
      stated left out (5-8%), mining moved to primary as before; the two tables agree within 0.40 points in 2011 and
      2016. Ireland: farming, fishing and mining 10.7% in 1996, 6.8% in 2002, 4.0% in 2022; making and building 26.1%
      in 2006, 17.4% in 2011 (construction 215,184 people in 2006, 90,357 in 2011; the LFS shows the same fall),
      18.6% in 2022; services 77.4% in 2022. The LFS (QLF03, yearly from 1998) not drawn: mining is not separate in it.
      Northern Ireland not drawn on its own: it is in the UK line, and the charts draw at most three lines.
- [x] C5c2b1 (2026-10-25; C5c2b split) England and Wales at the censuses of 1881-1911 (new `bidb/change_work_ew.py`),
      read from the page images of the 1911 Summary Tables (Cd. 7929, public domain; Internet Archive
      `censusofenglandw1911grea`): Table 65 (leaves 283, 285, 287; the 22 orders, 1911 classification carried back) and
      Table 64 (leaf 281: the food, tobacco and drink lines by sex, makers vs dealers; 1881-91 brackets shared out as in
      1901). Every order adds to the total occupied and every split line to its printed total (three misreadings found
      that way and corrected: order I 1911 289,261; defence 1901 168,238; greengrocers 1901 11,927, with two misprinted
      totals rebuilt from their under-15 and over-15 parts). Dealers the tables show apart (metals and machines,
      drapers, food, tobacco, drink, inns) moved to services; general labourers and order XXII's undefined others left
      out (6.1% of the occupied in 1881, 2.8% in 1911); dealers the condensed list joins to their trade stay there.
      Drawn as dots after Keibek's (the graphs already draw three lines). Farming, fishing and mining 18.2% in 1881,
      15.0% in 1911; making and building 42.6%, 43.3% (1901), 41.7%; services 39.2%, 43.3%.
- [x] C5c2b2 (2026-10-25) England and Wales 1861 and 1871 from Charles Booth's "Occupations of the people of the
      United Kingdom, 1801-81" (Journal of the Statistical Society 49, 1886; public domain, Internet Archive
      `s4833id1397560`), Appendix B (1) pp. 414-415: the censuses of 1841-1881 regrouped by Booth on one
      classification, dealers apart, in thousands (`work_booth_ew.csv`; every subtotal and total adds up). The 1861 and
      1871 reports' own tables are not on the Internet Archive (only their population volumes and the 1881 volumes).
      Grouped as the census figures: agriculture, fishing, mining / building, manufacture / transport, dealing,
      commercial, public and professional, domestic; general labour, the independent and indefinite left out. Booth's
      1881 within 1.3 points of the 1911 tables' (18.2/41.4/40.5 against 18.2/42.6/39.2), his 1851 within 0.4 points of
      Keibek's farming and mining and 1.7 of services; only 1861 and 1871 drawn: farming, fishing and mining 24.1%,
      20.5%; making and building 41.3%, 41.2%; services 34.6%, 38.3%.
- [ ] C5c2c Scotland and Ireland 1861-1911 the same way (Booth 1886 has Scotland and Ireland 1841-1881 on the same
      classification: Appendix B (2) p. 418, B (3) p. 422, same item; Irish census returns 1911 by province on the Internet
      Archive, `op1256115-1001` etc.); Broadberry et al. and Shaw-Taylor & Wrigley figures if their pages become
      available.
- [ ] C5d Prices and real wages: ONS RPI CDKO 1800– (OGL), Phelps Brown–Hopkins 1956 quoted per figure before it.
- [ ] C5e Shipping tonnage (Statistical Abstract 1840–1938, DfT FLE0101 1997–, Mitchell quoted from 1788), steam power
      as quoted totals (Kanefsky's published counts, Nuvolari et al. 2011) beside the engine houses and mills already
      on the map, banks (Statistical Abstract; country banks quoted from Pressnell); patents in Ireland (IPOI annual
      reports 2002–, quote figures) and 1916–94 grants (Patent Office annual reports, if found) left from C5a.
- [ ] C6 Innovations: inventions and firsts made in the isles (Wikidata inventor and place, researched list with
      sources), on the map and the slider, linked to the buildings and places where they were made or used
      (mills, works, mines, engine houses, exchanges).
- [ ] C7 Laws and institutions as dated events with citations: borough and guild charters, the Statute of the
      Staple, Navigation Acts, the Bubble Act, enclosure, Corn Laws and their repeal, Combination Acts, joint-stock
      and limited-liability Acts (1844, 1855–56), Factory Acts, co-operatives (Rochdale 1844), trade unions
      (Tolpuddle 1834, TUC 1868), Big Bang 1986; the Atlantic slave trade and abolition (1807, 1833) treated plainly,
      with the firms, ports and fortunes involved (from published histories and Acts, quoted; the Legacies of
      British Slavery database only linked, not used as data).
- [ ] C8 Trade stories: one page per trade (wool and cloth, tea, sugar and slavery, cotton, linen, coal, iron and
      steel, fishing, brewing and distilling, banking and finance), each with a timeline, its places on the map,
      graphs, the people, and cited analysis notes (E5 style, both sides where historians disagree: e.g. wool and
      the wool churches, the "industrious revolution", slavery's part in industrialisation, railway mania).
- [ ] C9 GUI: the trade stories reachable from the Change over time page, detail views ("Trade and industry here":
      the guild, firm or trade of a building), map filters by trade, Oldest page entries, quiz questions
      ("which came first?"), exports; INTERFACE, Help and figures updated.

## Building types: a family tree of building (planned 2026-10-23, George's idea)
A reference page that classifies every type of building and construction in the isles the way a biologist classifies
species, with their "evolutionary" links: which type grew out of which (hall house → Wealden → lobby-entry → double
pile; motte-and-bailey → shell keep → tower keep → tower house; basilica → minster → cathedral; longhouse → farmhouse
and byre; coaching inn → railway hotel). Diagrams and charts show how buildings developed over time and how the
families relate; generated examples show the features of each type; materials, construction techniques and
technologies are explained along the way. Builds on the catalogue's 31 categories, the ~48 oldest-of-type examples
(`bidb/oldest_types.py`), periods, floor plans and outlines, and the tree-ring dates. Rules as the research track:
each type, date range and link cites published sources (Pevsner, Brunskill's *Vernacular Architecture*, Historic
England's listing selection guides and Introductions to Heritage Assets (OGL), HES/Cadw guidance, the Irish NIAH,
RCAHMS/RCAHMW typologies, Getty AAT and Historic England's thesaurus of monument types (FISH, OGL) for terms); where
the descent of a type is disputed, both views are given and the link is drawn as uncertain.
- [ ] BT1 Research the classification: a hierarchy (domain → family → type → variant, e.g. Domestic → Hall houses →
      Wealden house → "recessed-hall" Wealden), built on the FISH thesaurus of monument types (OGL) and Getty AAT,
      with periods of use (first known, flourishing, last built), regions, materials, structural system, plan form,
      the earliest surviving example in the catalogue, and the sourced "descended from / influenced by / replaced by"
      links (lineage, borrowing from abroad, convergence: similar forms with separate origins). Licence check first.
- [ ] BT2 Data: `data/curated/building_types.json` (types, links with kind and confidence, citations and quotes as
      the evidence file), checked by script; every catalogue record and place kind mapped to a type (the categories
      and Wikidata classes as a start), so each type shows counts, a map and the dated examples.
- [ ] BT3 Materials and techniques: stone (rubble, ashlar, flint, cob, clay lump), timber framing (cruck, box frame,
      jetty, close studding, wattle and daub), brick (bonds, from the 13th c. revival to the Victorian kilns), roofs
      (thatch, stone slate, slate, tile, pantile; roof trusses from crown post to king post), glass, iron and steel,
      concrete; each with dates, regions (the geology layer of the Change page says where stone came from), the
      technology that made it possible (brick tax, railways, Portland cement) and catalogue examples.
- [ ] BT4 The page `/types`: a browsable tree (cladogram-style, collapsible, with a time axis so each branch spans
      its years; solid lines for documented descent, dashed for disputed), a type page per type (definition, how to
      recognise it, features, materials, plan, period chart, map of examples, the oldest surviving, family links,
      sources), and a search; reachable from detail views ("This is a Wealden house: see its family").
- [ ] BT5 Charts: types in use through time (a stream/swimlane chart of each family's span, linked to the Map
      page's slider), materials by century (from catalogue records with a recorded material), the spread of a type
      across the isles over time (first dates by county), and "what came next" chains.
- [ ] BT6 Generated examples (George's building-gen, `~/Documents/GitHub/building-gen`, MIT, own project: procedural
      glTF buildings from period-correct construction rules; 4 of its 29 researched types implemented: Georgian
      townhouse, Victorian terrace, cottage, medieval tavern). First check its accuracy against the sources and the
      catalogue's floor plans; use it only for types it renders faithfully, labelled as an illustration, not a
      record. Shown as a 3D viewer (three.js, cut-away and exploded views, plan and section) or pre-rendered images
      for the hosted copy; more types added in building-gen itself (its repo), not copied here. Where a generated
      example would be guesswork, use labelled diagrams (plan, section, elevation drawn as SVG) and Commons
      photographs and floor plans of real examples instead.
- [ ] BT7 Hosted copy, Help page, INTERFACE, figures; quiz questions ("which type came first?", "name the type").

## Data quality and references
- [x] `bidb.bundle release` failed on this connection (found 2026-10-23: `gh release create` ended twice in HTTP 408,
      the ~100 KB/s uplink stalls). Fixed 2026-10-24: draft release (an interrupted run carries on with today's
      draft) → upload through the GitHub API with up to 5 attempts (a half-uploaded asset is removed first) → size
      and SHA-256 checked against GitHub's asset digest → published as Latest → manifest. Not yet run for real (the
      next release will be its first); the API fields it reads were checked against db-2026-10-23.
- [x] Time Team digs at whole degrees outside the isles (found 2026-10-23). Fixed 2026-10-24: the `{{coord}}` reader
      took the first two numbers, so `{{coord|51|48|28|N|1|38|13|W}}` became 51°N 48°E. `hoards.coord` now reads
      decimal and degrees/minutes/seconds with hemispheres (digs and hoards use it); 45 digs moved (Priory Engagement
      51.81, −1.64), the 4 specials abroad (Maryland, Mallorca, Denia, Utrecht) left out: 201 digs, all with a
      nation; catalogue buildings with a Time Team dig within 300 m 865 → 916 excavation rows. Rerunning digs also
      showed it deleted its own 335 excavated places (they counted as already in the database): fixed.
      In the local database only; the hosted copy and the release still have the old positions.
- [ ] People of the places added after places_build (found in C3c, 2026-10-23): Maritime 9,184, Military 9,186,
      Museums 5,146, Sport 5,495, Victorian 684, Excavations 540 and others have no linked people (the people stage
      runs before them). bidb.trade_people's `run` could take a group list: museums (directors, founders), sport
      (founders), military (commanders) would gain most.
- [ ] Rerunning one place stage by hand undoes what later stages did to its places (found in C3c, 2026-10-23): C3a
      reran trade_works and lost, for its 27,000 places, the researched dates of bidb.oldest_lists, the date
      precision and reviewed corrections of bidb.oldest_checks (8,530 + 52) and every nation (nation_geo). Fixed by
      rerunning oldest_lists → oldest_checks → nation_geo → trade_people. Either a `--after` option that reruns the
      dependent stages, or document the order in each stage's docstring.
- [ ] Catalogue categories of guildhalls (found in C3a, 2026-10-23): Merchant Adventurers' Hall (York), Norwich
      Guildhall and St Mary's Guildhall (Coventry) are "House / domestic"; guildhalls, livery and cloth halls
      probably want "Civic building" or a guild category (bidb.categories keyword rules; check the knock-on counts).
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

## Research track: original sources and evidence (started 2026-10-21)
Substantiate claims from original and published sources, never silently. Every researched claim goes in
`data/curated/evidence.json` with its sources (kind: primary / listing / secondary / reference), where in each
(locator) and an exact short quote; `python -m bidb.evidence --check` fetches each source again and confirms the
quote is there; verdicts (kept / corrected / open) feed `date_corrections.json` / `date_confirmations.json`.
Detail views show "Evidence"; the Data quality page lists every claim. Sources that cannot be fetched by a script
(paywalled books, Historic England list pages, archives in person) are cited with a locator and marked unreachable.
- [x] R0–R8 done 2026-10-21/22 (evidence file and checker, date conflicts, research entries, oldest-of-type
      evidence, earliest churches, manor houses, tree-ring dates, the 100 oldest, oldest lists): see ROADMAP_DONE.md.
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
- [x] E3 (2026-10-22/23; `bidb/change_layers.py`, `change_geology.py`, `change_rasters.py`) Map layers that follow
      the slider: HYDE population, cropland, pasture and built-up area at 29 dates; built-up land (GHSL 1975/2020),
      land cover (CORINE 2000–2018), pollen tree cover 9500 BC–1935, towns and cities by size (Buringh); fixed
      layers: bedrock geology by period, coalfields, superficial deposits, ancient woodland, farmland grades.
- [x] E4 (2026-10-22: panel on the Map page + page `/change`) "Change over time" panel: stacked small graphs with a shared year axis and a marker at the slider's
      year; each toggled, with units, uncertainty bands, and a source link; also a page of its own with notes.
- [x] E6 (2026-10-23, George: "all the rest", with estimates for missing dates and models compared) Other models
      on the same axis, published estimates as dots with error bars (`estimates.json`), dotted gaps read as
      estimates; yearly temperature for every country of the isles and the globe; homes in England; layers: pasture
      and built-up (HYDE), people per km² 1975–2020, decade temperature and rainfall since 1901 (CRU TS), ice sheet
      and coast from 31,000 years ago, night lights, tree cover lost since 2001, railway stations and dated railway
      and canal lines, Ireland's census by county. Left: Domesday and 1930s land use (non-commercial licences),
      HadUK-Grid maps (CEDA login), KK10 (PANGAEA bot check), HYDE 3.3 (browser download).
- [x] E5 (2026-10-23: 19 notes from the Neolithic boom and bust to the 1952 smog and rising seas, 50 quotes from published research, each with link and locator, both sides where scholars disagree; on the Change over time page and, for the slider's year, in the Map panel; `data/curated/change/notes.json`) Analysis notes (cited): what the series show together (e.g. building booms against population and
      prosperity, the Little Ice Age and harvest failures, the Black Death, enclosure, the coal age and CO₂),
      quoting published research rather than our own inference where it makes a causal claim.
