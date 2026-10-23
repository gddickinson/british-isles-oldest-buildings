"""The railway network through time for "Change over time" (roadmap E3): every railway station in the isles with
an opening date on Wikidata (and its closing date where recorded), as dots that follow the year slider, and the dated
railway and canal lines of OpenHistoricalMap (CC0) as lines.

    python -m bidb.change_network     → app/static/data/change/layers/stations.json, rail_lines.json + layers.json
"""
import json
import sys

from .change_layers import OUT
from .http import sparql

COUNTRIES = {"Q145": "United Kingdom", "Q27": "Ireland", "Q9676": "Isle of Man", "Q25230": "Guernsey", "Q785": "Jersey"}
SOURCE = {"short": "Wikidata (railway stations)", "licence": "CC0", "url": "https://www.wikidata.org/wiki/Q55488",
          "citation": "Wikidata contributors, railway stations (Q55488 and subclasses) with opening (P1619) and closing "
                      "(P3999, P576) dates, queried 2026"}
NOT_RAIL = "wd:Q928830 wd:Q2175765 wd:Q17158079"          # metro stations, tram stops, bus stations


def stations():
    """[name, lat, lon, opened, closed or None] for stations with an opening year, oldest first."""
    rows = {}
    for c in COUNTRIES:
        for b in sparql(f"""SELECT ?i ?iLabel ?coord (MIN(YEAR(?o)) AS ?open) (MIN(YEAR(?x)) AS ?close) WHERE {{
              ?i wdt:P31/wdt:P279* wd:Q55488 ; wdt:P17 wd:{c} ; wdt:P625 ?coord .
              {{ ?i wdt:P1619 ?o }} UNION {{ ?i wdt:P571 ?o }}
              OPTIONAL {{ {{ ?i wdt:P3999 ?x }} UNION {{ ?i wdt:P576 ?x }} }}
              FILTER NOT EXISTS {{ ?i wdt:P31 ?t VALUES ?t {{ {NOT_RAIL} }} }}
              SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en". }} }}
            GROUP BY ?i ?iLabel ?coord"""):
            lon, lat = b["coord"]["value"][6:-1].split()
            opened = int(b["open"]["value"]) if "open" in b else None
            closed = int(b["close"]["value"]) if "close" in b else None
            if opened is None or opened < 1800 or (closed is not None and closed < opened):
                continue
            name = b["iLabel"]["value"].replace(" railway station", "").replace(" Railway Station", "")
            rows[b["i"]["value"]] = [name, round(float(lat), 4), round(float(lon), 4), opened, closed]
    return sorted(rows.values(), key=lambda r: r[3])


OHM = "https://overpass-api.openhistoricalmap.org/api/interpreter"
OHM_SOURCE = {"short": "OpenHistoricalMap (railway lines)", "licence": "CC0", "url": "https://www.openhistoricalmap.org/",
              "citation": "OpenHistoricalMap contributors: railway, narrow-gauge and canal ways with start_date and "
                          "end_date tags, queried 2026"}


def _year(v):
    try:
        return int(str(v).strip().lstrip("~")[:4]) if v else None
    except ValueError:
        return None


def _simplify(pts, tol=0.0015):
    """Douglas–Peucker on [lon, lat] points."""
    if len(pts) < 3:
        return pts
    (x0, y0), (x1, y1) = pts[0], pts[-1]
    dx, dy = x1 - x0, y1 - y0
    n = (dx * dx + dy * dy) ** 0.5 or 1e-12
    d = [abs(dy * (x - x0) - dx * (y - y0)) / n for x, y in pts[1:-1]]
    i = max(range(len(d)), key=d.__getitem__)
    if d[i] <= tol:
        return [pts[0], pts[-1]]
    return _simplify(pts[:i + 2], tol)[:-1] + _simplify(pts[i + 1:], tol)


def lines():
    """[kind, opened, closed or None, [[lon, lat], …]] for dated railway and canal ways on OpenHistoricalMap."""
    import requests
    from .config import USER_AGENT
    out, seen = [], set()
    for lat in range(49, 61, 2):
        for lon in range(-11, 2, 2):
            q = (f'[out:json][timeout:300];(way["railway"~"^(rail|narrow_gauge|light_rail)$"]["start_date"]({lat},{lon},{lat + 2},{lon + 2});'
                 f'way["waterway"="canal"]["start_date"]({lat},{lon},{lat + 2},{lon + 2}););out tags geom;')
            r = requests.post(OHM, data={"data": q}, headers={"User-Agent": USER_AGENT}, timeout=400)
            r.raise_for_status()
            for e in r.json()["elements"]:
                t = e.get("tags", {})
                o, c = _year(t.get("start_date")), _year(t.get("end_date"))
                if e["id"] in seen or o is None or "geometry" not in e or (c is not None and c < o):
                    continue
                seen.add(e["id"])
                pts = _simplify([[round(p["lon"], 4), round(p["lat"], 4)] for p in e["geometry"]])
                out.append(["canal" if t.get("waterway") == "canal" else "rail", o, c,
                            [[round(x, 3), round(y, 3)] for x, y in pts]])
    return out


def run(log=print):
    data = stations()
    (OUT / "layers").mkdir(parents=True, exist_ok=True)
    (OUT / "layers" / "stations.json").write_text(json.dumps(data, separators=(",", ":"), ensure_ascii=False))
    closed = sum(1 for r in data if r[4])
    meta = {"id": "stations", "title": "Railway stations open", "kind": "spans", "file": "layers/stations.json",
            "years": list(range(1825, 2030, 5)), "labels": {}, "unit": "",
            "legend": [{"color": "#2a5d8f", "label": "Open"}, {"color": "#b9b2a8", "label": "Closed by then (where known)"}],
            "note": f"{len(data):,} railway stations with an opening year on Wikidata, from the first passenger "
                    f"lines of the 1820s. Closing dates are recorded for only {closed:,} of them, so many stations "
                    "closed in the 1950s–60s still show as open: the growth of the network is clearer than its "
                    "contraction. Tram and metro stops are left out.",
            "sources": [SOURCE]}
    ways = lines()
    (OUT / "layers" / "rail_lines.json").write_text(json.dumps(ways, separators=(",", ":")))
    first = min(w[1] for w in ways)
    lmeta = {"id": "rail_lines", "title": "Railways and canals open", "kind": "lines", "file": "layers/rail_lines.json",
             "years": list(range(1760, 2030, 5)), "labels": {}, "unit": "",
             "legend": [{"color": "#7a2e2e", "label": "Railway open"}, {"color": "#2b6cb0", "label": "Canal open"},
                        {"color": "#b9b2a8", "label": "Closed by then"}],
             "note": f"{sum(1 for w in ways if w[0] == 'rail'):,} railway and {sum(1 for w in ways if w[0] == 'canal'):,} canal "
                     f"sections with an opening date on OpenHistoricalMap (from {first}), drawn if open in the year shown. "
                     "A volunteer map in progress: Scotland and northern England are well covered, Ireland and East "
                     "Anglia thinly, so gaps are missing data, not missing lines.",
             "sources": [OHM_SOURCE]}
    path = OUT / "layers.json"
    old = json.loads(path.read_text())["layers"] if path.exists() else []
    path.write_text(json.dumps({"layers": [l for l in old if l["id"] not in ("stations", "rail_lines")] + [meta, lmeta]},
                               ensure_ascii=False, indent=1))
    log(f"rail lines: {len(ways)} ways, {(OUT / lmeta['file']).stat().st_size // 1024} KB")
    log(f"stations: {len(data)} ({closed} with a closing year), {(OUT / meta['file']).stat().st_size // 1024} KB")


if __name__ == "__main__":
    run(lambda m: print(m, file=sys.stderr, flush=True))
