// "Sun and sky" in detail views (roadmap SK2, SK3): any [data-sky="<id>"] element with data-lat, data-lon and
// data-year gets the researched alignments of the record (static/data/sky.json, written by bidb.sky) and a compass of
// where the sun (and, for prehistoric sites, the moon at its standstills) rises and sets there, now and when begun;
// over the real skyline (SK7: sky.json for researched sites, /api/horizon in the local GUI) when it is known.
const SkyHere = (() => {
  let DATA = null;
  const load = () => (DATA = DATA || fetch((typeof IS_STATIC !== "undefined" && IS_STATIC ? "static" : "/static") + "/data/sky.json")
    .then((r) => r.json()).then((d) => {
      const by = {};
      d.alignments.forEach((a) => {
        if (a.horizon) a.horizon = skyline(a.horizon);
        if (a.record) (by[a.record] = by[a.record] || []).push(a);
      });
      return { all: d.alignments, by };
    }).catch(() => ({ all: [], by: {} })));
  let CHURCHES = null;
  const churches = () => (CHURCHES = CHURCHES || fetch((typeof IS_STATIC !== "undefined" && IS_STATIC ? "static" : "/static")
    + "/data/church_orientation.json").then((r) => r.json()).catch(() => ({ churches: {} })));
  // Skyline (bidb.sky_horizon.compact): altitudes in hundredths of a degree → degrees.
  const skyline = (h) => ({ ...h, alt: h.alt.map((a) => a / 100) });
  const horizonFor = (lat, lon) => fetch(`/api/horizon?lat=${lat}&lon=${lon}`).then((r) => (r.ok ? r.json() : null))
    .then((h) => h && skyline(h)).catch(() => null);
  // Azimuth of an event over the skyline when known, else over a flat horizon.
  const eventAz = (lat, body, e, rs, year, hz) => (hz
    ? Sky.horizonAzimuth(lat, body, e, rs, year ?? 2000, hz.alt, hz.step) : Sky.eventAzimuth(lat, body, e, rs, year ?? 2000));
  const MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"];
  const md = (s) => { const [m, d] = s.split("-").map(Number); return `${d} ${MONTHS[m - 1]}`; };
  const calendarPage = () => (IS_STATIC ? "sky.html" : "/sky");

  // Church orientation (SK5, SK5b): [axis, length/width, dates the sun rose on the axis, calendar year, feast, difference,
  // skyline altitude on the axis, the dates, feast and difference over that skyline] (bidb.church_orientation.FIELDS)
  function churchHTML(c) {
    const [az, el, flatDates, cal, flatFeast, flatDiff, hz, hzDates, hzFeast, hzDiff] = c;
    if (el < 1.4) return `<h4>Orientation</h4><p class="meta">The outline has no clear long axis (${el.toFixed(2)} times as long as wide).</p>`;
    if (!flatDates) return `<h4>Orientation</h4><p>The axis of the outline runs ${az.toFixed(0)}°–${(az + 180).toFixed(0)}°; neither end faces the sunrise.</p>`;
    const sky = hz != null, dates = sky ? hzDates : flatDates, feast = sky ? hzFeast : flatFeast, diff = sky ? hzDiff : flatDiff;
    return `<h4>Orientation</h4>
      <p>The east end of the outline's axis points ${az.toFixed(1)}° (${Sky.compass(az)})${sky
        ? `, where the skyline stands ${hz >= 0 ? "+" : ""}${hz.toFixed(1)}°` : ""}. ${dates.length
        ? `The sun rose on that line ${sky ? "over the skyline " : ""}on about ${dates.map(md).join(" and ")} ${cal != null ? ` in the Julian calendar of ${cal}, the year it was begun` : " in the Julian calendar of 1300 (it has no medieval start date)"}.`
        : "The sun never rises that far round."}${feast ? ` On the feast of its saint (${esc(feast)}) the sun rose ${diff.toFixed(1)}° from the axis${
          sky && flatDiff != null ? ` (${flatDiff.toFixed(1)}° over a flat horizon)` : ""}.` : ""}</p>
      <p class="meta">From the OpenStreetMap outline${sky ? "; skyline from the terrain model (bare ground: no trees or buildings)" : ", flat horizon"}.
        Whether churches were set out to face sunrise on their saint's day is disputed: see <a href="${calendarPage()}#churches">the test across the catalogue</a>.</p>`;
  }

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
    const hz = a.azimuth_horizon_built != null;
    const nums = !a.event ? [] : [hz ? `over the skyline ${deg(a.azimuth_horizon_built)}${a.built != null ? ` when built (${yearText(a.built)})` : ""}, where the hills stand ${
        a.horizon_altitude >= 0 ? "+" : ""}${a.horizon_altitude.toFixed(1)}° ${a.horizon_km < 1 ? "under a kilometre" : `${Math.round(a.horizon_km)} km`} away` : "",
      `over a flat horizon ${deg(a.azimuth_built ?? a.azimuth_now)}${!hz && a.built != null ? ` when built (${yearText(a.built)})` : ""}`,
      a.built != null ? `today ${deg(hz && a.azimuth_horizon_now != null ? a.azimuth_horizon_now : a.azimuth_now)}` : "",
      a.azimuth != null ? `published ${a.azimuth}°` : ""].filter(Boolean);
    return `<div class="sky-align">
      <p><b>${esc(what(a))}</b> <span class="sky-verdict ${esc(a.verdict)}">${esc(VERDICT[a.verdict] || a.verdict)}</span></p>
      <p>${esc(a.claim)}</p>${a.feature ? `<p class="meta">${esc(a.feature)}</p>` : ""}
      ${(a.views || []).length ? `<ul>${a.views.map((v) => `<li>${esc(v)}</li>`).join("")}</ul>` : ""}
      ${a.event ? `<p class="meta">Direction: ${nums.join("; ")}. ${esc(nextText(a))}.</p>` : ""}
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

  function compassSVG(lat, ev, year, aligned, church, hz) {
    const S = 200, c = S / 2, r = 78;
    const ray = (az, cls, len = r) => { const x = c + len * Math.sin(az * Math.PI / 180), y = c - len * Math.cos(az * Math.PI / 180);
      return `<line class="${cls}" x1="${c}" y1="${c}" x2="${x.toFixed(1)}" y2="${y.toFixed(1)}"/>`; };
    const lines = [];
    ev.forEach(([body, e]) => ["rise", "set"].forEach((rs) => {
      const now = eventAz(lat, body, e, rs, 2000, hz);
      if (now != null) lines.push(ray(now, `sky-${body} sky-${e.split("_")[0]}`));
      const then = year != null && year < 1000 ? eventAz(lat, body, e, rs, year, hz) : null;
      if (then != null && Math.abs(then - now) >= 0.3) lines.push(ray(then, "sky-then", r - 8));
    }));
    aligned.filter((a) => a.event).forEach((a) => lines.push(ray(a.azimuth_horizon_built ?? a.azimuth_built ?? a.azimuth_now, "sky-aligned", r + 10)));
    if (church && church[1] >= 1.4) lines.push(ray(church[0], "sky-axis", r + 10), ray(church[0] + 180, "sky-axis sky-axis-back", r - 20));
    const label = (t, az) => `<text x="${c + (r + 14) * Math.sin(az * Math.PI / 180)}" y="${c - (r + 14) * Math.cos(az * Math.PI / 180) + 4}">${t}</text>`;
    return `<svg class="sky-compass" viewBox="0 0 ${S} ${S}" role="img" aria-label="Compass of sunrise and sunset directions">
      <circle cx="${c}" cy="${c}" r="${r}"/>${label("N", 0)}${label("E", 90)}${label("S", 180)}${label("W", 270)}${lines.join("")}
      <circle class="sky-centre" cx="${c}" cy="${c}" r="3"/></svg>`;
  }

  function tableHTML(lat, ev, year, hz) {
    const then = year != null && year < 1000;
    const flat = (body, e, rs, y) => (hz ? ` title="Over a flat horizon ${deg(Sky.eventAzimuth(lat, body, e, rs, y))}"` : "");
    const row = ([body, e]) => {
      const n = Sky.next(body, e);
      return `<tr><td title="${esc(Sky.NAMES[e])}">${esc(Sky.SHORT[e])}</td>${["rise", "set"].map((rs) => `<td${flat(body, e, rs, 2000)}>${deg(eventAz(lat, body, e, rs, 2000, hz))}${
        then ? `<br><span class="meta">${deg(eventAz(lat, body, e, rs, year, hz))}</span>` : ""}</td>`).join("")}
        <td>${body === "sun" ? n.date.toLocaleDateString(undefined, { day: "numeric", month: "short", year: "numeric" }) : n.season ? `now (peak ${n.date.getFullYear()})` : n.date.getFullYear()}</td></tr>`;
    };
    return `<table class="sky-table"><thead><tr><th></th><th>Rises</th><th>Sets</th><th>Next</th></tr></thead>
      <tbody>${ev.map(row).join("")}</tbody></table>
      ${then ? `<p class="hint">Second line: when begun (${yearText(year)}); the earth's tilt was then ${Sky.obliquity(year).toFixed(2)}°, now ${Sky.obliquity(new Date().getFullYear()).toFixed(2)}°.</p>` : ""}`;
  }

  // The skyline as a strip from north round to north, heights stretched, with where each event rises and sets on it.
  function panoramaSVG(lat, ev, hz, aligned) {
    const W = 360, H = 70, top = Math.max(2, ...hz.alt), low = Math.min(-1, ...hz.alt);
    const y = (a) => (H - 14) * (top - a) / (top - low) + 4;
    const pts = hz.alt.map((a, i) => `${(i * hz.step).toFixed(1)},${y(a).toFixed(1)}`);
    const marks = [];
    ev.forEach(([body, e]) => ["rise", "set"].forEach((rs) => {
      const az = eventAz(lat, body, e, rs, 2000, hz);
      if (az != null) marks.push(`<line class="sky-${body} sky-${e.split("_")[0]}" x1="${az}" x2="${az}" y1="${y(Sky.altitudeAt(hz.alt, hz.step, az))}" y2="${y(Sky.altitudeAt(hz.alt, hz.step, az)) - 10}"><title>${esc(Sky.SHORT[e])} ${rs}: ${deg(az)}</title></line>`);
    }));
    aligned.filter((a) => a.azimuth_horizon_built != null).forEach((a) => marks.push(
      `<line class="sky-aligned" x1="${a.azimuth_horizon_built}" x2="${a.azimuth_horizon_built}" y1="${y(a.horizon_altitude)}" y2="${y(a.horizon_altitude) - 14}"><title>Researched alignment ${deg(a.azimuth_horizon_built)}</title></line>`));
    const tick = (t, az) => `<text x="${az}" y="${H - 1}">${t}</text>`;
    return `<svg class="sky-panorama" viewBox="0 0 ${W} ${H}" role="img" aria-label="Skyline from north round to north">
      <polygon class="sky-land" points="0,${H - 10} ${pts.join(" ")} ${W},${y(hz.alt[0])} ${W},${H - 10}"/>
      <line class="sky-flat" x1="0" x2="${W}" y1="${y(0)}" y2="${y(0)}"/>${marks.join("")}
      ${tick("N", 4)}${tick("E", 90)}${tick("S", 180)}${tick("W", 270)}</svg>
      <p class="hint">The skyline from north round to north (heights stretched; the dotted line is level with the eye),
        highest ${Math.max(...hz.alt).toFixed(1)}°; from the terrain tiles (Environment Agency LiDAR in England, SRTM and EU-DEM elsewhere),
        bare ground with no trees or buildings.</p>`;
  }

  async function mount(el) {
    el.dataset.skyDone = "1";
    const lat = parseFloat(el.dataset.lat);
    if (Number.isNaN(lat)) return;
    const year = el.dataset.year === "" || el.dataset.year == null ? null : parseInt(el.dataset.year, 10);
    const aligned = ((await load()).by[el.dataset.sky]) || [];
    const church = el.dataset.church ? (await churches()).churches[el.dataset.sky] : null;
    const ev = events(year != null && year < -500, aligned);
    const lon = parseFloat(el.dataset.lon);
    const hz0 = (aligned.find((a) => a.horizon) || {}).horizon || null;
    const grid = (hz) => `${compassSVG(lat, ev, year, aligned, church, hz)}<div>${tableHTML(lat, ev, year, hz)}
        <p class="hint">Directions from true north where the first or last gleam appears ${hz ? "over the skyline (hover a direction for the flat-horizon one)" : `over a flat horizon; hills and
        buildings move them${IS_STATIC || Number.isNaN(lon) ? "" : ' <button type="button" class="linkish sky-hz-btn">use the real skyline</button>'}`}. Lines: <span class="sky-key sun">sun</span>${ev.some(([b]) => b === "moon") ? ' <span class="sky-key moon">moon at its standstills</span>' : ""}${
          aligned.length ? ' <span class="sky-key aligned">researched alignment</span>' : ""}${
          church && church[1] >= 1.4 ? ' <span class="sky-key axis">axis of the building</span>' : ""}${year != null && year < 1000 ? ' <span class="sky-key then">when begun</span>' : ""}.</p>
        ${el.dataset.lon ? `<p><a href="${esc(skyMapUrl(el))}">Show sun lines on the map</a> · <a href="${calendarPage()}">Sky calendar</a></p>` : ""}</div>
        ${hz ? `<div class="sky-pano">${panoramaSVG(lat, ev, hz, aligned)}</div>` : ""}`;
    el.innerHTML = `${aligned.length ? `<h4>Sky alignment</h4>${aligned.map(alignmentHTML).join("")}` : ""}${church ? churchHTML(church) : ""}
      <details class="sky-details"${aligned.length ? " open" : ""}><summary>Sun${ev.some(([b]) => b === "moon") ? " and moon" : ""} on the horizon here</summary>
        <div class="sky-grid">${grid(hz0)}</div>
      </details>`;
    const box = el.querySelector(".sky-grid");
    box.addEventListener("click", async (e) => {
      const b = e.target.closest(".sky-hz-btn");
      if (!b) return;
      b.disabled = true;
      b.textContent = "reading the terrain…";
      const hz = await horizonFor(lat, lon);
      if (hz) box.innerHTML = grid(hz);
      else b.textContent = "terrain not available";
    });
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
