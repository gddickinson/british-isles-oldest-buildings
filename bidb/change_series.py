"""People and the environment through time (roadmap E1–E5): the series behind the "Change over time" graphs.

Curated inputs in `data/curated/change/`:
    sources.json   {id: {short, publisher, citation, licence, licence_url, url, download_url, checked, used}}
    series.json    [{id, title, theme, region, unit, unit_long, sources: [ids], note, modelled, default,
                     gap, zero, file}]     file = data/<file>.csv with columns year,value[,low,high]
    events.json    [{year, end, title, text, theme, citation}]   (or sources: [ids])

    python -m bidb.change_series     check them (every series and event cites a source with a licence) and
                                     write app/static/data/change/series.json for the GUI and the hosted copy
"""
import csv
import json
import sys

from .config import ROOT

SRC = ROOT / "data" / "curated" / "change"
OUT = ROOT / "app" / "static" / "data" / "change" / "series.json"
THEMES = ["People and settlements", "Prosperity and work", "Land and farming", "Industry and energy",
          "Climate and atmosphere", "Sea and coast", "This catalogue"]


def _num(v):
    v = (v or "").strip()
    if not v:
        return None
    f = float(v)
    return int(f) if f.is_integer() and abs(f) > 100 else round(f, 4)


def read_points(path):
    """[[year, value, low?, high?]] sorted by year; rows without a value are left out."""
    with open(path, newline="") as f:
        rows = list(csv.DictReader(f))
    pts = []
    for r in rows:
        if _num(r.get("value")) is None:
            continue
        p = [int(float(r["year"])), _num(r["value"])]
        lo, hi = _num(r.get("low")), _num(r.get("high"))
        if lo is not None and hi is not None:
            p += [lo, hi]
        pts.append(p)
    return sorted(pts, key=lambda p: p[0])


def check(sources, series, events):
    """Problems: a series or event without a known source, a source without licence or citation, unknown themes."""
    bad = []
    for sid, s in sources.items():
        for k in ("citation", "licence", "url"):
            if not s.get(k):
                bad.append(f"source {sid}: no {k}")
    for s in series + events:
        name = s.get("id") or s.get("title")
        if not s.get("sources") and not s.get("citation"):
            bad.append(f"{name}: no source")
        bad += [f"{name}: unknown source {x}" for x in s.get("sources", []) if x not in sources]
        if s.get("theme") not in THEMES:
            bad.append(f"{name}: unknown theme {s.get('theme')}")
    for s in series:
        if not (SRC / "data" / s["file"]).exists():
            bad.append(f"{s['id']}: missing data/{s['file']}")
    return bad


def build():
    sources = json.loads((SRC / "sources.json").read_text())
    series = json.loads((SRC / "series.json").read_text())
    events = json.loads((SRC / "events.json").read_text()) if (SRC / "events.json").exists() else []
    bad = check(sources, series, events)
    if bad:
        raise SystemExit("change series not written:\n  " + "\n  ".join(bad))
    order = {t: i for i, t in enumerate(THEMES)}
    out_series = []
    for s in sorted(series, key=lambda s: order[s["theme"]]):
        row = {k: v for k, v in s.items() if k != "file"}
        row["points"] = read_points(SRC / "data" / s["file"])
        out_series.append(row)
    used = {x for s in series + events for x in s.get("sources", [])}
    out = {"themes": THEMES, "sources": {k: v for k, v in sources.items() if k in used},
           "series": out_series, "events": events}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, ensure_ascii=False, separators=(",", ":")))
    return out


if __name__ == "__main__":
    o = build()
    print(f"{len(o['series'])} series, {len(o['events'])} events, {len(o['sources'])} sources → {OUT.relative_to(ROOT)}"
          f" ({OUT.stat().st_size // 1024} KB)", file=sys.stderr)
