// Researched claims with their evidence (bidb/evidence.py, data/curated/evidence.json): fills any
// [data-evidence="<record id>"] element in a detail view; Evidence.table() lists every claim (Data quality page).
const Evidence = (() => {
  let ALL = null;
  const all = () => (ALL = ALL || api("/api/evidence").catch(() => ({})));
  const KIND = { primary: "Primary source", listing: "Heritage listing", secondary: "History or report", reference: "Reference work" };
  const CHECK = { "quote-found": ["✓ quote found in the source", "verify-ok"], "quote-missing": ["✗ quote not found", "verify-bad"],
                  unreachable: ["source unreachable", "verify-bad"] };
  const VERDICT = { kept: "Catalogue value confirmed", corrected: "Catalogue corrected", open: "Still open" };
  const source = (s) => {
    const [check, cls] = CHECK[s.check] || ["not checked yet", ""];
    return `<li><span class="chip">${esc(KIND[s.kind] || s.kind)}</span>
      ${s.url ? `<a href="${esc(s.url)}" target="_blank" rel="noopener">${esc(s.title)}</a>` : esc(s.title)}
      ${s.author ? `<span class="meta">${esc(s.author)}</span>` : ""}${s.locator ? ` <span class="meta">(${esc(s.locator)})</span>` : ""}
      <blockquote>“${esc(s.quote)}”</blockquote><span class="hint ${cls}">${check}</span></li>`;
  };
  const claimHTML = (c) => `<div class="claim"><p><b>${esc(VERDICT[c.verdict] || c.verdict)}:</b> ${esc(c.claim)}</p>
    <p class="hint">${esc(c.assessment || "")} <i>Researched ${esc(c.researched || "")}.</i></p>
    <ul class="evidence-sources">${c.sources.map(source).join("")}</ul></div>`;

  async function mount(el) {
    el.dataset.evidenceDone = "1";
    const claims = (await all())[el.dataset.evidence] || [];
    if (claims.length) el.innerHTML = `<h4>Evidence</h4>${claims.map(claimHTML).join("")}`;
  }
  async function table(box) {
    const rows = Object.values(await all()).flat();
    if (!rows.length) return;
    box.innerHTML = `<table class="grid small"><thead><tr><th>Record</th><th>Claim</th><th>Verdict</th><th>Sources</th></tr></thead>
      <tbody>${rows.map((c) => `<tr><td>${c.record.startsWith("research:") ? `${esc(c.name)} <span class="meta">(${
        c.research && c.research.startsWith("events:") ? "history event" : "oldest of its type"})</span>`
        : `<a href="${buildingUrl(c.record)}">${esc(c.name)}</a>`}</td><td>${esc(c.claim)}</td>
      <td>${esc(VERDICT[c.verdict] || c.verdict)}</td><td>${c.sources.map((s) => `${esc(KIND[s.kind] || s.kind)}: ${
        (CHECK[s.check] || ["not checked"])[0]}`).join("<br>")}</td></tr>`).join("")}</tbody></table>`;
  }
  const scan = (root) => root.querySelectorAll && root.querySelectorAll("[data-evidence]:not([data-evidence-done])").forEach(mount);
  new MutationObserver((ms) => ms.forEach((m) => m.addedNodes.forEach((n) => n.nodeType === 1 && scan(n.parentNode || n))))
    .observe(document.documentElement, { childList: true, subtree: true });
  document.addEventListener("DOMContentLoaded", () => scan(document));
  return { table };
})();
