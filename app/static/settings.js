// Settings page: browser preferences (Prefs), data location and screenshot browser (server).
const $s = (sel) => document.querySelector(sel);
const gb = (n) => (n == null ? "?" : n >= 1e9 ? `${(n / 1e9).toFixed(n >= 1e11 ? 0 : 1)} GB` : `${Math.round(n / 1e6)} MB`);

// ---- preferences ---------------------------------------------------------------------
function bindPrefs() {
  document.querySelectorAll("[data-pref]").forEach((el) => {
    const k = el.dataset.pref, v = Prefs.get(k);
    if (el.type === "checkbox") el.checked = !!v; else el.value = String(v);
    el.addEventListener("change", () => {
      const val = el.type === "checkbox" ? el.checked : el.dataset.num ? +el.value : el.value;
      Prefs.set(k, val);
      if (k === "mapBase") { try { localStorage.removeItem("bi_map_base"); } catch (e) { /* blocked */ } }
      if (k === "recent" && !val) Prefs.recent.clear();
      drawRecent();
      UI.toast("Saved");
    });
  });
  $s("#s_layers_reset").addEventListener("click", () => {
    ["bi_map_layers", "bi_map_base", "bi_map_historic"].forEach((k) => { try { localStorage.removeItem(k); } catch (e) { /* blocked */ } });
    UI.toast("Map layers reset to the defaults");
  });
}

function drawRecent() {
  const l = Prefs.recent.list(), box = $s("#s_recent_list");
  if (!Prefs.get("recent")) { box.innerHTML = ""; return; }
  box.innerHTML = l.length ? `<p class="hint">Recently viewed (${l.length}) · <button type="button" class="linklike" id="s_recent_clear">clear</button></p>
    <ul class="nearby">${l.slice(0, 12).map((r, i) => `<li><a href="#" data-recent="${i}">${esc(r.name)}</a> <span class="meta">${esc(r.type)} · ${new Date(r.t).toLocaleDateString()}</span></li>`).join("")}</ul>`
    : `<p class="hint">Nothing viewed yet.</p>`;
  box.querySelectorAll("[data-recent]").forEach((a) => a.addEventListener("click", (e) => { e.preventDefault(); UI.openRecord(l[+a.dataset.recent]); }));
  $s("#s_recent_clear")?.addEventListener("click", () => { Prefs.recent.clear(); drawRecent(); });
}

// two clicks instead of a confirm() dialog
function confirmButton(btn, label, fn) {
  let armed = 0;
  const original = btn.textContent;
  btn.addEventListener("click", () => {
    if (Date.now() - armed < 4000) { fn(); btn.textContent = original; armed = 0; return; }
    armed = Date.now(); btn.textContent = label;
    setTimeout(() => { if (armed && Date.now() - armed >= 4000) { btn.textContent = original; armed = 0; } }, 4100);
  });
}

function bindBackup() {
  $s("#s_export").addEventListener("click", () => {
    const a = Object.assign(document.createElement("a"), { download: "british_isles_settings.json",
      href: URL.createObjectURL(new Blob([JSON.stringify(Prefs.exportAll(), null, 2)], { type: "application/json" })) });
    document.body.append(a); a.click(); a.remove();
  });
  $s("#s_import").addEventListener("change", async (e) => {
    const f = e.target.files[0];
    if (!f) return;
    try { Prefs.importAll(JSON.parse(await f.text())); UI.toast("Loaded; reloading…"); setTimeout(() => location.reload(), 800); }
    catch (err) { UI.toast("Could not load that file: " + err.message, 5000); }
  });
  confirmButton($s("#s_reset"), "Click again to reset", () => { Prefs.reset(); location.reload(); });
  confirmButton($s("#s_clear"), "Click again: clears lists too", () => {
    Prefs.STORE_KEYS.forEach((k) => { try { localStorage.removeItem(k); } catch (e) { /* blocked */ } });
    location.reload();
  });
}

// ---- data location (local app only) ----------------------------------------------------
let SETTINGS = null, pollTimer = null;

async function loadServer() {
  if (IS_STATIC) return;
  SETTINGS = await fetch("/api/settings").then((r) => r.json());
  drawItems(); drawVolumes(); drawJob(SETTINGS.data.job);
  $s("#s_chrome_found").textContent = SETTINGS.chrome || "None found: screenshots are unavailable until you set one.";
  $s("#s_chrome").value = SETTINGS.chrome_custom || "";
}

function drawItems() {
  const items = SETTINGS.data.items, vols = SETTINGS.data.volumes;
  $s("#dl_items").innerHTML = Object.entries(items).map(([key, it]) => `
    <div class="dl-item ${it.available ? "" : "missing"}" data-item="${key}">
      <div class="dl-head"><b>${esc(it.label)}</b> <span class="chip ${it.available ? "" : "warn"}">${it.available ? "available" : "not available: drive unplugged?"}</span>
        ${it.is_default ? `<span class="chip">in the project folder</span>` : ""}</div>
      <p class="hint">${esc(it.about)}</p>
      <dl><dt>Folder</dt><dd><code>${esc(it.path)}</code></dd>
        <dt>Size</dt><dd>${gb(it.bytes)} · ${it.files.toLocaleString()} file${it.files === 1 ? "" : "s"}</dd>
        <dt>Free on that drive</dt><dd>${gb(it.free)} of ${gb(it.total)}</dd></dl>
      <div class="dl-move">
        <label>Move to <select class="dl-dest">
          ${vols.filter((v) => v.writable).map((v) => `<option value="${esc(v.path)}">${esc(v.name)} (${gb(v.free)} free)</option>`).join("")}
          <option value="__other">Another folder…</option></select></label>
        <span class="dl-other hidden"><input type="text" class="dl-path" placeholder="/Volumes/MyDrive/somewhere">
          <button type="button" class="btn small ghost dl-browse">Browse…</button></span>
        <label><select class="dl-mode"><option value="move">Move (delete the old copy after checking)</option>
          <option value="copy">Copy (keep the old copy as a backup)</option>
          <option value="use">Use a copy that is already there</option></select></label>
        <button type="button" class="btn small dl-check">Check</button>
        ${it.is_default ? "" : `<button type="button" class="btn small ghost dl-home">Move back to the project folder</button>`}
      </div>
      <div class="dl-result"></div>
      <div class="dl-browser hidden"></div>
    </div>`).join("");
  document.querySelectorAll(".dl-item").forEach(bindItem);
}

function bindItem(box) {
  const item = box.dataset.item, dest = box.querySelector(".dl-dest"), other = box.querySelector(".dl-other");
  const result = box.querySelector(".dl-result");
  const chosen = () => (dest.value === "__other" ? box.querySelector(".dl-path").value.trim() : dest.value);
  dest.addEventListener("change", () => other.classList.toggle("hidden", dest.value !== "__other"));
  box.querySelector(".dl-browse").addEventListener("click", () => folderBrowser(box, box.querySelector(".dl-path").value || "/Volumes"));
  box.querySelector(".dl-check").addEventListener("click", () => check(item, chosen(), box.querySelector(".dl-mode").value, result));
  box.querySelector(".dl-home")?.addEventListener("click", () => check(item, SETTINGS.server.project, "move", result));
}

async function check(item, dest, mode, result) {
  if (!dest) { result.innerHTML = `<p class="warn-text">Choose a destination.</p>`; return; }
  let target = dest, problems = [];
  if (mode !== "use") {
    const r = await fetch("/api/settings/location/check", { method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ item, dest }) }).then((x) => x.json());
    target = r.dest; problems = r.problems;
  }
  const verb = { move: "Move", copy: "Copy", use: "Switch" }[mode];
  result.innerHTML = problems.length
    ? `<p class="warn-text">${problems.map(esc).join("<br>")}</p>`
    : `<p>${verb} to <code>${esc(target)}</code>${mode === "move" ? " and delete the old copy once every file has been checked" : ""}.
       <button type="button" class="btn small dl-go">${verb} now</button></p>`;
  result.querySelector(".dl-go")?.addEventListener("click", () => start(item, mode === "use" ? dest : target, mode, result));
}

async function start(item, dest, mode, result) {
  const r = await fetch("/api/settings/location", { method: "POST", headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ item, dest, mode, suggest: false }) });
  const j = await r.json();
  if (!j.ok) { result.innerHTML = `<p class="warn-text">${(j.problems || []).map(esc).join("<br>")}</p>`; return; }
  result.innerHTML = "";
  poll();
}

function drawJob(job) {
  const box = $s("#dl_job");
  if (!job) { box.classList.add("hidden"); return; }
  box.classList.remove("hidden");
  const pct = job.total_bytes ? Math.round(100 * job.copied_bytes / job.total_bytes) : (job.phase === "done" ? 100 : 0);
  box.innerHTML = `<b>${esc(job.mode === "copy" ? "Copying" : job.mode === "use" ? "Switching" : "Moving")} the ${esc(job.item)}</b>
    <span class="chip ${job.phase === "failed" ? "warn" : ""}">${esc(job.phase)}</span>
    ${job.total_bytes ? `<div class="progress"><span style="width:${pct}%"></span></div>
      <p class="hint">${(job.copied_files || 0).toLocaleString()} of ${(job.total_files || 0).toLocaleString()} files · ${gb(job.copied_bytes)} of ${gb(job.total_bytes)}</p>` : ""}
    ${job.message ? `<p>${esc(job.message)}</p>` : ""}`;
}

function poll() {
  clearTimeout(pollTimer);
  fetch("/api/settings/location").then((r) => r.json()).then((j) => {
    drawJob(j.job);
    if (j.job && !["done", "failed"].includes(j.job.phase)) pollTimer = setTimeout(poll, 1000);
    else { loadServer(); if (j.job) UI.toast(j.job.phase === "done" ? "Done" : "The move failed; the old location is still in use", 5000); }
  });
}

async function folderBrowser(box, path) {
  const panel = box.querySelector(".dl-browser");
  const r = await fetch("/api/settings/browse?path=" + encodeURIComponent(path));
  if (!r.ok) { panel.innerHTML = `<p class="warn-text">Cannot open ${esc(path)}</p>`; panel.classList.remove("hidden"); return; }
  const j = await r.json();
  panel.classList.remove("hidden");
  panel.innerHTML = `<div class="hint"><code>${esc(j.path)}</code> ${j.writable ? "" : "(read-only)"}</div>
    <ul class="folder-list">${j.parent ? `<li><a href="#" data-dir="${esc(j.parent)}">⬑ up</a></li>` : ""}
      ${j.dirs.map((d) => `<li><a href="#" data-dir="${esc(j.path.replace(/\/$/, "") + "/" + d)}">📁 ${esc(d)}</a></li>`).join("")}</ul>
    <button type="button" class="btn small" data-pick="${esc(j.path)}">Use this folder</button>
    <button type="button" class="btn small ghost" data-close="1">Close</button>`;
  panel.querySelectorAll("[data-dir]").forEach((a) => a.addEventListener("click", (e) => { e.preventDefault(); folderBrowser(box, a.dataset.dir); }));
  panel.querySelector("[data-pick]").addEventListener("click", (e) => { box.querySelector(".dl-path").value = e.target.dataset.pick; panel.classList.add("hidden"); });
  panel.querySelector("[data-close]").addEventListener("click", () => panel.classList.add("hidden"));
}

function drawVolumes() {
  $s("#dl_volumes").innerHTML = `<table class="data-table"><thead><tr><th>Drive</th><th>Path</th><th>Free</th><th>Size</th><th></th></tr></thead><tbody>
    ${SETTINGS.data.volumes.map((v) => `<tr><td>${esc(v.name)}</td><td><code>${esc(v.path)}</code></td><td>${gb(v.free)}</td><td>${gb(v.total)}</td>
      <td>${v.writable ? "" : "read-only"}</td></tr>`).join("")}</tbody></table>`;
}

function bindChrome() {
  $s("#s_chrome_save").addEventListener("click", async () => {
    const r = await fetch("/api/settings", { method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ chrome: $s("#s_chrome").value.trim() }) });
    const j = await r.json();
    if (!j.ok) { UI.toast((j.problems || ["Not saved"]).join(" "), 5000); return; }
    UI.toast("Saved"); loadServer();
  });
}

async function drawStreetAreas() {
  const box = $s("#s_streets");
  if (!box) return;
  const s = await fetch("/api/street_tiles").then((r) => r.json()).catch(() => ({ areas: [] }));
  box.innerHTML = s.areas.length ? `<ul>${s.areas.map((a) => `<li>${esc(a.name)} <span class="hint">${a.tiles} tiles, ${a.mb} MB,
    saved ${new Date(a.saved * 1000).toLocaleDateString()}</span></li>`).join("")}</ul>
    <button type="button" class="btn small ghost" id="s_streets_clear">Delete all saved street maps</button>` : "<p class='hint'>None saved yet.</p>";
  const clear = $s("#s_streets_clear");
  if (clear) clear.onclick = async () => { await fetch("/api/street_tiles", { method: "DELETE" }); drawStreetAreas(); UI.toast("Deleted"); };
}

bindPrefs(); drawRecent(); bindBackup(); if (!IS_STATIC) drawStreetAreas();
if (!IS_STATIC) { bindChrome(); loadServer().then(() => { if (SETTINGS.data.job && !["done", "failed"].includes(SETTINGS.data.job.phase)) poll(); }); }
