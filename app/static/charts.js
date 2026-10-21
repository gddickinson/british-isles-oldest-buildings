// Small SVG chart kit: stacked vertical bars (timeline) and horizontal bars (stats).
// Thin marks, 2px surface gaps between segments, rounded data-ends, hover tooltips,
// legends for multi-series, labels in text colours (never the series colour).
const SVGNS = "http://www.w3.org/2000/svg";
function svgEl(tag, attrs, parent) {
  const el = document.createElementNS(SVGNS, tag);
  Object.entries(attrs || {}).forEach(([k, v]) => el.setAttribute(k, v));
  if (parent) parent.appendChild(el);
  return el;
}

let _tip = null;
function tooltip() {
  if (!_tip) { _tip = document.createElement("div"); _tip.className = "chart-tip"; document.body.appendChild(_tip); }
  return _tip;
}
function showTip(evt, lines) {
  const t = tooltip();
  t.replaceChildren();
  lines.forEach(([value, label, color], i) => {
    const row = document.createElement("div");
    row.className = i === 0 ? "tip-head" : "tip-row";
    if (color) { const k = document.createElement("span"); k.className = "tip-key"; k.style.background = color; row.appendChild(k); }
    const v = document.createElement("b"); v.textContent = value; row.appendChild(v);
    if (label) { const l = document.createElement("span"); l.textContent = " " + label; row.appendChild(l); }
    t.appendChild(row);
  });
  t.style.display = "block";
  const x = Math.min(evt.clientX + 14, window.innerWidth - t.offsetWidth - 8);
  t.style.left = x + "px";
  t.style.top = (evt.clientY + 14 + window.scrollY) + "px";
}
function hideTip() { if (_tip) _tip.style.display = "none"; }

function niceMax(v) {
  if (v <= 5) return 5;
  const p = 10 ** Math.floor(Math.log10(v));
  return [1, 2, 2.5, 5, 10].map((m) => m * p).find((m) => m >= v);
}

function roundedTop(x, y, w, h, r) {
  r = Math.min(r, w / 2, h);
  return `M${x},${y + h}V${y + r}Q${x},${y} ${x + r},${y}H${x + w - r}Q${x + w},${y} ${x + w},${y + r}V${y + h}Z`;
}

// rows: [{label, counts: {series: n}}]; series: ordered names; color(series) -> css colour
function stackedBars(container, { rows, series, color, onClick, height = 340, valueLabel = "buildings" }) {
  container.replaceChildren();
  const width = Math.max(container.clientWidth || 800, 320);
  const m = { t: 12, r: 12, b: 44, l: 48 };
  const iw = width - m.l - m.r, ih = height - m.t - m.b;
  const totals = rows.map((r) => series.reduce((a, s) => a + (r.counts[s] || 0), 0));
  const max = niceMax(Math.max(1, ...totals));
  const svg = svgEl("svg", { width, height, role: "img", class: "chart-svg" }, container);
  const gGrid = svgEl("g", { class: "grid-lines" }, svg);
  for (let i = 0; i <= 4; i++) {
    const y = m.t + ih - (ih * i) / 4;
    svgEl("line", { x1: m.l, x2: width - m.r, y1: y, y2: y }, gGrid);
    const t = svgEl("text", { x: m.l - 6, y: y + 4, "text-anchor": "end", class: "axis-label" }, gGrid);
    t.textContent = Math.round((max * i) / 4).toLocaleString();
  }
  const band = iw / rows.length, bw = Math.max(2, Math.min(40, band * 0.72));
  const every = Math.ceil(rows.length / Math.max(1, Math.floor(iw / 60)));
  rows.forEach((r, i) => {
    const x = m.l + band * i + (band - bw) / 2;
    let y = m.t + ih;
    const g = svgEl("g", { class: "bar", tabindex: 0 }, svg);
    const present = series.filter((s) => r.counts[s]);
    present.forEach((s, j) => {
      const h = (ih * r.counts[s]) / max;
      const gap = j < present.length - 1 ? 2 : 0;              // 2px surface gap between segments
      const segH = Math.max(0, h - gap);
      y -= h;
      if (j === present.length - 1) svgEl("path", { d: roundedTop(x, y, bw, segH, 4), fill: color(s) }, g);
      else svgEl("rect", { x, y: y + gap, width: bw, height: segH, fill: color(s) }, g);
    });
    svgEl("rect", { x: m.l + band * i, y: m.t, width: band, height: ih, fill: "transparent" }, g);  // hit area
    const lines = [[totals[i].toLocaleString(), `${valueLabel} · ${r.label}`]]
      .concat(present.slice().reverse().map((s) => [r.counts[s].toLocaleString(), s, color(s)]));
    g.addEventListener("pointermove", (e) => showTip(e, lines));
    g.addEventListener("pointerleave", hideTip);
    g.addEventListener("focus", (e) => { const b = g.getBoundingClientRect(); showTip({ clientX: b.right, clientY: b.top }, lines); });
    g.addEventListener("blur", hideTip);
    if (onClick) { g.style.cursor = "pointer"; g.addEventListener("click", () => onClick(r)); }
    if (i % every === 0) {
      const t = svgEl("text", { x: x + bw / 2, y: height - m.b + 16, "text-anchor": "middle", class: "axis-label" }, svg);
      t.textContent = r.short || r.label;
    }
  });
  if (series.length > 1) container.appendChild(legend(series, color));
}

function legend(series, color) {
  const box = document.createElement("div");
  box.className = "chart-legend";
  series.forEach((s) => {
    const item = document.createElement("span");
    const key = document.createElement("i"); key.style.background = color(s);
    item.appendChild(key); item.appendChild(document.createTextNode(s));
    box.appendChild(item);
  });
  return box;
}

// rows: [[label, value]] single series; direct value labels at the bar end
function hBars(container, rows, { color, onClick, max: maxRows = 30, unit = "" } = {}) {
  container.replaceChildren();
  rows = rows.slice(0, maxRows);
  const width = Math.max(container.clientWidth || 500, 280), rowH = 24, m = { l: 170, r: 56 };
  const height = rows.length * rowH + 8;
  const max = Math.max(1, ...rows.map((r) => r[1]));
  const svg = svgEl("svg", { width, height, class: "chart-svg" }, container);
  rows.forEach(([label, v], i) => {
    const y = 4 + i * rowH, w = Math.max(2, ((width - m.l - m.r) * v) / max);
    const g = svgEl("g", { class: "bar", tabindex: 0 }, svg);
    const lt = svgEl("text", { x: m.l - 8, y: y + 15, "text-anchor": "end", class: "axis-label" }, g);
    lt.textContent = label.length > 26 ? label.slice(0, 25) + "…" : label;
    svgEl("rect", { x: m.l, y: y + 4, width: w, height: rowH - 8, rx: 4, fill: color || cssVar("--series-1") }, g);
    const vt = svgEl("text", { x: m.l + w + 6, y: y + 15, class: "value-label" }, g);
    vt.textContent = v.toLocaleString() + unit;
    svgEl("rect", { x: 0, y, width, height: rowH, fill: "transparent" }, g);
    g.addEventListener("pointermove", (e) => showTip(e, [[v.toLocaleString() + unit, label]]));
    g.addEventListener("pointerleave", hideTip);
    if (onClick) { g.style.cursor = "pointer"; g.addEventListener("click", () => onClick(label)); }
  });
}

function tableHTML(headers, rows) {
  return `<table class="grid small"><thead><tr>${headers.map((h) => `<th>${esc(h)}</th>`).join("")}</tr></thead>
    <tbody>${rows.map((r) => `<tr>${r.map((c) => `<td>${esc(c)}</td>`).join("")}</tr>`).join("")}</tbody></table>`;
}

function ordinal(n) {
  const suf = n % 100 >= 11 && n % 100 <= 13 ? "th" : ({ 1: "st", 2: "nd", 3: "rd" }[n % 10] || "th");
  return `${n}${suf}`;
}

function bucketLabel(start, size) {
  if (size === 100) return start < 0 ? `${ordinal(-start / 100)} c. BC` : `${ordinal(start / 100 + 1)} c.`;
  if (size === 1000) return start < 0 ? `${ordinal(-start / 1000)} mill. BC` : `${ordinal(start / 1000 + 1)} mill. AD`;
  const f = (y) => (y < 0 ? `${-y} BC` : `${y}`);
  return `${f(start)}–${f(start + size)}`;
}
