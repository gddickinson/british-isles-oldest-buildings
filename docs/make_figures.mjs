// Regenerate the README / Help figures in docs/img with headless Chrome (tests/cdp.mjs): real time,
// so the online street map, satellite imagery and historic maps load as they do for a user.
//
//   node docs/make_figures.mjs [--base http://127.0.0.1:5050] [--setup-base URL] [name ...]
//
// Needs the app running (./run.sh). The "setup" figure needs a second copy with no database
// (--setup-base); it is skipped otherwise.
import { join } from "node:path";
import { launch, sleep } from "../tests/cdp.mjs";

const arg = (k, d) => { const i = process.argv.indexOf(k); return i > 0 ? process.argv[i + 1] : d; };
const BASE = arg("--base", "http://127.0.0.1:5050"), SETUP = arg("--setup-base", "");
const CHROME = arg("--chrome", "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome");
const OUT = new URL("./img/", import.meta.url).pathname;
const only = process.argv.slice(2).filter((a, i, all) => !a.startsWith("--") && !all[i - 1]?.startsWith("--"));
const FAV = ["Q17530565", "Q2647826", "Q6818359", "Q15978988", "Q17530622"];       // York: a short walk

// name: { path, w, h, store (localStorage), js (run after load), wait (s), base }
const FIGURES = {
  catalogue: { path: "/?nation=Wales", w: 1400, h: 860 },
  detail: { path: "/building/Q1547466", w: 1280, h: 1500, wait: 9 },
  map_satellite: { path: "/map?lat=51.5081&lon=-0.0759&z=17", w: 1280, h: 760, store: { bi_map_base: "satellite", bi_map_layers: [] }, wait: 9 },
  map_layers: { path: "/map?lat=55.0&lon=-2.6&z=9", w: 1280, h: 800, store: { bi_map_base: "online", bi_map_layers: ["roman", "walking", "historic_counties"] },
                js: "document.querySelector('.ml-toggle').click()", wait: 9 },
  historic_map: { path: "/map?lat=55.9495&lon=-3.1910&z=15", w: 1280, h: 760, store: { bi_map_base: "online", bi_map_historic: { key: "os6inch", opacity: 0.9 } },
                  js: "document.querySelectorAll('#ex_groups input:checked').forEach((i) => i.click())", wait: 10 },
  places: { path: "/places?kind_group=Maritime+heritage&view=map", w: 1280, h: 800, store: { bi_map_base: "online" }, wait: 8 },
  people: { path: "/people?q=architect", w: 1280, h: 800 },
  pronunciation: { path: "/pronunciation?q=ll", w: 1280, h: 800 },
  pron_detail: { path: "/building/Q816295", w: 1280, h: 560, wait: 6 },
  stories: { path: "/stories?kind=supernatural", w: 1280, h: 820, store: { bi_map_base: "online" }, wait: 7 },
  tours: { path: "/tours?mode=walk&theme=ghosts", w: 1280, h: 900, store: { bi_map_base: "online" },
           js: "document.querySelector('.tour-card')?.click()", wait: 10 },
  tour_builder: { path: "/tours?tab=build", w: 1280, h: 900, store: { bi_map_base: "online", bi_favourites: FAV }, wait: 10 },
  history: { path: "/history", w: 1280, h: 900, store: { bi_map_base: "online" }, wait: 7 },
  oldest: { path: "/oldest", w: 1280, h: 800 },
  stats: { path: "/stats", w: 1280, h: 900, wait: 6 },
  quiz: { path: "/quiz", w: 1280, h: 760 },
  jobs: { path: "/data", w: 1280, h: 900, js: "document.querySelector('a[href=\"#jobs\"]').click()" },
  settings: { path: "/settings", w: 1280, h: 1000 },
  export_menu: { path: "/?q=castle&nation=Scotland", w: 1280, h: 620, js: "document.querySelector('#tb-export > button').click()" },
  palette: { path: "/", w: 1280, h: 620, js: "document.querySelector('.tb-tools > button').click()" },
  dark_mobile: { path: "/building/Q1547466", w: 390, h: 844, store: { bi_prefs: { theme: "dark" } }, mobile: true, wait: 8 },
  setup: { path: "/setup", w: 1280, h: 960, base: "setup" },
};

const browser = await launch(CHROME);
try {
  const page = await browser.page();
  for (const [name, f] of Object.entries(FIGURES)) {
    if (only.length && !only.includes(name)) continue;
    const base = f.base === "setup" ? SETUP : BASE;
    if (!base) { console.log("skip", name, "(needs --setup-base)"); continue; }
    await page.send("Emulation.setDeviceMetricsOverride", { width: f.w, height: f.h, deviceScaleFactor: 1, mobile: !!f.mobile });
    await page.goto(base + "/help", 300);
    await page.eval(`localStorage.clear(); ${Object.entries(f.store || {}).map(([k, v]) =>
      `localStorage.setItem(${JSON.stringify(k)}, ${JSON.stringify(JSON.stringify(v))});`).join("")}`);
    await page.goto(base + f.path, 3000);
    if (f.js) { await page.eval(f.js).catch((e) => console.log("  js:", e.message)); }
    await sleep((f.wait || 4) * 1000);
    await page.shot(join(OUT, name + ".jpg"));
    console.log("wrote", name, page.errors.length ? "errors: " + page.errors[0] : "");
  }
} finally {
  browser.close();
}
