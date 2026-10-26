// Building types BT5: charts through time. TypeTime.inUse (the types in use at each date, one small area chart per
// domain on the Map slider's time axis, a year to choose, the types in use then and a link to the Map page at that
// year), TypeTime.materials (materials and techniques by the century their records were begun, each row shaded
// against its own busiest century), TypeTime.spread (counties reached by a type over time) and TypeTime.chains
// (what came before and what came next).
const TypeTime = (() => {
  const NOW = new Date().getFullYear();
  const NS = "http://www.w3.org/2000/svg";
  const yt = TypeTree.yearText;
  const el = (tag, attrs, parent, text) => {
    const n = document.createElementNS(NS, tag);
    Object.entries(attrs).forEach(([k, v]) => v != null && n.setAttribute(k, v));
    if (text != null) n.textContent = text;
    if (parent) parent.appendChild(n);
    return n;
  };
  const TICKS = [-4000, -2000, -500, 43, 600, 1066, 1300, 1500, 1700, 1800, 1900, NOW];
  const STEPS = 200;                                   // sample dates along the slider's axis
  const samples = Array.from({ length: STEPS + 1 }, (_, i) => TimeSlider.toYear(i * 1000 / STEPS));
  const inUseAt = (t, y) => { const [a, b] = TypeTree.span(t.period); return a <= y && y <= b; };
  const mapUrl = (y) => `${IS_STATIC ? "map.html" : "/map"}?year=${y}`;

  // one row per domain: an area of how many of its types were in use at each date
  function inUse(box, tree, { year = 1500, onOpen } = {}) {
    const isles = tree.types.filter((t) => !t.abroad);
    const domains = tree.tree.map(([d]) => d);
    const counts = Object.fromEntries(domains.map((d) => [d, samples.map((y) => isles.filter((t) => t.domain === d && inUseAt(t, y)).length)]));
    const top = Math.max(1, ...Object.values(counts).flat());
    box.innerHTML = `<p class="prose">How many building types of each domain were being built at each date, from the periods of use in
      the family tree (first known to last built). The time axis gives early millennia less room than recent centuries.
      Choose a year to list the types in use then.</p>
      <div class="tt-year"><label>Year <input type="range" min="0" max="1000" class="tt-range" aria-label="Year"></label>
        <b class="tt-yearlabel"></b> <a class="btn small ghost tt-maplink">Show the map at this year</a></div>
      <div class="tt-box tt-inuse"></div><div class="tt-inuse-list" aria-live="polite"></div>`;
    const chart = box.querySelector(".tt-inuse"), range = box.querySelector(".tt-range");
    // narrow screens: the domain's name above its row, fewer dates on the axis
    const W = Math.max(chart.clientWidth || 900, 300), narrow = W < 640;
    const L = narrow ? 6 : Math.min(190, Math.round(W * 0.32)), R = narrow ? 14 : 12, ROW = narrow ? 44 : 34, TOP = 18;
    const ticks = narrow ? [-4000, 43, 1066, 1500, 1800, NOW] : TICKS;
    const x = (y) => L + (W - L - R) * TimeSlider.toPos(Math.max(-4000, Math.min(NOW, y))) / 1000;
    const H = TOP + domains.length * ROW + 22;
    const svg = el("svg", { width: W, height: H, class: "tt-svg", role: "img", "aria-label": "Building types in use through time, by domain" }, chart);
    const axis = el("g", { class: "tt-axis" }, svg);
    ticks.forEach((t) => {
      el("line", { x1: x(t), x2: x(t), y1: TOP - 4, y2: H - 18, class: "tt-grid" }, axis);
      el("text", { x: x(t), y: H - 5, "text-anchor": "middle" }, axis, t === NOW ? "now" : yt(t));
    });
    domains.forEach((d, i) => {
      const base = TOP + (i + 1) * ROW - 4, h = ROW - (narrow ? 20 : 8);
      const pts = samples.map((y, k) => `${x(y).toFixed(1)},${(base - counts[d][k] / top * h).toFixed(1)}`);
      if (narrow) el("text", { x: L, y: base - h - 1, class: "tt-label" }, svg, `${d} (up to ${Math.max(...counts[d])})`);
      else {
        el("text", { x: 4, y: base - 6, class: "tt-label" }, svg, d);
        el("text", { x: L - 6, y: base - 6, "text-anchor": "end", class: "tt-count" }, svg, `${Math.max(...counts[d])} max`);
      }
      el("path", { d: `M${x(samples[0])},${base} L${pts.join(" L")} L${x(NOW)},${base} Z`, class: "tt-area" }, svg);
      el("line", { x1: L, x2: W - R, y1: base, y2: base, class: "tt-base" }, svg);
    });
    const mark = el("line", { y1: TOP - 4, y2: H - 18, class: "tt-mark" }, svg);
    // hover: the counts of every domain at the date under the pointer
    const hit = el("rect", { x: L, y: 0, width: W - L - R, height: H, fill: "transparent" }, svg);
    const nearest = (px) => {
      const pos = Math.max(0, Math.min(1000, (px - L) / (W - L - R) * 1000));
      return Math.round(pos / 1000 * STEPS);
    };
    hit.addEventListener("pointermove", (e) => {
      const k = nearest(e.clientX - svg.getBoundingClientRect().left);
      showTip(e, [[yt(samples[k]), "types in use"], ...domains.filter((d) => counts[d][k]).map((d) => [String(counts[d][k]), d])]);
    });
    hit.addEventListener("pointerleave", hideTip);
    hit.addEventListener("click", (e) => { range.value = nearest(e.clientX - svg.getBoundingClientRect().left) * 1000 / STEPS; set(); });

    const list = box.querySelector(".tt-inuse-list"), lab = box.querySelector(".tt-yearlabel"), link = box.querySelector(".tt-maplink");
    function set() {
      const y = TimeSlider.toYear(+range.value);
      mark.setAttribute("x1", x(y)); mark.setAttribute("x2", x(y));
      lab.textContent = yt(y);
      link.href = mapUrl(y);
      const now = isles.filter((t) => inUseAt(t, y));
      list.innerHTML = `<h3>${now.length} types in use in ${esc(yt(y))}</h3>${domains.map((d) => {
        const ts = now.filter((t) => t.domain === d);
        return ts.length ? `<p><b>${esc(d)}</b> (${ts.length}): ${ts.map((t) => `<a href="?t=${encodeURIComponent(t.id)}" data-go="${esc(t.id)}">${esc(t.name)}</a>${
          (t.period.flourish && t.period.flourish[0] <= y && y <= t.period.flourish[1]) ? " <span class=\"meta\">flourishing</span>" : ""}`).join(", ")}</p>` : "";
      }).join("")}`;
      if (onOpen) onOpen(y);
    }
    range.value = TimeSlider.toPos(year);
    range.addEventListener("input", set);
    set();
  }

  // materials × centuries; each row shaded against its own busiest century, the material's first date ticked
  function materials(box, data) {
    const all = Object.values(data.counts).flatMap((c) => Object.keys(c).map(Number));
    const FIRST = Math.max(-1000, Math.min(...all)), cents = [];
    for (let c = FIRST; c <= 2000; c += 100) cents.push(c);
    const col = (c) => Math.max(FIRST, c);
    const cent = (c) => (c < 0 ? `${ordinal(-c / 100)} c. BC` : `${ordinal(c / 100 + 1)} c.`);
    const label = (c) => (c === FIRST && FIRST > Math.min(...all) ? `${cent(c)} or before` : cent(c));
    const rows = data.groups.map(([g, ids]) => [g, ids.filter((id) => data.counts[id])]).filter(([, ids]) => ids.length);
    box.innerHTML = `<p class="prose">How many catalogue records and places that name each material or technique were begun in each
      century. A record names the materials of all its phases, so the shading follows the buildings, not the material itself;
      records begun more than a century before the material's first known date (a later phase) are left out. Each row is
      shaded against its own busiest century; the tick marks the material's first known date. Click a row to open it.</p>
      <div class="tt-box"><table class="tt-heat"><thead><tr><th></th>${cents.map((c) => `<th scope="col"><span>${esc(label(c))}</span></th>`).join("")}</tr></thead>
      <tbody>${rows.map(([g, ids]) => `<tr class="tt-heat-group"><th colspan="${cents.length + 1}">${esc(g)}</th></tr>${ids.map((id) => {
        const by = {};
        Object.entries(data.counts[id]).forEach(([c, n]) => { by[col(+c)] = (by[col(+c)] || 0) + n; });
        const max = Math.max(...Object.values(by)), first = data.first[id];
        return `<tr><th scope="row"><a href="?m=${encodeURIComponent(id)}" data-gom="${esc(id)}">${esc(data.names[id])}</a></th>${cents.map((c) => {
          const n = by[c] || 0, tick = first != null && col(Math.floor(first / 100) * 100) === c;
          return `<td class="${tick ? "first" : ""}" title="${esc(`${data.names[id]}, ${label(c)}: ${n.toLocaleString()}${tick ? ` (first known ${yt(first)})` : ""}`)}"
            style="--v:${n ? (0.15 + 0.85 * Math.sqrt(n / max)).toFixed(2) : 0}"></td>`;
        }).join("")}</tr>`;
      }).join("")}`).join("")}</tbody></table></div>
      <p class="hint">Darker: more records begun in that century (square-root scale, per row). Hover a cell for the count.</p>`;
  }

  // a type's spread: how many counties had an example by each date, and the first one in each
  function spread(box, rows) {
    if (!rows || rows.length < 2) { box.remove(); return; }
    const first = rows[0].year, last = Math.max(rows[rows.length - 1].year, first + 1);
    const W = Math.max(box.clientWidth || 600, 300), L = 34, R = 10, H = 150, T = 10, B = 24;
    const x = (y) => L + (W - L - R) * (y - first) / (last - first), y = (n) => T + (H - T - B) * (1 - n / rows.length);
    box.innerHTML = `<h4>Spread across the isles</h4><p class="hint">Counties with a dated example (standing or a ruin, not dated from
      the type and not too early) by each date: ${rows.length} counties, first ${esc(rows[0].county)} (${esc(yt(first))}). A date given only to the century
      ("11th century") counts from the century's first year, so steps at 1001, 1101… gather many counties at once.</p>`;
    const svg = el("svg", { width: W, height: H, class: "tt-svg", role: "img", "aria-label": `Counties reached over time, ${rows.length} in all` }, box);
    const ax = el("g", { class: "tt-axis" }, svg);
    [0, Math.round(rows.length / 2), rows.length].forEach((n) => {
      el("line", { x1: L, x2: W - R, y1: y(n), y2: y(n), class: "tt-grid" }, ax);
      el("text", { x: L - 4, y: y(n) + 4, "text-anchor": "end" }, ax, String(n));
    });
    const step = Math.max(1, Math.round((last - first) / 5 / 50) * 50 || Math.ceil((last - first) / 5));
    for (let t = Math.ceil(first / step) * step; t <= last; t += step) el("text", { x: x(t), y: H - 6, "text-anchor": "middle" }, ax, yt(t));
    let d = `M${x(first)},${y(0)}`;
    rows.forEach((r, i) => { d += ` H${x(r.year).toFixed(1)} V${y(i + 1).toFixed(1)}`; });
    el("path", { d: d + ` H${x(last)}`, class: "tt-step" }, svg);
    rows.forEach((r, i) => {
      const c = el("circle", { cx: x(r.year), cy: y(i + 1), r: 4, class: "tt-dot" }, svg);
      c.addEventListener("pointermove", (e) => showTip(e, [[r.county, r.nation || ""], [r.date_text || yt(r.year), r.name]]));
      c.addEventListener("pointerleave", hideTip);
    });
    const ent = (r) => `<a href="${r.source === "place" ? "#" : buildingUrl(r.id)}" ${r.source === "place" ? "data-place" : "data-open"}="${esc(r.id)}">${esc(r.name)}</a>`;
    box.insertAdjacentHTML("beforeend", `<details class="tr-list"><summary>First example in each county</summary>
      <ul class="nearby">${rows.map((r) => `<li><b>${esc(r.county)}</b> <span class="meta">${esc(r.nation || "")}</span>: ${ent(r)}
        <span class="meta">${esc(r.date_text || yt(r.year))}</span></li>`).join("")}</ul></details>`);
  }

  // lines of descent through a type: oldest ancestor → … → this type → … → the last
  const ARROW = { descent: "grew into", replacement: "replaced by", revival: "revived as" };
  const node = (s) => `<a href="?t=${encodeURIComponent(s.id)}" data-go="${esc(s.id)}" class="${s.abroad ? "abroad" : ""}">${esc(s.name)}</a>${
    s.from != null ? ` <span class="meta">${esc(yt(s.from))}</span>` : ""}`;
  const arrow = (s) => `<span class="tt-arrow ${esc(s.confidence)}" title="${esc(s.confidence)}">→ ${esc(ARROW[s.kind])}${
    s.confidence !== "documented" ? ` (${esc(s.confidence)})` : ""} →</span>`;
  function lines(c, name) {
    // a line before: each step's link joins it to the next, the last to the type; a line after: each step's link joins the one before
    const before = c.before.map((p) => `<li>${p.map((s) => `${node(s)} ${arrow(s)} `).join("")}<b>${esc(name)}</b></li>`);
    const after = c.after.map((p) => `<li><b>${esc(name)}</b> ${p.map((s) => `${arrow(s)} ${node(s)}`).join(" ")}</li>`);
    return [before, after];
  }
  function chains(c, name) {
    if (!c) return "";
    const [before, after] = lines(c, name);
    let extra = "";
    if (!before.length && !after.length && c.form_of) {
      const [b, a] = lines(c.form_of, c.form_of.name);
      extra = `<p>A form of <a href="?t=${encodeURIComponent(c.form_of.id)}" data-go="${esc(c.form_of.id)}">${esc(c.form_of.name)}</a>, whose lines run:</p>
        <ul class="tt-chains">${b.concat(a).join("")}</ul>`;
    }
    if (!before.length && !after.length && !extra) return "";
    return `<h3>What came before and what came next</h3><p class="hint">Lines of descent, replacement and revival from the sourced
      family links (forms of a type are on the family list above).</p>${before.length || after.length ? `<ul class="tt-chains">${before.concat(after).join("")}</ul>` : ""}${extra}`;
  }

  return { inUse, materials, spread, chains, mapUrl };
})();
