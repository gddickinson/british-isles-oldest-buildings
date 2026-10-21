"""Parse Wikipedia's curated oldest-buildings list tables (UK and Scotland pages)."""
import re

from .config import CURATED_LIST_PAGE, WIKIPEDIA_API
from .http import request_json

_LINK = re.compile(r"\[\[([^\]|#]+)(?:#[^\]|]*)?(?:\|([^\]]*))?\]\]")
_FILE = re.compile(r"\[\[(?:File|Image):([^|\]]+)", re.I)
_FILE_FULL = re.compile(r"\[\[(?:File|Image):[^\[\]]*(?:\[\[[^\]]*\]\][^\[\]]*)*\]\]", re.I)


def _strip_wikitext(text):
    text = re.sub(r"<ref[^>]*/>", "", text)
    text = re.sub(r"<ref[^>]*>.*?</ref>", "", text, flags=re.S)
    text = re.sub(r"<!--.*?-->", "", text, flags=re.S)
    text = re.sub(r"\{\{(?:convert)\|([\d.]+)\|(\w+)[^}]*\}\}", r"\1 \2", text)
    text = re.sub(r"\{\{(?:circa|c\.?|ca)\|([^|{}]+)[^{}]*\}\}", r"c. \1", text, flags=re.I)
    text = re.sub(r"\{\{(?:nowrap|small|nobr)\|([^{}]*)\}\}", r"\1", text, flags=re.I)
    text = re.sub(r"\{\{sort\|[^|{}]*\|([^{}]*)\}\}", r"\1", text, flags=re.I)
    text = re.sub(r"\{\{[^{}]*\}\}", "", text)
    text = _FILE_FULL.sub("", text)
    text = _LINK.sub(lambda m: m.group(2) or m.group(1), text)
    text = re.sub(r"\[https?://\S+\s+([^\]]+)\]", r"\1", text)
    text = re.sub(r"\[https?://\S+\]", "", text)
    text = re.sub(r"'{2,}", "", text)
    text = re.sub(r"<[^>]+>", "", text)
    return text.replace("&nbsp;", " ").strip(" |\n")


def _cells(row_text):
    """Split one table row into cells (each line starting with '|' or '||' separators)."""
    cells, current = [], None
    for line in row_text.split("\n"):
        if line.startswith("|") and not line.startswith("|}"):
            if current is not None:
                cells.append(current)
            current = line[1:]
        elif current is not None:
            current += "\n" + line
    if current is not None:
        cells.append(current)
    flat = []
    for c in cells:
        flat.extend(c.split("||"))
    # drop cell attributes like 'style="..." | content'
    return [re.sub(r"^\s*[a-z]+=\"[^\"]*\"\s*\|", "", c).strip() for c in flat]


_HEADER_KEYS = [("location", ("location", "town", "place")),
                ("area", ("council", "county", "region")),
                ("date_text", ("date", "built", "year")),
                ("use", ("use", "type")),
                ("notes", ("notes", "description", "remarks"))]


def _column_roles(header_line_block):
    """Map column index -> role from a table's '!' header lines."""
    heads = []
    for line in header_line_block.split("\n"):
        if line.startswith("!"):
            heads.extend(h.strip() for h in line[1:].split("!!"))
    roles = {}
    for i, h in enumerate(heads):
        h_low = _strip_wikitext(h).lower()
        if i == 0:
            roles[i] = "name"
        elif not h_low or "image" in h_low or "photo" in h_low:
            roles[i] = "image"
        else:
            roles[i] = next((role for role, keys in _HEADER_KEYS
                             if any(k in h_low for k in keys)), "notes")
    return roles


def fetch_curated_list(page=CURATED_LIST_PAGE):
    """Rows of a Wikipedia list page -> dicts: title, name, period_heading, image, location,
    date_text, use, notes, source_page. Rows without a wiki link get title = plain name."""
    res = request_json(WIKIPEDIA_API, params={
        "action": "parse", "page": page, "prop": "wikitext",
        "format": "json", "formatversion": 2})
    wikitext = res["parse"]["wikitext"]
    entries, heading = [], ""
    for block in re.split(r"(?m)^(==[^=].*?==)\s*$", wikitext):
        if block.startswith("=="):
            heading = block.strip("= ").strip()
            continue
        for table in re.findall(r"\{\|.*?\n\|\}", block, flags=re.S):
            parts = table.split("\n|-")
            header = next((p for p in parts if "\n!" in "\n" + p.lstrip("\n")), "")
            roles = _column_roles(header)
            for row in parts[1:]:
                if row.lstrip("\n").startswith("!"):
                    continue
                cells = _cells(row)
                if len(cells) < 3:
                    continue
                link = _LINK.search(cells[0])
                name = _strip_wikitext(cells[0])
                if not name:
                    continue
                e = {"title": link.group(1).strip() if link else name, "name": name,
                     "linked": bool(link), "period_heading": heading, "source_page": page,
                     "image": None, "location": "", "area": "", "date_text": "",
                     "use": "", "notes": ""}
                for i, cell in enumerate(cells[1:], start=1):
                    m = _FILE.search(cell)
                    if m and not e["image"]:
                        e["image"] = m.group(1).strip()
                        continue
                    role = roles.get(i, "notes")
                    text = " ".join(_strip_wikitext(cell).split())
                    if role in ("name", "image") or not text:
                        continue
                    e[role] = f"{e[role]} {text}".strip() if role == "notes" else (e[role] or text)
                if e["area"]:
                    e["location"] = ", ".join(x for x in (e["location"], e["area"]) if x)
                entries.append(e)
    return entries


def titles_to_qids(titles):
    """Resolve enwiki titles (following redirects) to Wikidata QIDs -> {title: qid}."""
    out = {}
    titles = list(titles)
    for i in range(0, len(titles), 50):
        chunk = titles[i:i + 50]
        res = request_json(WIKIPEDIA_API, params={
            "action": "query", "titles": "|".join(chunk), "prop": "pageprops",
            "ppprop": "wikibase_item", "redirects": 1, "format": "json", "formatversion": 2})
        q = res.get("query", {})
        alias = {}
        for kind in ("normalized", "redirects"):
            for m in q.get(kind, []):
                alias[m["to"]] = alias.get(m["from"], m["from"])
        for page in q.get("pages", []):
            qid = page.get("pageprops", {}).get("wikibase_item")
            if not qid:
                continue
            t = page["title"]
            out[t] = qid
            src = t
            while src in alias:
                src = alias[src]
                out[src] = qid
    return out
