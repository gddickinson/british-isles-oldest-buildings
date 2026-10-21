// Places page: filters (URL-backed), list and map of places of interest, detail modal.
const P$ = (sel) => document.querySelector(sel);
const P_FACETS = ["kind_group", "kind_label", "nation", "period", "source"];
const PS = { view: "list", sort: "oldest", facets: {} };
let pOffset = 0, pTotal = 0, pTimer = null, pMap = null, pCluster = null;

function readPlaceState() {
  const p = new URLSearchParams(location.search);
  ["q", "year_min", "year_max", "sort", "view"].forEach((k) => { if (p.get(k)) PS[k] = p.get(k); });
  PS.has_image = p.get("has_image") === "1";
  P_FACETS.forEach((k) => { const v = p.getAll(k); if (v.length) PS.facets[k] = v; });
}

function placeParams(extra = {}, forUrl = false) {
  const p = new URLSearchParams();
  ["q", "year_min", "year_max", "sort"].forEach((k) => { if (PS[k]) p.set(k, PS[k]); });
  if (forUrl && PS.view !== "list") p.set("view", PS.view);
  if (PS.has_image) p.set("has_image", "1");
  Object.entries(PS.facets).forEach(([k, vals]) => vals.forEach((v) => p.append(k, v)));
  Object.entries(extra).forEach(([k, v]) => p.set(k, v));
  return p;
}

async function loadPlaceFacets() {
  const counts = await api("/api/places/facets?" + placeParams());
  document.querySelectorAll(".facet-list").forEach((box) => {
    const col = box.dataset.facet, chosen = new Set(PS.facets[col] || []);
    box.innerHTML = (counts[col] || []).map(([v, n]) => `<label class="check facet-item">
      <input type="checkbox" value="${esc(v)}" ${chosen.has(v) ? "checked" : ""}>
      ${col === "kind_group" ? `<span class="dot" style="background:${placeColor(v)}"></span>` : ""}
      <span>${esc(v)}</span><em>${n.toLocaleString()}</em></label>`).join("") || "<div class='hint'>No values</div>";
  });
}

async function loadPlaces(append = false) {
  if (!append) pOffset = 0;
  const data = await api("/api/places?" + placeParams({ limit: 48, offset: pOffset }));
  pTotal = data.total;
  P$("#total").textContent = pTotal.toLocaleString();
  const html = data.rows.map(placeCardHTML).join("");
  if (append) P$("#cards").insertAdjacentHTML("beforeend", html);
  else P$("#cards").innerHTML = html || "<p class='empty'>No places match these filters.</p>";
  pOffset += data.rows.length;
  P$("#pager").classList.toggle("hidden", pOffset >= pTotal || PS.view === "map");
}

async function loadPlaceMap() {
  if (!pMap) {
    pMap = L.map("map", { preferCanvas: true, maxZoom: 18 }).setView([54.3, -4.5], 6);
    addBaseLayer(pMap, { control: true });
    pCluster = L.markerClusterGroup(Prefs.cluster({ chunkedLoading: true, maxClusterRadius: 45, disableClusteringAtZoom: 13 }));
    pMap.addLayer(pCluster);
  }
  const pts = await api("/api/places/map?" + placeParams());
  pCluster.clearLayers();
  const ring = cssVar("--surface");
  pCluster.addLayers(pts.map((p) => {
    const m = L.circleMarker([p.lat, p.lon], { radius: 6, weight: 2, color: ring, fillOpacity: 0.95,
                                               fillColor: placeColor(p.kind_group) });
    m.bindTooltip(esc(p.name));
    m.on("click", () => openPlace(p.id));
    return m;
  }));
  const counts = {};
  pts.forEach((p) => { counts[p.kind_group] = (counts[p.kind_group] || 0) + 1; });
  P$("#legend").innerHTML = "<b>Layer</b>" + PLACE_GROUPS.filter((g) => counts[g]).map((g) =>
    `<div><i style="background:${placeColor(g)}"></i>${esc(g)} <em>${counts[g].toLocaleString()}</em></div>`).join("");
  setTimeout(() => pMap.invalidateSize(), 50);
}

function placeRefresh() {
  history.replaceState(null, "", location.pathname + "?" + placeParams({}, true));
  loadPlaceFacets();
  loadPlaces();
  if (PS.view === "map") loadPlaceMap();
}

function setPlaceView(view) {
  PS.view = view;
  document.querySelectorAll(".tab").forEach((t) => t.classList.toggle("active", t.dataset.view === view));
  document.querySelectorAll(".view").forEach((v) => v.classList.toggle("hidden", v.id !== "view-" + view));
  P$("#pager").classList.toggle("hidden", view === "map" || pOffset >= pTotal);
  history.replaceState(null, "", location.pathname + "?" + placeParams({}, true));
  if (view === "map") loadPlaceMap();
}

function pullPlaceControls() {
  ["q", "year_min", "year_max"].forEach((k) => { PS[k] = P$("#" + k).value.trim(); });
  PS.has_image = P$("#has_image").checked;
  PS.sort = P$("#sort").value;
}

function wirePlaces() {
  ["q", "year_min", "year_max"].forEach((k) => {
    P$("#" + k).value = PS[k] || "";
    P$("#" + k).addEventListener("input", () => { clearTimeout(pTimer); pTimer = setTimeout(() => { pullPlaceControls(); placeRefresh(); }, 250); });
  });
  P$("#has_image").checked = PS.has_image;
  P$("#sort").value = PS.sort;
  ["has_image", "sort"].forEach((k) => P$("#" + k).addEventListener("change", () => { pullPlaceControls(); placeRefresh(); }));
  P$("#sidebar").addEventListener("change", (e) => {
    const box = e.target.closest(".facet-list");
    if (!box) return;
    PS.facets[box.dataset.facet] = [...box.querySelectorAll("input:checked")].map((i) => i.value);
    placeRefresh();
  });
  document.querySelectorAll(".tab").forEach((t) => t.addEventListener("click", () => setPlaceView(t.dataset.view)));
  P$("#more").addEventListener("click", () => loadPlaces(true));
  P$("#reset").addEventListener("click", () => {
    Object.assign(PS, { q: "", year_min: "", year_max: "", has_image: false, sort: "oldest", facets: {} });
    ["q", "year_min", "year_max"].forEach((k) => { P$("#" + k).value = ""; });
    P$("#has_image").checked = false;
    placeRefresh();
  });
  P$("#toggle-filters").addEventListener("click", () => P$("#sidebar").classList.toggle("open"));
  document.addEventListener("keydown", (e) => {
    if (e.key === "Enter" && e.target.dataset && e.target.dataset.place) openPlace(e.target.dataset.place);
  });
}

// read the place to open first: setPlaceView and placeRefresh rewrite the URL without its hash
const openFirst = location.hash.length > 1 ? decodeURIComponent(location.hash.slice(1)) : null;
readPlaceState();
wirePlaces();
setPlaceView(PS.view);
placeRefresh();
if (openFirst) openPlace(openFirst);
