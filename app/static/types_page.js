// Building types page (/types, BT4a): the family tree on a time axis (TypeTree) with domain chips, a search and the
// link kinds to draw; the materials and techniques by group; charts through time (TypeTime, BT5, ?tab=time&year=);
// one type (?t=<id>) or material (?m=<id>) (TypeView).
(async () => {
  const $ = (s) => document.querySelector(s);
  const tree = await api("/api/type_tree");
  const state = { domain: "", q: "", kinds: new Set(Object.keys(TypeTree.KINDS)), collapsed: new Set() };
  let mats = null, cents = null, timeDrawn = false;

  $("#ty_domains").innerHTML = [["", "All"], ...tree.tree.map(([d]) => [d, d])]
    .map(([d, label]) => `<button type="button" data-d="${esc(d)}" class="${d === state.domain ? "on" : ""}">${esc(label)}</button>`).join("");
  const isles = tree.types.filter((t) => !t.abroad);
  $("#ty_count").textContent = `${isles.length} building types of the isles in ${tree.tree.length} domains (and ${
    tree.types.length - isles.length} types abroad they came from), ${tree.links.length} sourced links`;

  const drawTree = () => {
    $("#ty_legend").innerHTML = TypeTree.legend(state.kinds);
    TypeTree.draw($("#ty_tree"), tree, { ...state, onOpen: (id) => go({ t: id }) });
  };

  async function drawMaterials() {
    mats = mats || await api("/api/materials");
    const by = Object.fromEntries(mats.materials.map((m) => [m.id, m]));
    $("#ty_mats").innerHTML = `<p class="prose">${mats.materials.length} materials and techniques of building, each with its period, regions and
      the technology behind it, cited from published sources; the catalogue's records are linked to them from Wikidata,
      the official register descriptions and Wikipedia, with the sentence that names the material.</p>${mats.groups.map(([g, ids]) => `<h3>${esc(g)}</h3>
      <ul class="nearby ty-matlist">${ids.map((id) => by[id]).filter(Boolean).map((m) => `<li><a href="?m=${encodeURIComponent(m.id)}" data-gom="${esc(m.id)}">${esc(m.name)}</a>
        <span class="meta">${esc(m.kind)} · ${esc(TypeTree.periodText(m.period))}${m.buildings + m.places ? ` · ${(m.buildings + m.places).toLocaleString()} in the catalogue` : ""}${
          m.earliest ? ` · earliest: ${esc(m.earliest.name)} (${esc(m.earliest.date_text || TypeTree.yearText(m.earliest.year))})` : ""}</span></li>`).join("")}</ul>`).join("")}`;
  }

  async function drawTime() {
    const y = +new URLSearchParams(location.search).get("year") || 1500;
    if (!timeDrawn) TypeTime.inUse($("#ty_inuse"), tree, {
      year: y, onOpen: (yr) => history.replaceState(null, "", location.pathname + "?" + new URLSearchParams({ tab: "time", year: yr })) });
    timeDrawn = true;
    cents = cents || await api("/api/material_centuries");
    if (!$("#ty_matcent .tt-heat")) TypeTime.materials($("#ty_matcent"), cents);
  }

  // which view: the tree, the materials, the charts through time, one type or one material
  async function show() {
    const p = new URLSearchParams(location.search), t = p.get("t"), m = p.get("m"), tab = p.get("tab") || "tree";
    const one = t || m;
    $("#ty_lists").hidden = !!one;
    $("#ty_one").hidden = !one;
    document.querySelectorAll("#ty_tabs .tab").forEach((b) => b.classList.toggle("active", !one && b.dataset.tab === tab));
    if (one) {
      const box = $("#ty_one_body");
      box.innerHTML = '<p class="hint">Loading…</p>';
      const d = await api(t ? `/api/type_page/${encodeURIComponent(t)}` : `/api/material/${encodeURIComponent(m)}`).catch(() => null);
      if (!d) { box.innerHTML = '<p class="hint">Not found.</p>'; return; }
      document.title = `${t ? d.type.name : d.material.name} · Building types · British Isles Oldest Buildings`;
      t ? TypeView.type(box, d) : TypeView.material(box, d);
      window.scrollTo(0, 0);
      return;
    }
    document.title = "Building types · British Isles Oldest Buildings";
    $("#ty_tree_view").hidden = tab !== "tree";
    $("#ty_mats").hidden = tab !== "materials";
    $("#ty_time").hidden = tab !== "time";
    tab === "tree" ? drawTree() : tab === "time" ? drawTime() : drawMaterials();
  }
  function go(params) {
    history.pushState(null, "", location.pathname + "?" + new URLSearchParams(params));
    show();
  }

  $("#ty_domains").addEventListener("click", (e) => {
    const b = e.target.closest("button[data-d]");
    if (!b) return;
    state.domain = b.dataset.d;
    document.querySelectorAll("#ty_domains button").forEach((x) => x.classList.toggle("on", x === b));
    drawTree();
  });
  $("#ty_q").addEventListener("input", (e) => { state.q = e.target.value; drawTree(); });
  $("#ty_legend").addEventListener("change", (e) => {
    const k = e.target.dataset.kind;
    if (!k) return;
    e.target.checked ? state.kinds.add(k) : state.kinds.delete(k);
    drawTree();
  });
  $("#ty_fold").addEventListener("click", () => {
    const all = tree.tree.flatMap(([, fams]) => fams.map(([f]) => f));
    state.collapsed = state.collapsed.size ? new Set() : new Set(all);
    $("#ty_fold").textContent = state.collapsed.size ? "Open all families" : "Fold all families";
    drawTree();
  });
  $("#ty_tabs").addEventListener("click", (e) => { const b = e.target.closest(".tab"); if (b) go({ tab: b.dataset.tab }); });
  $("#ty_back").addEventListener("click", (e) => { e.preventDefault(); history.length > 1 ? history.back() : go({}); });
  document.addEventListener("click", (e) => {
    const a = e.target.closest("[data-go], [data-gom]");
    if (!a || !a.closest(".types-page")) return;
    e.preventDefault();
    go(a.dataset.go ? { t: a.dataset.go } : { m: a.dataset.gom });
  });
  window.addEventListener("popstate", show);
  let width = window.innerWidth;
  window.addEventListener("resize", () => {
    if (Math.abs(window.innerWidth - width) < 40 || !$("#ty_one").hidden) return;
    width = window.innerWidth;
    if (!$("#ty_tree_view").hidden) drawTree();
    if (!$("#ty_time").hidden) { timeDrawn = false; drawTime(); }
  });
  show();
})();
