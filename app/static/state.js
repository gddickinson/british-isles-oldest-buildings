// Shared front-end state: API access, URL <-> filter state, favourites and compare lists.
const IS_STATIC = window.__STATIC__ === true || document.body.dataset.static === "1";
const CAN_EDIT = !IS_STATIC && document.body.dataset.edit === "1";
// the computer running the app (not another one on the home network, which is read-only: app/lan.py)
const THIS_MACHINE = !IS_STATIC && document.body.dataset.here === "1";

async function api(url) {
  if (window.STATIC_API) return window.STATIC_API(url);   // hosted static version
  const r = await fetch(url);
  if (!r.ok) throw new Error(`${r.status} ${url}`);
  return r.json();
}

function buildingUrl(id) {
  return IS_STATIC ? `index.html#${encodeURIComponent(id)}` : `/building/${encodeURIComponent(id)}`;
}

// The Map page centred and zoomed in on a record, marked with its name (map_page.js reads these);
// placeGroup also switches on that places layer
function mapUrl(rec, placeGroup) {
  const p = new URLSearchParams({ lat: (+rec.lat).toFixed(5), lon: (+rec.lon).toFixed(5), z: "17", mark: rec.name || "" });
  if (placeGroup) p.set("places", placeGroup);
  return `${IS_STATIC ? "map.html" : "/map"}?${p}`;
}

function mapButton(rec, placeGroup) {
  return rec.lat == null ? "" : `<a class="btn small ghost" href="${esc(mapUrl(rec, placeGroup))}" data-showmap="1"
    title="Open the map zoomed in on this location">🗺 Show on the map</a>`;
}

// ---- URL state ---------------------------------------------------------------
const MULTI_KEYS = ["category_group", "category", "period", "nation", "heritage_grade",
                    "date_confidence", "date_check", "status", "county"];
const SCALAR_KEYS = ["q", "year_min", "year_max", "story", "sort", "view", "lat", "lon", "radius",
                     "near_label", "color_by", "bucket", "bbox"];
const FLAG_KEYS = ["has_image", "curated", "oldest_only", "buildings_only", "edited", "map_area",
                   "landmarks_only", "early_only"];

function readUrlState() {
  const p = new URLSearchParams(location.search);
  const s = { facets: {} };
  SCALAR_KEYS.forEach((k) => { if (p.get(k)) s[k] = p.get(k); });
  FLAG_KEYS.forEach((k) => { s[k] = p.get(k) === "1"; });
  MULTI_KEYS.forEach((k) => { const v = p.getAll(k); if (v.length) s.facets[k] = v; });
  return s;
}

function stateToParams(s, { forApi = false } = {}) {
  const p = new URLSearchParams();
  SCALAR_KEYS.forEach((k) => {
    if (s[k] === undefined || s[k] === null || s[k] === "") return;
    if (forApi && ["view", "near_label", "color_by", "bucket"].includes(k)) return;
    if (forApi && k === "bbox" && !s.map_area) return;
    p.set(k, s[k]);
  });
  FLAG_KEYS.forEach((k) => { if (s[k] && !(forApi && k === "map_area")) p.set(k, "1"); });
  Object.entries(s.facets || {}).forEach(([k, vals]) => vals.forEach((v) => p.append(k, v)));
  return p;
}

function writeUrlState(s) {
  const qs = stateToParams(s).toString();
  history.replaceState(null, "", location.pathname + (qs ? "?" + qs : "") + location.hash);
}

// ---- favourites & compare (per-browser conveniences in localStorage) -----------
const store = {
  get(key) {
    try { return JSON.parse(localStorage.getItem(key) || "[]"); } catch (e) { return []; }
  },
  set(key, ids) {
    try { localStorage.setItem(key, JSON.stringify(ids)); } catch (e) { /* storage blocked */ }
    updateNavCounts();
  },
  toggle(key, id, max) {
    let ids = store.get(key);
    if (ids.includes(id)) ids = ids.filter((x) => x !== id);
    else { ids.push(id); if (max && ids.length > max) ids = ids.slice(-max); }
    store.set(key, ids);
    return ids.includes(id);
  },
};
const FAV = "bi_favourites", CMP = "bi_compare", CMP_MAX = 3;

function updateNavCounts() {
  const n = { trip: store.get(FAV).length, compare: store.get(CMP).length };
  document.querySelectorAll("[data-count]").forEach((el) => {
    const v = n[el.dataset.count];
    el.textContent = v ? `(${v})` : "";
  });
}
document.addEventListener("DOMContentLoaded", updateNavCounts);
updateNavCounts();

// Star / compare toggles anywhere on any page (cards, detail view, trip list)
document.addEventListener("click", (e) => {
  const fav = e.target.closest("[data-fav]"), cmp = e.target.closest("[data-cmp]");
  if (!fav && !cmp) return;
  e.preventDefault();
  e.stopPropagation();
  const el = fav || cmp;
  const id = fav ? fav.dataset.fav : cmp.dataset.cmp;
  const on = fav ? store.toggle(FAV, id) : store.toggle(CMP, id, CMP_MAX);
  document.querySelectorAll(fav ? `[data-fav="${CSS.escape(id)}"]` : `[data-cmp="${CSS.escape(id)}"]`)
    .forEach((b) => {
      b.classList.toggle("on", on);
      b.setAttribute("aria-pressed", on);
      if (b.classList.contains("tg-wide")) {
        b.textContent = fav ? (on ? "★ In your tour" : "☆ Add to your tour")
                            : (on ? "⇄ In compare" : "⇄ Add to compare");
      }
    });
  if (cmp && on && store.get(CMP).length === CMP_MAX) {
    el.title = "Compare holds 3 buildings; the oldest pick was dropped";
  }
}, true);

// Map background (see basemap.js): online street map locally with an offline fallback; the bundled
// offline map when hosted. opts.control adds the layer switcher.
function addBaseLayer(map, opts = {}) {
  Basemap.attach(map, opts);
}

// Installed app / offline use (local GUI): register the service worker (served at /sw.js)
if (!IS_STATIC && "serviceWorker" in navigator) {
  window.addEventListener("load", () => navigator.serviceWorker.register("/sw.js").catch(() => null));
}

// Dialog focus (accessibility): move focus into an opened dialog and give it back on close
let lastFocus = null;
function dialogOpened(modal) {
  lastFocus = document.activeElement;
  const card = modal.querySelector("[role=dialog]");
  if (card) card.setAttribute("aria-modal", "true");
  const close = modal.querySelector(".close");
  if (close) setTimeout(() => close.focus());
}
function dialogClosed() {
  if (lastFocus && lastFocus.focus) lastFocus.focus();
  lastFocus = null;
}

// Copy text to the clipboard (used where file downloads are unavailable)
async function copyText(text, button, done = "Copied") {
  const old = button.textContent;
  try { await navigator.clipboard.writeText(text); button.textContent = done; }
  catch (e) { button.textContent = "Copy failed"; }
  setTimeout(() => { button.textContent = old; }, 1600);
}
