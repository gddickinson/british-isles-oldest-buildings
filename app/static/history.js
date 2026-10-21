// History page: period bands, buildings-per-period chart, filterable event timeline.
const fmtYear = (y) => (y < 0 ? `${(-y).toLocaleString()} BC` : y <= 1000 ? `AD ${y}` : String(y));
let H = null, VER = {};

function catalogueLink(period) {
  if (!period) return "";
  const href = (IS_STATIC ? "index.html" : "/") + "?period=" + encodeURIComponent(period);
  return `<a class="btn small ghost" href="${href}">See ${esc(period)} buildings in the catalogue</a>`;
}

function renderBands() {
  const box = document.getElementById("h_bands");
  box.innerHTML = H.periods.map((p, i) => `<a href="#period-${esc(p.id)}" class="band"
      style="--band:${i % 2 ? "var(--accent-soft)" : "var(--band-alt)"}">
      <b>${esc(p.name)}</b><span>${fmtYear(p.start)} – ${p.end >= 2000 ? "today" : fmtYear(p.end)}</span></a>`).join("");
}

async function renderChart() {
  const facets = await api("/api/facets").catch(() => null);
  if (!facets) return;
  const counts = Object.fromEntries(facets.period);
  const rows = PERIODS.filter((p) => counts[p]).map((p) => [p, counts[p]]);
  hBars(document.getElementById("h_chart"), rows, {
    color: cssVar("--series-1"),
    onClick: (p) => { location.href = (IS_STATIC ? "index.html" : "/") + "?period=" + encodeURIComponent(p); },
  });
}

function eventMatches(ev, q, region, kind) {
  if (region && ev.region !== region) return false;
  if (kind && ev.kind !== kind) return false;
  if (q && !(`${ev.title} ${ev.description}`.toLowerCase().includes(q))) return false;
  return true;
}

function renderPeriods() {
  const q = document.getElementById("ev_q").value.trim().toLowerCase();
  const region = document.getElementById("ev_region").value;
  const kind = document.getElementById("ev_kind").value;
  let shown = 0;
  document.getElementById("h_periods").innerHTML = H.periods.map((p) => {
    const evs = H.events.filter((e) => e.year >= p.start && e.year < Math.max(p.end, p.start + 1)
                                       && eventMatches(e, q, region, kind));
    shown += evs.length;
    return `<section class="period" id="period-${esc(p.id)}">
      <h3>${esc(p.name)} <span class="hint">${fmtYear(p.start)} – ${p.end >= 2000 ? "today" : fmtYear(p.end)}</span></h3>
      <div class="period-grid">
        <div class="prose">${p.summary.split(/\n+/).map((t) => `<p>${esc(t)}</p>`).join("")}
          <h4>What was built</h4><p>${esc(p.architecture)}</p>${catalogueLink(p.catalogue_period)}</div>
        <ol class="events">${evs.map((e) => `<li class="ev kind-${esc(e.kind)}" id="${esc(e.place_id || "")}">
          <span class="ev-date">${esc(e.date_text)}</span>
          <div><b>${esc(e.title)}</b> <span class="tag-pill">${esc(e.region)}</span> <span class="tag-pill">${esc(e.kind)}</span>
          ${e.lat != null ? `<a href="#" class="ev-map" data-map="${esc(e.place_id)}">📍 ${esc(e.place)}</a>` : ""}
          <p>${esc(e.description)}${e.source ? ` <a href="${esc(e.source)}" target="_blank" rel="noopener">source</a>` : ""}
          ${verifyMark(e.title)}</p></div>
          </li>`).join("") || '<li class="hint">No events match the filters.</li>'}</ol>
      </div></section>`;
  }).join("");
  document.getElementById("ev_count").textContent = `${shown} of ${H.events.length} events`;
}

function verifyMark(title) {
  const v = VER[title];
  if (!v) return "";
  return v.status === "confirmed"
    ? `<span class="verify-ok" title="${esc(v.evidence || "")}">✓ year confirmed in source</span>`
    : `<span class="verify-bad">${v.status === "unreachable" ? "source unreachable" : "year not found in source, check"}</span>`;
}

async function init() {
  H = await api("/api/history");
  VER = ((await api("/api/verification").catch(() => ({}))) || {}).events || {};
  document.getElementById("h_title").textContent = H.title;
  document.getElementById("h_intro").innerHTML = H.intro.split(/\n\n+/).map((t) => `<p>${esc(t)}</p>`).join("");
  const opts = (key) => [...new Set(H.events.map((e) => e[key]))].sort();
  opts("region").forEach((r) => document.getElementById("ev_region").insertAdjacentHTML("beforeend", `<option>${esc(r)}</option>`));
  opts("kind").forEach((k) => document.getElementById("ev_kind").insertAdjacentHTML("beforeend", `<option>${esc(k)}</option>`));
  ["ev_q", "ev_region", "ev_kind"].forEach((id) => document.getElementById(id).addEventListener("input", renderPeriods));
  renderBands();
  renderPeriods();
  renderChart();
  renderMap();
}

// Map of located events; colour follows the period (ordinal ramp, earliest lightest)
const markers = {};
let hMap = null;
function renderMap() {
  const el = document.getElementById("h_map");
  const evs = H.events.filter((e) => e.lat != null);
  if (!el || !evs.length || typeof L === "undefined") return;
  hMap = L.map(el, { scrollWheelZoom: false, maxZoom: 18 }).setView([54.3, -4.5], 5);
  addBaseLayer(hMap, { control: true });
  evs.forEach((e) => {
    const per = H.periods.find((p) => e.year >= p.start && e.year < Math.max(p.end, p.start + 1));
    const m = L.circleMarker([e.lat, e.lon], { radius: 7, weight: 2, color: cssVar("--surface"), fillOpacity: 1,
      fillColor: periodColor(per && per.catalogue_period) }).addTo(hMap);
    m.bindTooltip(`${esc(e.date_text)}: ${esc(e.title)}`);
    m.on("click", () => { const li = document.getElementById(e.place_id); if (li) { li.scrollIntoView({ behavior: "smooth", block: "center" }); li.classList.add("flash"); setTimeout(() => li.classList.remove("flash"), 1600); } });
    markers[e.place_id] = m;
  });
  hMap.setView([54.4, -4.8], window.innerWidth < 700 ? 5 : 6);
  document.addEventListener("click", (ev) => {
    const a = ev.target.closest("[data-map]");
    if (!a) return;
    ev.preventDefault();
    const m = markers[a.dataset.map];
    if (!m) return;
    document.getElementById("h_map").scrollIntoView({ behavior: "smooth", block: "center" });
    hMap.setView(m.getLatLng(), 9);
    m.openTooltip();
  });
}
init();
