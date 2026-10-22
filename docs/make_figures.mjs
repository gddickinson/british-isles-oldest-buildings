// Regenerate the README / Help figures in docs/img with headless Chrome (tests/cdp.mjs): real time,
// so the online street map, satellite imagery and historic maps load as they do for a user.
//
//   node docs/make_figures.mjs [--base http://127.0.0.1:5050] [--setup-base URL] [name ...]
//
// Needs the app running (./run.sh). The "setup" figure needs a second copy with no database
// (--setup-base; e.g. `git archive HEAD | tar -x -C /tmp/fresh` and run it on port 5071 — Chrome refuses
// 5060/5061); it is skipped otherwise.
import { join } from "node:path";
import { launch, sleep } from "../tests/cdp.mjs";

const arg = (k, d) => { const i = process.argv.indexOf(k); return i > 0 ? process.argv[i + 1] : d; };
const BASE = arg("--base", "http://127.0.0.1:5050"), SETUP = arg("--setup-base", "");
const CHROME = arg("--chrome", "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome");
const OUT = new URL("./img/", import.meta.url).pathname;
const only = process.argv.slice(2).filter((a, i, all) => !a.startsWith("--") && !all[i - 1]?.startsWith("--"));
const FAV = ["Q17530565", "Q2647826", "Q6818359", "Q15978988", "Q17530622"];       // York: a short walk

// name: { path, w, h, store (localStorage), js (run after load), wait (s), base, clip (part of the view) }
const FIGURES = {
  catalogue: { path: "/?nation=Wales", w: 1400, h: 860 },
  detail: { path: "/building/Q1547466", w: 1280, h: 1000, wait: 9 },
  map_satellite: { path: "/map?lat=51.5081&lon=-0.0759&z=17", w: 1280, h: 760, store: { bi_map_base: "satellite", bi_map_layers: [] }, wait: 9 },
  map_layers: { path: "/map?lat=53.75&lon=-1.2&z=9", w: 1280, h: 800, store: { bi_map_base: "online", bi_map_layers: ["roman", "walking", "historic_counties"] },
                js: "document.querySelector('.ml-toggle').click()", wait: 14 },
  historic_map: { path: "/map?lat=55.9495&lon=-3.1910&z=15", w: 1280, h: 760, store: { bi_map_base: "online", bi_map_historic: { key: "os6inch", opacity: 0.9 } },
                  js: "document.querySelectorAll('#ex_groups input:checked').forEach((i) => i.click())", wait: 10 },
  places: { path: "/places?kind_group=Maritime+heritage&view=map", w: 1280, h: 800, store: { bi_map_base: "online" }, wait: 8 },
  people: { path: "/people?role=Buried+here", w: 1280, h: 800 },
  pron_welsh: { path: "/pronunciation?variety=Welsh", w: 1280, h: 800 },
  then: { path: "/building/Q1070187", w: 1280, h: 900,
          js: "setTimeout(() => document.querySelector('[data-then]').scrollIntoView(), 5000)", wait: 10 },
  catalogue_landmarks: { path: "/?landmarks_only=1&has_image=1", w: 1400, h: 860 },
  data_quality: { path: "/data", w: 1280, h: 900,
                  js: "setTimeout(() => scrollTo({ top: document.querySelector('#e_box').getBoundingClientRect().top + scrollY - 140, behavior: 'instant' }), 3000)", wait: 6 },
  pron_detail: { path: "/building/Q816295", w: 1280, h: 560, wait: 6 },
  stories: { path: "/stories?kind=supernatural", w: 1280, h: 820, store: { bi_map_base: "online" }, wait: 7 },
  tours: { path: "/tours?mode=walk&theme=ghosts", w: 1280, h: 900, store: { bi_map_base: "online" },
           js: "setTimeout(() => [...document.querySelectorAll('.tour-card')].find((c) => /Cambridge/.test(c.textContent))?.click(), 2000)", wait: 12 },
  tour_builder: { path: "/tours?tab=build", w: 1280, h: 900, store: { bi_map_base: "online", bi_favourites: FAV }, wait: 10 },
  history: { path: "/history", w: 1280, h: 900, store: { bi_map_base: "online" }, wait: 7 },
  oldest: { path: "/oldest", w: 1280, h: 800 },
  oldest_lists: { path: "/oldest", w: 1280, h: 900, js: "setTimeout(() => document.querySelector('#o_lists').scrollIntoView(), 6000)", wait: 9 },
  evidence: { path: "/building/Q29265", w: 1280, h: 1000, store: { bi_map_base: "online" },
              js: "setTimeout(() => document.querySelector('[data-evidence]').scrollIntoView(), 4000)", wait: 9 },
  places_sport: { path: "/places?kind_group=Sport+%26+leisure&has_image=1", w: 1280, h: 800, wait: 8 },
  places_institutions: { path: "/places?kind_group=Public+institutions&has_image=1", w: 1280, h: 800, wait: 8 },
  quiz_menu: { path: "/quiz", w: 1280, h: 820 },
  quiz_story: { path: "/quiz?q=story", w: 1280, h: 760, wait: 5 },
  quiz_order: { path: "/quiz?q=order", w: 1280, h: 700, wait: 6 },
  places_graves: { path: "/places?kind_group=Graves+%26+burial+grounds&has_image=1", w: 1280, h: 800, store: { bi_map_base: "online" }, wait: 8 },
  stats: { path: "/stats", w: 1280, h: 900, wait: 6 },
  jobs: { path: "/data", w: 1280, h: 900, js: "setTimeout(() => scrollTo({ top: document.querySelector('#jobs').getBoundingClientRect().top + scrollY - 16, behavior: 'instant' }), 2000)",
          clip: { x: 0, y: 60, width: 1280, height: 780 } },
  settings: { path: "/settings", w: 1280, h: 1000 },
  sharing: { path: "/settings", w: 1280, h: 300, js: "setTimeout(() => document.querySelector('#sharing').scrollIntoView(), 1000)" },
  export_menu: { path: "/?q=castle&nation=Scotland", w: 1280, h: 620, js: "document.querySelector('#tb-export > button').click()" },
  palette: { path: "/", w: 1280, h: 620, wait: 6, js: "document.querySelector('.tb-tools > button').click(); setTimeout(() => { "
             + "const i = document.querySelector('#pal-q'); i.value = 'tintern'; i.dispatchEvent(new Event('input', { bubbles: true })); }, 600)" },
  dark_mobile: { path: "/building/Q1547466", w: 390, h: 844, store: { bi_prefs: { theme: "dark" } }, mobile: true, wait: 8 },
  // the copy with no database runs from a temporary folder: show the usual install path instead
  setup: { path: "/setup", w: 1280, h: 960, base: "setup", js: "document.querySelectorAll('main code').forEach((c) => { "
           + "if (/british_isles_buildings.sqlite/.test(c.textContent)) c.textContent = '~/british-isles-oldest-buildings/data/british_isles_buildings.sqlite'; })" },
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
    const clip = f.clip && { ...f.clip, y: f.clip.y + await page.eval("scrollY") };   // clip is in page coordinates
    await page.shot(join(OUT, name + ".jpg"), clip);
    console.log("wrote", name, page.errors.length ? "errors: " + page.errors[0] : "");
  }
} finally {
  browser.close();
}
