// Export menu (top bar): data for the current filters, screenshots, print/PDF, copy link.
// Locally the server writes the files (app/export_api.py, app/screenshot.py); in the hosted copy
// the same CSV / JSON / GeoJSON / KML files are built here in the browser.
const ExportMenu = (() => {
  const GEO_FIELDS = {
    buildings: ["id", "name", "category", "date_text", "year_start", "period", "nation", "county", "locality",
                "heritage_grade", "status", "wikidata_id"],
    places: ["id", "name", "kind_label", "kind_group", "type", "date_text", "year_start", "period", "nation",
             "locality", "source", "url"],
  };
  const FORMATS = [["csv", "CSV (spreadsheet)"], ["json", "JSON"], ["geojson", "GeoJSON (GIS)"], ["kml", "KML (Google Earth)"]];
  const page = () => document.body.dataset.page || "catalogue";
  const query = () => { const p = new URLSearchParams(location.search); ["view", "_theme", "_shot"].forEach((k) => p.delete(k)); return p.toString(); };

  // ---- serialisers (same output as app/export_api.py) -----------------------------
  const csvCell = (v) => { if (v === null || v === undefined) return ""; const s = typeof v === "object" ? JSON.stringify(v) : String(v); return /[",\n\r]/.test(s) ? `"${s.replace(/"/g, '""')}"` : s; };
  function toCSV(rows) {
    const cols = [...new Set(rows.flatMap((r) => Object.keys(r)))];
    return [cols.join(","), ...rows.map((r) => cols.map((c) => csvCell(r[c])).join(","))].join("\r\n") + "\r\n";
  }
  const pick = (r, f) => Object.fromEntries(f.map((k) => [k, r[k] ?? null]));
  const toGeoJSON = (rows, f) => JSON.stringify({ type: "FeatureCollection", features: rows.filter((r) => r.lat != null && r.lon != null)
    .map((r) => ({ type: "Feature", geometry: { type: "Point", coordinates: [r.lon, r.lat] }, properties: pick(r, f) })) });
  const x = (s) => String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
  const toKML = (rows, f, title) => `<?xml version="1.0" encoding="UTF-8"?><kml xmlns="http://www.opengis.net/kml/2.2"><Document><name>${x(title)}</name>${
    rows.filter((r) => r.lat != null).map((r) => `<Placemark><name>${x(r.name || r.id)}</name><description><![CDATA[${
      f.filter((k) => !["id", "name"].includes(k) && r[k] != null && r[k] !== "").map((k) => `${x(k)}: ${x(r[k])}`).join("<br>")}]]></description><Point><coordinates>${r.lon},${r.lat}</coordinates></Point></Placemark>`).join("")}</Document></kml>`;

  function save(text, name, type) {
    const a = Object.assign(document.createElement("a"), { href: URL.createObjectURL(new Blob([text], { type })), download: name });
    document.body.append(a); a.click(); a.remove();
    setTimeout(() => URL.revokeObjectURL(a.href), 4000);
  }

  async function exportStatic(kind, fmt) {
    UI.toast("Preparing the file…");
    const q = query();
    const url = kind === "buildings" ? "/api/export_rows?" + q : `/api/${kind}/export?` + q;
    const rows = kind === "pronunciations"
      ? (await Pron.search({ ...Object.fromEntries(new URLSearchParams(q)), limit: 1e7 })).rows
      : await api(url);
    const name = `british_isles_${kind}.${fmt}`;
    if (fmt === "csv") save(toCSV(rows), name, "text/csv");
    else if (fmt === "json") save(JSON.stringify(rows), name, "application/json");
    else if (fmt === "geojson") save(toGeoJSON(rows, GEO_FIELDS[kind]), name, "application/geo+json");
    else save(toKML(rows, GEO_FIELDS[kind], `British Isles ${kind}`), name, "application/vnd.google-earth.kml+xml");
    UI.toast(`Saved ${rows.length.toLocaleString()} ${kind}`);
  }

  function dataItems(kind, label) {
    const fmts = kind === "people" || kind === "pronunciations" ? FORMATS.slice(0, 2) : FORMATS;
    const q = query();
    return [{ sep: `${label}${q ? " (current filters)" : ""}` }].concat(fmts.map(([fmt, name]) => IS_STATIC
      ? { label: name, action: () => exportStatic(kind, fmt).catch((e) => UI.toast("Export failed: " + e.message)) }
      : { label: name, href: `/export/${kind}.${fmt}${q ? "?" + q : ""}`, download: true }));
  }

  // ---- screenshots -------------------------------------------------------------------
  async function screenshot(w, h) {
    if (IS_STATIC) return;
    const path = location.pathname + location.search + location.hash;
    UI.toast("Taking a screenshot… (a few seconds)", 6000);
    const params = new URLSearchParams({ path, w, h, theme: Prefs.effectiveTheme(), scale: devicePixelRatio > 1 ? 2 : 1 });
    const r = await fetch("/api/screenshot?" + params);
    if (!r.ok) { const j = await r.json().catch(() => ({})); UI.toast((j.problems || ["Screenshot failed"]).join(" "), 6000); return; }
    const blob = await r.blob();
    const a = Object.assign(document.createElement("a"), { href: URL.createObjectURL(blob),
      download: `british_isles_${(location.pathname.replace(/^\/|\.html$/g, "").replace(/\//g, "_") || "catalogue")}.png` });
    document.body.append(a); a.click(); a.remove();
    UI.toast("Screenshot saved to your downloads");
  }

  function copyLink() {
    const text = location.href.replace(/[?&]_(theme|shot)=[^&#]*/g, "");
    (navigator.clipboard ? navigator.clipboard.writeText(text) : Promise.reject()).then(
      () => UI.toast("Link copied"), () => prompt("Copy this link:", text));
  }

  function items() {
    const p = page(), out = [];
    if (p === "catalogue") out.push(...dataItems("buildings", "Buildings"));
    else if (p === "places") out.push(...dataItems("places", "Places"));
    else if (p === "people") out.push(...dataItems("people", "People"));
    else if (p === "pron") out.push(...dataItems("pronunciations", "Pronunciations"));
    else out.push({ sep: "All data" }, ...[["buildings", "Buildings"], ["places", "Places"], ["people", "People"]]
      .map(([k, l]) => (IS_STATIC ? { label: `${l} (CSV)`, action: () => exportStatic(k, "csv") }
                                  : { label: `${l} (CSV)`, href: `/export/${k}.csv`, download: true })));
    const noShot = "Not available in the hosted copy: use your browser's or system's screenshot tool (Shift+⌘+4 on a Mac).";
    out.push({ sep: "Picture & print" },
      { label: "Screenshot of this view", disabled: IS_STATIC, title: IS_STATIC ? noShot : "Opens this address in a hidden browser at your window size (open dialogs and map position may differ)",
        action: () => screenshot(innerWidth, innerHeight) },
      { label: "Screenshot, phone size", disabled: IS_STATIC, title: IS_STATIC ? noShot : "390 × 844", action: () => screenshot(390, 844) },
      { label: "Print or save as PDF", key: "⌘P", action: () => print() },
      { label: "Copy link to this view", action: copyLink });
    return out;
  }
  return { items, toCSV, toGeoJSON, toKML };
})();
