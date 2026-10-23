// "Change over time" panel: graphs of people, land, industry and climate through the centuries (data and
// citations in static/data/change/series.json, written by bidb.change_series), each switched on or off, on
// the year slider's scale and marked at its year. ChangePanel.mount(el, { local() -> [series], year })
// returns { setYear(y), refresh() }. `local` adds series made from this catalogue (e.g. records begun).
const ChangePanel = (() => {
  const URL_ = (typeof IS_STATIC !== "undefined" && IS_STATIC ? "static" : "/static") + "/data/change/series.json";
  const KEY = "bidb_change_graphs", RANGE_KEY = "bidb_change_range";
  const RANGES = [["Each graph's own years", "fit"], ["All time", -4000], ["Since AD 1000", 1000], ["Since 1500", 1500], ["Since 1700", 1700],
                  ["Since 1900", 1900]];
  let data = null;
  const load = () => (data = data || fetch(URL_).then((r) => r.json()).catch(() => ({ series: [], sources: {}, themes: [] })));
  const store = {
    get(k, d) { try { return JSON.parse(localStorage.getItem(k)) ?? d; } catch (e) { return d; } },
    set(k, v) { try { localStorage.setItem(k, JSON.stringify(v)); } catch (e) { /* private mode */ } },
  };

  function sourceLine(s, sources) {
    return (s.sources || []).map((id) => {
      const src = sources[id];
      if (!src) return "";
      return `<a href="${esc(src.url)}" target="_blank" rel="noopener">${esc(src.short || src.publisher)}</a>` +
        (src.licence ? ` <span class="cc-lic">(${esc(src.licence)})</span>` : "");
    }).filter(Boolean).join("; ");
  }

  function mount(el, opts = {}) {
    el.innerHTML = `<div class="cp-head"><b>📈 Change over time</b>
        <select class="cp-range" aria-label="Period shown">${RANGES.map(([t, y]) => `<option value="${y}">${t}</option>`).join("")}</select>
        <button class="cp-close" type="button" aria-label="Hide the graphs" title="Hide the graphs">×</button></div>
      ${opts.map ? '<div class="cp-layers"></div>' : ""}
      <details class="cp-pick"><summary>Choose graphs</summary><div class="cp-list"></div></details>
      <div class="cp-charts"></div>
      <p class="hint cp-foot">Hover a graph for values; the line marks the year on the slider. Dashed lines are
        modelled estimates. <a href="${typeof IS_STATIC !== "undefined" && IS_STATIC ? "change.html" : "/change"}">Sources and notes</a></p>`;
    const list = el.querySelector(".cp-list"), charts = el.querySelector(".cp-charts"), range = el.querySelector(".cp-range");
    let year = opts.year ?? null, all = [], sources = {};
    range.value = String(store.get(RANGE_KEY, "fit"));

    const chosen = () => new Set(store.get(KEY, null) ?? all.filter((s) => s.default).map((s) => s.id));
    function drawList() {
      const on = chosen(), themes = [...new Set(all.map((s) => s.theme))];
      list.innerHTML = themes.map((t) => `<div class="cp-theme"><b>${esc(t)}</b>${all.filter((s) => s.theme === t).map((s) =>
        `<label class="check"><input type="checkbox" value="${esc(s.id)}" ${on.has(s.id) ? "checked" : ""}> ${esc(s.title)}</label>`)
        .join("")}</div>`).join("");
    }
    function drawCharts() {
      const on = chosen();
      const shown = all.filter((s) => on.has(s.id));
      charts.innerHTML = shown.length ? "" : `<p class="hint">No graphs chosen — open “Choose graphs”.</p>`;
      shown.forEach((s) => {
        const v = year != null ? ChangeCharts.valueAt(s, year) : null;
        const item = document.createElement("div");
        item.className = "cc-item";
        item.innerHTML = `<div class="cc-title">${esc(s.title)}${s.region ? ` <span class="cc-region">${esc(s.region)}</span>` : ""}
            <span class="cc-now">${v != null ? `${ChangeCharts.fmt(v, s.unit)} in ${ChangeCharts.yearText(year)}` : esc(s.unit_long || s.unit || "")}</span></div>
          <div class="cc-plot"></div>
          <div class="cc-src">${sourceLine(s, sources)}${s.note ? ` <button type="button" class="cc-more" aria-expanded="false">notes</button>` : ""}</div>
          ${s.note ? `<p class="cc-note" hidden>${esc(s.note)}</p>` : ""}`;
        charts.appendChild(item);
        ChangeCharts.draw(item.querySelector(".cc-plot"), s, { ...ChangeCharts.span(s, range.value), year });
      });
    }
    list.addEventListener("change", () => {
      store.set(KEY, [...list.querySelectorAll("input:checked")].map((i) => i.value));
      drawCharts();
    });
    range.addEventListener("change", () => { store.set(RANGE_KEY, range.value); drawCharts(); });
    charts.addEventListener("click", (e) => {
      const b = e.target.closest(".cc-more");
      if (!b) return;
      const note = b.closest(".cc-item").querySelector(".cc-note");
      note.hidden = !note.hidden;
      b.setAttribute("aria-expanded", String(!note.hidden));
    });
    el.querySelector(".cp-close").addEventListener("click", () => opts.onClose?.());
    const mapLayers = opts.map ? ChangeLayers.mount(el.querySelector(".cp-layers"), opts.map) : null;
    mapLayers?.setYear(year);

    const refresh = async () => {
      const d = await load();
      sources = d.sources || {};
      all = (d.series || []).concat(opts.local ? opts.local() : []);
      drawList();
      drawCharts();
    };
    refresh();
    let pending = null;
    return {
      refresh,
      pause: (on) => mapLayers?.pause(on),
      setYear(y) {                                  // redraw at most every 150 ms while the slider moves
        year = y;
        mapLayers?.setYear(y);
        if (pending) return;
        pending = setTimeout(() => { pending = null; drawCharts(); }, 150);
      },
    };
  }

  return { mount, load };
})();
