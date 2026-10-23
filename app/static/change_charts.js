// "Change over time" small graphs: one series per graph (no second axis), all on the year slider's scale
// (TimeSlider.toPos, so early millennia take less room than recent centuries), with an uncertainty band where
// the source gives one, a marker at the slider's year, a hover crosshair and the value at that year.
// ChangeCharts.draw(el, series, { from, to, year }) · ChangeCharts.span(series, "fit" | year) · ChangeCharts.valueAt(series, year) · ChangeCharts.fmt(v, unit)
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

  // the value at a year, interpolated between neighbouring points; null outside the series
  function valueAt(s, year) {
    const p = s.points;
    if (!p.length || year < p[0][0] || year > p[p.length - 1][0]) return null;
    let i = p.findIndex((q) => q[0] >= year);
    if (p[i][0] === year || i === 0) return p[i][1];
    const [y0, v0] = p[i - 1], [y1, v1] = p[i];
    return v0 + (v1 - v0) * (year - y0) / (y1 - y0);
  }

  // the slider's scale, carried on at its earliest rate before 4000 BC (for series from the end of the Ice Age)
  const pos = (y) => (y < -4000 ? (y + 4000) * 120 / 3500 : TimeSlider.toPos(y));

  function draw(box, s, { from, to, year }) {
    const p0 = pos(from), p1 = pos(to);
    const x = (y) => PAD_L + (pos(y) - p0) / (p1 - p0 || 1) * (W - PAD_L - PAD_R);
    const pts = s.points.filter((q) => q[0] >= from && q[0] <= to);
    box.replaceChildren();
    const svg = el("svg", { viewBox: `0 0 ${W} ${H}`, class: "cc-svg", role: "img",
      "aria-label": `${s.title}: ${pts.length} values from ${yearText(from)} to ${yearText(to)}` }, box);
    if (!pts.length) {
      el("text", { x: W / 2, y: H / 2, class: "cc-empty", "text-anchor": "middle" }, svg).textContent = "No values in this period";
      return;
    }
    const vals = pts.flatMap((q) => [q[1], q[2], q[3]]).filter((v) => v != null);
    let lo = Math.min(...vals), hi = Math.max(...vals);
    if (s.zero !== false && lo > 0) lo = 0;                  // counts and amounts start from zero
    if (hi === lo) hi = lo + 1;
    const pad = (hi - lo) * 0.06;
    const y = (v) => PAD_T + (1 - (v - lo) / (hi - lo + pad)) * (H - PAD_T - PAD_B);

    // recessive frame: baseline and the top value
    el("line", { x1: PAD_L, x2: W - PAD_R, y1: H - PAD_B, y2: H - PAD_B, class: "cc-axis" }, svg);
    el("text", { x: PAD_L + 2, y: PAD_T + 8, class: "cc-tick" }, svg).textContent = fmt(hi, "");
    if (lo !== 0) el("text", { x: PAD_L + 2, y: H - PAD_B - 3, class: "cc-tick" }, svg).textContent = fmt(lo, "");
    ticks(from, to).forEach((t) => {
      el("line", { x1: x(t), x2: x(t), y1: H - PAD_B, y2: H - PAD_B + 3, class: "cc-axis" }, svg);
      el("text", { x: x(t), y: H - 2, class: "cc-tick", "text-anchor": "middle" }, svg).textContent = t < 0 ? `${-t} BC` : t;
    });

    // uncertainty band, then the line (gaps where the source has none: `gap` years between points)
    const band = pts.filter((q) => q[2] != null && q[3] != null);
    if (band.length > 1) {
      const d = band.map((q, i) => `${i ? "L" : "M"}${x(q[0]).toFixed(1)},${y(q[3]).toFixed(1)}`).join("") +
        band.slice().reverse().map((q) => `L${x(q[0]).toFixed(1)},${y(q[2]).toFixed(1)}`).join("") + "Z";
      el("path", { d, class: "cc-band" }, svg);
    }
    let d = "";
    pts.forEach((q, i) => {
      const jump = i === 0 || (s.gap && q[0] - pts[i - 1][0] > s.gap);
      d += `${jump ? "M" : "L"}${x(q[0]).toFixed(1)},${y(q[1]).toFixed(1)}`;
    });
    el("path", { d, class: "cc-line" + (s.modelled ? " cc-modelled" : "") }, svg);
    if (pts.length <= 30) pts.forEach((q) => el("circle", { cx: x(q[0]), cy: y(q[1]), r: 2.6, class: "cc-dot" }, svg));

    // the slider's year
    if (year != null && year >= from && year <= to) {
      el("line", { x1: x(year), x2: x(year), y1: PAD_T - 4, y2: H - PAD_B, class: "cc-year" }, svg);
      const v = valueAt(s, year);
      if (v != null) el("circle", { cx: x(year), cy: y(v), r: 4, class: "cc-year-dot" }, svg);
    }

    // hover: crosshair on the nearest value
    const cross = el("line", { y1: PAD_T - 4, y2: H - PAD_B, class: "cc-cross", visibility: "hidden" }, svg);
    const hit = el("rect", { x: 0, y: 0, width: W, height: H, fill: "transparent" }, svg);
    hit.addEventListener("mousemove", (e) => {
      const r = svg.getBoundingClientRect(), px = (e.clientX - r.left) / r.width * W;
      let best = pts[0];
      pts.forEach((q) => { if (Math.abs(x(q[0]) - px) < Math.abs(x(best[0]) - px)) best = q; });
      cross.setAttribute("x1", x(best[0])); cross.setAttribute("x2", x(best[0]));
      cross.setAttribute("visibility", "visible");
      const range = best[2] != null ? ` (${fmt(best[2])}–${fmt(best[3])})` : "";
      showTip(e, [[yearText(best[0]), ""], [fmt(best[1], s.unit) + range, s.modelled ? "modelled" : ""]]);
    });
    hit.addEventListener("mouseleave", () => { cross.setAttribute("visibility", "hidden"); hideTip(); });
  }

  // the years a graph shows: "fit" = the series' own first to last year, else from a year to today
  function span(s, range) {
    const now = new Date().getFullYear(), p = s.points;
    if (range !== "fit" || !p.length) return { from: +range, to: now };
    const from = p[0][0], to = p[p.length - 1][0];
    return to - from < 20 ? { from: from - 10, to: to + 10 } : { from, to };
  }

  // a few round years along the axis
  function ticks(from, to) {
    const cands = [-8000, -6000, -4000, -3000, -2000, -1000, 0, 500, 1000, 1250, 1500, 1600, 1700, 1750, 1800, 1825,
                   1850, 1875, 1900, 1925, 1950, 1975, 2000, 2025];
    const inside = cands.filter((t) => t > from && t < to);
    const out = [];
    inside.forEach((t) => {                                   // keep labels at least ~13% of the width apart
      const last = out[out.length - 1];
      const gap = (pos(t) - pos(last ?? from)) / (pos(to) - pos(from));
      if (last === undefined ? gap > 0.06 : gap > 0.13) out.push(t);
    });
    return out;
  }

  return { draw, valueAt, fmt, yearText, span };
})();
