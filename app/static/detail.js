// Detail view extras: map, nearby buildings, Commons gallery and the correction form.
function showDetail(b, container, inModal) {
  Prefs.recent.add(b.id, "building", b.name);
  container.innerHTML = renderDetail(b, inModal);
  mountDetailMap(b);
  loadNearby(b);
  loadRelated(b);
  loadGallery(b);
  const open = container.querySelector("#edit_open");
  if (open) open.addEventListener("click", () => openEditForm(b, container));
}

async function loadNearby(b) {
  const box = document.getElementById("detail-nearby");
  if (!box || b.lat == null) return;
  const rows = await api(`/api/nearby/${encodeURIComponent(b.id)}?limit=10&km=15`).catch(() => []);
  if (!rows.length) return;
  box.innerHTML = `<h4>Nearby old buildings (within ${Prefs.dist(15, 0)})</h4><ul class="nearby">${rows.map((r) =>
    `<li><a href="#" data-open="${esc(r.id)}">${esc(r.name)}</a>
     <span class="meta">${esc(r.date_text || "")} · ${esc(r.category)} · ${Prefs.dist(r.dist)}</span></li>`).join("")}</ul>`;
}

// People, objects kept here and nearby places of interest (from the places build)
async function loadRelated(b) {
  const box = document.getElementById("detail-related");
  if (!box) return;
  const rel = await api(`/api/related/${encodeURIComponent(b.id)}`).catch(() => null);
  if (!rel) return;
  box.innerHTML = peopleByRoleHTML(rel.people) +
    (rel.objects.length ? `<h4>Notable objects here</h4><ul class="nearby">${rel.objects.map((o) =>
      `<li><a href="#" data-place="${esc(o.id)}">${esc(o.name)}</a> <span class="meta">${esc(o.type || "")}${o.description ? " · " + esc(o.description) : ""}</span></li>`).join("")}</ul>` : "") +
    nearbyPlacesHTML(rel.places, `Places of interest within ${Prefs.dist(5, 0)}`);
}

async function loadGallery(b) {
  const box = document.getElementById("detail-gallery");
  if (!box || !String(b.id).startsWith("Q")) return;
  box.innerHTML = '<p class="hint">Looking for more photos on Wikimedia Commons…</p>';
  const res = await api(`/api/images/${encodeURIComponent(b.id)}`).catch(() => null);
  if (!res || !res.images || !res.images.length) { box.innerHTML = ""; return; }
  box.innerHTML = `<h4>More photos <span class="hint">from Commons category "${esc(res.category)}"</span></h4>
    <div class="gallery">${res.images.map((im) => `
      <a href="${esc(im.page)}" target="_blank" rel="noopener" title="${esc(im.title)}">
        <img loading="lazy" src="${esc(im.thumb)}" alt="${esc(im.title)}">
        <span>${esc(im.artist || "")}${im.license ? " · " + esc(im.license) : ""}</span></a>`).join("")}</div>`;
}

const EDIT_FIELDS = [["name", "Name"], ["date_text", "Date (text shown)"],
  ["year_start", "Sort year (negative = BC)"], ["category", "Category"], ["status", "Status"],
  ["heritage_grade", "Heritage grade"], ["street_address", "Address"],
  ["description", "Short description"], ["notes", "Your notes"]];

function openEditForm(b, container) {
  const box = container.querySelector("#detail-edit");
  box.innerHTML = `<form class="edit-form"><h4>Correct this record</h4>
    <p class="hint">Corrections are saved to data/overrides.json and survive rebuilds.</p>
    ${EDIT_FIELDS.map(([k, label]) => `<label>${label}
      ${k === "notes" || k === "description"
        ? `<textarea name="${k}" rows="2">${esc(k === "notes" ? b.user_notes : b[k])}</textarea>`
        : `<input name="${k}" value="${esc(b[k] ?? "")}" ${k === "year_start" ? 'type="number"' : ""}>`}</label>`).join("")}
    <label>Why (source or reason)<input name="_note" placeholder="e.g. Historic England list entry 1234"></label>
    <div class="actions"><button class="btn small" type="submit">Save correction</button>
      <button class="btn small ghost" type="button" data-cancel>Cancel</button>
      ${b.edited ? '<button class="btn small ghost" type="button" data-revert>Remove my corrections</button>' : ""}</div>
    <div class="hint" data-msg></div></form>`;
  const form = box.querySelector("form");
  form.querySelector("[data-cancel]").onclick = () => { box.innerHTML = ""; };
  const revert = form.querySelector("[data-revert]");
  if (revert) revert.onclick = async () => {
    const r = await fetch(`/api/override/${encodeURIComponent(b.id)}`, { method: "DELETE" });
    form.querySelector("[data-msg]").textContent = (await r.json()).note || "Removed.";
  };
  form.onsubmit = async (e) => {
    e.preventDefault();
    const fields = {};
    EDIT_FIELDS.forEach(([k]) => {
      const v = form.elements[k].value.trim();
      const orig = k === "notes" ? (b.user_notes || "") : String(b[k] ?? "");
      if (v !== orig) fields[k] = v;
    });
    if (!Object.keys(fields).length) { form.querySelector("[data-msg]").textContent = "Nothing changed."; return; }
    const r = await fetch(`/api/override/${encodeURIComponent(b.id)}`, {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ fields, note: form.elements._note.value.trim() }) });
    const res = await r.json();
    if (!res.ok) { form.querySelector("[data-msg]").textContent = res.error || "Could not save."; return; }
    const fresh = await api(`/api/building/${encodeURIComponent(b.id)}`);
    showDetail(fresh, container, container.id === "modal-body");
  };
}

let _detailMap = null, _planLayer = null;
function mountDetailMap(b) {
  const el = document.getElementById("detail-map");
  if (!el || b.lat == null || typeof L === "undefined") return;
  if (_detailMap) { _detailMap.remove(); _detailMap = null; }
  _detailMap = L.map(el, { scrollWheelZoom: false, maxZoom: 19 }).setView([b.lat, b.lon], IS_STATIC ? 13 : 15);
  addBaseLayer(_detailMap);
  let outline = null;
  if (b.footprint) {
    try {
      outline = L.geoJSON(JSON.parse(b.footprint), { style: () => ({ color: groupColor(b.category_group), weight: 2,
        fillOpacity: 0.25, fillColor: groupColor(b.category_group) }) }).bindTooltip("Building outline (OpenStreetMap)").addTo(_detailMap);
      const m = _detailMap, ol = outline;
      const fit = () => {                       // skipped if another detail view replaced this map
        if (m !== _detailMap) return;
        m.invalidateSize();
        m.fitBounds(ol.getBounds(), { maxZoom: 19, padding: [30, 30] });
      };
      if (el.clientWidth) fit();
      setTimeout(fit, 120);                     // modal views have no size until shown
    } catch (e) { outline = null; }
  }
  if (!outline) {
    L.circleMarker([b.lat, b.lon], { radius: 8, weight: 2, color: cssVar("--surface"), fillOpacity: 1,
                                     fillColor: groupColor(b.category_group) }).addTo(_detailMap);
  }
  mountPlan(b, outline);
  mountOldMaps(b);
}

// Georeferenced historic maps (Allmaps) covering the building, most detailed first
function mountOldMaps(b) {
  const box = document.getElementById("detail-oldmaps");
  if (!box || b.lat == null || typeof Historic === "undefined") return;
  Historic.mapsAt(b.lat, b.lon).then(({ total, maps }) => {
    if (!maps.length) return;
    const size = (a) => (a < 1 ? `${Math.round(a * 100)} ha` : `${a < 100 ? a.toFixed(1) : Math.round(a).toLocaleString()} km²`);
    box.innerHTML = `<h4>Historic maps of this place</h4><ul class="nearby">${maps.map((m) =>
      `<li><a href="https://viewer.allmaps.org/?url=${encodeURIComponent("https://annotations.allmaps.org/maps/" + m.id)}" target="_blank" rel="noopener">Map sheet</a>
        <span class="meta">${esc(m.p || "unknown library")} · covers ${size(m.a)}</span>
        ${m.l ? `<a class="meta" href="${esc(m.l)}" target="_blank" rel="noopener">library record</a>` : ""}</li>`).join("")}</ul>
      <p class="hint">${total > maps.length ? `${maps.length} most detailed of ${total} georeferenced maps` : `${total} georeferenced map${total > 1 ? "s" : ""}`}
        on <a href="https://allmaps.org" target="_blank" rel="noopener">Allmaps</a> (opens the scanned map in place over a modern map).</p>`;
  });
}

// Floor plan (Wikidata "plan view image"): shown under the map, optionally laid over it
function mountPlan(b, outline) {
  const box = document.getElementById("detail-plan");
  if (!box || !b.plan_image) return;
  if (IS_STATIC && !b.plan_thumb && window.STATIC_PLAN) {    // hosted: fetch this plan's shard first
    window.STATIC_PLAN(b.id).then((uri) => { if (uri) { b.plan_thumb = uri; mountPlan(b, outline); } });
    return;
  }
  const url = planUrl(b);
  if (!url) return;
  box.innerHTML = `<h4>Floor plan</h4><figure class="plan"><img src="${esc(url)}" alt="Plan of ${esc(b.name)}">
    <figcaption><a href="${COMMONS_PAGE}${encodeURIComponent(b.plan_image.replace(/ /g, "_"))}" target="_blank" rel="noopener">Plan on Wikimedia Commons</a>
    (author and licence on the file page)</figcaption></figure>
    <button class="btn small ghost" type="button" id="plan_overlay">Lay the plan over the map</button>
    <span class="hint">Approximate: the plan is stretched to the ${outline ? "building outline" : "area around the point"}; it is not georeferenced.</span>`;
  box.querySelector("#plan_overlay").onclick = (e) => {
    if (_planLayer) { _detailMap.removeLayer(_planLayer); _planLayer = null; e.target.textContent = "Lay the plan over the map"; return; }
    const bounds = outline ? outline.getBounds() : L.latLng(b.lat, b.lon).toBounds(80);
    _planLayer = L.imageOverlay(url, bounds, { opacity: 0.7 }).addTo(_detailMap);
    _detailMap.fitBounds(bounds, { maxZoom: 19 });
    e.target.textContent = "Remove the plan";
  };
}

const COMMONS_PAGE = "https://commons.wikimedia.org/wiki/File:";
function planUrl(b) {
  if (IS_STATIC) return b.plan_thumb || null;          // embedded copy in the hosted version
  return `https://commons.wikimedia.org/wiki/Special:FilePath/${encodeURIComponent(b.plan_image.replace(/ /g, "_"))}?width=900`;
}

// Links inside a detail view ("nearby") open that building
document.addEventListener("click", (e) => {
  const a = e.target.closest("[data-open]");
  if (!a || typeof openDetail === "function") return;      // catalogue page has its own modal
  e.preventDefault();
  location.href = buildingUrl(a.dataset.open);
});
