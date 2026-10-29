// Map layers of "Change over time" (static/data/change/layers.json, written by bidb.change_layers and
// bidb.change_geology): HYDE population and cropland grids that follow the year slider, and fixed layers
// (bedrock geology, coalfields, ancient woodland, land grades...), and towns as dots sized by population. One layer at a time, with its legend, note and source.
// ChangeLayers.mount(box, map) -> { setYear(y), pause(on) }
const ChangeLayers = (() => {
  const ROOT = (typeof IS_STATIC !== "undefined" && IS_STATIC ? "static" : "/static") + "/data/change/";
  const KEY = "bidb_change_layer";
  let meta = null;
  const load = () => (meta = meta || fetch(ROOT + "layers.json").then((r) => r.json()).catch(() => ({ layers: [] })));
  const yt = (y) => (y < 0 ? `${-y} BC` : y < 1000 ? `AD ${y}` : String(y));

  function mount(box, map) {
    box.innerHTML = `<div class="cl-head"><label>Map layer <select class="cl-pick"><option value="">None</option></select></label>
      <select class="cl-date" aria-label="Date of the map" hidden></select><span class="cl-when"></span></div><div class="cl-info"></div>`;
    const pick = box.querySelector(".cl-pick"), info = box.querySelector(".cl-info"), when = box.querySelector(".cl-when");
    const dateSel = box.querySelector(".cl-date");
    if (!map.getPane("changePane")) { map.createPane("changePane"); map.getPane("changePane").style.zIndex = 350; }
    let layers = [], current = null, shown = null, year = null, geo = {}, paused = false;

    // the latest date of the layer at or before the slider's year (null: the layer starts later); fixed layers have one
    const yearFor = (l) => {
      if (l.years.length === 1) return l.years[0];
      if (dateSel.value) return +dateSel.value;        // a date chosen for this layer wins over the slider
      const y = year ?? l.years[l.years.length - 1];
      return l.years.filter((v) => v <= y).pop() ?? null;
    };
    const whenText = (l, y) => (l.years.length === 1 ? (l.date || "") : y == null ? `starts ${yt(l.years[0])}; move the year slider`
      : dateSel.value ? "" : `map for ${l.labels?.[y] ?? yt(y)}${year == null ? " (latest; use the year slider)" : ""}`);
    const radius = (k) => 2 + Math.sqrt(k) * 0.45;    // dot area follows population (thousands)
    const dots = L.svg({ pane: "changePane" });      // the map's canvas only repaints new dots once it moves
    const spanCanvas = L.canvas({ pane: "changePane" });  // thousands of stations: canvas, restyled not rebuilt
    function drawInfo(l) {
      if (!l) { info.innerHTML = ""; when.textContent = ""; return; }
      const srcs = l.sources || [l.source];
      info.innerHTML = `<div class="cl-legend">${l.legend.map((k) => `<span><i style="background:${k.color}"></i>${esc(k.label)}</span>`).join("")}
          ${l.unit ? `<em>${esc(l.unit)}</em>` : ""}</div>
        <p class="cc-note">${esc(l.note || "")}</p>
        <div class="cc-src">Source: ${srcs.map((s) => `<a href="${esc(s.url)}" target="_blank" rel="noopener" title="${esc(s.citation)}">${esc(s.short)}</a>
          <span class="cc-lic">(${esc(s.licence)})</span>`).join("; ")}${l.modelled ? " · modelled" : ""}</div>`;
    }
    async function show() {
      const l = paused ? null : layers.find((x) => x.id === pick.value) || null;
      if (l !== current && shown) { map.removeLayer(shown); shown = null; }
      if (l !== current) {                              // dates of a time layer: follow the slider, or pick one
        const many = l && l.years && l.years.length > 1;
        dateSel.hidden = !many;
        dateSel.innerHTML = many ? `<option value="">Follow the year slider</option>` +
          l.years.map((y) => `<option value="${y}">${l.labels?.[y] ?? yt(y)}</option>`).join("") : "";
      }
      current = l;
      drawInfo(l);
      if (!l) return;
      if (l.kind === "grid") {
        geo[l.id] = geo[l.id] || fetch(ROOT + l.file).then((r) => r.json());   // {year: PNG data URI}
        const y = yearFor(l), url = y == null ? null : (await geo[l.id])[y];
        if (current !== l) return;
        when.textContent = whenText(l, y);
        if (!url) { if (shown) { map.removeLayer(shown); shown = null; } }
        else if (shown) shown.setUrl(url);
        else shown = L.imageOverlay(url, l.bounds, { opacity: 0.72, pane: "changePane", className: "cl-grid", interactive: false }).addTo(map);
      } else if (l.kind === "points") {
        geo[l.id] = geo[l.id] || fetch(ROOT + l.file).then((r) => r.json());   // [[name, lat, lon, {year: [thousands, estimated]}]]
        const y = yearFor(l), data = await geo[l.id];
        if (current !== l) return;
        when.textContent = whenText(l, y);
        if (shown) { map.removeLayer(shown); shown = null; }
        if (y == null) return;
        shown = L.layerGroup(data.filter((p) => p[3][y]).sort((a, b) => b[3][y][0] - a[3][y][0]).map(([name, lat, lon, v]) => {
          const [k, est] = v[y];
          return L.circleMarker([lat, lon], { pane: "changePane", renderer: dots, radius: radius(k), weight: 1, color: "#7a3418",
            fillColor: est ? l.legend[1].color : l.legend[0].color, fillOpacity: 0.8 })
            .bindTooltip(`${esc(name)}: about ${ChangeCharts.fmt(k * 1000)} people in ${yt(y)}${est ? " (estimated)" : ""}`);
        })).addTo(map);
      } else if (l.kind === "spans" || l.kind === "lines") {   // dated dots or lines: built once, restyled per year
        geo[l.id] = geo[l.id] || fetch(ROOT + l.file).then((r) => r.json());
        const y = yearFor(l) ?? l.years[l.years.length - 1], data = await geo[l.id];
        if (current !== l) return;
        if (!shown && l.kind === "lines") {
          shown = L.layerGroup(data.map(([kind, o, c, path]) => Object.assign(L.polyline(path.map(([x, yy]) => [yy, x]), {
            pane: "changePane", renderer: spanCanvas, weight: 1.6, interactive: true })
            .bindTooltip(`${kind === "canal" ? "Canal" : "Railway"}: opened ${o}${c ? `, closed ${c}` : ""}`, { sticky: true }),
            { span: [o, c], line: kind }))).addTo(map);
        } else if (!shown) {
          shown = L.layerGroup(data.map(([name, lat, lon, o, c, k]) => Object.assign(L.circleMarker([lat, lon], {   // k: legend entry (firms' industry)
            pane: "changePane", renderer: spanCanvas, radius: 2.2, weight: 0, fillOpacity: 0.9 })
            .bindTooltip(`${esc(name)}${k != null ? ` (${esc(l.legend[k].label)})` : ""}: ${l.verb || (l.id === "firms" ? "founded" : "opened")} ${o}${c ? `, closed ${c}` : ""}`),
            { span: [o, c], key: k ?? 0 }))).addTo(map);
        }
        let open = 0;
        shown.eachLayer((m) => {
          if (m.line) {                                    // [kind, opened, closed, path]: railway or canal line
            const [o, c] = m.span, now = o <= y && !(c && c <= y), gone = c && c <= y;
            open += now ? 1 : 0;
            m.setStyle({ color: now ? l.legend[m.line === "canal" ? 1 : 0].color : l.legend[2].color,
                         opacity: now ? 0.9 : gone ? 0.35 : 0, weight: now ? 1.6 : 1 });
            return;
          }
          const [o, c] = m.span, now = o <= y && !(c && c <= y), gone = c && c <= y;
          open += now ? 1 : 0;
          m.setStyle({ fillColor: now ? l.legend[m.key].color : l.legend[l.legend.length - 1].color, fillOpacity: now ? 0.9 : gone ? 0.5 : 0,
                       radius: now ? 2.2 : 1.6 });
        });
        when.textContent = `${open.toLocaleString()} ${l.count || (l.kind === "lines" ? "sections open in" : "open in")} ${y}${year == null && !dateSel.value ? " (use the year slider)" : ""}`;
        spanCanvas._redraw?.();                         // the canvas does not always repaint until the map moves
      } else if (l.kind === "choro") {                 // areas with {year: people}: coloured by the share of the base year
        geo[l.id] = geo[l.id] || fetch(ROOT + l.file).then((r) => r.json());
        const y = yearFor(l) ?? l.years[l.years.length - 1], data = await geo[l.id];
        if (current !== l) return;
        const share = (f) => 100 * f.properties.pop[y] / f.properties.pop[l.base];
        const colour = (v) => l.legend[Math.max(0, l.bins.filter((b) => v >= b).length - 1)].color;
        const style = (f) => ({ fillColor: colour(share(f)), fillOpacity: 0.7, weight: 0.6, color: "#555", opacity: 0.6 });
        if (!shown) {
          shown = L.geoJSON(data, { pane: "changePane", renderer: dots, style }).addTo(map);
          shown.eachLayer((m) => m.bindTooltip(() => `${esc(m.feature.properties.name)}: ${m.feature.properties.pop[shown.year]
            ?.toLocaleString()} people in ${shown.year} (${Math.round(share(m.feature))}% of ${l.base})`, { sticky: true }));
        } else shown.setStyle(style);
        shown.year = y;
        when.textContent = `census of ${y}${year == null && !dateSel.value ? " (use the year slider)" : ""}`;
      } else if (!shown) {
        when.textContent = "";
        geo[l.id] = geo[l.id] || fetch(ROOT + l.file).then((r) => r.json());
        const data = await geo[l.id];
        if (current !== l) return;
        shown = L.geoJSON(data, {
          pane: "changePane",
          style: (f) => ({ fillColor: f.properties.p != null ? l.legend[f.properties.p].color : l.legend[0].color,
                           fillOpacity: l.id === "coalfields" ? 0.35 : 0.5, weight: 0.4, color: "#555", opacity: 0.5 }),
          onEachFeature: (f, lay) => lay.bindTooltip(f.properties.name || f.properties.a ||
            (f.properties.p != null ? l.legend[f.properties.p].label : ""), { sticky: true }),
        }).addTo(map);
      }
    }
    load().then((m) => {
      layers = m.layers || [];
      const groups = { "Through time": layers.filter((l) => l.years && l.years.length > 1),
                       "The land": layers.filter((l) => !l.years || l.years.length < 2) };
      pick.innerHTML += Object.entries(groups).map(([g, ls]) => `<optgroup label="${g}">${ls.map((l) =>
        `<option value="${esc(l.id)}">${esc(l.title)}</option>`).join("")}</optgroup>`).join("");
      try { pick.value = localStorage.getItem(KEY) || ""; } catch (e) { /* private mode */ }
      if (pick.value) show();
    });
    dateSel.addEventListener("change", show);
    pick.addEventListener("change", () => {
      try { localStorage.setItem(KEY, pick.value); } catch (e) { /* private mode */ }
      show();
    });
    return {
      setYear(y) { year = y; if (current && current.kind !== "geojson") show(); },
      pause(on) { paused = on; show(); },          // the panel was hidden / shown again
    };
  }

  return { mount };
})();
