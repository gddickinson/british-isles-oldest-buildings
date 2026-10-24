"""Livery companies and their halls (roadmap C3a), read by bidb.trade_works.

Wikipedia's "Livery company" (CC BY-SA) has the companies in order of precedence with the year each charter was
granted (the table cites the companies' own sites, Vine 1886 and Hazlitt 1892); "List of mottos and halls of the
livery companies" gives each company's motto and hall. Wikidata adds the companies outside that table (the Cutlers
in Hallamshire, the Merchant Company of Edinburgh…) and coordinates: the company's own, else its hall's (the
hall's article, P159 headquarters or an item whose occupant, P466, is the company). A company with neither has no
place. Halls with an article and coordinates become guild-hall places too.

    companies()   {wikipedia title: {order, trade, charter, charter_url}} from the precedence table
    halls()       {wikipedia title: {hall, hall_title, motto, translation}} from the mottos table
    build()       place records: kind tr_livery (companies) and tr_guild (their halls)
    link_halls()  each company's hall as `extra.hall_ref` ("place:<id>" or "building:<id>"), after the write
"""
import json
import re
from urllib.parse import quote

from .hoards import wikitext
from .wikipedia_list import _LINK, _cells, _strip_wikitext, titles_to_qids

PRECEDENCE_PAGE = "Livery company"
HALLS_PAGE = "List of mottos and halls of the livery companies"
LIVERY_COMPANY = "Q1139056"
GUILD_LABEL = "Guildhall, livery or merchants' hall"
_URL = re.compile(r"\|\s*url\s*=\s*([^|}\s]+)")
_REF = re.compile(r"<ref[^>/]*>.*?</ref>|<ref[^>]*/>", re.S)
_EFN = re.compile(r"\{\{efn[^{}]*\}\}", re.I)


def _rows(text, header):
    """Rows (cell lists) of the first table after `header` in `text`."""
    i = text.find("{|", text.find(header))
    return [_cells(r) for r in text[i:text.find("\n|}", i)].split("\n|-")[1:]]


def _title(cell):
    link = _LINK.search(cell)
    return link.group(1).strip() if link else None


def companies(text=None):
    """The precedence table: {title: {order, name, trade, charter, charter_url}}."""
    text = text if text is not None else wikitext(PRECEDENCE_PAGE)
    out = {}
    for cells in _rows(text, "List of companies in order of precedence"):
        if len(cells) < 3 or not cells[0].strip().isdigit() or not _title(cells[1]):
            continue
        name_cell = _EFN.sub("", cells[1])
        trade = re.search(r"\)?\s*\(([^()]*(?:\[\[[^\]]*\]\][^()]*)*)\)\s*$", name_cell.strip())
        year = re.match(r"\s*(\d{4})", cells[2])
        url = _URL.search(cells[2])
        out[_title(cells[1])] = {
            "order": int(cells[0]), "name": _strip_wikitext(re.sub(r"\s*\(.*\)\s*$", "", name_cell)).strip(),
            "trade": _strip_wikitext(trade.group(1)).strip() if trade else None,
            "charter": int(year.group(1)) if year else None, "charter_url": url.group(1) if url else None}
    return out


def halls(text=None):
    """The mottos table: {title: {hall, hall_title, motto, translation}} (hall None for companies without one)."""
    text = text if text is not None else wikitext(HALLS_PAGE)
    out = {}
    for cells in _rows(text, "{|"):
        if len(cells) < 7 or not _title(cells[0]):
            continue
        hall = _strip_wikitext(_REF.sub("", cells[6])).strip(" ,")
        out[_title(cells[0])] = {"hall": hall or None, "hall_title": _hall_link(cells[6]) if hall else None,
                                 "motto": _strip_wikitext(cells[3]).strip(" '") or None,
                                 "translation": _strip_wikitext(cells[5]).strip() or None}
    return out


def _hall_link(cell):
    """The linked article of a hall cell that names a hall or house (not its street or district)."""
    for m in _LINK.finditer(cell):
        if re.search(r"\b(Hall|House|Court)\b", m.group(1)):
            return m.group(1).strip()
    return None


def hall_titles(info):
    """Article titles to try for a company's hall: its link, else "<name>, London" and its name."""
    if info.get("hall_title"):
        return [info["hall_title"]]
    name = hall_name(info)
    return [f"{name}, London", name] if name else []


def hall_name(info):
    """The hall's own name from the mottos table ("Bakers' Hall" of "Bakers' Hall, Harp Lane"), if it is one."""
    name = re.sub(r"\s*\(.*?\)", "", (info.get("hall") or "").split(",")[0]).strip()
    return name if re.search(r"\b(Hall|House)\b", name) else None


def in_london(lat, lon):
    return 51.28 < lat < 51.70 and -0.52 < lon < 0.34


def _hall_points(names):
    """{hall name: [(qid, lat, lon)]}: Wikidata items labelled exactly so (English) with coordinates."""
    from .http import sparql
    from .maritime import point
    out = {}
    if not names:
        return out
    vals = " ".join(json.dumps(n) + "@en" for n in sorted(names))
    for r in sparql(f"SELECT ?h ?l ?c WHERE {{ VALUES ?l {{ {vals} }} ?h rdfs:label ?l ; wdt:P625 ?c . }}"):
        pt = point(r["c"]["value"])
        if pt:
            out.setdefault(r["l"]["value"], []).append((r["h"]["value"].rsplit("/", 1)[-1], *pt))
    return out


def _places(info_by_qid, qid_of):
    """{company qid: (lat, lon, how, hall qid or None)}: the hall named by the mottos table (by article, else by
    label; in London for a City company, never the company itself), else the company's own coordinates, its P159
    headquarters (a building, not a town) or an item occupied by it (P466)."""
    from .http import sparql
    from .maritime import point
    wd = {}
    ids = " ".join(f"wd:{q}" for q in info_by_qid)
    for r in sparql(f"""SELECT ?i ?own ?hq ?hqc ?occ ?occc WHERE {{ VALUES ?i {{ {ids} }}
            OPTIONAL {{ ?i wdt:P625 ?own }}
            OPTIONAL {{ ?i wdt:P159 ?hq . ?hq wdt:P625 ?hqc FILTER NOT EXISTS {{ ?hq wdt:P31/wdt:P279* wd:Q486972 }} }}
            OPTIONAL {{ ?occ wdt:P466 ?i ; wdt:P625 ?occc }} }}"""):
        q = r["i"]["value"].rsplit("/", 1)[-1]
        for key, item in (("own", None), ("hqc", "hq"), ("occc", "occ")):
            pt = r.get(key) and point(r[key]["value"])
            if pt and q not in wd:
                wd[q] = (*pt, "own" if item is None else "hall", r[item]["value"].rsplit("/", 1)[-1] if item else None)
    cand = {q: [qid_of[t] for t in hall_titles(info) if qid_of.get(t) and qid_of[t] != q]
            for q, info in info_by_qid.items()}
    coords = {}
    hall_qids = {h for hs in cand.values() for h in hs}
    if hall_qids:
        for r in sparql(f"""SELECT ?h ?c WHERE {{ VALUES ?h {{ {' '.join('wd:' + h for h in hall_qids)} }}
                ?h wdt:P625 ?c }}"""):
            coords[r["h"]["value"].rsplit("/", 1)[-1]] = point(r["c"]["value"])
    by_label = _hall_points({hall_name(i) for i in info_by_qid.values() if hall_name(i)})
    out = {}
    for q, info in info_by_qid.items():
        city = bool(info.get("order"))
        ok = lambda pt: pt and (not city or in_london(*pt))
        hall = next(((h, coords[h]) for h in cand[q] if ok(coords.get(h))), None) or next(
            ((h, (lat, lon)) for h, lat, lon in by_label.get(hall_name(info) or "", []) if h != q and ok((lat, lon))), None)
        if hall:
            out[q] = (*hall[1], "hall", hall[0])
        elif q in wd and ok(wd[q][:2]):
            out[q] = wd[q]
    return out


def build(log=print):
    """Place records for the livery companies (tr_livery) and their halls (tr_guild)."""
    from .maritime import _record
    from .place_stage import rows_for
    table, hall_rows = companies(), halls()
    titles = set(table) | set(hall_rows) | {t for h in hall_rows.values() for t in hall_titles(h)}
    qid_of = titles_to_qids(titles)
    by_qid = {}
    for title in set(table) | set(hall_rows):
        if qid_of.get(title):
            by_qid.setdefault(qid_of[title], {"title": title}).update({**table.get(title, {}), **hall_rows.get(title, {})})
    for q in _wikidata_companies():
        by_qid.setdefault(q, {})
    where = _places(by_qid, qid_of)
    rows = {r["i"]["value"].rsplit("/", 1)[-1]: r
            for r in rows_for(by_qid, coord="OPTIONAL { ?i wdt:P625 ?coord }")}
    recs, no_place = {}, []
    for q, info in by_qid.items():
        r = rows.get(q)
        if q not in where or not r:
            no_place.append(info.get("name") or (r and r["iLabel"]["value"]) or q)
            continue
        lat, lon, how, hall = where[q]
        x = _record("tr_livery", "Livery company or guild", {**r, "coord": {"value": f"Point({lon} {lat})"}})
        if not x:
            continue
        extra = {k: info[k] for k in ("order", "trade", "charter", "charter_url", "hall", "motto", "translation")
                 if info.get(k)}
        if how == "hall":
            extra["placed_at"], extra["hall_id"] = "its hall", hall
        if info.get("charter"):
            x["year_start"], x["date_text"] = info["charter"], f"charter {info['charter']}"
            extra["charter_source"] = "https://en.wikipedia.org/wiki/" + quote(PRECEDENCE_PAGE.replace(" ", "_"))
        elif x.get("year_start"):
            x["date_text"] = f"founded {x['year_start']}"
        if info.get("order"):
            x["type"] = f"Livery company (no. {info['order']} in precedence)"
        if info.get("trade"):
            x["description"] = info["trade"][:1].upper() + info["trade"][1:]
        x["locality"] = info.get("hall") or x.get("locality")
        x["extra"] = extra
        recs[q] = x
    hall_ids = {w[3] for w in where.values() if w[3]}
    for r in rows_for(hall_ids):
        h = _record("tr_guild", GUILD_LABEL, r)
        if h:
            recs.setdefault(h["id"], h)
    log(f"  livery: {len(table)} in the precedence table, {len(by_qid)} companies, "
        f"{sum(r['kind'] == 'tr_livery' for r in recs.values())} placed "
        f"({sum(1 for w in where.values() if w[2] == 'hall')} at their hall), {len(no_place)} with no place; "
        f"{sum(r['kind'] == 'tr_guild' for r in recs.values())} halls")
    return list(recs.values())


def link_halls(conn):
    """Point each placed company at its hall's place or catalogue building (extra.hall_ref); returns the count."""
    buildings = {i for (i,) in conn.execute("SELECT id FROM buildings")}
    places = {i for (i,) in conn.execute("SELECT id FROM places WHERE kind = 'tr_guild'")}
    n = 0
    for pid, extra in conn.execute("SELECT id, extra FROM places WHERE kind = 'tr_livery'").fetchall():
        ex = json.loads(extra or "{}")
        h = ex.pop("hall_id", None)
        ref = h and ("building:" + h if h in buildings else "place:" + h if h in places else None)
        if ref:
            ex["hall_ref"], n = ref, n + 1
        conn.execute("UPDATE places SET extra = ? WHERE id = ?", (json.dumps(ex, ensure_ascii=False), pid))
    return n


def _wikidata_companies():
    """Livery companies on Wikidata, with or without coordinates."""
    from .http import sparql
    return {r["i"]["value"].rsplit("/", 1)[-1] for r in sparql(
        f"SELECT DISTINCT ?i WHERE {{ ?i wdt:P31 wd:{LIVERY_COMPANY} }}")}


if __name__ == "__main__":
    print(json.dumps(build(), ensure_ascii=False, default=str)[:3000])
