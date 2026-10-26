"""Building types BT3b: materials and techniques found in the text about a building (bidb.material_map).

Texts are split into sentences; each term rule of material_aliases.json (`terms`) is tried on every sentence:
    pattern   the term itself ("timber-framed", "Bath stone", "pantiles"), case-insensitive
    cue       true: a building word (`cue` of the file: built, walls, faced, roof, church, house...) must stand
              within CUE_WINDOW characters of the term, so "brick" in "the brick kilns of the parish" or "slate"
              in "a slate plaque" does not count
    ignore    the rule's own pattern that drops a match within CUE_WINDOW characters of the term
    near      a pattern that must stand within CUE_WINDOW characters of the term (post-holes of a building, not
              of a fence)
The file's `ignore` pattern (fonts, tombs, statues, gates, quarries, kilns...) drops a match when it stands within
IGNORE_WINDOW characters of the term: a Purbeck marble font or wrought-iron gates say nothing of the building.
Wikipedia sections whose heading matches `skip_sections` (Churchyard, Geology, Location, Monuments...) are left
out, and so are sentences of a register description matching `skip_sentence` (its boundary walls, gatepiers and
gardens); the first sentence that matches is kept as the evidence.
"""
import re

SENTENCE = re.compile(r"(?<=[.!?])\s+(?=[A-Z0-9\"'(])")
CUE_WINDOW = 60             # characters either side of a term that may hold a building word
IGNORE_WINDOW = 30          # characters either side of a term that may hold a word that drops it
MAX_SENTENCE = 600          # longer runs are lists or tables, not sentences
EVIDENCE = 300              # characters of the evidence sentence kept


class Rules:
    """The term rules of material_aliases.json, compiled."""

    def __init__(self, aliases, known=None):
        self.cue = re.compile(aliases["cue"], re.I)
        self.ignore = re.compile(aliases["ignore"], re.I)
        self.skip = re.compile(aliases["skip_sections"], re.I)
        self.skip_sentence = re.compile(aliases["skip_sentence"]) if aliases.get("skip_sentence") else None
        opt = lambda t, k: re.compile(t[k], re.I) if t.get(k) else None
        self.terms = [(t["material"], re.compile(t["pattern"], re.I), bool(t.get("cue")), opt(t, "ignore"),
                       opt(t, "near")) for t in aliases["terms"] if known is None or t["material"] in known]
        self.any = re.compile("|".join(f"(?:{t['pattern']})" for t in aliases["terms"]), re.I)

    def _near(self, pattern, sentence, m, window):
        return pattern.search(sentence[max(0, m.start() - window):m.end() + window]) is not None

    def in_sentence(self, sentence):
        """{material id: matched text} for one sentence."""
        found = {}
        if not self.any.search(sentence):          # most sentences name no material: one pass over the text
            return found
        if self.skip_sentence and self.skip_sentence.match(sentence):
            return found
        for mid, pat, cue, own, near in self.terms:
            if mid in found:
                continue
            for m in pat.finditer(sentence):
                if self._near(self.ignore, sentence, m, IGNORE_WINDOW) or (
                        own and self._near(own, sentence, m, CUE_WINDOW)):
                    continue
                if (cue and not self._near(self.cue, sentence, m, CUE_WINDOW)) or (
                        near and not self._near(near, sentence, m, CUE_WINDOW)):
                    continue
                found[mid] = m.group(0)
                break
        return found

    def find(self, blocks):
        """blocks: [(where, text)] in order of preference → {material id: (term, where, evidence sentence)}."""
        out = {}
        for where, text in blocks:
            for sentence in sentences(text):
                for mid, term in self.in_sentence(sentence).items():
                    out.setdefault(mid, (term, where, evidence(sentence)))
        return out

    def article_blocks(self, article):
        """Sections of a cached article (bidb.stories: {"s": [[heading, text], ...]}) not skipped."""
        out = []
        for heading, text in (article or {}).get("s") or []:
            if heading and self.skip.search(heading):
                continue
            out.append(("Wikipedia" + (f" › {heading}" if heading else ""), text))
        return out


def sentences(text):
    for para in (text or "").split("\n"):
        for s in SENTENCE.split(para):
            s = s.strip()
            if 12 < len(s) <= MAX_SENTENCE:
                yield s


def evidence(sentence):
    return sentence if len(sentence) <= EVIDENCE else sentence[:EVIDENCE - 1].rstrip() + "…"
