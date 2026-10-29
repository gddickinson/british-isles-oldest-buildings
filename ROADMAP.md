# ROADMAP

Future work for British Isles Oldest Buildings, kept between sessions. Newest decisions first in
each section; tick items off (and move them to SESSION_LOG.md) when done. Sections with every item done
are moved to [`ROADMAP_DONE.md`](ROADMAP_DONE.md).

## Status (2026-10-28)
- Dates: 156 text-mined catalogue dates corrected (quantities, road numbers, scanned register text; `bidb.date_recheck`), 207 reviewed date corrections.
- Building types: page `/types` (BT4a: family tree on a time axis, type and material pages, detail-view links; BT5: charts through time, spread by county, lines of descent; hosted too, BT4b; BT6b: plans of real examples on type pages; BT6c1, BT6c2b: labelled diagrams of 35 types; BT6c2a: plans of places); 321 types, 320 links, 2,216 quotes; materials and techniques: 114, 74 links, 1,105 quotes (BT3a), 8,879 records and 2,621 places linked to them (BT3b), each stone's bedrock on its map, the UK and Ireland (BT3c2); 15,729 records (69.9%) and 60,506 places typed, 257 of 295
  isles types with examples, 223 with an earliest surviving example (register periods no longer count).
- Catalogue 22,508 records; 173,789 places in 22 groups; 12,193 people; 517 floor plans; "Change over time": 320
  series, 76 events, 24 map layers, 19 notes, 138 sources; 894 researched claims (with the 24 of the tea list). Release db-2026-10-24 (102 MB).
- Repository public since 2026-10-27 (https://github.com/gddickinson/british-isles-oldest-buildings, MIT code, tests on
  every push); demo site on GitHub Pages https://gddickinson.github.io/british-isles-oldest-buildings/ (from release `site-2026-10-27`).
- Hosted copy https://claude.ai/artifact/4H8rfcGGxSJki91SrNFTPv (private), version 75 (2026-10-26, BT7 quizzes and Help; /types since 74,
  BT4b): 253.5 of 256 MiB, 490 of 511 files. Republish changed files only: checksum `dist/` before and after
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
- [x] C2d3b1 (2026-10-27; C2d3b split) Later tea prices, read from the page images: "Wholesale price of tea"
      (`tea_auction_uk`, "Tea—Indian average, London Auctions", d. a lb: No. 78 table 156 pp. 224-225, 1913 and
      1920-33; No. 83 table 192 pp. 258-259, 1924-38; overlaps equal; none printed 1914-19, dotted): 14.06d. in 1913,
      25.23 in 1923, 10.24 in 1932, 19.44 in 1938. Tea from India and Ceylon and from China (`tea_price_india_uk`,
      `tea_price_china_uk`, No. 68 table 49 pp. 218-219, 1908-22, declared values c.i.f.) drawn as two more lines on
      "Price of imported tea" (India within 0.5d. of all tea 1908-19; China 39.80d. in 1918 as printed). No. 77's OCR
      gives 1922 as 22.98; the page reads 22.93. No. 67's page index does not lead to its import-price page (1906-07
      left out). The new graph is also on the tea story.
- [x] C2d3b2 (2026-10-27) Tea duty before 1874 and after 1938 on "Duty on tea" (`tea_duty_uk`, `tea_duty_empire_uk`),
      each row quoting its source: 1847-1865 from the Budget debates in Hansard (Open Parliament Licence; the Victorian
      Customs Acts have no text on legislation.gov.uk): 2s. 2¼d. in 1847 and Dec. 1852, 1s. 10d. (Apr. 1853), 1s. 6d.
      (5 Apr. 1854), 1s. 9d. (Apr. 1855, Crimean War), 1s. 5d. (6 Apr. 1857), 1s. (Apr. 1863), 6d. (27 Apr. 1865). After
      1938: 8d. foreign and 6d. Empire held to 7 Apr. 1949 (Hansard 22 June 1949), then 2d. foreign and none on Empire
      tea (Finance Act 1949 s. 1, as enacted, OGL), a protective duty from 1963, removed from 1 Jan. 1964 (London
      Gazette 17 Dec. 1963: Import Duties (General) (No. 11) Order 1963). The Finance Acts 1939-64 with text were
      searched for tea (1941, 1943, 1945, 1947 (No. 2), 1955, 1957 have none there). New `tests/test_tea_duty.py`.
- [x] C2d3b3 (2026-10-27) Tea prices by origin 1854-1864: new graph "Price of imported tea by origin, 1854-1864"
      (`tea_price_china_1854_uk` with `tea_price_india_1854_uk`, `tea_price_japan_1854_uk` as lines), from No. 13's
      "Average prices, as fixed for the computed real value" pp. 36-37 (leaves 470-471; Nos. 11 p. 30 and 12 p. 36 print
      the same figures), read from crops of the page images: China 1856-64 (14.5d. → 20.19d. in 1862 → 18d.), India
      (Assam) 1856-64 (28.75d., 21d. in 1860-62, 27d.), Japan 1859-64 (18d. → 15.75d.); 1854-55 one price for China and
      India together (15.5d., 15.06d.), in the note. India 1857 read 2s. 1⅜d. (numerator blurred in all three
      editions). Computed values, so not joined to the declared values of 1908-22. On the tea story.
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
- [x] C5c2c1 (2026-10-25; C5c2c split) Scotland and Ireland 1841-1881 from Booth 1886, Appendices B (2) pp. 418-419
      and B (3) pp. 422-423 (same item, public domain; `work_booth_sc.csv`, `work_booth_ir.csv`, every subtotal adds
      up), grouped as England and Wales; new `bidb/change_work_nations.py`: two graphs, "Work by sector: Scotland,
      1841-1881" and "Work by sector: Ireland, 1841-2022" (three lines each; Ireland the whole island to 1881, then the
      state's census shares 1926-2022 after a break). Scotland: farming, fishing and mining 31.1% in 1841, 23.1% in
      1881; services 26.1%, 32.7%. Ireland: 54.1% and 46.4%; services 15.1% and 33.5% (army and navy counted in
      Ireland only from 1861). Left out: general labour etc., 5-13% in Scotland, 5-10% in Ireland, where most general
      labourers worked on the land (stated in the note).
- [x] C5c2c2a (2026-10-25; C5c2c2 split) Scotland at the censuses of 1901 and 1911 (new `bidb/change_work_sc.py`):
      Census of Scotland 1911, Vol. II (Cd. 6896, 1913; public domain; Internet Archive `b32177264_0004`), Table D1
      (leaves 86-97, pp. lxxv-lxxxvi), every one of the 397 occupation lines, males and females, 1911 and 1901 (the
      1901 figures regrouped by the census office), read from the page images (`work_census_sc.csv`; OCR unusable).
      Every line (or 1901 brace) agrees with its printed increase or decrease; the males add exactly to the printed
      totals occupied (1,473,757; 1,391,188), the women of 1911 too (593,210), the women of 1901 to 97 fewer than the
      printed 591,624 (kept as `KNOWN`). Grouped as Booth, whose line this carries on: every dealer line to services
      (coal, metals, drapers, butchers, grocers, tobacconists...), order XXII line by line (shopkeepers, costermongers,
      cattle dealers to services; sundry makers, engine drivers, factory hands to making); only general labourers left
      out (2.8% in 1901, 1.7% in 1911). Drawn on "Work by sector: Scotland, 1841-1911" after a break at 1901: farming,
      fishing and mining 19.0% in 1901, 19.1% in 1911 (Booth's 1881: 23.1%); making and building 43.6%, 41.7%;
      services 37.4%, 39.2%.
- [x] C5c2c2b (2026-10-25) Scotland 1891 (new `bidb/change_work_sc_1891.py`): Census of Scotland 1891, Vol. II,
      Part II (C. 7134, 1893; public domain; `tenthdecennialce0002vari`), the summary of occupations for all Scotland
      (pp. 2-9, leaves 41-48), read from the page images (`work_census_sc_1891.csv`): classes I-IV and the sub-orders
      of class V with no dealers whole from p. 3, the rest of class V line by line; every sub-order adds to its printed
      total and the sub-orders to the five class totals (1,776,952 occupied). Grouped as 1901-1911 line for line
      (cattle dealers, drovers, gamekeepers, coalheavers to services; mineral oil and gas works to making; coke burners,
      limeburners, quarriers to mining); six lines that join makers and dealers (tobacco, bakers and confectioners,
      furniture, provisions, clothes, platelayers and navvies) shared out as their lines were in 1901. Farming,
      fishing and mining 19.8%, making and building 42.7%, services 37.5%; general labourers left out 3.7%. Drawn
      between two breaks (1891: census lines after Booth; 1901: the 1911 classification). Booth's 1881 cannot be
      checked against it: the 1891 report compares 1881 only by class. Scotland's 1901 report occupation volumes (II,
      III: `op1254658-1001`, `op1254783-1001`) are empty stubs on the Internet Archive.
- [x] C5c2c2c (2026-10-25) Ireland 1891-1911 (new `bidb/change_work_ir.py`, `bidb/change_work_ir_1911.py`). Ireland kept
      the six-class classification of 1881 to 1911, with "working and dealing" sub-orders, so dealers needed the lines:
      - [x] C5c2c2c1 1891 and 1901 sub-orders: 1901 General Report (Cd. 1190, `op1254515-1001`) Table 91 (6 classes, 24
        orders, 80 sub-orders, `work_census_ir_t91.csv`), every row and total checked; one misprint (`KNOWN`).
      - [x] C5c2c2c2 1901 lines: Table 20 of the same report (males pp. 119-124, females pp. 125-130; the item's page
        views crop the left-hand pages at the gutter, the uncropped scans are in its `_images.zip`).
      - [x] C5c2c2c3 1891 lines: the 1891 General Report (C. 6780, `op1252985-1001`), Table 19 (pp. 114-128).
      - [x] C5c2c2c4 1911: the four province volumes' Summary Tables XIX (classes, sub-orders) and XX (lines),
        `work_census_ir_1911.csv`; the provinces add to 4,390,219 persons.
      Only the sub-orders that mix sectors were read line by line (orders 8-23, the students): 1,762 lines in
      `work_census_ir_lines.csv`, every sub-order equal to its printed total for each sex, year and province. Grouped as
      Scotland's lines; tobacconists, provision dealers, bakers and confectioners shared out as Scotland's 1901 lines;
      students and general labourers left out (5.8% of the occupied in 1891, 6.0% in 1901, 8.2% in 1911). Farming,
      fishing and mining 48.2%, 47.4%, 46.4%; making and building 21.8%, 21.8%, 21.3%; services 30.1%, 30.8%, 32.3%.
      Drawn on "Work by sector: Ireland" between breaks at 1891 and 1926.
- [x] C5d (2026-10-25) Prices and real wages (new `bidb/change_prices.py`, `bidb/change_wages.py`): graph "Prices since
      1800" (ONS long-run RPI CDKO, on a log axis, new `log` option of the graphs: 13.5 in 1800, 8.4 in 1850, 9.2 in 1900,
      25.3 in 1920, 15.8 in 1933, 1,589 in 2025); "Real wage rates, 1879-1912 and 1924-1938" (Board of Trade index of
      the general course of wages, Sixteenth Abstract of Labour Statistics p. 82, both printed means recomputed, one
      slip; Ministry of Labour weekly rates, Statistical Abstract No. 83 table 138; each divided by the RPI; +19% 1879-
      1900, 95.7 in 1912 (1900 = 100); 117.2 in 1938 (1924 = 100)); "Average weekly earnings at 2025 prices" (ONS KAB9,
      £740 in 2000, peak £819 in 2007, £728 in 2025).
- [x] C5d2a (2026-10-27; C5d2 split) Wages 1913-1934: "Real wage rates, 1879-1938" now has three lines. The Board of
      Trade index runs to 1913 from the Seventeenth Abstract of Labour Statistics (Cd. 7733, p. 66, leaf 90; 1880-1913,
      agriculture revised: 1912 mean 103.4 against 102.98 in the Sixteenth, so the latest edition is used, 1879 kept
      from the Sixteenth; all 35 rows' printed means recomputed). New line July 1914 = 100, 1914-1934: wage rates over
      the official cost-of-living index at the same date, the printed ranges as a band: Bowley 1921 Table XXXIII p. 106
      (July 1914-1919, quoted figures) and the Ministry of Labour's "estimated average percentage increase in weekly
      full-time rates of wages generally, compared with July, 1914" at 31 December 1920-1934 (Statistical Abstract
      No. 70 p. 93, No. 79 pp. 140-141; overlaps 1922-25 equal) over the cost of living at the next 1 January (No. 79
      p. 137, No. 80 p. 137). Real rates 76 in July 1917, 104 at the end of 1920, 111 in 1921, 97 in 1922, 115 in 1934.
      Bowley's July 1920 (260 over 252) agrees with the Ministry's end of 1920 within 2% (tested).
- [x] C5d2b1 (2026-10-27; C5d2b split) Wage rates 1935-1975 (new `bidb/change_wages_post.py`): graph "Real wage rates,
      1935-1975" (1939 = 100), the Ministry of Labour's index of weekly wage rates (all workers, all industries and
      services) at the end of each June over the RPI, read from the page images of the Annual Abstract Nos. 84, 88, 90,
      92, 93, 94, 100, 104, 108 and 112 (76 figures, `wages_mol_1935_1975.csv`, edition, leaf, page, table each; out
      of Crown copyright, published 1947-1975). Four bases chained by the printed links: June 1947 167-168 on September
      1939 = 100 (No. 94, revised from 166-167), January 1956 factor 1.561 (No. 94), July 1972 249.5 (No. 112); breaks
      marked at 1948, 1956, 1973. Overlapping editions agree except printed revisions (1966-67 +0.1, 1971 220.7 ->
      221.0); June 1956 105.4 x 1.561 = 164.5 against 164 on the old base. Real rates 94 in 1941, 100 in 1947, 95 in
      1952, 110 in 1960, 121 in 1970, 152 in 1975. New source `annual_abstract_wages_uk` (122).
- [x] C5d2b2a (2026-10-27; C5d2b2 split) Earnings 1963-1999: "Average weekly earnings at 2025 prices" now runs
      1963-2025, the ONS's AWE long run back series (MD9M, EARN02 table 11, OGL; monthly, not seasonally adjusted, each
      year the mean of its months) drawn dashed as modelled ("modelled estimates ... do not come with the same
      methodological assurances on quality as estimates from January 2000 onwards", quoted) under KAB9. £321 a week in
      1963 at 2025 prices, £741 in 1999 against KAB9's £740 in 2000; real earnings fell only in 1976-77 and 1995; +50%
      1963-1975 against +35% for real wage rates. New source `ons_md9m` (123).
- [x] C5d2b2b (2026-10-27) Wages before 1879 (new `bidb/change_wages_early.py`): graph "Wages in towns, 1790-1860"
      (1840 = 100). G. H. Wood, "The Course of Average Wages between 1790 and 1860" (Economic Journal 9, 1899, p. 591;
      public domain, Internet Archive periodicals scan): money wages in 24 towns and districts and their unweighted
      average (72 in 1790, 122 in 1810, 99 in 1845, 116 in 1860), every figure read from the page image
      (`wages_wood_1790_1860.csv`), each printed average within a point of its towns' mean except 1860 (116 printed,
      117.4). Real wages over the ONS RPI from 1800 (to 1810 over three years, as Wood's years stand for short
      periods): 72 in 1800, 96 in 1810, 138 in 1860 (1840 a dear year). Bowley's money-wage index numbers by decade
      1780-1899 ("not yet established", Wages in the United Kingdom in the Nineteenth Century, 1900, p. 126; quoted per
      figure in estimates.json) as estimate dots on 1840-50 = 100: 67 in the 1780s, 112 in the 1810s, 167 in the 1890s.
      New sources `wood_1899_wages`, `est_wages_bowley1900` (125). Not found open: Wood's 1909 JRSS real wages 1850-1902
      and Bowley's 1895 JRSS index 1860-91 (no JRSS volumes of those years on the Internet Archive), Phelps
      Brown–Hopkins (JSTOR); so 1861-1878 has only Bowley's decade dots.
- [x] C5e1 (2026-10-25; C5e split) Shipping (new `bidb/change_shipping.py`): "Merchant fleet registered in the UK,
      1884-1938" (all, steam and motor, sail; Statistical Abstract Nos. 46, 59, 70, 83, every row's parts checked, the
      editions' overlaps equal): 7.4 million net tons in 1884, 12.4 in 1914, 10.1 in 1918, 10.7 in 1938; sail 3.5 → 0.4;
      "Merchant ships built in the UK, 1897-1938" (1,200 thousand tons in 1913, 84 in 1933).
- [x] C5e2a (2026-10-27; C5e2 split) Merchant fleet registered 1848-1883: "Merchant fleet registered in the UK" now
      runs 1848-1938, read from the page images of Statistical Abstract No. 10 (table 35, p. 69, 1848-50), No. 13
      (table 36, p. 91, 1851-63), No. 26 (table 40, p. 100, 1864-69), No. 32 (table 54, p. 127, 1870-82) and No. 45
      (table 60, p. 175, 1883); in these multi-volume scans the image `page/n<leaf-1>` is the OCR leaf. Every row's
      sail + steam equals its printed total; the overlaps agree figure for figure (1851-62 Nos. 10/13, 1864-65 Nos.
      13/26, 1870-78 Nos. 26/32, 1884 Nos. 32/46) except 1883's steam tonnage (3,728,263 in Nos. 31 and 32, 3,728,268
      in No. 45, which adds to the total; `MISPRINTS`). Nos. 8 and 9 have no table of registered ships. 3.40 million
      net tons in 1848 (0.15 steam), sail at its peak 4.94 million in 1865, steam (net) overtook sail in 1883. No
      break marked for the Merchant Shipping Act 1854's measurement: the tables print no note of it and the line shows
      no jump at 1855 (ships were re-measured over years).
- [x] C5e2b1 (2026-10-28; C5e2b split) Ships built before 1897 (new `bidb/change_shipping_built.py`): "Merchant
      ships built in the UK" now runs 1846-1938, one line with breaks at 1871 and 1897: ships for British owners from
      the page images of Statistical Abstract Nos. 8 and 9 (built and registered, 1846-1861), 23 and 26 (built and
      first registered, to 1870), 26, 32, 33 and 46 (built whether registered or not, foreigners' and the Navy's left
      out, 1871-1898; `shipping_built_early_abstract_uk.csv`, 120 printed rows); every tonnage adds up (two printed
      vessel counts do not, `KNOWN`); each year from the latest edition, the revisions exactly as `REVISED` (1861 by
      No. 23: 310,900 → 200,839 tons; 1867-1873 by No. 26; 1877-1878 by No. 32). Second line: ships built for
      foreigners, war and merchant, 1884-1898 (No. 46 table 62: 162,430 tons in 1897 beside 482,267 for British
      owners; No. 59 gives 635,210 merchant tons in all, so the rest were warships). 125 thousand tons in 1846, steam
      first outweighed sail in 1870 and sail last in 1885, 769 thousand in 1883 the most before 1897.
- [x] C5e2b2a (2026-10-28; C5e2b2 split) Shipping 1939-1974 from the Annual Abstract (new
      `bidb/change_shipping_post.py`, read by bidb.change_shipping): "Merchant fleet registered in the UK" now runs
      1848-1970, the line continuing after a break at 1939 with the Annual Abstract's steam and motor vessels (net
      tons; Nos. 84, 88, 94, 100, 104, 108; sail no longer counted yearly, 3-4% of the tonnage; 1939-1962 with
      Commonwealth and foreign vessels on bareboat charter or requisitioned; 10.31 million in 1938 there against 10.30
      in the Statistical Abstract): 9.0 million in 1942, 12.0 in 1961, 11.5 in 1962, 14.7 in 1970 (estimate). New
      graph "Merchant ships completed in the UK, 1940-1974" (thousand gross tons, vessels of 100 gross tons and over;
      Nos. 84, 88, 90, 94, 100, 104, 108, 112) with tankers and ships for export (from 1957): 1,302 in 1942, 1,493 in
      1954, 848 in 1964, 1,189 in 1974; export 611 in 1967 (51%). Every row's parts checked, overlaps figure for
      figure (`REVISED`: only 1941 in No. 88), two misprinted totals replaced by their parts' sums (`MISPRINTS`).
      No. 109 onwards print only ships of 500 gross tons and over, so the register line ends in 1970.
- [x] C5e2b2b1 (2026-10-28; C5e2b2b split) The trading fleet since 1950 (new `bidb/change_shipping_fleet.py`, read
      by bidb.change_shipping): graph "UK-registered trading fleet, 1950-2025" (trading vessels of 500 gross tons and
      over registered in the UK and the Crown Dependencies, million gross tons: all, tankers, container ships from 1969)
      from DfT's table FLE0301 (OGL, one table 1950-2025; ODS read with the stdlib), breaks at 1986 (DfT's own records
      → Lloyd's/IHS data, 7.71 → 8.05 million on the two bases), 2009 (Statcode5 types, 25.81 on both) and 2022 (Sea/
      data). Checked against the Annual Abstract's "United Kingdom merchant vessels of 500 gross tons and over" read
      from the page images of Nos. 109, 110 and 112 (1961-1974, `shipping_500gt_annual_uk.csv`, 34 printed rows; types
      add to totals, No. 112 revised two parts): DfT gives the same number, gross tons and tankers in every year but
      1962-1963 (`DFT_DIFFERS`). 17.2 million gross tons (3,092 ships) in 1950, 31.5 million in 1975 (tankers 17.1),
      8.0 in 1986, 4.7 in 1993 (344 ships), 30.5 in 2017, 18.8 in 2025 (421 ships). Before 1986 DfT's type columns
      hold the old types (cargo liners under Ro-Ro, tramps under bulk carriers), so only all, tankers and containers are
      drawn. The 1970s gap of the net-ton register line is not joined (different coverage: every ship of 500 gross
      tons and over, 21.2 million in 1961, against 20.5 million of trading vessels).
- [x] C5e2b2b2a (2026-10-28; C5e2b2b2 split) Steam power (new `bidb/change_steam.py`): graph "Power in British
      industry, 1760-1907" (Industry and energy, log axis): Kanefsky's horsepower of steam, water and wind in Great
      Britain at 1760, 1800, 1830, 1870 and 1907 (thesis p. 338, not open) as printed in Crafts, Economic Journal 2004,
      Table 3 p. 342, quoted per figure in estimates.json (model `power_kanefsky1979`), drawn as estimate dots; `check`:
      each year's parts add to the printed total (the 2003 working paper's 160,000 for steam and water in 1830 do not,
      the journal's 165,000 do). Steam 5,000 hp in 1760, level with water in 1830, 9,659,000 (98%) in 1907; water's
      peak 230,000 in 1870. Note quotes Nuvolari, Verspagen and von Tunzelmann 2011 (Cliometrica, CC BY-NC): 95
      engines 1710-1733, 442 in 1734-1774, 2,279 by 1800 (479 Watt's; Tann 449). The NIC/Fouquet energy dataset has no
      power-by-source table. Nothing after 1907 yet (Census of Production engine horsepower 1907-1935 would continue it).
- [x] C5e2b2b2b1 (2026-10-28; C5e2b2b2b split) Country banks (new `bidb/change_banks.py`): the Statistical Abstract has no count of banks
      (only notes in circulation, savings banks, clearing; Pressnell is not open), so the count comes from Gilbart, The History
      and Principles of Banking (3rd edition 1837, public domain, `historyprinciple00gilb`), read from the page images: Table I
      p. 110, licences issued to country bankers and commissions of bankruptcy against country banks 1809-1832; Table II
      p. 111, the Stamp Office's country banks and partners by county for the licence years 1811-12 to 1818-19 (every county
      column adds to its printed total but the banks of 1815-16, 644 against 643, `KNOWN`). Graphs "Country banks in England
      and Wales, 1809-1832" (licences 702 in 1809, 940 in 1814, 636 in 1832; banks licensed 739 in 1811-12, 576 in 1817-18)
      and "Country bank failures, 1809-1830" (311 commissions; 89 in 1814-16, 80 in 1825-26), both in the banking trade story.
      Note quotes Gilbart on 1793 (22 bankrupt) and the Post-office Directory for 1834 (638 private country banks and branches,
      106 joint-stock banks and branches).
- [x] C5e2b2b2b2 (2026-10-28) Bank notes in circulation (new `bidb/change_banknotes.py`): the Statistical Abstract's table
      of promissory notes payable to bearer on demand in circulation, four dates a year, read from the page images of Nos. 8,
      13, 26, 41, 46, 59 and 68 (`banknotes_abstract_uk.csv`, 420 printed rows: Bank of England, country banks private and
      joint stock, Scotland, Bank of Ireland and other Irish banks, United Kingdom; No. 68 in thousands). Tesseract readings
      kept only where both printed sums hold, every other row read from the image (175 rows; 4 figures on damaged scans
      taken from the sums); overlapping editions equal but two Bank of England misprints (Dec 1893 in No. 41, Dec 1897 in
      No. 59, `KNOWN`); June 1900 does not add up as printed in Nos. 59 and 62. Graphs "Bank notes in circulation,
      1846-1922" (Bank of England £20.8 million in 1846, £28.5 million in 1913, £118 million in 1920; Scottish and Irish
      banks) and "Country bank notes in England and Wales, 1846-1921" (£7.65 million in 1846, £0.17 million in 1911,
      £2,000 in March 1921, none from June 1921), both in the banking trade story; event "Bank Charter Act and the end of
      country bank notes" (1844-1921). The Treasury's currency notes (1914-1928) are not drawn yet.
- [x] C5e2b2b2b3a (2026-10-28; C5e2b2b2b3 split) Savings banks (new `bidb/change_savings.py`): the Statistical Abstract's tables of
      the amount received from, paid to and due to depositors, read from the page images of Nos. 8, 13, 26, 41 (1879), 42, 46, 59, 70
      and 83 (`savings_banks_abstract_uk.csv`, 929 printed figures; nations to 1898, the United Kingdom from No. 59; No. 83 in
      thousands). OCR rows kept only where the nations add to the printed total, the rest read from the image; every year's amount
      due checked against the year before and the year's receipts, interest and payments (exact to the pound for the Post Office
      throughout and the trustee banks from 1877, when interest is first printed); overlapping editions equal with interest added
      to receipts (No. 46's Post Office receipts include it, No. 83 counts the trustee banks' dividends as receipts); two rows whose
      nations do not add up as printed (`KNOWN`), revisions of 1860 (No. 8's estimate) and 1865 (`REVISED`). Graphs "Savings banks:
      amount due to depositors, 1846-1938" (trustee banks £31.7 million in 1846, £41.5 million in 1861, £36.4 million in 1866; the
      Post Office passed them in 1885 and held £187 million in 1913, £509 million in 1938; special investment departments £96 million
      in 1938) and "Savings bank accounts open, 1897-1938" (breaks at 1909: active accounts only; 1924: No. 83's lower count; 1933:
      coupon accounts left out), both in the banking trade story; events "The first trustee savings bank, at Ruthwell" (1810) and
      "Post Office Savings Bank founded" (1861). Nations not drawn (in the CSV to 1898); Government stock held for depositors not drawn.
- [x] C5e2b2b2b3b1 (2026-10-28; C5e2b2b2b3b split) Bankers' clearing houses (new `bidb/change_clearing.py`): the Statistical
      Abstract's tables of amounts cleared at the London Bankers' Clearing House (1868-1938: total, six months to June, Stock
      Exchange and consols settling days, 4th of the month; town, metropolitan and country clearings from 1902) and the
      provincial houses (1897-1938, eleven towns and total), read from the page images of Nos. 31, 32, 33, 42, 46, 50, 59, 62,
      66, 69, 71, 78, 82, 83 (`clearing_london_abstract_uk.csv` 229 rows, `clearing_provincial_abstract_uk.csv` 120 rows).
      Every year but 1868 printed by two editions or more; checks: London parts add to the total, provincial towns to theirs,
      editions agree (London: one revision, 1883 4th of the month; provincial: No. 69 recompiled them from the London Clearing
      House's statements, revising most years by 0.1, and nine other differences listed). Nos. 29-30 print other totals with no
      year end stated, left out. Graphs "London Bankers' Clearing House: amounts cleared, 1868-1938" (log axis, town and
      country lines; break 1936, the District Bank admitted; £3,425 million 1868, £44,897 million at the 1929 height) and
      "Provincial bankers' clearing houses, 1897-1938" (Manchester, Liverpool; breaks 1909 Nottingham, 1912 Bradford, 1921
      Hull), both in the banking trade story.
- [x] C5e2b2b2b3b2a (2026-10-28; C5e2b2b2b3b2 split) Bank clearing 1939-1974 (new `bidb/change_clearing_post.py`, joined by
      bidb.change_clearing): the Annual Abstract's bank clearing tables read from the page images of Nos. 84, 88, 92, 96, 99, 104, 108,
      111 and 112 (`clearing_london_annual_uk.csv` 100 rows, `clearing_provincial_annual_uk.csv` 84 rows): every row checked by
      its parts (clearings against the Clearing House total, debit clearing = Clearing House + provincial houses, towns against
      their total within rounding), every year 1941-1973 printed by two editions or more and equal but the footnoted revisions
      (1968-1969 debit totals with the Liverpool afternoon clearing, the 1970 credit clearing after the bank mergers); 1939-1940
      only in No. 84, 1974 only in No. 112 (No. 113 still in Crown copyright). Graphs extended: "London Bankers' Clearing House:
      amounts cleared, 1868-1974" (general clearing from 28 August 1939 continuing the country line, break 1939; £1,640,190
      million in 1974), "Provincial bankers' clearing houses, 1897-1967" (abolished from 12 January 1968 but Liverpool's
      afternoon clearing; breaks 1943 Manchester restricted, 1945 Southampton); new "London Bankers' Clearing House at 1974
      prices, 1868-1974" (over the ONS long-run RPI: less in 1920 than 1913, 6.4 times 1938-1974 against 41 times in pounds
      of the time), in the banking trade story.
- [x] C5e2b2b2b3b2b (2026-10-28) Savings banks 1939-1975, by nation, and the credit clearing (new `bidb/change_savings_post.py`,
      read by bidb.change_savings): the Annual Abstract's "National savings" tables read from the page images of Nos. 86, 88,
      92, 96, 99, 104, 108 and 112 (`savings_banks_annual_uk.csv`, 2,728 printed figures; receipts, repayments and interest
      in years ended 31 March, amounts remaining invested at 31 March); every printed total checked against its parts, each
      savings bank's amount against the year before and the year's movements (within £1 million but the Eire banks in 1942,
      Service release benefits 1946-1949 and eight years the footnotes do not explain, `UNBALANCED`), the savings-bank
      figures of overlapping editions equal but twenty revisions (`REVISED`). "Savings banks: amount due to depositors"
      extended to 1846-1975 (break 1939: at 31 March from then; the trustee banks' departments printed together 1939-1948,
      their lines start again in 1949): the Post Office £1,981 million at its height in 1947, £1,475 million in 1971; the
      trustee banks' two departments passed the Post Office's ordinary accounts in 1965 and held £3,669 million in 1975. New
      "Savings banks by nation, 1846-1898" (England and Wales, Scotland, Ireland; trustee banks and from 1863 the Post Office;
      log axis) and "London credit clearing, 1961-1974" (breaks 1970, mergers, and 1971, BACS transfers left out, both
      quoted from the footnotes of Nos. 111-112), in the banking trade story. No account counts after 1938 (not in these
      tables); the other national savings (certificates, bonds, SAYE) are in the CSV for the checks, not drawn.
- [x] C5e2b2b2c (2026-10-28) Patents in Ireland 2000-2025 (new `bidb/change_patents_ie.py`): every English annual report of
      the Patents Office / IPOI 2002-2025 (24 PDFs, born-digital, read from their text) → `patents_ipoi_reports_ie.csv`
      (511 printed figures, one per row with report, PDF page and table or text): national applications and grants
      (full and short term, each report its year and the two before), applications from the State, European patents
      granted with effect in Ireland. Checks: every total against its parts, every figure printed twice equal but eight
      (`KNOWN`: three State counts revised by the next report, the 2015 report's 289 against its own chart's 250; three
      text figures unlike their table; the 2014 report's Irish-language page swapping the grant columns), every year
      present. Graphs "Patents in Ireland, 2000-2025" (1,169 applications in 2001, 206 in 2022; 774 in 2024 with the
      applications from China), "Patents with effect in Ireland, 2001-2025" (log axis: 7,922 European patents in 2001,
      135,374 in 2019, against the Office's 110 in 2025) and "Irish patent applications by term, 2001-2025". The site
      reserves all rights: figures cited one by one (source `ipoi_annual_reports`).
- [ ] C5e2b2b2c2 Patents in Ireland 1927-1999 (blocked, checked 2026-10-28): the Controller's annual reports since 1928
      are not online (Internet Archive: none), the Statistical Abstract of Ireland's patent tables are not in the CSO's
      CEPH tables (PxStat has none on patents), and WIPO's statistics (1980-) may not be republished. Needs scans of the
      reports or abstracts (National Library of Ireland), or WIPO's leave.
- [x] C6 (2026-10-25) Innovations: 36 inventions, discoveries and firsts made in the isles, 1701-1996
      (`data/curated/trade/innovations.json`, list `innovations` of bidb.oldest_lists, seven categories: power and
      engines, iron and materials, textiles, transport, communication and computing, science and medicine, farming,
      money and everyday life), each placed where it was made, tried or first used and cited with exact quotes (all 45
      found by `bidb.evidence --check`; 5 left "open" where the date or place needs a better source, rivals named in
      the notes); new place group "Innovations & firsts" (💡, colour 23) on the map, the Places page and the slider;
      `made_at` linked to the building or place (Cromford Mill, Hall i' th' Wood, the Iron Bridge, Cragside, St Mary's
      Hospital, Bletchley Park, Penydarren Ironworks, Birr Castle, Maynooth...; 15 of 36) shown as "Made or first used
      at"; section on the Oldest page.
- [x] C6b (2026-10-27) Wikidata inventions in the isles (new `bidb/innovations_wd.py`, run with bidb.oldest_lists):
      the narrow query (inventor P61 + place of discovery P189 or creation P1071 in the isles, no class tree) takes
      seconds on QLever. Wikidata places few: of ~580 items with an inventor and any isles place, 16 are kept: a place
      with its own coordinates (hydrogen, nitrogen, sodium and others are placed only at "United Kingdom"), not a
      find, fossil or museum object, not one of the 36 researched; 2 reviewed out (`SKIP`: "mechanical computer" is
      the general class; Salter's duck is placed at Coventry, it was devised at Edinburgh). Kind "Invention or
      discovery (Wikidata)" in Innovations & firsts (iridium 1803, barium at the Royal Institution 1808, Babbage's
      engines, Daniell cell, quaternions at Broom Bridge 1843, mauveine, traffic light, electron, xenon, proton,
      neutron, Turing machine, Hamilton scale, Pedersen bicycle, Fisherman's Friend); 10 linked to their place. The
      electron, proton, neutron, xenon and Hamilton scale had been filed under Finds & treasures (places_build takes
      anything with P189 as a find): this stage replaces those rows. Marked "Wikidata statements, not checked".
- [x] C7 (2026-10-25) Laws and institutions: 25 dated events in `change/events.json` (`topic: law`, a `trade` tag
      read by the trade stories: wool, trade, work, tea, banking, slavery, farming, cotton), each cited with an exact
      quote from its Wikipedia article (all 25 checked present when written): the Weavers' charter 1155, Carta
      Mercatoria 1303, Statute of Labourers 1351, Ordinance of the Staple 1353, Statute of Artificers 1563, East India
      Company 1600-1874, Navigation Acts 1651-1849, Bank of England 1694, Liverpool's first slave ship 1699, Bristol's
      slave trade 1700-1807, the Union of 1707, Bubble Act 1720-1825, Inclosure Act 1773, Combination Acts 1799-1824
      and their repeal, Slave Trade Act 1807, Corn Laws 1815-1846, Slavery Abolition Act 1833 and the £20 million paid
      to slave owners (Legacies of British Slavery named, not used as data), Factory Act 1833, Tolpuddle 1834,
      Rochdale Pioneers and the Joint Stock Companies Act 1844, Limited Liability Act 1855, TUC 1868, Big Bang 1986.
      Shown with the other events on "Change over time" (theme Prosperity and work).
- [x] C7b Borough charters and guild charters beyond London as events or places (Wikidata "town charter" dates are
      sparse; the guilds list of C3b holds the oldest guilds already). Split 2026-10-28: C7b1 Ballard 1913, C7b2
      Ballard and Tait 1923, C7b3 the 1913 appendix (all done).
- [x] C7b1 (2026-10-28) Borough charters 1042-1216 (new `bidb/change_charters.py`): the table of sources of Adolphus
      Ballard's British Borough Charters 1042-1216 (1913, public domain; Introduction section 4, pp. xxvi-xxxiii) read
      from the page images (Internet Archive, leaves 32-39) → `charters_ballard_1913.csv` (310 printed rows, 323 charters
      to 145 printed boroughs, sokens and gilds; Ballard's typeface kept: capitals = Domesday borough, italics = founded
      by a lesser lord). Checks: every date read, ranges in order, one typeface per borough, every borough placed on a
      GeoNames town (renamed or ambiguous ones by hand: Appleby-in-Westmorland, Hythe in Kent, Richmond in Yorkshire,
      Kells in Meath and Kilkenny, Rathmore in Kildare, Great Yarmouth...), 323 against the preface's "about 330" (the
      rest are in the appendix). Map layer "Boroughs by their first charter" (137 towns, following the slider: London
      1043, 43 by 1160, 125 by 1210) and graph "Borough charters per decade, 1040-1219" (kings 234, lay lords 63,
      bishops, abbots and popes 26; the 1200s busiest with 81; 99 royal grants are King John's: first written as 100,
      John fitz Robert's Corbridge charter wrongly counted, corrected in C7b2), theme People and settlements. The book's appendix (additional charters) and its code of clauses are not read.
- [x] C7b2 (2026-10-28) Borough charters 1216-1307: the table of sources of Ballard and Tait, British Borough Charters
      1216-1307 (1923, public domain; pp. xxv-xxxvi, Internet Archive leaves 33-45) read from the page images →
      `charters_ballard_tait_1923.csv` (532 printed rows to 214 places), joined to C7b1 in `bidb/change_charters.py`:
      the Barnard Castle (Hugh de Balliol) and Rathmore charters printed again with new dates count once, at the 1923
      date; Oxford University "1301 (b)" at 1305 as the footnote says; "Do." under a king of another reign written as
      the king of the date (Stafford, Stamford, Dublin). Graph "Borough charters per decade, 1040-1309" (replaces
      the 1040-1219 one; break at 1216 where the volumes meet; 853 charters to 260 towns: kings 617, lay lords 173,
      church 51, 12 with no grantor printed or the townspeople's own not drawn; Henry III 235, Edward I 117; busiest
      decade the 1250s, 113, 43 of them dated 1256, with Tait's note that the Charter Roll of 1255-6 is lost) and the
      layer to 1307 (258 towns, 121 first after 1216; Rathcool, "co. Tipperary", and the Cinque Ports as a body not
      placed; lost towns placed by hand: Ravenserod, Warenmouth, Skinburness for Skynburgh and Wavermouth, Nova
      Villa at Newton in Studland, Bere).
- [x] C7b3 (2026-10-28) Ballard 1913's appendix of additional charters (p. 250, leaf 404; "Some additional Charters
      will be found in the Appendix", p. xxxiii n. 1): 8 charters (Aberdeen, Christchurch, Devizes, Hartlepool,
      Newport and Yarmouth in the Isle of Wight, Torksey, the York weavers) → `charters_ballard_1913_appendix.csv`,
      counted with the first volume (331 printed against the preface's "about 330"); the one-typeface check runs per
      printed table (Hartlepool roman in the table, italics in the appendix). Rathcool placed at Rathcoole, co. Dublin:
      its charter 1228-56 (a) grants the burgesses "de Radcull" common "in monte de Slescoll", the grant Lewis 1837
      quotes under Rathcoole. 861 charters to 261 towns; layer 260 towns (Torksey and Rathcoole new). The Addenda
      (pp. 255-259) add texts to charters already in the table and reject John's Waterford charter: nothing to add.
- [x] C8 (2026-10-25) Trade stories: page `/trades` (nav "Trades"; hosted `trades.html` from `data/trades.json`), one
      story per trade (wool and cloth, tea, sugar and slavery, cotton, linen, coal, iron and steel, fishing, brewing and
      distilling, banking and finance) from `data/curated/trade/stories.json` and new `bidb/trade_stories.py`: intro,
      timeline (the C7 events by `trade` tag, the tea events, the C6 innovations), map and lists of its places (by kind,
      or whole-word name matches in trade-related groups) and catalogue buildings, the people linked to them, graphs of
      Change over time, and a cited analysis note per trade with exact quotes (all 30 checked against the articles):
      the wool churches and enclosure; tea, sugar and the "industrious revolution"; Williams's Capitalism and Slavery
      thesis and its critics (Engerman, Richardson) and defenders (Carrington); the Cotton Famine (war or
      overproduction); Belfast's linen and the Atlantic; Jevons's Coal Question; nationalised steel; herring towns;
      taxing drink (gin, whisky); railway mania and Overend Gurney.
- [x] C9 (2026-10-25) GUI for trade, enterprise and innovation: Change over time links to the trade stories (a line of
      links, "<trade> story" on each law event and each graph a story uses; `index` gives tags and graphs); detail
      views of buildings and places show "Trade and industry here" (the stories a record belongs to, the innovations
      made or first used there; `trade_stories.here`, `/api/trade_here/<id>`, `static/trade_here.js`); the Map page has
      a "Trade" select and `?trade=<id>` ringing the trade's places and buildings, linked from each story; the Oldest
      page lists the innovations (C6); quiz "Which came first?" (innovations and trade laws, `quiz_api.firsts`); Export
      on the Trades page saves the story's places and buildings (CSV, JSON, GeoJSON, KML) and its timeline; Help
      section "Trades and industries" with figures `trades.jpg`, `trade_here.jpg` (`docs/make_figures.mjs`);
      INTERFACE updated. Hosted copy: `trades.json` (0.6 MB) with `here`, static routes for all three APIs.

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
- BT1 Research the classification: a hierarchy (domain → family → type → variant, e.g. Domestic → Hall houses →
      Wealden house → "recessed-hall" Wealden), built on the FISH thesaurus of monument types (OGL) and Getty AAT,
      with periods of use (first known, flourishing, last built), regions, materials, structural system, plan form,
      the earliest surviving example in the catalogue, and the sourced "descended from / influenced by / replaced by"
      links (lineage, borrowing from abroad, convergence: similar forms with separate origins). Licence check first.
      Split 2026-10-25:
- [x] BT1a (2026-10-25) Licence check and the thesaurus (`data/curated/building_types/README.md`): FISH Thesaurus of
      Monument Types v29 is OGL v3.0 (stated in the scheme's own RDF at heritagedata.org), Getty AAT ODC-By 1.0;
      Historic England's publications are not stated as OGL and its site refuses scripts (cite with page, short
      quote). New `bidb/fish_types.py` reads the yearly CSV release (cached in `<cache>/fish/`, Building Materials
      and Components too, for BT3): 5,105 preferred terms, 3,192 non-preferred, 18 top concepts, 848 terms under
      more than one broader term (by function and by form: Wealden house has six paths). Catalogue classes matched
      by label alone: 18,638 of 27,400 uses (68.0%); the misses are synonyms and Wikidata-only classes ("built
      structure", "terrace house", "English country house"): BT2's alias table. Wikidata P14369 (FISH id) is on only
      172 classes so far.
- [x] BT1b (2026-10-25) First families with sourced links (new `bidb/building_types.py`,
      `data/curated/building_types/lineage.json`): houses (round houses, longhouses, hall houses, chimneyed houses,
      manor and country houses) and defence (castles, fortified houses and towers, artillery fortification), 33 types
      (5 abroad: Renaissance architecture of the Continent, crusader and Byzantine castles, the trace italienne, the
      Genoese tower at Mortella) and 29 links: descent 11, variant 7, influence 6, replacement 3, convergence 1
      (longhouse and bastle: animals and people under one roof "for different reasons"), revival 1 (Scottish
      baronial); documented 21, probable 5, disputed 3 (rounds and the Severnside shell keeps; crusader castles and
      the concentric plan; the Irish tower house from the hall house, Finan, or from Scotland). 76 quotes (Wikipedia,
      FISH scope notes, one Suffolk HER entry), all found by `python -m bidb.building_types --quotes` (using
      `evidence.check`, which now takes `claims` and `path`). The lobby-entry house from the hall house is "probable":
      sources describe chimneys inserted by the cross passage and single conversions (85 Church Street, Lavenham),
      none the descent of the type as a whole.
- BT1c The other families, split 2026-10-25 into BT1c1–BT1c3:
- [x] BT1c1 (2026-10-25) Religious and agricultural (`lineage_religious.json`, `lineage_agricultural.json`, read
      with lineage.json by `building_types.load`): 32 types, 28 links, 94 more quotes (170 in all, all found).
      Roman basilica → church; minster → parish church (disputed: the minster hypothesis, Blair vs Cambridge and
      Rollason), → collegiate church, → monastery (replaced in the Benedictine Reform, continental houses an
      influence); chapel of ease → parish church; round-tower churches (flint) vs Irish round towers (convergence);
      abbey → cathedral (monastic cathedrals, almost only in the isles); clochán → Gallarus-type oratory (probable);
      Commissioners' and ecclesiological churches as revivals; aisled barn → barn → threshing, cruck, bank, hay
      barns and the oast house; threshing barn → gin gang (1786-1840); dovecote after castle nest-holes (probable;
      Roman or Norman introduction disputed); longhouse and laithe house (convergence, probable).
- [x] BT1c2 (2026-10-25) Commercial, industrial, transport (`lineage_commercial.json`, `lineage_industrial.json`,
      `lineage_transport.json`): 63 types (7 abroad), 46 links, 135 more quotes (305 in all, all found; Wikipedia
      locators checked against the section each quote stands in). Alehouse → public house, gin palace → pub (the
      bar counter), inn → coaching inn, drovers' inn, hotel → railway hotel; coffee house → stock exchange
      (Jonathan's, 1773); Antwerp bourse → Royal Exchange; market cross → buttercross, market house → market hall
      → cloth hall; shop → department store, → bank (goldsmith bankers, probable). Roman watermills → watermill →
      tide mill (Nendrum 619), fulling mill, cotton mill; post mill → tower mill (replaced) → smock mill; Piedmont
      → Lombe's silk mill → Arkwright's cotton mill → fireproof mill (Strutt, Ditherington); weaver's cottage →
      weaving shed; bloomery → blast furnace (Wallonia, 1491); pottery kiln → bottle kiln → gas tunnel kiln (Clean
      Air Act 1956); brick kiln → Hoffmann kiln. Stepping stones → clapper bridge (probable); arch bridge →
      packhorse bridge → turnpike (replaced), → Iron Bridge; ships' chain cable → suspension bridge (Union Bridge
      1820); Roman aqueducts → railway viaduct; flash lock → pound lock (Exeter 1560s); river navigation → canal
      (probable), canal and turnpike → railway (replaced); wagonway → railway; railway station → railway hotel.
      Disputed: the vertical windmill from Persia, the shopping arcade from Paris. Not yet researched: the factory
      as a type, ironworks beyond the furnace, the parts of a station (train shed, goods shed, engine shed).
- BT1c3 Civic, education, health and welfare, recreational; periods of use (first known, flourishing, last
      built) for every type; structural system and plan form where the sources give them. (The earliest catalogue
      example per type needs BT2's mapping and moves there.) Split 2026-10-25:
- [x] BT1c3a (2026-10-25) Civic, education, health and welfare, recreational (`lineage_civic.json`,
      `lineage_education.json`, `lineage_health.json`, `lineage_recreation.json`; four research agents in parallel,
      each file reviewed): 96 types (8 abroad), 80 links, 288 more quotes; all 224 types and 183 links now, 593 of 593
      quotes found. Moot → moot hall, market house and tolbooth → town hall, castle → county gaol, Eastern State
      Penitentiary → Pentonville, lock-up → police station; cathedral school → grammar school → public school, Bell's
      Madras system → National and British schools, academic hall → college, mechanics' institute → university and
      public library, subscription library → public library → Carnegie library; monastery → medieval hospital →
      almshouse, leper house → almshouse, Les Invalides → Chelsea and Kilmainham, Stonehouse → pavilion hospital →
      workhouse infirmary → municipal hospital, corridor → echelon asylum, parish → union workhouse → Irish
      workhouse; inn yard → playhouse, real tennis court → Restoration playhouse, pub and song-and-supper room →
      music hall → variety theatre → cinema, Roman baths → spa (revival), landing pier → pleasure pier. 17 disputed in
      all (8 new: guildhall origin, panopticon and Millbank, panopticon and the radial prison, Leach's chantry schools,
      quadrangle and cloister, hospital origins, the first cottage hospital and sanatorium, the inn-yard theory,
      Perran Round). Details and what was left out in `data/curated/building_types/README.md`.
- [x] BT1c3b (2026-10-26) Periods of use for all 224 types (six research agents, one or two files each, reviewed
      here): `period` {text, from (first known), flourish [from, to] (68 types), to (last built, 170) or ongoing
      (54)}, structure (66 types) and plan form (100) where a source states them for the type; each backed by a
      source marked `about` period / structure / plan, checked by `building_types.period_problems` (years in order,
      to or ongoing, a source for each). 850 more quotes: 1,443 of 1,443 found. The texts say what each year really
      is: many "to" years are the latest example a source names, or a law or end of use (Beerhouse Act 1869, NHS
      1948, the 1930 end of the workhouses), not a known last building; disagreements given in the text (cottage
      hospital 1818/1827/1842/1859, Wealden house 1380 vs a 1340 claim in an unreadable PDF, lobby-entry house
      16th vs late 17th century). Reviewed here: the canal from the Roman Foss Dyke (c. AD 120, no consensus), the
      grammar school ongoing (the 2017 Sevenoaks annexe the first new one in decades, not the last).
- BT2 Data: the curated `lineage*.json` files (types, links with kind and confidence, citations and quotes as
      the evidence file), checked by script; every catalogue record and place kind mapped to a type (the categories
      and Wikidata classes as a start), so each type shows counts, a map and the dated examples. Split 2026-10-26:
- [x] BT2a (2026-10-26) Records and places mapped (new `bidb/type_map.py`, build stage "Building types";
      `data/curated/building_types/aliases.json`) → table `type_map`: each Wikidata class by type name, alias, FISH
      concept or nearest broader concept that is a type's (most specific kept; `within_period` for 21 types whose
      FISH concept is wider than the type, `nations`); name rules on the head of the name within categories or
      kinds, categories, place kinds; name, category and kind matches only within a century of the type's period.
      10,805 of 22,508 records (48.0%) and 27,401 places typed, to 123 of 203 isles types; 438 leftover labels
      reviewed (`not_in_tree`). Details in `data/curated/building_types/README.md`.
- [x] BT2b (2026-10-26) Per type (new `bidb/type_stats.py`, `app/types_api.py`: `/api/types`, `/api/type/<id>`,
      `/api/types_of/<id>`): counts, dated examples, by nation and century, map points, the earliest surviving
      example (primary type first, catalogue before places, not demolished, not dated by a type estimate) and
      "too early" flags (begun over a century before the type's first known date: 521, reviewed; mostly later use
      of an older building or the site's first phase, some wrong classes; never the earliest). The 80 types with no
      example searched by name and description: 75 reviewed text rules in aliases.json (`texts`), register labels
      split at ";" and ":" → 174 of 203 isles types with examples (was 123), 152 with an earliest surviving
      example. Fixed on the way: "Republic of Ireland" in the nation limits, lifeboat and power stations typed as
      railway stations. Details in `data/curated/building_types/README.md`.
- [x] BT1d (2026-10-26) More types for what BT2a could not type. George's decision: prehistoric and Roman structures
      people built and used join the tree; single standing stones, rock art, carved stones and finds stay in the
      archaeology groups. Five research agents, one new file each, reviewed here (`lineage_prehistoric.json`,
      `lineage_houses.json`, `lineage_estate.json`, `lineage_settlement.json`, `lineage_general.json`): 87 types
      (311 in all), 126 links (309), 680 quotes, 2,123 of 2,123 found. `type_map`: general types give way to their
      forms (variant links), text and name rules refine general types and uses, uses of a building (`secondary`)
      rank after its own type, a FISH concept may map to several types; 19 aliases, 12 reviewed text rules →
      15,713 records (69.8%, was 48.0%) and 58,753 places typed; 247 of 285 isles types with examples. Details in
      `data/curated/building_types/README.md`.
- [x] Irish SMR dates (emergent 2026-10-26, found in BT2b; fixed 2026-10-26): tower houses, churches and wells in
      townlands named Rath... or ...cashel were dated 600: `places_build.estimate_dates` read the type estimate from
      the whole name, and SMR names are "class, townland". SMR places now use the class alone (other registers'
      names still count: "Skye, Dun Liath"); friars' houses ("Religious house - Dominican friars") now get the
      friary range. Applied to the database: 78 re-estimated (tower houses 1400, friaries 1224), 30 left undated;
      too-early type examples 521 → 504.
- BT3 Materials and techniques: stone (rubble, ashlar, flint, cob, clay lump), timber framing (cruck, box frame,
      jetty, close studding, wattle and daub), brick (bonds, from the 13th c. revival to the Victorian kilns), roofs
      (thatch, stone slate, slate, tile, pantile; roof trusses from crown post to king post), glass, iron and steel,
      concrete; each with dates, regions (the geology layer of the Change page says where stone came from), the
      technology that made it possible (brick tax, railways, Portland cement) and catalogue examples. Only 500 of
      22,508 records have a Wikidata material (P186), so split 2026-10-26:
- [x] BT3a (2026-10-26) The curated materials and techniques (`data/curated/building_types/materials_*.json`, five
      research agents, one file each, reviewed here; checked by new `bidb/building_materials.py`; FISH Building
      Materials and Components thesauri read by `fish_types.concepts(scheme)`): 99 materials and techniques (stone
      18, mortar and render 6, earth 5, timber 13, brick and tile 20, roofs 19, glass 8, iron and steel 5, concrete
      5; 73 with a FISH concept), 51 links (documented 39, probable 11, disputed 1: the brick tax and mathematical
      tiles), 151 named examples, 978 quotes, all found. Periods with regions, technology (brick, window and glass
      taxes, slate duty 1831, railways, patents) and geology; `earlier: true` where the first date is only the
      earliest a source names (6). Two duplicated cross-file links merged, one single-building link dropped.
      Details in `data/curated/building_types/README.md`.
- [x] BT3b (2026-10-26) Records and places linked to materials (new `bidb/material_text.py`, `bidb/material_map.py`,
      build stage "Materials" after the stories; `bidb/material_stats.py`; `data/curated/building_types/
      material_aliases.json`) → table `material_map` with the matching sentence as evidence: Wikidata P186 (59 material
      items mapped, 41 left out as too general), cached HES/Cadw/NIAH register descriptions, cached Wikipedia articles,
      by 95 reviewed term rules (cue words near ambiguous terms, fittings, kilns and quarries dropped). 8,477 of 22,508
      records (37.7%) and 2,352 places, 24,957 links to 92 of 99 materials; about 28 of 30 sampled text links right.
      Per material: counts by source, nation and century begun (`by_century`, for BT5), "too early" links (901: later
      phases), earliest example begun in or after the material's first date (90). Details in the building types README.
- [x] Catalogue dates mined from quantities (emergent 2026-10-26, found in BT3b; fixed 2026-10-26): new
      `bidb/date_recheck.py` dates the text-mined records of the existing database again with the build's own
      `date_fill` step from the cache. `date_mining`: a bare number under 1000 is a year only after "c.", an era or
      an introducing word ("the remaining 600", "400 megawatts", "500 cavalrymen" are not); thousands separators,
      ordinals, "900-year-old", "between 600 and 1,000 years old", grid references and more units left out; life
      dates "(d. AD 637)", "(b. 1270)" skipped; no sentence break after "d.", "b.", "c.", "fl."; "c1460", "AD 75",
      "510±70 BC", "the 550s"; "mid-15th century" had stopped matching (the look-behind sat after the qualifier's
      hyphen) and "early-mid"/"mid to late" keep the first qualifier; "Grade I listed" no longer counts as the skip
      word "listed". Register text: "l8th"/"l851" (scanned l for 1) and "of C14" → "of14th" (normalise ate the
      space). NIAH: two records in only through a lost digit ("188–1840", "820–1825") left out and removed. 156
      dates changed (Liverpool Street, Battersea, Waterloo Bridge, Banff's "l8th century" houses dated 701, the
      Churchill Barriers' lengths...), each reviewed; 25 dates the miner still gets wrong (the article's earliest
      date is of something else) added to `date_corrections.json` with quotes (206 entries; St Seachnall's undated,
      `year_start: null`). Timeline table rebuilt (45,805 events).
- [x] Seven new date-check conflicts (emergent 2026-10-26, reviewed 2026-10-28; `docs/date_review.md`, third review):
      against the list descriptions and article bodies, four corrected (Ston Easton church 11th century, Bradeston
      13th century, Sheffield Cathedral c. 1430, Ormesby Hall c. 1600 from its own entry 1311002, not the stable
      block's 1139662 that `bidb.listings` matched) and three kept (Antony 1259, Hart 675, Woodchester 2nd century).
      Conflicts 7 → 0; 262 reviewed.
- [ ] `bidb.listings` takes Ormesby Hall's list entry from Wikidata, which points at the stable block (found
      2026-10-28): check how many records' NHLE ids are those of an outbuilding.
- [x] Clackmannan Tower (emergent 2026-10-26, seen in BT5's spread chart; fixed 2026-10-26): year 1301 with the date
      text "Late 14th century". `dates.parse_text_year` (Wikipedia list dates, hoards, research claims) ignored
      qualifiers; it now reads them as the text miner does (`dates.century_start`, shared: mid +33, late or second
      half +50, the first qualifier counts). `bidb.date_recheck` reads list dates and hoards again: 6 records
      (Clackmannan and Crichton 1351, Lauriston 1251, Oxford Castle 1034, Glasgow Cathedral 1134; Culross Abbey's
      list date no longer earlier than Wikidata's, so 1217) and 43 hoards; Sketrick Castle kept (confirmed date).
- [x] Register-period dates as earliest examples (emergent 2026-10-26, seen on the /types tree; fixed 2026-10-26):
      `type_stats.estimated` now counts "(register period)" dates (8,800 HES, Cadw and NI places, whose year only
      stands for the period, `registers.period_year`) as estimates, so they are never a type's earliest surviving
      example, and `too_early` no longer flags them (108 of 808 flags were such years: 70 duns, 13 brochs at -2000).
      Seven types changed: round-house, longhouse, fulling-mill, pottery-kiln and cursus now have no earliest
      example (220 → 215 types with one); lock-up 1650 → Former Lockup 1823; railway → Waterloo & City line. Reviewing
      them found railway lines untyped: two text rules on the name for kinds `in_rail`/`ino_rail` (signal boxes left
      out) type 198 lines as railways from 1825 and 9 before it as wagonways (Wollaton 1604, Tanfield 1725, Middleton
      1758…, the curated periods with `slack: 0`); the Waterloo & City line was dated 1864 (another company's line)
      and is now 1894 (a reviewed date correction, quote found in the cached article).
- [x] Earliest railway is a catalogue record of 1894 (emergent 2026-10-26, fixed 2026-10-26): for a type with more
      places than records, `type_stats.earliest` now ranks its places of the structure groups (Military heritage,
      Infrastructure & utilities, Bridges, Maritime heritage, Underground) dated to the year with the records
      (`structure_place`). Railway → Stockton and Darlington Railway 1825, Martello tower → Dymchurch 1805, polygonal
      fort → Fort Brockhurst 1858. Hospitals, fire stations, theatres and works left as they were: their places carry
      the founding date of the organisation (Manchester Royal Infirmary 1752, Carron Company 1759), not the building's.
- [x] Tramways, funiculars, cliff lifts and inclines (emergent 2026-10-26, done 2026-10-26): six types in
      `lineage_transport.json` with sourced periods and structure (47 quotes, all found): plateway 1787-1830, street
      tramway 1860- (Birkenhead; Glasgow closed 1962; Metrolink 1992), funicular or cliff railway 1875- (one type:
      most British funiculars are cliff railways), railway inclined plane 1796-1974, canal inclined plane 1777-1900,
      signal box 1843-; seven links (wagonway → plateway → railway, wagonway ⇢ street tramway, railway → funicular,
      railway incline ⇢ funicular, pound lock → canal incline, railway ⇢ signal box). Text rules and register labels
      (Cadw "Tramroad", "Incline") type 434 places: 370 signal boxes, 22 funiculars, 20 plateways, 14 railway and 4
      canal inclines, 3 street tramways. Left out on review: railway stations and tram stops whose articles mention a
      tramway, the Lickey Incline (a locomotive gradient, never rope-worked), a proposed light railway, a target railway.
- [x] Tramroad bridges untyped (found 2026-10-26, done 2026-10-26): wider than found: 980 bridge places had no
      type (597 railway, 169 aqueducts, 91 swing or bascule, 121 early crossings) because their kind labels match no
      class. Bridge kinds now default to the general bridge type (`place_kinds`), and four new forms with sourced
      periods (35 quotes, all found): canal aqueduct 1761- (Barton; no FISH concept of its own), swing bridge 1786-,
      bascule or lifting bridge 1786- (canal lift bridges, drawbridges; Tower Bridge 1886-94; Gull Wing 2024),
      transporter bridge 1905-1917. Kind labels ending "(gone or closed)" were not read either (`type_map.CLOSED`):
      95 closed schools and 21 bridges typed. Left out on review: pipe bridges, Loch Katrine water aqueducts, the
      New River's Flash Road aqueduct, the River Wey aqueducts.
- [ ] Wikidata classes Bingley Five Rise Locks as a "canal inclined plane" (found 2026-10-26; a staircase lock rule
      types it a pound lock); fix at source with the other Wikidata errors.
- [x] FISH scope notes cut short (found in BT4a, fixed 2026-10-26): `glossary.ADVICE` matched "use with" inside
      "house with" (case-insensitive, no word boundary), so 52 notes (Wealden house: "A medieval ho") were cut on the
      Glossary page too; now case-sensitive at a word boundary.
- [x] Generic stones for BT3 (emergent 2026-10-26, done 2026-10-26): new `materials_stones.json`, 15 entries with
      sourced periods, regions, technology and geology (127 quotes, all found): sandstone (from Coldrum's sarsens,
      3980 BC), limestone (West Kennet, 37th century BC), granite (Brownshill dolmen), marble (Fishbourne, 75),
      chalk and clunch (Hyde Abbey 1110), whinstone (St Giles' 12th century), Coade stone 1769-1840, Magnesian
      Limestone, sarsen, York, Reigate (to the 1960s), Ketton, Ancaster, Heavitree (c. 1350-19th century), Hopton
      Wood (1687-2006); 23 links: variants from limestone, sandstone, granite and marble to the 19 named stones, Coade
      stone replaced by cast stone (probable). Materials marked `general` give way to their named variants in
      `material_map` (`general_of`: a Bath stone church is not also limestone; rubble/ashlar and slate/Welsh slate
      still both kept). 17 Wikidata P186 items moved from `not_in_list`; text rules with reviewed exclusions (marble
      fittings, fonts and monuments, limestone landscapes, York stone paving, hill figures). Result: sandstone 1,874
      links, limestone 570, granite 505, marble 145, whinstone 96; records linked 8,475 → 8,879, places 2,352 → 2,621.
- [x] Marble's earliest example was Chester Roman Amphitheatre, from a sentence about its recreation in a modern mural
      (found 2026-10-26, fixed 2026-10-28): `skip_sentence` in material_aliases.json now also drops sentences about
      murals, recreations, artist's impressions and reconstruction drawings, from any source. Earliest now Canterbury
      Cathedral (Purbeck marble shafting; dated by the founding, the known later-phase limit); records linked to
      materials 8,879 → 8,875.
- [ ] Hopton Wood stone has no examples (found 2026-10-26; its P186 items are memorials of skipped kinds). Greensand,
      ironstone, lias, Bargate stone, Pennant sandstone and Collyweston still have no entry (P186 and text mentions).
- [x] BT3c Materials on the detail views and type pages (with BT4); a material's region drawn over the geology
      layer. Split 2026-10-26: BT3c1 (materials on the detail views, the type pages and a material page of their
      own) is done with BT4a (2026-10-26); BT3c2 done 2026-10-26.
- [x] BT3c2 (2026-10-26) A material's bedrock on its page's map (new `app/static/types_geology.js`): the period layer
      alone could not do it (it dates granite by when it cooled: Dartmoor is "Carboniferous", Aberdeen "Ordovician"),
      so the BGS 625k bedrock (OGL, 16 MB zip in `<cache>/bgs625k/`) was dissolved once by period range and the kinds
      of building rock each unit names (`data/curated/change/layers/prepare_rocks.py` → `rocks.json`, 1.3 MB: limestone
      and dolostone, chalk, sandstone, mudstone/pelite/slate, felsic intrusions, dolerite and basalt; UK, as BGS 625k
      includes Northern Ireland). 25 materials name their rocks (`rock`, validated: `building_materials.ROCKS`; [] for
      Caen stone, quarried abroad). Drawn within the material's curated periods (any of a unit's periods, so the Lias
      Group, Triassic to Jurassic, counts for Bath stone), igneous kinds at any age; Ireland by period only (its layer
      has ages only); materials with periods and no rock (sarsen, Lake District slate) by period. The caption counts
      the examples standing on it, of those on land the layers cover: Cotswold stone 81%, gritstone 72%, chalk 71%,
      limestone 43%, Bath stone 30%, granite 20%, Portland stone 5% and Welsh slate 2% (both carried far).
- [x] Ireland's rock kinds for BT3c2 (found 2026-10-26, done 2026-10-27): the GSI/GSNI 1:500k shapefile (CC BY 4.0 /
      OGL, 7 MB, `<cache>/gsi500k/`) names each unit's rocks in plain words; `prepare_rocks.py gsi` reads them with the
      same six kinds (whole words; gneiss, schist, quartzite and meta-dolerite left out as BGS's metamorphic rocks are,
      rhyolite as a lava; age brackets kept as period ranges) → `gsi500k_bedrock_rock.geojson` (3,257 polygons → 33
      features, 495 KB), merged into `rocks.json` (1.3 → 1.7 MB). Materials with rock kinds are now drawn on rock
      in all Ireland, no longer by period there: limestone 43% → 51% of 546 mapped examples.
- [ ] Lake District slate (volcanic green slate and Silurian blue-grey) and sarsen (silcrete) have no rock kind of
      their own (found 2026-10-26); Kilkenny marble has no examples yet (no P186 items or text matches).
- [x] BT4 The page `/types`: a browsable tree (cladogram-style, collapsible, with a time axis so each branch spans
      its years; solid lines for documented descent, dashed for disputed), a type page per type (definition, how to
      recognise it, features, materials, plan, period chart, map of examples, the oldest surviving, family links,
      sources), and a search; reachable from detail views ("This is a Wealden house: see its family").
      Split 2026-10-26: BT4a the local page (done), BT4b the hosted copy's /types (with BT7).
- [x] BT4a (2026-10-26) The page `/types` in the local GUI (new `bidb/type_pages.py`, `app/static/types_tree.js`,
      `types_view.js`, `types_page.js`, `types_here.js`, `types.css`; five endpoints in `app/types_api.py`): the
      family tree on the Map slider's time axis, 285 isles types and 26 abroad in 14 domains, bars for the period of
      use (thick while flourishing), a dot for the earliest surviving example, the 309 links as branches at the later
      type's first date (colour by kind, dashed disputed, faint probable; links between domains only on hover), folding
      families, domain chips, search; a page per type (FISH definition, period, structure, plan, materials curated and
      found in its records, family links with claims, views and quoted sources, earliest surviving example, begun per
      century and by nation, map, dated examples) and per material (BT3c1); detail views say "This is a Wealden house:
      see its family" and list the materials with the sentence that names them. Nav link hidden in the hosted copy.
- [x] BT4b (2026-10-26) The hosted copy's /types (new `app/static_types.py`, `app/static/static_types.js`): the tree,
      the "Through time" tab, every type and material page and the detail views' types and materials, from 21 compact
      files (5.8 MB: catalogue records named by id and filled in from the rows the browser already holds, places as
      short arrays, place map points as integer steps of 1/1000°, family links stored once; 40 examples per type and 25
      per material with evidence cut to 200 characters; place dots link to the Map page; no evidence sentences in the
      detail views). Room made without losing anything: tour route lines simplified to ~4 m (3.2 → 2.1 MB), common link
      starts of places encoded (`URL_PREFIXES`, the Irish SMR viewer link alone 127 characters × 13,425 places) and
      4,293 register texts that only say there is no description left out. Hosted copy version 74: 253.0 MiB, 487 files.
- [x] BT5 (2026-10-26) Charts (new `bidb/type_charts.py`, `app/static/types_time.js`, `/api/material_centuries`):
      tab "Through time" on /types (`?tab=time&year=`): types in use per domain at each date (an area per domain on
      the Map slider's axis, from the curated periods; a year to choose lists the types in use then, 79 in 1300, and
      "Show the map at this year" opens /map?year=, which now switches the slider on there), materials by century
      begun (91 materials, rows shaded against their own busiest century, first known date ticked, too-early records
      left out); on each type page the spread across the isles (counties with a dated example by each date, step
      chart, first example per county: motte and bailey 63 counties, tower house 40) and "what came before and what
      came next" (lines of descent, replacement and revival, no type twice; forms without lines of their own show
      their general type's: Wealden house → hall house's; 207 of 311 types have lines). Century-only dates gather at
      1001, 1101… in the spread chart (said under it). Local GUI only (hosted with BT4b).
- [ ] BT6 Generated examples (George's building-gen, `~/Documents/GitHub/building-gen`, MIT, own project: procedural
      glTF buildings from period-correct construction rules; 4 of its 29 researched types implemented: Georgian
      townhouse, Victorian terrace, cottage, medieval tavern). First check its accuracy against the sources and the
      catalogue's floor plans; use it only for types it renders faithfully, labelled as an illustration, not a
      record. Shown as a 3D viewer (three.js, cut-away and exploded views, plan and section) or pre-rendered images
      for the hosted copy; more types added in building-gen itself (its repo), not copied here. Where a generated
      example would be guesswork, use labelled diagrams (plan, section, elevation drawn as SVG) and Commons
      photographs and floor plans of real examples instead.
      Split 2026-10-28: BT6a the check (done), BT6b plans of real examples (done), BT6c labelled diagrams, BT6d
      generated examples once building-gen passes the checks.
- [x] BT6a (2026-10-28) building-gen checked against the sourced plans and structures of the catalogue's types
      (`docs/building_gen_review.md`): none of its four types is shown yet. One style ("georgian", brick) for every
      type; modern fittings (washing machine, fridge, sofa, fitted bathrooms) in every period; 3D views are boxes
      with the roof beside them. Georgian townhouse: a near-square 12 × 12 m plan with a 50 m² ground-floor dressing
      room; the detailed 1763 façade has its chimney stacks across the windows and a street-facing gable instead of
      a parapet. Victorian terrace: right in outline, but a full-width outshot (no yard), an indoor bathroom where
      the source has a privy. Cottage: two up two down, but no ground-floor windows and brick. Medieval tavern: a
      brick double pile with no courtyard or stables, where the sourced inn is timber-framed round a court. The
      catalogue has no plans of these types to compare (two townhouse plans, both before 1650).
- [x] BT6b (2026-10-28) "Plans of real examples" on each type page: up to 12 catalogue records of the type with a
      Commons floor plan (the type's own records first, too-early ones last, then oldest first), thumbnails from
      Commons with the record and file page; links only in the hosted copy (`type_pages.plans`; 61 types have one,
      castle 123, country house 53, church 49).
- [x] BT6c1 (2026-10-28) Labelled diagrams (plan, section, elevation as SVG) on the type pages: 22 diagrams of 22
      types (hall house, Wealden house, longhouse, blackhouse, bastle, lobby-entry and double pile houses, byelaw
      terrace, back-to-back houses, cottage, Roman villa; motte and bailey, ringfort, promontory fort, henge, long
      barrow, passage, court and wedge tombs, pound lock, market house, Martello tower) as shapes in
      `data/curated/building_types/diagrams_*.json` (`bidb.type_diagrams`, `types_diagram.js`). Every label must
      be found word for word in a quote of the type's sources on its plan or structure, so a diagram names nothing
      its sources do not; each lists the quotes it is drawn from and a note of what is schematic (proportions, roof
      outlines, rooms the sources do not name). Martello tower and ringfort drawn to their quoted sizes.
- [ ] BT6c2 Commons plans of real examples of types the catalogue has none for (terraces, cottages, inns: Commons
      categories "Floor plans of houses in …"); more diagrams where a type's plan has a quoted source (tower house,
      tenement, almshouse, union workhouse, panopticon, Elizabethan playhouse, need quotes on their plan first).
      Split 2026-10-28: BT6c2a plans of typed places (done), BT6c2b more diagrams (done); BT6c2c the rest.
- [x] BT6c2b (2026-10-28) 13 more labelled diagrams from the plan quotes the types already had (no new research):
      threshing barn, bank barn (section into the slope), laithe house, shell keep, concentric castle, gatehouse keep
      (Tonbridge style), tower keep (square and twice-as-long), separate-system prison, panopticon, monitorial
      schoolroom, Kempthorne's square union workhouse, pavilion hospital, tholsel (`diagrams_castles_farms.json`,
      `diagrams_institutions.json`); every label found in a quote (`bidb.type_diagrams`: 35 diagrams of 35 types, no
      problems); notes say only what is schematic (first drafts named Pentonville's five wings and Kilkenny's arches,
      which no quoted source gives: taken out).
- [ ] BT6c2c Commons plans from generic categories ("Floor plans of houses in …") for terraces, cottages and inns;
      diagrams for tower house, tenement, almshouse, Elizabethan playhouse once their plans have quoted sources.
- [x] BT6c2a (2026-10-28) Plans of typed places (new `bidb/place_plans.py`, build stage after type_map → table
      `place_plans`): of 48,537 typed places with a Wikidata item (not catalogue records), 20 have a plan view image
      (P3311; maps, sections and elevations left out: Ham Hill and Bat's Castle "Somerset Map", the Eddystone section,
      Wolf Rock's engineering drawing, Wyre Light's elevation), 1 a Commons "Plans of" category (Powis Castle), and
      for the types short of 12 plans, 25 places a type with a Commons category were searched for a file titled as
      a plan in their own category tree: 16 found in 1,250 searched (Hurst and Sandown Castles, Millbank Prison,
      Newcastle Gaol, the Surrey Dispensary, Manchester and Bristol infirmaries, Crofton Roman villa, Easter
      Aquhorthies...). Reviewed out (`NOT_PLANS`): the Stockton and Darlington's route map, Liverpool Royal
      Infirmary's nurses' home, a proposal for La Hougue Bie, Grime's Graves (typed a round barrow). 30 places;
      types with a plan 61 → 69 (8 only from places: polygonal fort 5, gaol, penitentiary, dispensary, fever
      hospital, funicular, public baths, Roman villa). Shown after the catalogue's plans on type pages (and as links
      in the hosted copy, `static_types` `pl` now takes places). Commons holds few plans of these places: the
      generic categories ("Floor plans of houses in …") not tried.
- [x] Grime's Graves (flint mines) typed a round barrow (found in BT6c2a, fixed 2026-10-28): Wikidata gives Q638485
      the class "round barrow" beside mine and mining museum, and the places build dated it by the round barrows'
      typical range (c. 2200-1500 BC). New `not_types` in aliases.json (entity → types dropped, with the reviewed
      reason; checked by `type_map.problems`) and reviewed date corrections now reach places (`date_corrections.
      apply_places`, run by places_build after its type estimates; `apply_to_db` updates places too): c. 2600-2300 BC,
      "It was worked between c. 2600 and c. 2300 BC" (its article). The class is listed with the Wikidata errors.
- [ ] BT6d Generated examples from building-gen, type by type, once a type passes the checks at the end of
      `docs/building_gen_review.md` (fixes made in building-gen's own repo).
- [x] BT7 (2026-10-26) Hosted copy (BT4b), Help page section "Building types" with three figures (`types_tree`,
      `type_page`, `types_time`), INTERFACE; two quizzes: "Which type came first?" (two isles types by first known
      date, 400 years apart or 60 on Hard, Hard mostly within one domain) and "Name the type" (a photographed
      catalogue record, up to 4 per type over 187 types, by its main type; wrong answers from other domains, on Hard
      the same domain but another family, since forms of one family can all be right).

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
- [ ] Known Wikidata errors to fix at source: Grime's Graves (Q638485) an instance of "round barrow"; Joan of Arc "place of burial" = Winchester Cathedral
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
- [x] Quiz and tours brought up to date (2026-10-27): quizzes "Oldest things" (which is the oldest recipe, book,
      song…? easy from other themes, hard from the same) and "What is it built of?" (a photo; materials found in the
      register text or on Wikidata, walls first; wrong answers never one of its materials or related to them, hard
      from the same group and kind); the oldest things also in "How old is it?" and, from AD 43, "Which came first?"
      (15 quizzes). Tours: four themes for the newer place groups, markets & trade, sport & leisure, schools,
      hospitals & town halls, graves & churchyards (39 tours; 407 in all), also in "Suggest a tour".
      `tour_surface` keeps its downloads by the route's points (regenerated tours keep their ids, not their routes).
- [ ] Graves & churchyards gave one walk (few burial grounds with an article within walking distance of each other):
      allow cemeteries without an article as tour stops, or a shorter APART for walks of that theme.
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
- [x] A6 GitHub Pages (2026-10-27): switched on (source GitHub Actions), `site-2026-10-27` deployed by the Pages
      workflow, live at https://gddickinson.github.io/british-isles-oldest-buildings/ (address on the repository and in the README). Refresh: export with
      `--full-pages`, new `site-*` release, run the workflow.
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
- [x] R9 Oldest things (2026-10-27, George's idea): the page /things (`bidb/oldest_things.py`, `app/static/things.js`,
      `/api/things`, hosted too): 113 researched entries in eight themes (`data/curated/things/*.json`: food and drink,
      writing, music, laws and maps, games and sport, customs, everyday things, pictures and media), each with claim,
      evidence, verdict (74 kept, 10 corrected, 29 open), where it is kept, made, found or held, and 332 quotes, all
      found (`data/things_check.json`).
- [ ] R9b Oldest things to add (left out in the first round): Anglo-Norman recipe collections (their only source
      gives the checker a bot page), Bakewell pudding and mince pies, the Biddenden dole (from 1605), Swan Upping,
      the Padstow 'Obby 'Oss, the Kirkwall Ba', the Olney pancake race, the Ballinderry board, the 1729 cricket
      bat, the 1511 curling stone, the Ferriby and Dover boats, Offa's penny, astrolabes made in England; more
      Welsh and Irish entries in pictures and media; "Which came first?" quiz questions from the entries.
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
