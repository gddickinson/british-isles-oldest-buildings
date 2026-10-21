// Stories: legends, ghosts, folklore and curious history. Any element with data-stories="<record id>"
// (detail views) is filled automatically; search/counts serve the Stories page and tours.
// Hosted copy: answers from data/stories.json (loaded the first time a story is needed).
const Stories = (() => {
  const KINDS = { supernatural: ["Ghosts & the supernatural", "👻"], legend: ["Legends & myths", "🐉"],
                  folklore: ["Folklore & customs", "🌿"], curiosity: ["Curious history", "🗝"] };
  const COLS = ["entity_kind", "entity_id", "kind", "heading", "text", "source_url", "name", "nation", "locality",
                "lat", "lon", "date_text", "licence"];
  let STATIC = null;
  const loadStatic = () => (STATIC = STATIC || fetch("data/stories.json").then((r) => r.json()).then((d) => {
    const rows = d.rows.map((a) => Object.fromEntries(COLS.map((c, i) => [c, a[i] ?? ""])));
    const byId = new Map();
    rows.forEach((r) => { if (!byId.has(r.entity_id)) byId.set(r.entity_id, []); byId.get(r.entity_id).push(r); });
    return { rows, byId };
  }).catch(() => ({ rows: [], byId: new Map() })));

  const label = (k) => (KINDS[k] || [k])[0];
  // "OGL (Cadw)" -> "the Cadw register (OGL)"; default Wikipedia
  const source = (s) => { const m = /^OGL \((.+)\)$/.exec(s.licence || "");
    return m ? `the ${m[1]} register (OGL)` : /Wikidata/.test(s.licence || "") ? "Wikidata (CC0)" : "Wikipedia (CC BY-SA)"; };
  const icon = (k) => (KINDS[k] || ["", "•"])[1];

  async function forRecord(id) {
    if (!IS_STATIC) return api("/api/stories/" + encodeURIComponent(id));
    return (await loadStatic()).byId.get(id) || [];
  }

  async function search(p) {        // p: {q, kind, nation, limit, offset}
    if (!IS_STATIC) return api("/api/stories?" + new URLSearchParams(p));
    const d = await loadStatic(), words = (p.q || "").toLowerCase().split(/\s+/).filter(Boolean);
    const hits = d.rows.filter((r) => (!p.kind || r.kind === p.kind) && (!p.nation || r.nation === p.nation)
      && words.every((w) => `${r.text} ${r.name} ${r.locality}`.toLowerCase().includes(w)))
      .sort((a, b) => /^Wikipedia lists/.test(a.text) - /^Wikipedia lists/.test(b.text) || b.text.length - a.text.length);
    const off = +p.offset || 0;
    return { total: hits.length, rows: hits.slice(off, off + (+p.limit || 60)) };
  }

  async function counts() {
    if (!IS_STATIC) return api("/api/stories_counts");
    const d = await loadStatic(), n = {};
    const seen = new Set();
    d.rows.forEach((r) => { const k = r.kind + "|" + r.entity_id; if (!seen.has(k)) { seen.add(k); n[r.kind] = (n[r.kind] || 0) + 1; } });
    return Object.keys(KINDS).map((k) => ({ kind: k, label: label(k), count: n[k] || 0 }));
  }

  function storyHTML(s, withRecord) {
    const head = s.heading && !/^(History|Background|Description)$/i.test(s.heading) ? ` · ${esc(s.heading)}` : "";
    return `<article class="story story-${esc(s.kind)}">
      <div class="story-kind">${icon(s.kind)} ${esc(label(s.kind))}${head}</div>
      ${withRecord ? `<h3><a href="#" data-story-open="${esc(s.entity_kind)}" data-id="${esc(s.entity_id)}">${esc(s.name)}</a>
        <span class="hint">${esc([s.date_text, s.locality || s.nation].filter(Boolean).join(" · "))}</span></h3>` : ""}
      <p>${esc(s.text)}</p>
      ${Stories.canSpeak() ? `<button class="speak" type="button" data-speak="${esc(s.text)}" title="Read aloud" aria-label="Read aloud">🔊</button>` : ""}
      <div class="story-src">From <a href="${esc(s.source_url)}" target="_blank" rel="noopener">${esc(source(s))}</a></div>
    </article>`;
  }

  async function mount(el) {
    el.dataset.storiesDone = "1";
    try {
      const rows = await forRecord(el.dataset.stories);
      if (rows.length) el.innerHTML = `<h4>Stories &amp; legends</h4>${rows.map((s) => storyHTML(s, false)).join("")}`;
    } catch (e) { /* no stories table yet */ }
  }

  // Read aloud (browser speech synthesis, British English voice when there is one)
  const canSpeak = () => "speechSynthesis" in window;
  function speak(texts, onDone) {
    if (!canSpeak()) return;
    speechSynthesis.cancel();
    const voice = speechSynthesis.getVoices().find((v) => v.lang === "en-GB") || null;
    [].concat(texts).forEach((t, i, all) => {
      const u = new SpeechSynthesisUtterance(t);
      if (voice) u.voice = voice;
      u.lang = "en-GB"; u.rate = 0.95;
      if (i === all.length - 1 && onDone) u.onend = onDone;
      speechSynthesis.speak(u);
    });
  }
  const stop = () => canSpeak() && speechSynthesis.cancel();
  document.addEventListener("click", (e) => {
    const b = e.target.closest("[data-speak]");
    if (!b) return;
    e.preventDefault();
    if (canSpeak() && speechSynthesis.speaking) { stop(); return; }
    speak(b.dataset.speak);
  });

  document.addEventListener("click", (e) => {
    const a = e.target.closest("[data-story-open]");
    if (!a) return;
    e.preventDefault();
    if (a.dataset.storyOpen === "place") openPlace(a.dataset.id);
    else location.href = buildingUrl(a.dataset.id);
  });

  // Timeline of a building (bidb/timeline.py): dated events from its article, earliest first
  const TL_ICON = { "Built or founded": "🏗", Rebuilt: "🔨", Enlarged: "➕", Restored: "🛠", Fire: "🔥", Destroyed: "💥",
    "War and siege": "⚔", Dissolved: "⛪", "Changed hands": "🤝", Opened: "🔑", "Closed or abandoned": "🚪",
    Protected: "🛡", "Visitors and residents": "👑" };
  async function timeline(id) {
    if (!IS_STATIC) return api("/api/timeline/" + encodeURIComponent(id));
    const b = await api("/api/building/" + encodeURIComponent(id));
    return ((b && b.timeline) || []).map(([year, label, text]) => ({ year, label, text }));
  }
  async function mountTimeline(el) {
    el.dataset.timelineDone = "1";
    const rows = await timeline(el.dataset.timeline).catch(() => []);
    if (!rows.length) return;
    const yr = (y) => (y < 0 ? `${-y} BC` : y);
    el.innerHTML = `<details class="timeline" ${rows.length <= 6 ? "open" : ""}><summary><h4>Timeline (${rows.length})</h4></summary>
      <ol>${rows.map((r) => `<li><span class="tl-year">${yr(r.year)}</span><span class="tl-kind">${TL_ICON[r.label] || "•"} ${esc(r.label)}</span>
        <p>${esc(r.text)}</p></li>`).join("")}</ol><p class="hint">Dated sentences from the Wikipedia article.</p></details>`;
  }

  const scan = (root) => {
    if (!root.querySelectorAll) return;
    root.querySelectorAll("[data-stories]:not([data-stories-done])").forEach(mount);
    root.querySelectorAll("[data-timeline]:not([data-timeline-done])").forEach(mountTimeline);
  };
  new MutationObserver((ms) => ms.forEach((m) => m.addedNodes.forEach((n) => n.nodeType === 1 && scan(n.parentNode || n))))
    .observe(document.body, { childList: true, subtree: true });
  document.addEventListener("DOMContentLoaded", () => scan(document));
  scan(document);

  return { KINDS, label, icon, forRecord, search, counts, storyHTML, speak, stop, canSpeak };
})();
