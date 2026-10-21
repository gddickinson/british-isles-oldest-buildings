// People page: search people linked to buildings and places; open one for their connections.
const Q$ = (sel) => document.querySelector(sel);
let peopleOffset = 0, peopleTotal = 0, peopleTimer = null;

function personCardHTML(p) {
  const links = p.links.map((l) => `<a href="#" class="tag-pill" data-target="${esc(l.target_id)}">${esc(l.role)}: ${esc(l.name || l.target_id)}</a>`).join(" ");
  return `<article class="person" data-person="${esc(p.id)}" tabindex="0">
    ${p.image_thumb ? `<img loading="lazy" src="${esc(p.image_thumb)}" alt="" onerror="this.remove()">` : '<div class="avatar">👤</div>'}
    <div><h3>${esc(p.name)} <span class="hint">${esc(lifeYears(p))}</span></h3>
      ${p.description ? `<div class="meta">${esc(p.description)}</div>` : ""}
      ${p.summary ? `<p>${esc(p.summary)}</p>` : ""}
      <div class="person-links">${links}</div></div></article>`;
}

async function loadPeople(append = false) {
  if (!append) peopleOffset = 0;
  const p = new URLSearchParams({ q: Q$("#p_q").value.trim(), role: Q$("#p_role").value,
                                  sort: Q$("#p_sort").value, limit: 40, offset: peopleOffset });
  const data = await api("/api/people?" + p);
  peopleTotal = data.total;
  Q$("#p_count").textContent = `${peopleTotal.toLocaleString()} people`;
  const html = data.rows.map(personCardHTML).join("");
  if (append) Q$("#p_list").insertAdjacentHTML("beforeend", html);
  else Q$("#p_list").innerHTML = html || "<p class='empty'>No people match.</p>";
  peopleOffset += data.rows.length;
  Q$("#p_more").parentElement.classList.toggle("hidden", peopleOffset >= peopleTotal);
  const qs = new URLSearchParams();
  ["q", "role", "sort"].forEach((k) => { const v = Q$("#p_" + k).value.trim(); if (v && !(k === "sort" && v === "known")) qs.set(k, v); });
  history.replaceState(null, "", location.pathname + (qs.toString() ? "?" + qs : "") + location.hash);
}

async function initPeople() {
  const roles = await api("/api/people/roles");
  roles.forEach(([r, n]) => Q$("#p_role").insertAdjacentHTML("beforeend", `<option value="${esc(r)}">${esc(r)} (${n.toLocaleString()})</option>`));
  const url = new URLSearchParams(location.search);
  ["q", "role", "sort"].forEach((k) => { if (url.get(k)) Q$("#p_" + k).value = url.get(k); });
  Q$("#p_q").addEventListener("input", () => { clearTimeout(peopleTimer); peopleTimer = setTimeout(() => loadPeople(), 250); });
  ["#p_role", "#p_sort"].forEach((s) => Q$(s).addEventListener("change", () => loadPeople()));
  Q$("#p_more").addEventListener("click", () => loadPeople(true));
  // a connection pill opens the building or place itself, not the person
  document.addEventListener("click", (e) => {
    const t = e.target.closest("[data-target]");
    if (!t) return;
    e.preventDefault();
    e.stopPropagation();
    const id = t.dataset.target;
    api("/api/place/" + encodeURIComponent(id)).then(() => openPlace(id))
      .catch(() => { location.href = buildingUrl(id); });
  }, true);
  document.addEventListener("keydown", (e) => {
    if (e.key === "Enter" && e.target.dataset && e.target.dataset.person) openPerson(e.target.dataset.person);
  });
  await loadPeople();
  if (location.hash.length > 1) openPerson(decodeURIComponent(location.hash.slice(1)));
}
initPeople();
