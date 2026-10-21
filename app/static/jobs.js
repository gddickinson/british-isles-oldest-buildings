// Jobs panel (Data page, setup page): start long jobs (rebuild, photos, map layers…), follow their
// progress with an estimate, stop them. A job runs on after the GUI is closed; reopening the page
// picks it up again from runs/job_status.json (app/jobs_api.py, bidb/progress.py).
const Jobs = (() => {
  const h = (s) => String(s ?? "").replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
  const num = (n) => Number(n || 0).toLocaleString();
  const STATE = { running: "Running", finished: "Finished", failed: "Failed or stopped", died: "Stopped unexpectedly" };

  function dur(s) {
    if (s == null || !isFinite(s)) return "";
    s = Math.max(0, Math.round(s));
    if (s < 60) return `${s} s`;
    if (s < 3600) return `${Math.round(s / 60)} min`;
    return `${Math.floor(s / 3600)} h ${String(Math.round((s % 3600) / 60)).padStart(2, "0")} min`;
  }

  // Overall fraction and time left: stage times from the last successful run when known
  // (weighted), else stage k of n; items done within a stage refine both.
  function estimate(st) {
    const stages = st.stages || [], i = st.index ?? -1, n = stages.length || 1;
    if (st.state === "finished") return { pct: 1, left: 0 };
    const frac = st.items && st.items[1] ? Math.min(1, st.items[0] / st.items[1]) : null;
    const inStage = st.stage_started ? st.now - st.stage_started : 0;
    const stageLeft = frac && frac > 0.02 ? inStage / frac * (1 - frac) : null;
    if (stages.length && stages.every((s) => s.expected != null)) {
      const total = stages.reduce((a, s) => a + s.expected, 0) || 1;
      const before = stages.slice(0, Math.max(i, 0)).reduce((a, s) => a + s.expected, 0);
      const exp = i >= 0 ? stages[i].expected : 0;
      const cur = frac != null ? frac * exp : Math.min(inStage, exp * 0.95);
      const after = stages.slice(i + 1).reduce((a, s) => a + s.expected, 0);
      return { pct: (before + cur) / total, left: (stageLeft ?? Math.max(exp - inStage, exp * 0.05)) + after,
               basis: "estimate from the last run's stage times" };
    }
    return { pct: (Math.max(i, 0) + (frac ?? 0)) / n, left: i === n - 1 ? stageLeft : null, stageLeft,
             basis: "no estimate yet: the first run records how long each stage takes" };
  }

  function statusHTML(st) {
    if (!st || st.state === "none") return `<p class="hint">No job has run yet.</p>`;
    const e = estimate(st), i = st.index ?? -1, stages = st.stages || [];
    const elapsed = (st.finished || st.now) - st.started;
    const cur = stages[i];
    const line = [
      st.state === "running" && cur ? `Stage ${i + 1} of ${stages.length}: <b>${h(cur.name)}</b>` : "",
      st.state === "running" && st.items ? `${num(st.items[0])} of ${num(st.items[1])} items` : "",
      st.downloads || st.cached ? `${num(st.downloads)} downloaded, ${num(st.cached)} from the cache` : "",
      `${dur(elapsed)} ${st.state === "running" ? "so far" : "in all"}`,
      st.state === "running" && e.left != null ? `about ${dur(e.left)} left`
        : st.state === "running" && e.stageLeft != null ? `about ${dur(e.stageLeft)} left in this stage` : "",
    ].filter(Boolean).join(" · ");
    const list = stages.map((s, k) => {
      const mark = s.took != null && (k < i || st.finished) ? "✓" : k === i && st.state === "running" ? "▶" : k === i ? "✗" : "·";
      return `<li class="job-st ${k === i ? "cur" : ""}">${mark} ${h(s.name)}${s.took != null ? ` <span class="hint">${dur(s.took)}</span>` : ""}</li>`;
    }).join("");
    const opts = st.options || {};
    return `<div class="job-head"><b>${h(st.label || st.job)}</b> <span class="job-state ${st.state}">${STATE[st.state] || st.state}</span>
        ${opts.refresh && opts.refresh !== "off" ? `<span class="hint">refresh: ${h(opts.refresh)}</span>` : ""}</div>
      <div class="progress" role="progressbar" aria-valuenow="${Math.round(e.pct * 100)}" aria-valuemin="0" aria-valuemax="100">
        <span style="width:${(e.pct * 100).toFixed(1)}%"></span></div>
      <p class="hint">${line}${st.state === "running" && e.basis ? ` <span title="${h(e.basis)}">ⓘ</span>` : ""}</p>
      ${st.state === "died" ? `<p class="warn-text">The job stopped without finishing (the computer slept or restarted, or the
        process was ended). Start it again: everything already downloaded is kept in the cache.</p>` : ""}
      ${st.state === "failed" && st.message ? `<p class="warn-text">${h(st.message)}</p>` : ""}
      ${st.state === "running" ? `<button type="button" class="btn small ghost" data-stop>Stop</button>
        <span class="hint">It keeps running if you close this window or the app; come back to this page to follow it.</span>` : ""}
      <details><summary>Stages</summary><ul class="job-stages">${list}</ul></details>
      ${st.tail && st.tail.length ? `<details ${st.state !== "finished" ? "open" : ""}><summary>Log</summary>
        <pre class="log">${h(st.tail.join("\n"))}</pre></details>` : ""}`;
  }

  function controlsHTML(info, only) {
    const names = (info.order || Object.keys(info.jobs)).filter((k) => !only || only.includes(k));
    return names.map((k) => {
      const j = info.jobs[k];
      const extra = k === "build" ? `<details class="job-opts"><summary>Options: refresh downloads, cut-off year</summary>
          <div class="set-row"><label>Download again anything older than <input type="number" min="0" step="1" data-o="refresh_days"
            placeholder="—" style="width:5em"> days</label></div>
          <div class="set-row"><span>Download again from these sources only:</span>
            ${Object.entries(info.sources).map(([s, label]) => `<label class="check"><input type="checkbox" data-src="${s}"> ${h(label)}</label>`).join("")}</div>
          <p class="hint">Both empty: everything already downloaded is reused (fast). Sources without a number of days: everything
            from those sources is fetched again. Wikidata and Wikipedia changes made since the last download only arrive this way.</p>
          <div class="set-row"><label>Buildings begun before <input type="number" data-o="cutoff" placeholder="1500" style="width:6em"></label></div>
        </details>` : "";
      return `<div class="job-card" data-job="${k}"><div><b>${h(j.label)}</b> <span class="hint">(${h(j.time)})</span>
        <div class="hint">${h(j.about)}</div>${extra}</div><button type="button" class="btn small" data-start="${k}">Start</button></div>`;
    }).join("");
  }

  function options(card) {
    const o = {};
    card.querySelectorAll("[data-o]").forEach((i) => { if (i.value !== "") o[i.dataset.o] = Number(i.value); });
    o.refresh_sources = [...card.querySelectorAll("[data-src]:checked")].map((i) => i.dataset.src);
    return o;
  }

  async function post(url, body) {
    const r = await fetch(url, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body || {}) });
    const j = await r.json().catch(() => ({}));
    if (!r.ok) (window.UI ? UI.toast((j.problems || ["Failed"]).join(" "), 6000) : alert((j.problems || []).join(" ")));
    return r.ok;
  }

  // el: container; opts.only: job names to offer (null = all, [] = status only); opts.onFinish(status)
  function mount(el, opts = {}) {
    el.innerHTML = `<div class="job-status"></div><div class="job-list"></div>`;
    let timer = null, wasRunning = false;
    async function tick() {
      clearTimeout(timer);
      const info = await fetch("/api/jobs").then((r) => r.json());
      const st = info.status, running = st.state === "running";
      el.querySelector(".job-status").innerHTML = statusHTML(st);
      const stop = el.querySelector("[data-stop]");
      if (stop) stop.addEventListener("click", async () => { stop.disabled = true; await post("/api/jobs/stop"); tick(); });
      const list = el.querySelector(".job-list");
      if (!list.dataset.drawn && opts.only !== undefined && opts.only !== null && !opts.only.length) list.dataset.drawn = "1";
      if (!list.dataset.drawn) {
        list.dataset.drawn = "1";
        list.innerHTML = controlsHTML(info, opts.only);
        list.querySelectorAll("[data-start]").forEach((b) => b.addEventListener("click", async () => {
          b.disabled = true;
          if (await post("/api/jobs/start", { job: b.dataset.start, options: options(b.closest(".job-card")) })) tick();
          else b.disabled = false;
        }));
      }
      list.querySelectorAll("[data-start]").forEach((b) => { b.disabled = running; });
      if (wasRunning && !running && opts.onFinish) opts.onFinish(st);
      wasRunning = running;
      if (running) timer = setTimeout(tick, 2000);
    }
    tick();
    return { refresh: tick };
  }

  return { mount, estimate, dur };
})();
