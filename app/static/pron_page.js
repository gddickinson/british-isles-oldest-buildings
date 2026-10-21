// Pronunciation page: searchable guide to how names are said, filtered by variety and record kind.
const Q$ = (sel) => document.querySelector(sel);
let prOffset = 0, prTotal = 0, prTimer = null, prVariety = "";
const PR_KIND = { building: "Building", place: "Place", person: "Person", town: "Town / area" };

function prRow(r) {
  const ipa = r.ipa ? `<span class="ipa">/${esc(r.ipa.replace(/^\/|\/$/g, ""))}/</span>` : "";
  const sp = r.respell ? ` <span class="respell">${esc(r.respell)}</span>` : "";
  const open = r.entity_kind === "town"
    ? `<a href="${esc(r.source_url)}" target="_blank" rel="noopener">${esc(r.source)}</a>`
    : `<a href="#" data-open="${esc(r.entity_kind)}" data-id="${esc(r.entity_id)}">open</a>`;
  return `<tr><td class="pron-name" lang="${esc(r.lang)}">${esc(r.name)}</td><td>${esc(r.variety)}</td>
    <td>${ipa}${sp}</td><td>${Pron.playButton(r)}</td>
    <td class="kind">${PR_KIND[r.entity_kind] || ""} · ${open}</td></tr>`;
}

async function loadPron(append = false) {
  if (!append) prOffset = 0;
  const p = { q: Q$("#pr_q").value.trim(), variety: prVariety, kind: Q$("#pr_kind").value, limit: 60, offset: prOffset };
  const data = await Pron.search(p);
  prTotal = data.total;
  Q$("#pr_count").textContent = `${prTotal.toLocaleString()} pronunciations`;
  const html = data.rows.map(prRow).join("");
  if (append) Q$("#pr_list").insertAdjacentHTML("beforeend", html);
  else Q$("#pr_list").innerHTML = html || "<tr><td colspan='5' class='empty'>No pronunciations match.</td></tr>";
  prOffset += data.rows.length;
  Q$("#pr_more").parentElement.classList.toggle("hidden", prOffset >= prTotal);
  const qs = new URLSearchParams();
  if (p.q) qs.set("q", p.q);
  if (p.variety) qs.set("variety", p.variety);
  if (p.kind) qs.set("kind", p.kind);
  history.replaceState(null, "", location.pathname + (qs.toString() ? "?" + qs : ""));
}

async function initPron() {
  const url = new URLSearchParams(location.search);
  Q$("#pr_q").value = url.get("q") || "";
  Q$("#pr_kind").value = url.get("kind") || "";
  prVariety = url.get("variety") || "";
  const vs = await Pron.varieties().catch(() => []);
  const chip = (v, n, label) => `<button type="button" data-v="${esc(v)}" class="${v === prVariety ? "on" : ""}">${esc(label || v)}${n ? ` <span class="hint">${n.toLocaleString()}</span>` : ""}</button>`;
  Q$("#pr_chips").innerHTML = chip("", 0, "All varieties") + vs.slice(0, 18).map((v) => chip(v.variety, v.count)).join("");
  Q$("#pr_chips").addEventListener("click", (e) => {
    const b = e.target.closest("button[data-v]");
    if (!b) return;
    prVariety = b.dataset.v;
    Q$("#pr_chips").querySelectorAll("button").forEach((x) => x.classList.toggle("on", x === b));
    loadPron();
  });
  Q$("#pr_q").addEventListener("input", () => { clearTimeout(prTimer); prTimer = setTimeout(() => loadPron(), 250); });
  Q$("#pr_kind").addEventListener("change", () => loadPron());
  Q$("#pr_more").addEventListener("click", () => loadPron(true));
  document.addEventListener("click", (e) => {
    const a = e.target.closest("[data-open]");
    if (!a) return;
    e.preventDefault();
    const { open, id } = a.dataset;
    if (open === "building") location.href = buildingUrl(id);
    else if (open === "place") openPlace(id);
    else openPerson(id);
  });
  loadPron();
}
initPron();
