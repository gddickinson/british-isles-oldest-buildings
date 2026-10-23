// Hosted (static) version: places, people and related-item routes. Searching places loads every place
// (data/places_<n>.json); a place's page loads its one shard, and building pages, people pages and map layers
// load light rows by location (data/pcells/, data/places_index.json); people from data/people.json.
(function () {
  let PLACES = null, BYID = null, PERSONS = null, LINKS = null, LOADING = null;
  const FACETS = ["kind_group", "kind_label", "nation", "period", "source"];
  const GROUPS = ["Battles & sieges", "Archaeological sites", "Lost places", "Parks, gardens & trees",
    "Industrial heritage", "Finds & treasures", "Plaques & people", "History events",
    "Legends & literature", "Maritime heritage", "Victorian era", "Underground", "Military heritage", "Museums & collections", "Bridges", "Excavations",
    "Nature & deep time", "Graves & burial grounds", "Markets & trade", "Infrastructure & utilities", "Sport & leisure", "Public institutions"];

  // a place's full row as the export leaves it: label, group, source and Wikidata link are put back
  const expand = (p, kinds) => {            // left out when they repeat the kind or the id (static_places.py)
    const [label, group] = kinds[p.kind] || [];
    if (!p.kind_label && label) p.kind_label = label;
    if (!p.kind_group && group) p.kind_group = group;
    if (!p.source) p.source = "Wikidata";
    if (!p.wikidata_id && /^Q\d+$/.test(p.id)) p.wikidata_id = p.id;
    if (!p.url && /^Q\d+$/.test(p.id)) p.url = "https://www.wikidata.org/wiki/" + p.id;
    return p;
  };
  const loadPeople = () => (PEOPLE = PEOPLE || fetch("data/people.json").then((r) => r.json())
    .catch(() => ({ persons: [], links: [] })).then((ppl) => {
      PERSONS = new Map(ppl.persons.map((p) => [p.id, p]));
      LINKS = ppl.links.map(([person_id, target_id, target_type, role, ref]) => ({ person_id, target_id, target_type, role, ref }));
    }));
  let PEOPLE = null;

  // every place, for searching, facets and exports (the places_<n>.json shards)
  const load = (meta) => (LOADING = LOADING || (async () => {
    const [shards] = await Promise.all([
      Promise.all((meta.place_shards || []).map((n) => fetch("data/" + n).then((r) => r.json()))), loadPeople()]);
    PLACES = shards.flat();
    const kinds = meta.place_kinds || {};
    PLACES.forEach((p) => {
      expand(p, kinds);
      p._text = fold([p.name, p.description, p.type, p.locality, p.designation, p.wikipedia_extract,
      JSON.stringify(p.extra || ""), p.other_names].join(" ")); });
    BYID = new Map(PLACES.map((p) => [p.id, p]));
  })());

  // light rows by location (pcells/<lat>_<lon>.json, places_index.json): building pages, a place's own page,
  // the people pages and plain map layers need names and positions only, not the 50 MB of places
  let INDEX = null;
  const CELLS = new Map(), LITE = new Map();
  const liteRow = ([id, name, lat, lon, l, g, date_text, building_id, year_start]) =>
    ({ id, name, lat, lon, kind_label: INDEX.labels[l], kind_group: INDEX.groups[g], date_text, building_id, year_start });
  let INDEX_LOADING = null;
  const loadIndex = () => (INDEX_LOADING = INDEX_LOADING || fetch("data/places_index.json").then((r) => r.json()).then((ix) => {
    INDEX = ix;
    ix.nowhere.forEach((r) => { const p = liteRow(r); LITE.set(p.id, p); });
    return ix;
  }));
  const loadCell = (key) => {
    if (!CELLS.has(key)) CELLS.set(key, fetch(`data/pcells/${key}.json`)
      .then((r) => { if (!r.ok) throw new Error(r.status); return r.json(); })
      .then((rows) => rows.map((r) => { const p = liteRow(r); LITE.set(p.id, p); return p; }))
      .catch(() => fetch(`data/pcells/${key}.json`).then((r) => r.json())       // one retry, then give up for now
        .then((rows) => rows.map((r) => { const p = liteRow(r); LITE.set(p.id, p); return p; }))
        .catch(() => { CELLS.delete(key); return []; })));
    return CELLS.get(key);
  };
  async function cellsAround(lat, lon, km) {
    const ix = await loadIndex(), [h, w] = ix.cell, keys = new Set();
    const dlat = km / 100, dlon = km / 60;      // generous at British latitudes, as near() below
    for (const a of [lat - dlat, lat + dlat]) for (const o of [lon - dlon, lon + dlon])
      keys.add(`${Math.floor(a / h) * h}_${Math.floor(o / w) * w}`);
    return (await Promise.all([...keys].filter((k) => ix.cells[k]).map(loadCell))).flat();
  }
  const loadAllLite = async () => {
    const ix = await loadIndex(), keys = Object.keys(ix.cells);
    // six requests at a time: a hundred at once makes small servers drop connections
    await Promise.all(Array.from({ length: 6 }, async () => { while (keys.length) await loadCell(keys.shift()); }));
    return [...LITE.values()];
  };
  // the same hash as static_places.shard_of: which shard holds a place's full row
  const shardOf = (id) => {
    let h = 0;
    for (let i = 0; i < id.length; i++) h = (Math.imul(h, 31) + id.charCodeAt(i)) >>> 0;
    return h % INDEX.shards;
  };
  const SHARDS = new Map();
  async function fullPlace(id, meta) {
    if (BYID && LOADING) { await LOADING; return BYID.get(id); }
    await loadIndex();
    const n = shardOf(id);
    if (!SHARDS.has(n)) SHARDS.set(n, fetch(`data/places_${n}.json`).then((r) => r.json()));
    const r = (await SHARDS.get(n)).find((p) => p.id === id);
    return r && expand({ ...r }, meta.place_kinds || {});
  }

  const fold = (s) => s.toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g, "");   // accents ignored
  const num = (v) => (v === null || v === "" || v === undefined || isNaN(+v) ? null : +v);
  function filters(p) {
    const f = { q: fold(p.get("q") || "").split(/\s+/).filter(Boolean), year_min: num(p.get("year_min")),
                year_max: num(p.get("year_max")), has_image: p.get("has_image") === "1", facets: {} };
    FACETS.forEach((k) => { const v = p.getAll(k); if (v.length) f.facets[k] = new Set(v); });
    return f;
  }
  function matches(r, f, skip) {
    if (f.q.length && !f.q.every((w) => r._text.includes(w))) return false;
    for (const [k, set] of Object.entries(f.facets)) if (k !== skip && !set.has(r[k] ?? "Unknown")) return false;
    if (f.year_min !== null && !(r.year_start >= f.year_min)) return false;
    if (f.year_max !== null && !(r.year_start != null && r.year_start <= f.year_max)) return false;
    if (f.has_image && !r.image_thumb) return false;
    return true;
  }
  const countBy = (rows, k) => {
    const m = {};
    rows.forEach((r) => { const v = r[k] ?? "Unknown"; m[v] = (m[v] || 0) + 1; });
    return Object.entries(m).sort((a, b) => b[1] - a[1]);
  };
  const SORTS = {
    oldest: (a, b) => (a.year_start == null) - (b.year_start == null) || (a.year_start - b.year_start) || a.name.localeCompare(b.name),
    newest: (a, b) => (a.year_start == null) - (b.year_start == null) || (b.year_start - a.year_start) || a.name.localeCompare(b.name),
    name: (a, b) => a.name.localeCompare(b.name, undefined, { sensitivity: "base" }),
  };
  const rad = Math.PI / 180;
  const dist = (a, b, c, d) => 12742 * Math.asin(Math.sqrt(Math.min(1,
    Math.sin((c - a) * rad / 2) ** 2 + Math.cos(a * rad) * Math.cos(c * rad) * Math.sin((d - b) * rad / 2) ** 2)));
  function near(lat, lon, km, limit, exclude, rows = PLACES) {
    return rows.filter((p) => p.lat != null && p.id !== exclude && Math.abs(p.lat - lat) < km / 100 && Math.abs(p.lon - lon) < km / 60)
      .map((p) => ({ id: p.id, name: p.name, kind_label: p.kind_label, kind_group: p.kind_group, date_text: p.date_text,
                     dist: dist(lat, lon, p.lat, p.lon) }))
      .filter((p) => p.dist <= km).sort((a, b) => a.dist - b.dist).slice(0, limit);
  }
  function peopleFor(id) {
    return LINKS.filter((l) => l.target_id === id && PERSONS.has(l.person_id)).map((l) => ({ ...PERSONS.get(l.person_id), role: l.role, ref: l.ref }))
      .sort((a, b) => a.role.localeCompare(b.role) || b.sitelinks - a.sitelinks);
  }
  function targetInfo(id, buildings) {
    const p = (BYID && BYID.get(id)) || LITE.get(id);
    if (p) return { name: p.name, date_text: p.date_text, lat: p.lat, lon: p.lon, what: p.kind_label };
    const b = buildings.get(id);
    return b ? { name: b.name, date_text: b.date_text, lat: b.lat, lon: b.lon, what: b.category } : { name: id };
  }

  const routes = {
    "places": (p) => {
      const f = filters(p);
      const cmp = SORTS[p.get("sort")] || SORTS.oldest, rank = window.nameRank(f.q, p.get("sort"));
      const rows = PLACES.filter((r) => matches(r, f)).sort(rank ? (a, b) => rank(a) - rank(b) || cmp(a, b) : cmp);
      const off = num(p.get("offset")) || 0, lim = Math.min(num(p.get("limit")) || 48, 500);
      return { total: rows.length, rows: rows.slice(off, off + lim) };
    },
    "places/facets": (p) => {
      const f = filters(p), out = {};
      FACETS.forEach((k) => { out[k] = countBy(PLACES.filter((r) => matches(r, f, k)), k); });
      out.kind_group.sort((a, b) => GROUPS.indexOf(a[0]) - GROUPS.indexOf(b[0]));
      return out;
    },
    "places/map": async (p, id, ctx) => {
      const f = filters(p);
      const plain = [...p.keys()].every((k) => k === "kind_group" || k === "kind_label");
      // a layer chosen by group or kind only: the light rows hold all a map marker needs
      const rows = plain && !LOADING ? (await loadAllLite()).map((r) => ({ ...r, _text: "" })) : (await load(ctx.meta), PLACES);
      return rows.filter((r) => r.lat != null && matches(r, f)).map((r) => ({ id: r.id, name: r.name, lat: r.lat, lon: r.lon,
        kind_label: r.kind_label, kind_group: r.kind_group, date_text: r.date_text, year_start: r.year_start }));
    },
    "places/near": (p) => near(+p.get("lat"), +p.get("lon"), num(p.get("km")) || 5, num(p.get("limit")) || 12, p.get("exclude")),
    "place": async (p, id, ctx) => {
      const r = await fullPlace(id, ctx.meta);
      if (!r) throw new Error("no place " + id);
      const around = r.lat != null ? await cellsAround(r.lat, r.lon, 5) : [];
      return { ...r, people: peopleFor(id), nearby_places: r.lat != null ? near(r.lat, r.lon, 5, 8, id, around) : [] };
    },
    "related": async (p, id, ctx) => {
      const b = ctx.buildings.get(id), ix = await loadIndex();
      const around = b && b.lat != null ? await cellsAround(b.lat, b.lon, 5) : [];
      return { people: peopleFor(id), objects: (ix.objects[id] || []).map(liteRow),
               places: b && b.lat != null ? near(b.lat, b.lon, 5, 12, id, around) : [] };
    },
    "people": (p, id, ctx) => {
      const q = (p.get("q") || "").toLowerCase(), role = p.get("role") || "";
      let rows = [...PERSONS.values()];
      if (q) rows = rows.filter((r) => `${r.name} ${r.description || ""}`.toLowerCase().includes(q));
      if (role) { const ids = new Set(LINKS.filter((l) => l.role === role).map((l) => l.person_id)); rows = rows.filter((r) => ids.has(r.id)); }
      const sort = p.get("sort") || "known";
      rows.sort(sort === "born" ? (a, b) => (a.birth == null) - (b.birth == null) || a.birth - b.birth
        : sort === "name" ? (a, b) => a.name.localeCompare(b.name) : (a, b) => b.sitelinks - a.sitelinks);
      const off = num(p.get("offset")) || 0, lim = Math.min(num(p.get("limit")) || 48, 200);
      return { total: rows.length, rows: rows.slice(off, off + lim).map((r) => ({ ...r,
        links: LINKS.filter((l) => l.person_id === r.id).slice(0, 12)
          .map((l) => ({ role: l.role, target_id: l.target_id, name: targetInfo(l.target_id, ctx.buildings).name })) })) };
    },
    "people/roles": () => countBy(LINKS.map((l) => ({ role: l.role })), "role"),
    "person": (p, id, ctx) => {
      const r = PERSONS.get(id);
      if (!r) throw new Error("no person " + id);
      return { ...r, links: LINKS.filter((l) => l.person_id === id)
        .map((l) => ({ role: l.role, ref: l.ref, target_id: l.target_id, target_type: l.target_type, ...targetInfo(l.target_id, ctx.buildings) })) };
    },
    // full filtered lists for the Export menu (ui_export.js)
    "places/export": (p) => PLACES.filter((r) => matches(r, filters(p))).sort(SORTS.oldest).map(({ _text, ...r }) => r),
    "people/export": (p) => {
      const q = (p.get("q") || "").toLowerCase(), role = p.get("role") || "";
      let rows = [...PERSONS.values()];
      if (q) rows = rows.filter((r) => `${r.name} ${r.description || ""}`.toLowerCase().includes(q));
      if (role) { const ids = new Set(LINKS.filter((l) => l.role === role).map((l) => l.person_id)); rows = rows.filter((r) => ids.has(r.id)); }
      return rows.sort((a, b) => b.sitelinks - a.sitelinks);
    },
  };

  const LIGHT = new Set(["place", "related", "places/map", "people", "person", "people/roles", "people/export"]);
  // called by static_api.js: returns undefined when the path is not a places/people route
  window.STATIC_PLACES = async function (parts, params, ctx) {
    const two = parts.slice(0, 2).join("/");
    const key = routes[two] ? two : routes[parts[0]] ? parts[0] : null;
    if (!key) return undefined;
    // routes that need every place load the shards; the others load what they need themselves
    if (LIGHT.has(key)) await loadPeople();
    else await load(ctx.meta);
    if (key === "people" || key === "person" || key === "people/export") if (!LOADING) await loadAllLite();
    const rest = parts.slice(key.split("/").length).join("/");
    return routes[key](params, rest ? decodeURIComponent(rest) : null, ctx);
  };
})();
