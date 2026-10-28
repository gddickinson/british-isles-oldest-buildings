"""Building types BT6c: labelled diagrams (plan, section, elevation) of building types, drawn as simple shapes
(`data/curated/building_types/diagrams_*.json`) from the type's quoted sources on its plan and structure.

Every label must be found word for word (ignoring case, punctuation and hyphens) in a quote of one of the type's
sources marked `about` plan or structure, or be a word of orientation (`GENERIC`), so a diagram shows nothing its
sources do not say; what a diagram has to draw without a source (proportions, roof outlines) its `note` says.

    {"id", "type", "view": plan|section|elevation, "title", "size": [w, h],
     "shapes": [[kind, ...coordinates, class], ...],
     "labels": [{"t": text, "at": [x, y], "to": [x, y] or [[x, y], ...], "a": start|end}],
     "note": what is schematic}

Shape kinds: ["rect", x, y, w, h, cls(, rx)], ["circle", cx, cy, r, cls], ["ellipse", cx, cy, rx, ry, cls],
["poly", [x, y, ...], cls] (closed), ["line", [x, y, ...], cls] (open), ["path", "<svg path>", cls].

    load()            every diagram, in file order
    validate(...)     problems: unknown types, kinds, classes, labels not in the sources, shapes off the canvas
    drawn_from(d, t)  the sources whose quotes give the diagram's labels
    for_type(id)      the diagrams of one type, each with the sources it is drawn from
"""
import json
import re

from .building_types import PATH, load as load_types

VIEWS = ("plan", "section", "elevation")
KINDS = {"rect": 5, "circle": 4, "ellipse": 5, "poly": 2, "line": 2, "path": 2}   # values before the class
CLASSES = {"room", "open", "wall", "walls", "stone", "timber", "earth", "bank", "ditch", "water", "roof", "yard",
           "land", "gap", "door", "window", "hearth", "stair", "dash", "thin", "ground", "chamber", "cairn", "kerb"}
GENERIC = {"plan", "section", "long section", "cross section", "elevation", "end elevation", "front", "back",
           "inside", "outside", "west", "east", "north", "south", "w", "e", "n", "s"}
PATH_CHARS = re.compile(r"^[MLHVCSQTAZmlhvcsqtaz0-9 .,\-]+$")


def files():
    return sorted(PATH.parent.glob("diagrams*.json"))


def load(paths=None):
    out = []
    for p in paths or files():
        out.extend(json.loads(p.read_text())["diagrams"])
    return out


def norm(text):
    """Lower case, hyphens and punctuation as spaces, "30 m" as "30m", single spaces."""
    text = re.sub(r"[‐-―\-/]", " ", text.lower())
    text = re.sub(r"[^\w\s]", " ", text)
    text = re.sub(r"(\d)\s+m\b", r"\1m", text)
    return " ".join(text.split())


def quoted(t):
    """The sources of a type on its plan or structure that carry a quote."""
    return [s for s in t.get("sources", []) if s.get("quote") and set(s.get("about") or []) & {"plan", "structure"}]


def _found(label, sources):
    n = norm(label)
    return [s for s in sources if n and n in norm(s["quote"])]


def _numbers(shape):
    nums = []
    for v in shape[1:]:
        if isinstance(v, (int, float)) and not isinstance(v, bool):
            nums.append(v)
        elif isinstance(v, list):
            nums.extend(v)
    return nums


def _points(shape):
    """The x, y points a shape reaches (circles and ellipses by their bounds), for the canvas check."""
    kind = shape[0]
    if kind == "rect":
        x, y, w, h = shape[1:5]
        return [(x, y), (x + w, y + h)]
    if kind == "circle":
        cx, cy, r = shape[1:4]
        return [(cx - r, cy - r), (cx + r, cy + r)]
    if kind == "ellipse":
        cx, cy, rx, ry = shape[1:5]
        return [(cx - rx, cy - ry), (cx + rx, cy + ry)]
    if kind in ("poly", "line"):
        v = shape[1]
        return list(zip(v[0::2], v[1::2]))
    return []


def _shape_problems(shape, w, h):
    if not isinstance(shape, list) or not shape or shape[0] not in KINDS:
        return [f"unknown shape {shape!r:.60}"]
    kind, n = shape[0], KINDS[shape[0]]
    if len(shape) < n + 1 or len(shape) > n + 2:
        return [f"{kind}: {len(shape) - 1} values"]
    cls = shape[n]
    out = [] if cls in CLASSES else [f"{kind}: unknown class {cls!r}"]
    if kind == "path":
        if not isinstance(shape[1], str) or not PATH_CHARS.match(shape[1]):
            out.append("path: not a plain SVG path")
        return out
    if kind in ("poly", "line") and (not isinstance(shape[1], list) or len(shape[1]) < 4 or len(shape[1]) % 2):
        return out + [f"{kind}: needs x, y pairs"]
    if not all(isinstance(v, (int, float)) for v in _numbers(shape[:n + 1])):
        return out + [f"{kind}: coordinates not numbers"]
    if any(not (-1 <= x <= w + 1 and -1 <= y <= h + 1) for x, y in _points(shape)):
        out.append(f"{kind} off the canvas: {shape[1:n]!r:.60}")
    return out


def validate(diagrams=None, data=None):
    diagrams = load() if diagrams is None else diagrams
    data = data or load_types()
    types = {t["id"]: t for t in data["types"]}
    problems, seen = [], set()
    for d in diagrams:
        did = d.get("id", "?")
        p = lambda msg: problems.append(f"{did}: {msg}")     # noqa: E731
        if did in seen:
            p("duplicate id")
        seen.add(did)
        t = types.get(d.get("type"))
        if t is None:
            p(f"unknown type {d.get('type')!r}")
            continue
        if d.get("view") not in VIEWS:
            p(f"view {d.get('view')!r}")
        if not d.get("title"):
            p("no title")
        w, h = d.get("size") or (0, 0)
        if not (w > 0 and h > 0):
            p("no size")
        for shape in d.get("shapes", []):
            for msg in _shape_problems(shape, w, h):
                p(msg)
        sources = quoted(t)
        if not d.get("labels"):
            p("no labels")
        for lab in d.get("labels", []):
            text = lab.get("t", "")
            if norm(text) not in GENERIC and not _found(text, sources):
                p(f"label {text!r} is in no quote on the type's plan or structure")
            x, y = lab.get("at") or (None, None)
            if x is None or not (0 <= x <= w and 0 <= y <= h):
                p(f"label {text!r} off the canvas")
            to = lab.get("to")
            for q in ([to] if to and not isinstance(to[0], list) else to or []):
                if not (0 <= q[0] <= w and 0 <= q[1] <= h):
                    p(f"label {text!r}: leader off the canvas")
            if lab.get("a") not in (None, "start", "end", "middle"):
                p(f"label {text!r}: anchor {lab.get('a')!r}")
    return problems


def drawn_from(d, t):
    """The type's quoted sources that give at least one of the diagram's labels, in the type's order."""
    sources, used = quoted(t), set()
    for lab in d.get("labels", []):
        used.update(id(s) for s in _found(lab["t"], sources))
    return [s for s in sources if id(s) in used]


def for_type(type_id, data=None, diagrams=None):
    data = data or load_types()
    t = next((x for x in data["types"] if x["id"] == type_id), None)
    if t is None:
        return []
    return [dict(d, sources=drawn_from(d, t)) for d in (load() if diagrams is None else diagrams)
            if d["type"] == type_id]


if __name__ == "__main__":
    ds = load()
    probs = validate(ds)
    print(f"{len(ds)} diagrams of {len({d['type'] for d in ds})} types; {len(probs)} problems")
    for msg in probs:
        print(" ", msg)
