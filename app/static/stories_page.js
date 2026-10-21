// Stories page: legends, ghosts, folklore and curious history, by theme, nation and search, with a map.
const S$ = (sel) => document.querySelector(sel);
let stOffset = 0, stTotal = 0, stTimer = null, stKind = "", stMap = null, stLayer = null;

async function loadStories(append = false) {
  if (!append) stOffset = 0;
  const p = { q: S$("#st_q").value.trim(), kind: stKind, nation: S$("#st_nation").value, limit: 40, offset: stOffset };
  const data = await Stories.search(p);
  stTotal = data.total;
  S$("#st_count").textContent = `${stTotal.toLocaleString()} stories`;
  const html = data.rows.map((s) => Stories.storyHTML(s, true)).join("");
  if (append) S$("#st_list").insertAdjacentHTML("beforeend", html);
  else S$("#st_list").innerHTML = html || "<p class='empty'>No stories match.</p>";
  stOffset += data.rows.length;
  S$("#st_more").parentElement.classList.toggle("hidden", stOffset >= stTotal);
  drawStoryMap(data.rows, append);
  const qs = new URLSearchParams(Object.entries({ q: p.q, kind: p.kind, nation: p.nation }).filter(([, v]) => v));
  history.replaceState(null, "", location.pathname + (qs.toString() ? "?" + qs : ""));
}

function drawStoryMap(rows, append) {
  if (!stMap) {
    stMap = L.map("st_map", { maxZoom: 17 }).setView([54.3, -4.5], 5);
    addBaseLayer(stMap);
  }
  if (!append && stLayer) stLayer.remove();
  if (!append || !stLayer) stLayer = L.layerGroup().addTo(stMap);
  rows.filter((s) => s.lat !== "" && s.lat != null).forEach((s) => L.marker([+s.lat, +s.lon], {
    icon: L.divIcon({ className: "story-marker", html: Stories.icon(s.kind), iconSize: [24, 24] }) })
    .bindPopup(`<b>${esc(s.name)}</b><br>${esc(Stories.label(s.kind))}<br><a href="#" data-story-open="${esc(s.entity_kind)}" data-id="${esc(s.entity_id)}">Open</a>`)
    .addTo(stLayer));
}

async function initStories() {
  const url = new URLSearchParams(location.search);
  S$("#st_q").value = url.get("q") || "";
  S$("#st_nation").value = url.get("nation") || "";
  stKind = url.get("kind") || "";
  const cs = await Stories.counts().catch(() => []);
  const chip = (k, n, label) => `<button type="button" data-k="${esc(k)}" class="${k === stKind ? "on" : ""}">${label}${n ? ` <span class="hint">${n.toLocaleString()}</span>` : ""}</button>`;
  S$("#st_chips").innerHTML = chip("", 0, "All stories") + cs.map((c) => chip(c.kind, c.count, `${Stories.icon(c.kind)} ${esc(c.label)}`)).join("");
  S$("#st_chips").addEventListener("click", (e) => {
    const b = e.target.closest("button[data-k]");
    if (!b) return;
    stKind = b.dataset.k;
    S$("#st_chips").querySelectorAll("button").forEach((x) => x.classList.toggle("on", x === b));
    loadStories();
  });
  S$("#st_q").addEventListener("input", () => { clearTimeout(stTimer); stTimer = setTimeout(() => loadStories(), 250); });
  S$("#st_nation").addEventListener("change", () => loadStories());
  S$("#st_more").addEventListener("click", () => loadStories(true));
  loadStories();
}
initStories();
