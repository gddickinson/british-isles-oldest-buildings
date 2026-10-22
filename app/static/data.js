// Data quality page: gaps report, rebuild trigger with progress, last build diff.
const GAP_LABELS = { no_image: "No image", no_coordinates: "No coordinates", no_date: "No date",
  estimated_date: "Date estimated from type", no_nation: "No nation", no_designation: "No heritage designation",
  date_conflict: "Date conflicts between sources" };
let GAPS = null;

function renderGapRows() {
  const k = document.getElementById("g_kind").value, g = GAPS[k];
  document.getElementById("g_hint").textContent = g.count > g.rows.length ? `showing the oldest ${g.rows.length} of ${g.count}` : "";
  document.getElementById("g_rows").innerHTML = `<table class="grid small"><thead><tr><th>Name</th><th>Nation</th>
    <th>County</th><th>Date</th><th>Fix at source</th></tr></thead><tbody>${g.rows.map((r) => `<tr>
    <td><a href="${buildingUrl(r.id)}">${esc(r.name)}</a></td><td>${esc(r.nation || "")}</td><td>${esc(r.county || "")}</td>
    <td>${esc(r.date_text || "")}${r.date_check_note && k === "date_conflict" ? `<div class="hint">${esc(r.date_check_note)}</div>` : ""}</td><td>${r.wikidata_id ? `<a class="ext" target="_blank" rel="noopener"
      href="https://www.wikidata.org/wiki/${esc(r.wikidata_id)}">Wikidata ↗</a>` : ""}</td></tr>`).join("")}</tbody></table>`;
}

async function renderDiff() {
  const info = await api("/api/build_info").catch(() => ({}));
  const d = info.build_diff, b = info.build_info || {};
  if (!d) { document.getElementById("rb_diff").innerHTML = "<p class='hint'>No comparison available yet.</p>"; return; }
  const list = (title, items) => items.length ? `<details><summary>${esc(title)} (${items.length} shown)</summary>
    <ul>${items.map((i) => `<li>${esc(i)}</li>`).join("")}</ul></details>` : "";
  document.getElementById("rb_diff").innerHTML = `<p>Built ${esc(b.built || "?")} · ${(b.records || 0).toLocaleString()} records:
    <b>${d.added}</b> added, <b>${d.removed}</b> removed, <b>${d.redated}</b> re-dated.</p>
    ${list("Added", d.examples.added)}${list("Removed", d.examples.removed)}${list("Re-dated", d.examples.redated)}`;
}

// Researched files (history events, oldest-of-type claims) checked against their own sources
async function renderVerification() {
  const v = await api("/api/verification").catch(() => null);
  const box = document.getElementById("v_box");
  if (!box || !v || !v.summary) return;
  const LABEL = { confirmed: "Confirmed in source", evidenced: "Confirmed by researched evidence", "year-missing": "Year not found in source",
                  "name-missing": "Name not found in source", unreachable: "Source unreachable" };
  const rows = [...Object.entries(v.events || {}).map(([k, x]) => ["History event", k, x]),
                ...Object.entries(v.examples || {}).map(([k, x]) => ["Oldest of type", k.replace("|", ": "), x])];
  box.innerHTML = `<div class="tiles">${Object.entries(v.summary).map(([k, n]) =>
      `<div class="tile"><span>${esc(LABEL[k] || k)}</span><b>${n}</b></div>`).join("")}</div>
    <details><summary>All ${rows.length} checks</summary><div class="table-wrap"><table class="grid small"><thead><tr>
      <th>Kind</th><th>Item</th><th>Result</th><th>Evidence from the source</th></tr></thead><tbody>${rows.map(([kind, k, x]) => `<tr>
      <td>${esc(kind)}</td><td>${x.source ? `<a href="${esc(x.source)}" target="_blank" rel="noopener">${esc(k)}</a>` : esc(k)}</td>
      <td class="${["confirmed", "evidenced"].includes(x.status) ? "verify-ok" : "verify-bad"}">${esc(LABEL[x.status] || x.status)}</td>
      <td>${esc(x.evidence || "")}</td></tr>`).join("")}</tbody></table></div></details>`;
}

async function init() {
  GAPS = await api("/api/gaps");
  document.getElementById("g_tiles").innerHTML = Object.entries(GAP_LABELS).map(([k, label]) =>
    `<div class="tile"><span>${esc(label)}</span><b>${GAPS[k].count.toLocaleString()}</b></div>`).join("");
  const sel = document.getElementById("g_kind");
  sel.innerHTML = Object.entries(GAP_LABELS).map(([k, l]) => `<option value="${k}">${esc(l)}</option>`).join("");
  sel.addEventListener("change", renderGapRows);
  renderGapRows();
  renderDiff();
  renderVerification();
  Evidence.table(document.getElementById("e_box"));
  const panel = document.getElementById("jobs_panel");
  if (panel) Jobs.mount(panel, { onFinish: (st) => { if (st.job === "build" && st.state === "finished") renderDiff(); } });
}
init();

// Pronunciation coverage and hard names still missing one
Pron.coverage().then((c) => {
  if (!c || !c.entities) return;
  const e = c.entities, kinds = [["building", "buildings"], ["place", "places"], ["person", "people"], ["town", "towns and areas"]];
  document.getElementById("pr_cov").innerHTML = `<p>${kinds.map(([k, l]) => `<b>${(e[k] || 0).toLocaleString()}</b> ${l}`).join(" · ")}
      have their own entry; <b>${(c.records_with_town || 0).toLocaleString()}</b> records lie in a town that has one.</p>
    <table class="grid small"><thead><tr><th>Variety</th><th>Entries</th><th>With IPA</th><th>Recordings</th></tr></thead><tbody>
    ${c.varieties.slice(0, 20).map((v) => `<tr><td><a href="${UI.href("/pronunciation")}?variety=${encodeURIComponent(v.variety)}">${esc(v.variety)}</a></td>
      <td>${v.rows.toLocaleString()}</td><td>${v.ipa.toLocaleString()}</td><td>${v.audio.toLocaleString()}</td></tr>`).join("")}</tbody></table>
    ${c.missing && c.missing.length ? `<details><summary>${c.missing.length} hard-looking names with no pronunciation</summary>
      <table class="grid small"><tbody>${c.missing.map((r) => `<tr><td><a href="${buildingUrl(r.id)}">${esc(r.name)}</a></td>
      <td>${esc(r.nation || "")}</td><td>${r.wikipedia_title ? `<a class="ext" target="_blank" rel="noopener" href="https://en.wikipedia.org/wiki/${encodeURIComponent(r.wikipedia_title.replace(/ /g, "_"))}">Wikipedia ↗</a>` : ""}
      ${r.wikidata_id ? `<a class="ext" target="_blank" rel="noopener" href="https://www.wikidata.org/wiki/${esc(r.wikidata_id)}">Wikidata ↗</a>` : ""}</td></tr>`).join("")}</tbody></table></details>` : ""}`;
}).catch(() => null);
