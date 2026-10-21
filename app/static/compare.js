// Compare up to three buildings side by side.
const ROWS = [["Date built", "date_text"], ["Date basis", "date_confidence"], ["Period", "period"],
  ["Category", "category"], ["Type (Wikidata)", "classes"], ["Status", "status"], ["Nation", "nation"],
  ["County", "county"], ["Locality", "locality"], ["Heritage grade", "heritage_grade"],
  ["Designations", "designations"], ["Style", "style"], ["Materials", "materials"],
  ["Dedicated to", "dedication"], ["Height (m)", "height_m"], ["Oldest-of-type claim", "type_claim"]];

async function render() {
  const ids = store.get(CMP);
  const box = document.getElementById("c_body");
  if (!ids.length) { box.innerHTML = "<p class='empty'>Nothing to compare yet. Use ⇄ on up to three buildings.</p>"; return; }
  const bs = await api("/api/buildings?ids=" + ids.map(encodeURIComponent).join(","));
  const years = bs.map((b) => b.year_start).filter((y) => y != null);
  const span = years.length > 1 ? Math.max(...years) - Math.min(...years) : null;
  box.innerHTML = `${span != null ? `<p class="hint">The oldest and newest of these are about ${span.toLocaleString()} years apart.</p>` : ""}
    <div class="table-wrap"><table class="grid compare"><thead><tr><th></th>${bs.map((b) => `<th>
      ${b.image_thumb ? `<img src="${esc(b.image_thumb)}" alt="">` : ""}
      <a href="${buildingUrl(b.id)}">${esc(b.name)}</a><br><button class="btn small ghost" data-cmp="${esc(b.id)}">Remove</button></th>`).join("")}
    </tr></thead><tbody>${ROWS.map(([label, k]) => `<tr><th>${esc(label)}</th>${bs.map((b) => `<td>${esc(b[k] ?? "")}</td>`).join("")}</tr>`).join("")}
    </tbody></table></div>`;
}
document.addEventListener("click", (e) => { if (e.target.closest("[data-cmp]")) setTimeout(render, 0); });
render();
