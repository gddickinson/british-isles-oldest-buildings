"""Firms through time for "Change over time" (roadmap C4a): businesses of the isles on Wikidata with a founding year
(and a closing year where recorded), placed at their own coordinates or else their head office, sorted into broad
industries by their classes and stated industry (P452).

Wikidata's business classes also hold parish councils, NHS trusts, societies, railway lines and websites, so items
with any class named in `NOT_FIRM` are left out.

    python -m bidb.change_firms   → app/static/data/change/layers/firms.json (+ layers.json),
                                     data/curated/change/data/firms_founded_*.csv (graphs, via bidb.change_series)
"""
import csv
import hashlib
import json
import re
import sys

from .change_layers import OUT
from .config import ROOT
from .http import request_json

QLEVER = "https://qlever.dev/api/wikidata"        # the same Wikidata data; WDQS times out on the subclass tree
COUNTRIES = ("Q145 Q27 Q9676 Q25230 Q785 Q174193 Q161885 Q179876 Q230791 Q215530 Q31747")  # incl. historical states
SOURCE = {"short": "Wikidata (firms)", "licence": "CC0", "url": "https://www.wikidata.org/wiki/Q783794",
          "citation": "Wikidata contributors, companies (Q783794 and subclasses) and items directly of class business "
                      "(Q4830453) or enterprise (Q6881511) in the isles or with their head office there, with "
                      "founding (P571), dissolution (P576), coordinates (P625, else head office P159) and industry "
                      "(P452), queried 2026 through QLever"}
DATA = ROOT / "data" / "curated" / "change" / "data"

NOT_FIRM = re.compile(r"council|authority|\bnhs\b|societ|universit|college|school|education|association|union|"
                      r"charit|nonprofit|non-profit|non-governmental|railway line|line section|railway network|"
                      r"narrow-gauge railway|industrial railway|heritage railway|miniature railway|wagonway|tramway|"
                      r"tram system|website|web service|web application|software$|mobile app|^brand|trademark|"
                      r"legislature|library|archives|art gallery|museum|church|parish|inns? of c|learned|academy|"
                      r"foundation|think tank|government|regulatory|agency of|advocacy|sports|sporting|event|"
                      r"magazine|newspaper|periodical|newsletter|television channel|television station|"
                      r"proposed|abandoned|built structure|building$|theatre building|^mine$|^hotel$|duo|band$|"
                      r"research institute|institute|military|clinic|plantation|trust$|branch$|division$|"
                      r"public body|statutory|executive|combined|colonial|club|fund$|^chain$|"
                      r"political|order$|lodge|guild|livery", re.I)
NOT_FIRM_KEEP = re.compile(r"investment trust|holding company|building society|co-operative|cooperative|"
                           r"credit union|investment fund", re.I)
GENERIC = re.compile(r"^(business|company|enterprise|organi[sz]ation|public company|privately held company|"
                     r"limited company|private company.*|public limited company|private limited company|"
                     r"subsidiary company|holding company|corporation|partnership|joint-stock company|"
                     r"family business|startup company|multinational corporation|conglomerate|concern|"
                     r"corporate group|commercial organization|defunct organization|former entity|"
                     r"dormant company|limited liability .*|brick and mortar|state-owned enterprise)$", re.I)

# (label, colour, words) in order: the first that matches a firm's classes, else its industries, wins
SECTORS = [
    ("Food, drink and tobacco", "#b7791f", r"brew|distill|whisk|gin\b|food|beverage|drink|tobacco|bakery|baker|dairy|"
                                           r"confection|sugar|\btea\b|coffee|meat|fish|mill(ing|er)|flour|cider|wine|"
                                           r"chocolate|biscuit|restaurant|caf[eé]|pub chain|catering"),
    ("Banks, finance and insurance", "#2f855a", r"bank|financ|insur|building society|credit|invest|stock|fund|"
                                                r"broker|asset|wealth|equity|fintech|mortgage|pension|capital|"
                                                r"savings|exchange|accounting|holding companies"),
    ("Transport and utilities", "#2b6cb0", r"railway|rail |rail$|train|bus |bus$|coach|airline|air transport|"
                                           r"aviation|airport|shipping|ferry|cruise|freight|transport|canal|tram|"
                                           r"logistic|haul|port |water supply|water collection|utility|electric(ity)? "
                                           r"(supply|power|generation)|power generation|energy|gas |gas$|"
                                           r"telecom|telephone|postal|mobile (virtual|phone)|internet service|"
                                           r"distribution network|transmission|waste|recycling|electricity"),
    ("Publishing, print and media", "#805ad5", r"publish|print|press\b|imprint|book|newspaper|news agency|"
                                               r"magazine|music|record (label|company|pressing)|recording|"
                                               r"phonograph|film|cinema|television|tv |broadcast|radio|media|"
                                               r"photograph|photo agency|animation|video|theatre|entertainment|"
                                               r"postcard|map publishing|stationer|advertis|game"),
    ("Farming, mining and quarrying", "#744210", r"crop|farm|agricult|growing of|animal (production|husbandry)|"
                                                 r"forestry|logging|fishing|mining|mine |\bmines?\b|quarr|coal|"
                                                 r"stone industry|petroleum|crude|oil|natural gas|non-wood|"
                                                 r"ore|slate|clay pit|peat|gathering"),
    ("Making things", "#c53030", r"manufactur|maker|industr|engineer|shipbuild|shipyard|foundry|founding|iron|"
                                 r"steel|metal|textile|cloth|cotton|wool|linen|spinning|weaving|pottery|ceramic|"
                                 r"porcelain|chemical|pharma|automo|motor|car |car$|vehicle|aircraft|aerospace|"
                                 r"locomotive|rolling stock|weapon|arms|gun|glass|paper|furniture|brick|works|"
                                 r"factory|electronic|electrical|semiconductor|machinery|plastic|rubber|leather|"
                                 r"footwear|shoe|fashion|clothing|jewel|watch|clock|instrument|bicycle|cosmetic|"
                                 r"perfume|soap|tool|biotech|medical device|construction of|coachbuild|bell|\bmint\b|pottery"),
    ("Shops and trade", "#d53f8c", r"retail|shop|store|wholesale|trade|trading|merchant|supermarket|market|"
                                   r"e-commerce|online shop|auction|dealer|dealership|vendor|chain|grocer|"
                                   r"pharmacy|optician|bookseller|import|export"),
    ("Services and other", "#4a5568", r"."),
]
NOT_STATED = ("Kind not stated", "#a0aec0")
CLOSED = "#cbd5e0"


def fetch():
    """Wikidata bindings, one per item (QLever)."""
    q = f"""PREFIX wd: <http://www.wikidata.org/entity/> PREFIX wdt: <http://www.wikidata.org/prop/direct/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
SELECT ?i (SAMPLE(?lab) AS ?name) (MIN(YEAR(?inc)) AS ?open) (MIN(YEAR(?dis)) AS ?close) (SAMPLE(?co) AS ?coord)
  (SAMPLE(?hq) AS ?hqcoord) (GROUP_CONCAT(DISTINCT ?cl; separator="|") AS ?classes)
  (GROUP_CONCAT(DISTINCT ?il; separator="|") AS ?inds) WHERE {{
  VALUES ?c {{ {" ".join("wd:" + c for c in COUNTRIES.split())} }}
  {{ ?i wdt:P31/wdt:P279* wd:Q783794 }} UNION {{ ?i wdt:P31 wd:Q4830453 }} UNION {{ ?i wdt:P31 wd:Q6881511 }}
  {{ ?i wdt:P17 ?c }} UNION {{ ?i wdt:P159/wdt:P17 ?c }}
  ?i wdt:P31 ?cls . OPTIONAL {{ ?cls rdfs:label ?cl FILTER(LANG(?cl)="en") }}
  OPTIONAL {{ ?i rdfs:label ?lab FILTER(LANG(?lab)="en") }}
  OPTIONAL {{ ?i wdt:P571 ?inc }} OPTIONAL {{ ?i wdt:P576 ?dis }}
  OPTIONAL {{ ?i wdt:P625 ?co }} OPTIONAL {{ ?i wdt:P159/wdt:P625 ?hq }}
  OPTIONAL {{ ?i wdt:P452 ?ind . ?ind rdfs:label ?il FILTER(LANG(?il)="en") }}
}} GROUP BY ?i"""
    res = request_json(QLEVER, params={"query": q}, headers={"Accept": "application/sparql-results+json"},
                       min_interval=1.0)
    return res["results"]["bindings"]


def is_firm(classes):
    """False when any class names something that is not a firm (council, society, railway line…)."""
    return not any(NOT_FIRM.search(c) and not NOT_FIRM_KEEP.search(c) for c in classes)


def sector(classes, industries, name=""):
    """Index into SECTORS, or None when neither the classes, the industries nor the name ("… Brewery", "… Bank")
    say what the firm does. The name never falls through to "Services and other"."""
    for words in ([c for c in classes if not GENERIC.match(c)], industries, [name]):
        text = " | ".join(words).lower()
        if not text:
            continue
        for k, (_, _, rx) in enumerate(SECTORS[:-1] if words == [name] else SECTORS):
            if re.search(rx, text):
                return k
    return None


def _point(wkt):
    lon, lat = wkt[6:-1].split()
    return float(lat), float(lon)


def _jitter(qid):
    """A fixed offset of up to ~1 km, so firms placed at the same head-office town do not sit on one dot."""
    h = hashlib.sha1(qid.encode()).digest()
    return (h[0] / 255 - 0.5) * 0.018, (h[1] / 255 - 0.5) * 0.028


def firms(bindings):
    """Rows [name, lat, lon, opened, closed or None, sector or None, at head office] of dated firms with a position."""
    from .land import near_land
    out = []
    for b in bindings:
        val = lambda k: b[k]["value"] if k in b else None
        classes = (val("classes") or "").split("|") if val("classes") else []
        inds = (val("inds") or "").split("|") if val("inds") else []
        name, opened, closed = val("name"), val("open"), val("close")
        if not name or not opened or not is_firm(classes) or not (val("coord") or val("hqcoord")):
            continue
        opened, closed = int(opened), int(closed) if closed else None
        if not 1000 <= opened <= 2026 or (closed is not None and (closed < opened or closed > 2026)):
            continue
        lat, lon = _point(val("coord") or val("hqcoord"))
        if not near_land(lat, lon):
            continue                                   # head offices abroad (P17 in the isles, HQ in New York…)
        hq = not val("coord")
        if hq:
            dy, dx = _jitter(val("i"))
            lat, lon = lat + dy, lon + dx
        out.append([name, round(lat, 4), round(lon, 4), opened, closed, sector(classes, inds, name), hq])
    return sorted(out, key=lambda r: r[3])


def founded(bindings):
    """{decade: [all, with a closing year, per sector…]} for dated firms (with or without a position)."""
    out = {}
    for b in bindings:
        val = lambda k: b[k]["value"] if k in b else None
        classes = val("classes").split("|") if val("classes") else []
        if not val("name") or not val("open") or not is_firm(classes):
            continue
        o, c = int(val("open")), int(val("close")) if val("close") else None
        if not 1000 <= o <= 2026 or (c is not None and c < o):
            continue
        row = out.setdefault(o // 10 * 10, [0, 0] + [0] * len(SECTORS))
        row[0] += 1
        row[1] += c is not None
        k = sector(classes, val("inds").split("|") if val("inds") else [], val("name"))
        if k is not None:
            row[2 + k] += 1
    return out


GRAPHS = [   # id, title, label, column (0 all, 1 closed, 2+k sector k), models [(id, label, column)]
    ("firms_founded", "Firms founded per decade", "Firms founded (Wikidata)", 0,
     [("firms_founded_closed", "Of these, closed (closing year recorded)", 1)]),
    ("firms_founded_making", "Firms founded per decade: making, food and drink, mining", SECTORS[5][0], 7,
     [("firms_founded_food", SECTORS[0][0], 2), ("firms_founded_mining", SECTORS[4][0], 6)]),
    ("firms_founded_money", "Firms founded per decade: finance, transport, shops", SECTORS[1][0], 3,
     [("firms_founded_transport", SECTORS[2][0], 4), ("firms_founded_shops", SECTORS[6][0], 8)]),
    ("firms_founded_media", "Firms founded per decade: publishing and services", SECTORS[3][0], 5,
     [("firms_founded_services", SECTORS[7][0], 9)]),
]
NOTE = ("Firms on Wikidata with a founding year, by the decade they were founded; the 2020s are a part decade. "
        "This is a record of the firms that lasted, grew famous or were written about, not a count of all "
        "businesses: most firms of every century left no trace, the oldest that remain are survivors, and modern "
        "firms are over-represented by Wikipedia's interest in them. Few closing years are recorded, so the closed "
        "line is a floor. National branches of foreign firms (\"Merck (United Kingdom)\") sometimes carry the "
        "parent company's founding year. Industries are sorted from each firm's Wikidata classes, stated industry "
        "or name; {none:,} of {all:,} dated firms say neither and count only in the total.")


def write_graphs(counts, log=print):
    """The CSVs and series.json entries of GRAPHS (series.json lives in data/curated/change)."""
    decades = range(1600, 2030, 10)                    # only a handful before 1600 (on the map)
    zero = [0] * (2 + len(SECTORS))
    total = sum(counts[d][0] for d in counts)
    stated = sum(sum(counts[d][2:]) for d in counts)
    path = DATA.parent / "series.json"
    series = [s for s in json.loads(path.read_text()) if not s["id"].startswith("firms_founded")]
    for gid, title, label, col, models in GRAPHS:
        for sid, lab, c, hidden in [(gid, label, col, False)] + [(m[0], m[1], m[2], True) for m in models]:
            with open(DATA / f"{sid}.csv", "w", newline="") as f:
                w = csv.writer(f)
                w.writerow(["year", "value"])
                w.writerows([d, counts.get(d, zero)[c]] for d in decades)
            row = {"id": sid, "theme": "Prosperity and work", "title": title if not hidden else f"Firms founded: {lab}",
                   "region": "all the isles", "unit": "firms", "unit_long": "firms founded in the decade",
                   "label": lab, "sources": ["wikidata_firms"], "file": f"{sid}.csv", "default": False}
            if hidden:
                row["hidden"] = True
            else:
                row["models"] = [m[0] for m in models]
                row["note"] = NOTE.format(none=total - stated, all=total)
            series.append(row)
    path.write_text(json.dumps(series, ensure_ascii=False, indent=1))
    log(f"graphs: {len(GRAPHS)} ({total:,} dated firms, {stated:,} with an industry, decades {decades[0]}–{decades[-1]})")


def run(log=print):
    bindings = fetch()
    rows = firms(bindings)
    (OUT / "layers").mkdir(parents=True, exist_ok=True)
    (OUT / "layers" / "firms.json").write_text(json.dumps([r[:5] + [len(SECTORS) if r[5] is None else r[5]] for r in rows], separators=(",", ":"), ensure_ascii=False))
    closed, hq = sum(1 for r in rows if r[4]), sum(1 for r in rows if r[6])
    meta = {"id": "firms", "title": "Firms open", "kind": "spans", "file": "layers/firms.json",
            "years": list(range(1600, 2030, 10)), "labels": {}, "unit": "",
            "legend": [{"color": c, "label": l} for l, c, _ in SECTORS] + [
                {"color": NOT_STATED[1], "label": NOT_STATED[0]}, {"color": CLOSED, "label": "Closed by then (where known)"}],
            "note": f"{len(rows):,} firms on Wikidata with a founding year and a position, coloured by industry. "
                    f"{hq:,} are placed at their head office town, spread by up to a kilometre so they do not sit on "
                    f"one dot, so a dot is the firm's base, not its works. Closing years are recorded for only "
                    f"{closed:,}: many long-gone firms still show as open. The map keeps the firms that lasted or "
                    "were written about, not every business of the time.",
            "sources": [SOURCE]}
    path = OUT / "layers.json"
    old = json.loads(path.read_text())["layers"] if path.exists() else []
    path.write_text(json.dumps({"layers": [l for l in old if l["id"] != "firms"] + [meta]}, ensure_ascii=False, indent=1))
    log(f"firms: {len(rows):,} ({closed:,} with a closing year, {hq:,} at the head office), "
        f"{(OUT / meta['file']).stat().st_size // 1024} KB")
    write_graphs(founded(bindings), log)


if __name__ == "__main__":
    run(lambda m: print(m, file=sys.stderr, flush=True))
