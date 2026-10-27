// Oldest things page (/things): researched oldest recipes, books, songs, laws, games, customs, objects and pictures
// from /api/things (bidb.oldest_things): theme chips, search, nation, by category or oldest first, a map of where
// they are kept, made or held, and each claim's sources with their quotes and check results. ?theme=&q=&nation=&sort=
(async () => {
  const $ = (s) => document.querySelector(s);
  const data = await api("/api/things").catch(() => ({ themes: [], count: 0 }));
  const COLORS = ["#b5651d", "#2e6fbf", "#8e44ad", "#2e7d32", "#c0392b", "#d4a017", "#16808a", "#6d4c41"];
  const all = [];
  data.themes.forEach((t, i) => t.categories.forEach((c) => c.entries.forEach((e) =>
    all.push({ ...e, theme: t.id, themeTitle: t.title, color: COLORS[i % COLORS.length] }))));
  const url = new URLSearchParams(location.search);
  const S = { theme: url.get("theme") || "", q: url.get("q") || "", nation: url.get("nation") || "", sort: url.get("sort") || "cat" };
  $("#th_q").value = S.q; $("#th_nation").value = S.nation; $("#th_sort").value = S.sort;
  const counts = {};
  all.forEach((e) => { counts[e.theme] = (counts[e.theme] || 0) + 1; });
  $("#th_chips").innerHTML = [["", `All (${all.length})`], ...data.themes.filter((t) => counts[t.id]).map((t) => [t.id, `${t.title} (${counts[t.id]})`])]
    .map(([id, label]) => `<button type="button" data-t="${esc(id)}">${esc(label)}</button>`).join("");

  const ROLE = { kept: "Kept at", made: "Made at", held: "Takes place at", found: "Found at" };
  const VERDICT = { kept: ["settled", "The sources agree"], corrected: ["corrected", "The popular claim is wrong; this is the defensible one"],
    open: ["open", "Disputed or uncertain"] };
  const CHECK = { "quote-found": "✓ quote found in the source", "quote-missing": "quote not found at the last check",
    unreachable: "source could not be read at the last check", "no-link": "print source" };
  const wiki = (t) => `https://en.wikipedia.org/wiki/${encodeURIComponent(t.replace(/ /g, "_"))}`;

  const card = (e) => {
    const [cls, tip] = VERDICT[e.verdict] || VERDICT.open;
    return `<article class="th-card" id="thing-${esc(e.id)}" style="--th:${e.color}">
      <h3>${esc(e.name)} <span class="th-date">${esc(e.age_text)}</span></h3>
      <p class="th-claim"><span class="th-verdict ${cls}" title="${esc(tip)}">${esc(cls)}</span> ${esc(e.claim)}</p>
      <p class="meta">${esc(e.nation)}${e.where ? ` · ${ROLE[e.where.role]} <a href="#" data-pan="${esc(e.id)}">${esc(e.where.name)}</a>` : ""}${
        e.wikipedia_title ? ` · <a href="${wiki(e.wikipedia_title)}" target="_blank" rel="noopener">Wikipedia</a>` : ""}${
        S.sort === "year" ? ` · ${esc(e.themeTitle)}` : ""}</p>
      <p>${esc(e.evidence)}</p>
      <details><summary>${e.sources.length} source${e.sources.length === 1 ? "" : "s"}</summary><ul class="th-sources">${e.sources.map((s) =>
        `<li>“${esc(s.quote)}” — <a href="${esc(s.url)}" target="_blank" rel="noopener">${esc(s.title)}</a>${s.locator ? ` (${esc(s.locator)})` : ""}${
          s.check ? ` <span class="th-check ${s.check === "quote-found" ? "ok" : ""}">${esc(CHECK[s.check] || s.check)}</span>` : ""}</li>`).join("")}</ul></details>
    </article>`;
  };

  let map, layer;
  const markers = new Map();
  function drawMap(rows) {
    if (!map) { map = L.map("th_map", { maxZoom: 17 }).setView([54.3, -4.5], 5); addBaseLayer(map); }
    if (layer) layer.remove();
    layer = L.layerGroup().addTo(map);
    markers.clear();
    rows.filter((e) => e.where).forEach((e) => {
      const m = L.circleMarker([e.where.lat, e.where.lon], { radius: 7, color: "#fff", weight: 1.5, fillColor: e.color, fillOpacity: 0.9 })
        .bindPopup(`<b>${esc(e.name)}</b> (${esc(e.age_text)})<br>${esc(ROLE[e.where.role])} ${esc(e.where.name)}<br><a href="#thing-${esc(e.id)}">Read more</a>`)
        .addTo(layer);
      markers.set(e.id, m);
    });
    if (markers.size) map.fitBounds(L.featureGroup([...markers.values()]).getBounds().pad(0.15), { maxZoom: 9 });
  }

  function render() {
    const words = S.q.toLowerCase().split(/\s+/).filter(Boolean);
    const rows = all.filter((e) => (!S.theme || e.theme === S.theme) && (!S.nation || e.nation === S.nation)
      && words.every((w) => `${e.name} ${e.claim} ${e.evidence} ${e.age_text} ${e.category} ${e.where?.name || ""} ${e.nation}`.toLowerCase().includes(w)));
    document.querySelectorAll("#th_chips button").forEach((b) => b.classList.toggle("on", b.dataset.t === S.theme));
    $("#th_count").textContent = `${rows.length} of ${all.length}`;
    let html = "";
    if (S.sort === "year") html = rows.slice().sort((a, b) => a.year - b.year).map(card).join("");
    else data.themes.forEach((t) => {
      const mine = rows.filter((e) => e.theme === t.id);
      if (!mine.length) return;
      html += `<section class="th-theme"><h2>${esc(t.title)}</h2><p class="meta">${esc(t.intro)}</p>`;
      t.categories.forEach((c) => {
        const es = mine.filter((e) => e.category === c.category);
        if (es.length) html += `<h3 class="th-cat">${esc(c.category)}</h3>${es.map(card).join("")}`;
      });
      html += "</section>";
    });
    $("#th_list").innerHTML = html || `<p class="meta">Nothing matches.</p>`;
    drawMap(rows);
    const p = new URLSearchParams();
    Object.entries(S).forEach(([k, v]) => { if (v && !(k === "sort" && v === "cat")) p.set(k, v); });
    history.replaceState(null, "", `${location.pathname}${p.toString() ? "?" + p : ""}${location.hash}`);
  }

  let timer = null;
  $("#th_q").addEventListener("input", (e) => { clearTimeout(timer); timer = setTimeout(() => { S.q = e.target.value.trim(); render(); }, 150); });
  $("#th_nation").addEventListener("change", (e) => { S.nation = e.target.value; render(); });
  $("#th_sort").addEventListener("change", (e) => { S.sort = e.target.value; render(); });
  $("#th_chips").addEventListener("click", (e) => { const b = e.target.closest("button[data-t]"); if (b) { S.theme = b.dataset.t; render(); } });
  $("#th_list").addEventListener("click", (e) => {
    const a = e.target.closest("a[data-pan]");
    if (!a) return;
    e.preventDefault();
    const m = markers.get(a.dataset.pan);
    if (m) { map.setView(m.getLatLng(), Math.max(map.getZoom(), 12)); m.openPopup(); $("#th_map").scrollIntoView({ block: "nearest" }); }
  });
  render();
  if (location.hash.startsWith("#thing-")) document.getElementById(location.hash.slice(1))?.scrollIntoView();
})();
