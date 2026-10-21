// Building outlines (OpenStreetMap footprints of catalogue buildings) on zoomed-in maps.
function attachOutlines(map, minZoom = 15) {
  const layer = L.layerGroup().addTo(map);
  let seq = 0;
  async function draw() {
    const my = ++seq;
    if (map.getZoom() < minZoom) { layer.clearLayers(); return; }
    const b = map.getBounds();
    const rows = await api(`/api/footprints?bbox=${[b.getSouth(), b.getWest(), b.getNorth(), b.getEast()].map((v) => v.toFixed(5)).join(",")}`).catch(() => []);
    if (my !== seq) return;                         // a newer move superseded this one
    layer.clearLayers();
    rows.forEach((r) => {
      try {
        L.geoJSON(JSON.parse(r.footprint), { style: () => ({ color: groupColor(r.category_group), weight: 2,
          fillOpacity: 0.2, fillColor: groupColor(r.category_group) }) })
          .bindTooltip(esc(r.name)).on("click", () => (typeof openDetail === "function" ? openDetail(r.id)
            : (location.href = buildingUrl(r.id)))).addTo(layer);
      } catch (e) { /* malformed outline: skip */ }
    });
  }
  map.on("moveend", draw);
  draw();
  return layer;
}
