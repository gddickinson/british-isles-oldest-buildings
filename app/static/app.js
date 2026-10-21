// Catalogue page: URL-backed filter state, gallery/table/map/timeline views, near-me search, modal.
const $ = (sel) => document.querySelector(sel);
const PAGE = +Prefs.get("pageSize") || 48;      // Settings: results per page
const S = Object.assign({ view: Prefs.get("defaultView"), sort: Prefs.get("defaultSort"), color_by: "group", bucket: "100" },
                        readUrlState());
let offset = 0, total = 0, debounceTimer = null;

// ---- controls <-> state -----------------------------------------------------------
const TEXT_INPUTS = ["q", "year_min", "year_max", "story"];
const CHECKS = ["has_image", "curated", "oldest_only", "buildings_only", "edited", "map_area",
                "landmarks_only", "early_only"];

function pushControlsToUI() {
  TEXT_INPUTS.forEach((k) => { if ($("#" + k)) $("#" + k).value = S[k] || ""; });
  CHECKS.forEach((k) => { if ($("#" + k)) $("#" + k).checked = !!S[k]; });
  $("#sort").value = S.sort; $("#color_by").value = S.color_by; $("#bucket").value = S.bucket;
  if (S.radius !== undefined) $("#radius").value = S.radius || "";
  if (S.near_label) $("#near_status").textContent = `Near ${S.near_label}`;
}

function pullControlsFromUI() {
  TEXT_INPUTS.forEach((k) => { S[k] = $("#" + k).value.trim(); });
  CHECKS.forEach((k) => { if ($("#" + k)) S[k] = $("#" + k).checked; });
  S.sort = $("#sort").value; S.color_by = $("#color_by").value; S.bucket = $("#bucket").value;
  S.radius = S.lat ? $("#radius").value : "";
}

const apiParams = (extra = {}) => {
  const p = stateToParams(S, { forApi: true });
  Object.entries(extra).forEach(([k, v]) => p.set(k, v));
  return p;
};

// ---- loading ----------------------------------------------------------------------
async function loadFacets() {
  const counts = await api("/api/facets?" + apiParams());
  document.querySelectorAll(".facet-list").forEach((box) => {
    const col = box.dataset.facet, chosen = new Set(S.facets[col] || []);
    box.innerHTML = (counts[col] || []).map(([v, n]) => `
      <label class="check facet-item"><input type="checkbox" value="${esc(v)}" ${chosen.has(v) ? "checked" : ""}>
      ${col === "category_group" ? `<span class="dot" style="background:${groupColor(v)}"></span>` : ""}
      <span>${esc(v)}</span><em>${n}</em></label>`).join("") || "<div class='hint'>No values</div>";
  });
}

async function loadResults(append = false) {
  if (!append) offset = 0;
  const data = await api("/api/search?" + apiParams({ limit: PAGE, offset }));
  total = data.total;
  $("#total").textContent = total.toLocaleString();
  const cards = data.rows.map(cardHTML).join(""), rows = data.rows.map(rowHTML).join("");
  if (append) {
    $("#cards").insertAdjacentHTML("beforeend", cards);
    $("#rows").insertAdjacentHTML("beforeend", rows);
  } else {
    $("#cards").innerHTML = cards || "<p class='empty'>No buildings match these filters.</p>";
    $("#rows").innerHTML = rows;
  }
  offset += data.rows.length;
  $("#pager").classList.toggle("hidden", offset >= total || ["map", "timeline"].includes(S.view));
  $("#export").href = IS_STATIC ? "#" : "/export.csv?" + apiParams();
}

async function loadMap() {
  MapView.init("map", (bbox) => {
    S.bbox = bbox;
    writeUrlState(S);
    if (S.map_area) { loadFacets(); loadResults(); }
  });
  const p = apiParams();
  p.delete("bbox");                        // the map always shows everything matching
  MapView.setPoints(await api("/api/map?" + p), S.color_by);
  MapView.initOverlay($("#overlay"));
}

async function loadTimeline() {
  const size = parseInt(S.bucket, 10);
  const p = apiParams({ bucket: size });
  p.delete("year_min"); p.delete("year_max");
  const data = await api("/api/timeline?" + p);
  const rows = data.rows.map((r) => ({ start: r.start, label: bucketLabel(r.start, size), counts: r.counts }));
  stackedBars($("#timeline"), {
    rows, series: data.groups, color: groupColor,
    onClick: (r) => { S.year_min = String(r.start); S.year_max = String(r.start + size - 1); pushControlsToUI(); setView("gallery"); refresh(); },
  });
  $("#timeline_table").innerHTML = tableHTML(["Period", "Total", ...data.groups],
    rows.map((r) => [r.label, data.groups.reduce((a, g) => a + (r.counts[g] || 0), 0), ...data.groups.map((g) => r.counts[g] || 0)]));
}

function refresh() {
  writeUrlState(S);
  loadFacets();
  loadResults();
  if (S.view === "map") loadMap();
  if (S.view === "timeline") loadTimeline();
}
const refreshSoon = () => { clearTimeout(debounceTimer); debounceTimer = setTimeout(() => { pullControlsFromUI(); refresh(); }, 250); };

function setView(view) {
  S.view = view;
  document.querySelectorAll(".tab").forEach((t) => t.classList.toggle("active", t.dataset.view === view));
  document.querySelectorAll(".view").forEach((v) => v.classList.toggle("hidden", v.id !== "view-" + view));
  $("#pager").classList.toggle("hidden", ["map", "timeline"].includes(view) || offset >= total);
  writeUrlState(S);
  if (view === "map") loadMap();
  if (view === "timeline") loadTimeline();
}

// ---- near a place / near me --------------------------------------------------------
function setNear(lat, lon, label) {
  Object.assign(S, { lat: lat.toFixed(5), lon: lon.toFixed(5), near_label: label, sort: "distance",
                     radius: $("#radius").value });
  $("#sort").value = "distance";
  $("#near_status").innerHTML = `Near ${esc(label)} · <a href="#" id="near_clear">clear</a>`;
  if (S.view === "map") MapView.flyTo(lat, lon);
  refresh();
}

async function nearSearch() {
  const q = $("#near_q").value.trim();
  if (!q) return;
  $("#near_status").textContent = "Searching…";
  const hits = await api("/api/geocode?q=" + encodeURIComponent(q)).catch(() => []);
  if (!hits.length) { $("#near_status").textContent = "Place not found"; return; }
  setNear(hits[0].lat, hits[0].lon, hits[0].name.split(",").slice(0, 2).join(","));
}

function nearMe() {
  if (!navigator.geolocation) { $("#near_status").textContent = "Location not available"; return; }
  $("#near_status").textContent = "Finding your location…";
  navigator.geolocation.getCurrentPosition(
    (pos) => setNear(pos.coords.latitude, pos.coords.longitude, "your location"),
    () => { $("#near_status").textContent = "Location permission denied"; });
}

// ---- modal --------------------------------------------------------------------------
async function openDetail(id) {
  const b = await api("/api/building/" + encodeURIComponent(id));
  showDetail(b, $("#modal-body"), true);
  $("#modal").classList.remove("hidden");
  $("#modal").setAttribute("aria-hidden", "false");
  document.body.classList.add("noscroll");
  dialogOpened($("#modal"));
  history.replaceState(null, "", location.pathname + location.search + "#" + encodeURIComponent(id));
}

function closeDetail() {
  $("#modal").classList.add("hidden");
  $("#modal").setAttribute("aria-hidden", "true");
  document.body.classList.remove("noscroll");
  dialogClosed();
  history.replaceState(null, "", location.pathname + location.search);
}

// ---- wiring -------------------------------------------------------------------------
function wire() {
  TEXT_INPUTS.forEach((k) => $("#" + k).addEventListener("input", refreshSoon));
  CHECKS.concat(["sort", "color_by", "bucket", "radius"]).forEach((k) => {
    if ($("#" + k)) $("#" + k).addEventListener("change", () => { pullControlsFromUI(); if (k === "map_area" && S.map_area && MapView.map) S.bbox = MapView.bboxString(); refresh(); });
  });
  $("#sidebar").addEventListener("change", (e) => {
    const box = e.target.closest(".facet-list");
    if (!box) return;
    S.facets[box.dataset.facet] = [...box.querySelectorAll("input:checked")].map((i) => i.value);
    refresh();
  });
  document.querySelectorAll(".tab").forEach((t) => t.addEventListener("click", () => setView(t.dataset.view)));
  $("#more").addEventListener("click", () => loadResults(true));
  $("#near_go").addEventListener("click", nearSearch);
  $("#near_q").addEventListener("keydown", (e) => { if (e.key === "Enter") nearSearch(); });
  $("#near_me").addEventListener("click", nearMe);
  $("#tl_table").addEventListener("click", () => {
    const hidden = $("#timeline_table").classList.toggle("hidden");
    $("#tl_table").textContent = hidden ? "Show as table" : "Hide table";
  });
  $("#copy_link").addEventListener("click", async () => {
    try { await navigator.clipboard.writeText(location.href); $("#copy_link").textContent = "Link copied"; }
    catch (e) { prompt("Copy this link", location.href); }
    setTimeout(() => { $("#copy_link").textContent = "Copy link"; }, 1500);
  });
  $("#reset").addEventListener("click", () => {
    Object.keys(S).forEach((k) => { if (!["view", "color_by", "bucket"].includes(k)) delete S[k]; });
    Object.assign(S, { facets: {}, sort: "oldest" });
    $("#near_status").textContent = ""; $("#near_q").value = "";
    pushControlsToUI();
    refresh();
  });
  $("#toggle-filters").addEventListener("click", () => $("#sidebar").classList.toggle("open"));
  document.addEventListener("click", (e) => {
    if (e.target.id === "near_clear") {
      e.preventDefault();
      ["lat", "lon", "near_label", "radius"].forEach((k) => delete S[k]);
      S.sort = "oldest"; $("#near_status").textContent = ""; pushControlsToUI(); refresh(); return;
    }
    const opener = e.target.closest("[data-open]");
    if (opener) { e.preventDefault(); openDetail(opener.dataset.open); return; }
    const item = e.target.closest(".card, tr[data-id]");
    if (item && !e.target.closest(".modal") && !e.target.closest("a.ext")) { e.preventDefault(); openDetail(item.dataset.id); }
  });
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") closeDetail();
    if (e.key === "Enter" && e.target.classList.contains("card")) openDetail(e.target.dataset.id);
  });
  $("#modal-close").addEventListener("click", closeDetail);
  $("#modal").addEventListener("click", (e) => { if (e.target.id === "modal") closeDetail(); });
}

S.facets = S.facets || {};
if (IS_STATIC) {                 // features the hosted sandbox blocks
  ["#near_me", "#copy_link", "#export"].forEach((sel) => { const el = $(sel); if (el) el.hidden = true; });
  $("#near_q").placeholder = "Near a place in the catalogue…";
}
pushControlsToUI();
wire();
setView(S.view);
refresh();
window.addEventListener("thumbs-loaded", () => { if (["gallery", "table"].includes(S.view)) loadResults(); });
if (location.hash.length > 1) openDetail(decodeURIComponent(location.hash.slice(1)));
