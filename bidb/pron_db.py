"""Tables `pronunciations` and `pron_towns` (same SQLite file) and their queries.

pronunciations: one row per name form and variety for a building, place, person or town
    (entity_kind building|place|person|town). Towns are the places a record lies in (Wikidata
    P131), so "Cholmondeley Castle" can show how to say Cholmondeley.
pron_towns: record id -> town QID (and the town's English name).
"""
import hashlib
import re
from urllib.parse import quote

COLUMNS = ["entity_kind", "entity_id", "name", "lang", "variety", "ipa", "respell", "audio",
           "source", "source_url", "licence"]
SOURCES = {
    "Wikipedia": "CC BY-SA 4.0 (Wikipedia article text)",
    "Wikidata": "CC0 (Wikidata); recording licence on its Commons file page",
    "Wiktionary": "CC BY-SA 4.0 (Wiktionary)",
}


def create(conn):
    conn.executescript("""
        DROP TABLE IF EXISTS pronunciations;
        DROP TABLE IF EXISTS pron_towns;
        CREATE TABLE pronunciations (entity_kind TEXT, entity_id TEXT, name TEXT, lang TEXT,
            variety TEXT, ipa TEXT, respell TEXT, audio TEXT, source TEXT, source_url TEXT, licence TEXT);
        CREATE TABLE pron_towns (record_id TEXT, town_id TEXT, town TEXT);
        CREATE INDEX pron_entity ON pronunciations(entity_id);
        CREATE INDEX pron_towns_record ON pron_towns(record_id);
    """)


def write(conn, rows, towns):
    """rows: dicts with COLUMNS; towns: [(record_id, town_qid, town_name)]."""
    create(conn)
    conn.executemany(f"INSERT INTO pronunciations VALUES ({','.join('?' * len(COLUMNS))})",
                     [tuple(r.get(c, "") or "" for c in COLUMNS) for r in rows])
    conn.executemany("INSERT INTO pron_towns VALUES (?,?,?)", towns)
    conn.commit()


def has_tables(conn):
    return bool(conn.execute("SELECT 1 FROM sqlite_master WHERE name='pronunciations'").fetchone())


def other_names(conn, kind):
    """{record id: "names …"} of a record's names in other languages (Welsh, Gaelic, Irish …)."""
    out = {}
    if has_tables(conn):
        for rid, name in conn.execute("SELECT entity_id, name FROM pronunciations "
                                      "WHERE entity_kind = ? AND lang != 'en' AND name != ''", (kind,)):
            out.setdefault(rid, set()).add(name)
    return {k: " ".join(sorted(v)) for k, v in out.items()}


def audio_urls(name):
    """Commons recording -> {"page", "src", "mp3"}: the file page (author, licence), the original
    file and Wikimedia's MP3 transcode (Safari cannot play Ogg)."""
    if not name:
        return {}
    f = name.replace(" ", "_")
    f = f[:1].upper() + f[1:]
    h = hashlib.md5(f.encode()).hexdigest()
    base = f"https://upload.wikimedia.org/wikipedia/commons/{h[0]}/{h[:2]}/{quote(f)}"
    mp3 = (f"https://upload.wikimedia.org/wikipedia/commons/transcoded/{h[0]}/{h[:2]}/{quote(f)}/{quote(f)}.mp3"
           if not f.lower().endswith(".mp3") else base)
    return {"page": "https://commons.wikimedia.org/wiki/File:" + quote(f), "src": base, "mp3": mp3}


def _row(r):
    d = dict(zip(COLUMNS, r))
    d["audio_urls"] = audio_urls(d["audio"])
    return d


def for_record(conn, record_id):
    """{"own": [rows for the record itself], "towns": [{"id", "name", "rows"}]}."""
    if not has_tables(conn):
        return {"own": [], "towns": []}
    q = f"SELECT {','.join(COLUMNS)} FROM pronunciations WHERE entity_id = ? ORDER BY rowid"
    own = [_row(r) for r in conn.execute(q, (record_id,))]
    towns = []
    for town_id, town in conn.execute("SELECT town_id, town FROM pron_towns WHERE record_id = ?",
                                      (record_id,)):
        rows = [_row(r) for r in conn.execute(q, (town_id,))]
        if rows:
            towns.append({"id": town_id, "name": town, "rows": rows})
    return {"own": own, "towns": towns}


def coverage(conn):
    """Counts for the Data quality page / report: per entity kind and per variety."""
    if not has_tables(conn):
        return {}
    kinds = {k: n for k, n in conn.execute(
        "SELECT entity_kind, COUNT(DISTINCT entity_id) FROM pronunciations GROUP BY 1")}
    varieties = conn.execute("""SELECT variety, COUNT(*), SUM(ipa != ''), SUM(audio != '')
        FROM pronunciations GROUP BY 1 ORDER BY 2 DESC""").fetchall()
    with_town = conn.execute("""SELECT COUNT(DISTINCT t.record_id) FROM pron_towns t
        WHERE EXISTS (SELECT 1 FROM pronunciations p WHERE p.entity_id = t.town_id)""").fetchone()[0]
    return {"entities": kinds, "records_with_town": with_town,
            "varieties": [{"variety": v, "rows": n, "ipa": i or 0, "audio": a or 0}
                          for v, n, i, a in varieties]}


def search(conn, q="", variety="", kind="", limit=100, offset=0):
    """Pronunciation guide: rows with IPA, respelling or audio, filtered."""
    if not has_tables(conn):
        return {"total": 0, "rows": []}
    where, args = ["(ipa != '' OR respell != '' OR audio != '')"], []
    if q:
        where.append("name LIKE ?")
        args.append(f"%{q}%")
    if variety:
        where.append("variety = ?")
        args.append(variety)
    if kind:
        where.append("entity_kind = ?")
        args.append(kind)
    w = " AND ".join(where)
    # one row per name, variety and pronunciation (two records of one town give the same Wiktionary entry)
    one = f"""SELECT * FROM pronunciations WHERE rowid IN (SELECT MIN(rowid) FROM pronunciations WHERE {w}
              GROUP BY name, variety, ipa, respell, audio)"""
    total = conn.execute(f"SELECT COUNT(*) FROM ({one})", args).fetchone()[0]
    rows = conn.execute(f"SELECT {','.join(COLUMNS)} FROM ({one}) ORDER BY name COLLATE NOCASE LIMIT ? OFFSET ?",
                        args + [limit, offset])
    return {"total": total, "rows": [_row(r) for r in rows]}


def varieties(conn):
    """[(variety, rows with IPA/respelling/audio)] for the guide's filter."""
    if not has_tables(conn):
        return []
    return conn.execute("""SELECT variety, COUNT(*) FROM (SELECT DISTINCT name, variety, ipa, respell, audio
        FROM pronunciations WHERE ipa != '' OR respell != '' OR audio != '') GROUP BY 1 ORDER BY 2 DESC""").fetchall()


def all_rows(conn):
    if not has_tables(conn):
        return []
    return [_row(r) for r in conn.execute(f"SELECT {','.join(COLUMNS)} FROM pronunciations ORDER BY rowid")]


# spellings that are easy to get wrong: Welsh / Gaelic, Irish and Manx letters by nation; English traps anywhere
TRICKY = {
    "Wales": re.compile(r"\bll|dd|\brh|[bcdfghlmnprst]w[bcdfghlmnprst]|ŵ|ŷ|\bystrad|\bcwm", re.I),
    "Gaelic": re.compile(r"bh|mh|dh|fh|gh|aoi|ao|[áéíóúàèìòù]|\bkil|\bdrum|\bbally|\bach", re.I),
    "any": re.compile(r"ough|augh|cester|mondeley|leigh|wick\b|wich\b|\bbeau|belvoir|magdalen|marjori"
                      r"|\balnwick|\bglamis|\bkeswick|holborn|\bslough", re.I),
}
GAELIC_NATIONS = {"Scotland", "Republic of Ireland", "Northern Ireland", "Isle of Man"}


def tricky(name, nation):
    if TRICKY["any"].search(name):
        return True
    if nation == "Wales":
        return bool(TRICKY["Wales"].search(name))
    return nation in GAELIC_NATIONS and bool(TRICKY["Gaelic"].search(name))


def missing_tricky(conn, limit=200):
    """Buildings with a hard-looking name and no pronunciation for the record or its town:
    candidates for manual research (landmarks first)."""
    if not has_tables(conn):
        return []
    rows = conn.execute("""SELECT b.id, b.name, b.nation, b.county, b.wikidata_id, b.wikipedia_title
        FROM buildings b
        WHERE NOT EXISTS (SELECT 1 FROM pronunciations p WHERE p.entity_id = b.id
                          AND (p.ipa != '' OR p.respell != '' OR p.audio != ''))
          AND NOT EXISTS (SELECT 1 FROM pron_towns t JOIN pronunciations p ON p.entity_id = t.town_id
                          WHERE t.record_id = b.id AND (p.ipa != '' OR p.respell != '' OR p.audio != ''))
        ORDER BY b.landmark DESC, b.wikipedia_title IS NULL OR b.wikipedia_title = '', b.year_start""")
    out = []
    for r in rows:
        if tricky(r[1] or "", r[2] or ""):
            out.append(dict(zip(["id", "name", "nation", "county", "wikidata_id", "wikipedia_title"], r)))
            if len(out) >= limit:
                break
    return out
