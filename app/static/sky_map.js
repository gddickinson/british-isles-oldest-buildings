// Sun and moon lines on the Map page (roadmap SK4): "☀ Sun lines" draws, from a chosen point, where the sun rises
// and sets on a chosen date, at the solstices and equinoxes and (optionally) where the moon rises and sets at its
// major standstill, for today's sky or the sky of a chosen year; researched alignments near the point (sky.json) in
// red. Click the map to move the point. `?sky=1&lat=&lon=[&skyyear=]` opens it there (detail view link).
// SK7b: in the local GUI "Over the real skyline" reads the point's skyline (/api/horizon) and draws every line
// where the first or last gleam clears the hills (Sky.horizonAzimuth / horizonAzimuthDec); flat direction on hover.
const SkyMap = (() => {
  let map = null, svg = null, layer = null, point = null, on = false, panel = null, near = [], hz = null, hzFor = null;
  const st = { date: new Date().toISOString().slice(0, 10), solstices: true, moon: false, year: "", skyline: false };

  function end(az, frac = 0.42) {
    const size = map.getSize(), c = map.latLngToContainerPoint(point);
    const len = Math.min(size.x, size.y) * frac, a = az * Math.PI / 180;
    return map.containerPointToLatLng([c.x + len * Math.sin(a), c.y - len * Math.cos(a)]);
  }
  const fmt = (d) => d.toLocaleDateString(undefined, { day: "numeric", month: "short" });
  function ray(az, cls, label, frac, flat = null) {
    if (az == null) return;
    const other = flat != null && Math.abs(flat - az) >= 0.05 ? ` (flat horizon ${flat.toFixed(1)}°)` : "";
    L.polyline([point, end(az, frac)], { renderer: svg, className: "sky-ray " + cls, interactive: true, weight: cls.includes("aligned") ? 5 : 3 })
      .bindTooltip(`${label} · ${az.toFixed(1)}° ${Sky.compass(az)}${other}`, { sticky: true }).addTo(layer);
  }
  // Over the skyline when it is read, else over a flat horizon; the flat direction kept for the tooltip.
  const eventRay = (lat, body, e, rs, year, cls, label) => {
    const flat = Sky.eventAzimuth(lat, body, e, rs, year);
    ray(hz ? Sky.horizonAzimuth(lat, body, e, rs, year, hz.alt, hz.step) : flat, cls, label, 0.36, hz ? flat : null);
  };
  const decRay = (lat, dec, rs, cls, label) => {
    const flat = Sky.azimuth(lat, dec, rs);
    ray(hz ? Sky.horizonAzimuthDec(lat, dec, "sun", rs, hz.alt, hz.step) : flat, cls, label, 0.46, hz ? flat : null);
  };

  function draw() {
    layer.clearLayers();
    if (!on || !point) return;
    const lat = point.lat, year = st.year === "" ? 2000 : +st.year;
    L.circleMarker(point, { renderer: svg, radius: 5, color: cssVar("--ink"), weight: 2, fillOpacity: 1, interactive: false }).addTo(layer);
    if (st.solstices) {
      ["summer_solstice", "equinox", "winter_solstice"].forEach((e) => ["rise", "set"].forEach((rs) =>
        eventRay(lat, "sun", e, rs, year, "sun-event", `${Sky.NAMES[e]} sun${rs}`)));
    }
    if (st.moon) {
      ["major_north", "major_south"].forEach((e) => ["rise", "set"].forEach((rs) =>
        eventRay(lat, "moon", e, rs, year, "moon", `${Sky.NAMES[e]}: moon${rs}`)));
    }
    const d = new Date(st.date + "T12:00:00Z");
    if (!Number.isNaN(d.getTime())) {
      const dec = Sky.sunDeclination(Sky.jdOf(d));
      ["rise", "set"].forEach((rs) => decRay(lat, dec, rs, "sun-date", `Sun${rs} on ${fmt(d)}`));
    }
    near.filter((a) => a.event).forEach((a) => ray(a.azimuth_horizon_built ?? a.azimuth_built ?? a.azimuth_now, "aligned", `${a.name}: ${Sky.NAMES[a.event]} ${a.body}${a.rise_set} (researched)`, 0.5));
    const pos = panel.querySelector(".sky-pos");
    if (pos) pos.textContent = `${point.lat.toFixed(4)}, ${point.lng.toFixed(4)}`;
    const note = panel.querySelector(".sky-hz-note");
    if (note) note.textContent = hz ? "Over the skyline (bare ground: no trees or buildings)." : "Flat horizon.";
  }

  // The point's skyline from /api/horizon (a few seconds the first time for a new place); a newer click wins.
  async function readSkyline() {
    hz = null;
    if (!st.skyline || !point) return;
    const at = point, key = `${at.lat.toFixed(4)},${at.lng.toFixed(4)}`;
    const note = panel.querySelector(".sky-hz-note");
    if (note) note.textContent = "Reading the terrain…";
    hzFor = key;
    const h = await fetch(`/api/horizon?lat=${at.lat.toFixed(4)}&lon=${at.lng.toFixed(4)}`).then((r) => (r.ok ? r.json() : null)).catch(() => null);
    if (hzFor !== key || !st.skyline) return;
    hz = h && { ...h, alt: h.alt.map((a) => a / 100) };
    if (!hz && note) { note.textContent = "Terrain not available here: flat horizon."; return; }
    draw();
  }

  async function setPoint(ll) {
    point = L.latLng(ll);
    const all = (await SkyHere.load()).all;
    near = all.filter((a) => map.distance(point, [a.lat, a.lon]) < 600);
    if (near.length && st.year === "" && near[0].built != null) { st.year = String(near[0].built); panel.querySelector("[name=year]").value = st.year; }
    hz = null;
    draw();
    readSkyline();
  }

  function toggle(v = !on, at = null) {
    on = v;
    panel.hidden = !on;
    map.getContainer().classList.toggle("sky-picking", on);
    if (on && (at || !point)) setPoint(at || map.getCenter());
    else draw();
  }

  function attach(m) {
    map = m;
    svg = L.svg();                    // the page draws on canvas; the rays need SVG for their CSS classes
    layer = L.layerGroup().addTo(map);
    const Ctl = L.Control.extend({
      onAdd() {
        const box = L.DomUtil.create("div", "sky-control leaflet-bar");
        box.innerHTML = `<button type="button" class="sky-toggle" title="Where the sun and moon rise and set from a point">☀ Sun lines</button>
          <div class="sky-panel" hidden>
            <p class="hint">Click the map to move the point: <span class="sky-pos"></span></p>
            <label>Date <input type="date" name="date" value="${st.date}"></label>
            <label class="check"><input type="checkbox" name="solstices" checked> Solstices and equinoxes</label>
            <label class="check"><input type="checkbox" name="moon"> Moon at its major standstill</label>
            <label>Sky of the year <input type="number" name="year" placeholder="today" step="100" title="Negative for BC: the earth's tilt changes the solstice directions over the millennia"></label>
            <p class="hint"><span class="sky-key sun">date</span> <span class="sky-key then">solstices, equinoxes</span>
              <span class="sky-key moon">moon</span> <span class="sky-key aligned">researched alignment</span>. <span class="sky-hz-note">Flat horizon.</span></p>
            ${IS_STATIC ? "" : '<label class="check" title="The skyline round the point from the terrain model: where the first or last gleam clears the hills"><input type="checkbox" name="skyline"> Over the real skyline</label>'}
          </div>`;
        L.DomEvent.disableClickPropagation(box);
        L.DomEvent.disableScrollPropagation(box);
        panel = box.querySelector(".sky-panel");
        box.querySelector(".sky-toggle").addEventListener("click", () => toggle());
        panel.addEventListener("input", (e) => {
          const t = e.target;
          st[t.name] = t.type === "checkbox" ? t.checked : t.value;
          if (t.name === "skyline") { if (st.skyline) readSkyline(); else { hz = null; hzFor = null; draw(); } return; }
          draw();
        });
        return box;
      },
    });
    new Ctl({ position: "topleft" }).addTo(map);
    map.on("click", (e) => on && setPoint(e.latlng));
    map.on("zoomend moveend resize", draw);
    const p = new URLSearchParams(location.search);
    if (p.get("sky")) {
      if (p.get("skyyear")) { st.year = p.get("skyyear"); panel.querySelector("[name=year]").value = st.year; }
      const lat = parseFloat(p.get("lat")), lon = parseFloat(p.get("lon"));
      if (!Number.isNaN(lat) && !Number.isNaN(lon)) toggle(true, [lat, lon]);
    }
  }
  return { attach, toggle };
})();
