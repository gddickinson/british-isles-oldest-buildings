// Top-bar tools (theme, export, help, settings), keyboard shortcuts, "Go to" quick search (⌘K),
// toasts and back-to-top. The Export menu's items come from ui_export.js.
const UI = (() => {
  const PAGES = [
    ["Catalogue", "/", "c"], ["Map", "/map", "m"], ["Places", "/places", "p"], ["People", "/people", "e"],
    ["Pronunciation", "/pronunciation", "n"], ["Stories", "/stories", "l"], ["Tours", "/tours", "t"], ["Quiz", "/quiz", "q"],
    ["History", "/history", "h"], ["Oldest by type", "/oldest", "o"], ["Statistics", "/stats", "s"],
    ["Compare", "/compare", "r"], ["Data quality", "/data", "d"],
    ["Settings", "/settings", ","], ["Help", "/help", "?"],
  ];
  const STATIC_FILES = { "/": "index.html", "/map": "map.html", "/places": "places.html", "/people": "people.html", "/pronunciation": "pronunciation.html",
    "/history": "history.html", "/oldest": "oldest.html", "/stats": "stats.html", "/tours": "tours.html", "/trip": "tours.html", "/stories": "stories.html", "/quiz": "quiz.html",
    "/compare": "compare.html", "/data": "data.html", "/settings": "settings.html", "/help": "help.html" };
  const href = (path) => (IS_STATIC ? STATIC_FILES[path.split("#")[0]] + (path.includes("#") ? "#" + path.split("#")[1] : "") : path);
  const typing = (e) => /^(INPUT|TEXTAREA|SELECT)$/.test(e.target.tagName) || e.target.isContentEditable;

  // ---- toasts ---------------------------------------------------------------------
  function toast(msg, ms = 2600) {
    let box = document.getElementById("toasts");
    if (!box) { box = Object.assign(document.createElement("div"), { id: "toasts" }); box.setAttribute("role", "status"); document.body.append(box); }
    const t = Object.assign(document.createElement("div"), { className: "toast", textContent: msg });
    box.append(t);
    setTimeout(() => t.remove(), ms);
  }

  // ---- dropdown menus ----------------------------------------------------------------
  function closeMenus(except) {
    document.querySelectorAll(".tb-menu.open").forEach((m) => { if (m !== except) { m.classList.remove("open"); m.querySelector("button").setAttribute("aria-expanded", "false"); } });
  }
  function menu(id, label, title, itemsFn) {
    const wrap = Object.assign(document.createElement("div"), { className: "tb-menu", id });
    wrap.innerHTML = `<button type="button" class="tb-btn" aria-haspopup="true" aria-expanded="false" title="${title}">${label}</button><div class="tb-pop" role="menu"></div>`;
    const btn = wrap.querySelector("button"), pop = wrap.querySelector(".tb-pop");
    btn.addEventListener("click", (e) => {
      e.stopPropagation();
      const open = !wrap.classList.contains("open");
      closeMenus(wrap);
      if (open) { pop.innerHTML = ""; itemsFn().forEach((it) => pop.append(item(it))); }
      wrap.classList.toggle("open", open);
      btn.setAttribute("aria-expanded", String(open));
      if (open) pop.querySelector("a, button")?.focus();
    });
    return wrap;
  }
  function item(it) {
    if (it.sep) return Object.assign(document.createElement("div"), { className: "tb-sep", textContent: it.sep });
    const el = document.createElement(it.href ? "a" : "button");
    el.className = "tb-item" + (it.disabled ? " disabled" : "");
    el.setAttribute("role", "menuitem");
    el.innerHTML = `<span>${it.label}</span>${it.key ? `<kbd>${it.key}</kbd>` : ""}`;
    if (it.title) el.title = it.title;
    if (it.href) { el.href = it.href; if (it.download) el.setAttribute("download", ""); if (it.external) el.target = "_blank"; }
    else el.type = "button";
    if (it.action && !it.disabled) el.addEventListener("click", (e) => { e.preventDefault(); closeMenus(); it.action(); });
    return el;
  }

  function helpItems() {
    const page = document.body.dataset.page || "catalogue";
    return [
      { label: "Help & guide", href: href("/help") },
      { label: "Help for this page", href: href("/help#" + page) },
      { label: "Keyboard shortcuts", key: "?", action: shortcutsOverlay },
      { label: "Go to… (quick search)", key: "⌘K", action: palette },
      { sep: "About the data" },
      { label: "Sources & licences", href: href("/help#sources") },
      { label: "Data quality & known gaps", href: href("/data") },
      { label: "About this project", href: href("/help#about") },
    ];
  }

  function buildToolbar() {
    const bar = document.querySelector(".topbar");
    if (!bar || bar.querySelector(".tb-tools")) return;
    const tools = Object.assign(document.createElement("div"), { className: "tb-tools" });
    const theme = Object.assign(document.createElement("button"), { type: "button", className: "tb-btn", title: "Light / dark theme (T)" });
    const paintTheme = () => { theme.textContent = Prefs.effectiveTheme() === "dark" ? "☀" : "☾"; theme.setAttribute("aria-label", "Switch to " + (Prefs.effectiveTheme() === "dark" ? "light" : "dark") + " theme"); };
    theme.addEventListener("click", () => { Prefs.toggleTheme(); paintTheme(); });
    paintTheme();
    window.addEventListener("prefs-changed", paintTheme);
    const search = Object.assign(document.createElement("button"), { type: "button", className: "tb-btn", title: "Go to… (⌘K)",
      innerHTML: '<svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="11" cy="11" r="7"/><path d="m20 20-4-4"/></svg>' });
    search.setAttribute("aria-label", "Go to a page or record");
    search.addEventListener("click", palette);
    const settings = Object.assign(document.createElement("a"), { className: "tb-btn" + (document.body.dataset.page === "settings" ? " active" : ""), href: href("/settings"), title: "Settings (G then ,)",
      innerHTML: '<svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.7 1.7 0 0 0 .3 1.8l.1.1a2 2 0 1 1-2.8 2.8l-.1-.1a1.7 1.7 0 0 0-1.8-.3 1.7 1.7 0 0 0-1 1.5V21a2 2 0 1 1-4 0v-.1a1.7 1.7 0 0 0-1.1-1.5 1.7 1.7 0 0 0-1.8.3l-.1.1a2 2 0 1 1-2.8-2.8l.1-.1a1.7 1.7 0 0 0 .3-1.8 1.7 1.7 0 0 0-1.5-1H3a2 2 0 1 1 0-4h.1a1.7 1.7 0 0 0 1.5-1.1 1.7 1.7 0 0 0-.3-1.8l-.1-.1a2 2 0 1 1 2.8-2.8l.1.1a1.7 1.7 0 0 0 1.8.3H9a1.7 1.7 0 0 0 1-1.5V3a2 2 0 1 1 4 0v.1a1.7 1.7 0 0 0 1 1.5 1.7 1.7 0 0 0 1.8-.3l.1-.1a2 2 0 1 1 2.8 2.8l-.1.1a1.7 1.7 0 0 0-.3 1.8V9a1.7 1.7 0 0 0 1.5 1H21a2 2 0 1 1 0 4h-.1a1.7 1.7 0 0 0-1.5 1z"/></svg>' });
    settings.setAttribute("aria-label", "Settings");
    tools.append(search, menu("tb-export", "⤓ Export", "Export data, screenshot or print", () => (typeof ExportMenu !== "undefined" ? ExportMenu.items() : [])),
                 menu("tb-help", "? Help", "Help", helpItems), theme, settings);
    bar.append(tools);
    document.addEventListener("click", () => closeMenus());
  }

  // ---- keyboard ----------------------------------------------------------------------
  let gPressed = 0;
  function onKey(e) {
    if (e.key === "Escape") { closeMenus(); closeOverlay(); return; }
    if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "k") { e.preventDefault(); palette(); return; }
    if (!Prefs.get("shortcuts") || typing(e) || e.metaKey || e.ctrlKey || e.altKey) return;
    if (Date.now() - gPressed < 1200) {
      const hit = PAGES.find(([, , k]) => k === e.key);
      gPressed = 0;
      if (hit) { location.href = href(hit[1]); e.preventDefault(); }
      return;
    }
    if (e.key === "g") { gPressed = Date.now(); return; }
    if (e.key === "/") {
      const box = document.querySelector("#q, #pq, #people_q, input[type=search]");
      if (box) { e.preventDefault(); box.focus(); box.select?.(); }
    } else if (e.key === "?") { e.preventDefault(); shortcutsOverlay(); }
    else if (e.key === "t") { Prefs.toggleTheme(); }
    else if (e.key === "x") { document.querySelector("#tb-export > button")?.click(); }
  }

  // ---- overlays (shortcuts, quick search) ------------------------------------------
  function overlay(html, cls) {
    closeOverlay();
    const o = Object.assign(document.createElement("div"), { id: "ui-overlay", className: "ui-overlay " + (cls || "") });
    o.innerHTML = `<div class="ui-card" role="dialog" aria-modal="true">${html}</div>`;
    o.addEventListener("click", (e) => { if (e.target === o) closeOverlay(); });
    document.body.append(o);
    return o;
  }
  function closeOverlay() { document.getElementById("ui-overlay")?.remove(); }

  function shortcutsOverlay() {
    const rows = [["/", "Search on this page"], ["⌘K or Ctrl+K", "Go to a page, building, place or person"], ["?", "This list"],
      ["T", "Light / dark theme"], ["X", "Export menu"], ["Esc", "Close menus and dialogs"]]
      .concat(PAGES.map(([name, , k]) => [`G then ${k}`, name]));
    overlay(`<h3>Keyboard shortcuts</h3><table class="kbd-table">${rows.map(([k, v]) => `<tr><td><kbd>${esc(k)}</kbd></td><td>${esc(v)}</td></tr>`).join("")}</table>
      <p class="hint">${Prefs.get("shortcuts") ? "Turn shortcuts off on the Settings page." : "Single-key shortcuts are off (Settings); ⌘K and Esc still work."}</p>
      <button class="btn small" type="button" onclick="UI.closeOverlay()">Close</button>`);
  }

  function palette() {
    const o = overlay(`<input id="pal-q" type="search" placeholder="Go to a page, or search buildings, places and people…" autocomplete="off">
      <ul id="pal-list" class="pal-list" role="listbox"></ul><p class="hint">↑ ↓ to choose · Enter to open · Esc to close</p>`, "palette");
    const q = o.querySelector("#pal-q"), list = o.querySelector("#pal-list");
    let items = [], sel = 0, seq = 0;
    const draw = () => {
      list.innerHTML = items.map((it, i) => `<li role="option" class="${i === sel ? "sel" : ""}" data-i="${i}"><span class="pal-kind">${esc(it.kind)}</span>${esc(it.label)}${it.meta ? ` <span class="meta">${esc(it.meta)}</span>` : ""}</li>`).join("")
        || `<li class="meta">Nothing found</li>`;
      list.querySelectorAll("li[data-i]").forEach((li) => li.addEventListener("click", () => go(items[+li.dataset.i])));
    };
    const go = (it) => { if (!it) return; closeOverlay(); it.go(); };
    const pageItems = (t) => PAGES.filter(([n]) => !t || n.toLowerCase().includes(t)).map(([n, p]) => ({ kind: "Page", label: n, go: () => (location.href = href(p)) }));
    const recentItems = () => Prefs.recent.list().slice(0, 6).map((r) => ({ kind: "Recent", label: r.name, meta: r.type, go: () => openRecord(r) }));
    async function update() {
      const t = q.value.trim().toLowerCase(), mine = ++seq;
      items = t ? pageItems(t) : recentItems().concat(pageItems(""));
      sel = 0; draw();
      if (t.length < 2) return;
      const [b, pl, pe] = await Promise.all([
        api(`/api/search?q=${encodeURIComponent(t)}&limit=6`).catch(() => ({ rows: [] })),
        api(`/api/places?q=${encodeURIComponent(t)}&limit=4`).catch(() => ({ rows: [] })),
        api(`/api/people?q=${encodeURIComponent(t)}&limit=4`).catch(() => ({ rows: [] }))]);
      if (mine !== seq) return;
      items = items.concat(
        (b.rows || []).map((r) => ({ kind: "Building", label: r.name, meta: r.date_text || "", go: () => openRecord({ id: r.id, type: "building" }) })),
        (pl.rows || []).map((r) => ({ kind: "Place", label: r.name, meta: r.kind_label || "", go: () => openRecord({ id: r.id, type: "place" }) })),
        (pe.rows || []).map((r) => ({ kind: "Person", label: r.name, meta: r.description || "", go: () => openRecord({ id: r.id, type: "person" }) })));
      draw();
    }
    q.addEventListener("input", update);
    q.addEventListener("keydown", (e) => {
      if (e.key === "ArrowDown") { sel = Math.min(sel + 1, items.length - 1); draw(); e.preventDefault(); }
      else if (e.key === "ArrowUp") { sel = Math.max(sel - 1, 0); draw(); e.preventDefault(); }
      else if (e.key === "Enter") { go(items[sel]); e.preventDefault(); }
    });
    update(); q.focus();
  }

  function openRecord(r) {
    if (r.type === "building") location.href = buildingUrl(r.id);
    else if (r.type === "place") openPlace(r.id);          // render_places.js: a modal on any page
    else openPerson(r.id);
  }

  // ---- back to top ---------------------------------------------------------------------
  function backToTop() {
    const b = Object.assign(document.createElement("button"), { type: "button", className: "to-top", title: "Back to top", textContent: "↑" });
    b.setAttribute("aria-label", "Back to top");
    b.addEventListener("click", () => window.scrollTo({ top: 0, behavior: Prefs.get("motion") === "reduce" ? "auto" : "smooth" }));
    document.body.append(b);
    addEventListener("scroll", () => b.classList.toggle("show", scrollY > 900), { passive: true });
  }

  document.addEventListener("keydown", onKey);
  buildToolbar();
  backToTop();
  return { toast, closeOverlay, palette, shortcutsOverlay, href, openRecord, PAGES };
})();
