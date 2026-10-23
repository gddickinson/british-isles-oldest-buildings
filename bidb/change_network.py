"""The railway network through time for "Change over time" (roadmap E3): every railway station in the isles with
an opening date on Wikidata (and its closing date where recorded), as dots that follow the year slider.

    python -m bidb.change_network     → app/static/data/change/layers/stations.json + an entry in layers.json
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
    path = OUT / "layers.json"
    old = json.loads(path.read_text())["layers"] if path.exists() else []
    path.write_text(json.dumps({"layers": [l for l in old if l["id"] != "stations"] + [meta]}, ensure_ascii=False, indent=1))
    log(f"stations: {len(data)} ({closed} with a closing year), {(OUT / meta['file']).stat().st_size // 1024} KB")


if __name__ == "__main__":
    run(lambda m: print(m, file=sys.stderr, flush=True))
