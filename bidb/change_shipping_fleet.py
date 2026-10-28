"""The UK-registered trading fleet 1950-2025 for "Change over time" (roadmap C5e2b2b1), read by bidb.change_shipping:
trading vessels of 500 gross tons and over registered in the United Kingdom, the Channel Islands and the Isle of
Man at the end of each year, from the Department for Transport's table FLE0301 (Shipping fleet statistics, Open
Government Licence v3.0; ODS read with the stdlib, `ods_rows`; cached in `<cache>/registers/dft/`): all, tankers,
container ships (from 1969), thousand gross tons, and the number of vessels.

DfT's own records of trading vessels of 500 gross tons and over to 1986, then Lloyd's/IHS data (1986 printed on both
bases), its own ship types from 2009 (both bases), Sea/ data from 2022: breaks at 1986, 2009 and 2022. Before 1986
the type columns hold the Annual Abstract's old types (cargo liners under Ro-Ro, tramps under bulk carrier before
1966), so only all vessels, tankers and container ships are drawn.

Checked against the Annual Abstract (`data/curated/change/data/shipping_500gt_annual_uk.csv`, read from the page
images: No. 109 table 267 p. 236, 1961-1971; No. 110 table 263 p. 236, 1962-1972; No. 112 table 283 p. 264,
1964-1974, "United Kingdom merchant vessels of 500 gross tons and over"): every row's types add to its total, the
editions agree on the totals (No. 112 revised two parts, `PART_REVISIONS`), and DfT's number, gross tons and
tankers equal the latest edition's in every year but 1962-1963 (`DFT_DIFFERS`).
"""
import csv
import xml.etree.ElementTree as ET
import zipfile

from .change_firms import DATA
from .change_registers import _download, _row

URL = "https://assets.publishing.service.gov.uk/media/699da84007d7bff3604d6c1b/fle0301.ods"
AA = DATA / "shipping_500gt_annual_uk.csv"
SOURCE, AA_SOURCE = "dft_fleet_uk", "annual_abstract_shipping_uk"
PARTS = ("passenger", "cargo_liners", "tramps", "bulk", "tankers")
COMPARED = ("number", "gross", "tankers")
COLUMNS = {"tankers": "Tanker gross", "container": "Container gross", "gross": "Total gross", "number": "Total number"}
PART_REVISIONS = {(1968, "tramps"): (2173, 2174), (1969, "cargo_liners"): (5645, 5646)}  # Nos. 109-110 → No. 112
# DfT's figures that differ from the Annual Abstract's latest edition (the types revised too; parts still add up)
DFT_DIFFERS = {(1962, "tankers"): (7488, 7486), (1963, "gross"): (20400, 20396), (1963, "tankers"): (7798, 7788)}
BREAKS = {1986: "From 1986 Lloyd's Register (IHS) data on new ship types; before, DfT's own records of trading vessels "
                "of 500 gross tons and over. 1986: {old:.2f} million gross tons on the old basis, {new:.2f} on the new",
          2009: "From 2009 DfT's ship types from IHS Statcode5 (before, the International Classification of Ship "
                "Types). 2009: {old:.2f} million gross tons on the old basis, {new:.2f} on the new",
          2022: "From 2022 data from Sea/ by Maritech (before, IHS); DfT: \"comparisons between 2022 and previous "
                "years should be used with caution\""}
T = "{urn:oasis:names:tc:opendocument:xmlns:table:1.0}"
OFFICE = "{urn:oasis:names:tc:opendocument:xmlns:office:1.0}"
TEXT = "{urn:oasis:names:tc:opendocument:xmlns:text:1.0}"


def ods_rows(path, sheet):
    """Rows of one sheet of an ODS file as lists of strings (numbers as their value; empty trailing cells cut)."""
    root = ET.fromstring(zipfile.ZipFile(path).read("content.xml"))
    for t in root.iter(f"{T}table"):
        if t.get(f"{T}name") != sheet:
            continue
        out = []
        for r in t.iter(f"{T}table-row"):
            cells = []
            for c in r.findall(f"{T}table-cell"):
                v = c.get(f"{OFFICE}value") or " ".join("".join(p.itertext()) for p in c.findall(f"{TEXT}p"))
                cells += [v] * min(int(c.get(f"{T}number-columns-repeated", "1")), 50)
            while cells and not cells[-1]:
                cells.pop()
            out.append(cells)
        return out
    raise KeyError(sheet)


def dft(path=None, log=print):
    """({year: {gross, tankers, container, number}}, {break year: old-basis row}); tonnage in thousand gross tons."""
    rows = ods_rows(path or _download(URL, "fle0301.ods", log, "registers/dft"), "FLE0301")
    head = next(r for r in rows if r and r[0] == "Year")
    idx = {k: next(i for i, h in enumerate(head) if h.startswith(v)) for k, v in COLUMNS.items()}
    new, old = {}, {}
    for r in rows[rows.index(head) + 1:]:
        if not r or not r[0][:4].isdigit():
            continue
        year = int(r[0][:4])
        vals = {k: (None if r[i] == "[x]" else round(float(r[i]), 1)) for k, i in idx.items()}
        if year in new and "[b]" in r[0]:
            old[year] = new[year]
        new[year] = vals
    return new, old


def aa_rows(data=None):
    if data is not None:
        return data
    with open(AA, newline="") as f:
        out = list(csv.DictReader(f))
    for r in out:
        for k in ("year", "no") + COMPARED + PARTS:
            r[k] = int(r[k]) if r[k] not in ("", None) else None
    return out


def check(data=None):
    """Problems: rows whose types do not add to the total (within rounding), editions printing a total differently,
    parts revised other than `PART_REVISIONS`."""
    bad, by = [], {}
    for r in aa_rows(data):
        parts = [r[k] for k in PARTS if r[k] is not None]
        if abs(sum(parts) - r["gross"]) > len(parts) - 1:
            bad.append(f"No. {r['no']} {r['year']}: types add to {sum(parts)}, printed {r['gross']}")
        by.setdefault(r["year"], []).append(r)
    for y, rs in by.items():
        for k in COMPARED + PARTS:
            vals = sorted({r[k] for r in rs if r[k] is not None})
            if len(vals) > 1 and PART_REVISIONS.get((y, k)) != tuple(vals):
                bad.append(f"{y} {k}: editions print {vals}")
    return bad


def latest(data=None):
    """{year: row} from the latest edition printing the year."""
    return {r["year"]: r for r in sorted(aa_rows(data), key=lambda r: r["no"])}


def differences(fle, data=None):
    """{(year, key): (Annual Abstract, DfT)} where DfT's figure differs from the latest edition's."""
    return {(y, k): (r[k], round(fle[y][k])) for y, r in latest(data).items() for k in COMPARED
            if round(fle[y][k]) != r[k]}


NOTE = ("Trading vessels (carrying cargo or passengers) of 500 gross tons and over registered in the United Kingdom, "
        "the Channel Islands and the Isle of Man at the end of each year, million gross tons, from the Department for "
        "Transport's table FLE0301: all, tankers and (from 1969) container ships. To 1974 these are the Annual "
        "Abstract's \"United Kingdom merchant vessels of 500 gross tons and over\" (Nos. 109, 110, 112, read from the "
        "page images: DfT gives the same number, gross tons and tankers in every year but 1962-1963, which it has "
        "revised slightly). The fleet was {g1950:.1f} million gross tons ({n1950:,} ships) in 1950, {g1961:.1f} "
        "million in 1961, and grew with its tankers to {gmax:.1f} million in {ymax} ({nmax:,} ships; tankers "
        "{tmax:.1f} million in {tymax}), then fell to {g1986:.1f} million in 1986 and {gmin:.1f} million in {ymin} "
        "({nmin:,} ships); it was {gpeak2:.1f} million in {ypeak2} and {glast:.1f} million in {last} ({nlast:,} ships, "
        "{clast:.1f} million of them container ships). The gross tons of the register graph to 1970 count every "
        "steam and motor ship of 500 gross tons and over, trading or not ({reg1961:.1f} million in 1961); these "
        "trading vessels are fewer. Breaks: 1986 (Lloyd's Register data), 2009 (new ship types), 2022 (new data "
        "supplier), each with the year on both bases where DfT prints it.")


def series(fle=None, old=None, log=print, reg1961=None):
    """({series id: {year: million gross tons}}, series.json rows)."""
    if fle is None:
        fle, old = dft(log=log)
    pts = {sid: {y: round(v[k] / 1000, 3) for y, v in sorted(fle.items()) if v[k] is not None}
           for sid, k in (("fleet_500gt_uk", "gross"), ("fleet_500gt_tankers_uk", "tankers"),
                          ("fleet_500gt_container_uk", "container"))}
    g, n = pts["fleet_500gt_uk"], {y: int(v["number"]) for y, v in fle.items()}
    tk = pts["fleet_500gt_tankers_uk"]
    last = max(g)
    ymax = max(g, key=g.get)
    ymin = min((y for y in g if y > ymax), key=g.get)
    ypeak2 = max((y for y in g if y > ymin), key=g.get)
    note = NOTE.format(g1950=g[1950], n1950=n[1950], g1961=g[1961], gmax=g[ymax], ymax=ymax, nmax=n[ymax],
                       tmax=max(tk.values()), tymax=max(tk, key=tk.get), g1986=g[1986], gmin=g[ymin], ymin=ymin,
                       nmin=n[ymin], gpeak2=g[ypeak2], ypeak2=ypeak2, glast=g[last], last=last, nlast=n[last],
                       clast=pts["fleet_500gt_container_uk"][last], reg1961=reg1961 or 0)
    unit = "million gross tons"
    rows = [_row("fleet_500gt_uk", f"UK-registered trading fleet, 1950-{last}", "All trading vessels", unit,
                 [SOURCE, AA_SOURCE], "United Kingdom", note, ["fleet_500gt_tankers_uk", "fleet_500gt_container_uk"],
                 unit="m gt"),
            _row("fleet_500gt_tankers_uk", "Trading fleet: tankers", "Tankers", unit, [SOURCE], "United Kingdom",
                 unit="m gt"),
            _row("fleet_500gt_container_uk", "Trading fleet: container ships", "Container ships", unit, [SOURCE],
                 "United Kingdom", unit="m gt")]
    rows[0]["breaks"] = [[y, t.format(old=old[y]["gross"] / 1000, new=fle[y]["gross"] / 1000) if y in old else t]
                         for y, t in BREAKS.items()]
    for r in rows:
        r["theme"] = "Industry and energy"
    return pts, rows


def problems(fle):
    """Everything `run` refuses: Annual Abstract checks, DfT differences other than `DFT_DIFFERS`, years missing."""
    bad = check()
    if differences(fle) != DFT_DIFFERS:
        bad.append(f"DfT differs from the Annual Abstract: {differences(fle)}")
    if sorted(fle) != list(range(1950, max(fle) + 1)):
        bad.append("DfT years missing")
    return bad
