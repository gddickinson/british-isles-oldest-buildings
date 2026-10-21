// Catalogue map: clustered markers coloured by building group or period, legend, map-area filter.
const MapView = {
  map: null, cluster: null, onArea: null,

  init(el, onArea) {
    if (this.map) return;
    this.onArea = onArea;
    this.map = L.map(el, { preferCanvas: true, maxZoom: 18 }).setView([54.3, -4.5], 6);
    addBaseLayer(this.map, { control: true });
    this.cluster = L.markerClusterGroup(Prefs.cluster({ chunkedLoading: true, maxClusterRadius: 40,
                                                        disableClusteringAtZoom: 13 }));
    this.map.addLayer(this.cluster);
    attachOutlines(this.map);
    this.map.on("moveend", () => this.onArea && this.onArea(this.bboxString()));
  },

  bboxString() {
    const b = this.map.getBounds();
    return [b.getSouth(), b.getWest(), b.getNorth(), b.getEast()].map((v) => v.toFixed(4)).join(",");
  },

  colorFor(p, by) {
    return by === "period" ? periodColor(p.period) : groupColor(p.category_group);
  },

  setPoints(pts, by) {
    this.cluster.clearLayers();
    const ring = cssVar("--surface") || "#fff";
    this.cluster.addLayers(pts.map((p) => {
      const m = L.circleMarker([p.lat, p.lon], { radius: 7, weight: 2, color: ring, fillOpacity: 0.95,
                                                 fillColor: this.colorFor(p, by) });
      m.bindPopup(`<b>${esc(p.name)}</b><br>${esc(p.date_text || "")}<br>${esc(p.category)} · ${esc(p.period)}
        <br><a href="#" data-open="${esc(p.id)}">View details</a>`);
      m.bindTooltip(esc(p.name));
      return m;
    }));
    this.legend(pts, by);
    setTimeout(() => this.map.invalidateSize(), 50);
  },

  legend(pts, by) {
    const el = document.getElementById("legend");
    const names = by === "period" ? PERIODS : GROUPS;
    const counts = {};
    pts.forEach((p) => { const k = by === "period" ? p.period : p.category_group; counts[k] = (counts[k] || 0) + 1; });
    const keys = names.filter((n) => counts[n]).concat(Object.keys(counts).filter((k) => !names.includes(k)));
    el.innerHTML = `<b>${by === "period" ? "Period" : "Building group"}</b>` + keys.map((k) =>
      `<div><i style="background:${by === "period" ? periodColor(k) : groupColor(k)}"></i>${esc(k)} <em>${counts[k]}</em></div>`).join("");
  },

  flyTo(lat, lon, zoom = 11) { if (this.map) this.map.setView([lat, lon], zoom); },

  // Places-of-interest overlay: one toggle per layer, drawn smaller with a dark ring
  overlay: null, overlayOn: new Set(),
  initOverlay(box) {
    if (!box || box.dataset.ready) return;
    box.dataset.ready = "1";
    box.insertAdjacentHTML("beforeend", PLACE_GROUPS.map((g) => `<label class="check overlay-item">
      <input type="checkbox" value="${esc(g)}"><span class="dot" style="background:${placeColor(g)}"></span>${esc(g)}</label>`).join(""));
    this.overlay = L.markerClusterGroup(Prefs.cluster({ chunkedLoading: true, maxClusterRadius: 50, disableClusteringAtZoom: 14,
      iconCreateFunction: (c) => L.divIcon({ html: `<span>${c.getChildCount()}</span>`, className: "overlay-cluster", iconSize: [30, 30] }) }));
    this.map.addLayer(this.overlay);
    box.addEventListener("change", () => {
      this.overlayOn = new Set([...box.querySelectorAll("input:checked")].map((i) => i.value));
      this.loadOverlay();
    });
  },
  async loadOverlay() {
    this.overlay.clearLayers();
    if (!this.overlayOn.size) return;
    const p = new URLSearchParams();
    this.overlayOn.forEach((g) => p.append("kind_group", g));
    const pts = await api("/api/places/map?" + p).catch(() => []);
    const ink = cssVar("--ink") || "#222";
    this.overlay.addLayers(pts.map((pt) => {
      const m = L.circleMarker([pt.lat, pt.lon], { radius: 5, weight: 1.5, color: ink, fillOpacity: 0.9,
                                                   fillColor: placeColor(pt.kind_group) });
      m.bindTooltip(`${esc(pt.name)} · ${esc(pt.kind_label)}`);
      m.on("click", () => openPlace(pt.id));
      return m;
    }));
  },
};
