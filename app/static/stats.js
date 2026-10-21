// Statistics dashboard: tiles, single-series bar charts, completeness and oldest-per-county.
const F = { nation: "s_nation", category_group: "s_group", period: "s_period" };

function filterParams() {
  const p = new URLSearchParams();
  Object.entries(F).forEach(([k, id]) => { const v = document.getElementById(id).value; if (v) p.set(k, v); });
  return p;
}

function openCatalogue(extra) {
  const p = filterParams();
  Object.entries(extra).forEach(([k, v]) => p.append(k, v));
  location.href = (IS_STATIC ? "index.html?" : "/?") + p;
}

async function render() {
  const d = await api("/api/stats?" + filterParams());
  const pct = (n) => (d.total ? Math.round((100 * n) / d.total) : 0);
  const comp = Object.fromEntries(d.completeness);
  const oldest = d.oldest_by_county.slice().sort((a, b) => a.year - b.year)[0];
  document.getElementById("s_tiles").innerHTML = [
    ["Records", d.total.toLocaleString()], ["With images", `${pct(comp.image)}%`],
    ["With a recorded date", `${pct(comp["recorded date"])}%`],
    ["Oldest", oldest ? `${oldest.name}` : "–", oldest ? oldest.date_text : ""],
  ].map(([label, value, sub]) => `<div class="tile"><span>${esc(label)}</span><b>${esc(value)}</b>${sub ? `<em>${esc(sub)}</em>` : ""}</div>`).join("");
  const series = cssVar("--series-1");
  [["nation", "nation"], ["period", "period"], ["category", "category"], ["heritage_grade", "heritage_grade"],
   ["status", "status"], ["county", "county"]].forEach(([key, col]) => {
    let rows = d[key];
    if (key === "period") rows = PERIODS.map((p) => rows.find((r) => r[0] === p)).filter(Boolean)
      .concat(rows.filter((r) => !PERIODS.includes(r[0])));
    hBars(document.getElementById("c_" + key), rows, { color: series, max: 40,
      onClick: (label) => openCatalogue({ [col]: label }) });
  });
  hBars(document.getElementById("c_completeness"), d.completeness.map(([l, n]) => [l, pct(n)]),
        { color: series, unit: "%" });
  document.getElementById("t_oldest").innerHTML = `<table class="grid small"><thead><tr><th>County</th><th>Nation</th>
    <th>Oldest building</th><th>Date</th></tr></thead><tbody>${d.oldest_by_county.map((r) => `<tr>
    <td>${esc(r.county)}</td><td>${esc(r.nation || "")}</td><td><a href="${buildingUrl(r.id)}">${esc(r.name)}</a></td>
    <td>${esc(r.date_text || "")}</td></tr>`).join("")}</tbody></table>`;
}

async function init() {
  const f = await api("/api/facets");
  const fill = (id, rows) => rows.forEach(([v]) => document.getElementById(id).insertAdjacentHTML("beforeend", `<option>${esc(v)}</option>`));
  fill("s_nation", f.nation); fill("s_group", f.category_group);
  fill("s_period", PERIODS.map((p) => [p]));
  Object.values(F).forEach((id) => document.getElementById(id).addEventListener("change", render));
  render();
}
init();
