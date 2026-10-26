// Building types (BT4a): the family tree on a time axis. Every type is a row (domain → family → type); its bar spans
// its period of use (first known to last built, or to today), thicker while it flourished; the sourced links between
// types are drawn as branches at the later type's first date: solid for documented, dashed for disputed, faint for
// probable. Hovering a type brings its links forward; links between domains are drawn only then. TypeTree.draw(el, tree, { domain, q, kinds, collapsed, onOpen }).
const TypeTree = (() => {
  const NOW = new Date().getFullYear();
  const KINDS = { descent: ["grew into", "--g1"], variant: ["has the form", "--g3"], influence: ["shaped", "--g2"],
                  replacement: ["replaced by", "--g8"], revival: ["revived as", "--g7"], convergence: ["similar to (separate origins)", "--g-other"] };
  const TICKS = [-4000, -2000, -500, 43, 600, 1066, 1300, 1500, 1700, 1800, 1900, NOW];
  const ROW = { domain: 28, family: 22, type: 19 };
  const NS = "http://www.w3.org/2000/svg";
  const el = (tag, attrs, parent, text) => {
    const n = document.createElementNS(NS, tag);
    Object.entries(attrs).forEach(([k, v]) => v != null && n.setAttribute(k, v));
    if (text != null) n.textContent = text;
    if (parent) parent.appendChild(n);
    return n;
  };
  const span = (p) => [p.from, p.to ?? (p.ongoing ? NOW : p.from + 50)];
  const yearText = (y) => (y < 0 ? `${-y} BC` : y < 1000 ? `AD ${y}` : String(y));
  const periodText = (p) => {
    const [a, b] = span(p);
    return `${yearText(a)}–${p.ongoing ? "today" : yearText(b)}${p.flourish ? `, flourished ${yearText(p.flourish[0])}–${yearText(p.flourish[1])}` : ""}`;
  };

  // which rows to show: domains, families (collapsed ones without their types), types matching the search
  function rows(tree, byId, { domain, q, collapsed }) {
    const want = (q || "").trim().toLowerCase(), out = [];
    tree.tree.forEach(([dom, fams]) => {
      if (domain && domain !== dom) return;
      const famRows = [];
      fams.forEach(([fam, ids]) => {
        const hits = ids.filter((id) => !want || byId[id].name.toLowerCase().includes(want) || fam.toLowerCase().includes(want));
        if (!hits.length) return;
        const shut = !want && collapsed.has(fam);
        famRows.push({ kind: "family", label: fam, n: hits.length, shut });
        if (!shut) hits.forEach((id) => famRows.push({ kind: "type", t: byId[id] }));
      });
      if (famRows.length) out.push({ kind: "domain", label: dom }, ...famRows);
    });
    return out;
  }

  function draw(box, tree, opts) {
    const byId = Object.fromEntries(tree.types.map((t) => [t.id, t]));
    const list = rows(tree, byId, opts);
    box.replaceChildren();
    if (!list.length) { box.innerHTML = '<p class="hint">No building type matches.</p>'; return; }
    const W = Math.max(box.clientWidth || 900, 320), L = Math.min(250, Math.round(W * 0.38)), R = 12, TOP = 30;
    const x = (y) => L + (W - L - R) * TimeSlider.toPos(Math.max(-4000, Math.min(NOW, y))) / 1000;
    let y = TOP;
    const at = {};
    list.forEach((r) => { r.y = y; y += ROW[r.kind]; if (r.kind === "type") at[r.t.id] = r.y + ROW.type / 2; });
    const H = y + 24;
    const svg = el("svg", { width: W, height: H, class: "tt-svg", role: "img", "aria-label": "Family tree of building types on a time axis" }, box);
    // axis: ticks at the top and bottom, faint lines between
    const axis = el("g", { class: "tt-axis" }, svg);
    TICKS.forEach((t) => {
      el("line", { x1: x(t), x2: x(t), y1: TOP - 6, y2: H - 20, class: "tt-grid" }, axis);
      [TOP - 10, H - 6].forEach((ty) => el("text", { x: x(t), y: ty, "text-anchor": "middle" }, axis, t === NOW ? "now" : yearText(t)));
    });
    // rows
    const body = el("g", {}, svg);
    list.forEach((r) => {
      if (r.kind === "domain") {
        el("rect", { x: 0, y: r.y + 2, width: W, height: ROW.domain - 4, class: "tt-domain-band" }, body);
        el("text", { x: 6, y: r.y + 19, class: "tt-domain" }, body, r.label);
      } else if (r.kind === "family") {
        const g = el("g", { class: "tt-family", tabindex: 0, role: "button", "aria-expanded": String(!r.shut), "data-family": r.label }, body);
        el("text", { x: 10, y: r.y + 15 }, g, `${r.shut ? "▸" : "▾"} ${r.label}${r.shut ? ` (${r.n})` : ""}`);
      } else {
        const t = r.t, p = t.period, [a, b] = span(p), cy = r.y + ROW.type / 2;
        const g = el("g", { class: "tt-type" + (t.abroad ? " abroad" : ""), tabindex: 0, role: "link", "data-id": t.id }, body);
        el("rect", { x: 0, y: r.y, width: W, height: ROW.type, class: "tt-hit" }, g);
        const n = t.buildings + t.places;
        const max = Math.floor((L - 62) / 6.6);
        el("text", { x: 22, y: cy + 4, class: "tt-label" }, g, t.name.length > max ? t.name.slice(0, max - 1) + "…" : t.name);
        if (n || t.abroad) el("text", { x: L - 6, y: cy + 4, "text-anchor": "end", class: "tt-count" }, g, t.abroad ? "abroad" : n.toLocaleString());
        el("line", { x1: x(a), x2: Math.max(x(b), x(a) + 3), y1: cy, y2: cy, class: "tt-span" + (p.ongoing ? " ongoing" : "") }, g);
        if (p.flourish) el("line", { x1: x(p.flourish[0]), x2: Math.max(x(p.flourish[1]), x(p.flourish[0]) + 3), y1: cy, y2: cy, class: "tt-flourish" }, g);
        if (t.earliest && t.earliest.year != null) el("circle", { cx: x(t.earliest.year), cy, r: 3, class: "tt-earliest" }, g);
        el("title", {}, g, `${t.name} (${t.family}): ${periodText(p)}${n ? `; ${n.toLocaleString()} in the catalogue` : ""}${
          t.earliest ? `; earliest surviving: ${t.earliest.name} (${t.earliest.date_text || yearText(t.earliest.year)})` : ""}`);
      }
    });
    // links: a branch from the earlier type's row down (or up) to the later type, at the later type's first date
    const lg = el("g", { class: "tt-links" }, svg);
    svg.insertBefore(lg, body);
    tree.links.forEach((k) => {
      if (!(k.from in at) || !(k.to in at) || !opts.kinds.has(k.kind)) return;
      const t = byId[k.to], xs = x(t.period.from), y1 = at[k.from], y2 = at[k.to];
      el("path", { d: `M${xs - 6},${y1} H${xs} V${y2} H${xs + 4}`, class: `tt-link ${k.confidence}${byId[k.from].domain !== t.domain ? " far" : ""}`, stroke: cssVar(KINDS[k.kind][1]),
                   "data-from": k.from, "data-to": k.to }, lg);
    });
    // interaction: hover or focus brings a type's links forward; click opens it; families fold
    const focus = (id) => {
      svg.classList.toggle("focus", !!id);
      lg.querySelectorAll("path").forEach((p) => p.classList.toggle("on", !!id && (p.dataset.from === id || p.dataset.to === id)));
    };
    svg.addEventListener("pointerover", (e) => { const g = e.target.closest(".tt-type"); focus(g && g.dataset.id); });
    svg.addEventListener("pointerleave", () => focus(null));
    svg.addEventListener("focusin", (e) => { const g = e.target.closest(".tt-type"); focus(g && g.dataset.id); });
    const act = (e) => {
      const g = e.target.closest(".tt-type, .tt-family");
      if (!g) return;
      if (g.classList.contains("tt-type")) opts.onOpen(g.dataset.id);
      else {
        const f = g.dataset.family;
        opts.collapsed.has(f) ? opts.collapsed.delete(f) : opts.collapsed.add(f);
        draw(box, tree, opts);
        box.querySelector(`.tt-family[data-family="${CSS.escape(f)}"]`)?.focus();
      }
    };
    svg.addEventListener("click", act);
    svg.addEventListener("keydown", (e) => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); act(e); } });
  }

  function legend(kinds) {
    return `<span class="tt-key"><i class="tt-key-span"></i>in use <i class="tt-key-flourish"></i>flourished
      <i class="tt-key-dot"></i>earliest surviving in the catalogue</span>${Object.entries(KINDS).map(([k, [label, c]]) =>
      `<label class="tt-key"><input type="checkbox" data-kind="${k}" ${kinds.has(k) ? "checked" : ""}>
        <i class="tt-key-link" style="border-color:${cssVar(c)}"></i>${esc(label)}</label>`).join("")}
      <span class="tt-key"><i class="tt-key-link disputed"></i>disputed</span><span class="tt-key"><i class="tt-key-link probable"></i>probable</span>`;
  }

  return { draw, legend, periodText, yearText, KINDS, span };
})();
