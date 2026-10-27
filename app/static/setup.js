// First-run setup page: bundled database, existing data folder, or build from scratch (app/jobs_api.py).
(() => {
  const $ = (s) => document.querySelector(s);
  const h = (s) => String(s ?? "").replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
  let jobs = null;

  async function post(body) {
    const r = await fetch("/api/setup", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });
    const j = await r.json().catch(() => ({}));
    if (!r.ok) { $("#su_problems").innerHTML = (j.problems || ["Failed"]).map((p) => `<p class="warn-text">${h(p)}</p>`).join(""); return null; }
    $("#su_problems").innerHTML = j.message ? `<p class="ok-text">${h(j.message)}</p>` : "";
    return j;
  }

  function ready(st) {
    if (st.db_exists) { $("#su_done").classList.remove("hidden"); location.href = "/"; }
  }

  function follow() {
    $("#su_progress").classList.remove("hidden");
    if (!jobs) jobs = Jobs.mount($("#su_jobs"), { only: [], onFinish: async () => ready(await fetch("/api/setup").then((r) => r.json())) });
    else jobs.refresh();
  }

  async function init() {
    const st = await fetch("/api/setup").then((r) => r.json());
    if (st.db_exists) { ready(st); return; }
    $("#su_db").textContent = st.db;
    $("#su_problems").innerHTML = st.problems.map((p) => `<p class="warn-text">${h(p)}</p>`).join("");
    const b = st.bundled;
    $("#su_bundled").innerHTML = b ? `The database that comes with the app (${b.mb} MB packed, made ${h(b.date)}${b.local ? ""
      : "; downloaded from the project's GitHub release, no sign-in needed"}): every
      building, place, story and tour as of then. Photos and the street map load from the internet as you browse.
      Rebuild later on the Data quality page to bring it up to date.` : "No bundled database in this copy of the app.";
    $("#su_use_bundled").disabled = !b;
    $("#su_cache").value = st.settings.cache_dir || "";
    const job = await fetch("/api/jobs").then((r) => r.json());
    if (job.status.state === "running" || (["build", "bundled"].includes(job.status.job) && job.status.state !== "none")) follow();

    $("#su_use_bundled").addEventListener("click", async (e) => {
      e.target.disabled = true; e.target.textContent = "Unpacking…";
      const j = await post({ action: "bundled" });
      e.target.textContent = "Use the bundled database";
      if (j && j.job) follow(); else if (j) ready(j.status); else e.target.disabled = false;
    });
    $("#su_use_folder").addEventListener("click", async () => {
      const j = await post({ action: "use", folder: $("#su_folder").value.trim() });
      if (j) ready(j.status);
    });
    $("#su_browse").addEventListener("click", () => browse($("#su_folder").value || "/Volumes"));
    $("#su_build").addEventListener("click", async (e) => {
      e.target.disabled = true;
      if (await post({ action: "build", cache_folder: $("#su_cache").value.trim() })) follow();
      else e.target.disabled = false;
    });
  }

  async function browse(path) {
    const panel = $("#su_browser");
    const r = await fetch("/api/settings/browse?path=" + encodeURIComponent(path));
    panel.classList.remove("hidden");
    if (!r.ok) { panel.innerHTML = `<p class="warn-text">Cannot open ${h(path)}</p>`; return; }
    const j = await r.json();
    panel.innerHTML = `<div class="hint"><code>${h(j.path)}</code></div>
      <ul class="folder-list">${j.parent ? `<li><a href="#" data-dir="${h(j.parent)}">⬑ up</a></li>` : ""}
        ${j.dirs.map((d) => `<li><a href="#" data-dir="${h(j.path.replace(/\/$/, "") + "/" + d)}">📁 ${h(d)}</a></li>`).join("")}</ul>
      <button type="button" class="btn small" data-pick="${h(j.path)}">Choose this folder</button>`;
    panel.querySelectorAll("[data-dir]").forEach((a) => a.addEventListener("click", (e) => { e.preventDefault(); browse(a.dataset.dir); }));
    panel.querySelector("[data-pick]").addEventListener("click", () => { $("#su_folder").value = j.path; panel.classList.add("hidden"); });
  }

  init();
})();
