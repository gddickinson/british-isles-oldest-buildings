"""Historic maps: python -m app.historic_build

1. Lists the National Library of Scotland town plans (bounds and zooms from each layer's
   metadata.json) and writes app/static/data/historic/layers.json for the GUI.
2. Downloads the low-zoom tiles of the layers marked `bundle` (see app.historic_layers), converts
   them to WebP and keeps them in data/cache/historic_tiles/ (copied into dist/ by the static
   export, so the hosted copy has historic maps without network access). About 1 request/s.
"""
import json
import math
import re
import subprocess
import tempfile
import time
from pathlib import Path

import requests

from bidb.config import CACHE_DIR, ROOT, USER_AGENT

from .historic_layers import LAYERS, NLS, NLS_ATTR, TOWN_PREFIXES

OUT = ROOT / "app" / "static" / "data" / "historic"
TILES = CACHE_DIR / "historic_tiles"
S = requests.Session()
S.headers["User-Agent"] = USER_AGENT


def log(msg, t0=[time.time()]):
    print(f"[{time.time() - t0[0]:5.0f}s] {msg}", flush=True)


def _get(url, pause=1.0):
    time.sleep(pause)
    for attempt in range(3):
        try:
            r = S.get(url, timeout=90)
            if r.status_code in (429, 502, 503):
                time.sleep(5 * (attempt + 1))
                continue
            return r
        except requests.RequestException:
            time.sleep(5)
    return None


def town_plans():
    """[{name, url, bounds, min, max}] for every NLS town plan layer."""
    cache = CACHE_DIR / "historic_towns.json"
    if cache.exists():
        return json.loads(cache.read_text())
    out = []
    for prefix in TOWN_PREFIXES:
        r = _get(f"{NLS}?delimiter=/&prefix={prefix}")
        for layer in re.findall(r"<Prefix>([^<]+)</Prefix>", r.text if r else ""):
            if layer == prefix:
                continue
            m = _get(f"{NLS}{layer}metadata.json", pause=0.5)
            if not m or m.status_code != 200:
                continue
            try:
                meta = m.json()
                b = meta["bounds"]
                w, s, e, n = [float(v) for v in (b if isinstance(b, list) else str(b).split(","))]
            except (ValueError, KeyError):
                continue
            name = layer[len(prefix):].strip("/").replace("-", " ").replace("_", " ")
            name = re.sub(r"\s+", " ", re.sub(r"(\D)(\d{4})$", r"\1 \2", name)).strip().title()
            out.append({"name": name, "url": f"{NLS}{layer}{{z}}/{{x}}/{{y}}.png", "bounds": [w, s, e, n],
                        "min": int(meta.get("minzoom", 1)), "max": int(meta.get("maxzoom", 18))})
    out.sort(key=lambda t: t["name"])
    cache.write_text(json.dumps(out))
    return out


def tile_range(bounds, z):
    w, s, e, n = bounds
    def xy(lon, lat):
        x = (lon + 180) / 360 * 2 ** z
        y = (1 - math.asinh(math.tan(math.radians(lat))) / math.pi) / 2 * 2 ** z
        return int(x), int(y)
    x0, y0 = xy(w, n)
    x1, y1 = xy(e, s)
    return [(x, y) for x in range(x0, x1 + 1) for y in range(y0, y1 + 1)]


def bundle_layer(layer):
    z0, z1 = layer["bundle"]
    saved = tried = 0
    for z in range(z0, z1 + 1):
        for x, y in tile_range(layer["bounds"], z):
            dest = TILES / layer["key"] / str(z) / str(x) / f"{y}.webp"
            if dest.exists() or dest.with_suffix(".none").exists():
                saved += dest.exists()
                continue
            tried += 1
            data = None
            for tmpl in layer["urls"]:
                r = _get(tmpl.format(z=z, x=x, y=y), pause=0.6)
                if r is not None and r.status_code == 200 and r.headers.get("content-type", "").startswith("image/") \
                        and len(r.content) > 900:           # tiny PNGs are empty/transparent tiles
                    data = r.content
                    break
            dest.parent.mkdir(parents=True, exist_ok=True)
            if data is None:
                dest.with_suffix(".none").touch()            # remember the gap; do not re-request
                continue
            with tempfile.NamedTemporaryFile(suffix=".png") as tmp:
                Path(tmp.name).write_bytes(data)
                subprocess.run(["cwebp", "-quiet", "-q", "70", "-alpha_q", "80", tmp.name, "-o", str(dest)],
                               check=False)
            saved += dest.exists()
    size = sum(p.stat().st_size for p in (TILES / layer["key"]).rglob("*.webp"))
    log(f"{layer['key']}: {saved} tiles ({size / 1e6:.1f} MB), {tried} requested now")


IRISH_COUNTIES = ["antrim", "armagh", "carlow", "cavan", "clare", "cork", "derry", "londonderry", "donegal", "down",
                  "dublin", "fermanagh", "galway", "kerry", "kildare", "kilkenny", "laois", "queens", "leitrim",
                  "limerick", "longford", "louth", "mayo", "meath", "monaghan", "offaly", "kings", "roscommon",
                  "sligo", "tipperary", "tyrone", "waterford", "westmeath", "wexford", "wicklow"]


def irish_six_inch():
    """Two layers (first and second edition) of the Ordnance Survey of Ireland six-inch maps at the
    NLS, one tileset per county, each with its own bounds ("parts"); cached in <cache>."""
    from bidb.config import cache_dir
    cache = cache_dir() / "historic_ireland_six_inch.json"
    if cache.exists():
        found = json.loads(cache.read_text())
    else:
        found = {}
        for ed in ("", "_2nd"):
            for c in IRISH_COUNTIES:
                r = _get(f"{NLS}os/{c}{ed}/metadata.json", pause=0.3)
                if r is not None and r.status_code == 200:
                    m = r.json()
                    found[c + ed] = {"bounds": [float(x) for x in m["bounds"]], "max": int(m.get("maxzoom", 17))}
        cache.write_text(json.dumps(found))
    layers = []
    for ed, label, date in (("", "Ireland six-inch, first edition", "1829–1842"),
                            ("_2nd", "Ireland six-inch, later revision", "later 19th century")):
        parts = [{"url": f"{NLS}os/{c}{ed}/{{z}}/{{x}}/{{y}}.png", "bounds": v["bounds"], "name": c.title()}
                 for c, v in sorted(found.items()) if (c.endswith("_2nd") if ed else not c.endswith("_2nd"))
                 for c in [c.replace("_2nd", "")]]
        if parts:
            layers.append({"key": "ireland6" + ed.replace("_", ""), "label": label, "date": date,
                           "bounds": [min(p["bounds"][0] for p in parts), min(p["bounds"][1] for p in parts),
                                      max(p["bounds"][2] for p in parts), max(p["bounds"][3] for p in parts)],
                           "max": 17, "min": 8, "urls": [], "parts": parts, "attr": NLS_ATTR, "bundle": None})
    return layers


def main(bundle=True):
    OUT.mkdir(parents=True, exist_ok=True)
    towns = town_plans()
    log(f"town plans: {len(towns)}")
    layers = [{k: v for k, v in l.items()} for l in LAYERS] + irish_six_inch()
    log(f"Ireland six-inch: {sum(len(l['parts']) for l in layers if l.get('parts'))} county tilesets")
    (OUT / "layers.json").write_text(json.dumps({"layers": layers, "towns": towns}, ensure_ascii=False))
    if bundle:
        for layer in LAYERS:
            if layer.get("bundle"):
                bundle_layer(layer)


if __name__ == "__main__":
    import sys
    main(bundle="--no-tiles" not in sys.argv)
