// Grid references on the Map page (roadmap LD2): the OS or Irish grid reference under the pointer (bottom left;
// click it to copy), a pop-up with both forms on right-click or long press, and grid references for the finder.
const GridMap = (() => {
  const label = (lat, lon, digits = 8) => {
    const g = OSGrid.forPoint(lat, lon, digits);
    return g ? `${g.grid} grid ${g.ref}` : "off the grids";
  };

  // A typed grid reference ("SU 1224 4219", "O 007 727") -> [lat, lon], else null
  function parse(text) {
    const q = String(text || "").trim();
    if (!/^[a-z][a-z0]?\s*\d/i.test(q)) return null;
    return OSGrid.toLatLon(q) || OSGrid.toLatLon(q, true);      // two letters: OS; one: Irish
  }

  function popup(map, latlng) {
    const { lat, lng } = latlng, ll = `${lat.toFixed(5)}, ${lng.toFixed(5)}`;
    const g = OSGrid.forPoint(lat, lng, 10);
    const row = (name, text) => `<div class="gm-row"><span>${name}</span> <b>${esc(text)}</b>
      <button class="copy-btn" data-copy="${esc(text)}" title="Copy" aria-label="Copy ${name}">⧉</button></div>`;
    L.popup({ className: "gm-popup" }).setLatLng(latlng).setContent(
      (g ? row(g.grid === "OS" ? "OS grid" : "Irish grid", g.ref) : "") + row("Lat, lon", ll)).openOn(map);
  }

  function attach(map) {
    const Readout = L.Control.extend({
      options: { position: "bottomleft" },
      onAdd() {
        const div = L.DomUtil.create("button", "gm-readout");
        div.type = "button";
        div.title = "Grid reference under the pointer (click to copy; right-click the map for more)";
        L.DomEvent.disableClickPropagation(div);
        div.addEventListener("click", () => div.dataset.ref && copyText(div.dataset.ref, div, "Copied"));
        return div;
      },
    });
    const box = new Readout().addTo(map).getContainer();
    const show = (latlng) => {
      const g = OSGrid.forPoint(latlng.lat, latlng.lng, 8);
      box.dataset.ref = g ? g.ref : "";
      box.textContent = label(latlng.lat, latlng.lng);
    };
    map.on("mousemove", (e) => show(e.latlng));
    map.on("moveend", () => { if (!box.textContent) show(map.getCenter()); });
    show(map.getCenter());
    map.on("contextmenu", (e) => popup(map, e.latlng));
  }

  return { attach, parse, label };
})();
