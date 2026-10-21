// Tours page, "Ready-made tours" tab: filter the generated tours, show one on the map with its stops
// and their stories, export it, or copy it into the builder (tour_builder.js: TourBuilder.load).
const T$ = (sel) => document.querySelector(sel);
let trMode = "", trTimer = null, trMap = null, trLayer = null, trCurrent = null, unfollow = null;

function tourCard(t) {
  const m = TourLib.MODES[t.mode];
  return `<button type="button" class="tour-card ${trCurrent && trCurrent.id === t.id ? "on" : ""}" data-tour="${esc(t.id)}">
    <span class="tour-icon">${m.icon}</span>
    <span><b>${esc(t.title)}</b><span class="meta">${esc(TourLib.THEMES[t.theme] || t.theme)} · ${Prefs.dist(t.distance_km, 1)} ·
      ${t.stages ? `${t.stages.length} day${t.stages.length > 1 ? "s" : ""}` : TourLib.hours(t.duration_min)} · ${t.stops.length} stops${t.elevation ? " · " + esc(t.elevation.hilly) : ""}</span></span></button>`;
}

async function loadTours() {
  const p = new URLSearchParams(Object.entries({ mode: trMode, theme: T$("#tr_theme").value, nation: T$("#tr_nation").value,
    q: T$("#tr_q").value.trim() }).filter(([, v]) => v));
  const rows = await api("/api/tours?" + p).catch(() => []);
  T$("#tr_count").textContent = `${rows.length} tours`;
  T$("#tr_list").innerHTML = rows.map(tourCard).join("") || "<p class='empty'>No tours match.</p>";
  history.replaceState(null, "", location.pathname + (p.toString() ? "?" + p : "") + location.hash);
}

function stopHTML(s, i) {
  const tales = (s.story_kinds || []).map((k) => `<span title="${esc(Stories.label(k))}">${Stories.icon(k)}</span>`).join("");
  return `<li><b>${i + 1}. <a href="#" data-story-open="${esc(s.kind)}" data-id="${esc(s.id)}">${esc(s.name)}</a></b> ${tales}
    <div class="meta">${esc([s.date_text, s.category, s.locality].filter(Boolean).join(" · "))}</div>
    ${(s.story_kinds || []).length ? `<div class="stop-story" data-stop-story="${esc(s.id)}"></div>` : ""}</li>`;
}

async function showTour(id) {
  const t = await api("/api/tour/" + encodeURIComponent(id));
  t.line = t.geometry ? TourLib.decode(t.geometry) : t.stops.concat(TourLib.MODES[t.mode].loop ? [t.stops[0]] : []).map((s) => [s.lat, s.lon]);
  t.routed = !!t.routed;
  trCurrent = t;
  document.querySelectorAll("[data-tour]").forEach((b) => b.classList.toggle("on", b.dataset.tour === id));
  if (!trMap) {
    trMap = L.map("tr_map", { maxZoom: 18 }).setView([54.3, -4.5], 5);
    addBaseLayer(trMap, { control: true });
    trLayer = L.layerGroup().addTo(trMap);
  }
  TourLib.draw(trMap, trLayer, t);
  const loop = TourLib.MODES[t.mode].loop;
  T$("#tr_detail").innerHTML = `<h2>${TourLib.MODES[t.mode].icon} ${esc(t.title)}</h2>
    <p>${esc(t.summary)}</p>
    <p class="hint">${t.routed ? "Route along paths and roads from OpenStreetMap (OSRM, routing.openstreetmap.de)." : "Straight lines between stops; distance estimated."}
      ${t.stages ? "Waymarked long-distance route: follow the signs; stops are sights within 1.5 km of the path." : loop ? "A round trip." : "One way: start at stop 1."}</p>
    <div class="filter-row">
      <a class="btn small" target="_blank" rel="noopener" href="${esc(TourLib.googleMaps(t.mode, t.stops, loop))}">Directions in Google Maps</a>
      <button class="btn small ghost" id="tr_gpx">GPX</button><button class="btn small ghost" id="tr_kml">KML</button>
      <button class="btn small ghost" id="tr_print">Print</button>
      <button class="btn small ghost" id="tr_copy">Copy to Your tour</button>
      ${Stories.canSpeak() ? '<button class="btn small ghost" id="tr_listen">🔊 Listen to the tour</button>' : ""}
      <button class="btn small ghost" id="tr_follow">📍 Follow</button>
    </div>
    <div id="tr_follow_status" class="follow-status" aria-live="polite"></div><div>
    </div>
    ${TourLib.profileHTML(t.elevation)}
    ${t.stages ? `<details class="stages" open><summary><b>Day by day</b> (about ${Prefs.dist(t.distance_km / t.stages.length, 0)} a day)</summary><ol>${t.stages.map((d) =>
      `<li><b>Day ${d.day}</b> <span class="hint">${Prefs.dist(d.from_km, 0)}–${Prefs.dist(d.to_km, 0)}</span>${d.stops.length ? ": " + d.stops.map(esc).join(", ") : ""}</li>`).join("")}</ol></details>` : ""}
    <p class="getting-there" data-transport="${t.stops[0].lat},${t.stops[0].lon}"></p>
    <ol class="tour-stops">${t.stops.map(stopHTML).join("")}</ol>`;
  T$("#tr_gpx").onclick = (e) => TourLib.save(TourLib.fileName(t, "gpx"), "application/gpx+xml", TourLib.gpx(t), e.target);
  T$("#tr_kml").onclick = (e) => TourLib.save(TourLib.fileName(t, "kml"), "application/vnd.google-earth.kml+xml", TourLib.kml(t), e.target);
  T$("#tr_print").onclick = () => window.print();
  if (T$("#tr_listen")) T$("#tr_listen").onclick = () => listenTour(t);
  if (unfollow) unfollow();
  unfollow = null;
  T$("#tr_follow").onclick = (e) => {
    if (unfollow) { unfollow(); unfollow = null; e.target.textContent = "📍 Follow"; return; }
    unfollow = TourLib.follow(trMap, t.stops, t.mode, T$("#tr_follow_status"));
    e.target.textContent = "Stop following";
  };
  T$("#tr_copy").onclick = () => { TourBuilder.load({ name: t.title, mode: t.mode, loop, stops: t.stops }); switchTab("build"); };
  history.replaceState(null, "", location.pathname + location.search + "#tour=" + encodeURIComponent(id));
  document.querySelectorAll("[data-stop-story]").forEach(async (el) => {
    const rows = await Stories.forRecord(el.dataset.stopStory).catch(() => []);
    if (rows[0]) el.innerHTML = `<p>${Stories.icon(rows[0].kind)} ${esc(rows[0].text.length > 260 ? rows[0].text.slice(0, 260).replace(/\s+\S*$/, "") + " …" : rows[0].text)}</p>`;
  });
}

// Audio tour: the title and summary, then each stop with its date and first story
async function listenTour(t) {
  if (speechSynthesis.speaking) { Stories.stop(); return; }
  const parts = [`${t.title}. ${t.summary}`];
  for (const [i, s] of t.stops.entries()) {
    const tales = (s.story_kinds || []).length ? await Stories.forRecord(s.id).catch(() => []) : [];
    parts.push(`Stop ${i + 1}: ${s.name}${s.date_text ? ", " + s.date_text : ""}.` + (tales[0] ? " " + tales[0].text : ""));
  }
  Stories.speak(parts);
}

function switchTab(name) {
  document.querySelectorAll(".tour-tabs .tab").forEach((b) => b.classList.toggle("active", b.dataset.tab === name));
  document.querySelectorAll(".tour-tab").forEach((s) => s.classList.toggle("hidden", s.id !== "tab-" + name));
  if (name === "build") TourBuilder.show();
  else if (trMap) setTimeout(() => trMap.invalidateSize());
}

async function initTours() {
  const url = new URLSearchParams(location.search);
  T$("#tr_theme").innerHTML += Object.entries(TourLib.THEMES).map(([k, v]) => `<option value="${k}">${esc(v)}</option>`).join("");
  T$("#tr_theme").value = url.get("theme") || "";
  T$("#tr_nation").value = url.get("nation") || "";
  T$("#tr_q").value = url.get("q") || "";
  trMode = url.get("mode") || "";
  T$("#tr_modes").querySelectorAll("button").forEach((b) => b.classList.toggle("on", b.dataset.m === trMode));
  T$("#tr_modes").addEventListener("click", (e) => {
    const b = e.target.closest("button[data-m]");
    if (!b) return;
    trMode = b.dataset.m;
    T$("#tr_modes").querySelectorAll("button").forEach((x) => x.classList.toggle("on", x === b));
    loadTours();
  });
  ["#tr_theme", "#tr_nation"].forEach((s) => T$(s).addEventListener("change", loadTours));
  T$("#tr_q").addEventListener("input", () => { clearTimeout(trTimer); trTimer = setTimeout(loadTours, 250); });
  T$("#tr_list").addEventListener("click", (e) => { const b = e.target.closest("[data-tour]"); if (b) showTour(b.dataset.tour); });
  document.querySelectorAll(".tour-tabs .tab").forEach((b) => b.addEventListener("click", () => switchTab(b.dataset.tab)));
  await loadTours();
  if (location.hash.startsWith("#tour=")) showTour(decodeURIComponent(location.hash.slice(6)));
  else if (location.hash === "#build" || location.pathname.endsWith("/trip") || url.get("tab") === "build") switchTab("build");
  else { const first = document.querySelector("[data-tour]"); if (first) showTour(first.dataset.tour); }
}
document.addEventListener("DOMContentLoaded", initTours);
