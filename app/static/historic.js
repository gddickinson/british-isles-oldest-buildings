// Historic map overlays (see app/historic_layers.py): one at a time, with opacity, chosen in the
// map's layer switcher. Online tiles locally; bundled low-zoom WebP tiles in the hosted copy.
const Historic = (() => {
  const CONF_URL = (IS_STATIC ? "static" : "/static") + "/data/historic/layers.json";
  const STORE = "bi_map_historic";
  const BLANK = "data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7";
  const packs = {};
  let conf = null;
  const getConf = () => (conf = conf || fetch(CONF_URL).then((r) => r.json()).catch(() => ({ layers: [], towns: [] })));
  const read = () => { try { return JSON.parse(localStorage.getItem(STORE)) || { key: "", opacity: 0.75 }; } catch (e) { return { key: "", opacity: 0.75 }; } };
  const save = (v) => { try { localStorage.setItem(STORE, JSON.stringify(v)); } catch (e) { /* blocked */ } };
  const bounds = (b) => L.latLngBounds([b[1], b[0]], [b[3], b[2]]);

  function makeLayer(l, opacity) {
    const opts = { pane: "historic", opacity, bounds: bounds(l.bounds), attribution: l.attr, minZoom: 1,
                   maxZoom: 19, maxNativeZoom: l.max, minNativeZoom: l.min || 1, errorTileUrl: "" };
    if (IS_STATIC) {                     // tiles packed per layer as {"z/x/y": base64 WebP}
      const [z0, z1] = l.bundle;
      const g = L.layerGroup();
      packs[l.key] = packs[l.key] || fetch(`static/data/historic/packs/${l.key}.json`).then((r) => r.json());
      packs[l.key].then((pack) => {
        const Packed = L.TileLayer.extend({ getTileUrl: (c) => (pack[`${c.z}/${c.x}/${c.y}`]
          ? "data:image/webp;base64," + pack[`${c.z}/${c.x}/${c.y}`] : BLANK) });
        g.addLayer(new Packed("", { ...opts, minNativeZoom: z0, maxNativeZoom: z1 }));
      });
      return g;
    }
    if (l.parts) {                       // one tileset per county, each only within its own bounds
      return L.layerGroup(l.parts.map((p) => L.tileLayer(p.url, { ...opts, bounds: bounds(p.bounds) })));
    }
    return L.layerGroup(l.urls.map((u) => L.tileLayer(u, opts)));
  }

  // Bundled low-zoom tiles served by the local app (/historic_tiles), for when a map's server is down
  function bundledLayer(l, opacity) {
    const [z0, z1] = l.bundle;
    return L.tileLayer(`/historic_tiles/${l.key}/{z}/{x}/{y}.webp`, { pane: "historic", opacity, bounds: bounds(l.bounds),
      minZoom: 1, maxZoom: 19, minNativeZoom: z0, maxNativeZoom: z1, errorTileUrl: "", attribution: l.attr });
  }

  // Calls back once if none of the layer's tiles has loaded within `ms` although some were asked for
  function watchServer(layer, ms, onDead) {
    let loaded = 0, asked = 0;
    const each = (f) => (layer.eachLayer ? layer.eachLayer(f) : f(layer));
    each((t) => { t.on("tileloadstart", () => asked++); t.on("tileload", () => loaded++); });
    const timer = setTimeout(() => { if (!loaded && asked) onDead(); }, ms);
    layer.on("remove", () => clearTimeout(timer));
  }

  function townsLayer(towns, opacity) {
    return L.layerGroup(towns.map((t) => L.tileLayer(t.url, { pane: "historic", opacity, bounds: bounds(t.bounds),
      minZoom: Math.max(12, t.min), maxNativeZoom: t.max, maxZoom: 21, errorTileUrl: "",
      attribution: 'Town plans: <a href="https://maps.nls.uk/">National Library of Scotland</a> (CC-BY)' })));
  }

  // Adds the "Historic map" block to a layer-switcher panel
  async function bind(panel, map) {
    if (!map.getPane("historic")) map.createPane("historic").style.zIndex = 350;
    const c = await getConf();
    const layers = c.layers.filter((l) => !IS_STATIC || l.bundle);
    if (!layers.length) return;
    const st = read();
    const fromUrl = new URLSearchParams(location.search).get("historic");
    if (fromUrl) st.key = fromUrl;
    const block = document.createElement("div");
    block.className = "ml-historic";
    block.innerHTML = `<b>Historic map</b>
      <select class="ml-hsel"><option value="">None</option>
        ${layers.map((l) => `<option value="${esc(l.key)}">${esc(l.label)} (${esc(l.date)})</option>`).join("")}
        ${!IS_STATIC && c.towns.length ? `<option value="__towns">Town plans 1840s–90s (${c.towns.length} towns; zoom in)</option>` : ""}
      </select>
      <label class="ml-op">Opacity <input type="range" min="0.2" max="1" step="0.05" value="${st.opacity}"></label>
      <small class="ml-hnote"></small>`;
    panel.insertBefore(block, panel.querySelector("small:last-child"));
    const sel = block.querySelector("select"), op = block.querySelector("input"), note = block.querySelector(".ml-hnote");
    let current = null;
    const apply = () => {
      if (current) map.removeLayer(current);
      current = null;
      const key = sel.value, opacity = 1;              // tiles opaque; the pane carries the chosen opacity,
      map.getPane("historic").style.opacity = op.value; // so overlapping plans cover each other instead of stacking
      save({ key, opacity: parseFloat(op.value) });
      note.textContent = "";
      if (!key) return;
      if (key === "__towns") {
        current = townsLayer(c.towns, opacity);
        note.textContent = "Shown from zoom 12 where a plan exists.";
      } else {
        const l = layers.find((x) => x.key === key);
        current = makeLayer(l, opacity);
        if (IS_STATIC) note.textContent = `Bundled up to zoom ${l.bundle[1]}; blurrier when zoomed in further.`;
        else {
          const host = new URL((l.parts || []).map((x) => x.url).concat(l.urls || [])[0]).hostname, mine = current;
          watchServer(current, 8000, () => {
            if (current !== mine) return;
            if (l.bundle) {                    // live server silent: use the bundled copy instead
              map.removeLayer(current);
              current = bundledLayer(l, 1);
              map.addLayer(current);
              note.textContent = `${host} is not responding; showing the bundled copy (sharp up to zoom ${l.bundle[1]}).`;
            } else note.textContent = `${host} is not responding at the moment; try again later.`;
          });
        }
        if (!map.getBounds().intersects(bounds(l.bounds))) map.fitBounds(bounds(l.bounds));
      }
      map.addLayer(current);
    };
    sel.value = layers.some((l) => l.key === st.key) || st.key === "__towns" ? st.key : "";
    sel.addEventListener("change", apply);
    op.addEventListener("input", () => {
      save({ key: sel.value, opacity: parseFloat(op.value) });
      map.getPane("historic").style.opacity = op.value;
    });
    if (sel.value) apply();
  }

  // Georeferenced maps on Allmaps whose outline contains a point, most detailed (smallest) first
  let allmaps = null;
  const inside = (pt, ring) => {
    let hit = false;
    for (let i = 0, j = ring.length - 1; i < ring.length; j = i++) {
      const [xi, yi] = ring[i], [xj, yj] = ring[j];
      if ((yi > pt[1]) !== (yj > pt[1]) && pt[0] < ((xj - xi) * (pt[1] - yi)) / (yj - yi) + xi) hit = !hit;
    }
    return hit;
  };
  function mapsAt(lat, lon, limit = 8) {
    allmaps = allmaps || fetch(CONF_URL.replace("layers.json", "allmaps.json")).then((r) => r.json()).catch(() => []);
    return allmaps.then((rows) => {
      const found = rows.filter((m) => inside([lon, lat], m.g));
      return { total: found.length, maps: found.slice(0, limit) };
    });
  }

  return { bind, mapsAt };
})();
