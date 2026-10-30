"""The 3D models (roadmap SH3): the registry behind the page /models and the "3D model" links on record pages, and
what every model's data file shares (`python -m bidb.models3d [id ...] [--quotes]`).

Each model other than Stonehenge (bidb.stonehenge) has a builder module `bidb.model_<id>` whose `spec()` turns the
researched facts of `data/curated/models/<id>.json` (every number with a quoted source) into parts (stones, mounds,
passages, chambers, posts, banks: app/static/model_parts.js), camera views, sky events and the facts listed under the
model. `write` adds the ground (Environment Agency 1 m LiDAR in England, else the terrain tiles; flattened under a
mound, whose own shape is a part), the skyline (bidb.sky_horizon) and the bright stars, and writes
`app/static/data/model_<id>.json` and `model_<id>_dtm.bin`. `--quotes` checks every quote of the research files
(bidb.evidence.check → `data/models_check.json`).
"""
import importlib
import json
import math
import struct
import sys

from . import osgrid, sky_horizon
from .config import ROOT

HERE = ROOT / "data" / "curated" / "models"
OUT = ROOT / "app" / "static" / "data"
CHECK = ROOT / "data" / "models_check.json"

# Every model, in the order of the page /models. `route` for those with a page of their own.
MODELS = [
    {"id": "stonehenge", "name": "Stonehenge", "record": "Q39671", "route": "/stonehenge",
     "summary": "The stones now and as built, under the sun, moon and stars of any date back to the Neolithic."},
    {"id": "bryn_celli_ddu", "name": "Bryn Celli Ddu", "record": "Q2519821",
     "summary": "A passage tomb on Anglesey: the midsummer sunrise shines down the passage into the chamber."},
    {"id": "newgrange", "name": "Newgrange", "record": "Q339503",
     "summary": "The great passage tomb of the Boyne: the midwinter sunbeam through the roof-box."},
    {"id": "calanais", "name": "Calanais", "record": "hes-SM90054",
     "summary": "The stones of Lewis: the moon skimming the hills at the major standstill."},
    {"id": "orkney", "name": "Maeshowe, Stenness and Brodgar", "record": "Q507076",
     "records": ["Q507076", "Q1478558", "Q643631"],
     "summary": "The heart of Neolithic Orkney: the midwinter sunset down Maeshowe's passage."},
    {"id": "durrington", "name": "Woodhenge and Durrington Walls", "record": "Q534028",
     "records": ["Q534028", "Q17648062"],
     "summary": "The timber circles rebuilt from their postholes, facing the solstices."},
    {"id": "mousa", "name": "Mousa Broch", "record": "Q923376",
     "summary": "The best-preserved Iron Age tower, whole and in cutaway."},
    {"id": "loughcrew_t", "name": "Loughcrew Cairn T", "record": "Q202563", "research": "irish_tombs",
     "summary": "The hilltop passage tomb whose backstone the equinox sunrise lights."},
    {"id": "knowth", "name": "Knowth", "record": "Q1482124", "research": "irish_tombs",
     "summary": "The great mound with two passages, east and west, on their measured azimuths."},
    {"id": "dowth", "name": "Dowth", "record": "Q1253443", "research": "irish_tombs",
     "summary": "Two tombs on the west; the midwinter afternoon sun enters Dowth South."},
    {"id": "carrowkeel_g", "name": "Carrowkeel Cairn G", "record": "Q261318", "research": "irish_tombs",
     "summary": "A small cairn high in the Bricklieve Mountains, facing the midsummer sunset."},
    {"id": "avebury", "name": "Avebury", "record": "Q661855", "research": "earthworks",
     "summary": "The great henge from the Environment Agency's LiDAR, with its stones as mapped."},
    {"id": "silbury", "name": "Silbury Hill", "record": "Q225896", "research": "earthworks",
     "summary": "The largest prehistoric mound in Europe, from the LiDAR ground model."},
    {"id": "maiden_castle", "name": "Maiden Castle", "record": "Q1232816", "research": "earthworks",
     "summary": "The Iron Age hillfort's ramparts and entrances, from the LiDAR ground model."},
    {"id": "uffington", "name": "Uffington White Horse", "record": "Q1056493", "records": ["Q1056493", "Q2473790"], "research": "earthworks",
     "summary": "White Horse Hill: the hillfort, Dragon Hill and the Manger, from the LiDAR ground model."},
    {"id": "rt_glendalough", "name": "Glendalough round tower", "record": "Q113976325", "research": "old_plans",
     "summary": "An early medieval round tower, from its published dimensions."},
    {"id": "rt_kildare", "name": "Kildare round tower", "record": "Q124853386", "research": "old_plans",
     "summary": "An early medieval round tower, from its published dimensions."},
    {"id": "rt_ardmore", "name": "Ardmore round tower", "record": "Q61374651", "research": "old_plans",
     "summary": "An early medieval round tower, from its published dimensions."},
    {"id": "rt_clondalkin", "name": "Clondalkin round tower", "record": "Q24896274", "research": "old_plans",
     "summary": "An early medieval round tower, from its published dimensions."},
    {"id": "rt_brechin", "name": "Brechin round tower", "record": "Q2307632", "research": "old_plans",
     "summary": "An early medieval round tower, from its published dimensions."},
    {"id": "rt_abernethy", "name": "Abernethy round tower", "record": "Q1147465", "research": "old_plans",
     "summary": "An early medieval round tower, from its published dimensions."},
    {"id": "broch_dun_carloway", "name": "Dun Carloway", "record": "Q1265209", "research": "old_plans",
     "summary": "An Iron Age broch, whole and in cutaway, from its published dimensions."},
    {"id": "broch_clickimin", "name": "Clickimin Broch", "record": "Q923324", "research": "old_plans",
     "summary": "An Iron Age broch, whole and in cutaway, from its published dimensions."},
    {"id": "broch_dun_telve", "name": "Dun Telve", "record": "Q3342584", "research": "old_plans",
     "summary": "An Iron Age broch, whole and in cutaway, from its published dimensions."},
    {"id": "broch_dun_troddan", "name": "Dun Troddan", "record": "Q2131824", "research": "old_plans",
     "summary": "An Iron Age broch, whole and in cutaway, from its published dimensions."},
    {"id": "clava", "name": "Balnuaran of Clava", "record": "Q39505213", "research": "hougue_clava",
     "summary": "Two passage graves and a ring cairn in their stone circles, the passages facing the midwinter sunset."},
]


def ready(m):
    """True when the model has been built (its page works)."""
    return m["id"] == "stonehenge" or (OUT / f"model_{m['id']}.json").exists()


def links(static=False):
    """Record or place id → link of its 3D model, for detail views: built models, and in the local GUI the stone
    circles with mapped stones (bidb.model_circles)."""
    out = {}
    if not static:                                     # stone circles built on request (bidb.model_circles)
        from .model_circles import known
        out.update({eid: f"/model/circle/{eid}" for eid in known()})
    for m in MODELS:
        if not ready(m):
            continue
        href = page_file(m) if static else m.get("route", f"/model/{m['id']}")
        for r in m.get("records", [m["record"]]):
            out[r] = href
    return out


def page_file(m):
    return "stonehenge.html" if m["id"] == "stonehenge" else f"model_{m['id']}.html"


def get(mid):
    return next((m for m in MODELS if m["id"] == mid), None)


# Shared data ------------------------------------------------------------------------------------------------

STAR_NAMES = {
    "Alp CMa": "Sirius", "Alp Boo": "Arcturus", "Alp Lyr": "Vega", "Alp Aur": "Capella", "Bet Ori": "Rigel",
    "Alp CMi": "Procyon", "Alp Ori": "Betelgeuse", "Alp Aql": "Altair", "Alp Tau": "Aldebaran", "Alp Sco": "Antares",
    "Alp Vir": "Spica", "Bet Gem": "Pollux", "Alp PsA": "Fomalhaut", "Alp Cyg": "Deneb", "Alp Leo": "Regulus",
    "Alp Gem": "Castor", "Alp UMi": "Polaris", "Alp Dra": "Thuban", "Gam Ori": "Bellatrix", "Eps Ori": "Alnilam",
    "Zet Ori": "Alnitak", "Del Ori": "Mintaka", "Eta Tau": "Alcyone (Pleiades)", "Alp UMa": "Dubhe",
    "Eta UMa": "Alkaid", "Zet UMa": "Mizar", "Bet UMi": "Kochab", "Alp Per": "Mirfak", "Bet Per": "Algol",
    "Alp And": "Alpheratz", "Alp Cas": "Schedar", "Alp Hya": "Alphard", "Alp Peg": "Markab",
}


def stars(mag=5.5):
    """The bright stars as compact rows [ra, dec, pm ra, pm dec, V, B-V, (name)] (Yale Bright Star Catalogue)."""
    from .stonehenge_sources import bright_stars
    rows = []
    for ra, dec, pmra, pmdec, vmag, bv, name in bright_stars(mag):
        bayer = " ".join(name.lstrip("0123456789").split()[:2]) if name else ""
        row = [round(ra, 4), round(dec, 4), round(pmra, 3), round(pmdec, 3), round(vmag, 2), round(bv, 2)]
        if bayer in STAR_NAMES:
            row.append(STAR_NAMES[bayer])
        rows.append(row)
    return rows


def ground(lat, lon, size=600, step=2, source="tiles", flatten=None):
    """Ground heights round a point every `step` m over a `size` m square, rows north to south: (grid, meta).
    source "ea": Environment Agency LiDAR (England); "tiles": the terrain tiles (zoom 15, bilinear). `flatten`:
    {"c": [x, y], "r": metres, "edge": metres} levels the ground under a mound to the mean round its foot."""
    k = size // step
    half = (k - 1) * step / 2
    if source == "ea":
        from .stonehenge_sources import lidar
        e, n = osgrid.to_en(lat, lon)
        rows = lidar(e, n, size)
        grid = [[sum(rows[i * step + a][j * step + b] for a in range(step) for b in range(step)) / step ** 2
                 for j in range(k)] for i in range(k)]
    else:
        from .terrain_tiles import Terrain
        t = Terrain()
        grid = [[t.height(lat + (half - i * step) / 110574,
                          lon + (j * step - half) / (111320 * math.cos(math.radians(lat))), z=15)
                 for j in range(k)] for i in range(k)]
    if flatten:
        flatten_grid(grid, step, flatten)
    low = min(min(row) for row in grid)
    c = k // 2
    meta = {"n": k, "step": step, "x0": -half, "y0": half, "min": round(low, 2), "scale": 0.01,
            "ground": round(grid[c][c], 2), "source": source,
            "about": "rows north to south, columns west to east; height = min + value × scale (metres OD)"}
    return grid, meta


def flatten_grid(grid, step, flatten):
    """Level a square grid (rows north to south, centred on the origin) under a mound: within r of c to the mean
    height of the ring r..r+edge, blending back to the ground across that ring."""
    k = len(grid)
    half = (k - 1) * step / 2
    xy = lambda i, j: (j * step - half, half - i * step)        # noqa: E731
    (cx, cy), r, edge = flatten["c"], flatten["r"], flatten.get("edge", 6)
    ring = [grid[i][j] for i in range(k) for j in range(k) if r <= math.dist(xy(i, j), (cx, cy)) <= r + edge]
    level = sum(ring) / len(ring)
    for i in range(k):
        for j in range(k):
            d = math.dist(xy(i, j), (cx, cy))
            if d < r + edge:
                t = max(0.0, (d - r) / edge)
                grid[i][j] = level * (1 - t) + grid[i][j] * t
    return level


def despike(alt, width=3, jump=150):
    """Remove narrow spikes from a skyline (centidegrees every step): a run of up to `width` steps rising more than
    `jump` above both sides is a fault of the terrain data (a single bad pixel seen from close by), not a hill."""
    out, n = list(alt), len(alt)
    for i in range(n):
        for w in range(1, width + 1):
            lo, hi = out[(i - 1) % n], out[(i + w) % n]
            run = [out[(i + k) % n] for k in range(w)]
            if min(run) - max(lo, hi) > jump:
                for k in range(w):
                    out[(i + k) % n] = round(lo + (hi - lo) * (k + 1) / (w + 1))
                break
    return out


def cite(research, refs):
    """[{source, quote}] of a research file → [{title, url, quote}] for the page."""
    src = research["sources"]
    return [{"title": src[c["source"]]["title"], "url": src[c["source"]]["url"], "quote": c["quote"]}
            for c in refs or [] if c.get("source") in src]


CREDITS_TILES = "Ground and skyline: Terrain Tiles (Mapzen / AWS Open Data; Environment Agency LiDAR, SRTM, EU-DEM)"
CREDITS_EA = "Ground: Environment Agency LiDAR Composite DTM 1 m (Open Government Licence)"


def write(mid):
    """Build model `mid` from its builder's spec and write its data file and ground grid."""
    builder = importlib.import_module(f"bidb.model_{mid}")
    spec = builder.spec()
    grid, dtm = ground(spec["lat"], spec["lon"], spec.get("size", 600), spec.get("step", 2),
                       spec.get("ground", "tiles"), spec.get("flatten"))
    dtm["file"] = f"model_{mid}_dtm.bin"
    with open(OUT / dtm["file"], "wb") as f:
        f.write(struct.pack("<%dH" % (dtm["n"] ** 2), *[round((h - dtm["min"]) * 100) for r in grid for h in r]))
    hz = sky_horizon.compact(sky_horizon.cached_profile(round(spec["lat"], 4), round(spec["lon"], 4)))
    hz["alt"] = despike(hz["alt"])
    credits = spec.get("credits", []) + [CREDITS_EA if spec.get("ground") == "ea" else CREDITS_TILES,
                                         "Stars: Yale Bright Star Catalogue (BSC5), via HEASARC", "three.js r160 (MIT)"]
    data = {"id": mid, "name": spec["name"], "record": spec.get("record"),
            "origin": {"lat": round(spec["lat"], 7), "lon": round(spec["lon"], 7)},
            "dtm": dtm, "horizon": hz, "stars": stars(), "credits": credits,
            **{k: spec[k] for k in ("views", "cams", "events", "face", "start", "axis", "axis_length", "shadow",
                                    "facts", "built_year", "about", "built_label", "lantern", "axis_label", "ghosts",
                                    "labels_label") if k in spec}}
    (OUT / f"model_{mid}.json").write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")))
    return data


# Quotes ---------------------------------------------------------------------------------------------------

def research(mid):
    return json.loads((HERE / f"{mid}.json").read_text())


def _cites(node):
    """Every {source, quote} inside a research file, wherever it sits."""
    if isinstance(node, dict):
        if "source" in node and "quote" in node:
            yield node
        for v in node.values():
            yield from _cites(v)
    elif isinstance(node, list):
        for v in node:
            yield from _cites(v)


def claims(mid):
    """The quotes of a research file as evidence claims (one per source), for bidb.evidence.check."""
    r = research(mid)
    by = {}
    for c in _cites({k: v for k, v in r.items() if k != "sources"}):
        s = r["sources"].get(c["source"])
        if s and s.get("url"):
            by.setdefault(c["source"], []).append({"title": s["title"], "url": s["url"], "quote": c["quote"], "kind": "reference"})
    return [{"id": f"model-{mid}-{k}", "record": r.get("record"), "name": r.get("name"), "field": "model",
             "claim": f"facts of the 3D model of {r.get('name')}", "verdict": "documented", "sources": v}
            for k, v in by.items()]


def problems(mid):
    """Citations to sources the file does not list."""
    r = research(mid)
    return [f"{mid}: unknown source {c['source']}" for c in _cites({k: v for k, v in r.items() if k != "sources"})
            if c["source"] not in r["sources"]]


def main(argv):
    ids = [a for a in argv if not a.startswith("--")] or [m["id"] for m in MODELS if m["id"] != "stonehenge"
                                                          and (HERE / f"{m['id']}.json").exists()]
    if "--quotes" in argv:
        from .evidence import check
        prev = json.loads(CHECK.read_text()) if CHECK.exists() else {}
        rids = sorted({(get(mid) or {}).get("research", mid) for mid in ids})
        out = check(claims=[c for r in rids for c in claims(r)], path=CHECK)
        CHECK.write_text(json.dumps({**prev, **out}, indent=1) + "\n")
        return 0
    rid = lambda mid: (get(mid) or {}).get("research", mid)            # noqa: E731  the model's research file
    bad = [p for r in sorted({rid(mid) for mid in ids}) for p in problems(r)]
    for p in bad:
        print("problem:", p)
    for mid in ids:
        try:
            importlib.import_module(f"bidb.model_{mid}")
        except ModuleNotFoundError:
            print(f"{mid}: research only, no builder yet")
            continue
        d = write(mid)
        parts = {k: len(v) for k, v in d["views"].items()}
        print(f"{mid}: {parts} parts, ground {d['dtm']['n']}² at {d['dtm']['step']} m ({d['dtm']['source']}), "
              f"{len(d['stars'])} stars → app/static/data/model_{mid}.json")
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
