// Glossary page: terms from /api/glossary (bidb.glossary): search, group chips, A-Z, "see also" links (#term-<slug>).
(async () => {
  const $ = (s) => document.querySelector(s);
  const slug = (t) => t.toLowerCase().normalize("NFD").replace(/[̀-ͯ]/g, "").replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "");
  const data = await api("/api/glossary").catch(() => ({ groups: [], terms: [] }));
  const terms = data.terms, byName = new Map(terms.map((t) => [t.term, t]));
  const url = new URLSearchParams(location.search);
  const S = { q: url.get("q") || "", group: url.get("group") || "" };
  const findable = new Set(["Building types", "Archaeology"]);

  $("#gl_q").value = S.q;
  const counts = {};
  terms.forEach((t) => { counts[t.group] = (counts[t.group] || 0) + 1; });
  $("#gl_groups").innerHTML = [["", `All (${terms.length})`], ...data.groups.filter((g) => counts[g]).map((g) => [g, `${g} (${counts[g]})`])]
    .map(([g, label]) => `<button type="button" data-g="${esc(g)}">${esc(label)}</button>`).join("");

  const entry = (t) => `<div class="gl-entry" id="term-${slug(t.term)}">
    <dt>${esc(t.term)} <span class="gl-group">${esc(t.family || t.group)}</span></dt>
    <dd><p>${esc(t.text)}${t.source ? ` <a class="gl-src" href="${esc(t.source.url)}" target="_blank" rel="noopener" title="${esc(t.source.title)}">FISH</a>` : ""}</p>
    ${t.see.length || t.link || findable.has(t.group) ? `<p class="meta">${[
      t.see.length ? `See also: ${t.see.map((s) => `<a href="#term-${slug(s)}" data-see="${esc(s)}">${esc(s)}</a>`).join(", ")}` : "",
      t.link ? `<a href="${esc(t.link.href)}"${/^https?:/.test(t.link.href) ? ' target="_blank" rel="noopener"' : ""}>${esc(t.link.label)}</a>` : "",
      findable.has(t.group) ? `<a href="/?q=${encodeURIComponent(t.term.replace(/\s*\(.*\)/, ""))}">Find in the catalogue</a>` : "",
    ].filter(Boolean).join(" · ")}</p>` : ""}</dd></div>`;

  function render() {
    const words = S.q.toLowerCase().split(/\s+/).filter(Boolean);
    const rows = terms.filter((t) => (!S.group || t.group === S.group)
      && words.every((w) => `${t.term} ${t.text} ${t.family || ""}`.toLowerCase().includes(w)));
    document.querySelectorAll("#gl_groups button").forEach((b) => b.classList.toggle("on", b.dataset.g === S.group));
    $("#gl_count").textContent = `${rows.length.toLocaleString()} of ${terms.length.toLocaleString()} terms`;
    const letters = [...new Set(rows.map((t) => t.term[0].toUpperCase()))];
    $("#gl_letters").innerHTML = letters.map((l) => `<a href="#gl-${l}">${esc(l)}</a>`).join("");
    let last = "";
    $("#gl_list").innerHTML = rows.map((t) => {
      const l = t.term[0].toUpperCase(), head = l !== last ? `<h2 class="gl-letter" id="gl-${esc(l)}">${esc(l)}</h2>` : "";
      last = l;
      return head + entry(t);
    }).join("") || `<p class="meta">No term matches.</p>`;
    const p = new URLSearchParams();
    if (S.q) p.set("q", S.q);
    if (S.group) p.set("group", S.group);
    history.replaceState(null, "", `${location.pathname}${p.toString() ? "?" + p : ""}${location.hash}`);
  }

  function go(name) {                     // show a "see also" term even when the search or group hides it
    if (!byName.has(name)) return;
    const el = document.getElementById(`term-${slug(name)}`);
    if (!el) { S.q = ""; S.group = ""; $("#gl_q").value = ""; render(); }
    const target = document.getElementById(`term-${slug(name)}`);
    target?.scrollIntoView({ block: "start" });
    target?.classList.add("hit");
    setTimeout(() => target?.classList.remove("hit"), 1600);
  }

  let timer = null;
  $("#gl_q").addEventListener("input", (e) => { clearTimeout(timer); timer = setTimeout(() => { S.q = e.target.value.trim(); render(); }, 150); });
  $("#gl_groups").addEventListener("click", (e) => {
    const b = e.target.closest("button[data-g]");
    if (b) { S.group = b.dataset.g; render(); }
  });
  $("#gl_list").addEventListener("click", (e) => {
    const a = e.target.closest("a[data-see]");
    if (a) { e.preventDefault(); history.replaceState(null, "", `${location.pathname}${location.search}#term-${slug(a.dataset.see)}`); go(a.dataset.see); }
  });
  render();
  if (location.hash.startsWith("#term-")) {
    const t = terms.find((x) => `#term-${slug(x.term)}` === location.hash);
    if (t) go(t.term);
  }
})();
