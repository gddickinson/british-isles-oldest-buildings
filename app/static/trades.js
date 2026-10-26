// Trades page (roadmap C8): one story per trade from /api/trades and /api/trade/<id> (bidb.trade_stories): intro,
// timeline of events and innovations, places and buildings on a map, people, graphs of Change over time, cited notes.
(async () => {
  const $ = (s) => document.querySelector(s);
  const yt = (y) => (y < 0 ? `${-y} BC` : String(y));
  const index = await api("/api/trades").catch(() => []);
  const series = (await ChangePanel.load().catch(() => ({}))).series || [];
  let map = null, layer = null;

  $("#tr_chips").innerHTML = index.map((s) => `<button type="button" data-t="${esc(s.id)}">${esc(s.title)}</button>`).join("");
  $("#tr_chips").addEventListener("click", (e) => {
    const b = e.target.closest("button[data-t]");
    if (b) show(b.dataset.t);
  });

  const timeline = (ev) => ev.length ? `<h3>Timeline</h3><ul class="ch-events tr-timeline">${ev.map((e) => `<li><b>${yt(e.year)}${
    e.end && e.end !== e.year ? `–${yt(e.end)}` : ""}</b> ${e.kind === "innovation" ? `💡 <a href="#" data-place="${esc(e.place)}">${esc(e.title)}</a>`
    : esc(e.title)}${e.text ? ` — ${esc(e.text)}` : ""}${e.citation ? ` <span class="cc-src">(${esc(e.citation)})</span>` : ""}</li>`).join("")}</ul>` : "";
  const notes = (ns) => ns.map((n) => `<article class="ch-note"><h3>${esc(n.title)}</h3><p>${esc(n.text)}</p>
    <ul class="cc-src">${n.sources.map((s) => `<li>“${esc(s.quote)}” — <a href="${esc(s.url)}" target="_blank" rel="noopener">${esc(s.short || s.citation)}</a></li>`).join("")}</ul></article>`).join("");
  const people = (ps) => ps.length ? `<h3>People</h3><ul class="nearby">${ps.map((p) => `<li><a href="#" data-person="${esc(p.id)}">${esc(p.name)}</a>
    <span class="meta">${esc([p.description, p.roles.join(", ")].filter(Boolean).join(" · "))}</span></li>`).join("")}</ul>` : "";
  const list = (title, rows, kind) => rows.length ? `<details class="tr-list"><summary>${esc(title)} (${rows.length.toLocaleString()})</summary>
    <ul class="nearby">${rows.map((r) => `<li><span class="dot" style="background:${kind === "place" ? placeColor(r.kind_group) : groupColor(r.category_group)}"></span>
      <a href="${kind === "place" ? "#" : buildingUrl(r.id)}" ${kind === "place" ? "data-place" : "data-open"}="${esc(r.id)}">${esc(r.name)}</a>
      <span class="meta">${esc([r.kind_label || r.category, r.date_text].filter(Boolean).join(" · "))}</span></li>`).join("")}</ul></details>` : "";

  function drawMap(s) {
    if (!map) {
      map = L.map("tr_map", { maxZoom: 17 }).setView([54.3, -4.5], 5);
      addBaseLayer(map);
    }
    if (layer) layer.remove();
    layer = L.layerGroup().addTo(map);
    const pts = [];
    s.places.forEach((p) => {
      pts.push([p.lat, p.lon]);
      L.circleMarker([p.lat, p.lon], { radius: 5, color: placeColor(p.kind_group), weight: 1, fillOpacity: 0.8 })
        .bindPopup(`<b>${esc(p.name)}</b><br>${esc(p.kind_label || "")}${p.date_text ? " · " + esc(p.date_text) : ""}<br><a href="#" data-place="${esc(p.id)}">Open</a>`)
        .addTo(layer);
    });
    s.buildings.forEach((b) => {
      pts.push([b.lat, b.lon]);
      L.circleMarker([b.lat, b.lon], { radius: 6, color: "#222", weight: 1.5, fillColor: groupColor(b.category_group), fillOpacity: 0.9 })
        .bindPopup(`<b>${esc(b.name)}</b><br>${esc(b.category || "")}${b.date_text ? " · " + esc(b.date_text) : ""}<br><a href="${buildingUrl(b.id)}" data-open="${esc(b.id)}">Open</a>`)
        .addTo(layer);
    });
    if (pts.length) map.fitBounds(pts, { padding: [20, 20], maxZoom: 9 });
  }

  function drawGraphs(ids) {
    const box = $("#tr_graphs");
    const shown = ids.map((id) => series.find((x) => x.id === id)).filter(Boolean);
    box.innerHTML = shown.map((s) => `<figure class="cc-item ch-fig" data-id="${esc(s.id)}"><figcaption class="cc-title">${esc(s.title)}
      ${s.region ? `<span class="cc-region">${esc(s.region)}</span>` : ""}<span class="cc-now">${esc(s.unit_long || s.unit || "")}</span></figcaption>
      <div class="cc-plot"></div><div class="cc-src"><a href="${IS_STATIC ? "change.html" : "/change"}#fig-${esc(s.id)}">Sources and notes on Change over time</a></div></figure>`).join("");
    box.querySelectorAll(".ch-fig").forEach((f) => {
      const s = series.find((x) => x.id === f.dataset.id);
      const models = (s.models || []).map((id) => series.find((x) => x.id === id)).filter(Boolean);
      ChangeCharts.draw(f.querySelector(".cc-plot"), s, { ...ChangeCharts.span(s, "fit", models), year: null, models });
    });
  }

  async function show(id) {
    document.querySelectorAll("#tr_chips button").forEach((b) => b.classList.toggle("on", b.dataset.t === id));
    history.replaceState(null, "", location.pathname + "?t=" + encodeURIComponent(id));
    const s = await api("/api/trade/" + encodeURIComponent(id));
    $("#tr_body").innerHTML = `<h2>${esc(s.title)}</h2><p class="prose">${esc(s.intro)}</p>
      <div class="tr-layout"><div>${timeline(s.events)}${people(s.people)}</div>
        <div><div id="tr_map" class="stories-map"></div><p class="hint">${s.places.length.toLocaleString()} places and
          ${s.buildings.length.toLocaleString()} catalogue buildings (dark outline) whose kind or name belongs to the trade.
          <a href="${IS_STATIC ? "map.html" : "/map"}?trade=${encodeURIComponent(s.id)}">Show on the Map page</a>, with the other layers and the year slider.</p>
          ${list("Places", s.places, "place")}${list("Catalogue buildings", s.buildings, "building")}</div></div>
      <h3>What historians say</h3>${notes(s.notes)}
      <h3>Graphs</h3><div class="ch-grid" id="tr_graphs"></div>`;
    map = null;
    drawMap(s);
    drawGraphs(s.series);
  }
  const want = new URLSearchParams(location.search).get("t");
  if (index.length) show(index.some((s) => s.id === want) ? want : index[0].id);
})();
