// Map layers of "Change over time" (static/data/change/layers.json, written by bidb.change_layers and
// bidb.change_geology): HYDE population and cropland grids that follow the year slider, and fixed layers
// (bedrock geology, coalfields). One layer at a time, with its legend, note and source.
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

    const yearFor = (l) => {                          // the latest date of the grid at or before the slider's year
      const y = year ?? l.years[l.years.length - 1];
      return l.years.filter((v) => v <= y).pop() ?? l.years[0];
    };
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
        const y = yearFor(l), url = (await geo[l.id])[y];
        if (current !== l) return;
        when.textContent = `map for ${yt(y)}${year == null ? " (latest; use the year slider)" : ""}`;
        if (shown) shown.setUrl(url);
        else shown = L.imageOverlay(url, l.bounds, { opacity: 0.72, pane: "changePane", className: "cl-grid", interactive: false }).addTo(map);
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
      pick.innerHTML += layers.map((l) => `<option value="${esc(l.id)}">${esc(l.title)}</option>`).join("");
      try { pick.value = localStorage.getItem(KEY) || ""; } catch (e) { /* private mode */ }
      if (pick.value) show();
    });
    pick.addEventListener("change", () => {
      try { localStorage.setItem(KEY, pick.value); } catch (e) { /* private mode */ }
      show();
    });
    return {
      setYear(y) { year = y; if (current && current.kind === "grid") show(); },
      pause(on) { paused = on; show(); },          // the panel was hidden / shown again
    };
  }

  return { mount };
})();
