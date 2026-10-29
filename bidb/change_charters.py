"""Borough charters 1042-1307 (roadmap C7b1, C7b2): the tables of the charters in British Borough Charters (1913, 1923).

Adolphus Ballard, British Borough Charters 1042-1216 (Cambridge, 1913; public domain), Introduction section 4,
"Sources", pp. xxvi-xxxiii: "the charters and other documents contained in this volume, their dates, their grantors,
and the sources from which our text is derived", England and Wales, Scotland and Ireland. Read from the page images
(Internet Archive britishboroughch00balluoft, leaves 32-39) into `charters_ballard_1913.csv`, one printed row per line
("Do." written out; "(2)" after a date is two charters; the sources column left out: the page is the citation).
Names "mentioned in Domesday Book are printed in capitals, and of those founded by mesne lords in italics" (column
`style`). Charters in the book's appendix and the undated Leges Quattuor Burgorum are not in the table.

The second volume (C7b2): Adolphus Ballard and James Tait, British Borough Charters 1216-1307 (Cambridge, 1923;
public domain, Tait d. 1944), Introduction section 3, "Sources", pp. xxv-xxxvi, read the same way from the page images
(Internet Archive britishboroughc00balluoft, leaves 33-45) into `charters_ballard_tait_1923.csv`: 532 printed rows,
"(a)", "(b)" after a date being separate charters of that year. Where "Do." stands under a king of another reign the
row names the king of the date (Stafford 1228 and 1261, Stamford 1257 under Edward I; Dublin 1280 and 1285 under
Henry III; the sources cited are of those reigns). Rows with no grantor printed (Brecon, Criccieth, Portsmouth 1255-6,
York 1256-67), the borough's own grants and the Totnes composition are kind `other`, counted but not drawn. Two
charters of the first volume are printed again with new dates (`REDATED`: Barnard Castle, Hugh de Balliol; Rathmore,
Maurice fitz Gerald) and count once, at the 1923 date; the footnote on Oxford University "1301 (b)": "Should be 1305".

- `check`: every date read, ranges in order and within 1040-1320, one style per borough in each volume, every borough
  placed (but `UNPLACED`).
- Map layer "Boroughs by their first charter" (kind `spans`, coloured by Ballard's typeface) and graph "Borough
  charters per decade, 1040-1309" (granted by kings; by lay lords; by bishops, abbots and popes), each charter at the
  middle of its dated range, kept within its volume's years (at most 1216 in the first, at least 1216 in the second;
  a break at 1216 where the volumes meet).

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
FILE_1923 = DATA / "charters_ballard_tait_1923.csv"
REDATED = {("Barnard Castle", "Hugh de Balliol"), ("Rathmore", "Maurice fitz Gerald")}   # vol. 1 rows printed again
FOOTNOTES = {("Oxford (University)", "1301 (b)"): 1305}                 # p. xxxii n. 1: "Should be 1305"
UNPLACED = {"Rathcool": "printed as in co. Tipperary; no place of the name found there",
            "Cinque Ports": "the confederation of ports, not one town (Hythe and Lydd have their own rows)"}
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
          "Drogheda (Louth)": "Drogheda",
          # second volume
          "Newcastle-upon-Tyne": "Newcastle upon Tyne", "Yarmouth, Great": "Great Yarmouth", "Builth": "Builth Wells",
          "Carnarvon": "Caernarfon", "Conway": "Conwy", "Dunheved (Launceston)": "Launceston", "Hull": "Kingston upon Hull",
          "Kingston-on-Thames": "Kingston upon Thames", "Kirkby Johannis": "Newton Arlosh", "Looe, West": "West Looe",
          "Lyme": "Lyme Regis", "Melcombe": "Melcombe Regis", "Nether Weare": "Lower Weare", "Windsor, New": "Windsor",
          "Wycombe": "High Wycombe", "Fraunceville (Newtown)": "Newtown (I. of W.)", "Agardsley": "Newborough (Staffs.)",
          "Skynburgh": "Skinburness", "Wavermouth": "Skinburness", "Westcheap": "Pontefract", "Aberavon": "Port Talbot",
          "Kilmaclenine": "Kilmaclenine Cross Roads", "Salisbury (Old)": "Salisbury", "Salisbury (New)": "Salisbury"}
POINTS = {"Hythe": (51.0715, 1.0842), "Kells (Meath)": (53.7264, -6.8792), "Kells (Kilkenny)": (52.5411, -7.2731),
          "Newport (Salop)": (52.7668, -2.3773), "Rathmore": (53.2172, -6.5644), "Richmond": (54.4036, -1.7343),
          "Bere (Merioneth)": (52.6597, -3.9017), "Bridgeton Pomeroy": (50.4320, -3.6800), "Burford (Salop)": (52.3110, -2.5940),
"Clifton (Worc.)": (52.2580, -2.4130), "Clonmel": (52.3550, -7.7040),
          "Kinver": (52.4490, -2.2280), "Newborough (Anglesey)": (53.1667, -4.3667), "Newborough (Staffs.)": (52.8167, -1.8000),
          "Newcastle-under-Lyme": (53.0109, -2.2278), "Newport (Pembroke)": (52.0180, -4.8330),
          "Newport (I. of W.)": (50.7010, -1.2890), "Newtown (I. of W.)": (50.7159, -1.4026), "Nova Villa (Newton)": (50.6650, -1.9900),
          "Overton": (52.9660, -2.9370), "Ravenserod": (53.5800, 0.1100), "Warenmouth": (55.6160, -1.7760),
          "Berwick": (55.7710, -2.0050)}
KINGS = ("Henry I", "Henry II", "Richard I", "John", "King John", "Stephen", "William I", "William II",
         "Edward Confessor", "William the Lion", "William", "David", "Alexander II", "Empress Maud",
         "Henry III", "Edward I", "Alexander III", "Robert I")
CHURCH = re.compile(r"\b(Archbp|Bp|Bishop|Abbot|Prior|Pope|abp|bp|abbot|dean)\b")
NOT_CHURCH = {"Jordan Bishop"}                        # a surname
OTHER = {"", "Mayor and community", "Free tenants and community", "(composition)"}
KINDS = {"crown": "Granted by kings", "lay": "By lay lords", "church": "By bishops, abbots and popes"}


def years(date):
    """(first, last, count) of a printed date: "1157-85" → (1157, 1185, 1); "1201 (2)" → two charters;
    "c. 1175" → 1175; "After 1212" and "Before 1189" → that year only; "?1296", "1230?" and "1228 (b)" → that year;
    "1272-c. 74" → (1272, 1274, 1)."""
    n = re.search(r"\((\d)\)", date)
    m = re.match(r"(?:c\. |After |Before |\?)?(\d{4})\??(?:-(?:c\. )?(\d{1,4}))?", date)
    if not m:
        raise ValueError(f"date not read: {date!r}")
    a, b = int(m.group(1)), m.group(2)
    last = int(str(a)[:4 - len(b)] + b) if b else a
    return a, last, int(n.group(1)) if n else 1


def kind(grantor):
    if grantor in OTHER:
        return "other"
    if grantor in KINGS or grantor == "(Fine)" or re.match(r"(John|Henry III) \(to |Henry III \(\?\)", grantor):
        return "crown"
    return "church" if CHURCH.search(grantor) and grantor not in NOT_CHURCH else "lay"


def place(borough):
    if borough in PLACES or borough in POINTS:
        return PLACES.get(borough, borough)
    return re.sub(r"\s*\((?!Meath|Kilkenny|Salop).*\)$", "", borough)


def load_volume(path, volume):
    rows = []
    with open(path, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            r["first"], r["last"], r["count"] = years(r["date"])
            if (r["borough"], r["date"]) in FOOTNOTES:
                r["first"] = r["last"] = FOOTNOTES[r["borough"], r["date"]]
            mid = (r["first"] + r["last"]) // 2
            # vol. 1: "can be dated before the death of King John"; vol. 2 runs from 1216 to the end of Edward I's reign
            r["year"] = min(mid, 1216) if volume == 1 else max(mid, 1216)
            r["volume"], r["kind"], r["place"] = volume, kind(r["grantor"]), place(r["borough"])
            rows.append(r)
    return rows


def load(path=FILE, path_1923=FILE_1923):
    """Both volumes' rows, without the first volume's charters printed again in the second (`REDATED`)."""
    return ([r for r in load_volume(path, 1) if (r["borough"], r["grantor"]) not in REDATED]
            + (load_volume(path_1923, 2) if path_1923 else []))


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
    bad = [f"{r['borough']} {r['date']}: range out of order or outside 1040-1320" for r in rows
           if not 1040 <= r["first"] <= r["last"] <= 1320]
    styles = defaultdict(set)
    for r in rows:
        styles[r.get("volume", 1), r["borough"]].add(r["style"])
    bad += [f"{b}: printed in {sorted(s)}" for (_, b), s in styles.items() if len(s) > 1 or not s <= set(STYLES)]
    bad += [f"{r['borough']}: no place for {r['place']!r}" for r in rows
            if not point(r["place"], t) and r["place"] not in UNPLACED]
    total = sum(r["count"] for r in rows if r.get("volume", 1) == 1)
    if not 300 <= total <= 340:                     # preface: "about 330 charters and documents"
        bad.append(f"{total} charters, the preface says about 330")
    return bad


def first_charters(rows=None, t=None):
    """[place, lat, lon, year, None, style index] of each place's earliest charter, oldest first."""
    rows, t = rows or load(), t or towns()
    first = {}
    for r in sorted(rows, key=lambda r: (r["year"], r["first"])):
        if r["place"] not in UNPLACED:
            first.setdefault(r["place"], r)
    keys = list(STYLES)
    return sorted([[p, *point(p, t), r["year"], None, keys.index(r["style"])] for p, r in first.items()],
                  key=lambda x: (x[3], x[0]))


def per_decade(rows=None):
    """{kind: {decade: charters}} with every decade 1040-1300, each charter at the middle of its range."""
    out = {k: {d: 0 for d in range(1040, 1310, 10)} for k in (*KINDS, "other")}
    for r in rows or load():
        out[r["kind"]][r["year"] // 10 * 10] += r["count"]
    return out


def facts(rows=None):
    rows = rows or load()
    d = per_decade(rows)
    total = Counter()
    for k in KINDS:
        total.update(d[k])
    v1, v2 = ([r for r in rows if r.get("volume", 1) == v] for v in (1, 2))
    n = lambda rs: sum(r["count"] for r in rs)
    later = [p for p in first_charters(rows) if p[3] > 1216]
    return {"charters": n(rows), "v1": n(v1), "v2": n(v2), "boroughs": len({r["place"] for r in rows}),
            "new_towns": len(later), "wide": n(r for r in rows if r["last"] - r["first"] > 20),
            "kinds": {k: sum(d[k].values()) for k in KINDS}, "other": sum(d["other"].values()),
            "peak": max(total, key=total.get), "peak_n": max(total.values()),
            "y1256": n(r for r in rows if r["first"] == r["last"] == 1256),
            "john": n(r for r in v1 if r["kind"] == "crown" and r["first"] >= 1199 and re.match(r"(King )?John\b", r["grantor"])),
            "henry3": n(r for r in v2 if r["grantor"].startswith("Henry III")),
            "edward1": n(r for r in v2 if r["grantor"] == "Edward I")}


NOTE = ("The charters and other documents granted to the boroughs of the isles from Edward the Confessor to the end of "
        "Edward I's reign, from the tables of sources in British Borough Charters: {v1} to 1216 in Adolphus Ballard's "
        "first volume (1913, pp. xxvi-xxxiii) and {v2} from 1216 to 1307 in the second, which James Tait finished "
        "after Ballard's death (1923, pp. xxv-xxxvi): {charters} charters to {boroughs} towns (sokens, gilds and the "
        "universities of Oxford and Cambridge counted with their town). Each charter is at the decade of the middle "
        "of its dated range, kept within its volume's years; {wide} are dated only within more than twenty years, so "
        "a decade's count is rough. Kings granted {crown}, lay lords {lay} and bishops, abbots and popes {church}; "
        "{other} more have no grantor printed or were made by the townspeople themselves, and are not drawn. "
        "{john} of the royal grants before 1216 are King John's, {henry3} after it Henry III's and {edward1} Edward "
        "I's. The busiest decade is the {peak}s ({peak_n}; {y1256} dated 1256 alone), although Tait regrets that of "
        "the Charter Rolls \"one of the missing rolls is that of 40 Henry III (1255-6) which was the most important "
        "year of the reign from our point of view\" (p. xxiv). The two volumes did not collect alike: Ballard writes "
        "of \"about 330 charters and documents relating to the boroughs of the British Isles, which can be dated "
        "before the death of King John\" (1913, Preface, p. v), while for 1216-1307 \"as regards charters in the "
        "strict sense, the collection is as nearly exhaustive as it was possible to make it\" but of documents such "
        "as grants of murage and pavage \"only typical examples could be given\" (1923, pp. v-vi, xxiii), so the "
        "line may step at 1216. John's charters as Count of Mortain and Lord of Ireland, the Lord Edward's, Edward of "
        "Caernarfon's as Prince of Wales and Richard of Cornwall's as King of the Romans count with the lords.")
BREAK = ("Ballard's first volume ends with King John's death in 1216 and the second (Ballard and Tait, 1923) begins "
         "there; the second aims to hold every charter in the strict sense")


def series(rows=None):
    rows = rows or load()
    d, f = per_decade(rows), facts(rows)
    note = NOTE.format(**{k: v for k, v in f.items() if k != "kinds"}, **f["kinds"])
    ids = {k: f"charters_{k}" for k in KINDS}
    src = ["ballard_1913_charters", "ballard_tait_1923_charters"]
    out = [_row(ids["crown"], "Borough charters per decade, 1040-1309", KINDS["crown"], "charters granted in the decade",
                src, "the isles", note, [ids["lay"], ids["church"]], unit="charters")]
    out += [_row(ids[k], f"Borough charters: {KINDS[k].lower()}", KINDS[k], "charters granted in the decade", src,
                 "the isles", unit="charters") for k in ("lay", "church")]
    out[0]["breaks"] = [[1216, BREAK]]
    for r in out:
        r["theme"] = "People and settlements"
    return {ids[k]: sorted(d[k].items()) for k in KINDS}, out


def layer(rows=None):
    rows = rows or load()
    data, f = first_charters(rows), facts(rows)
    by = Counter(STYLES[list(STYLES)[r[5]]] for r in data)
    meta = {"id": "charters", "title": "Boroughs by their first charter", "kind": "spans", "verb": "first charter",
            "count": "boroughs with a charter by",
            "file": "layers/charters.json", "years": list(range(1040, 1310, 5)), "labels": {}, "unit": "",
            "legend": [{"color": COLOURS[k], "label": v} for k, v in STYLES.items()],
            "note": f"{len(data)} towns with a charter (or other grant) dated before 1307 in British Borough Charters "
                    f"(Ballard 1913, Ballard and Tait 1923), {f['new_towns']} of them first after 1216, shown from the "
                    "middle of the dated range of their earliest one: "
                    f"{by[STYLES['capitals']]} mentioned as boroughs in Domesday Book, {by[STYLES['italics']]} founded "
                    "by lesser lords, as the tables print them. A town appears with its earliest charter in the "
                    "tables, not when it became a town or a borough. The charters to the Cinque Ports as a body, and "
                    "Rathcool's (printed as in county Tipperary), are not placed.",
            "sources": [{"short": "Ballard 1913", "licence": "Public domain (1913)",
                         "url": "https://archive.org/details/britishboroughch00balluoft",
                         "citation": "Adolphus Ballard, British Borough Charters 1042-1216 (Cambridge University Press, "
                                     "1913), Introduction section 4, Sources, pp. xxvi-xxxiii"},
                        {"short": "Ballard and Tait 1923", "licence": "Public domain (authors died 1915 and 1944)",
                         "url": "https://archive.org/details/britishboroughc00balluoft",
                         "citation": "Adolphus Ballard and James Tait, British Borough Charters 1216-1307 (Cambridge "
                                     "University Press, 1923), Introduction section 3, Sources, pp. xxv-xxxvi"}]}
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
    old_ids = {f"charters_{k}_1216" for k in KINDS}
    for sid, p in pts.items():
        _csv(sid, p)
    for sid in old_ids:
        (DATA / f"{sid}.csv").unlink(missing_ok=True)
    spath = DATA.parent / "series.json"
    keep = [s for s in json.loads(spath.read_text()) if s["id"] not in pts and s["id"] not in old_ids]
    spath.write_text(json.dumps(keep + out, ensure_ascii=False, indent=1))
    log(f"charters: {len(data)} places; {out[0]['note']}")


if __name__ == "__main__":
    run(lambda m: print(m, file=sys.stderr, flush=True))
