"""Building types BT2a: catalogue records and places mapped to the building types of bidb.building_types.

A record's Wikidata classes (buildings.classes, ';'-separated, most important first) are matched one by one:
    type     the class names a type ("tolbooth", "Prodigy house": its name or id)
    alias    curated Wikidata labels the thesaurus lacks (aliases.json `classes`: "English country house")
    fish     the class's FISH concept is a type's
    broader  the nearest broader FISH concept that is a type's (Wealden house → hall house type when the
             catalogue has no Wealden class, a ruined abbey → abbey); every concept at that distance counts
A record whose classes find none, or only a type a text rule `refines`, may match a text rule (`texts`: a pattern
on the name, the short description and the first two sentences of the Wikipedia extract: "is a Wealden hall
house" makes a hall house a Wealden house; limited to `categories` for records, and applied to places only of the
listed `kinds`; `slack` narrows the century allowed around the type's period) → via `text`. A record whose classes and texts find none may still match a name rule (`names`: a pattern on the head of the name, the
part before the first comma, within the listed categories: "... Castle" only among castles and fortifications;
"Gate Piers, Baldoon Castle" is not a castle) → via `name`, or its category (`categories`) → via `category`.
Matches by name, category or kind need a record begun within a century of the type's period of use when its
year is known (no Iron Age "Clinch Castle"). Of the types found, the most specific stay: a type is dropped when another
found type's FISH concept lies under its own (motte-and-bailey and castle → motte-and-bailey). The first type
left is the record's primary type. A type whose FISH concept is wider than the type (`within_period`: the
Georgian playhouse has THEATRE, the medieval hospital HOSPITAL) is found through FISH only for a record begun
within the type's period of use; a type limited to nations (`nations`) only for records there. BT1d: a general
type (windmill, school, theatre) gives way to its forms found with it (variant links: post mill, grammar school), and
one sharing a FISH concept with a `within_period` type gives way to it when the year fits (theatre → Georgian
playhouse); uses of a building (`secondary`: museum, school, hospital...) rank after its own type; text and name
rules may also refine a general type or a use ("Hulme Grammar School" labelled School, a castle that is a museum).

Places (not the kinds in `skip_kinds`: objects, plaques, finds, battles, wrecks...; places never repeat a
catalogue building): their own type label as a class (Wikidata class, or register type such as "Castle - tower house": the whole label,
then each part after " - ", ";" or ":", as in "Prehistoric domestic and defensive: hut circle, roundhouse"),
then the text rules, then its kind (`place_kinds`), then the name rules for that kind.

Records or places given a type by a wrong Wikidata class are listed with the reviewed reason in `not_types`
({entity id: {types, reason}}): those types are dropped for that entity.

Labels reviewed and left without a type (no type for them in the tree yet, or too general) are listed in
`not_in_tree`, so the report shows what is still unreviewed.

    python -m bidb.type_map [--report]     → table type_map (entity, source, type_id, via, label, is_primary)
"""
import json
import re
import sys
import time
from collections import Counter

from . import building_types, fish_types
from .db import connect

PATH = building_types.PATH.parent / "aliases.json"
COLUMNS = ("entity_id", "source", "type_id", "via", "label", "is_primary")
VIAS = ("type", "alias", "fish", "broader", "text", "name", "category", "kind")
NATIONS = ("England", "Scotland", "Wales", "Northern Ireland", "Republic of Ireland", "Isle of Man", "Jersey",
           "Guernsey")
SLACK = 100                 # years either side of a period for matches by text, name, category or kind
SENTENCE = re.compile(r"(?<=[.!?])\s+(?=[A-Z])")
CLOSED = re.compile(r"\s*\(gone or closed\)$")   # added to kind labels by the bridges, institutions, sports... stages


def load_aliases(path=PATH):
    return json.loads(path.read_text())


def problems(aliases, types):
    """Aliases that point at unknown types, name rules that do not compile, labels both aliased and left out."""
    ids, bad = {t["id"] for t in types}, []
    bad += [f"{where} {t!r}: unknown type" for where in ("within_period", "nations")
            for t in aliases.get(where, []) if t not in ids]
    bad += [f"nations {t!r}: unknown nation {n!r}" for t, ns in aliases.get("nations", {}).items()
            for n in ns if n not in NATIONS]
    for rule in aliases.get("texts", []):
        bad += [f"text rule {rule.get('pattern')!r}: unknown type {t!r}"
                for t in [rule.get("type")] + rule.get("refines", []) if t not in ids]
        try:
            re.compile(rule["pattern"])
        except (re.error, KeyError):
            bad.append(f"text rule {rule.get('pattern')!r}: not a pattern")
    for where in ("classes", "categories", "place_kinds", "place_types"):
        bad += [f"{where} {k!r}: unknown type {v!r}" for k, v in aliases.get(where, {}).items() if v not in ids]
    for rule in aliases.get("names", []):
        if rule.get("type") not in ids:
            bad.append(f"name rule {rule.get('pattern')!r}: unknown type {rule.get('type')!r}")
        try:
            re.compile(rule["pattern"])
        except (re.error, KeyError):
            bad.append(f"name rule {rule.get('pattern')!r}: not a pattern")
        if not rule.get("categories") and not rule.get("kinds"):
            bad.append(f"name rule {rule.get('pattern')!r}: no categories or kinds to limit it")
    for e, v in aliases.get("not_types", {}).items():
        bad += [f"not_types {e!r}: unknown type {t!r}" for t in v.get("types", []) if t not in ids]
        if not v.get("reason"):
            bad.append(f"not_types {e!r}: no reason")
    left = {fish_types.normalise(x) for x in aliases.get("not_in_tree", [])}
    bad += [f"class {k!r}: both aliased and left out" for k in aliases.get("classes", {})
            if fish_types.normalise(k) in left]
    return bad


class Matcher:
    """Class labels → building types. `concepts` as fish_types.concepts(), `lookup` a label → concept id."""

    def __init__(self, types, aliases, concepts=None, lookup=None, links=()):
        self.types = [t for t in types if not t.get("abroad")]
        self.concepts = concepts if concepts is not None else fish_types.concepts()
        self.lookup = lookup or fish_types.lookup
        norm = fish_types.normalise
        self.by_name = {}
        for t in self.types:
            self.by_name.setdefault(norm(t["name"]), t["id"])
            self.by_name.setdefault(norm(t["id"]), t["id"])
        self.aliases = {norm(k): v for k, v in aliases.get("classes", {}).items()}
        self.place_types = {norm(k): v for k, v in aliases.get("place_types", {}).items()}
        self.by_fish = {}       # a general type may share its concept with a type limited to a period
        for t in self.types:
            if t.get("fish"):
                self.by_fish.setdefault(t["fish"], []).append(t["id"])
        self.fish_of = {t["id"]: t.get("fish") for t in self.types}
        self.categories = aliases.get("categories", {})
        self.place_kinds = aliases.get("place_kinds", {})
        self.skip_kinds = aliases.get("skip_kinds", [])
        self.not_types = {e: set(v["types"]) for e, v in aliases.get("not_types", {}).items()}
        self.names = [dict(r, rx=re.compile(r["pattern"], re.I)) for r in aliases.get("names", [])]
        self.texts = [dict(r, rx=re.compile(r["pattern"], re.I), refines=set(r.get("refines", [])))
                      for r in aliases.get("texts", [])]
        self.within = set(aliases.get("within_period", []))
        self.secondary = set(aliases.get("secondary", []))
        self.parents = {}           # variant links: a general type (windmill) → its forms (post mill)
        for link in links:
            if link.get("kind") == "variant":
                self.parents.setdefault(link["to"], set()).add(link["from"])
        self.nations = aliases.get("nations", {})
        self.period = {t["id"]: (t["period"]["from"], t["period"].get("to", building_types.THIS_YEAR))
                       for t in self.types if t.get("period")}
        self._memo = {}

    def nearest(self, cid):
        """Type ids of the nearest concepts at or above `cid` that are types' (all those at the least distance)."""
        seen, front, step = {cid}, [cid], 0
        while front:
            hits = [t for c in front for t in self.by_fish.get(c, [])]
            if hits:
                return hits, step
            nxt = []
            for c in front:
                for b in self.concepts.get(c, {}).get("broader", []):
                    if b not in seen:
                        seen.add(b)
                        nxt.append(b)
            front, step = nxt, step + 1
        return [], step

    def for_class(self, label):
        """[(type id, via)] for one class label."""
        if label not in self._memo:
            key = fish_types.normalise(label)
            if key in self.by_name:
                t = self.by_name[key]       # "hospital": the medieval hospital too, if the year fits
                out = [(x, "fish") for x in self.by_fish.get(self.fish_of.get(t), [])
                       if x != t and x in self.within] + [(t, "type")]
            elif key in self.aliases:
                out = [(self.aliases[key], "alias")]
            else:
                cid = self.lookup(label)
                hits, step = self.nearest(cid) if cid else ([], 0)
                out = [(h, "fish" if step == 0 else "broader") for h in hits]
            self._memo[label] = out
        return self._memo[label]

    def general_of(self, t):
        """Every type `t` is a form of, through variant links (post mill → windmill)."""
        out, todo = set(), [t]
        while todo:
            for p in self.parents.get(todo.pop(), ()):
                if p not in out:
                    out.add(p)
                    todo.append(p)
        return out

    def refines(self, t, found):
        """Type `t` (of a text or name rule) may stand for the found primary type: nothing found, a general
        type of which `t` is a form, or a use (`secondary`: museum, school) of the building."""
        return not found or found[0][0] in self.general_of(t) or found[0][0] in self.secondary

    def _under(self, a, b):
        """Type a's FISH concept lies under type b's (a is the more specific)."""
        fa, fb = self.fish_of.get(a), self.fish_of.get(b)
        return bool(fa and fb and fa != fb and fa in fish_types.descendants(fb)) if self.concepts else False

    def allowed(self, t, via, year, nation, slack=SLACK):
        if t in self.nations and nation not in self.nations[t]:
            return False
        lo, hi = self.period.get(t, (None, None))
        if via in ("text", "name", "category", "kind") and year is not None and lo is not None \
                and not lo - slack <= year <= hi + slack:
            return False
        if t in self.within and via in ("fish", "broader"):
            return year is not None and lo <= year <= hi
        return True

    def specific(self, found, year=None, nation=None):
        """[(type, via, label)] allowed for the record's year and nation, without repeats, and without types
        that another found type lies under."""
        seen, out = set(), []
        for t, via, label in found:
            if t not in seen and self.allowed(t, via, year, nation):
                seen.add(t)
                out.append((t, via, label))
        out = [x for x in out if not any(self._under(y[0], x[0]) for y in out if y[0] != x[0])]
        dated = {self.fish_of.get(t) for t, _, _ in out if t in self.within} - {None}   # period-limited wins
        out = [x for x in out if x[0] in self.within or self.fish_of.get(x[0]) not in dated]
        general = {g for t, _, _ in out for g in self.general_of(t)}
        out = [x for x in out if x[0] not in general]
        return sorted(out, key=lambda x: x[0] in self.secondary)    # a museum in a country house: house first

    def by_name_rule(self, name, category=None, kind=None):
        head = (name or "").split(",")[0].strip()
        for r in self.names:
            if (category in r.get("categories", []) or kind in r.get("kinds", [])) and r["rx"].search(head):
                return [(r["type"], "name", r["pattern"])]
        return []

    def name_refined(self, found, name, year=None, nation=None, category=None, kind=None):
        """`found`, or a name rule's type put first when nothing was found or it refines the primary type
        ("Hulme Grammar School" labelled School)."""
        hit = self.specific(self.by_name_rule(name, category=category, kind=kind), year, nation)
        if hit and (not found or (hit[0][0] != found[0][0] and self.refines(hit[0][0], found))):
            return self.specific(hit + found, year, nation)
        return found

    def by_text(self, found, text, year=None, nation=None, category=None, kind=None):
        """`found` with the first text rule that matches put first, when nothing was found or the primary type
        is one the rule refines (the refined types are dropped)."""
        if not text or (found and not any(found[0][0] in r["refines"] or self.refines(r["type"], found)
                                          for r in self.texts)):
            return found
        for r in self.texts:
            if (kind is not None and kind not in r.get("kinds", [])) or \
                    (kind is None and r.get("categories") and category not in r["categories"]):
                continue
            if (found and found[0][0] in r["refines"] or self.refines(r["type"], found)) and r["rx"].search(text) \
                    and self.allowed(r["type"], "text", year, nation, r.get("slack", SLACK)):
                return [(r["type"], "text", r["pattern"])] + [x for x in found if x[0] not in r["refines"]
                                                                and x[0] != r["type"]]
        return found

    @staticmethod
    def text_of(name, description, extract):
        """The text that text rules search: name, short description, first two sentences of the extract."""
        return " | ".join(x for x in (name, description, " ".join(SENTENCE.split(extract or "")[:2])) if x)

    def record(self, classes, name, category, year=None, nation=None, text=None):
        """[(type, via, label)] for a catalogue record, primary first."""
        labels = [s.strip() for s in (classes or "").split(";") if s.strip()]
        found = self.specific([(t, via, label) for label in labels for t, via in self.for_class(label)],
                              year, nation)
        found = self.by_text(found, text, year, nation, category=category)
        found = self.name_refined(found, name, year, nation, category=category)
        if not found and category in self.categories:
            found = self.specific([(self.categories[category], "category", category)], year, nation)
        return found

    @staticmethod
    def label_parts(label):
        """A register type label and its parts: "A: b, c; D: e" → the whole, "b, c", "e"; "Castle - tower house"
        → the whole, "tower house"."""
        parts = [label]
        for piece in label.split(";"):
            piece = piece.strip().split(" - ", 1)[-1]
            parts.append(piece.split(":", 1)[-1].strip())
        return list(dict.fromkeys(p for p in parts if p))

    def place(self, kind, type_label, name, year=None, nation=None, text=None):
        """[(type, via, label)] for a place without a catalogue building."""
        found = []
        if type_label:
            type_label = CLOSED.sub("", type_label)
            key = fish_types.normalise(type_label)
            if key in self.place_types:
                found = [(self.place_types[key], "alias", type_label)]
            else:
                for part in self.label_parts(type_label):
                    if fish_types.normalise(part) in self.place_types:
                        found = [(self.place_types[fish_types.normalise(part)], "alias", type_label)]
                        break
                    found = [(t, via, type_label) for t, via in self.for_class(part)]
                    found = self.specific(found, year, nation)
                    if found:
                        break
        found = self.by_text(self.specific(found, year, nation), text, year, nation, kind=kind)
        found = self.name_refined(found, name, year, nation, kind=kind)
        if not found and kind in self.place_kinds:
            found = self.specific([(self.place_kinds[kind], "kind", kind)], year, nation)
        return found


def rows(conn, matcher):
    """Rows of the type_map table for every catalogue record and place."""
    out, skip = [], set(matcher.skip_kinds)
    for rid, classes, name, category, year, nation, desc, extract in conn.execute(
            "SELECT id, classes, name, category, year_start, nation, description, wikipedia_extract FROM buildings"):
        found = matcher.record(classes, name, category, year, nation, matcher.text_of(name, desc, extract))
        found = [f for f in found if f[0] not in matcher.not_types.get(rid, ())]
        out += [(rid, "building", t, via, label, int(i == 0)) for i, (t, via, label) in enumerate(found)]
    for pid, kind, label, name, year, nation, desc, extract in conn.execute(
            "SELECT id, kind, type, name, year_start, nation, description, wikipedia_extract FROM places"):
        if kind in skip:
            continue
        found = matcher.place(kind, label, name, year, nation, matcher.text_of(name, desc, extract))
        found = [f for f in found if f[0] not in matcher.not_types.get(pid, ())]
        out += [(pid, "place", t, via, lab, int(i == 0)) for i, (t, via, lab) in enumerate(found)]
    return out


def write(conn, out):
    conn.execute("DROP TABLE IF EXISTS type_map")
    conn.execute(f"CREATE TABLE type_map ({', '.join(COLUMNS)})")
    conn.execute("CREATE INDEX type_map_type ON type_map(type_id)")
    conn.execute("CREATE INDEX type_map_entity ON type_map(entity_id)")
    conn.executemany(f"INSERT INTO type_map VALUES ({', '.join('?' for _ in COLUMNS)})", out)
    conn.commit()


def run(log=print):
    t0 = time.time()
    data, aliases = building_types.load(), load_aliases()
    bad = problems(aliases, data["types"])
    if bad:
        raise ValueError("aliases.json: " + "; ".join(bad))
    conn = connect()
    conn.execute("PRAGMA busy_timeout = 120000")
    out = rows(conn, Matcher(data["types"], aliases, links=data["links"]))
    write(conn, out)
    n_b = conn.execute("SELECT COUNT(*) FROM buildings").fetchone()[0]
    typed = {s: len({r[0] for r in out if r[1] == s}) for s in ("building", "place")}
    log(f"[{time.time() - t0:5.0f}s] Building types: {typed['building']:,} of {n_b:,} records and "
        f"{typed['place']:,} places mapped to {len({r[2] for r in out})} types")


def report(conn, top=60):
    """Coverage lines: records typed by how, the types with most records, the unreviewed classes left over."""
    aliases = load_aliases()
    left = {fish_types.normalise(x) for x in aliases.get("not_in_tree", [])}
    lines = []
    for source, table in (("building", "buildings"), ("place", "places")):
        total = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        vias = Counter(dict(conn.execute("SELECT via, COUNT(*) FROM type_map WHERE source = ? AND is_primary "
                                         "GROUP BY via", (source,))))
        lines.append(f"{table}: {sum(vias.values()):,} of {total:,} typed "
                     f"({100 * sum(vias.values()) / total:.1f}%): "
                     + ", ".join(f"{v} {n:,}" for v, n in vias.most_common()))
    lines.append("Types with most records: " + ", ".join(
        f"{t} {n}" for t, n in conn.execute("SELECT type_id, COUNT(*) n FROM type_map WHERE source = 'building' "
                                            "AND is_primary GROUP BY type_id ORDER BY n DESC LIMIT 40")))
    unused = [t["id"] for t in building_types.load()["types"] if not t.get("abroad")
              and not conn.execute("SELECT 1 FROM type_map WHERE type_id = ?", (t["id"],)).fetchone()]
    lines.append(f"Types with no record or place ({len(unused)}): {', '.join(unused)}")
    miss = Counter()
    for (classes,) in conn.execute("SELECT classes FROM buildings WHERE id NOT IN "
                                   "(SELECT entity_id FROM type_map WHERE source = 'building')"):
        miss.update(x for x in (s.strip() for s in (classes or "").split(";"))
                    if x and fish_types.normalise(x) not in left)
    lines.append(f"Unreviewed classes of untyped records ({len(miss)}): "
                 + "; ".join(f"{k} {n}" for k, n in miss.most_common(top)))
    return lines


if __name__ == "__main__":
    if "--report" in sys.argv:
        print("\n".join(report(connect())))
    else:
        run()
