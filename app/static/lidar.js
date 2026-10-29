// LiDAR ground model in the map's layer panel (roadmap LD1): the Environment Agency's composite 1 m DTM hillshade of
// England (WMS, Open Government Licence), over the background with an opacity slider. Earthworks, barrows, field
// systems, hollow ways and lost villages show where trees and buildings hide them. Local GUI only (the hosted copy
// cannot reach map servers). Scotland, Wales and Ireland publish no hillshade service yet (roadmap LD1).
const Lidar = (() => {
  const STORE = "bi_lidar";
  const SOURCES = [{
    key: "ea", label: "England, 1 m (Environment Agency)",
    url: "https://environment.data.gov.uk/spatialdata/lidar-composite-digital-terrain-model-dtm-1m/wms",
    layers: "Lidar_Composite_Hillshade_DTM_1m", bounds: [[49.85, -6.45], [55.82, 1.8]], minZoom: 10,
    attribution: "LiDAR © Environment Agency, Open Government Licence",
  }];
  const read = () => { try { return JSON.parse(localStorage.getItem(STORE)) || {}; } catch (e) { return {}; } };
  const save = (v) => { try { localStorage.setItem(STORE, JSON.stringify(v)); } catch (e) { /* private mode */ } };

  function make(s) {
    return L.tileLayer.wms(s.url, { layers: s.layers, styles: "", format: "image/png", transparent: true, version: "1.3.0",
      pane: "lidar", bounds: s.bounds, minZoom: s.minZoom, maxZoom: 19, attribution: s.attribution, tileSize: 512 });
  }

  function bind(panel, map) {
    if (IS_STATIC) return;
    if (!map.getPane("lidar")) map.createPane("lidar").style.zIndex = 330;      // over the background, under historic maps
    const st = { key: "", opacity: 0.7, ...read() };
    const fromUrl = new URLSearchParams(location.search).get("lidar");
    if (fromUrl !== null) st.key = fromUrl === "0" ? "" : fromUrl || "ea";
    const block = document.createElement("div");
    block.className = "ml-historic ml-lidar";
    block.innerHTML = `<b>Ground (LiDAR)</b>
      <select class="ml-lsel"><option value="">None</option>
        ${SOURCES.map((s) => `<option value="${s.key}">${esc(s.label)}</option>`).join("")}</select>
      <label class="ml-op">Opacity <input type="range" min="0.2" max="1" step="0.05" value="${st.opacity}"></label>
      <small class="ml-lnote"></small>`;
    panel.insertBefore(block, panel.querySelector(":scope > small:last-child"));
    const sel = block.querySelector("select"), op = block.querySelector("input"), note = block.querySelector(".ml-lnote");
    sel.value = st.key;
    let current = null;
    const hint = () => {
      const s = SOURCES.find((x) => x.key === sel.value);
      note.textContent = !s ? "" : map.getZoom() < s.minZoom ? `Zoom in to see it (from zoom ${s.minZoom}).`
        : "Light from the north-west; look for banks, ditches and mounds.";
    };
    const apply = () => {
      if (current) map.removeLayer(current);
      current = null;
      map.getPane("lidar").style.opacity = op.value;
      save({ key: sel.value, opacity: parseFloat(op.value) });
      const s = SOURCES.find((x) => x.key === sel.value);
      if (s) current = make(s).addTo(map);
      hint();
    };
    sel.addEventListener("change", apply);
    op.addEventListener("input", apply);
    map.on("zoomend", hint);
    apply();
  }
  return { bind, SOURCES };
})();
