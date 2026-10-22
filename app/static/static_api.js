// Hosted (static) version: answers the app's /api/* calls in the browser from data/*.json.
(function () {
  let DATA = null, META = null, HISTORY = null, LOADING = null, BYID = null;
  const load = () => (LOADING = LOADING || (async () => {
    {
      const [d, h] = await Promise.all([fetch("data/buildings.json").then((r) => r.json()),
                                        fetch("data/history.json").then((r) => r.json()).catch(() => null)]);
      META = d.meta; HISTORY = h;
      DATA = d.rows.concat(...await Promise.all((META.row_shards || []).map((n) => fetch("data/" + n).then((r) => r.json()))));
      const byId = BYID = new Map(DATA.map((r) => [r.id, r]));
      const planShards = {};        // floor plans: only the shard holding this building's plan, on demand
      window.STATIC_PLAN = (id) => {
        const i = (META.plan_index || {})[id];
        if (i === undefined) return Promise.resolve(null);
        planShards[i] = planShards[i] || fetch("data/" + META.plan_shards[i]).then((r) => r.json()).catch(() => ({}));
        return planShards[i].then((shard) => { const r = byId.get(id); if (r && shard[id]) r.plan_thumb = shard[id]; return shard[id] || null; });
      };
      DATA.forEach((r) => { r._text = [r.name, r.description, r.locality, r.located_in, r.county, r.classes,
        r.wikipedia_extract, r.curated_notes, r.style, r.dedication, r.type_claim, r.people_text, r.other_names].join(" ").toLowerCase()
        .normalize("NFD").replace(/[\u0300-\u036f]/g, ""); });     // accents ignored: "dun" finds "Dún"
    }
  })());
  // Loaded on demand (static_export._split_lazy): thumbnails (row.t = shard), detail-only fields
  // (row.d = shard) and building outlines. Each file is fetched once.
  const shardCache = {};
  const shard = (name) => (shardCache[name] = shardCache[name] || fetch("data/" + name).then((r) => r.json()).catch(() => ({})));
  async function withThumbs(list) {
    const rows = list.filter((x) => x && x.id && !x.image_thumb && BYID.get(x.id) && BYID.get(x.id).t != null);
    await Promise.all([...new Set(rows.map((x) => BYID.get(x.id).t))].map((i) => shard(META.thumb_shards[i])));
    for (const x of rows) x.image_thumb = (await shard(META.thumb_shards[BYID.get(x.id).t]))[x.id];
    return list;
  }
  async function full(r) {
    if (!r) return r;
    const d = r.d != null ? (await shard(META.detail_shards[r.d]))[r.id] : null;
    const [out] = await withThumbs([{ ...r, ...(d || {}) }]);
    return out;
  }
  let OUTLINES = null;
  const outlines = () => (OUTLINES = OUTLINES || Promise.all((META.outline_shards || []).map(shard))
    .then((parts) => parts.flatMap((p) => Object.entries(p).map(([id, o]) => ({ id, ...o })))));

  // Tours: data/tours.json; suggestions score the catalogue rows as bidb/tour_plan.interest does
  let TOURS = null, VISITS = null, DOMESDAY = null, DIGS = null, TREE = null;
  const tours = () => (TOURS = TOURS || fetch("data/tours.json").then((r) => r.json()).catch(() => []));
  const TOP = ["Grade I", "Category A", "Grade A", "World Heritage", "National Monument"];
  const interest = (r) => 1 + (r.landmark ? 3 : 0) + (r.oldest_of_type ? 2 : 0) + (r.curated ? 1.5 : 0) + (r.t != null ? 1.5 : 0)
    + Math.min((r.sk || []).length, 3) * 1.2 + (r.wikipedia_title ? 1 : 0) + (TOP.some((g) => (r.heritage_grade || "").includes(g)) ? 1 : 0)
    + (r.year_start != null && r.year_start < 1100 ? 1.5 : r.year_start != null && r.year_start < 1500 ? 0.7 : 0)
    - (r.status === "Demolished / destroyed" ? 2.5 : 0);
  const THEME_TEST = {
    highlights: () => true,
    trail: () => true,
    literary: () => false,                  // literary places are not catalogue buildings
    maritime: (r) => /Lighthouse|Harbour|Dock/.test(r.category || ""),
    industrial: (r) => r.category_group === "Industry & transport",
    victorian: (r) => r.period === "Victorian",
    ghosts: (r) => (r.sk || []).some((k) => k !== "curiosity"),
    prehistoric: (r) => ["Neolithic", "Bronze Age", "Iron Age"].includes(r.period) || r.category_group === "Prehistoric",
    castles: (r) => r.category_group === "Fortification",
    churches: (r) => r.category_group === "Religious" && r.year_start != null && r.year_start < 1300,
    roman: (r) => r.category_group === "Roman" || (r.period === "Roman Britain" && ["England", "Wales", "Scotland"].includes(r.nation)),
  };

  const num = (v) => (v === null || v === "" || v === undefined || isNaN(+v) ? null : +v);
  const rad = Math.PI / 180;
  const dist = (a, b, lat, lon) => {
    if (a == null || lat == null) return null;
    const h = Math.sin((lat - a) * rad / 2) ** 2 + Math.cos(a * rad) * Math.cos(lat * rad) * Math.sin((lon - b) * rad / 2) ** 2;
    return 12742 * Math.asin(Math.sqrt(Math.min(1, h)));
  };

  function filtersFrom(p) {
    const f = { q: (p.get("q") || "").toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g, "").split(/\s+/).filter(Boolean),
                year_min: num(p.get("year_min")), year_max: num(p.get("year_max")), story: p.get("story") || "", facets: {} };
    ["has_image", "curated", "buildings_only", "oldest_only", "edited", "landmarks_only", "early_only"]
      .forEach((k) => { f[k] = p.get(k) === "1"; });
    META.facets.forEach((k) => { const v = p.getAll(k); if (v.length) f.facets[k] = new Set(v); });
    if (p.get("bbox")) f.bbox = p.get("bbox").split(",").map(Number);
    if (p.get("lat") && p.get("lon")) f.near = [+p.get("lat"), +p.get("lon"), num(p.get("radius"))];
    if (p.get("ids")) f.ids = new Set(p.get("ids").split(","));
    return f;
  }

  function matches(r, f, skipFacet) {
    if (f.q.length && !f.q.every((w) => r._text.includes(w))) return false;
    for (const [k, set] of Object.entries(f.facets)) if (k !== skipFacet && !set.has(r[k] ?? "Unknown")) return false;
    if (f.year_min !== null && !(r.year_start >= f.year_min)) return false;
    if (f.year_max !== null && !(r.year_start <= f.year_max && r.year_start !== null)) return false;
    if (f.has_image && r.t == null) return false;
    if (f.story && !(r.sk && (f.story === "any" ? r.sk.length : r.sk.includes(f.story)))) return false;
    if (f.curated && !r.curated) return false;
    if (f.buildings_only && !r.is_building) return false;
    if (f.oldest_only && !r.oldest_of_type) return false;
    if (f.landmarks_only && !r.landmark) return false;
    if (f.early_only && !(r.year_start != null && r.year_start < 1500)) return false;
    if (f.edited) return false;
    if (f.bbox && !(r.lat >= f.bbox[0] && r.lat <= f.bbox[2] && r.lon >= f.bbox[1] && r.lon <= f.bbox[3])) return false;
    if (f.near && f.near[2] && !(dist(r.lat, r.lon, f.near[0], f.near[1]) <= f.near[2])) return false;
    if (f.ids && !f.ids.has(r.id)) return false;
    return true;
  }

  const cmpNull = (a, b, dir = 1) => (a == null) - (b == null) || (a == null ? 0 : (a < b ? -dir : a > b ? dir : 0));
  const SORTS = {
    oldest: (a, b) => cmpNull(a.year_start, b.year_start) || a.name.localeCompare(b.name),
    newest: (a, b) => cmpNull(a.year_start, b.year_start, -1) || a.name.localeCompare(b.name),
    name: (a, b) => a.name.localeCompare(b.name, undefined, { sensitivity: "base" }),
    nation: (a, b) => cmpNull(a.nation, b.nation) || cmpNull(a.year_start, b.year_start),
    distance: (a, b) => cmpNull(a.dist, b.dist),
  };
  const countBy = (rows, k) => {
    const m = {};
    rows.forEach((r) => { const v = r[k] ?? "Unknown"; m[v] = (m[v] || 0) + 1; });
    return Object.entries(m).sort((a, b) => b[1] - a[1]);
  };
  const ordered = (pairs, order) => pairs.sort((a, b) => (order.indexOf(a[0]) + 1 || 99) - (order.indexOf(b[0]) + 1 || 99));
  const pick = (r, keys) => Object.fromEntries(keys.map((k) => [k, r[k] ?? null]));
  const LIST = ["id", "name", "category", "category_group", "period", "year_start", "date_text", "date_confidence",
    "oldest_of_type", "landmark", "nation", "county", "locality", "heritage_grade", "status", "image_thumb", "lat", "lon", "curated"];

  // Searching: exact name, name with the whole phrase, name with every word, then the rest (as bidb.db.name_rank);
  // the chosen order applies within each tier
  window.nameRank = (words, sort) => {
    const w = (words || []).filter((x) => x.length > 1), phrase = w.join(" ");
    if (!w.length || sort === "name" || sort === "distance") return null;
    const fold = (s) => String(s || "").toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g, "");
    return (r) => { const n = r._name ?? (r._name = fold(r.name));
      return n === phrase ? 0 : n.includes(phrase) ? 1 : w.every((x) => n.includes(x)) ? 2 : 3; };
  };
  const ranked = (cmp, rank) => (rank ? (a, b) => rank(a) - rank(b) || cmp(a, b) : cmp);

  const routes = {
    search(p, f) {
      let rows = DATA.filter((r) => matches(r, f));
      rows.forEach((r) => { r.dist = f.near ? dist(r.lat, r.lon, f.near[0], f.near[1]) : null; });
      let sort = p.get("sort") || "oldest";
      if (sort === "distance" && !f.near) sort = "oldest";
      rows.sort(ranked(SORTS[sort] || SORTS.oldest, window.nameRank(f.q, sort)));
      const off = num(p.get("offset")) || 0, lim = Math.min(num(p.get("limit")) || 48, 500);
      return withThumbs(rows.slice(off, off + lim).map((r) => ({ ...pick(r, LIST), dist: r.dist })))
        .then((page) => ({ total: rows.length, rows: page }));
    },
    facets(p, f) {
      const out = {};
      META.facets.forEach((k) => { out[k] = countBy(DATA.filter((r) => matches(r, f, k)), k); });
      ordered(out.period, META.periods.concat(["Unknown"]));
      ordered(out.category, META.categories); ordered(out.category_group, META.groups);
      return out;
    },
    map: (p, f) => DATA.filter((r) => r.lat != null && matches(r, { ...f, bbox: null }))
      .map((r) => pick(r, ["id", "name", "lat", "lon", "category", "category_group", "period", "date_text", "year_start"])),
    building: (p, f, id) => full(BYID.get(id)),
    buildings: (p) => Promise.all((p.get("ids") || "").split(",").map((id) => full(BYID.get(id)))).then((l) => l.filter(Boolean)),
    nearby(p, f, id) {
      const b = DATA.find((r) => r.id === id);
      if (!b || b.lat == null) return [];
      const near = DATA.filter((r) => r.id !== id && r.lat != null && Math.abs(r.lat - b.lat) < 0.3 && Math.abs(r.lon - b.lon) < 0.5)
        .map((r) => ({ ...pick(r, ["id", "name", "category", "date_text"]), dist: dist(r.lat, r.lon, b.lat, b.lon) }))
        .filter((r) => r.dist <= 15).sort((a, c) => a.dist - c.dist).slice(0, 10);
      return withThumbs(near);
    },
    timeline(p, f) {
      const size = num(p.get("bucket")) || 100, buckets = {}, present = new Set();
      DATA.filter((r) => r.year_start != null && matches(r, { ...f, year_min: null, year_max: null })).forEach((r) => {
        const b = Math.floor(r.year_start / size) * size, g = r.category_group || "Other";
        (buckets[b] = buckets[b] || {})[g] = (buckets[b][g] || 0) + 1; present.add(g);
      });
      return { bucket: size, groups: META.groups.filter((g) => present.has(g)),
               rows: Object.keys(buckets).map(Number).sort((a, b) => a - b).map((b) => ({ start: b, counts: buckets[b] })) };
    },
    stats(p, f) {
      const rows = DATA.filter((r) => matches(r, f));
      const c = (fn) => rows.filter(fn).length;
      const oc = {};
      rows.filter((r) => r.year_start != null && r.county).forEach((r) => {
        const k = r.county + "|" + r.nation;
        if (!oc[k] || r.year_start < oc[k].year) oc[k] = { county: r.county, nation: r.nation, id: r.id, name: r.name, date_text: r.date_text, year: r.year_start };
      });
      return { total: rows.length, nation: countBy(rows, "nation"), category: ordered(countBy(rows, "category"), META.categories),
        period: countBy(rows, "period"), heritage_grade: countBy(rows, "heritage_grade"), status: countBy(rows, "status"),
        county: countBy(rows, "county").slice(0, 25),
        completeness: [["image", c((r) => r.t != null)], ["coordinates", c((r) => r.lat != null)],
          ["recorded date", c((r) => r.date_confidence === "Recorded")], ["any date", c((r) => r.year_start != null)],
          ["heritage designation", c((r) => r.designations)], ["Wikipedia article", c((r) => r.wikipedia_title)]],
        oldest_by_county: Object.values(oc).sort((a, b) => cmpNull(a.nation, b.nation) || a.county.localeCompare(b.county)) };
    },
    gaps() {
      const checks = { no_image: (r) => r.t == null, no_coordinates: (r) => r.lat == null, no_date: (r) => r.year_start == null,
        estimated_date: (r) => r.date_confidence === "Estimate (building type)", no_nation: (r) => !r.nation,
        no_designation: (r) => !r.designations, date_conflict: (r) => r.date_check === "Conflict" };
      return Object.fromEntries(Object.entries(checks).map(([k, fn]) => {
        const rows = DATA.filter(fn).sort(SORTS.oldest);
        return [k, { count: rows.length, rows: rows.slice(0, 200).map((r) => pick(r, ["id", "name", "nation", "county", "date_text", "wikidata_id", "date_check_note"])) }];
      }));
    },
    async oldest(p) {
      const per = num(p.get("per")) || 6;
      const out = META.categories.map((cat) => {
        const all = DATA.filter((r) => r.category === cat);
        const ex = all.filter((r) => r.year_start != null).sort(SORTS.oldest).slice(0, per).map((r) => ({ ...r }));
        return { category: cat, group: META.group_of[cat] || "Other", count: all.length, examples: ex };
      }).filter((c) => c.examples.length);
      await withThumbs(out.flatMap((c) => c.examples));
      return out;
    },
    history: () => HISTORY,
    verification: async () => fetch("data/verification.json").then((r) => r.json()).catch(() => ({})),
    evidence: async () => fetch("data/evidence.json").then((r) => r.json()).catch(() => ({})),
    build_info: () => ({ build_info: META.build_info }),
    geocode(p) {                 // hosted: match places named in the catalogue itself
      const q = (p.get("q") || "").trim().toLowerCase();
      if (!q) return [];
      const hit = (field) => DATA.filter((r) => r.lat != null && (r[field] || "").toLowerCase().split(/,\s*/).includes(q));
      const rows = hit("locality").concat(hit("county"), hit("located_in"));
      if (!rows.length) return [];
      const lat = rows.reduce((a, r) => a + r.lat, 0) / rows.length, lon = rows.reduce((a, r) => a + r.lon, 0) / rows.length;
      return [{ name: p.get("q"), lat, lon }];
    },
    images: () => [],
    quiz(p) {                    // random photographed buildings with a well-supported date
      const pool = DATA.filter((r) => r.t != null && r.year_start != null && r.period !== "Unknown"
        && ["Corroborated", "Referenced", "Reviewed"].includes(r.date_check));
      const out = [];
      for (let i = 0; i < Math.min(num(p.get("n")) || 10, 30) && pool.length; i++)
        out.push(pick(pool.splice(Math.floor(Math.random() * pool.length), 1)[0],
          ["id", "name", "year_start", "date_text", "period", "category", "locality", "nation"]));
      return withThumbs(out);
    },
    async tours(p) {
      let rows = await tours();
      ["mode", "theme", "nation"].forEach((k) => { if (p.get(k)) rows = rows.filter((t) => t[k] === p.get(k)); });
      (p.get("q") || "").toLowerCase().split(/\s+/).filter(Boolean).forEach((w) => {
        rows = rows.filter((t) => `${t.title} ${t.summary} ${t.area}`.toLowerCase().includes(w)); });
      return rows.map(({ geometry, ...t }) => t);
    },
    async tour(p, f, id) { return (await tours()).find((t) => t.id === id); },
    async oldest_lists() { return fetch("data/oldest_lists.json").then((r) => r.json()); },
    async dendro(p, f, id) {
      TREE = TREE || fetch("data/dendro.json").then((r) => r.json()).catch(() => ({}));
      return ((await TREE)[id] || []).map(([location, date_text, method, reference]) => ({ record_id: id, location, date_text, method, reference }));
    },
    async excavations(p, f, id) {
      DIGS = DIGS || fetch("data/excavations.json").then((r) => r.json()).catch(() => ({}));
      return ((await DIGS)[id] || []).map(([what, years, who]) => ({ entity_id: id, what, years, who }));
    },
    async domesday(p, f, id) {
      DOMESDAY = DOMESDAY || fetch("data/domesday.json").then((r) => r.json()).catch(() => ({ s: {}, r: {} }));
      const d = await DOMESDAY, m = d.r[id];
      if (!m) return null;
      const sid = m.replace(/^=/, ""), [settlement, od, churches, priests, households, phillimore] = d.s[sid] || [];
      const entry = churches === undefined ? null : { od_id: od, churches, priests, households, phillimore };
      return { entity_id: id, settlement_id: sid, settlement, od_id: od, itself: m.startsWith("=") ? 1 : 0, entry };
    },
    async visiting(p, f, id) {
      VISITS = VISITS || fetch("data/visiting.json").then((r) => r.json()).catch(() => ({}));
      const v = (await VISITS)[id];
      return v ? { entity_id: id, ...v } : null;
    },
    tour_candidates(p) {
      const lat = +p.get("lat"), lon = +p.get("lon"), radius = Math.min(+p.get("km") || 10, 80);
      const test = THEME_TEST[p.get("theme")] || THEME_TEST.highlights;
      const near = DATA.filter((r) => r.lat != null && Math.abs(r.lat - lat) < radius / 100 && test(r)
        && dist(r.lat, r.lon, lat, lon) <= radius)
        .map((r) => ({ ...pick(r, ["id", "name", "lat", "lon", "date_text", "category", "locality"]), kind: "building",
                       story_kinds: r.sk || [], score: interest(r) }));
      return near.sort((a, b) => b.score - a.score).slice(0, 300);
    },
    // every column of every matching record, for the Export menu (ui_export.js)
    async export_rows(p, f) {
      const sort = p.get("sort") && p.get("sort") !== "distance" ? p.get("sort") : "oldest";
      const rows = DATA.filter((r) => matches(r, f)).sort(SORTS[sort] || SORTS.oldest);
      await Promise.all([...new Set(rows.filter((r) => r.d != null).map((r) => r.d))].map((i) => shard(META.detail_shards[i])));
      return Promise.all(rows.map(async ({ _text, dist, t, d, ...r }) =>
        ({ ...r, ...(d != null ? (await shard(META.detail_shards[d]))[r.id] || {} : {}) })));
    },
    async footprints(p) {
      const [s, w, n, e] = (p.get("bbox") || "").split(",").map(Number);
      return (await outlines()).filter((r) => r.lat >= s && r.lat <= n && r.lon >= w && r.lon <= e).slice(0, 800)
        .map((r) => pick(r, ["id", "name", "category_group", "footprint"]));
    },
  };

  window.STATIC_API = async function (url) {
    await load();
    const u = new URL(url, location.href), parts = u.pathname.replace(/^.*\/api\//, "").split("/");
    if (window.STATIC_PLACES) {
      const res = await window.STATIC_PLACES(parts, u.searchParams, { meta: META, buildings: BYID });
      if (res !== undefined) return res;
    }
    const name = parts[0], id = parts.length > 1 ? decodeURIComponent(parts.slice(1).join("/")) : null;
    const fn = routes[name];
    if (!fn) throw new Error("No static route for " + url);
    const plain = ["history", "gaps", "tours", "tour", "tour_candidates", "visiting", "domesday", "dendro", "excavations", "oldest_lists", "quiz"].includes(name);
    return fn(u.searchParams, plain ? null : filtersFrom(u.searchParams), id);
  };
})();
