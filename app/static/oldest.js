// "Oldest of each type": the earliest dated examples per category, with claims vs evidence.
let OLD = [];

function exampleHTML(ex) {
  const img = ex.image_thumb ? `<img loading="lazy" src="${esc(ex.image_thumb)}" alt="">`
                             : `<div class="noimg small">${CAT_ICON[ex.category] || "📍"}</div>`;
  return `<a class="ex" href="${buildingUrl(ex.id)}">${img}<div>
    <b>${esc(ex.name)}</b><div class="date">${dateHTML(ex)}</div>
    <div class="meta">${esc([ex.locality, ex.nation].filter(Boolean).join(" · "))}</div>
    ${ex.type_claim ? `<div class="claim">${esc(ex.type_claim.split(". Source:")[0])}</div>` : ""}</div></a>`;
}

function render() {
  const g = document.getElementById("o_group").value, q = document.getElementById("o_q").value.toLowerCase();
  const shown = OLD.filter((c) => (!g || c.group === g) && (!q || c.category.toLowerCase().includes(q)));
  document.getElementById("o_index").innerHTML = shown.map((c) =>
    `<a href="#t-${encodeURIComponent(c.category)}">${CAT_ICON[c.category] || ""} ${esc(c.category)}</a>`).join("");
  document.getElementById("o_list").innerHTML = shown.map((c) => `
    <section class="type-block" id="t-${encodeURIComponent(c.category)}">
      <h2><span class="dot" style="background:${groupColor(c.group)}"></span>${esc(c.category)}
        <span class="hint">${c.count.toLocaleString()} in the catalogue ·
        <a href="${IS_STATIC ? "index.html" : "/"}?category=${encodeURIComponent(c.category)}">see all</a></span></h2>
      <div class="examples">${c.examples.map((ex) => exampleHTML({ ...ex, category: c.category })).join("")}</div>
    </section>`).join("") || "<p class='empty'>No types match.</p>";
}

async function init() {
  OLD = await api("/api/oldest?per=8");
  GROUPS.concat(["Other"]).forEach((grp) => document.getElementById("o_group").insertAdjacentHTML(
    "beforeend", `<option>${esc(grp)}</option>`));
  ["o_group", "o_q"].forEach((id) => document.getElementById(id).addEventListener("input", render));
  render();
}
init();
window.addEventListener("thumbs-loaded", render);
