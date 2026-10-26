// "Trade and industry here" (roadmap C9): fills any [data-trade-here="<record id>"] element in a detail view with the
// trade stories the building or place belongs to (links to /trades) and the innovations made or first used there.
(() => {
  const url = (id) => `${IS_STATIC ? "trades.html" : "/trades"}?t=${encodeURIComponent(id)}`;
  async function mount(el) {
    el.dataset.tradeDone = "1";
    const h = await api("/api/trade_here/" + encodeURIComponent(el.dataset.tradeHere)).catch(() => null);
    if (!h || (!h.trades.length && !h.made.length)) return;
    el.innerHTML = `<h4>Trade and industry here</h4>${h.made.length ? `<p>${h.made.map(([id, name, year]) =>
      `💡 <a href="#" data-place="${esc(id)}">${esc(name)}</a>${year != null ? ` (${year})` : ""}`).join("<br>")}</p>` : ""}${
      h.trades.length ? `<p>Part of the story of ${h.trades.map(([id, title]) => `<a href="${url(id)}">${esc(title.toLowerCase())}</a>`).join(", ")}.</p>` : ""}`;
  }
  const scan = (root) => root.querySelectorAll && root.querySelectorAll("[data-trade-here]:not([data-trade-done])").forEach(mount);
  new MutationObserver((ms) => ms.forEach((m) => m.addedNodes.forEach((n) => n.nodeType === 1 && scan(n.parentNode || n))))
    .observe(document.documentElement, { childList: true, subtree: true });
  document.addEventListener("DOMContentLoaded", () => scan(document));
})();
