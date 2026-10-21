// Offline map: bundled vector layers (counties, roads, minor roads by tile, rail, trails, rivers, parks, towns, landscape
// names, airports) drawn by Leaflet, with a layer switcher. Used when hosted (tile servers are blocked),
// as a fallback when the online street map cannot load, and on request as a simpler map.
const Basemap = (() => {
  const ROOT = IS_STATIC ? "static/data/basemap/" : "/static/data/basemap/";
  const LAYERS = [
    { key: "counties", label: "Counties & council areas", on: true, online: true },
    { key: "historic_counties", label: "Historic counties (before 1974)", on: false, online: true },
    { key: "parks", label: "National parks & AONBs", on: true, online: true },
    { key: "rivers", label: "Rivers & lakes", on: true },
    { key: "roads", label: "Major roads", on: true },
    { key: "minor", label: "Minor roads (zoom in)", on: false },
    { key: "streams", label: "Streams (zoom in)", on: false },
    { key: "lakes", label: "Lakes, lochs & reservoirs (zoom in)", on: true },
    { key: "walking", label: "Regional & local walking routes (zoom in)", on: false, online: true },
    { key: "cycling", label: "National Cycle Network & regional cycle routes", on: false, online: true },
    { key: "roman", label: "Roman roads", on: false, online: true },
    { key: "buried", label: "Buried rivers & streams (culverted; zoom in)", on: false, online: true },
    { key: "rail", label: "Railways", on: false },
    { key: "underground", label: "Underground railways & tunnels", on: false, online: true },
    { key: "trails", label: "National trails & long-distance paths", on: false, online: true },
    { key: "towns", label: "Cities, towns & villages", on: true },
    { key: "landscape", label: "Hills, forests, islands & coast", on: false },
    { key: "airports", label: "Airports", on: false },
    { key: "stations", label: "Railway & bus stations (zoom in)", on: false, online: true },
    { key: "defences", label: "Pillboxes, bunkers & trenches (zoom in)", on: false, online: true },
  ].concat(IS_STATIC ? [] : [{ key: "streets", label: "Street detail (areas saved for offline)", on: true }]);
  const STORE = "bi_map_layers", BASE_STORE = "bi_map_base";
  const cache = {};
  const load = (name) => (cache[name] = cache[name] || fetch(ROOT + name + ".json").then((r) => r.json()));
  const css = (n) => getComputedStyle(document.documentElement).getPropertyValue(n).trim();
  const read = (k, d) => { try { return JSON.parse(localStorage.getItem(k)) ?? d; } catch (e) { return d; } };
  const save = (k, v) => { try { localStorage.setItem(k, JSON.stringify(v)); } catch (e) { /* blocked */ } };

  function chosen() {
    const saved = read(STORE, null);
    return new Set(saved || LAYERS.filter((l) => l.on).map((l) => l.key));
  }

  // ---- vector layers ---------------------------------------------------------------
  function landLayer(map, r) {
    const g = L.layerGroup();
    load("land").then((gj) => {
      L.geoJSON(gj, { renderer: r, interactive: false, style: (f) => ({
        stroke: false, fillOpacity: 1, fillColor: f.properties.x ? css("--map-land-other") : css("--map-land") }) }).addTo(g);
    });
    return g;
  }

  // Areas with outlines and labels at county zooms: today's counties (land.json) or pre-1974 ones
  const areaLayer = (file, pick, style, tip, cls) => (map, r) => {
    const g = L.layerGroup(), labels = L.layerGroup().addTo(g);
    load(file).then((gj) => {
      const own = { ...gj, features: gj.features.filter(pick) };
      L.geoJSON(own, { renderer: r, style, onEachFeature: (f, l) => l.bindTooltip(tip(f), { sticky: true }) }).addTo(g);
      const draw = () => {
        labels.clearLayers();
        const z = map.getZoom();
        if (z < 7 || z > 10) return;
        const b = map.getBounds().pad(0.1);
        own.features.forEach((f) => {
          const [x, y] = f.properties.l;
          if (b.contains([y, x])) labels.addLayer(L.marker([y, x], { interactive: false,
            icon: L.divIcon({ className: "map-label " + cls, html: esc(f.properties.n), iconSize: null }) }));
        });
      };
      map.on("zoomend moveend", draw); draw();
      g.on("remove", () => map.off("zoomend moveend", draw));
    });
    return g;
  };
  const countiesLayer = areaLayer("land", (f) => !f.properties.x,
    () => ({ color: css("--map-border"), weight: 0.8, fill: true, fillOpacity: 0, dashArray: "3 3" }),
    (f) => `${esc(f.properties.n)}<br><small>${esc(f.properties.t || "")}</small>`, "county");
  const historicCountiesLayer = areaLayer("historic_counties", () => true,
    () => ({ color: css("--map-historic-county"), weight: 1.4, fill: true, fillOpacity: 0, dashArray: "8 4" }),
    (f) => `${esc(f.properties.n)}<br><small>historic county (before 1974)</small>`, "county historic");

  function lineLayer(name, style, tip) {
    return (map, r) => {
      const g = L.layerGroup();
      load(name).then((gj) => L.geoJSON(gj, { renderer: r, style, filter: (f) => !f.properties.lake || name === "rivers",
        onEachFeature: tip ? (f, l) => { const t = tip(f); if (t) l.bindTooltip(t, { sticky: true }); } : undefined }).addTo(g));
      return g;
    };
  }

  const roadsLayer = lineLayer("roads", (f) => ({ color: f.properties.k === "ferry" ? css("--map-water-line") : css(
      f.properties.k === "motorway" ? "--map-motorway" : f.properties.k === "major" ? "--map-road-major" : "--map-road"),
    weight: { motorway: 2.6, major: 2, secondary: 1.4, road: 1, ferry: 1 }[f.properties.k] || 1,
    dashArray: f.properties.k === "ferry" ? "4 4" : null, opacity: 0.95 }),
  (f) => f.properties.n ? esc(f.properties.n) : "");

  // Minor roads and streams: 1-degree tiles (basemap/<dir>/<lat>_<lon>.json, app/basemap_tiled.py),
  // loaded for the view once zoomed in to minZoom.
  // Each tile is {"r": [[kind, label, [x0, y0, dx, dy, …] in 1/10000 degree], …]}.
  const tiledLayer = (dir, minZoom, style) => (map, r) => {
    const g = L.layerGroup(), tiles = {}, MINOR_ZOOM = minZoom;
    const draw = (data) => {
      const t = L.layerGroup();
      data.r.forEach(([k, label, c]) => {
        let x = c[0], y = c[1];
        const pts = [[y / 1e4, x / 1e4]];
        for (let i = 2; i < c.length; i += 2) { x += c[i]; y += c[i + 1]; pts.push([y / 1e4, x / 1e4]); }
        const line = (k === "l" ? L.polygon : L.polyline)(pts, { renderer: r, ...style(k) });
        if (label) line.bindTooltip(esc(label), { sticky: true });
        t.addLayer(line);
      });
      return t;
    };
    const update = () => {
      const z = map.getZoom(), b = map.getBounds();
      // hosted copy: tiles come in packs (static_export._pack_map_tiles): pack_index = {tile: pack number}
      (IS_STATIC ? load(dir + "/pack_index") : load(dir + "/index")).then((index) => {
        const want = new Set();
        if (z >= MINOR_ZOOM) {
          for (let la = Math.floor(b.getSouth()) - 1; la <= Math.floor(b.getNorth()); la++)
            for (let lo = Math.floor(b.getWest()) - 1; lo <= Math.floor(b.getEast()); lo++)
              if (index[`${la}_${lo}`] !== undefined) want.add(`${la}_${lo}`);
        }
        Object.keys(tiles).forEach((k) => { if (!want.has(k) && tiles[k].layer) g.removeLayer(tiles[k].layer); });
        want.forEach((k) => {
          if (!tiles[k]) tiles[k] = {};
          const tile = tiles[k];
          if (tile.layer) { g.addLayer(tile.layer); return; }
          if (tile.loading) return;
          const get = IS_STATIC ? load(`${dir}/pack_${index[k]}`).then((p) => p[k]) : load(dir + "/" + k);
          tile.loading = get.then((data) => {
            tile.layer = draw(data);
            if (map.hasLayer(g)) update();          // adds it if the view still wants this tile
          });
        });
      });
    };
    g.on("add", () => { map.on("moveend", update); update(); });
    g.on("remove", () => map.off("moveend", update));
    return g;
  };
  const minorLayer = tiledLayer("minor", 9, (k) => ({ color: css(k === "s" ? "--map-road-major" : "--map-road-minor"),
    weight: k === "s" ? 1.6 : 1.1, opacity: k === "s" ? 0.85 : 0.95 }));
  const streamsLayer = tiledLayer("streams", 11, () => ({ color: css("--map-water-line"), weight: 0.8, opacity: 0.8 }));
  const walkingLayer = tiledLayer("walking", 10, () => ({ color: css("--map-trail"), weight: 1.6, dashArray: "4 3", opacity: 0.9 }));
  const cyclingLayer = tiledLayer("cycling", 9, (k) => ({ color: k === "n" ? "#d6332e" : "#7b3fb5", weight: k === "n" ? 2.2 : 1.6,
    opacity: 0.85 }));
  const romanLayer = tiledLayer("roman", 7, () => ({ color: "#8b1d1d", weight: 2, dashArray: "8 3 2 3", opacity: 0.85 }));
  const buriedLayer = tiledLayer("buried", 11, () => ({ color: css("--map-water-line"), weight: 2, dashArray: "1 4", opacity: 0.9 }));
  const lakesLayer = tiledLayer("lakes", 9, () => ({ color: css("--map-water-line"), weight: 0.6, fillColor: css("--map-water"),
    fillOpacity: 1, opacity: 0.9 }));

  // tube lines (red; lighter where they run above ground) and railway, disused, canal and road tunnels
  const UG = { s: ["#dc241f", 2.2, null], r: ["#4a4a4a", 2, "4 3"], d: ["#8a5a2b", 2, "1 3"], c: ["#2b7bb9", 2, "4 3"],
               h: ["#7d7d7d", 2, "6 3"] };
  const UG_NAME = { s: "Underground railway", r: "Railway tunnel", d: "Disused railway tunnel", c: "Canal tunnel", h: "Road tunnel" };
  const undergroundLayer = lineLayer("underground", (f) => {
    const [color, weight, dashArray] = UG[f.properties.k] || UG.r;
    return { color, weight, dashArray, opacity: f.properties.k === "s" && !f.properties.u ? 0.45 : 0.9 };
  }, (f) => `${f.properties.n ? esc(f.properties.n) + "<br>" : ""}<small>${UG_NAME[f.properties.k] || ""}${
    f.properties.k === "s" && !f.properties.u ? " (above ground)" : ""}</small>`);

  const railLayer = lineLayer("rail", () => ({ color: css("--map-rail"), weight: 1.2, dashArray: "6 3" }));
  const trailsLayer = lineLayer("trails", () => ({ color: css("--map-trail"), weight: 1.6, dashArray: "2 4", opacity: 0.9 }),
    (f) => `${esc(f.properties.n)}${f.properties.o ? `<br><small>${esc(f.properties.o)}</small>` : ""}`);

  const riversLayer = lineLayer("rivers", (f) => f.properties.lake
    ? { stroke: false, fillColor: css("--map-water"), fillOpacity: 1 }
    : f.properties.c ? { color: css("--map-water-line"), weight: 1.1, dashArray: "5 2" }    // canal
    : { color: css("--map-water-line"), weight: { 1: 1.8, 2: 1.2, 3: 0.8 }[f.properties.r] || 1 },
  (f) => f.properties.n ? esc(f.properties.n) : "");

  function parksLayer(map, r) {
    const g = L.layerGroup();
    load("parks").then((gj) => L.geoJSON(gj, { renderer: r, style: (f) => ({
      color: css("--map-park-line"), weight: 1, fillColor: css("--map-park"),
      fillOpacity: f.properties.k === "National Park" ? 0.35 : 0.2 }),
      onEachFeature: (f, l) => l.bindTooltip(`${esc(f.properties.n)}<br><small>${esc(f.properties.k)}</small>`, { sticky: true }) }).addTo(g));
    return g;
  }

  // ---- labels: rebuilt on every move, with simple screen-space collision avoidance -----
  function labelLayer(name, pick, html) {
    return (map) => {
      const g = L.layerGroup();
      load(name).then((rows) => {
        const draw = () => {
          g.clearLayers();
          const z = map.getZoom(), b = map.getBounds().pad(0.05), taken = new Set();
          let n = 0;
          for (const row of rows) {
            if (n > 400) break;
            const cls = pick(row, z);
            if (!cls || !b.contains([row[1], row[2]])) continue;
            // reserve the label's whole width (about 7 px a character) in 24 x 16 px cells
            const p = map.latLngToContainerPoint([row[1], row[2]]), w = 14 + 7 * String(row[0]).length;
            const cells = [];
            for (let y = Math.floor((p.y - 8) / 16); y <= Math.floor((p.y + 8) / 16); y++)
              for (let x = Math.floor((p.x - 6) / 24); x <= Math.floor((p.x + w) / 24); x++) cells.push(`${x}:${y}`);
            if (cells.some((c) => taken.has(c))) continue;
            cells.forEach((c) => taken.add(c));
            n++;
            g.addLayer(L.marker([row[1], row[2]], { interactive: false, keyboard: false,
              icon: L.divIcon({ className: "map-label " + cls, html: html(row), iconSize: null }) }));
          }
        };
        map.on("zoomend moveend", draw); draw();
        g.on("remove", () => map.off("zoomend moveend", draw));
      });
      return g;
    };
  }

  const townsLayer = labelLayer("towns", (t, z) => (t[3] === 0 && z >= 5 ? "city" : t[3] === 1 && z >= 8 ? "town"
    : t[3] === 2 && z >= 11 ? "village" : null), (t) => `<i></i>${esc(t[0])}`);
  const LAND_ZOOM = { region: 5, range: 7, forest: 9, moor: 9, island: 9, bay: 9, lake: 10, glen: 10, headland: 10, hill: 10 };
  const landscapeLayer = labelLayer("landscape", (t, z) => (z >= (LAND_ZOOM[t[3]] || 11) ? "land " + t[3] : null),
    (t) => `${t[3] === "hill" ? "▲ " : ""}${esc(t[0])}${t[3] === "hill" && t[4] ? ` <small>${t[4]} m</small>` : ""}`);
  const airportsLayer = labelLayer("airports", (a, z) => (z >= 6 ? "airport" : null), (a) => `✈ ${esc(a[0])}`);
  const STATION_ICON = { rail: "🚉", heritage: "🚂", metro: "Ⓜ", bus: "🚌" };
  const stationsLayer = labelLayer("stations", (s, z) => (z >= (s[3] === "bus" ? 12 : 10) ? "station" : null),
    (s) => `${STATION_ICON[s[3]] || "🚉"} ${esc(s[0])}`);
  const DEFENCE = { pillbox: "Pillbox", bunker: "Bunker", gun: "Gun emplacement", trench: "Trench" };
  const defencesLayer = labelLayer("defences", (d, z) => (z >= 12 ? "defence" : null),
    (d) => `<span class="defence-dot"></span>${esc(d[0] || DEFENCE[d[3]] || "Bunker")}`);
  // nearest stations to a point (detail views, tours): [{name, kind, km, lat, lon}], one per kind
  async function nearestStations(lat, lon, maxKm = 15) {
    const rows = await load("stations").catch(() => []);
    const rad = Math.PI / 180, best = {};
    for (const [name, la, lo, kind] of rows) {
      if (Math.abs(la - lat) > 0.2) continue;
      const h = Math.sin((la - lat) * rad / 2) ** 2 + Math.cos(lat * rad) * Math.cos(la * rad) * Math.sin((lo - lon) * rad / 2) ** 2;
      const d = 12742 * Math.asin(Math.sqrt(Math.min(1, h)));
      if (d <= maxKm && (!best[kind] || d < best[kind].km)) best[kind] = { name, kind, km: d, lat: la, lon: lo, icon: STATION_ICON[kind] };
    }
    return Object.values(best).sort((a, b) => a.km - b.km);
  }

  // street-level vector tiles saved with "Save this area for offline" (app/street_tiles.py; local GUI)
  function streetsLayer(map) {
    if (!window.protomapsL) return L.layerGroup();
    if (!map.getPane("streets")) map.createPane("streets").style.zIndex = 255;   // above the land fill
    const dark = document.documentElement.dataset.theme === "dark"
      || (!document.documentElement.dataset.theme && matchMedia("(prefers-color-scheme: dark)").matches);
    const layer = window.protomapsL.leafletLayer({ url: "/tiles/{z}/{x}/{y}.mvt", flavor: dark ? "dark" : "light", maxDataZoom: 15,
      attribution: "© OpenStreetMap contributors, Protomaps", pane: "streets" });
    layer.backgroundColor = null;     // the flavour's grey background would hide the land and sea outside saved areas
    return layer;
  }

  const MAKERS = { streets: streetsLayer, counties: countiesLayer, historic_counties: historicCountiesLayer, parks: parksLayer, rivers: riversLayer, roads: roadsLayer, minor: minorLayer, streams: streamsLayer, lakes: lakesLayer, walking: walkingLayer,
                   cycling: cyclingLayer, roman: romanLayer, buried: buriedLayer,
                   rail: railLayer, underground: undergroundLayer, trails: trailsLayer, towns: townsLayer, landscape: landscapeLayer, airports: airportsLayer, stations: stationsLayer,
                   defences: defencesLayer };

  // ---- attach to a map -------------------------------------------------------------------
  function offline(map) {
    if (!map.getPane("basemap")) map.createPane("basemap").style.zIndex = 250;   // below historic maps
    const r = L.canvas({ padding: 0.3, pane: "basemap" });
    const group = L.layerGroup([landLayer(map, r)]);
    const layers = {};
    LAYERS.forEach((l) => { layers[l.key] = MAKERS[l.key](map, r); });
    group.layers = layers;
    group.on("add", () => { map.getContainer().classList.add("outline-map"); applyChosen(); });
    group.on("remove", () => { map.getContainer().classList.remove("outline-map"); Object.values(layers).forEach((x) => map.removeLayer(x)); });
    const applyChosen = () => { const on = chosen(); LAYERS.forEach((l) => (on.has(l.key) ? map.addLayer(layers[l.key]) : map.removeLayer(layers[l.key]))); };
    group.applyChosen = applyChosen;
    // over the online street map: only the overlays marked online (routes, borders, Roman roads…)
    group.applyOnline = () => { const on = chosen(); LAYERS.forEach((l) => (l.online && on.has(l.key)
      ? map.addLayer(layers[l.key]) : map.removeLayer(layers[l.key]))); };
    return group;
  }

  // bases: {online: street map, satellite: imagery} (null when hosted: offline only)
  function control(map, offlineGroup, bases) {
    const online = bases && bases.online;
    const C = L.Control.extend({ options: { position: "topright" }, onAdd() {
      const box = L.DomUtil.create("div", "map-layers leaflet-bar");
      const on = chosen();
      box.innerHTML = `<button type="button" class="ml-toggle" aria-expanded="false" title="Map layers">☰ Layers</button>
        <div class="ml-panel" hidden>
          ${online ? `<b>Background</b>
            <label><input type="radio" name="ml-base" value="online"> Street map (online)</label>
            <label><input type="radio" name="ml-base" value="satellite"> Satellite (online)</label>
            <label><input type="radio" name="ml-base" value="offline"> Offline map</label>` : "<b>Offline map</b>"}
          <div class="ml-overlays">${LAYERS.map((l) => `<label class="${l.online ? "ml-any" : "ml-off-only"}"><input type="checkbox" value="${l.key}" ${on.has(l.key) ? "checked" : ""}> ${l.label}</label>`).join("")}</div>
          ${online ? '<small class="ml-hint">Greyed layers show on the offline map only.</small>' : ""}
          ${IS_STATIC ? "" : '<button type="button" class="btn small ghost ml-save">⬇ Save this area for offline</button><span class="ml-save-status hint"></span>'}
          <small>Data: Natural Earth, GeoNames, © OpenStreetMap contributors</small></div>`;
      L.DomEvent.disableClickPropagation(box);
      L.DomEvent.disableScrollPropagation(box);
      const panel = box.querySelector(".ml-panel"), btn = box.querySelector(".ml-toggle");
      btn.onclick = () => { panel.hidden = !panel.hidden; btn.setAttribute("aria-expanded", String(!panel.hidden)); };
      const saveBtn = box.querySelector(".ml-save");      // not "save": that name stores the layer choice
      if (saveBtn) saveBtn.onclick = () => saveArea(map, box.querySelector(".ml-save-status"));
      const current = () => (map.hasLayer(offlineGroup) ? "offline" : bases && map.hasLayer(bases.satellite) ? "satellite" : "online");
      const syncBase = () => {
        const isOff = map.hasLayer(offlineGroup), cur = current();
        box.querySelectorAll("input[name=ml-base]").forEach((i) => { i.checked = i.value === cur; });
        box.querySelector(".ml-overlays").classList.toggle("online", !isOff);
        const hint = box.querySelector(".ml-hint");
        if (hint) hint.hidden = isOff;
      };
      box.addEventListener("change", (e) => {
        if (e.target.name === "ml-base") {
          const want = e.target.value;
          save(BASE_STORE, want);
          [offlineGroup, bases.online, bases.satellite].forEach((l) => map.removeLayer(l));
          map.addLayer(want === "offline" ? offlineGroup : bases[want]);
          syncBase();
          return;
        }
        save(STORE, [...box.querySelectorAll(".ml-overlays input:checked")].map((i) => i.value));
        if (map.hasLayer(offlineGroup)) offlineGroup.applyChosen(); else offlineGroup.applyOnline();
      });
      map.on("layeradd layerremove", syncBase);
      setTimeout(syncBase);
      if (typeof Historic !== "undefined") Historic.bind(panel, map);
      return box;
    } });
    map.addControl(new C());
  }

  // Save the street detail of the area in view (zoom 10–15) for offline use; progress in `status`
  async function saveArea(map, status) {
    const b = map.getBounds(), name = prompt("Name for this saved area", "Saved area");
    if (name === null) return;
    const r = await fetch("/api/street_tiles", { method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name, bbox: [b.getSouth(), b.getWest(), b.getNorth(), b.getEast()] }) }).then((x) => x.json());
    if (r.error) { status.textContent = r.error; return; }
    const poll = async () => {
      const s = await fetch("/api/street_tiles").then((x) => x.json());
      const j = s.job || {};
      status.textContent = j.state === "running" ? ` ${j.done}/${j.total} tiles…` : j.state === "done"
        ? ` Saved (${j.tiles} tiles, ${(j.bytes / 1e6).toFixed(1)} MB).` : j.state === "error" ? ` Failed: ${j.error}` : "";
      if (j.state === "running") setTimeout(poll, 1500);
      else if (j.state === "done") map.eachLayer((l) => l.redraw && l.options && String(l.options.url || "").startsWith("/tiles/") && l.redraw());
    };
    poll();
  }

  // Background for any map. opts.control adds the layer switcher (main maps).
  function attach(map, opts = {}) {
    const off = offline(map);
    map.attributionControl.addAttribution("Natural Earth · GeoNames · © OpenStreetMap contributors");
    // maps made while hidden (modals, closed tabs) have no size: redraw when their box changes,
    // keeping the same centre
    if (typeof ResizeObserver !== "undefined") {
      const el = map.getContainer();
      new ResizeObserver(() => {
        if (!el.clientWidth || !el.clientHeight || !map._loaded) return;
        const c = map.getCenter(), z = map.getZoom();      // centre as last set, before the new size counts
        map.invalidateSize({ pan: false });
        map.setView(c, z, { animate: false });
      }).observe(el);
    }
    if (IS_STATIC) {
      map.addLayer(off);
      if (opts.control) control(map, off, null);
      return;
    }
    const online = L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", { maxZoom: 19 });
    // Esri World Imagery (free to show with attribution) with Esri's place-name and border labels on top
    const ESRI = "https://server.arcgisonline.com/ArcGIS/rest/services/";
    const satellite = L.layerGroup([
      L.tileLayer(ESRI + "World_Imagery/MapServer/tile/{z}/{y}/{x}", { maxZoom: 19, maxNativeZoom: 18,
        attribution: "Imagery © Esri, Maxar, Earthstar Geographics, and the GIS User Community" }),
      L.tileLayer(ESRI + "Reference/World_Boundaries_and_Places/MapServer/tile/{z}/{y}/{x}", { maxZoom: 19, maxNativeZoom: 18 }),
    ]);
    let loaded = 0, failed = 0;
    const watch = (layer, isOn) => {
      layer.on("tileload", () => { loaded++; });
      layer.on("tileerror", () => {            // no internet or tile server down: switch to offline
        failed++;
        if (failed >= 4 && loaded === 0 && isOn()) {
          map.removeLayer(online); map.removeLayer(satellite);
          if (opts.control) Object.values(off.layers).forEach((x) => map.removeLayer(x));
          map.addLayer(off);
        }
      });
    };
    watch(online, () => map.hasLayer(online));
    satellite.eachLayer((t) => watch(t, () => map.hasLayer(satellite)));
    const wanted = new URLSearchParams(location.search).get("base") || read(BASE_STORE, Prefs.get("mapBase"));
    if (opts.control) {                        // main maps: chosen overlays over the online backgrounds too
      online.on("add", () => off.applyOnline());
      satellite.on("add", () => off.applyOnline());
    }
    map.addLayer(wanted === "offline" ? off : wanted === "satellite" ? satellite : online);
    if (opts.control) control(map, off, { online, satellite });
  }

  // "Getting there" lines: any element with data-transport="lat,lon" (detail views)
  // and, with data-visit="<record id>", who looks after it, opening hours and entry (OpenStreetMap)
  const FEE = { yes: "Entry fee", no: "Free entry", donation: "Donations welcome" };
  const ACCESS = { yes: "Wheelchair accessible", limited: "Limited wheelchair access", no: "Not wheelchair accessible" };
  const mountTransport = async (el) => {
    el.dataset.transportDone = "1";
    const [lat, lon] = el.dataset.transport.split(",").map(Number);
    const [near, visit] = await Promise.all([nearestStations(lat, lon).then((s) => s.slice(0, 3)),
      el.dataset.visit ? api("/api/visiting/" + encodeURIComponent(el.dataset.visit)).catch(() => null) : null]);
    const lines = [];
    if (visit) {
      const bits = [visit.operator && `Looked after by ${esc(visit.operator)}`, visit.opening_hours && `Open: <code>${esc(visit.opening_hours)}</code>`,
        FEE[visit.fee] || (visit.fee && `Entry: ${esc(visit.fee)}`), ACCESS[visit.wheelchair],
        visit.website && `<a href="${esc(visit.website)}" target="_blank" rel="noopener">Visitor website</a>`].filter(Boolean);
      if (bits.length) lines.push(`<b>Visiting:</b> ${bits.join(" · ")} <span class="hint">(OpenStreetMap; check before you go)</span>`);
    }
    if (near.length) lines.push(`<b>Getting there:</b> ${near.map((s) => `${s.icon} ${esc(s.name)} <span class="hint">${Prefs.dist(s.km, 1)}</span>`).join(" · ")}`);
    el.innerHTML = lines.join("<br>");
  };
  const scan = (root) => root.querySelectorAll && root.querySelectorAll("[data-transport]:not([data-transport-done])").forEach(mountTransport);
  new MutationObserver((ms) => ms.forEach((m) => m.addedNodes.forEach((n) => n.nodeType === 1 && scan(n.parentNode || n))))
    .observe(document.documentElement, { childList: true, subtree: true });
  document.addEventListener("DOMContentLoaded", () => scan(document));

  return { attach, LAYERS, nearestStations };
})();
