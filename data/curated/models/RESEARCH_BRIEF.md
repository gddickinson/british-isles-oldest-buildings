# Research brief for the 3D models (roadmap SH3)

The app already has a 3D model of Stonehenge (`/stonehenge`; its research is `data/curated/stonehenge/stones.json`,
read it for the standard expected). Each new model is drawn from one research file,
`data/curated/models/<id>.json`, in which **every number and every shape is backed by a source with an exact
quote**. The geometry is built from these facts in code, so what matters is facts with measurements, not prose.

## Rules
- Quote exactly, word for word, from a page that a script can fetch (Wikipedia, Cadw, Coflein, Canmore/HES
  portal, Historic England, World Heritage Ireland / Heritage Ireland, National Monuments Service, Welsh Journals
  Online, PSAS and SAS books (journals.socantscot.org, books.socantscot.org), Archaeology Data Service, open-access
  PDFs). PDFs are fine. Keep quotes short (one sentence or a phrase with the number in it).
- Check every quote before you finish, with the project's own checker (run from the project root):
  ```
  .venv/bin/python -c "
  from bidb.verify_research import source_text; from bidb.evidence import quote_found
  t = source_text('<url>'); print(t is not None and quote_found('<quote>', t))"
  ```
  A quote that is not found does not go in. Pages that refuse scripts (many Historic England pages do) cannot be
  used; say so in `gaps`.
- Licences: text quotes are fine from any source. A plan or drawing can only be traced if its licence allows it
  (CC BY, CC BY-SA, OGL, public domain); record the licence of any plan you point to.
- When sources disagree, keep both with their quotes and say so in a `note`. Do not average or invent. Values you
  derive (e.g. reading a scale bar, arithmetic from quoted numbers) are marked `"derived": true` with how.
- Do not edit any other file in the repository. Work only in your own JSON file (and scratch files outside the
  repository).

## File format (`data/curated/models/<id>.json`)
```json
{
 "id": "<id>", "name": "...", "record": "<catalogue record id given in your task>",
 "date_checked": "2026-10-29",
 "about": "one paragraph: what the monument is, its date, what survives, what was restored and when",
 "sources": {"<key>": {"title": "...", "author": "...", "url": "...", "licence_note": "..."}},
 "facts": {
   "<name>_m": {"value": 26, "unit": "m", "note": "what exactly is measured",
                "cites": [{"source": "<key>", "quote": "..."}]}
 },
 "elements": [ {"id": "...", "kind": "...", "...measurements and state...": "...", "cites": [...]} ],
 "alignment": [ {"event": "e.g. summer solstice sunrise", "claim": "...", "cites": [...]} ],
 "phases": [ {"name": "...", "date": "...", "what": "...", "cites": [...]} ],
 "debate": [ {"claim": "...", "cites": [...]} ],
 "plans": [ {"title": "...", "url": "...", "licence": "...", "what it shows": "..."} ],
 "gaps": [ "what you could not find or could not reach, and where it probably is" ]
}
```
Facts to look for in every case (where they apply): overall dimensions (diameters, lengths, widths, heights;
inner/outer, to stone centres or faces), orientation (azimuth of the passage, axis or entrance, in degrees from
true north if given), numbers of stones and which survive, each stone's height, width, thickness, shape and state
(standing, leaning, fallen, stump, lost, re-erected, moved), the passage and chamber (length, width, height, floor
rise, how roofed: lintels, corbelling, capstones), the mound/cairn/bank/ditch (diameter, height, kerb, material),
the stone used (rock type, colour), modern restoration and what is reconstructed (so the "now" and "as built" views
differ correctly), and the sky alignment with its quoted sources. Also give the position (lat/lon or grid reference)
of a clear reference point (chamber centre, circle centre) with a source.

Finish with a short summary: how many facts and quotes (all checked), the most important gaps, and which plan
(if any, with licence) would let the layout be traced.
