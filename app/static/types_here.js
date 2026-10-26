// "Building type and materials" (BT4a, BT3c1): fills any [data-types-here="<record id>"] element in a detail view with
// the building types of the record or place (links to its page on /types, "see its family") and the materials and
// techniques found for it, each with how it was found and the sentence that names it.
(() => {
  const url = (k, id) => `${IS_STATIC ? "types.html" : "/types"}?${k}=${encodeURIComponent(id)}`;
  const VIA = { wikidata: "Wikidata", wikipedia: "Wikipedia", register: "the register" };
  async function mount(el) {
    el.dataset.typesDone = "1";
    const h = await api("/api/types_here/" + encodeURIComponent(el.dataset.typesHere)).catch(() => null);
    if (!h || (!h.types.length && !h.materials.length)) return;
    const [main, ...rest] = h.types;
    const mats = {};
    h.materials.forEach((m) => { (mats[m.id] = mats[m.id] || { ...m, found: [] }).found.push(m); });
    el.innerHTML = `<h4>Building type and materials</h4>${main ? `<p>${main.primary ? "This is" : "Used as"} ${/^[aeiou]/i.test(main.name) ? "an" : "a"}
      <a href="${url("t", main.id)}">${esc(main.name)}</a> (${esc(main.family || "")}): <a href="${url("t", main.id)}">see its family</a>.${
      rest.length ? ` Also: ${rest.map((t) => `<a href="${url("t", t.id)}">${esc(t.name)}</a>`).join(", ")}.` : ""}</p>` : ""}${
      Object.keys(mats).length ? `<details><summary>Materials and techniques: ${Object.values(mats).map((m) => esc(m.name)).join(", ")}</summary>
        <ul class="ty-here-mats">${Object.values(mats).map((m) => `<li><a href="${url("m", m.id)}">${esc(m.name)}</a> <span class="meta">from ${
          [...new Set(m.found.map((f) => VIA[f.via] || f.via))].join(", ")}</span>${m.found.filter((f) => f.evidence).slice(0, 1).map((f) =>
          `<br><span class="hint">“${esc(f.evidence.length > 260 ? f.evidence.slice(0, 259) + "…" : f.evidence)}”</span>`).join("")}</li>`).join("")}</ul></details>` : ""}`;
  }
  const scan = (root) => root.querySelectorAll && root.querySelectorAll("[data-types-here]:not([data-types-done])").forEach(mount);
  new MutationObserver((ms) => ms.forEach((m) => m.addedNodes.forEach((n) => n.nodeType === 1 && scan(n.parentNode || n))))
    .observe(document.documentElement, { childList: true, subtree: true });
  document.addEventListener("DOMContentLoaded", () => scan(document));
})();
