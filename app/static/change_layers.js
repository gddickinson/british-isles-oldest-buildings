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
      <span class="cl-when"></span></div><div class="cl-info"></div>`;
    const pick = box.querySelector(".cl-pick"), info = box.querySelector(".cl-info"), when = box.querySelector(".cl-when");
    if (!map.getPane("changePane")) { map.createPane("changePane"); map.getPane("changePane").style.zIndex = 350; }
    let layers = [], current = null, shown = null, year = null, geo = {}, paused = false;

    // the latest date of the layer at or before the slider's year (null: the layer starts later); fixed layers have one
    const yearFor = (l) => {
      if (l.years.length === 1) return l.years[0];
      const y = year ?? l.years[l.years.length - 1];
      return l.years.filter((v) => v <= y).pop() ?? null;
    };
    const whenText = (l, y) => (l.years.length === 1 ? (l.date || "") : y == null ? `starts ${yt(l.years[0])}; move the year slider`
      : `map for ${yt(y)}${year == null ? " (latest; use the year slider)" : ""}`);
    const radius = (k) => 2 + Math.sqrt(k) * 0.45;    // dot area follows population (thousands)
    const dots = L.svg({ pane: "changePane" });      // the map's canvas only repaints new dots once it moves
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
