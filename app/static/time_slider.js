// "Through time" on the Map page: a year slider that shows what had been built or founded by then (and not yet
// closed or lost), with a histogram of start years, a play button and, optionally, the historic map of the time.
// TimeSlider.mount(el, { onChange(year|null), counts() -> [years…], historic: true }).
const TimeSlider = (() => {
  // the slider runs 0–1000; early millennia get less of it than recent centuries
  const STOPS = [[0, -4000], [120, -500], [200, 43], [330, 600], [470, 1066], [620, 1500], [800, 1800], [930, 1900],
                 [1000, new Date().getFullYear()]];
  const toYear = (v) => {
    for (let i = 1; i < STOPS.length; i++) {
      const [p0, y0] = STOPS[i - 1], [p1, y1] = STOPS[i];
      if (v <= p1) return Math.round(y0 + (y1 - y0) * (v - p0) / (p1 - p0));
    }
    return STOPS[STOPS.length - 1][1];
  };
  const toPos = (y) => {
    for (let i = 1; i < STOPS.length; i++) {
      const [p0, y0] = STOPS[i - 1], [p1, y1] = STOPS[i];
      if (y <= y1) return p0 + (p1 - p0) * (Math.max(y, y0) - y0) / (y1 - y0);
    }
    return 1000;
  };
  const label = (y) => (y < 0 ? `${-y} BC` : y < 1000 ? `AD ${y}` : String(y));

  // the historic map that best fits a year (first one this copy has); keys from app/historic_layers.py
  const ERAS = [[43, 409, ["romana"]], [410, 850, ["anglosaxon"]], [851, 1199, ["isles900"]], [1200, 1699, ["gough"]],
                [1700, 1799, ["roy", "smith"]], [1800, 1879, ["oldseries", "smith"]], [1880, 1914, ["os6inch", "bartholomew", "os1inch"]],
                [1915, 1945, ["bartholomew"]]];

  // a closing year, from date texts such as "1836–1987" (opened–closed); "between 1800 and 1839" is no range
  const endOf = (r) => { const m = /^(?:c\. )?(\d{1,4})–(\d{1,4})$/.exec(r.date_text || ""); return m ? +m[2] : null; };
  const standing = (r, y) => r.year_start != null && r.year_start <= y && !((endOf(r) ?? Infinity) <= y);

  function histogram(years, w = 300, h = 34, bins = 60) {
    const n = new Array(bins).fill(0);
    years.forEach((y) => { if (y != null) n[Math.min(bins - 1, Math.floor(toPos(y) / 1000 * bins))]++; });
    const top = Math.max(1, ...n.map((v) => Math.sqrt(v)));
    return `<svg viewBox="0 0 ${w} ${h}" preserveAspectRatio="none" class="ts-hist" aria-hidden="true">${n.map((v, i) =>
      `<rect x="${(i * w / bins).toFixed(1)}" width="${(w / bins - 0.6).toFixed(1)}" y="${(h - Math.sqrt(v) / top * h).toFixed(1)}"
        height="${(Math.sqrt(v) / top * h).toFixed(1)}"/>`).join("")}</svg>`;
  }

  function mount(el, opts) {
    el.innerHTML = `<div class="ts-head"><label class="check"><input type="checkbox" class="ts-on"> <b>Through time</b></label>
        <span class="ts-year">—</span><button class="btn small ts-play" type="button" disabled>▶ Play</button>
        <label class="check ts-maps"><input type="checkbox" class="ts-hist-map"> Map of the time</label>
        <button class="ts-close" type="button" title="Hide the year slider" aria-label="Hide the year slider">×</button></div>
      <div class="ts-body"><div class="ts-histbox"></div>
        <input type="range" class="ts-range" min="0" max="1000" value="${toPos(1500)}" disabled aria-label="Year"></div>
      <small class="hint ts-note">What survives or is recorded, from the year each was begun or founded (until it closed,
        where known). Undated records are hidden; early centuries look emptier than they were.</small>`;
    const on = el.querySelector(".ts-on"), range = el.querySelector(".ts-range"), play = el.querySelector(".ts-play"),
          year = el.querySelector(".ts-year"), hist = el.querySelector(".ts-histbox"), mapBox = el.querySelector(".ts-hist-map");
    let timer = null, pending = null, lastEra = null;
    const current = () => toYear(+range.value);
    const historic = (y) => {                         // switch the layer switcher's historic map to the era's
      const sel = document.querySelector(".ml-hsel");
      if (!sel || !mapBox.checked) return;
      const era = ERAS.find(([a, b]) => y >= a && y <= b);
      const key = era ? era[2].find((k) => [...sel.options].some((o) => o.value === k)) || "" : "";
      if (key === lastEra) return;
      lastEra = key;
      sel.value = key;
      sel.dispatchEvent(new Event("change"));
    };
    const update = () => {                            // redraw at most every 200 ms while dragging or playing
      const y = on.checked ? current() : null;
      year.textContent = y === null ? "—" : label(y);
      if (y !== null) historic(y);
      if (pending) return;
      pending = setTimeout(() => { pending = null; opts.onChange(on.checked ? current() : null); }, 200);
    };
    const redrawHist = () => { hist.innerHTML = on.checked ? histogram(opts.counts()) : ""; };
    on.addEventListener("change", () => {
      range.disabled = play.disabled = !on.checked;
      el.classList.toggle("on", on.checked);
      if (!on.checked && timer) play.click();
      if (!on.checked && mapBox.checked) { lastEra = null; const sel = document.querySelector(".ml-hsel"); if (sel) { sel.value = ""; sel.dispatchEvent(new Event("change")); } }
      redrawHist();
      update();
    });
    // hide / show the whole control; hiding also switches it off so every record shows again
    const show = document.createElement("button");
    show.type = "button";
    show.className = "btn small ts-show";
    show.textContent = "🕰 Through time";
    show.title = "Show the year slider";
    el.after(show);
    const visible = (v, keep = true) => {
      el.hidden = !v;
      show.hidden = v;
      if (!v && on.checked) { on.checked = false; on.dispatchEvent(new Event("change")); }
      if (keep) try { localStorage.setItem("bidb_time_slider", v ? "shown" : "hidden"); } catch (e) { /* private mode */ }
    };
    el.querySelector(".ts-close").addEventListener("click", () => visible(false));
    show.addEventListener("click", () => visible(true));
    let saved = null;
    try { saved = localStorage.getItem("bidb_time_slider"); } catch (e) { /* private mode */ }
    visible(saved !== "hidden", false);
    mapBox.addEventListener("change", () => { lastEra = null; if (on.checked) historic(current()); });
    range.addEventListener("input", update);
    play.addEventListener("click", () => {
      if (timer) { clearInterval(timer); timer = null; play.textContent = "▶ Play"; return; }
      if (+range.value >= 1000) range.value = 0;
      play.textContent = "❚❚ Pause";
      timer = setInterval(() => {
        range.value = Math.min(1000, +range.value + 2);
        update();
        if (+range.value >= 1000) play.click();
      }, 60);
    });
    return { refresh: redrawHist, year: () => (on.checked ? current() : null) };
  }

  return { mount, standing, endOf, toYear, toPos, label };
})();
