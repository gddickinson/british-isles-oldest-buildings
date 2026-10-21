// "Then": paintings, prints and drawings of a building or place (bidb/depictions.py, Wikidata P180).
// Fills any [data-then="<record id>"] element in a detail view. The hosted copy cannot show images
// from Wikimedia Commons, so it lists the works with links instead.
const Then = (() => {
  let ALL = null;
  const load = (id) => (IS_STATIC
    ? (ALL = ALL || fetch("data/depictions.json").then((r) => r.json()).catch(() => ({}))).then((d) => (d[id] || [])
      .map(([title, creator, year, image]) => ({ title, creator, year, image })))
    : api("/api/depictions/" + encodeURIComponent(id)).catch(() => []));
  const page = (image) => `https://commons.wikimedia.org/wiki/File:${encodeURIComponent(image.replace(/ /g, "_"))}`;
  const caption = (a) => `${esc(a.title)}${a.creator ? ` <span class="meta">${esc(a.creator)}</span>` : ""}${
    a.year ? ` <span class="meta">${a.year}</span>` : ""}`;

  async function mount(el) {
    el.dataset.thenDone = "1";
    const arts = await load(el.dataset.then);
    if (!arts.length) return;
    el.innerHTML = `<h4>Then: paintings, prints and drawings</h4>${IS_STATIC
      ? `<ul class="nearby">${arts.map((a) => `<li><a href="${page(a.image)}" target="_blank" rel="noopener">${caption(a)}</a></li>`).join("")}</ul>`
      : `<div class="then-grid">${arts.map((a) => `<figure><a href="${page(a.image)}" target="_blank" rel="noopener">
          <img loading="lazy" src="${esc(a.thumb)}" alt="${esc(a.title)}"></a><figcaption>${caption(a)}</figcaption></figure>`).join("")}</div>`}
      <p class="hint">From Wikidata and Wikimedia Commons; each image's author and licence are on its file page.</p>`;
  }
  const scan = (root) => root.querySelectorAll && root.querySelectorAll("[data-then]:not([data-then-done])").forEach(mount);
  new MutationObserver((ms) => ms.forEach((m) => m.addedNodes.forEach((n) => n.nodeType === 1 && scan(n.parentNode || n))))
    .observe(document.documentElement, { childList: true, subtree: true });
  document.addEventListener("DOMContentLoaded", () => scan(document));
  return { load };
})();
