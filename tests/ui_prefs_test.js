// Run from the project root: node tests/ui_prefs_test.js  (preferences and export serialisers)
// minimal browser stubs, then load ui_prefs.js and ui_export.js serialisers
const store = {};
global.localStorage = { getItem: (k) => (k in store ? store[k] : null), setItem: (k, v) => { store[k] = String(v); }, removeItem: (k) => { delete store[k]; } };
global.location = { search: "?_theme=dark" };
global.document = { documentElement: { dataset: {}, style: {} }, body: { dataset: {} } };
global.matchMedia = () => ({ matches: false, addEventListener() {} });
global.window = { dispatchEvent() {} }; global.CustomEvent = class { constructor(t, o) { this.type = t; this.detail = o && o.detail; } };
global.window.addEventListener = () => {};
const fs = require("fs");
eval(fs.readFileSync("app/static/ui_prefs.js", "utf8") + "; global.Prefs = Prefs;");
const assert = require("assert");
assert.equal(document.documentElement.dataset.theme, "dark");           // URL override
assert.equal(Prefs.get("pageSize"), 48);
Prefs.set("pageSize", 96); assert.equal(Prefs.get("pageSize"), 96);
Prefs.set("units", "mi"); assert.equal(Prefs.dist(10), "6.2 mi");
Prefs.set("units", "km"); assert.equal(Prefs.dist(10, 0), "10 km"); assert.ok(!("units" in JSON.parse(store.bi_prefs)));
Prefs.set("cluster", false); assert.equal(Prefs.cluster({ disableClusteringAtZoom: 13 }).disableClusteringAtZoom, 1);
Prefs.recent.add("Q1", "building", "A"); Prefs.recent.add("Q2", "place", "B"); Prefs.recent.add("Q1", "building", "A");
assert.deepEqual(Prefs.recent.list().map((r) => r.id), ["Q1", "Q2"]);
const dump = Prefs.exportAll(); Prefs.reset(); assert.equal(Prefs.get("pageSize"), 48);
Prefs.importAll(dump); assert.equal(Prefs.get("pageSize"), 96);
Prefs.set("textSize", 125); assert.equal(document.documentElement.style.fontSize, "125%");
// serialisers
global.IS_STATIC = false; global.UI = { toast() {} }; global.api = async () => [];
eval(fs.readFileSync("app/static/ui_export.js", "utf8") + "; global.ExportMenu = ExportMenu;");
const rows = [{ id: "Q1", name: 'Say "hi", ok', lat: 51, lon: -1, year_start: 1100 }, { id: "Q2", name: "No coords" }];
const csv = ExportMenu.toCSV(rows);
assert.equal(csv.split("\r\n")[1], 'Q1,"Say ""hi"", ok",51,-1,1100');
assert.equal(JSON.parse(ExportMenu.toGeoJSON(rows, ["id", "name"])).features.length, 1);
assert.ok(ExportMenu.toKML(rows, ["id", "name", "year_start"], "t").includes("<coordinates>-1,51</coordinates>"));
console.log("all JS checks passed");
