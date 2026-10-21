// Places of interest and people: colours, cards, detail views and a shared modal.
const PLACE_GROUPS = ["Battles & sieges", "Archaeological sites", "Lost places", "Parks, gardens & trees",
  "Industrial heritage", "Finds & treasures", "Plaques & people", "History events",
    "Legends & literature", "Maritime heritage", "Victorian era", "Underground", "Military heritage", "Museums & collections"];
const PLACE_ICON = { "Battles & sieges": "⚔", "Archaeological sites": "🪨", "Lost places": "🏚",
  "Parks, gardens & trees": "🌳", "Industrial heritage": "⚙", "Finds & treasures": "💰",
  "Plaques & people": "🔵", "History events": "📜", "Legends & literature": "📖", "Maritime heritage": "⚓", "Victorian era": "🎩", "Underground": "🚇", "Military heritage": "🛡", "Museums & collections": "🏛" };
const EXTRA_LABELS = { part_of: "Part of", now_in: "Now kept at", found_at: "Found at",
  commemorates: "Commemorates", inscription: "Inscription", region: "Region", register_ref: "Register reference",
  works: "Works set here" };
// a list value: plain strings, or [title, author, year] for literary works
const extraText = (v) => (Array.isArray(v) ? v.map((x) => (Array.isArray(x)
  ? `${x[0]}${x[1] ? ` (${x[1]}${x[2] ? ", " + x[2] : ""})` : ""}` : x)).join("; ") : v);

function placeColor(g) {
  const i = PLACE_GROUPS.indexOf(g);
  return cssVar(i >= 0 ? `--g${i + 1}` : "--g-other");
}

const lifeYears = (p) => (p.birth != null || p.death != null)
  ? `(${p.birth != null ? yearLabel(p.birth).replace("AD ", "") : "?"}–${p.death != null ? yearLabel(p.death).replace("AD ", "") : ""})` : "";

function placeCardHTML(p) {
  const icon = PLACE_ICON[p.kind_group] || "📍";
  const img = p.image_thumb
    ? `<img loading="lazy" src="${esc(p.image_thumb)}" alt="" onerror="this.replaceWith(Object.assign(document.createElement('div'),{className:'noimg',textContent:'${icon}'}))">`
    : `<div class="noimg">${icon}</div>`;
  return `<article class="card" data-place="${esc(p.id)}" tabindex="0">
    <div class="thumb">${img}</div>
    <div class="card-body"><h3>${esc(p.name)}</h3>
      ${p.date_text ? `<div class="date">${esc(p.date_text)}</div>` : ""}
      <div class="meta"><span class="dot" style="background:${placeColor(p.kind_group)}"></span>${esc(p.type || p.kind_label)}</div>
      <div class="meta">${esc([p.locality, p.nation].filter(Boolean).join(" · "))}</div>
      ${p.source && p.source !== "Wikidata" ? `<div class="meta">Source: ${esc(p.source)}</div>` : ""}
    </div></article>`;
}

// Wikidata reference behind a person <-> place link ({s: stated in, u: url}; a JSON string from the local API)
function linkRefHTML(ref) {
  if (typeof ref === "string") { try { ref = JSON.parse(ref); } catch (e) { ref = null; } }
  if (!ref || !(ref.s || ref.u)) return "";
  const label = esc(ref.s || "reference");
  return ` <span class="meta link-ref">· source: ${ref.u ? `<a href="${esc(ref.u)}" target="_blank" rel="noopener">${label}</a>` : label}</span>`;
}

function personLinkHTML(p) {
  return `<li><a href="#" data-person="${esc(p.id)}">${esc(p.name)}</a> <span class="meta">${esc(lifeYears(p))}
    ${p.description ? " · " + esc(p.description) : ""}</span>${linkRefHTML(p.ref)}</li>`;
}

function peopleByRoleHTML(people) {
  if (!people || !people.length) return "";
  const roles = {};
  people.forEach((p) => (roles[p.role] = roles[p.role] || []).push(p));
  return `<h4>People</h4>${Object.entries(roles).map(([role, ps]) =>
    `<div class="role-block"><b>${esc(role)}</b><ul class="nearby">${ps.slice(0, 12).map(personLinkHTML).join("")}</ul>
     ${ps.length > 12 ? `<div class="hint">and ${ps.length - 12} more</div>` : ""}</div>`).join("")}`;
}

function nearbyPlacesHTML(places, title) {
  if (!places || !places.length) return "";
  return `<h4>${esc(title)}</h4><ul class="nearby">${places.map((p) =>
    `<li><span class="dot" style="background:${placeColor(p.kind_group)}"></span>
      <a href="#" data-place="${esc(p.id)}">${esc(p.name)}</a>
      <span class="meta">${esc(p.kind_label)}${p.date_text ? " · " + esc(p.date_text) : ""}${p.dist != null ? ` · ${Prefs.dist(p.dist)}` : ""}</span></li>`).join("")}</ul>`;
}

// extras with their own rendering: objects a museum keeps, museum links for "now kept at"
const SPECIAL_EXTRA = ["kept_here", "now_in_ids"];
// "place:<id>" or "building:<id>" (bidb/museums.py link_finds)
const museumLink = (name, ref) => {
  if (!ref) return esc(name);
  const [kind, id] = [ref.slice(0, ref.indexOf(":")), ref.slice(ref.indexOf(":") + 1)];
  return kind === "building" ? `<a href="${buildingUrl(id)}" data-open="${esc(id)}">${esc(name)}</a>`
    : `<a href="#" data-place="${esc(id)}">${esc(name)}</a>`;
};
const fieldHTML = (label, html) => (html ? `<dt>${esc(label)}</dt><dd>${html}</dd>` : "");
function keptHereHTML(objs) {
  if (!objs || !objs.length) return "";
  return `<h4>Kept here</h4><ul class="nearby kept-here">${objs.map(([name, title, qid, type]) => `<li>${title
    ? `<a href="https://en.wikipedia.org/wiki/${encodeURIComponent(title.replace(/ /g, "_"))}" target="_blank" rel="noopener">${esc(name)}</a>`
    : `<a href="https://www.wikidata.org/wiki/${esc(qid)}" target="_blank" rel="noopener">${esc(name)}</a>`}${
    type ? ` <span class="meta">${esc(type)}</span>` : ""}</li>`).join("")}</ul>`;
}

function placeDetailHTML(p) {
  const enc = encodeURIComponent;
  const ex = p.extra || {};
  const extra = Object.entries(ex).filter(([k, v]) => v && !SPECIAL_EXTRA.includes(k) && (!Array.isArray(v) || v.length))
    .map(([k, v]) => k === "now_in" && ex.now_in_ids ? fieldHTML(EXTRA_LABELS[k], v.map((n) => museumLink(n, ex.now_in_ids[n])).join("; "))
      : field(EXTRA_LABELS[k] || k, extraText(v))).join("");
  const links = [
    p.url && link(p.source === "History timeline" ? "Source" : `Official record (${p.source})`, p.url),
    p.wikipedia_title && link("Wikipedia", `https://en.wikipedia.org/wiki/${enc(p.wikipedia_title.replace(/ /g, "_"))}`),
    p.wikidata_id && link("Wikidata", `https://www.wikidata.org/wiki/${p.wikidata_id}`),
    p.lat != null && link("OpenStreetMap", `https://www.openstreetmap.org/?mlat=${p.lat}&mlon=${p.lon}#map=15/${p.lat}/${p.lon}`),
  ].filter(Boolean).join("");
  return `<div class="detail">
    ${p.image_thumb ? `<figure><img src="${esc(p.image_thumb.replace(/width=\d+/, "width=1000"))}" alt="${esc(p.name)}">
      ${p.image_page ? `<figcaption>${p.image_note ? esc(p.image_note) + ". " : ""}<a href="${esc(p.image_page)}" target="_blank" rel="noopener">Image: Wikimedia Commons, see file page for author and licence</a></figcaption>` : ""}</figure>` : ""}
    <div class="detail-text">
      <h2>${esc(p.name)}</h2>
      <div class="pron" data-pron="${esc(p.id)}" data-pron-title="${esc(p.name)}"></div>
      ${p.lat != null ? `<div class="actions"><button class="btn small ghost tg-wide" data-fav="${esc(p.id)}">${store.get(FAV).includes(p.id) ? "★ In your tour" : "☆ Add to your tour"}</button>${mapButton(p, p.kind_group)}</div>` : ""}
      ${p.description ? `<p class="lede">${esc(p.description)}</p>` : ""}
      <div class="chips"><span class="chip" style="border-color:${placeColor(p.kind_group)}">${esc(p.kind_group)}</span>
        <span class="chip">${esc(p.type || p.kind_label)}</span>${p.nation ? `<span class="chip">${esc(p.nation)}</span>` : ""}
        ${p.period && p.period !== "Unknown" ? `<span class="chip">${esc(p.period)}</span>` : ""}</div>
      <dl>${field("Date", p.date_text)}${field("Where", p.locality)}${field("Designation", p.designation)}
        ${field("Source", p.source)}${extra}
        ${field("Coordinates", p.lat != null ? `${p.lat.toFixed(5)}, ${p.lon.toFixed(5)}` : "")}</dl>
      ${p.building_id ? `<p>Kept in: <a href="${buildingUrl(p.building_id)}" data-open="${esc(p.building_id)}">${esc(p.locality || "the building")}</a></p>` : ""}
      ${keptHereHTML(ex.kept_here)}
      ${p.wikipedia_extract ? `<h4>About</h4>${p.wikipedia_extract.split(/\n+/).map((t) => `<p>${esc(t)}</p>`).join("")}` : ""}
      <div class="stories-box" data-stories="${esc(p.id)}"></div>
      ${peopleByRoleHTML(p.people)}
      ${p.lat != null ? `<p class="getting-there" data-transport="${p.lat},${p.lon}" data-visit="${esc(p.id)}"></p>` : ""}
      <div class="links">${links}</div>
      ${sourcesHTML({ refs: p.refs })}
      ${p.lat != null ? '<div id="place-map" class="detail-map"></div>' : ""}
      ${nearbyPlacesHTML(p.nearby_places, `Other places of interest within ${Prefs.dist(5, 0)}`)}
    </div></div>`;
}

function personDetailHTML(p) {
  const roles = {};
  (p.links || []).forEach((l) => (roles[l.role] = roles[l.role] || []).push(l));
  return `<div class="detail"><div class="detail-text">
    ${p.image_thumb ? `<img class="portrait" src="${esc(p.image_thumb)}" alt="">` : ""}
    <h2>${esc(p.name)} <span class="hint">${esc(lifeYears(p))}</span></h2>
    <div class="pron" data-pron="${esc(p.id)}" data-pron-title="${esc(p.name)}"></div>
    ${p.description ? `<p class="lede">${esc(p.description)}</p>` : ""}
    ${p.summary ? `<p>${esc(p.summary)}</p>` : ""}
    <h4>Connected places</h4>${Object.entries(roles).map(([role, ls]) => `<div class="role-block"><b>${esc(role)}</b>
      <ul class="nearby">${ls.map((l) => `<li><a href="#" ${l.target_type === "place" ? "data-place" : "data-open"}="${esc(l.target_id)}">${esc(l.name || l.target_id)}</a>
        <span class="meta">${esc(l.what || "")}${l.date_text ? " · " + esc(l.date_text) : ""}</span>${linkRefHTML(l.ref)}</li>`).join("")}</ul></div>`).join("")}
    <div id="person-map" class="detail-map"></div>
    <div class="links">${p.wikipedia_title ? link("Wikipedia", `https://en.wikipedia.org/wiki/${encodeURIComponent(p.wikipedia_title.replace(/ /g, "_"))}`) : ""}
      ${link("Wikidata", `https://www.wikidata.org/wiki/${p.id}`)}</div>
  </div></div>`;
}

// ---- modal shared by the Places, People and History pages ----------------------------
let _miniMap = null;
function miniMap(id, points, zoom = 12) {
  const el = document.getElementById(id);
  if (!el || typeof L === "undefined") return;
  const pts = points.filter((p) => p.lat != null);
  if (!pts.length) { el.remove(); return; }
  if (_miniMap) { _miniMap.remove(); _miniMap = null; }
  _miniMap = L.map(el, { scrollWheelZoom: false, maxZoom: 18 });
  addBaseLayer(_miniMap);
  pts.forEach((p) => L.circleMarker([p.lat, p.lon], { radius: 7, weight: 2, color: cssVar("--surface"),
    fillOpacity: 1, fillColor: p.color || cssVar("--series-1") }).bindTooltip(esc(p.name || "")).addTo(_miniMap));
  if (pts.length === 1) _miniMap.setView([pts[0].lat, pts[0].lon], IS_STATIC ? Math.min(zoom, 9) : zoom);
  else _miniMap.fitBounds(pts.map((p) => [p.lat, p.lon]), { padding: [20, 20], maxZoom: 12 });
}

function showModal(html) {
  if (!document.getElementById("modal")) {           // pages without their own modal (history, detail)
    document.body.insertAdjacentHTML("beforeend", `<div id="modal" class="modal hidden" aria-hidden="true">
      <div class="modal-card" role="dialog"><button class="close" id="modal-close" aria-label="Close">×</button>
      <div id="modal-body"></div></div></div>`);
  }
  const m = document.getElementById("modal");
  document.getElementById("modal-body").innerHTML = html;
  m.classList.remove("hidden");
  m.setAttribute("aria-hidden", "false");
  document.body.classList.add("noscroll");
  if (!m.dataset.open) dialogOpened(m);
  m.dataset.open = "1";
}

function hideModal() {
  const m = document.getElementById("modal");
  if (!m) return;
  m.classList.add("hidden");
  m.setAttribute("aria-hidden", "true");
  document.body.classList.remove("noscroll");
  if (m.dataset.open) dialogClosed();
  delete m.dataset.open;
}

async function openPlace(id) {
  const p = await api("/api/place/" + encodeURIComponent(id));
  Prefs.recent.add(p.id, "place", p.name);
  showModal(placeDetailHTML(p));
  miniMap("place-map", [{ ...p, color: placeColor(p.kind_group) }]);
}

async function openPerson(id) {
  const p = await api("/api/person/" + encodeURIComponent(id));
  Prefs.recent.add(p.id, "person", p.name);
  showModal(personDetailHTML(p));
  miniMap("person-map", (p.links || []).map((l) => ({ lat: l.lat, lon: l.lon, name: `${l.name} (${l.role})` })));
}

document.addEventListener("click", (e) => {
  const pl = e.target.closest("[data-place]"), pe = e.target.closest("[data-person]");
  if (pl && !e.target.closest("[data-fav],[data-cmp]")) { e.preventDefault(); openPlace(pl.dataset.place); return; }
  if (pe) { e.preventDefault(); openPerson(pe.dataset.person); return; }
  const b = e.target.closest("[data-open]");          // a building, on pages without the catalogue modal
  if (b && typeof openDetail !== "function" && typeof showDetail !== "function") {
    e.preventDefault();
    location.href = buildingUrl(b.dataset.open);
    return;
  }
  if (e.target.id === "modal-close" || e.target.id === "modal") hideModal();
});
document.addEventListener("keydown", (e) => { if (e.key === "Escape") hideModal(); });
