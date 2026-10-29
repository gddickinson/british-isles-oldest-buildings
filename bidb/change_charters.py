"""Borough charters 1042-1216 (roadmap C7b1): Ballard's table of the charters in British Borough Charters (1913).

Adolphus Ballard, British Borough Charters 1042-1216 (Cambridge, 1913; public domain), Introduction section 4,
"Sources", pp. xxvi-xxxiii: "the charters and other documents contained in this volume, their dates, their grantors,
and the sources from which our text is derived", England and Wales, Scotland and Ireland. Read from the page images
(Internet Archive britishboroughch00balluoft, leaves 32-39) into `charters_ballard_1913.csv`, one printed row per line
("Do." written out; "(2)" after a date is two charters; the sources column left out: the page is the citation).
Names "mentioned in Domesday Book are printed in capitals, and of those founded by mesne lords in italics" (column
`style`). Charters in the book's appendix and the undated Leges Quattuor Burgorum are not in the table.

- `check`: every date read, ranges in order and within 1040-1250, one style per borough, every borough placed.
- Map layer "Boroughs by their first charter" (kind `spans`, coloured by Ballard's typeface) and graph "Borough
  charters per decade, 1040-1219" (granted by kings; by lay lords; by bishops, abbots and popes), each charter at the
  middle of its dated range (at most 1216, the book's limit).

    python -m bidb.change_charters     check, write the layer, CSVs and series.json rows, then run bidb.change_series
"""
import csv
import json
import re
import sys
from collections import Counter, defaultdict

from .change_firms import DATA
from .change_layers import OUT
from .change_registers import _csv, _row
from .config import ROOT

FILE = DATA / "charters_ballard_1913.csv"
TOWNS = ROOT / "app" / "static" / "data" / "basemap" / "towns.json"
STYLES = {"capitals": "Domesday borough (capitals)", "italics": "Founded by a lesser lord (italics)",
          "roman": "Other borough"}
COLOURS = {"capitals": "#7a2e2e", "italics": "#2b6cb0", "roman": "#c08a2b"}
# the place a borough stands for, where the printed name is not the GeoNames town (or names more than one)
PLACES = {"Appleby": "Appleby-in-Westmorland", "Bridgenorth": "Bridgnorth", "Bridgewater": "Bridgwater",
          "Burton-on-Trent": "Burton upon Trent", "Lynn": "King's Lynn", "Newcastle-on-Tyne": "Newcastle upon Tyne",
          "Romney": "New Romney", "Rye & Winchelsea": "Winchelsea", "St Andrews": "Saint Andrews",
          "Stratford-on-Avon": "Stratford-upon-Avon", "Wearmouth": "Sunderland", "Yarmouth": "Great Yarmouth",
          "Elvet": "Durham", "Edinburgh (Canongate)": "Edinburgh", "Drogheda (Meath)": "Drogheda",
          "Drogheda (Louth)": "Drogheda"}
POINTS = {"Hythe": (51.0715, 1.0842), "Kells (Meath)": (53.7264, -6.8792), "Kells (Kilkenny)": (52.5411, -7.2731),
          "Newport (Salop)": (52.7668, -2.3773), "Rathmore": (53.2172, -6.5644), "Richmond": (54.4036, -1.7343)}
KINGS = ("Henry I", "Henry II", "Richard I", "John", "King John", "Stephen", "William I", "William II",
         "Edward Confessor", "William the Lion", "William", "David", "Alexander II", "Empress Maud")
CHURCH = re.compile(r"\b(Archbp|Bp|Bishop|Abbot|Prior|Pope)\b")
KINDS = {"crown": "Granted by kings", "lay": "By lay lords", "church": "By bishops, abbots and popes"}


def years(date):
    """(first, last, count) of a printed date: "1157-85" → (1157, 1185, 1); "1201 (2)" → two charters;
    "c. 1175" → 1175; "After 1212" and "Before 1189" → that year only."""
    n = re.search(r"\((\d)\)", date)
    m = re.match(r"(?:c\. |After |Before )?(\d{4})(?:-(\d{1,4}))?", date)
    if not m:
        raise ValueError(f"date not read: {date!r}")
    a, b = int(m.group(1)), m.group(2)
    last = int(str(a)[:4 - len(b)] + b) if b else a
    return a, last, int(n.group(1)) if n else 1


def kind(grantor):
    if grantor in KINGS or grantor.startswith("John (to ") or grantor == "(Fine)":
        return "crown"
    return "church" if CHURCH.search(grantor) else "lay"


def load(path=FILE):
    rows = []
    with open(path, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            r["first"], r["last"], r["count"] = years(r["date"])
            r["year"] = min((r["first"] + r["last"]) // 2, 1216)      # Ballard: "can be dated before the death of King John"
            r["kind"] = kind(r["grantor"])
            r["place"] = PLACES.get(r["borough"], re.sub(r"\s*\((?!Meath|Kilkenny|Salop).*\)$", "", r["borough"]))
            rows.append(r)
    return rows


def towns():
    """{name: (lat, lon)} of the largest GeoNames town of each name."""
    out = {}
    for name, lat, lon, _, pop in sorted(json.loads(TOWNS.read_text()), key=lambda t: t[4]):
        out[name] = (lat, lon)
    return out


def point(place, t):
    return POINTS.get(place) or t.get(place)


def check(rows=None, t=None):
    rows, t = rows or load(), t or towns()
    bad = [f"{r['borough']} {r['date']}: range out of order or outside 1040-1250" for r in rows
           if not 1040 <= r["first"] <= r["last"] <= 1250]
    styles = defaultdict(set)
    for r in rows:
        styles[r["borough"]].add(r["style"])
    bad += [f"{b}: printed in {sorted(s)}" for b, s in styles.items() if len(s) > 1 or not s <= set(STYLES)]
    bad += [f"{r['borough']}: no place for {r['place']!r}" for r in rows if not point(r["place"], t)]
    total = sum(r["count"] for r in rows)
    if not 300 <= total <= 340:                     # preface: "about 330 charters and documents"
        bad.append(f"{total} charters, the preface says about 330")
    return bad


def first_charters(rows=None, t=None):
    """[place, lat, lon, year, None, style index] of each place's earliest charter, oldest first."""
    rows, t = rows or load(), t or towns()
    first = {}
    for r in sorted(rows, key=lambda r: (r["year"], r["first"])):
        first.setdefault(r["place"], r)
    keys = list(STYLES)
    return sorted([[p, *point(p, t), r["year"], None, keys.index(r["style"])] for p, r in first.items()],
                  key=lambda x: (x[3], x[0]))


def per_decade(rows=None):
    """{kind: {decade: charters}} with every decade 1040-1210, each charter at the middle of its range."""
    out = {k: {d: 0 for d in range(1040, 1220, 10)} for k in KINDS}
    for r in rows or load():
        out[r["kind"]][r["year"] // 10 * 10] += r["count"]
    return out


def facts(rows=None):
    rows = rows or load()
    d = per_decade(rows)
    total = Counter()
    for k in KINDS:
        total.update(d[k])
    return {"charters": sum(r["count"] for r in rows), "boroughs": len({r["place"] for r in rows}),
            "wide": sum(r["count"] for r in rows if r["last"] - r["first"] > 20),
            "kinds": {k: sum(d[k].values()) for k in KINDS}, "peak": max(total, key=total.get),
            "peak_n": max(total.values()),
            "john": sum(r["count"] for r in rows if r["first"] >= 1199 and re.match(r"(King )?John\b(?!,)", r["grantor"]))}


NOTE = ("The charters and other documents granted to the boroughs of the isles before the death of King John, from "
        "the table of sources in Adolphus Ballard's British Borough Charters 1042-1216 (1913, pp. xxvi-xxxiii): "
        "{charters} charters to {boroughs} towns (London's sokens and gilds and Oxford's cordwainers counted with their "
        "town), "
        "by the decade of the middle of their dated range (1216 for ranges running past it); {wide} are dated only "
        "within more than twenty years, so a decade's count is rough. Kings granted {crown}, lay lords {lay} and "
        "bishops, abbots and popes {church}. The busiest decade is the {peak}s ({peak_n}); {john} of the royal grants "
        "are King John's (1199-1216). These are the charters Ballard found in print, rolls and town archives, not every "
        "grant made: he writes that he collected \"about 330 charters and documents relating to the boroughs of the "
        "British Isles, which can be dated before the death of King John\" (Preface, p. v). John's charters as Count "
        "of Mortain and Lord of Ireland count with the lords.")


def series(rows=None):
    rows = rows or load()
    d, f = per_decade(rows), facts(rows)
    note = NOTE.format(**{k: v for k, v in f.items() if k != "kinds"}, **f["kinds"])
    ids = {k: f"charters_{k}_1216" for k in KINDS}
    src = ["ballard_1913_charters"]
    out = [_row(ids["crown"], "Borough charters per decade, 1040-1219", KINDS["crown"], "charters granted in the decade",
                src, "the isles", note, [ids["lay"], ids["church"]], unit="charters")]
    out += [_row(ids[k], f"Borough charters: {KINDS[k].lower()}", KINDS[k], "charters granted in the decade", src,
                 "the isles", unit="charters") for k in ("lay", "church")]
    for r in out:
        r["theme"] = "People and settlements"
    return {ids[k]: sorted(d[k].items()) for k in KINDS}, out


def layer(rows=None):
    rows = rows or load()
    data = first_charters(rows)
    by = Counter(STYLES[list(STYLES)[r[5]]] for r in data)
    meta = {"id": "charters", "title": "Boroughs by their first charter", "kind": "spans", "verb": "first charter",
            "count": "boroughs with a charter by",
            "file": "layers/charters.json", "years": list(range(1040, 1225, 5)), "labels": {}, "unit": "",
            "legend": [{"color": COLOURS[k], "label": v} for k, v in STYLES.items()],
            "note": f"{len(data)} towns with a charter (or other grant) dated before 1216 in Ballard's British "
                    f"Borough Charters, shown from the middle of the dated range of their earliest one: "
                    f"{by[STYLES['capitals']]} mentioned as boroughs in Domesday Book, {by[STYLES['italics']]} founded "
                    "by lesser lords, as his table prints them. A town appears with its earliest charter in the "
                    "table, not when it became a town or a borough.",
            "sources": [{"short": "Ballard 1913", "licence": "Public domain (1913)",
                         "url": "https://archive.org/details/britishboroughch00balluoft",
                         "citation": "Adolphus Ballard, British Borough Charters 1042-1216 (Cambridge University Press, "
                                     "1913), Introduction section 4, Sources, pp. xxvi-xxxiii"}]}
    return data, meta


def run(log=print):
    rows = load()
    bad = check(rows)
    if bad:
        raise ValueError("; ".join(bad))
    data, meta = layer(rows)
    (OUT / "layers").mkdir(parents=True, exist_ok=True)
    (OUT / meta["file"]).write_text(json.dumps(data, separators=(",", ":"), ensure_ascii=False))
    path = OUT / "layers.json"
    old = json.loads(path.read_text())["layers"] if path.exists() else []
    path.write_text(json.dumps({"layers": [l for l in old if l["id"] != "charters"] + [meta]}, ensure_ascii=False, indent=1))
    pts, out = series(rows)
    for sid, p in pts.items():
        _csv(sid, p)
    spath = DATA.parent / "series.json"
    keep = [s for s in json.loads(spath.read_text()) if s["id"] not in pts]
    spath.write_text(json.dumps(keep + out, ensure_ascii=False, indent=1))
    log(f"charters: {len(data)} places; {out[0]['note']}")


if __name__ == "__main__":
    run(lambda m: print(m, file=sys.stderr, flush=True))
