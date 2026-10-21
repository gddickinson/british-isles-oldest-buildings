"""Choosing and ordering tour stops (pure functions; mirrored in app/static/tour_lib.js).

    interest(record)                 how worth a visit a record is (landmark, oldest of type, stories …)
    pick_stops(cands, centre, mode)  the best stops within the mode's radius, spread apart
    order(stops, loop)               nearest neighbour then 2-opt (shortest straight-line tour)
"""
import math

MODES = {
    # radius around the centre, stops, minimum spacing, travel speed (fallback), minutes per stop
    "walk": {"radius_km": 1.3, "min": 5, "max": 9, "spacing_km": 0.12, "kmh": 4.5, "stop_min": 15,
             "loop": False, "label": "Walk", "detour": 1.3},
    "cycle": {"radius_km": 7, "min": 5, "max": 7, "spacing_km": 1.5, "kmh": 15, "stop_min": 15,
              "loop": True, "label": "Cycle ride", "detour": 1.35},
    "drive": {"radius_km": 25, "min": 5, "max": 7, "spacing_km": 5, "kmh": 50, "stop_min": 35,
              "loop": True, "label": "Drive", "detour": 1.4},
}
TOP_GRADES = ("Grade I", "Category A", "Grade A", "World Heritage", "National Monument")


def km(a, b):
    """Great-circle distance between two (lat, lon) pairs."""
    rad = math.pi / 180
    h = (math.sin((b[0] - a[0]) * rad / 2) ** 2 +
         math.cos(a[0] * rad) * math.cos(b[0] * rad) * math.sin((b[1] - a[1]) * rad / 2) ** 2)
    return 12742 * math.asin(math.sqrt(min(1, h)))


def interest(r):
    """Score a candidate record (dict with catalogue columns, `stories` = number of stories)."""
    s = 1.0
    s += 3 if r.get("landmark") else 0
    s += 2 if r.get("oldest_of_type") else 0
    s += 1.5 if r.get("curated") else 0
    s += 1.5 if r.get("image_thumb") else 0
    s += min(r.get("stories") or 0, 3) * 1.2
    s += 1 if r.get("wikipedia_title") else 0
    s += 1 if any(g in (r.get("heritage_grade") or "") for g in TOP_GRADES) else 0
    y = r.get("year_start")
    s += 1.5 if y is not None and y < 1100 else 0.7 if y is not None and y < 1500 else 0
    s -= 2.5 if r.get("status") == "Demolished / destroyed" else 0
    return s


def pick_stops(cands, centre, mode):
    """Highest-interest candidates within the radius, at least spacing_km apart."""
    m = MODES[mode]
    near = [c for c in cands if km(centre, (c["lat"], c["lon"])) <= m["radius_km"]]
    near.sort(key=lambda c: -c["score"])
    chosen = []
    for c in near:
        if all(km((c["lat"], c["lon"]), (o["lat"], o["lon"])) >= m["spacing_km"] for o in chosen):
            chosen.append(c)
            if len(chosen) == m["max"]:
                break
    return chosen if len(chosen) >= m["min"] else []


def _length(path, loop):
    d = sum(km((a["lat"], a["lon"]), (b["lat"], b["lon"])) for a, b in zip(path, path[1:]))
    return d + (km((path[-1]["lat"], path[-1]["lon"]), (path[0]["lat"], path[0]["lon"])) if loop else 0)


def order(stops, loop=False, start=None):
    """Nearest-neighbour order from `start` (index; default the westernmost stop), improved by 2-opt."""
    if len(stops) < 3:
        return list(stops)
    rest = list(stops)
    first = rest.pop(start if start is not None else min(range(len(rest)), key=lambda i: rest[i]["lon"]))
    path = [first]
    while rest:
        last = path[-1]
        i = min(range(len(rest)), key=lambda i: km((last["lat"], last["lon"]), (rest[i]["lat"], rest[i]["lon"])))
        path.append(rest.pop(i))
    improved = True
    while improved:
        improved = False
        for i in range(1, len(path) - 1):
            for j in range(i + 1, len(path)):
                cand = path[:i] + path[i:j + 1][::-1] + path[j + 1:]
                if _length(cand, loop) < _length(path, loop) - 1e-9:
                    path, improved = cand, True
    return path
