# Research brief: festivals and seasons (page /festivals)

The page `/festivals` of British Isles Oldest Buildings is a fun way into the catalogue's buildings, monuments and
places through the year's festivals: one sub-page per festival with its history, customs, legends, food, oldest
examples and the buildings, monuments and sites tied to it, across England, Scotland, Wales, Ireland (both
jurisdictions), the Isle of Man and the Channel Islands. Each festival is one file,
`data/curated/festivals/<id>.json`, and **every fact and every place has a source with an exact quote**, checked by
script. Aim for lively, surprising and accurate: the kind of fact people repeat to friends, but true.

## Rules
- Quote exactly, word for word, from a page a script can fetch: Wikipedia, English Heritage, Historic
  Environment Scotland, Cadw, Heritage Ireland / OPW, National Trust, National Museums (Scotland, Wales, Ireland),
  British Library, Royal Collection, Historic Royal Palaces, cathedral and abbey sites, BBC, university pages,
  open-access PDFs. Keep quotes short (a sentence or phrase that carries the fact). A fact may cite two sources.
- Check every quote before you finish. From the project root:
  `.venv/bin/python -m bidb.festivals --file data/curated/festivals/<id>.json`
  prints problems and any quote not found. A quote that is not found does not go in (fix it or drop the fact).
  Pages that refuse scripts cannot be used.
- Write `intro`, fact `text` and place `why` in your own words (plain, British English, no hype). Do not overstate:
  if an origin is tradition or disputed ("said to", "first recorded in"), say so. Pagan-origin claims about
  Christmas, Easter and Halloween are often overstated: give what the sources actually support.
- Places must be real buildings, monuments or sites in the isles with coordinates (decimal degrees, WGS84, from
  Wikipedia/Wikidata). Give `qid`, the Wikidata id, when the place has one (look it up; it lets the page link to
  the catalogue's record). Prefer old buildings and monuments: churches, abbeys, castles, stone circles, tombs,
  holy wells, hills, market crosses, inns, halls where a custom is held or an event happened.
- Do not edit any other file in the repository. Work only in your own JSON files (scratch files outside the repo).

## File format
```json
{
 "id": "christmas",
 "title": "Christmas and Yule",
 "also": ["Yule", "Nadolig (Welsh)", "Nollaig (Irish)"],
 "season": "winter",
 "when": {"date": "12-25"},
 "when_text": "25 December; the twelve days run to Twelfth Night, 5 January",
 "intro": "Two or three sentences in your own words.",
 "facts": [
  {"kind": "history", "title": "A king crowned on Christmas Day", "year": 1066,
   "text": "Own words, one to three sentences.",
   "where": {"name": "Westminster Abbey", "lat": 51.4993, "lon": -0.1273, "qid": "Q5933"},
   "sources": [{"title": "Westminster Abbey (Wikipedia)", "author": "Wikipedia contributors", "kind": "reference",
                "url": "https://en.wikipedia.org/wiki/...", "locator": "section History", "quote": "exact words"}]}
 ],
 "places": [
  {"name": "Glastonbury Abbey", "qid": "Q...", "lat": 51.1460, "lon": -2.7149,
   "why": "Own words: why it belongs to this festival.", "sources": [ ... ]}
 ]
}
```
- `when`: `{"date": "MM-DD"}` for a fixed day, `{"easter": 0}` (days from Easter Sunday, e.g. -47 for Shrove
  Tuesday), `{"sun": "winter_solstice" | "summer_solstice" | "equinox"}`, or `{"rule": "last Tuesday of January"}`.
- `kind` of a fact: history, custom, legend, food, oldest, sky, curiosity. `year` is optional (negative for BC).
  `where` is optional: give it when the fact happens somewhere mappable.
- Source `kind`: primary, listing, secondary or reference (Wikipedia is reference).
- Target per festival: 10-14 facts (a mix of kinds, spread across the nations where the festival is kept) and 8-12
  places.

## Report back
For each file: counts of facts and places, quotes found out of quotes given, and anything you could not source.
