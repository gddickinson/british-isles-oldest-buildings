// "Sun and sky" in detail views (roadmap SK2, SK3): any [data-sky="<id>"] element with data-lat, data-lon and
// data-year gets the researched alignments of the record (static/data/sky.json, written by bidb.sky) and a compass of
// where the sun (and, for prehistoric sites, the moon at its standstills) rises and sets there, now and when begun.
const SkyHere = (() => {
  let DATA = null;
  const load = () => (DATA = DATA || fetch((typeof IS_STATIC !== "undefined" && IS_STATIC ? "static" : "/static") + "/data/sky.json")
    .then((r) => r.json()).then((d) => {
      const by = {};
      d.alignments.forEach((a) => a.record && (by[a.record] = by[a.record] || []).push(a));
      return { all: d.alignments, by };
    }).catch(() => ({ all: [], by: {} })));
  const VERDICT = { established: "Established", probable: "Probable", disputed: "Disputed" };
  const fmtDate = (d) => d.toLocaleDateString(undefined, { day: "numeric", month: "long", year: "numeric" });
  const deg = (a) => (a == null ? "–" : `${a.toFixed(1)}° ${Sky.compass(a)}`);
  const yearText = (y) => (y < 0 ? `${-y} BC` : `AD ${y}`);
  const what = (a) => (a.event ? `${Sky.NAMES[a.event]} ${a.body === "sun" ? "sun" : "moon"}${a.rise_set}`
    : `${a.body === "sun" ? "Sun" : "Moon"} (no particular event named)`);

  function nextText(a) {
    const n = Sky.next(a.body, a.event);
    return n.season ? `The moon is near its standstill now (peak ${n.date.getFullYear()}); its season lasts about a year either side`
      : a.body === "moon" ? `Next standstill ${n.date.getFullYear()}` : `Next on ${fmtDate(n.date)}`;
  }

  function alignmentHTML(a) {
    const nums = !a.event ? [] : [`computed ${deg(a.azimuth_built ?? a.azimuth_now)}${a.built != null ? ` when built (${yearText(a.built)})` : ""}`,
      a.built != null ? `today ${deg(a.azimuth_now)}` : "", a.azimuth != null ? `published ${a.azimuth}°` : ""].filter(Boolean);
    return `<div class="sky-align">
      <p><b>${esc(what(a))}</b> <span class="sky-verdict ${esc(a.verdict)}">${esc(VERDICT[a.verdict] || a.verdict)}</span></p>
      <p>${esc(a.claim)}</p>${a.feature ? `<p class="meta">${esc(a.feature)}</p>` : ""}
      ${(a.views || []).length ? `<ul>${a.views.map((v) => `<li>${esc(v)}</li>`).join("")}</ul>` : ""}
      ${a.event ? `<p class="meta">Direction: ${nums.join("; ")} (flat horizon). ${esc(nextText(a))}.</p>` : ""}
      ${a.viewing ? `<p class="meta">Seeing it: ${esc(a.viewing)}</p>` : ""}
      <ul class="sky-sources">${a.sources.map((s) => `<li><a href="${esc(s.url)}" target="_blank" rel="noopener">${esc(s.title)}</a>${
        s.author ? ` <span class="meta">${esc(s.author)}${s.locator ? `, ${esc(s.locator)}` : ""}</span>` : ""}<br>“${esc(s.quote)}”${
        s.check === "quote-found" ? ' <span class="meta" title="Last check found these words on the page">✓ quote found</span>' : ""}</li>`).join("")}</ul>
    </div>`;
  }

  // Events shown: the solstices and equinoxes always; for prehistoric sites the cross-quarter days and the moon.
  function events(early, aligned) {
    const ev = [["sun", "summer_solstice"], ["sun", "equinox"], ["sun", "winter_solstice"]];
    if (early) ev.push(["sun", "beltane"], ["sun", "samhain"]);
    if (early || aligned.some((a) => a.body === "moon")) ev.push(["moon", "major_north"], ["moon", "major_south"]);
    return ev;
  }

  function compassSVG(lat, ev, year, aligned) {
    const S = 200, c = S / 2, r = 78;
    const ray = (az, cls, len = r) => { const x = c + len * Math.sin(az * Math.PI / 180), y = c - len * Math.cos(az * Math.PI / 180);
      return `<line class="${cls}" x1="${c}" y1="${c}" x2="${x.toFixed(1)}" y2="${y.toFixed(1)}"/>`; };
    const lines = [];
    ev.forEach(([body, e]) => ["rise", "set"].forEach((rs) => {
      const now = Sky.eventAzimuth(lat, body, e, rs);
      if (now != null) lines.push(ray(now, `sky-${body} sky-${e.split("_")[0]}`));
      const then = year != null && year < 1000 ? Sky.eventAzimuth(lat, body, e, rs, year) : null;
      if (then != null && Math.abs(then - now) >= 0.3) lines.push(ray(then, "sky-then", r - 8));
    }));
    aligned.filter((a) => a.event).forEach((a) => lines.push(ray(a.azimuth_built ?? a.azimuth_now, "sky-aligned", r + 10)));
    const label = (t, az) => `<text x="${c + (r + 14) * Math.sin(az * Math.PI / 180)}" y="${c - (r + 14) * Math.cos(az * Math.PI / 180) + 4}">${t}</text>`;
    return `<svg class="sky-compass" viewBox="0 0 ${S} ${S}" role="img" aria-label="Compass of sunrise and sunset directions">
      <circle cx="${c}" cy="${c}" r="${r}"/>${label("N", 0)}${label("E", 90)}${label("S", 180)}${label("W", 270)}${lines.join("")}
      <circle class="sky-centre" cx="${c}" cy="${c}" r="3"/></svg>`;
  }

  function tableHTML(lat, ev, year) {
    const then = year != null && year < 1000;
    const row = ([body, e]) => {
      const n = Sky.next(body, e);
      return `<tr><td title="${esc(Sky.NAMES[e])}">${esc(Sky.SHORT[e])}</td>${["rise", "set"].map((rs) => `<td>${deg(Sky.eventAzimuth(lat, body, e, rs))}${
        then ? `<br><span class="meta">${deg(Sky.eventAzimuth(lat, body, e, rs, year))}</span>` : ""}</td>`).join("")}
        <td>${body === "sun" ? n.date.toLocaleDateString(undefined, { day: "numeric", month: "short", year: "numeric" }) : n.season ? `now (peak ${n.date.getFullYear()})` : n.date.getFullYear()}</td></tr>`;
    };
    return `<table class="sky-table"><thead><tr><th></th><th>Rises</th><th>Sets</th><th>Next</th></tr></thead>
      <tbody>${ev.map(row).join("")}</tbody></table>
      ${then ? `<p class="hint">Second line: when begun (${yearText(year)}); the earth's tilt was then ${Sky.obliquity(year).toFixed(2)}°, now ${Sky.obliquity(new Date().getFullYear()).toFixed(2)}°.</p>` : ""}`;
  }

  async function mount(el) {
    el.dataset.skyDone = "1";
    const lat = parseFloat(el.dataset.lat);
    if (Number.isNaN(lat)) return;
    const year = el.dataset.year === "" || el.dataset.year == null ? null : parseInt(el.dataset.year, 10);
    const aligned = ((await load()).by[el.dataset.sky]) || [];
    const ev = events(year != null && year < -500, aligned);
    el.innerHTML = `${aligned.length ? `<h4>Sky alignment</h4>${aligned.map(alignmentHTML).join("")}` : ""}
      <details class="sky-details"${aligned.length ? " open" : ""}><summary>Sun${ev.some(([b]) => b === "moon") ? " and moon" : ""} on the horizon here</summary>
        <div class="sky-grid">${compassSVG(lat, ev, year, aligned)}<div>${tableHTML(lat, ev, year)}
        <p class="hint">Directions from true north where the first or last gleam appears over a flat horizon; hills and
        buildings move them. Lines: <span class="sky-key sun">sun</span>${ev.some(([b]) => b === "moon") ? ' <span class="sky-key moon">moon at its standstills</span>' : ""}${
          aligned.length ? ' <span class="sky-key aligned">researched alignment</span>' : ""}${year != null && year < 1000 ? ' <span class="sky-key then">when begun</span>' : ""}.</p>
        ${el.dataset.lon ? `<p><a href="${esc(skyMapUrl(el))}">Show sun lines on the map</a></p>` : ""}</div></div>
      </details>`;
  }
  const skyMapUrl = (el) => {
    const p = new URLSearchParams({ lat: el.dataset.lat, lon: el.dataset.lon, z: "15", mark: el.dataset.name || "", sky: "1" });
    if (el.dataset.year) p.set("skyyear", el.dataset.year);
    return `${IS_STATIC ? "map.html" : "/map"}?${p}`;
  };

  const scan = (root) => root.querySelectorAll && root.querySelectorAll("[data-sky]:not([data-sky-done])").forEach(mount);
  new MutationObserver((ms) => ms.forEach((m) => m.addedNodes.forEach((n) => n.nodeType === 1 && scan(n.parentNode || n))))
    .observe(document.documentElement, { childList: true, subtree: true });
  document.addEventListener("DOMContentLoaded", () => scan(document));
  return { load };
})();
