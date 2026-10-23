# Trade, enterprise and innovation: sources (roadmap C1)

`sources.json` holds 72 sources researched on 2026-10-23 by three research agents (firms and institutions, economic
series, innovations and laws). Each source has its publisher, citation, licence with a verbatim quote, the landing and
download URLs as checked on that day, years, regions, size, the items it serves (C2–C8), what we would take, and a
verdict. Check the file with `python -m bidb.trade_sources`.

Verdicts: **use** 32 (open licence), **quote figures** 17 (single published figures cited with page and quote),
**link only** 8, **ask** 12 (permission or terms needed: `reason` says whom), **left out** 3.

## Best sources per item
- **C2 tea:** the Statistical Abstract for the UK (c.1840–1938, Internet Archive scans, out of Crown copyright) for
  tea imports and duty, figures to be transcribed by hand (the OCR is rough); HMRC trade API (HS 0902, OGL) for the
  modern end; Schumpeter 1960 and Mitchell 1988 for the 18th century (quote figures).
- **C3 guilds, exchanges, trading houses:** Wikidata (CC0; livery company Q1139056, guild Q170161, chartered company
  Q162157, coffeehouse Q4236467, guild house Q1961493, livery hall Q98034180; 244 banks); Wikipedia's livery company
  table (114 companies, 87 charter years), Guilds of the City of Dublin (25), Edinburgh and Glasgow incorporated
  trades (CC BY-SA leads; each fact to be sourced).
- **C4 firms:** Wikidata 28,419 firms (58% founding year, 66% coordinates, 48% both, 13% closing year, 33%
  industry); Wikidata's "business" class also holds pubs, schools and parish councils, so firms need an allow-list
  of classes. Ireland's CRO register (CC BY 4.0, 827,786 companies incl. dissolved, Eircode, sector; SQL API).
  Companies House basic data (live companies only, 5.5 M rows, 471 MB).
- **C5 graphs:** Companies House Table A8 (incorporations and dissolutions 1939–2026, OGL); Federico–Tena World Trade
  Historical Database (UK 1800–1938, Ireland 1922–38, CC BY 4.0); CEPII TRADHIST exports/GDP 1827–2014 (Etalab
  2.0, via OWID); ONS IKBH/IKBI 1948– and CSO TSA01 1930–; ONS long-term employment 1861–2018 and JOBS02, CSO CNNL1
  (Ireland by industry and county 1926–96); OWID farming share of jobs from 1400; ONS RPI CDKO 1800–; IPO patents
  1852–1915 yearly (archived page, OGL) and 2016– (OGL), Bottomley 2014 1700–1851 by country (quote figures).
  Before the statistics: Shaw-Taylor & Wrigley 2014, Keibek 2017, Davis 1962, Cullen 1968, Riden 1977, King 2005,
  Phelps Brown–Hopkins 1956, Pressnell (quote figures).
- **C6 innovations:** Wikidata 1,167 inventions by inventors of the isles once astronomy and species are left out
  (402 dated, 210 before 1900); Wikipedia lists of English (~607), Scottish (~162), Irish (~76) and Welsh (~29)
  inventions and discoveries as leads.
- **C7 laws and institutions:** legislation.gov.uk (OGL; has the Navigation Act 1660, Combination Acts, Joint Stock
  Companies Act 1844, Limited Liability Act 1855, Companies Act 1862; not the Bubble Act 1720), Irish Statute Book
  (CC BY 4.0), the National Archives' Discovery API (OGL); founding dates of the Royal Society, RSA, TUC and
  Rochdale Pioneers quoted from their own pages (link only).
- **C8 trade stories:** draw on all of the above; Lloyd's Register of Ships 1768–1900 (137 Internet Archive volumes
  CC BY-SA 4.0; the rest non-commercial or no licence).

## To ask (user items)
Bank of England millennium dataset (best compilation: wool and cloth exports from 1280, tea, cotton, shipping, wages
and prices; personal or internal non-commercial use only), Cambridge Group occupational tables and steam-engine GIS,
Kanefsky's Early Engines Database (spreadsheet by email; footer reserves all rights), Clark's prices and wages, Allen's
wages, GPIH, MeasuringWorth (more than five consecutive years), Nuvolari patent quality (ICPSR login), Legacies of
British Slavery (UCL; site refuses scripts, licence possibly non-commercial), the Livery Committee database, Companies
House dissolved companies (API key). Left out: I-CeM individual data, WIPO statistics, the BoE dataset's (non-existent)
bank counts.

## Gaps
No open series before c.1840 for shipping or iron; no open yearly count of companies before 1939 or of country banks;
patents 1916–c.1995 (WIPO only); no Irish patent series before 2002; no Wikidata query for "firsts"; Tate's enclosure
figures only through the Cambridge Group's parish GIS.
