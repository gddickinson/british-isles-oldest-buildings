// Extensive GUI review in headless Chrome: every page and its maps, every background and overlay layer,
// every historic map, places layers, pop-ups and the hosted copy. Writes a JSON report and screenshots.
//
//   node tests/ui_review.mjs --base http://127.0.0.1:5050 --out runs/ui_review [--only maps,layers]
//   node tests/ui_review.mjs --base http://127.0.0.1:8099 --static --out runs/ui_review_static
//
// Groups: pages, popups, maps, layers, historic, places, extras (static: pages, maps, layers, historic).
import { mkdirSync, writeFileSync, existsSync } from "node:fs";
import { join } from "node:path";
import { launch, sleep } from "./cdp.mjs";

const arg = (k, d) => { const i = process.argv.indexOf(k); return i > 0 ? process.argv[i + 1] : d; };
const BASE = arg("--base", "http://127.0.0.1:5050"), OUT = arg("--out", "runs/ui_review");
const STATIC = process.argv.includes("--static"), ONLY = arg("--only", "") ? arg("--only").split(",") : null;
const CHROME = arg("--chrome", "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome");
const P = (p) => !STATIC ? p : p.startsWith("/building/") ? "/index.html#" + p.slice(10)
  : p.replace(/^\/$/, "/index.html").replace(/^\/(\w+)(\?|$)/, "/$1.html$2");
mkdirSync(OUT, { recursive: true });
const report = [];

// Every Leaflet map on the page: size, tiles loaded, whether the offline canvas has paint
const MAPS_JS = `[...document.querySelectorAll('.leaflet-container')].map((el) => {
  const r = el.getBoundingClientRect();
  const tiles = [...el.querySelectorAll('.leaflet-tile-pane img.leaflet-tile')];
  const hist = [...el.querySelectorAll('.leaflet-historic-pane img.leaflet-tile')];
  const ok = (a) => a.filter((i) => i.complete && i.naturalWidth > 0).length;
  let painted = null;
  const c = el.querySelector('.leaflet-basemap-pane canvas');
  if (c && c.width && c.height) {
    const d = c.getContext('2d').getImageData(0, 0, c.width, c.height).data; let n = 0, k = 0;
    for (let i = 3; i < d.length; i += 4 * 97) { k++; if (d[i] > 0) n++; }
    painted = Math.round(100 * n / k);
  }
  return { id: el.id || el.className.split(' ')[0], w: Math.round(r.width), h: Math.round(r.height),
           visible: r.width > 20 && r.height > 20 && el.offsetParent !== null, outline: el.classList.contains('outline-map'),
           tiles: tiles.length, tilesOk: ok(tiles), hist: hist.length, histOk: ok(hist), painted,
           markers: el.querySelectorAll('.leaflet-marker-icon').length,
           vectors: el.querySelectorAll('svg path.leaflet-interactive').length + el.querySelectorAll('.leaflet-overlay-pane canvas').length };
})`;
const mapOk = (m) => m.visible && (m.tilesOk > 0 || (m.outline && m.painted > 0));

function bad(page, sameOrigin = true) {
  return [...page.requests.values()].filter((q) => (!sameOrigin || q.url.startsWith(BASE))
    && ((q.status && q.status >= 400) || (q.failed && !/ERR_ABORTED|ERR_BLOCKED_BY_CLIENT/.test(q.failed))))
    .map((q) => `${q.status || q.failed} ${q.url.replace(BASE, "")}`.slice(0, 160));
}

async function record(name, page, extra = {}) {
  const shot = join(OUT, name.replace(/[^a-z0-9_.-]+/gi, "_") + ".jpg");
  try { await page.shot(shot); } catch (e) { /* page gone */ }
  const entry = { name, ok: true, errors: page.errors.slice(0, 5), failed: bad(page).slice(0, 8), shot, ...extra };
  if (entry.errors.length || entry.failed.length || extra.problem) entry.ok = false;
  report.push(entry);
  console.log(`${entry.ok ? "ok  " : "FAIL"} ${name}${extra.problem ? " — " + extra.problem : ""}${entry.errors.length ? " — " + entry.errors[0] : ""}${entry.failed.length ? " — " + entry.failed[0] : ""}`);
  return entry;
}

async function setStorage(page, kv) {
  await page.goto(BASE + P("/help"), 300);
  await page.eval(`(() => { localStorage.clear(); ${Object.entries(kv).map(([k, v]) => `localStorage.setItem(${JSON.stringify(k)}, ${JSON.stringify(JSON.stringify(v))});`).join("")} })()`);
}

const PAGES = [
  ["catalogue", "/", "document.querySelectorAll('.card').length"],
  ["catalogue_table", "/?view=table", "document.querySelectorAll('#rows tr').length"],
  ["catalogue_map", "/?view=map", "maps"],
  ["catalogue_timeline", "/?view=timeline", "document.querySelectorAll('#timeline svg rect').length"],
  ["building_outline_plan", "/building/Q1003041", "maps"],
  ["building_story", "/building/Q1529151", "document.querySelectorAll('.story').length"],
  ["map_page", "/map", "maps"],
  ["places_list", "/places", "document.querySelectorAll('[data-place]').length"],
  ["places_map", "/places?view=map", "maps"],
  ["people", "/people", "document.querySelectorAll('[data-person], .person').length"],
  ["pronunciation", "/pronunciation?q=ll", "document.querySelectorAll('.ipa, .respell').length"],
  ["stories", "/stories", "maps"],
  ["tours", "/tours", "maps"],
  ["tour_builder", "/tours?tab=build", "maps"],
  ["history", "/history", "maps"],
  ["quiz", "/quiz", "document.querySelectorAll('.quiz-choices button').length"],
  ["oldest", "/oldest", "document.querySelectorAll('.ex').length"],
  ["stats", "/stats", "document.querySelectorAll('svg').length"],
  ["compare", "/compare", "document.querySelectorAll('table, .compare-grid').length"],
  ["data", "/data", "document.querySelectorAll('#g_tiles .tile').length"],
  ["settings", "/settings", "document.querySelectorAll('.set-card').length"],
  ["help", "/help", "document.querySelectorAll('section').length"],
];

async function pages(page) {
  await setStorage(page, { bi_compare: ["Q1003041", "Q1018590"], bi_favourites: ["Q1003041", "Q1018590", "Q1025082"] });
  for (const [name, path, probe] of PAGES) {
    await page.goto(BASE + P(path), 5000);
    if (probe === "maps") {
      const maps = await page.eval(MAPS_JS);
      const vis = maps.filter((m) => m.visible);
      const broken = vis.filter((m) => !mapOk(m));
      await record("page_" + name, page, { maps, problem: !vis.length ? "no visible map" : broken.length ? `blank map: ${JSON.stringify(broken[0])}` : null });
    } else {
      const n = await page.eval(probe).catch((e) => -1);
      await record("page_" + name, page, { count: n, problem: n > 0 ? null : `nothing shown (${probe})` });
    }
  }
}

async function popups(page) {
  // catalogue card -> modal map; places card -> modal map; person; Show on the map
  for (const [name, path, sel, mapId] of [["catalogue_modal", "/?q=Alan%20Stevenson%20House", ".card", "detail-map"],
    ["catalogue_modal_outline", "/?q=Buildwas%20Abbey", ".card", "detail-map"],
    ["places_modal", "/places?q=Mary%20Rose", "[data-place]", "place-map"],
    ["people_modal", "/people?q=Wordsworth", "[data-person]", null]]) {
    await page.goto(BASE + P(path), 4000);
    const clicked = await page.eval(`(() => { const c = document.querySelector(${JSON.stringify(sel)}); if (!c) return false; c.click(); return true; })()`);
    await sleep(4000);
    const maps = await page.eval(MAPS_JS);
    const m = mapId ? maps.find((x) => x.id === mapId) : null;
    const modalShown = await page.eval("!!document.querySelector('.modal:not(.hidden)')");
    await record("popup_" + name, page, { maps, problem: !clicked ? "nothing to click" : !modalShown ? "no pop-up"
      : mapId && !m ? "no map in pop-up" : m && !mapOk(m) ? `blank pop-up map ${JSON.stringify(m)}` : null });
  }
  // Show on the map from a detail page
  await page.goto(BASE + P("/building/Q17574990"), 3000);
  const href = await page.eval("document.querySelector('[data-showmap]')?.getAttribute('href')");
  if (!href) { await record("show_on_map", page, { problem: "no Show on the map button" }); return; }
  await page.goto(new URL(href, BASE + "/").href, 5000);
  const c = await page.eval("(() => { const c = exMap.getCenter(); return [c.lat, c.lng, exMap.getZoom(), document.querySelectorAll('.map-mark').length, document.querySelectorAll('.map-mark-label').length]; })()");
  await record("show_on_map", page, { center: c, problem: Math.abs(c[0] - 56.4487) > 0.001 || c[2] < 15 || !c[3] || !c[4] ? `centre/zoom/mark wrong ${c}` : null });
}

// Map page with one background and the chosen overlays; counts what the basemap drew
const COUNT_JS = `(() => { let paths = 0, labels = 0; exMap.eachLayer((l) => {
  if (l instanceof L.Path && l.options.renderer && l.options.renderer.options.pane === 'basemap') paths++;
  else if (l instanceof L.Marker && /map-label/.test((l.options.icon && l.options.icon.options.className) || '')) labels++; });
  return { paths, labels }; })()`;
const LAYER_VIEWS = {   // key: [lat, lon, zoom] where the layer has something to show
  counties: [54.0, -1.5, 8], historic_counties: [53.5, -2.0, 8], parks: [54.45, -3.1, 9], rivers: [54.0, -1.5, 8],
  roads: [53.5, -1.5, 8], minor: [53.96, -1.08, 12], streams: [54.45, -3.1, 12], lakes: [54.37, -2.93, 11],
  walking: [53.35, -1.8, 11], cycling: [53.96, -1.08, 10], roman: [52.4, -1.4, 9], buried: [51.517, -0.108, 13],
  rail: [53.5, -1.5, 9], trails: [54.0, -2.0, 8], towns: [53.5, -1.5, 9], landscape: [54.45, -3.1, 10],
  airports: [53.5, -1.5, 7], stations: [51.51, -0.12, 13], streets: [53.96, -1.08, 14],
};

async function layers(page) {
  const keys = Object.keys(LAYER_VIEWS).filter((k) => !(STATIC && k === "streets"));
  for (const key of keys) {
    const [lat, lon, z] = LAYER_VIEWS[key];
    await setStorage(page, { bi_map_layers: [], bi_map_base: "offline" });
    await page.goto(BASE + P(`/map?lat=${lat}&lon=${lon}&z=${z}`), 5000);
    const before = await page.eval(COUNT_JS);
    await setStorage(page, { bi_map_layers: [key], bi_map_base: "offline" });
    await page.goto(BASE + P(`/map?lat=${lat}&lon=${lon}&z=${z}`), key === "streets" ? 8000 : 6000);
    const after = await page.eval(COUNT_JS), maps = await page.eval(MAPS_JS);
    let drew = after.paths - before.paths + after.labels - before.labels;
    if (key === "streets") drew = await page.eval("document.querySelectorAll('.leaflet-streets-pane canvas, .leaflet-streets-pane .leaflet-tile').length");
    await record("layer_" + key, page, { before, after, maps, problem: drew > 0 ? null : "layer drew nothing here" });
  }
  // overlays over the online street map (routes, borders, Roman roads… marked online in basemap.js)
  if (!STATIC) for (const key of ["counties", "historic_counties", "parks", "walking", "cycling", "roman", "buried", "trails", "stations"]) {
    const [lat, lon, z] = LAYER_VIEWS[key];
    await setStorage(page, { bi_map_layers: [key], bi_map_base: "online" });
    await page.goto(BASE + P(`/map?lat=${lat}&lon=${lon}&z=${z}`), 6000);
    const after = await page.eval(COUNT_JS), maps = await page.eval(MAPS_JS);
    await record("online_overlay_" + key, page, { after, maps, problem: after.paths + after.labels > 0 && maps[0].tilesOk > 0 ? null : "overlay or street map missing" });
  }
  await setStorage(page, {});
  await page.goto(BASE + P("/map?lat=53.96&lon=-1.08&z=13"), 6000);
  await record("online_defaults_york", page, { after: await page.eval(COUNT_JS) });
  await page.goto(BASE + P("/map?lat=54.3&lon=-2.5&z=8"), 6000);
  await record("online_defaults_north", page, { after: await page.eval(COUNT_JS) });
  // online background
  await setStorage(page, { bi_map_base: "online" });
  await page.goto(BASE + P("/map?lat=53.96&lon=-1.08&z=13"), 7000);
  const maps = await page.eval(MAPS_JS);
  await record("background_online", page, { maps, problem: STATIC ? null : maps[0].tilesOk > 0 ? null : "no street-map tiles loaded" });
  // satellite background with an overlay, and switching to it from the layer panel
  if (!STATIC) {
    await setStorage(page, { bi_map_base: "satellite", bi_map_layers: ["roman"] });
    await page.goto(BASE + P("/map?lat=54.99&lon=-2.38&z=13"), 8000);
    const sm = await page.eval(MAPS_JS), sc = await page.eval(COUNT_JS);
    const esri = page.reqs("arcgisonline.com").filter((q) => q.status === 200).length;
    await record("background_satellite", page, { maps: sm, esri, problem: esri > 0 && sm[0].tilesOk > 0 && sc.paths > 0 ? null : `satellite tiles ${esri}, overlay paths ${sc.paths}` });
    await setStorage(page, { bi_map_base: "online" });
    await page.goto(BASE + P("/map?lat=51.508&lon=-0.076&z=16"), 4000);
    await page.eval("document.querySelector('.ml-toggle').click(); const r = document.querySelector('input[name=ml-base][value=satellite]'); r.checked = true; r.dispatchEvent(new Event('change', { bubbles: true }))");
    await sleep(5000);
    const sw = await page.eval("({ saved: localStorage.getItem('bi_map_base'), esri: [...document.querySelectorAll('.leaflet-tile-pane img')].filter((i) => /arcgisonline/.test(i.src) && i.naturalWidth).length, osm: [...document.querySelectorAll('.leaflet-tile-pane img')].filter((i) => /openstreetmap/.test(i.src)).length })");
    await record("background_satellite_switch", page, { ...sw, problem: sw.esri > 0 && sw.osm === 0 && /satellite/.test(sw.saved) ? null : JSON.stringify(sw) });
  }
  // dark theme offline
  await setStorage(page, { bi_map_base: "offline", bi_prefs: { theme: "dark" } });
  await page.goto(BASE + P("/map?lat=54.3&lon=-3&z=8"), 5000);
  const dm = await page.eval(MAPS_JS);
  await record("background_offline_dark", page, { maps: dm, problem: mapOk(dm[0]) ? null : "blank" });
}

async function historic(page) {
  const conf = await fetch(BASE + (STATIC ? "/static" : "/static") + "/data/historic/layers.json").then((r) => r.json());
  const list = conf.layers.filter((l) => !STATIC || l.bundle);
  for (const l of list) {
    const [w, s, e, n] = l.bounds;
    let lat = (s + n) / 2, lon = (w + e) / 2;
    if (l.key.startsWith("ireland6")) { lat = 53.35; lon = -6.26; }          // Dublin (county tilesets)
    if (l.key === "os6inch" || l.key === "os1inch") { lat = 53.96; lon = -1.08; }
    const z = STATIC ? l.bundle[1] : Math.max(l.min || 5, Math.min(l.max || 12, l.key.includes("6") ? 14 : 10));
    await setStorage(page, { bi_map_base: "offline", bi_map_layers: [], bi_map_historic: { key: l.key, opacity: 0.8 } });
    await page.goto(BASE + P(`/map?lat=${lat.toFixed(3)}&lon=${lon.toFixed(3)}&z=${z}`), 9000);
    const maps = await page.eval(MAPS_JS), m = maps[0];
    await record("historic_" + l.key, page, { z, maps, problem: m.histOk > 0 ? null : `no historic tiles (${m.hist} requested)` });
  }
  if (!STATIC) {
    await setStorage(page, { bi_map_base: "online", bi_map_historic: { key: "__towns", opacity: 0.8 } });
    await page.goto(BASE + "/map?lat=55.951&lon=-3.19&z=15", 9000);
    const m = (await page.eval(MAPS_JS))[0];
    await record("historic_town_plans", page, { maps: [m], problem: m.histOk > 0 ? null : "no town plan tiles at Edinburgh" });
  }
}

async function places(page) {
  const groups = await (async () => { await page.goto(BASE + P("/map"), 3000); return page.eval("PLACE_GROUPS"); })();
  for (const g of groups) {
    await setStorage(page, { bi_map_base: "offline" });
    await page.goto(BASE + P("/map?lat=54.3&lon=-3&z=6"), 3000);
    await page.eval(`(() => { const i = [...document.querySelectorAll('#ex_places input')].find((x) => x.value === ${JSON.stringify(g)}); i.click(); })()`);
    await sleep(4000);
    const n = await page.eval("pCluster.getLayers().length");
    await record("places_layer_" + g, page, { count: n, problem: n > 0 ? null : "no markers" });
  }
}

async function extras(page) {
  // mobile width, tours with a route and elevation, exports, setup redirect when a database exists
  await page.send("Emulation.setDeviceMetricsOverride", { width: 390, height: 844, deviceScaleFactor: 1, mobile: true });
  for (const [n, p] of [["mobile_catalogue", "/"], ["mobile_map", "/map"], ["mobile_tours", "/tours"]]) {
    await page.goto(BASE + P(p), 4000);
    const over = await page.eval("document.documentElement.scrollWidth - innerWidth");
    await record(n, page, { overflow: over, problem: over > 2 ? `page ${over}px wider than the screen` : null });
  }
  await page.send("Emulation.setDeviceMetricsOverride", { width: 1280, height: 900, deviceScaleFactor: 1, mobile: false });
  await page.goto(BASE + P("/tours"), 4000);
  await page.eval("document.querySelector('.tour-card')?.click()");
  await sleep(5000);
  const t = await page.eval("({ route: document.querySelectorAll('#tr_map path.leaflet-interactive').length, stops: document.querySelectorAll('.tour-stops li').length, profile: document.querySelectorAll('.elev svg, .profile svg, svg.elev').length })");
  await record("tour_open", page, { ...t, problem: t.route && t.stops ? null : "tour route or stops missing" });
  if (!STATIC) {
    for (const u of ["/export/buildings.csv?q=castle", "/export/places.geojson?kind_group=Maritime%20heritage", "/api/jobs", "/setup"]) {
      const r = await fetch(BASE + u, { redirect: "manual" });
      report.push({ name: "http " + u, ok: r.status < 400, status: r.status });
      console.log(`${r.status < 400 ? "ok  " : "FAIL"} http ${u} ${r.status}`);
    }
  }
}

// Searching ranks name matches first (bidb.db.name_rank / static nameRank)
async function search(page) {
  for (const [path, sel, want] of [["/?q=Tower%20of%20London", ".card h3", "Tower of London"],
    ["/?q=Westminster%20Abbey", ".card h3", "Westminster Abbey"],
    ["/places?q=Mary%20Rose", "[data-place]", "Mary Rose"]]) {
    await page.goto(BASE + P(path), 4000);
    const first = await page.eval(`(document.querySelector(${JSON.stringify(sel)})?.innerText || "").split("\\n").map((x) => x.trim()).filter(Boolean).slice(0, 3).join(" | ")`);
    await record("search " + path, page, { first, problem: first.includes(want) ? null : `first result: ${first}` });
  }
}

// Interactions: tour builder, filters, near a place, quick search, theme, quiz, plan overlay, layer panel
async function interact(page) {
  const t = async (name, fn) => {
    let problem = null, info = null;
    try { info = await fn(); if (typeof info === "string") { problem = info; info = null; } }
    catch (e) { problem = "crashed: " + String(e).slice(0, 160); }
    await record("interact_" + name, page, { info, problem });
  };
  const ev = (js) => page.eval(js);
  await setStorage(page, { bi_favourites: ["Q17530565", "Q2647826", "Q6818359"] });
  await t("tour_builder", async () => {
    await page.goto(BASE + P("/tours?tab=build"), 7000);
    const r = await ev("({ stops: document.querySelectorAll('#tb_list li').length, route: document.querySelectorAll('#tb_map path.leaflet-interactive').length, total: document.querySelector('#tb_total')?.innerText || '' })");
    return r.stops === 3 && r.route > 0 && /km|mi/.test(r.total) ? r : `stops ${r.stops}, route ${r.route}, total "${r.total}"`;
  });
  await t("facet_filter", async () => {
    await page.goto(BASE + P("/"), 4000);
    const before = await ev("document.querySelector('#total').innerText");
    await ev("[...document.querySelectorAll('[data-facet=nation] input')].find((i) => i.value === 'Wales').click()");
    await sleep(2500);
    const after = await ev("document.querySelector('#total').innerText");
    return after !== before && /nation=Wales/.test(await ev("location.search")) ? { before, after } : `total ${before} -> ${after}`;
  });
  await t("near_place", async () => {
    await page.goto(BASE + P("/"), 4000);
    await ev("document.querySelector('#near_q').value = 'York'; document.querySelector('#near_go').click()");
    await sleep(4000);
    const r = await ev("({ status: document.querySelector('#near_status').innerText, first: document.querySelector('.card .meta:nth-of-type(3)')?.innerText || document.querySelector('.card')?.innerText.slice(0, 80) })");
    return /York/i.test(r.status) ? r : `status "${r.status}"`;
  });
  await t("load_more", async () => {
    await page.goto(BASE + P("/"), 4000);
    const a = await ev("document.querySelectorAll('.card').length");
    await ev("document.querySelector('#more').click()"); await sleep(2500);
    const b = await ev("document.querySelectorAll('.card').length");
    return b > a ? { a, b } : `cards ${a} -> ${b}`;
  });
  await t("quick_search", async () => {
    await page.goto(BASE + P("/map"), 3000);
    await ev("document.dispatchEvent(new KeyboardEvent('keydown', { key: 'k', metaKey: true, bubbles: true }))"); await sleep(500);
    await ev("const q = document.querySelector('#pal-q'); q.value = 'tintern'; q.dispatchEvent(new Event('input', { bubbles: true }))"); await sleep(2500);
    const items = await ev("[...document.querySelectorAll('#pal-list li')].map((l) => l.innerText).slice(0, 5)");
    return items.some((x) => /Tintern/i.test(x)) ? { items } : `palette items: ${JSON.stringify(items)}`;
  });
  await t("theme_toggle", async () => {
    await setStorage(page, {});
    await page.goto(BASE + P("/"), 2500);
    const a = await ev("getComputedStyle(document.body).backgroundColor");
    await ev("document.querySelector('.tb-btn[title^=\"Light\"]').click()"); await sleep(500);
    const b = await ev("getComputedStyle(document.body).backgroundColor");
    return a !== b ? { a, b } : `background unchanged ${a}`;
  });
  await t("quiz_answer", async () => {
    await page.goto(BASE + P("/quiz"), 4000);
    await ev("document.querySelector('.quiz-choices button').click()"); await sleep(800);
    const r = await ev("({ next: !!document.querySelector('#qz_next'), marked: document.querySelectorAll('.quiz-choices .right, .quiz-choices .wrong, .quiz-choices [class*=correct]').length })");
    return r.next ? r : "no feedback after answering";
  });
  if (!STATIC) await t("plan_overlay", async () => {
    await page.goto(BASE + P("/building/Q1003041"), 5000);
    const has = await ev("!!document.querySelector('#plan_overlay')");
    if (!has) return "no plan button";
    await ev("document.querySelector('#plan_overlay').click()"); await sleep(3000);
    const n = await ev("document.querySelectorAll('#detail-map .leaflet-image-layer, #detail-map img.leaflet-image-layer').length");
    return n ? { overlays: n } : "plan not laid over the map";
  });
  await t("layer_panel_toggle", async () => {
    await setStorage(page, { bi_map_base: "offline", bi_map_layers: [] });
    await page.goto(BASE + P("/map?lat=52.4&lon=-1.4&z=9"), 4000);
    await ev("document.querySelector('.ml-toggle').click()"); await sleep(300);
    const before = (await ev(COUNT_JS)).paths;
    await ev("document.querySelector('.ml-overlays input[value=roman]').click()"); await sleep(3000);
    const after = (await ev(COUNT_JS)).paths, saved = await ev("localStorage.getItem('bi_map_layers')");
    await ev("document.querySelector('.ml-overlays input[value=roman]').click()"); await sleep(800);
    const off = (await ev(COUNT_JS)).paths;
    return after > before && off === before && /roman/.test(saved) ? { before, after, off } : `paths ${before} -> ${after} -> ${off}, saved ${saved}`;
  });
  await t("historic_via_panel", async () => {
    await setStorage(page, { bi_map_base: "offline" });
    await page.goto(BASE + P("/map?lat=53.96&lon=-1.08&z=8"), 4000);
    await ev("document.querySelector('.ml-toggle').click(); const s = document.querySelector('.ml-hsel'); s.value = 'bartholomew'; s.dispatchEvent(new Event('change'))");
    await sleep(7000);
    const m = (await ev(MAPS_JS))[0];
    return m.histOk > 0 ? { hist: m.histOk } : `historic tiles ${m.histOk}/${m.hist}`;
  });
  await t("town_finder", async () => {
    await page.goto(BASE + P("/map"), 3000);
    await ev("document.querySelector('#ex_q').value = 'Whitby'; document.querySelector('#ex_go').click()"); await sleep(1500);
    const c = await ev("[exMap.getCenter().lat, exMap.getCenter().lng]");
    return Math.abs(c[0] - 54.486) < 0.05 && Math.abs(c[1] + 0.615) < 0.05 ? { c } : `centre ${c}`;
  });
  await t("story_chip", async () => {
    await page.goto(BASE + P("/stories"), 4000);
    await ev("document.querySelectorAll('#st_chips button')[1].click()"); await sleep(2500);
    const r = await ev("({ on: document.querySelector('#st_chips button.on')?.innerText, n: document.querySelectorAll('.story').length })");
    return r.n > 0 && r.on && !/All/.test(r.on) ? r : JSON.stringify(r);
  });
  await page.send("Emulation.setDeviceMetricsOverride", { width: 390, height: 844, deviceScaleFactor: 1, mobile: true });
  await t("mobile_layer_panel", async () => {
    await page.goto(BASE + P("/map"), 3000);
    await ev("document.querySelector('.ml-toggle').click()"); await sleep(400);
    const r = await ev("(() => { const b = document.querySelector('.ml-panel').getBoundingClientRect(); return { left: b.left, right: b.right, bottom: b.bottom, w: innerWidth, h: innerHeight }; })()");
    return r.left >= 0 && r.right <= r.w + 1 ? r : `panel off screen ${JSON.stringify(r)}`;
  });
  await t("mobile_detail", async () => {
    await page.goto(BASE + P("/building/Q1003041"), 4000);
    const over = await ev("document.documentElement.scrollWidth - innerWidth");
    return over <= 2 ? { over } : `page ${over}px wider than the screen`;
  });
  await page.send("Emulation.setDeviceMetricsOverride", { width: 1280, height: 900, deviceScaleFactor: 1, mobile: false });
}

const GROUPS = { pages, popups, search, interact, layers, historic, places, extras };
const browser = await launch(CHROME);
try {
  const page = await browser.page();
  for (const [name, fn] of Object.entries(GROUPS)) {
    if (ONLY && !ONLY.includes(name)) continue;
    try { await fn(page); } catch (e) { report.push({ name: name + " (crashed)", ok: false, error: String(e) }); console.log("FAIL", name, e); }
  }
} finally {
  browser.close();
}
writeFileSync(join(OUT, "report.json"), JSON.stringify(report, null, 1));
const fails = report.filter((r) => !r.ok);
console.log(`\n${report.length - fails.length}/${report.length} checks passed; report ${join(OUT, "report.json")}`);
process.exit(fails.length ? 1 : 0);
