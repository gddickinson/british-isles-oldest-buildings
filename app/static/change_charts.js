// "Change over time" small graphs: one measure per graph (no second axis), all on the year slider's scale
// (TimeSlider.toPos, so early millennia take less room than recent centuries), with an uncertainty band where
// the source gives one, a marker at the slider's year, a hover crosshair and the values at that year.
// Other estimates of the same measure (`models`: other series, same unit) are drawn on the same axes in their own
// colours with a legend (at most two, so three lines in the validated categorical slots); series of separate published estimates (`style: "estimates"`) are drawn as dots with
// error bars; stretches longer than a series' `gap` have no data and are bridged by a faint dotted line; a series'
// `breaks` (changes of definition) are marked by thin lines, where the line starts again, and named on hover.
// ChangeCharts.draw(el, series, { from, to, year, models }) · span(series, "fit" | year) · valueAt(series, year) · fmt(v, unit)
const ChangeCharts = (() => {
  const NS = "http://www.w3.org/2000/svg";
  const W = 320, H = 74, PAD_L = 4, PAD_R = 4, PAD_T = 6, PAD_B = 14;
  const el = (tag, attrs, parent) => {
    const e = document.createElementNS(NS, tag);
    Object.entries(attrs).forEach(([k, v]) => e.setAttribute(k, v));
    if (parent) parent.appendChild(e);
    return e;
  };

  function fmt(v, unit = "") {
    if (v == null || isNaN(v)) return "—";
    const a = Math.abs(v);
    const n = a >= 1e9 ? (v / 1e9).toFixed(a >= 1e10 ? 0 : 1) + " bn" : a >= 1e6 ? (v / 1e6).toFixed(a >= 1e7 ? 0 : 1) + " m"
      : a >= 1e4 ? Math.round(v / 1e3) + "k" : a >= 100 ? Math.round(v).toLocaleString()
      : a >= 10 ? v.toFixed(1).replace(/\.0$/, "") : v.toFixed(2).replace(/0$/, "");
    return unit ? `${n} ${unit}` : n;
  }
  const yearText = (y) => (y < 0 ? `${-y} BC` : y < 1000 ? `AD ${y}` : String(y));
  const label = (s) => s.label || s.title;

  // the value at a year, interpolated between neighbouring points; null outside the series
  function valueAt(s, year) {
    const p = s.points;
    if (!p.length || year < p[0][0] || year > p[p.length - 1][0]) return null;
    let i = p.findIndex((q) => q[0] >= year);
    if (p[i][0] === year || i === 0) return p[i][1];
    const [y0, v0] = p[i - 1], [y1, v1] = p[i];
    return v0 + (v1 - v0) * (year - y0) / (y1 - y0);
  }
  // the longest stretch drawn as a plain line: the series' own `gap`, or for measured series five times their usual
  // spacing (at least 50 years); longer stretches have no figures and are shown dotted, read as estimates
  function gapOf(s) {
    if (s.gap != null) return s.gap;
    if (s.modelled || s.points.length < 3) return null;
    const d = s.points.slice(1).map((q, i) => q[0] - s.points[i][0]).sort((a, b) => a - b);
    return Math.max(50, 5 * d[Math.floor(d.length / 2)]);
  }
  // true when the year falls between two values further apart than that (an estimate, not a figure)
  function bridged(s, year) {
    const p = s.points, i = p.findIndex((q) => q[0] >= year), g = gapOf(s);
    return i > 0 && p[i][0] !== year && g != null && p[i][0] - p[i - 1][0] > g;
  }

  // the slider's scale, carried on at its earliest rate before 4000 BC (for series from the end of the Ice Age)
  const pos = (y) => (y < -4000 ? (y + 4000) * 120 / 3500 : TimeSlider.toPos(y));

  function drawOne(svg, s, pts, x, y, cls, primary) {
    const band = pts.filter((q) => q[2] != null && q[3] != null);
    if (s.style === "estimates") {                          // separate published estimates: dots and error bars
      if (pts.length > 1) el("path", { d: pts.map((q, i) => `${i ? "L" : "M"}${x(q[0]).toFixed(1)},${y(q[1]).toFixed(1)}`).join(""),
        class: `cc-gap ${cls}` }, svg);
      band.forEach((q) => el("line", { x1: x(q[0]), x2: x(q[0]), y1: y(q[2]), y2: y(q[3]), class: `cc-err ${cls}` }, svg));
      pts.forEach((q) => el("circle", { cx: x(q[0]), cy: y(q[1]), r: 3, class: `cc-dot ${cls}` }, svg));
      return;
    }
    if (band.length > 1) {
      const d = band.map((q, i) => `${i ? "L" : "M"}${x(q[0]).toFixed(1)},${y(q[3]).toFixed(1)}`).join("") +
        band.slice().reverse().map((q) => `L${x(q[0]).toFixed(1)},${y(q[2]).toFixed(1)}`).join("") + "Z";
      el("path", { d, class: `cc-band ${cls}` }, svg);
    }
    let d = "", gaps = "";
    const g = gapOf(s), br = (s.breaks || []).map((b) => b[0]);
    pts.forEach((q, i) => {
      const jump = i > 0 && g && q[0] - pts[i - 1][0] > g;
      const cut = i > 0 && br.some((b) => pts[i - 1][0] < b && b <= q[0]);   // a new definition: the line starts again
      if (cut && !jump) { d += `M${x(q[0]).toFixed(1)},${y(q[1]).toFixed(1)}`; return; }
      if (jump) gaps += `M${x(pts[i - 1][0]).toFixed(1)},${y(pts[i - 1][1]).toFixed(1)}L${x(q[0]).toFixed(1)},${y(q[1]).toFixed(1)}`;
      d += `${i === 0 || jump ? "M" : "L"}${x(q[0]).toFixed(1)},${y(q[1]).toFixed(1)}`;
    });
    if (gaps) el("path", { d: gaps, class: `cc-gap ${cls}` }, svg);
    el("path", { d, class: `cc-line ${cls}` + (s.modelled ? " cc-modelled" : "") }, svg);
    if (primary && pts.length <= 30) pts.forEach((q) => el("circle", { cx: x(q[0]), cy: y(q[1]), r: 2.6, class: `cc-dot ${cls}` }, svg));
  }

  function draw(box, s, { from, to, year, models = [] }) {
    const p0 = pos(from), p1 = pos(to);
    const x = (yr) => PAD_L + (pos(yr) - p0) / (p1 - p0 || 1) * (W - PAD_L - PAD_R);
    const cmp = models.length > 0;                          // comparing: every line takes a validated categorical colour
    const lines = [s, ...models.slice(0, 2)].map((m, i) => ({ s: m, cls: cmp ? `cc-m${i}` : "", pts: m.points.filter((q) => q[0] >= from && q[0] <= to) }));
    const pts = lines[0].pts;
    box.replaceChildren();
    const svg = el("svg", { viewBox: `0 0 ${W} ${H}`, class: "cc-svg", role: "img",
      "aria-label": `${s.title}: ${pts.length} values from ${yearText(from)} to ${yearText(to)}` +
        (lines.length > 1 ? `, compared with ${lines.slice(1).map((l) => label(l.s)).join(", ")}` : "") }, box);
    if (!lines.some((l) => l.pts.length)) {
      el("text", { x: W / 2, y: H / 2, class: "cc-empty", "text-anchor": "middle" }, svg).textContent = "No values in this period";
      return;
    }
    const vals = lines.flatMap((l) => l.pts.flatMap((q) => [q[1], q[2], q[3]])).filter((v) => v != null);
    let lo = Math.min(...vals), hi = Math.max(...vals);
    const logY = s.log && lo > 0;                            // prices over centuries: equal steps are equal ratios
    if (s.zero !== false && lo > 0 && !logY) lo = 0;         // counts and amounts start from zero
    if (hi === lo) hi = lo + 1;
    const f = logY ? Math.log10 : (v) => v;
    const pad = (f(hi) - f(lo)) * 0.06;
    const y = (v) => PAD_T + (1 - (f(v) - f(lo)) / (f(hi) - f(lo) + pad)) * (H - PAD_T - PAD_B);

    // recessive frame: baseline and the top value
    el("line", { x1: PAD_L, x2: W - PAD_R, y1: H - PAD_B, y2: H - PAD_B, class: "cc-axis" }, svg);
    el("text", { x: PAD_L + 2, y: PAD_T + 8, class: "cc-tick" }, svg).textContent = fmt(hi, "");
    if (lo !== 0) el("text", { x: PAD_L + 2, y: H - PAD_B - 3, class: "cc-tick" }, svg).textContent = fmt(lo, "");
    if (logY) el("text", { x: W - PAD_R - 2, y: PAD_T + 8, class: "cc-tick", "text-anchor": "end" }, svg).textContent = "log scale";
    ticks(from, to).forEach((t) => {
      el("line", { x1: x(t), x2: x(t), y1: H - PAD_B, y2: H - PAD_B + 3, class: "cc-axis" }, svg);
      el("text", { x: x(t), y: H - 2, class: "cc-tick", "text-anchor": "middle" }, svg).textContent = t < 0 ? `${-t} BC` : t;
    });

    // breaks of definition: a thin mark between the last year on the old definition and the first on the new
    const breaks = (s.breaks || []).filter((b) => b[0] > from && b[0] <= to);
    breaks.forEach((b) => el("line", { x1: x(b[0] - 0.5), x2: x(b[0] - 0.5), y1: PAD_T, y2: H - PAD_B, class: "cc-break" }, svg));
    lines.slice(1).reverse().forEach((l) => drawOne(svg, l.s, l.pts, x, y, l.cls, false));   // comparisons under the main line
    drawOne(svg, s, pts, x, y, lines[0].cls, true);

    // the slider's year
    if (year != null && year >= from && year <= to) {
      el("line", { x1: x(year), x2: x(year), y1: PAD_T - 4, y2: H - PAD_B, class: "cc-year" }, svg);
      lines.forEach((l) => {
        const v = valueAt(l.s, year);
        if (v != null && l.s.style !== "estimates") el("circle", { cx: x(year), cy: y(v), r: l.s === s ? 4 : 3, class: `cc-year-dot ${l.cls}` }, svg);
      });
    }

    // hover: crosshair on the nearest year with a value, and every line's value there
    const all = lines.flatMap((l) => l.pts.map((q) => q[0]));
    const cross = el("line", { y1: PAD_T - 4, y2: H - PAD_B, class: "cc-cross", visibility: "hidden" }, svg);
    const hit = el("rect", { x: 0, y: 0, width: W, height: H, fill: "transparent" }, svg);
    hit.addEventListener("mousemove", (e) => {
      const r = svg.getBoundingClientRect(), px = (e.clientX - r.left) / r.width * W;
      let best = all[0];
      all.forEach((yr) => { if (Math.abs(x(yr) - px) < Math.abs(x(best) - px)) best = yr; });
      cross.setAttribute("x1", x(best)); cross.setAttribute("x2", x(best));
      cross.setAttribute("visibility", "visible");
      const rows = [[yearText(best), ""]];
      lines.forEach((l) => {
        if (l.s.style === "estimates") {                     // every estimate for that year, with whose it is
          l.pts.filter((p) => p[0] === best).forEach((q) => rows.push([`${fmt(q[1], l.s.unit)}${q[2] != null ?
            ` (${fmt(q[2])}–${fmt(q[3])})` : ""}`, q[4] || label(l.s)]));
          return;
        }
        const q = l.pts.find((p) => p[0] === best), v = q ? q[1] : valueAt(l.s, best);
        if (v == null) return;
        const range = q && q[2] != null ? ` (${fmt(q[2])}–${fmt(q[3])})` : "";
        const est = !q || bridged(l.s, best) ? "≈ " : "";
        rows.push([`${est}${fmt(v, l.s.unit)}${range}`, lines.length > 1 ? label(l.s) : l.s.modelled ? "modelled" : ""]);
      });
      breaks.filter((b) => best === b[0] || best === b[0] - 1).forEach((b) => rows.push([`Break, ${b[0] - 1}/${b[0]}`, b[1]]));
      showTip(e, rows);
    });
    hit.addEventListener("mouseleave", () => { cross.setAttribute("visibility", "hidden"); hideTip(); });

    if (lines.length > 1) {                                  // legend: identity is never colour alone
      const lg = document.createElement("div");
      lg.className = "cc-legend";
      lg.innerHTML = lines.map((l) => `<span><i class="cc-key ${l.cls}${l.s.style === "estimates" ? " cc-key-dot" : ""}"></i>${esc(label(l.s))}</span>`).join("");
      box.appendChild(lg);
    }
  }

  // the years a graph shows: "fit" = the first to last year of the series and its comparisons, else from a year to today
  function span(s, range, models = []) {
    const now = new Date().getFullYear(), p = [s, ...models].flatMap((m) => m.points.map((q) => q[0]));
    if (range !== "fit" || !p.length) return { from: +range, to: now };
    const from = Math.min(...p), to = Math.max(...p);
    return to - from < 20 ? { from: from - 10, to: to + 10 } : { from, to };
  }

  // a few round years along the axis
  function ticks(from, to) {
    const cands = [-8000, -6000, -4000, -3000, -2000, -1000, 0, 500, 1000, 1250, 1500, 1600, 1700, 1750, 1800, 1825,
                   1850, 1875, 1900, 1925, 1950, 1975, 2000, 2025];
    const inside = cands.filter((t) => t > from && t < to && (pos(to) - pos(t)) / (pos(to) - pos(from)) > 0.05);   // no label clipped at the right
    const out = [];
    inside.forEach((t) => {                                   // keep labels at least ~13% of the width apart
      const last = out[out.length - 1];
      const gap = (pos(t) - pos(last ?? from)) / (pos(to) - pos(from));
      if (last === undefined ? gap > 0.06 : gap > 0.13) out.push(t);
    });
    return out;
  }

  return { draw, valueAt, bridged, fmt, yearText, span };
})();
