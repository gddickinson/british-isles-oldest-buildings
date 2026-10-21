// Tours page, "Your tour" tab: stops from ☆ (bi_favourites: building or place ids), travel mode,
// best order, route, suggested tours, stops along the way, saved tours (localStorage), exports.
const TourBuilder = (() => {
  const B$ = (sel) => document.querySelector(sel);
  const OPTS = "bi_tour_opts", SAVED = "bi_saved_tours";
  const read = (k, d) => { try { return JSON.parse(localStorage.getItem(k)) ?? d; } catch (e) { return d; } };
  const write = (k, v) => { try { localStorage.setItem(k, JSON.stringify(v)); } catch (e) { /* blocked */ } };
  const KEEP = ["id", "kind", "name", "lat", "lon", "date_text", "category", "locality", "story_kinds"];
  let STOPS = [], known = {}, map = null, layer = null, candLayer = null, routeSeq = 0, last = null, started = false;

  const opts = () => Object.assign({ name: "", mode: "walk", loop: false }, read(OPTS, {}));
  const setOpts = (o) => write(OPTS, Object.assign(opts(), o));
  const located = () => STOPS.filter((s) => s.lat != null);
  const slim = (s) => Object.fromEntries(KEEP.map((k) => [k, s[k] ?? null]));

  async function resolve(ids) {
    // stops we know already, buildings in one request, places one by one
    const need = ids.filter((id) => !known[id]);
    if (need.length) {
      const bs = await api("/api/buildings?ids=" + need.map(encodeURIComponent).join(",")).catch(() => []);
      bs.forEach((b) => { known[b.id] = slim({ ...b, kind: "building" }); });
      for (const id of need.filter((i) => !known[i])) {
        const p = await api("/api/place/" + encodeURIComponent(id)).catch(() => null);
        if (p) known[id] = slim({ ...p, kind: "place", category: p.kind_label });
      }
    }
    return ids.map((id) => known[id]).filter(Boolean);
  }

  const saveIds = () => store.set(FAV, STOPS.map((s) => s.id));

  function load(t) {                                   // from a ready-made or saved tour
    t.stops.forEach((s) => { known[s.id] = slim(s); });
    STOPS = t.stops.map((s) => known[s.id]);
    setOpts({ name: t.name || "", mode: t.mode || "walk", loop: !!t.loop });
    saveIds();
    if (started) { pushOpts(); render(); }
  }

  function pushOpts() {
    const o = opts();
    B$("#tb_name").value = o.name; B$("#tb_mode").value = o.mode; B$("#tb_loop").checked = o.loop;
  }

  function render() {
    B$("#tb_list").innerHTML = STOPS.map((s, i) => `<li>
      <div><b>${i + 1}. ${esc(s.name)}</b> ${(s.story_kinds || []).map((k) => Stories.icon(k)).join("")}
        <div class="meta">${esc([s.date_text, s.category, s.locality].filter(Boolean).join(" · "))}${s.lat == null ? " · <em>no coordinates</em>" : ""}</div></div>
      <div class="row-actions"><button data-up="${i}" title="Move up">↑</button><button data-down="${i}" title="Move down">↓</button>
        <a href="#" data-story-open="${esc(s.kind || "building")}" data-id="${esc(s.id)}" title="Details">ⓘ</a>
        <button data-del="${i}" title="Remove">✕</button></div></li>`).join("")
      || "<p class='empty'>No stops yet. Use ☆ on any building or place, or ✨ Suggest a tour.</p>";
    drawRoute();
  }

  async function drawRoute() {
    if (!map) {
      map = L.map("tb_map", { maxZoom: 18 }).setView([54.3, -4.5], 6);
      addBaseLayer(map, { control: true });
      layer = L.layerGroup().addTo(map);
      candLayer = L.layerGroup().addTo(map);
    }
    const o = opts(), pts = located(), seq = ++routeSeq;
    const t = { title: o.name || "My tour", stops: pts, line: pts.map((s) => [s.lat, s.lon]), routed: false };
    TourLib.draw(map, layer, t);
    B$("#tb_gmaps").classList.toggle("disabled", pts.length < 2);
    if (pts.length < 2) { B$("#tb_total").textContent = ""; B$("#tb_elev").innerHTML = ""; last = t; return; }
    B$("#tb_total").textContent = "Routing…";
    const r = await TourLib.route(o.mode, pts, o.loop);
    if (seq !== routeSeq) return;                      // a newer change is already routing
    Object.assign(t, { line: r.line, routed: r.routed, distance_km: r.distance_km, duration_min: r.duration_min });
    B$("#tb_elev").innerHTML = TourLib.profileHTML(r.elevation);
    TourLib.draw(map, layer, t);
    last = t;
    B$("#tb_total").textContent = `${TourLib.MODES[o.mode].icon} ${pts.length} stops · ${Prefs.dist(r.distance_km, 1)} · about ${TourLib.hours(r.duration_min)}`
      + (r.routed ? "" : " (estimated: straight lines × detour)");
    B$("#tb_gmaps").href = TourLib.googleMaps(o.mode, pts, o.loop);
  }

  const savedList = () => read(SAVED, []);
  function renderSaved() {
    B$("#tb_saved").innerHTML = `<option value="">Saved tours (${savedList().length})…</option>` + savedList().map((t, i) =>
      `<option value="load:${i}">${esc(t.name)} · ${TourLib.MODES[t.mode].icon} ${t.stops.length} stops</option>`).join("")
      + (savedList().length ? `<optgroup label="Delete">${savedList().map((t, i) => `<option value="del:${i}">✕ ${esc(t.name)}</option>`).join("")}</optgroup>` : "");
  }

  // ---- suggestions -------------------------------------------------------------------
  async function candidates(lat, lon, radius, theme) {
    return api(`/api/tour_candidates?lat=${lat}&lon=${lon}&km=${radius}&theme=${theme}`).catch(() => []);
  }

  async function suggest(lat, lon, label) {
    const o = opts(), hrs = +B$("#sg_hours").value, theme = B$("#sg_theme").value;
    const want = TourLib.stopsFor(o.mode, hrs), m = TourLib.MODES[o.mode];
    B$("#sg_status").textContent = "Finding places…";
    const cands = await candidates(lat, lon, m.radius * Math.max(1, want / 8) * 1.2, theme);
    const picked = TourLib.pick(cands, { lat, lon }, o.mode, want);
    if (picked.length < 2) { B$("#sg_status").textContent = "Not enough places near there for this theme; try another theme or a longer time."; return; }
    const start = { lat, lon };
    picked.sort((a, b) => TourLib.km(start, a) - TourLib.km(start, b));
    load({ name: `${TourLib.THEMES[theme]} ${label ? "from " + label : "tour"}`, mode: o.mode, loop: o.mode !== "walk",
           stops: TourLib.order(picked, o.mode !== "walk") });
    B$("#sg_status").textContent = `${picked.length} stops chosen.`;
  }

  async function along() {                            // best places near the route that are not stops yet
    const pts = located();
    if (!pts.length) return UI.toast("Add a stop first");
    const o = opts(), m = TourLib.MODES[o.mode];
    const lat = pts.reduce((a, s) => a + s.lat, 0) / pts.length, lon = pts.reduce((a, s) => a + s.lon, 0) / pts.length;
    const span = Math.max(...pts.map((s) => TourLib.km({ lat, lon }, s)));
    const near = (c) => Math.min(...(last && last.line.length ? last.line : pts.map((s) => [s.lat, s.lon]))
      .map(([la, lo]) => TourLib.km({ lat: la, lon: lo }, c)));
    const have = new Set(STOPS.map((s) => s.id));
    const cands = (await candidates(lat, lon, Math.min(80, span + m.radius / 2), "highlights"))
      .filter((c) => !have.has(c.id) && near(c) <= m.radius / 3).slice(0, 12);
    candLayer.clearLayers();
    cands.forEach((c) => L.circleMarker([c.lat, c.lon], { radius: 7, color: cssVar("--accent"), fillOpacity: 0.3 })
      .bindPopup(`<b>${esc(c.name)}</b><br>${esc(c.date_text || "")}<br><button class="btn small" data-add-cand="${esc(c.id)}">Add to tour</button>`).addTo(candLayer));
    cands.forEach((c) => { known[c.id] = slim(c); });
    B$("#tb_cands").innerHTML = cands.length ? `<h4>Worth a detour</h4><ul class="nearby">${cands.map((c) =>
      `<li><button class="btn small ghost" data-add-cand="${esc(c.id)}">+</button> ${esc(c.name)}
        <span class="meta">${esc(c.date_text || "")} · ${Prefs.dist(near(c), 1)} off the route ${(c.story_kinds || []).map(Stories.icon).join("")}</span></li>`).join("")}</ul>`
      : "<p class='empty'>Nothing more of note close to this route.</p>";
  }

  function insertBest(stop) {                         // cheapest place to slot a new stop into the route
    const pts = STOPS;
    let best = pts.length, cost = Infinity;
    for (let i = 0; i <= pts.length; i++) {
      const a = pts[i - 1], b = pts[i];
      const c = (a ? TourLib.km(a, stop) : 0) + (b ? TourLib.km(stop, b) : 0) - (a && b ? TourLib.km(a, b) : 0);
      if (c < cost) { cost = c; best = i; }
    }
    STOPS.splice(best, 0, stop);
  }

  function bind() {
    B$("#tb_list").addEventListener("click", (e) => {
      const b = e.target.closest("button");
      if (!b) return;
      const i = +(b.dataset.up ?? b.dataset.down ?? b.dataset.del);
      if (b.dataset.up !== undefined && i > 0) [STOPS[i - 1], STOPS[i]] = [STOPS[i], STOPS[i - 1]];
      if (b.dataset.down !== undefined && i < STOPS.length - 1) [STOPS[i + 1], STOPS[i]] = [STOPS[i], STOPS[i + 1]];
      if (b.dataset.del !== undefined) STOPS.splice(i, 1);
      saveIds(); render();
    });
    document.addEventListener("click", (e) => {
      const b = e.target.closest("[data-add-cand]");
      if (!b || !known[b.dataset.addCand]) return;
      insertBest(known[b.dataset.addCand]);
      b.closest("li")?.remove();
      saveIds(); render();
    });
    B$("#tb_name").addEventListener("change", () => setOpts({ name: B$("#tb_name").value.trim() }));
    B$("#tb_mode").addEventListener("change", () => { setOpts({ mode: B$("#tb_mode").value }); drawRoute(); });
    B$("#tb_loop").addEventListener("change", () => { setOpts({ loop: B$("#tb_loop").checked }); drawRoute(); });
    B$("#tb_opt").onclick = () => { const rest = STOPS.filter((s) => s.lat == null);
      STOPS = TourLib.order(located(), opts().loop).concat(rest); saveIds(); render(); };
    B$("#tb_suggest_open").onclick = () => B$("#tb_suggest").classList.toggle("hidden");
    B$("#sg_theme").innerHTML = Object.entries(TourLib.THEMES).map(([k, v]) => `<option value="${k}">${esc(v)}</option>`).join("");
    B$("#tb_suggest").addEventListener("submit", async (e) => {
      e.preventDefault();
      const q = B$("#sg_where").value.trim();
      if (!q) return B$("#sg_status").textContent = "Type a place, or use your location or the map centre.";
      const hits = await api("/api/geocode?q=" + encodeURIComponent(q)).catch(() => []);
      if (!hits.length) return B$("#sg_status").textContent = `Could not find “${q}”.`;
      suggest(hits[0].lat, hits[0].lon, q);
    });
    B$("#sg_here").onclick = () => navigator.geolocation ? navigator.geolocation.getCurrentPosition(
      (p) => suggest(p.coords.latitude, p.coords.longitude, "here"), () => { B$("#sg_status").textContent = "Location not available."; })
      : null;
    B$("#sg_mapc").onclick = () => { const c = map.getCenter(); suggest(c.lat, c.lng, ""); };
    B$("#tb_along").onclick = along;
    B$("#tb_save").onclick = () => {
      const o = opts(), name = o.name || prompt("Name for this tour", "My tour");
      if (!name || !STOPS.length) return;
      const list = savedList().filter((t) => t.name !== name);
      list.unshift({ name, mode: o.mode, loop: o.loop, stops: STOPS.map(slim), saved: new Date().toISOString() });
      write(SAVED, list); setOpts({ name }); pushOpts(); renderSaved();
      UI.toast(`Saved “${name}”`);
    };
    B$("#tb_saved").addEventListener("change", (e) => {
      const [act, i] = e.target.value.split(":");
      const list = savedList();
      if (act === "load" && list[i]) load(list[i]);
      if (act === "del" && list[i]) { list.splice(+i, 1); write(SAVED, list); }
      e.target.value = ""; renderSaved();
    });
    const tour = () => Object.assign({ title: opts().name || "My tour" }, last || { stops: located(), line: [] });
    B$("#tb_gpx").onclick = (e) => TourLib.save(TourLib.fileName(tour(), "gpx"), "application/gpx+xml", TourLib.gpx(tour()), e.target);
    B$("#tb_kml").onclick = (e) => TourLib.save(TourLib.fileName(tour(), "kml"), "application/vnd.google-earth.kml+xml", TourLib.kml(tour()), e.target);
    B$("#tb_print").onclick = () => window.print();
    let unfollow = null;
    B$("#tb_follow").onclick = (e) => {
      if (unfollow) { unfollow(); unfollow = null; e.target.textContent = "📍 Follow"; return; }
      unfollow = TourLib.follow(map, located(), opts().mode, B$("#tb_follow_status"));
      e.target.textContent = "Stop following";
    };
    B$("#tb_share").onclick = (e) => {                // the stops travel in the link itself
      const o = opts(), u = new URL(location.href);
      u.search = new URLSearchParams({ tab: "build", mode: o.mode, loop: o.loop ? "1" : "0", name: o.name || "",
                                       stops: STOPS.map((s) => s.id).join(",") }).toString();
      u.hash = "";
      copyText(u.toString(), e.target, "Link copied");
    };
    B$("#tb_clear").onclick = () => { STOPS = []; setOpts({ name: "" }); pushOpts(); saveIds(); candLayer && candLayer.clearLayers();
      B$("#tb_cands").innerHTML = ""; render(); };
  }

  async function show() {
    if (!started) {
      started = true;
      bind();
      pushOpts();
      renderSaved();
      const url = new URLSearchParams(location.search);
      if (url.get("stops")) {                          // a shared tour replaces the current one
        store.set(FAV, url.get("stops").split(",").filter(Boolean));
        setOpts({ name: url.get("name") || "", mode: url.get("mode") || "walk", loop: url.get("loop") === "1" });
        pushOpts();
      }
      STOPS = await resolve(store.get(FAV));
      render();
    }
    setTimeout(() => map && map.invalidateSize());
  }

  return { show, load };
})();
