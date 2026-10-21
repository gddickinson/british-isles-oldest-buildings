// Per-browser preferences (Settings page): appearance, catalogue and map defaults, units, history.
// Stored in localStorage "bi_prefs"; the theme/text size are also applied by an inline script in
// base.html before the page paints, so there is no flash of the wrong theme.
const Prefs = (() => {
  const KEY = "bi_prefs", RECENT = "bi_recent";
  const DEFAULTS = {
    theme: "system",          // system | light | dark
    textSize: 100,            // % of the base font size
    density: "comfortable",   // comfortable | compact
    motion: "system",         // system | reduce
    units: "km",              // km | mi
    defaultView: "gallery",   // gallery | table | map | timeline
    defaultSort: "oldest",    // oldest | newest | name | nation
    pageSize: 48,             // results per page in the catalogue
    mapBase: "online",        // online | satellite | offline
    cluster: true,            // group nearby markers
    recent: true,             // remember recently viewed records
    shortcuts: true,          // keyboard shortcuts
    approxMarker: true,       // "≈" before estimated dates
    pron: true,               // pronunciations under names in detail views
    pronNative: true,         // also names in Welsh, Gaelic, Irish, Manx … without a pronunciation
  };
  const read = () => { try { return JSON.parse(localStorage.getItem(KEY)) || {}; } catch (e) { return {}; } };
  const write = (v) => { try { localStorage.setItem(KEY, JSON.stringify(v)); } catch (e) { /* storage blocked */ } };

  function get(k) { const v = read(); return k in v ? v[k] : DEFAULTS[k]; }
  function all() { return { ...DEFAULTS, ...read() }; }
  function set(k, val) {
    const v = read();
    if (val === DEFAULTS[k]) delete v[k]; else v[k] = val;
    write(v);
    apply();
    window.dispatchEvent(new CustomEvent("prefs-changed", { detail: { key: k, value: val } }));
  }
  function reset() { write({}); apply(); window.dispatchEvent(new CustomEvent("prefs-changed", { detail: {} })); }

  // theme / size / density / motion on <html>; ?_theme=dark in the URL wins (screenshots)
  function apply() {
    const root = document.documentElement, p = all();
    const forced = new URLSearchParams(location.search).get("_theme");
    const theme = forced || p.theme;
    if (theme === "light" || theme === "dark") root.dataset.theme = theme; else delete root.dataset.theme;
    root.style.fontSize = p.textSize !== 100 ? p.textSize + "%" : "";
    root.dataset.density = p.density;
    root.dataset.motion = p.motion;
    if (new URLSearchParams(location.search).get("_shot")) root.dataset.shot = "1";
  }
  function effectiveTheme() {
    const t = document.documentElement.dataset.theme;
    return t || (matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light");
  }
  function toggleTheme() { set("theme", effectiveTheme() === "dark" ? "light" : "dark"); }

  // distances: everything is computed in km; this formats in the chosen unit
  function dist(km, digits = 1) {
    if (km == null || isNaN(km)) return "";
    return get("units") === "mi" ? `${(km * 0.621371).toFixed(digits)} mi` : `${(+km).toFixed(digits)} km`;
  }
  // marker cluster options honour the "group nearby markers" preference
  function cluster(opts) { return get("cluster") ? opts : { ...opts, disableClusteringAtZoom: 1 }; }

  // recently viewed records: [{id, type: building|place|person, name, t}]
  const recent = {
    list() { try { return JSON.parse(localStorage.getItem(RECENT)) || []; } catch (e) { return []; } },
    add(id, type, name) {
      if (!get("recent") || !id) return;
      const l = recent.list().filter((r) => !(r.id === id && r.type === type));
      l.unshift({ id, type, name: name || id, t: Date.now() });
      try { localStorage.setItem(RECENT, JSON.stringify(l.slice(0, 30))); } catch (e) { /* blocked */ }
    },
    clear() { try { localStorage.removeItem(RECENT); } catch (e) { /* blocked */ } },
  };

  // everything this browser stores, for backup / moving to another browser
  const STORE_KEYS = [KEY, RECENT, "bi_favourites", "bi_compare", "bi_map_layers", "bi_map_base", "bi_map_historic", "bi_tour_opts", "bi_saved_tours"];
  function exportAll() {
    const out = { app: "british-isles-oldest-buildings", saved: new Date().toISOString(), data: {} };
    STORE_KEYS.forEach((k) => { try { const v = localStorage.getItem(k); if (v !== null) out.data[k] = JSON.parse(v); } catch (e) { /* skip */ } });
    return out;
  }
  function importAll(obj) {
    if (!obj || !obj.data) throw new Error("Not a settings file from this app.");
    Object.entries(obj.data).forEach(([k, v]) => { if (STORE_KEYS.includes(k)) localStorage.setItem(k, JSON.stringify(v)); });
    apply();
  }

  apply();
  matchMedia("(prefers-color-scheme: dark)").addEventListener?.("change", () => window.dispatchEvent(new Event("theme-changed")));
  return { DEFAULTS, get, set, all, reset, apply, effectiveTheme, toggleTheme, dist, cluster, recent, exportAll,
           importAll, STORE_KEYS };
})();
