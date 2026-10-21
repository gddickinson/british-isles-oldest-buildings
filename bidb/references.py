"""References and fact checks for catalogue records.

1. Wikidata statement references (stated in / reference URL / title) for the facts shown:
   inception (P571), heritage designation (P1435), architect (P84), style (P149).
2. A list of sources per record (Wikidata, Wikipedia, official registers, curated lists).
3. A date check comparing the catalogue date with independent sources:
     Corroborated   another source gives a date within 100 years (or the same century;
                    within 500 years when both are BC)
     Conflict       another source gives a date more than 150 years away
     Single source  nothing independent to compare with
"""
import json
import re

from .date_mining import date_from_text
from .http import sparql

PROPS = {"P571": "Date built", "P1435": "Heritage designation", "P84": "Architect", "P149": "Style"}
# places: battles/events are dated by point in time / start time
PLACE_PROPS = {"P571": "Date", "P585": "Date", "P580": "Date", "P1435": "Heritage designation"}


def _qid(uri):
    return uri.rsplit("/", 1)[-1]


def wikidata_references(qids, log=print, props=PROPS):
    """{qid: [{"fact", "value", "stated_in", "url", "title"}]} from statement references."""
    out = {}
    values_p = " ".join(f"(p:{p} ps:{p})" for p in props)
    ids = sorted(q for q in qids if q and q.startswith("Q"))
    for n in range(0, len(ids), 250):
        values = " ".join("wd:" + q for q in ids[n:n + 250])
        rows = sparql(f"""SELECT ?i ?pp ?v ?vLabel ?statedLabel ?url ?title WHERE {{
            VALUES ?i {{ {values} }} VALUES (?pp ?ps) {{ {values_p} }}
            ?i ?pp ?st . ?st ?ps ?v ; prov:wasDerivedFrom ?ref .
            OPTIONAL {{ ?ref pr:P248 ?stated }} OPTIONAL {{ ?ref pr:P854 ?url }} OPTIONAL {{ ?ref pr:P1476 ?title }}
            SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en". }} }}""")
        for r in rows:
            val = lambda k: (r.get(k) or {}).get("value")
            stated, url = val("statedLabel"), val("url")
            if not stated and not url:
                continue
            prop = _qid(val("pp"))
            value = val("vLabel") or val("v")
            if prop in ("P571", "P585", "P580") and value:
                value = value[:4].lstrip("+0") or value
            ref = {"fact": props.get(prop, prop), "value": value, "stated_in": stated, "url": url,
                   "title": val("title")}
            lst = out.setdefault(_qid(val("i")), [])
            if ref not in lst:
                lst.append(ref)
        if n % 5000 == 0:
            log(f"  references: {n}/{len(ids)} items, {len(out)} with references")
    return out


def sources(r):
    """Every source behind a record, as [{"label", "url"}]."""
    enc = lambda s: s.replace(" ", "_")
    s = []
    if r.get("wikidata_id"):
        s.append({"label": "Wikidata", "url": f"https://www.wikidata.org/wiki/{r['wikidata_id']}"})
    if r.get("wikipedia_title"):
        s.append({"label": "Wikipedia", "url": f"https://en.wikipedia.org/wiki/{enc(r['wikipedia_title'])}"})
    if r.get("nhle_id"):
        s.append({"label": "Historic England list entry",
                  "url": f"https://historicengland.org.uk/listing/the-list/list-entry/{r['nhle_id']}"})
    if r.get("hes_id"):
        s.append({"label": "Historic Environment Scotland",
                  "url": f"https://portal.historicenvironment.scot/designation/{r['hes_id']}"})
    if r.get("cadw_id"):
        s.append({"label": "Cadw", "url": "https://cadwpublic-api.azurewebsites.net/reports/listedbuilding/"
                                          f"FullReport?lang=en&id={r['cadw_id']}"})
    if r.get("ie_niah_id"):
        s.append({"label": "NIAH (Ireland)", "url": r.get("register_url") or
                  f"https://www.buildingsofireland.ie/buildings-search/building/{r['ie_niah_id']}/"})
    if r.get("ie_smr_id"):
        s.append({"label": "Irish SMR", "url": f"https://maps.archaeology.ie/HistoricEnvironment/?SMR={r['ie_smr_id']}"})
    if r.get("curated_notes") and "[" in (r.get("curated_notes") or ""):
        page = r["curated_notes"].rsplit("[", 1)[1].rstrip("]")
        s.append({"label": f"Wikipedia: {page}", "url": f"https://en.wikipedia.org/wiki/{enc(page)}"})
    return s


# a later date in a sentence about part of the building is an addition, not a conflict
PARTS = re.compile(r"\b(bells?|screen|font|windows?|glass|monuments?|tombs?|memorials?|effig\w*|organ|"
                   r"pulpit|clock|paintings?|murals?|brass(es)?|porch|spire|tower|chancel|aisles?|nave|"
                   r"roof|wings?|extension|extended|added|enlarged|gatehouse|remnant|surviv\w*|fittings?|"
                   r"most(ly)?|largely|mainly|rebuilt|remodell\w*|altered|present building|current building|"
                   # later events, contents and neighbours rather than construction
                   r"register|benches|bench ends|silver\w*|chalice|arms|hanging|clerestory|gallery|"
                   r"vicarage|interior|grounds|estate|excavation|chronicler|antiquary|foundation|"
                   r"coeducational|museum|listed|congregation|served|demolished|replaced|new church|"
                   r"third building|second building|farmhouse|manor house|mansion|inn\b|"
                   r"house (?:was )?built|reuse|ruins|storms?|railway|items|plan of|establish\w*|founded|"
                   r"premises|newly built|name|paid|naval|ships?|lifeboats|erected in|moved|boathouse)\b", re.I)


# an earlier date for the founding or the site, not for the present fabric
ORIGIN = re.compile(r"\b(found\w*|establish\w*|origins?|site|first church|original church|earlier|"
                    r"predecessor|successor|replac\w*|occupied|worship|traced? back|since)\b", re.I)


_CONFIRMED = {}


def _confirmations():
    """Reviewed conflicts where the catalogue date stands: data/curated/date_confirmations.json."""
    if not _CONFIRMED:
        from .config import DATA_DIR
        try:
            _CONFIRMED.update(json.loads((DATA_DIR / "curated" / "date_confirmations.json").read_text()))
        except (OSError, ValueError):
            _CONFIRMED["_none"] = ""
    return _CONFIRMED


def _year_of(text):
    """(year, evidence sentence) of the construction date in a text, or None."""
    hit = date_from_text(text or "", strict=True)
    return (hit[0], hit[2]) if hit else None


def date_check(r, refs):
    """(status, note) for the record's date against independent evidence."""
    y = r.get("year_start")
    if y is None:
        return "Not dated", ""
    conf = r.get("date_confidence") or ""
    if conf == "Corrected (reviewed)":
        return "Reviewed", "Date corrected after reviewing conflicting sources (data/curated/date_corrections.json)"
    others = []
    if conf == "Recorded" and r.get("wikipedia_extract"):
        wy = _year_of(r["wikipedia_extract"])
        if wy is not None:
            others.append(("Wikipedia introduction", *wy))
    if conf != "Recorded":
        wd_dates = [ref for ref in refs if ref["fact"] == "Date built"]
        if wd_dates and re.fullmatch(r"-?\d+", str(wd_dates[0]["value"] or "")):
            others.append(("Wikidata (referenced)", int(wd_dates[0]["value"]), ""))
    m = re.search(r"\((?:Wikidata|Wikipedia list): ([^)]*)\)", r.get("date_text") or "")
    if m:
        from .dates import parse_text_year
        ly = parse_text_year(m.group(1))
        if ly is not None:
            others.append(("second source in the date", ly, ""))
    others = [o for o in others if not (o[1] > y + 150 and o[2] and PARTS.search(o[2]))]
    if not others:
        sourced = any(ref["fact"] == "Date built" for ref in refs)
        return ("Referenced" if sourced else "Single source",
                "The date carries a reference on Wikidata" if sourced else "")
    label, oy, evidence = min(others, key=lambda o: abs(o[1] - y))
    diff = abs(oy - y)
    same_century = (y - 1) // 100 == (oy - 1) // 100
    if diff <= 100 or same_century or (y < 0 and oy < 0 and diff <= 500):   # prehistoric: looser
        return "Corroborated", f"{label} gives {oy}"
    if diff > 150:
        quote = f' ("{evidence[:200]}")' if evidence else ""
        if oy < y and evidence and ORIGIN.search(evidence):
            return "Earlier origin", f"{label} gives {oy} for the founding or site{quote}; the catalogue dates the present building ({y})"
        kept = _confirmations().get(r.get("id"))
        if kept:
            return "Reviewed", f"Catalogue date kept after review: {kept} ({label} gives {oy})"
        return "Conflict", f"{label} gives {oy}{quote}; the catalogue uses {y}"
    return "Single source", f"{label} gives {oy}"


def annotate(records, log=print):
    """Add refs / sources / date_check / date_check_note to records in place."""
    refs = wikidata_references([r["id"] for r in records], log)
    counts = {}
    for r in records:
        rr = refs.get(r["id"], [])
        r["refs"] = json.dumps(rr, ensure_ascii=False) if rr else None
        r["sources"] = json.dumps(sources(r), ensure_ascii=False)
        r["date_check"], r["date_check_note"] = date_check(r, rr)
        counts[r["date_check"]] = counts.get(r["date_check"], 0) + 1
    log(f"references for {len(refs)} records; date checks: {counts}")
    return records


def recheck(log=print):
    """Recompute date checks in the existing database (after changing the rules): python -m bidb.references"""
    from .db import connect
    conn = connect()
    conn.execute("PRAGMA busy_timeout = 120000")       # background jobs may be writing
    cols = ["id", "year_start", "date_confidence", "wikipedia_extract", "date_text", "refs"]
    counts, updates = {}, []
    for row in conn.execute(f"SELECT {', '.join(cols)} FROM buildings"):
        r = dict(zip(cols, row))
        status, note = date_check(r, json.loads(r["refs"]) if r["refs"] else [])
        counts[status] = counts.get(status, 0) + 1
        updates.append((status, note, r["id"]))
    conn.executemany("UPDATE buildings SET date_check = ?, date_check_note = ? WHERE id = ?", updates)
    conn.commit()
    log(f"date checks: {counts}")


if __name__ == "__main__":
    recheck()
