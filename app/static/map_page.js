// Map page: full-screen map with building groups, places-of-interest layers, the detailed
// background (layer switcher), an offline town/village finder and a year slider (time_slider.js).
const E$ = (s) => document.querySelector(s);
const exMap = L.map("ex_map", { preferCanvas: true, maxZoom: 18 });
const exState = { groups: new Set(GROUPS.concat(["Other"])), places: new Set(), landmarks: false, early: false, year: null };
let exBuildings = [], exPlaces = [], exTowns = null, exTime = null, exChange = null;
const inTime = (r) => exState.year === null || TimeSlider.standing(r, exState.year);
const bCluster = L.markerClusterGroup(Prefs.cluster({ chunkedLoading: true, maxClusterRadius: 40, disableClusteringAtZoom: 13 }));
const pCluster = L.markerClusterGroup(Prefs.cluster({ chunkedLoading: true, maxClusterRadius: 50, disableClusteringAtZoom: 14,
  iconCreateFunction: (c) => L.divIcon({ html: `<span>${c.getChildCount()}</span>`, className: "overlay-cluster", iconSize: [30, 30] }) }));

function startView() {
  const p = new URLSearchParams(location.search);
  const lat = parseFloat(p.get("lat")), lon = parseFloat(p.get("lon")), z = parseInt(p.get("z"), 10);
  exMap.setView(isNaN(lat) ? [54.4, -4.8] : [lat, lon], isNaN(z) ? (innerWidth < 700 ? 5 : 6) : z);
}

function drawBuildings() {
  bCluster.clearLayers();
  const ring = cssVar("--surface");
  const pts = exBuildings.filter((b) => exState.groups.has(b.category_group || "Other") && inTime(b));
  bCluster.addLayers(pts.map((b) => {
    const m = L.circleMarker([b.lat, b.lon], { radius: 7, weight: 2, color: ring, fillOpacity: 0.95, fillColor: groupColor(b.category_group) });
    m.bindTooltip(`${esc(b.name)} · ${esc(b.date_text || "")}`);
    m.on("click", () => showBuilding(b.id));
    return m;
  }));
  E$("#ex_bcount").textContent = `(${pts.length.toLocaleString()})`;
}

async function loadBuildings() {
  const p = new URLSearchParams();
  if (exState.landmarks) p.set("landmarks_only", "1");
  if (exState.early) p.set("early_only", "1");
  exBuildings = await api("/api/map?" + p);
  const counts = {};
  exBuildings.forEach((b) => { const g = b.category_group || "Other"; counts[g] = (counts[g] || 0) + 1; });
  E$("#ex_groups").innerHTML = GROUPS.concat(["Other"]).filter((g) => counts[g]).map((g) => `<label class="check">
    <input type="checkbox" value="${esc(g)}" ${exState.groups.has(g) ? "checked" : ""}>
    <span class="dot" style="background:${groupColor(g)}"></span>${esc(g)} <em>${counts[g].toLocaleString()}</em></label>`).join("");
  drawBuildings();
  if (exTime) exTime.refresh();
  exChange?.refresh();
}

async function drawPlaces() {
  exPlaces = [];
  if (exState.places.size) {
    const p = new URLSearchParams();
    exState.places.forEach((g) => p.append("kind_group", g));
    exPlaces = await api("/api/places/map?" + p).catch(() => []);
  }
  renderPlaces();
  if (exTime) exTime.refresh();
  exChange?.refresh();
}

function renderPlaces() {
  pCluster.clearLayers();
  const ink = cssVar("--ink");
  pCluster.addLayers(exPlaces.filter(inTime).map((pt) => {
    const m = L.circleMarker([pt.lat, pt.lon], { radius: 5, weight: 1.5, color: ink, fillOpacity: 0.9, fillColor: placeColor(pt.kind_group) });
    m.bindTooltip(`${esc(pt.name)} · ${esc(pt.kind_label)}`);
    m.on("click", () => openPlace(pt.id));
    return m;
  }));
}

async function showBuilding(id) {
  const b = await api("/api/building/" + encodeURIComponent(id));
  showModal("");
  showDetail(b, document.getElementById("modal-body"), true);
}

// Offline gazetteer: the map's own towns layer (GeoNames), so it works when hosted
async function towns() {
  exTowns = exTowns || await fetch((IS_STATIC ? "static" : "/static") + "/data/basemap/towns.json").then((r) => r.json());
  return exTowns;
}

async function suggest() {
  const q = E$("#ex_q").value.trim().toLowerCase();
  if (q.length < 2) return;
  const list = (await towns()).filter((t) => t[0].toLowerCase().startsWith(q)).slice(0, 12);
  E$("#ex_towns").innerHTML = list.map((t) => `<option value="${esc(t[0])}">`).join("");
}

async function findTown() {
  const q = E$("#ex_q").value.trim().toLowerCase();
  if (!q) return;
  const all = await towns();
  const hit = all.find((t) => t[0].toLowerCase() === q) || all.find((t) => t[0].toLowerCase().startsWith(q));
  if (!hit) { E$("#ex_status").textContent = "Not found"; return; }
  E$("#ex_status").textContent = "";
  exMap.setView([hit[1], hit[2]], hit[3] === 0 ? 11 : hit[3] === 1 ? 12 : 13);
}

function wireExplore() {
  E$("#ex_places").innerHTML = PLACE_GROUPS.map((g) => `<label class="check">
    <input type="checkbox" value="${esc(g)}"><span class="dot" style="background:${placeColor(g)}"></span>${esc(g)}</label>`).join("");
  E$("#ex_groups").addEventListener("change", (e) => {
    if (e.target.checked) exState.groups.add(e.target.value); else exState.groups.delete(e.target.value);
    drawBuildings();
  });
  E$("#ex_places").addEventListener("change", (e) => {
    if (e.target.checked) exState.places.add(e.target.value); else exState.places.delete(e.target.value);
    drawPlaces();
  });
  E$("#ex_landmarks").addEventListener("change", (e) => { exState.landmarks = e.target.checked; loadBuildings(); });
  E$("#ex_early").addEventListener("change", (e) => { exState.early = e.target.checked; loadBuildings(); });
  E$("#ex_q").addEventListener("input", suggest);
  E$("#ex_q").addEventListener("keydown", (e) => { if (e.key === "Enter") findTown(); });
  E$("#ex_go").addEventListener("click", findTown);
  E$("#ex_toggle").addEventListener("click", () => E$("#ex_panel").classList.toggle("open"));
  exMap.on("moveend", () => {
    const c = exMap.getCenter();
    history.replaceState(null, "", `${location.pathname}?lat=${c.lat.toFixed(4)}&lon=${c.lng.toFixed(4)}&z=${exMap.getZoom()}${
      exTrade ? `&trade=${encodeURIComponent(exTrade)}` : ""}`);
  });
}

// A trade (roadmap C9): the places and buildings of one trade story (bidb/trade_stories.py), ringed, from the panel's
// select or `?trade=<id>`; kept in the address as the map moves
const tradeLayer = L.layerGroup().addTo(exMap);
let exTrade = new URLSearchParams(location.search).get("trade") || "";
async function showTrade(id, fit = true) {
  exTrade = id;
  tradeLayer.clearLayers();
  E$("#ex_trade_note").innerHTML = "";
  if (!id) return;
  const s = await api("/api/trade/" + encodeURIComponent(id)).catch(() => null);
  if (!s) return;
  const pts = [];
  s.places.concat(s.buildings).forEach((r) => {
    pts.push([r.lat, r.lon]);
    L.circleMarker([r.lat, r.lon], { radius: 7, weight: 2.5, color: cssVar("--accent"), fillColor: r.kind_group
      ? placeColor(r.kind_group) : groupColor(r.category_group), fillOpacity: 0.85 })
      .bindPopup(`<b>${esc(r.name)}</b><br>${esc(r.kind_label || r.category || "")}${r.date_text ? " · " + esc(r.date_text) : ""}<br>
        <a href="${r.kind_group ? "#" : buildingUrl(r.id)}" ${r.kind_group ? "data-place" : "data-open"}="${esc(r.id)}">Open</a>`)
      .addTo(tradeLayer);
  });
  E$("#ex_trade_note").innerHTML = `${pts.length.toLocaleString()} places and buildings of the trade, ringed.
    <a href="${IS_STATIC ? "trades.html" : "/trades"}?t=${encodeURIComponent(id)}">The story of ${esc(s.title.toLowerCase())}</a>`;
  if (fit && pts.length) exMap.fitBounds(pts, { padding: [30, 30], maxZoom: 10 });
}
async function wireTrades() {
  const list = await api("/api/trades").catch(() => []);
  E$("#ex_trade").innerHTML += list.map((t) => `<option value="${esc(t.id)}">${esc(t.title)}</option>`).join("");
  E$("#ex_trade").value = exTrade;
  E$("#ex_trade").addEventListener("change", (e) => showTrade(e.target.value));
  if (exTrade) showTrade(exTrade, !new URLSearchParams(location.search).get("lat"));
}

// Arriving from "Show on the map": ring and name at the record, its places layer switched on
let exMark = [];
function markFromUrl(search = location.search) {
  const p = new URLSearchParams(search);
  exMark.forEach((l) => l.remove());
  exMark = [];
  const lat = parseFloat(p.get("lat")), lon = parseFloat(p.get("lon")), name = p.get("mark");
  if (name !== null && !isNaN(lat) && !isNaN(lon)) {
    exMark.push(L.circleMarker([lat, lon], { radius: 16, weight: 3, color: cssVar("--accent"), fill: false,
                                             interactive: false, className: "map-mark",
                                             renderer: L.svg() }).addTo(exMap));     // SVG so the pulse can animate
    if (name) exMark.push(L.tooltip({ permanent: true, direction: "top", offset: [0, -14], className: "map-mark-label" })
      .setLatLng([lat, lon]).setContent(esc(name)).addTo(exMap));
  }
  const group = p.get("places");
  if (group && PLACE_GROUPS.includes(group)) {
    exState.places.add(group);
    const box = [...document.querySelectorAll("#ex_places input")].find((i) => i.value === group);
    if (box) box.checked = true;
    drawPlaces();
  }
}

// "Change over time" graphs (change_panel.js), opened from the map's button; the catalogue's own series is
// the dated buildings and places on the map, counted by the century they were begun in
function catalogueSeries() {
  const n = {};
  exBuildings.concat(exPlaces).forEach((r) => {
    if (r.year_start == null || r.year_start < -4000) return;
    const c = Math.floor(r.year_start / 100) * 100;
    n[c] = (n[c] || 0) + 1;
  });
  const now = new Date().getFullYear();
  const points = [];
  for (let c = -4000; c <= now; c += 100) points.push([Math.min(c + 50, now), n[c] || 0]);
  // how many were standing at each date: begun by then and not yet closed (the year slider's rule)
  const dated = exBuildings.concat(exPlaces).filter((r) => r.year_start != null);
  const steps = [];
  for (let y = -4000; y < 1500; y += 100) steps.push(y);
  for (let y = 1500; y <= now; y += 25) steps.push(y);
  const starts = dated.map((r) => r.year_start).sort((a, b) => a - b);
  const ends = dated.map((r) => TimeSlider.endOf(r)).filter((e) => e != null).sort((a, b) => a - b);
  let i = 0, j = 0;
  const total = steps.map((y) => {                      // begun by y, minus closed by y (one sweep over sorted years)
    while (i < starts.length && starts[i] <= y) i++;
    while (j < ends.length && ends[j] <= y) j++;
    return [y, i - j];
  });
  return [{ id: "catalogue_begun", theme: "This catalogue", title: "Buildings and places on the map, begun per century",
            unit: "per century", default: true, sources: [], points,
            note: "Counted from the dated records shown on the map (their start year). Only what survives or was " +
                  "recorded: far more was built than this, above all before 1500, so early centuries look emptier than they were." },
          { id: "catalogue_standing", theme: "This catalogue", title: "Buildings and places on the map, standing at each date",
            unit: "standing", default: true, sources: [], points: total,
            note: "Running total of the dated records shown on the map that had been begun by each date and not yet closed " +
                  "(where a closing year is known). A sample of what survives or was recorded, not the whole: compare " +
                  "the estimated number of homes in England." }];
}
function wireChange() {
  const panel = E$("#ex_change"), btn = E$("#ex_graphs");
  const show = (v) => {
    panel.hidden = !v;
    btn.hidden = v;
    try { localStorage.setItem("bidb_change_panel", v ? "shown" : "hidden"); } catch (e) { /* private mode */ }
    if (v && !exChange) exChange = ChangePanel.mount(panel, { local: catalogueSeries, year: exState.year, map: exMap, onClose: () => show(false) });
    else exChange?.pause(!v);
  };
  btn.addEventListener("click", () => show(true));
  let saved = null;
  try { saved = localStorage.getItem("bidb_change_panel"); } catch (e) { /* private mode */ }
  if (saved === "shown") show(true);
}

startView();
addBaseLayer(exMap, { control: true });
exMap.addLayer(bCluster);
exMap.addLayer(pCluster);
attachOutlines(exMap);
wireExplore();
exTime = TimeSlider.mount(E$("#ex_time"), {
  onChange: (y) => { exState.year = y; drawBuildings(); renderPlaces(); exChange?.setYear(y); },
  counts: () => exBuildings.filter((b) => exState.groups.has(b.category_group || "Other")).map((b) => b.year_start)
    .concat(exPlaces.map((p) => p.year_start)),
});
wireChange();
loadBuildings();
markFromUrl();
{ const y = parseInt(new URLSearchParams(location.search).get("year"), 10); if (!Number.isNaN(y)) exTime.setYear(y); }
wireTrades();

// Building links inside a detail view open in this page's modal
window.openDetail = showBuilding;
document.addEventListener("click", (e) => {
  const show = e.target.closest("[data-showmap]");
  if (show) {                                 // already on the map: close the record and go there
    e.preventDefault();
    const q = show.getAttribute("href").split("?")[1] || "", p = new URLSearchParams(q);
    document.getElementById("modal-close")?.click();
    exMap.setView([+p.get("lat"), +p.get("lon")], +p.get("z") || 17);
    markFromUrl("?" + q);
    return;
  }
  const a = e.target.closest("[data-open]");
  if (!a) return;
  e.preventDefault();
  showBuilding(a.dataset.open);
});
