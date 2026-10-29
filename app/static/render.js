// HTML rendering helpers shared by the catalogue page and the standalone detail page.
const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) =>
  ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));

const CAT_ICON = {
  "Prehistoric monument": "🪨", "Prehistoric dwelling": "🛖", "Roman structure": "🏛",
  "Cathedral": "⛪", "Abbey / monastery": "⛪", "Church / chapel": "⛪",
  "Castle / fortification": "🏰", "Civic building": "🏛", "Palace / manor house": "🏯",
  "House / domestic": "🏠", "Agricultural / industrial": "🌾",
  "Bridge / infrastructure": "🌉", "Cross / carved stone": "✝", "Public house / inn": "🍺",
  "Hotel": "🛎", "Market / shop": "🛒", "Bank / office": "🏦", "Post office": "✉",
  "School / college": "🎓", "Library": "📚", "Almshouse / hospital": "🏥",
  "Theatre / entertainment": "🎭", "Prison": "⛓", "Museum": "🖼", "Observatory / science": "🔭",
  "Railway": "🚂", "Lighthouse": "🗼", "Mill": "⚙", "Synagogue / mosque / meeting house": "🕍", "Ruin / archaeological site": "🏚", "Other structure": "📍",
};

// Eight colour groups, fixed order = fixed palette slot (validated CVD-safe); "Other" is grey
const GROUPS = ["Religious", "Fortification", "Prehistoric", "Domestic", "Roman",
                "Commercial & civic", "Institutions & culture", "Industry & transport"];
const PERIODS = ["Neolithic", "Bronze Age", "Iron Age", "Roman Britain", "Early Medieval", "Norman",
                 "High Medieval", "Late Medieval", "Tudor", "Stuart", "Georgian", "Victorian",
                 "Modern"];
function cssVar(name) {
  return getComputedStyle(document.documentElement).getPropertyValue(name).trim();
}
function groupColor(g) {
  const i = GROUPS.indexOf(g);
  return cssVar(i >= 0 ? `--g${i + 1}` : "--g-other");
}
function periodColor(p) {
  const i = PERIODS.indexOf(p);
  return cssVar(i >= 0 ? `--p${i + 1}` : "--g-other");
}

function yearLabel(y) {
  if (y === null || y === undefined) return "";
  return y < 0 ? `${-y} BC` : `AD ${y}`;
}

// "≈" marks dates mined from article text or estimated from the building type
function dateHTML(r) {
  const approx = r.date_confidence && !["Recorded", "Not recorded", "Corrected (reviewed)", "Corrected by user"].includes(r.date_confidence);
  const text = esc(r.date_text || "date unknown");
  return approx ? `<span title="${esc(r.date_confidence)}">${Prefs.get("approxMarker") ? "≈ " : ""}${text}</span>` : text;
}

function cardHTML(r) {
  const img = r.image_thumb
    ? `<img loading="lazy" src="${esc(r.image_thumb)}" alt="" onerror="this.replaceWith(Object.assign(document.createElement('div'),{className:'noimg',textContent:'${CAT_ICON[r.category] || "📍"}'}))">`
    : `<div class="noimg">${CAT_ICON[r.category] || "📍"}</div>`;
  const badges = (r.curated ? '<span class="badge">Notable</span>' : "") +
    (r.landmark && !r.curated && !r.oldest_of_type ? '<span class="badge">Landmark</span>' : "") +
    (r.oldest_of_type ? `<span class="badge alt">Oldest ${esc(r.oldest_of_type.toLowerCase())}</span>` : "");
  return `<article class="card" data-id="${esc(r.id)}" tabindex="0">
    <div class="thumb">${img}<div class="badges">${badges}</div>${toggleButtons(r.id)}</div>
    <div class="card-body">
      <h3>${esc(r.name)}</h3>
      <div class="date">${dateHTML(r)}</div>
      <div class="meta"><span class="dot" style="background:${groupColor(r.category_group)}"></span>${esc(r.category)} · ${esc(r.period)}</div>
      ${r.dist != null ? `<div class="meta">${Prefs.dist(r.dist)} away</div>` : ""}
      <div class="meta">${esc([r.locality, r.nation].filter(Boolean).join(" · "))}</div>
    </div></article>`;
}

function toggleButtons(id) {
  const fav = store.get(FAV).includes(id), cmp = store.get(CMP).includes(id);
  return `<div class="toggles">
    <button class="tg ${fav ? "on" : ""}" data-fav="${esc(id)}" title="Add to your tour" aria-pressed="${fav}">★</button>
    <button class="tg ${cmp ? "on" : ""}" data-cmp="${esc(id)}" title="Add to compare (max 3)" aria-pressed="${cmp}">⇄</button></div>`;
}

function rowHTML(r) {
  return `<tr data-id="${esc(r.id)}"><td class="dot-cell"><span class="dot" style="background:${groupColor(r.category_group)}"></span></td>
    <td><a href="#" class="name">${esc(r.name)}</a>${r.curated ? ' <span class="pill">Notable</span>' : ""}</td>
    <td>${dateHTML(r)}</td><td>${esc(r.period)}</td><td>${esc(r.category)}</td>
    <td>${esc(r.nation)}</td><td>${esc(r.locality)}</td><td>${esc(r.heritage_grade)}</td>
    <td>${esc(r.status)}</td></tr>`;
}

function field(label, value) {
  if (value === null || value === undefined || value === "") return "";
  return `<dt>${esc(label)}</dt><dd>${esc(value)}</dd>`;
}

// Coordinates and the OS or Irish grid reference (to 10 m), each with a copy button (roadmap LD2)
function coordsHTML(lat, lon) {
  const ll = `${lat.toFixed(5)}, ${lon.toFixed(5)}`, g = typeof OSGrid !== "undefined" && OSGrid.forPoint(lat, lon, 8);
  const copy = (text) => `<button class="copy-btn" type="button" data-copy="${esc(text)}" title="Copy" aria-label="Copy ${esc(text)}">⧉</button>`;
  return `${esc(ll)} ${copy(ll)}` + (g ? `<br><span title="${g.grid === "OS" ? "Ordnance Survey National Grid" : "Irish Grid"}, to 10 m">${g.grid} grid ${esc(g.ref)}</span> ${copy(g.ref)}` : "");
}
const coordsField = (lat, lon) => (lat != null ? `<dt>Coordinates</dt><dd>${coordsHTML(lat, lon)}</dd>` : "");
document.addEventListener("click", (e) => {
  const b = e.target.closest("[data-copy]");
  if (b) { e.preventDefault(); copyText(b.dataset.copy, b, "✓"); }
});

function link(label, url) {
  return url ? `<a class="ext" href="${esc(url)}" target="_blank" rel="noopener">${esc(label)} ↗</a>` : "";
}

function detailLinks(b) {
  const enc = encodeURIComponent;
  return [
    b.wikipedia_title && link("Wikipedia", `https://en.wikipedia.org/wiki/${enc(b.wikipedia_title.replace(/ /g, "_"))}`),
    b.wikidata_id && link("Wikidata", `https://www.wikidata.org/wiki/${b.wikidata_id}`),
    b.nhle_id && link("Historic England list entry", `https://historicengland.org.uk/listing/the-list/list-entry/${enc(b.nhle_id)}`),
    b.hes_id && link("Historic Environment Scotland", `https://portal.historicenvironment.scot/designation/${enc(b.hes_id)}`),
    b.ie_niah_id && link("Buildings of Ireland (NIAH)", `https://www.buildingsofireland.ie/buildings-search/building/${enc(b.ie_niah_id)}/`),
    b.ie_smr_id && link("Historic Environment Viewer (SMR)", `https://maps.archaeology.ie/HistoricEnvironment/?SMR=${enc(b.ie_smr_id)}`),
    b.cadw_id && link("Cadw record", `https://cadwpublic-api.azurewebsites.net/reports/listedbuilding/FullReport?lang=en&id=${enc(b.cadw_id)}`),
    b.register_url && link("Official register record", b.register_url),
    b.website && link("Official website", b.website),
    b.lat != null && link("OpenStreetMap", `https://www.openstreetmap.org/?mlat=${b.lat}&mlon=${b.lon}#map=17/${b.lat}/${b.lon}`),
    b.lat != null && link("Google Maps", `https://www.google.com/maps/search/?api=1&query=${b.lat},${b.lon}`),
  ].filter(Boolean).join("");
}

// Sources behind the record and the references Wikidata gives for its facts
function sourcesHTML(b) {
  const parse = (v) => { try { return JSON.parse(v || "[]"); } catch (e) { return []; } };
  const src = parse(b.sources), refs = parse(b.refs);
  if (!src.length && !refs.length) return "";
  return `<details class="sources-box"><summary>Sources &amp; references (${src.length + refs.length})</summary>
    ${src.length ? `<ul>${src.map((s) => `<li><a href="${esc(s.url)}" target="_blank" rel="noopener">${esc(s.label)}</a></li>`).join("")}</ul>` : ""}
    ${refs.length ? `<p class="hint">References attached to the facts on Wikidata:</p><ul>${refs.map((r) =>
      `<li><b>${esc(r.fact)}</b>${r.value ? ` (${esc(r.value)})` : ""}: ${r.url ? `<a href="${esc(r.url)}" target="_blank" rel="noopener">${esc(r.title || r.stated_in || "source")}</a>` : ""}${r.stated_in && (!r.url || r.title) ? `${r.url ? " · " : ""}stated in ${esc(r.stated_in)}` : ""}</li>`).join("")}</ul>` : ""}
  </details>`;
}

function renderDetail(b, inModal) {
  const img = b.image_thumb
    ? `<figure><img src="${esc(b.image_thumb.replace(/width=\d+/, "width=1200"))}" alt="${esc(b.name)}">
        ${b.image_page ? `<figcaption>${b.image_note ? esc(b.image_note) + ". " : ""}<a href="${esc(b.image_page)}" target="_blank" rel="noopener">Image: Wikimedia Commons — see file page for author &amp; licence</a></figcaption>` : ""}</figure>`
    : "";
  const address = [b.street_address, b.locality, b.postcode && `nearest postcode ${b.postcode}`]
    .filter(Boolean).join(", ");
  return `<div class="detail">
    ${img}
    <div class="detail-text">
      <h2>${esc(b.name)}</h2>
      <div class="pron" data-pron="${esc(b.id)}" data-pron-title="${esc(b.name)}"></div>
      <div class="actions">
        <button class="btn small ghost tg-wide" data-fav="${esc(b.id)}">${store.get(FAV).includes(b.id) ? "★ In your tour" : "☆ Add to your tour"}</button>
        <button class="btn small ghost tg-wide" data-cmp="${esc(b.id)}">${store.get(CMP).includes(b.id) ? "⇄ In compare" : "⇄ Add to compare"}</button>
        ${mapButton(b)}
        ${b.id === "Q39671" ? `<a class="btn small" href="${typeof IS_STATIC !== "undefined" && IS_STATIC ? "stonehenge.html" : "/stonehenge"}">🪨 Stonehenge in 3D</a>` : ""}
        ${CAN_EDIT ? '<button class="btn small ghost" id="edit_open">✎ Correct this record</button>' : ""}
      </div>
      ${b.description ? `<p class="lede">${esc(b.description)}</p>` : ""}
      <div class="chips">
        <span class="chip">${esc(b.category)}</span><span class="chip">${esc(b.period)}</span>
        ${b.nation ? `<span class="chip">${esc(b.nation)}</span>` : ""}
        <span class="chip">${esc(b.heritage_grade)}</span><span class="chip">${esc(b.status)}</span>
        ${b.curated ? '<span class="chip accent">On a Wikipedia oldest-buildings list</span>' : ""}
        ${b.oldest_of_type ? `<span class="chip accent">Among the oldest: ${esc(b.oldest_of_type)}</span>` : ""}
        ${b.landmark ? `<span class="chip accent">Landmark: ${esc(b.landmark)}</span>` : ""}
        ${b.date_confidence && b.date_confidence !== "Recorded" ? `<span class="chip warn">Date: ${esc(b.date_confidence)}</span>` : ""}
        ${b.edited ? '<span class="chip warn">Corrected by you</span>' : ""}
      </div>
      <dl>
        ${field("Date built", b.date_text)}
        ${field("Sort year", yearLabel(b.year_start))}
        ${field("Date source", b.date_source)}
        ${field("Date basis", b.date_confidence)}
        ${field("Date evidence", b.date_evidence)}
        ${b.date_check ? `<dt>Date check</dt><dd><span class="check-${esc(b.date_check.toLowerCase().replace(/ /g, "-"))}">${esc(b.date_check)}</span>${b.date_check_note ? ` · ${esc(b.date_check_note)}` : ""}</dd>` : ""}
        ${field("Address", address)}
        ${field("Administrative area", b.located_in)}
        ${field("County / district", [b.county, b.district].filter((v, i, a) => v && a.indexOf(v) === i).join(" / "))}
        ${coordsField(b.lat, b.lon)}
        ${field("Type (Wikidata)", b.classes)}
        ${field("Heritage designations", b.designations)}
        ${field("NHLE list entry", b.nhle_id)}
        ${field("HES reference", b.hes_id)}
        ${field("Cadw reference", b.cadw_id)}
        ${field("Irish National Monument no.", b.ie_nm_id)}
        ${field("Irish SMR no.", b.ie_smr_id)}
        ${field("NIAH reg. no.", b.ie_niah_id)}
        ${field("Architectural style", b.style)}
        ${field("Materials", b.materials)}
        ${field("Architect / builder", b.architect)}
        ${field("Religion", b.religion)}
        ${field("Dedicated to", b.dedication)}
        ${field("Condition", b.condition)}
        ${field("Height", b.height_m ? `${b.height_m} m` : "")}
      </dl>
      <div id="detail-edit"></div>
      ${b.user_notes ? `<h4>Your notes</h4><p>${esc(b.user_notes)}</p>` : ""}
      ${b.type_claim ? `<h4>"Oldest of its type" claim</h4><p>${esc(b.type_claim)}</p>` : ""}
      ${b.curated_notes ? `<h4>From Wikipedia's list of oldest buildings</h4><p>${esc(b.curated_notes)}</p>` : ""}
      ${b.register_notes ? `<h4>From the official register</h4><p>${esc(b.register_notes)}</p>
        ${b.register_source ? `<p class="hint">${esc(b.register_source)}</p>` : ""}` : ""}
      ${b.wikipedia_extract ? `<h4>About</h4>${b.wikipedia_extract.split(/\n+/).map((p) => `<p>${esc(p)}</p>`).join("")}` : ""}
      <div class="stories-box" data-stories="${esc(b.id)}"></div>
      <div class="timeline-box" data-timeline="${esc(b.id)}"></div>
      <div class="types-box" data-types-here="${esc(b.id)}"></div>
      <div class="trade-box" data-trade-here="${esc(b.id)}"></div>
      <div class="then-box" data-then="${esc(b.id)}"></div>
      ${b.lat != null ? `<div class="sky-box" data-sky="${esc(b.id)}" data-lat="${b.lat}" data-lon="${b.lon}" data-year="${b.year_start ?? ""}" data-name="${esc(b.name || "")}"${b.category_group === "Religious" ? ' data-church="1"' : ""}></div>` : ""}
      <div class="evidence-box" data-evidence="${esc(b.id)}"></div>
      ${b.lat != null ? `<p class="getting-there" data-transport="${b.lat},${b.lon}" data-visit="${esc(b.id)}"${b.category === "Public house / inn" ? ' data-pub="1"' : ""}></p>` : ""}
      <div class="links">${detailLinks(b)}${inModal ? `<a class="ext" href="${buildingUrl(b.id)}">Permalink</a>` : ""}</div>
      ${b.lat != null ? '<div id="detail-map" class="detail-map"></div>' : ""}
      <div id="detail-plan"></div>
      <div id="detail-oldmaps"></div>
      ${sourcesHTML(b)}
      <div id="detail-related"></div>
      <div id="detail-nearby"></div>
    </div></div>
    <div id="detail-gallery"></div>`;
}
