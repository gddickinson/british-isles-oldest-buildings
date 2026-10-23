"""Census populations of the 26 counties of Ireland, 1841–2022 (CSO table FY001, CC BY 4.0), as a county map that
follows the year slider: each county's population as a share of its 1841 figure, showing the Famine's long
emptying of the west and the growth of Dublin (roadmap E3).

    python -m bidb.change_census      → app/static/data/change/layers/ireland_census.json + an entry in layers.json
"""
import json
import sys

from .change_layers import OUT
from .config import ROOT
from .http import request_json

FY001 = "https://ws.cso.ie/public/api.restful/PxStat.Data.Cube_API.ReadDataset/FY001/JSON-stat/2.0/en"
SOURCE = {"short": "CSO, Population at Each Census (FY001)", "licence": "CC BY 4.0",
          "url": "https://data.cso.ie/table/FY001",
          "citation": "Central Statistics Office, Ireland. FY001: Population at Each Census, 1841–2022, by county and sex"}
# Natural Earth areas (static/data/basemap/land.json) → the 26 traditional counties of the census
MERGE = {"Dún Laoghaire–Rathdown": "Dublin", "Fingal": "Dublin", "South Dublin": "Dublin", "North Tipperary": "Tipperary",
         "South Tipperary": "Tipperary", "Laoighis": "Laois"}
BINS = [(0, "#7f3b08"), (35, "#b35806"), (50, "#e08214"), (65, "#fdb863"), (85, "#d8d2c9"), (115, "#80cdc1"),
        (200, "#35978f"), (400, "#01665e")]


def populations():
    """{county: {year: people}} for both sexes."""
    d = request_json(FY001)
    dims = d["id"]
    size = d["size"]
    cats = [list(d["dimension"][k]["category"]["index"]) if isinstance(d["dimension"][k]["category"]["index"], list)
            else sorted(d["dimension"][k]["category"]["index"], key=d["dimension"][k]["category"]["index"].get) for k in dims]
    labels = [d["dimension"][k]["category"]["label"] for k in dims]
    out = {}
    for i, v in enumerate(d["value"]):
        idx, rest = [], i
        for n in reversed(size):
            idx.append(rest % n)
            rest //= n
        idx.reverse()
        key = [cats[k][idx[k]] for k in range(len(dims))]
        year, county, sex = labels[1][key[1]], labels[2][key[2]], labels[3][key[3]]
        if sex == "Both sexes" and county != "State" and v is not None:
            out.setdefault(county, {})[int(year)] = int(v)
    return out


def run(log=print):
    pops = populations()
    land = json.loads((ROOT / "app" / "static" / "data" / "basemap" / "land.json").read_text())["features"]
    feats = []
    for f in land:
        p = f["properties"]
        if p.get("c") != "Ireland":
            continue
        name = MERGE.get(p["n"], p["n"])
        if name in pops:
            feats.append({"type": "Feature", "geometry": f["geometry"], "properties": {"name": name, "pop": pops[name]}})
    missing = sorted(set(pops) - {f["properties"]["name"] for f in feats})
    (OUT / "layers").mkdir(parents=True, exist_ok=True)
    (OUT / "layers" / "ireland_census.json").write_text(json.dumps({"type": "FeatureCollection", "features": feats},
                                                                   separators=(",", ":"), ensure_ascii=False))
    years = sorted({y for p in pops.values() for y in p})
    labels = ["under 35%", "35–50%", "50–65%", "65–85%", "85–115%", "115–200%", "200–400%", "over 400%"]
    meta = {"id": "ireland_census", "title": "Ireland's counties: people compared with 1841", "kind": "choro",
            "file": "layers/ireland_census.json", "years": years, "base": 1841, "bins": [b for b, _ in BINS],
            "legend": [{"color": c, "label": t} for (_, c), t in zip(BINS, labels)], "unit": "% of the 1841 population",
            "note": "Population of each of the 26 counties at each census from 1841, as a share of its 1841 figure: the "
                    "Great Famine and a century of emigration halved most counties, and many in the west were still "
                    "below half in 2022, while Dublin and its neighbours grew. The six counties of Northern Ireland are "
                    "not in this table. Outlines are today's administrative counties.",
            "sources": [SOURCE]}
    path = OUT / "layers.json"
    old = json.loads(path.read_text())["layers"] if path.exists() else []
    path.write_text(json.dumps({"layers": [l for l in old if l["id"] != "ireland_census"] + [meta]}, ensure_ascii=False, indent=1))
    log(f"ireland census: {len(pops)} counties, {len(feats)} areas, missing {missing}")


if __name__ == "__main__":
    run(lambda m: print(m, file=sys.stderr, flush=True))
