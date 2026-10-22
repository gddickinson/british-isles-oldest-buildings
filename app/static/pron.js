// Pronunciations: the box under a name in detail views (any element with data-pron="<record id>"
// is filled automatically), the play button, and data access for the Pronunciation page.
// Hosted copy: answers from data/pron.json; recordings open on Wikimedia Commons there.
const Pron = (() => {
  let STATIC = null;
  const COLS = ["name", "lang", "variety", "ipa", "respell", "audio", "source", "source_url", "entity_kind", "entity_id"];

  function loadStatic() {
    STATIC = STATIC || fetch("data/pron.json").then((r) => r.json()).then((d) => {
      const rows = d.rows.map((a) => Object.fromEntries(COLS.map((c, i) => [c, a[i] || ""])));
      const byId = new Map();
      rows.forEach((r) => { if (!byId.has(r.entity_id)) byId.set(r.entity_id, []); byId.get(r.entity_id).push(r); });
      return { rows, byId, towns: d.towns || {}, coverage: d.coverage || {} };
    }).catch(() => ({ rows: [], byId: new Map(), towns: {} }));
    return STATIC;
  }

  async function forRecord(id) {
    if (!IS_STATIC) return api("/api/pron/" + encodeURIComponent(id));
    const d = await loadStatic();
    return { own: d.byId.get(id) || [],
             towns: (d.towns[id] || []).map(([tid, name]) => ({ id: tid, name, rows: d.byId.get(tid) || [] }))
                                       .filter((t) => t.rows.length) };
  }

  const said = (r) => r.ipa || r.respell || r.audio;
  async function search(p) {      // p: {q, variety, kind, limit, offset}
    if (!IS_STATIC) return api("/api/pronunciations?" + new URLSearchParams(p));
    const d = await loadStatic(), q = (p.q || "").toLowerCase(), seen = new Set();
    const hits = d.rows.filter((r) => said(r) && (!q || r.name.toLowerCase().includes(q))
      && (!p.variety || r.variety === p.variety) && (!p.kind || r.entity_kind === p.kind))
      .filter((r) => { const k = [r.name, r.variety, r.ipa, r.respell, r.audio].join("|");   // as bidb.pron_db.search
                       return !seen.has(k) && seen.add(k); })
      .sort((a, b) => a.name.localeCompare(b.name));
    const off = +p.offset || 0;
    return { total: hits.length, rows: hits.slice(off, off + (+p.limit || 60)) };
  }

  async function varieties() {
    if (!IS_STATIC) return api("/api/pronunciations/varieties");
    const d = await loadStatic(), n = {}, seen = new Set();
    d.rows.filter(said).forEach((r) => {
      const k = [r.name, r.variety, r.ipa, r.respell, r.audio].join("|");
      if (!seen.has(k)) { seen.add(k); n[r.variety] = (n[r.variety] || 0) + 1; } });
    return Object.entries(n).sort((a, b) => b[1] - a[1]).map(([variety, count]) => ({ variety, count }));
  }

  async function coverage() {
    return IS_STATIC ? (await loadStatic()).coverage : api("/api/pronunciations/coverage");
  }

  // Commons file -> page / original / MP3 transcode (same scheme as bidb/pron_db.audio_urls)
  function audioUrls(r) {
    if (r.audio_urls && r.audio_urls.page) return r.audio_urls;
    if (!r.audio) return {};
    let f = r.audio.replace(/ /g, "_");
    f = f[0].toUpperCase() + f.slice(1);
    return { page: "https://commons.wikimedia.org/wiki/File:" + encodeURIComponent(f) };
  }

  function playButton(r) {
    const u = audioUrls(r);
    if (!u.page) return "";
    if (IS_STATIC || !u.src) {
      return `<a class="pron-play" href="${esc(u.page)}" target="_blank" rel="noopener" title="Listen on Wikimedia Commons">▶</a>`;
    }
    return `<button type="button" class="pron-play" data-src="${esc(u.src)}" data-mp3="${esc(u.mp3)}" data-page="${esc(u.page)}"
      title="Play recording (${esc(r.audio)})" aria-label="Play recording of ${esc(r.name)}">▶</button>`;
  }

  function rowHTML(r, showName) {
    const ipa = r.ipa ? `<span class="ipa" title="International Phonetic Alphabet">/${esc(r.ipa.replace(/^\/|\/$/g, ""))}/</span>` : "";
    const sp = r.respell ? `<span class="respell" title="Say it like this">${esc(r.respell)}</span>` : "";
    const name = showName || !(ipa || sp || r.audio) ? `<span class="pron-name" lang="${esc(r.lang)}">${esc(r.name)}</span>` : "";
    return `<li><span class="pron-var">${esc(r.variety)}</span> ${name} ${ipa} ${sp} ${playButton(r)}</li>`;
  }

  function html(data, title) {
    const keep = (rows) => rows.filter((r) => said(r) || (Prefs.get("pronNative") && r.lang !== "en"));
    const own = keep(data.own || []);
    const ownSaid = new Set(own.map((r) => r.ipa + "|" + r.respell));
    const towns = (data.towns || []).map((t) => ({ ...t, rows: keep(t.rows).filter(said) }))
      .filter((t) => t.rows.length && !t.rows.every((r) => ownSaid.has(r.ipa + "|" + r.respell) || (!r.ipa && !r.respell && own.some((o) => o.audio))));
    if (!own.length && !towns.length) return "";
    const sources = [...new Set([...own, ...towns.flatMap((t) => t.rows)].map((r) => r.source))].join(", ");
    return `<div class="pron-box">
      ${own.length ? `<ul class="pron-list">${own.map((r) => rowHTML(r, r.name !== title)).join("")}</ul>` : ""}
      ${towns.map((t) => `<div class="pron-town"><span class="hint">Saying ${esc(t.name)}:</span>
        <ul class="pron-list">${t.rows.slice(0, 3).map((r) => rowHTML(r, r.name !== t.name)).join("")}</ul></div>`).join("")}
      <p class="hint pron-src">From ${esc(sources)}${[...own, ...towns.flatMap((t) => t.rows)].some((r) => r.audio)
        ? "; recordings from Wikimedia Commons (▶; author and licence on the file page)" : ""}.
        <a href="${UI.href("/help")}#pronunciation">About pronunciations</a></p></div>`;
  }

  async function mount(el) {
    el.dataset.pronDone = "1";
    if (!Prefs.get("pron")) return;
    try {
      el.innerHTML = html(await forRecord(el.dataset.pron), el.dataset.pronTitle || "");
    } catch (e) { /* no pronunciations table yet */ }
  }

  let current = null;
  document.addEventListener("click", (e) => {
    const b = e.target.closest("button.pron-play");
    if (!b) return;
    if (current) current.pause();
    const a = new Audio();
    a.src = a.canPlayType("audio/ogg; codecs=vorbis") || !/\.(ogg|oga|opus|wav)$/i.test(b.dataset.src) ? b.dataset.src : b.dataset.mp3;
    a.onerror = () => { if (a.src !== b.dataset.mp3) { a.src = b.dataset.mp3; a.play().catch(() => null); }
                        else UI.toast("Could not play the recording; opening it on Wikimedia Commons"), window.open(b.dataset.page, "_blank"); };
    b.classList.add("playing");
    a.onended = a.onpause = () => b.classList.remove("playing");
    a.play().catch(() => null);
    current = a;
  });

  const scan = (root) => root.querySelectorAll && root.querySelectorAll("[data-pron]:not([data-pron-done])").forEach(mount);
  new MutationObserver((ms) => ms.forEach((m) => m.addedNodes.forEach((n) => n.nodeType === 1 && scan(n.parentNode || n))))
    .observe(document.body, { childList: true, subtree: true });
  document.addEventListener("DOMContentLoaded", () => scan(document));
  scan(document);

  return { forRecord, search, varieties, coverage, html, rowHTML, playButton, mount };
})();
