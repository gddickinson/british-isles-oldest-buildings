// Hosted (static) version of the /types routes (BT4b): type_tree, materials, material_centuries, type_page/<id>,
// material/<id>, types_here/<id>, from the compact files of app/static_types.py. Catalogue records come as ids and are
// filled in from the catalogue rows; places come as [id, name, year, date text, county, nation]; places on the maps as
// integer steps of 1/1000 degree (no pop-up of their own: they link to the Map page at that point).
(function () {
  let TREE = null, INDEX = null;
  const json = (name) => fetch("data/" + name).then((r) => r.json());
  const tree = () => (TREE = TREE || json("types_tree.json"));
  const index = () => (INDEX = INDEX || json("types_index.json"));
  const files = {};
  const file = (name) => (files[name] = files[name] || json(name).catch(() => ({})));

  // a record or place as the page shows it
  function entity(ref, rows) {
    if (Array.isArray(ref)) {
      const [id, name, year, date_text, county, nation] = ref;
      return { id, source: "place", name, year, date_text, county, nation };
    }
    const r = rows.get(ref) || {};
    return { id: ref, source: "building", name: r.name || ref, year: r.year_start ?? null, date_text: r.date_text,
             county: r.county, nation: r.nation, status: r.status, lat: r.lat, lon: r.lon };
  }
  function steps(flat) {
    const out = [];
    let lat = 0, lon = 0;
    for (let i = 0; i + 1 < flat.length; i += 2) { lat += flat[i]; lon += flat[i + 1]; out.push([lat / 1000, lon / 1000]); }
    return out;
  }
  // map points [lat, lon, id, source, year, primary]: records from their rows, places without an id
  function points(pts, rows) {
    const out = [];
    [["b", 1], ["b2", 0]].forEach(([k, primary]) => (pts[k] || []).forEach((id) => {
      const r = rows.get(id);
      if (r && r.lat != null) out.push([r.lat, r.lon, id, "building", r.year_start ?? null, primary]);
    }));
    [["p", 1], ["p2", 0]].forEach(([k, primary]) => steps(pts[k] || []).forEach(([lat, lon]) =>
      out.push([lat, lon, null, "place", null, primary])));
    return out;
  }
  function links(idx, all, names, own) {
    return idx.map((i) => all[i]).map((k) => {
      const other = k.from === own ? k.to : k.from;
      return { ...k, other, other_name: names.get(other) || other, direction: k.from === own ? "out" : "in" };
    });
  }
  async function page(key) {
    const ix = await index(), n = ix.pages[key];
    if (n === undefined) return null;
    return (await file(`types_pages_${n}.json`))[key] || null;
  }

  const routes = {
    async type_tree() {
      const t = await tree();
      const links = t.type_links.map((k) => Object.fromEntries(
        ["id", "from", "to", "kind", "confidence", "claim", "region"].map((f) => [f, k[f] ?? null])));
      return { ...t.tree, links };
    },
    async materials() { return (await tree()).materials; },
    async material_centuries() { return (await tree()).centuries; },
    async type_page(id, rows) {
      const [d, t] = [await page("t:" + id), await tree()];
      if (!d) throw new Error("No such type");
      const names = new Map(t.tree.types.map((x) => [x.id, x.name]));
      return { ...d, links: links(d.links, t.type_links, names, id),
        examples: d.ex.map(([ref, early]) => ({ ...entity(ref, rows), too_early: !!early })),
        spread: d.sp.map(([county, nation, year, ref]) => ({ ...entity(ref, rows), county, nation, year })),
        points: points(d.pts || {}, rows) };
    },
    async material(id, rows) {
      const [d, t] = [await page("m:" + id), await tree()];
      if (!d) throw new Error("No such material");
      const names = new Map(t.materials.materials.map((x) => [x.id, x.name]));
      return { ...d, links: links(d.links, t.mat_links, names, id),
        examples: d.ex.map(([ref, early, evidence]) => ({ ...entity(ref, rows), too_early: !!early, evidence })),
        points: points(d.pts || {}, rows).map((q) => q.slice(0, 5)) };
    },
    async types_here(id) {
      const ix = await index();
      const h = (await file(`types_here_${window.STATIC_ID_HASH(id) % ix.here_shards}.json`))[id];
      if (!h) return { types: [], materials: [] };
      const VIA = ["wikidata", "wikipedia", "register"];
      return {
        types: h[0].map((i) => { const [tid, name, family] = ix.types[i < 0 ? -1 - i : i]; return { id: tid, name, family, primary: i >= 0 }; }),
        materials: h[1].map((v) => { const [mid, name, group] = ix.mats[Math.floor(v / 3)]; return { id: mid, name, group, via: VIA[v % 3] }; }),
      };
    },
  };

  // called by static_api.js: undefined when the path is not a /types route
  window.STATIC_TYPES = async function (parts, ctx) {
    const fn = routes[parts[0]];
    if (!fn) return undefined;
    return fn(parts.length > 1 ? decodeURIComponent(parts.slice(1).join("/")) : null, ctx.buildings);
  };
})();
