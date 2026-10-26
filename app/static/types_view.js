// Building types (BT4a) and materials (BT3c1): the view of one type (/types?t=<id>) or one material (/types?m=<id>):
// definition (FISH scope note), period, structure and plan, family links with their claims and quoted sources, the
// materials of the type (curated and found in its records), the earliest surviving example, examples by century and
// nation, a map, its spread across the counties and what came before and after (TypeTime, BT5), examples oldest first
// and the sources. TypeView.type(el, d, names), TypeView.material(el, d).
const TypeView = (() => {
  const yt = TypeTree.yearText;
  // the link as read from this side: [label, other end]
  const PHRASE = {
    descent: ["Grew out of", "Grew into"], variant: ["A form of", "Forms"], influence: ["Shaped by", "Shaped"],
    replacement: ["Replaced", "Replaced by"], revival: ["Revival of", "Revived as"],
    convergence: ["Similar to, from separate origins", "Similar to, from separate origins"],
  };
  const cap = (s) => (s ? s[0].toUpperCase() + s.slice(1) : "");
  const typeUrl = (id) => `?t=${encodeURIComponent(id)}`;
  const matUrl = (id) => `?m=${encodeURIComponent(id)}`;

  const sourceList = (sources) => sources && sources.length ? `<ul class="cc-src ty-sources">${sources.map((s) =>
    `<li>${s.quote ? `“${esc(s.quote)}” — ` : ""}<a href="${esc(s.url)}" target="_blank" rel="noopener">${esc(s.title)}</a>${
      s.author ? `, ${esc(s.author)}` : ""}${s.locator ? ` (${esc(s.locator)})` : ""}${s.about ? ` <span class="meta">[${esc(s.about.join(", "))}]</span>` : ""}</li>`).join("")}</ul>` : "";

  const definition = (d, own) => d.definition ? `<p class="prose">${esc(d.definition.text || d.definition.term)}
    <span class="meta">(<a href="${esc(d.definition.url)}" target="_blank" rel="noopener">FISH thesaurus</a>, Historic England, OGL)</span></p>`
    : own ? `<p class="prose">${esc(own)}</p>` : "";

  // links grouped by how they read from this side
  function links(list, url) {
    if (!list.length) return "";
    const groups = {};
    list.forEach((k) => {
      const label = PHRASE[k.kind][k.direction === "in" ? 0 : 1];
      (groups[label] = groups[label] || []).push(k);
    });
    return `<h3>Family</h3><dl class="ty-links">${Object.entries(groups).map(([label, ks]) => `<dt>${esc(label)}</dt>${ks.map((k) =>
      `<dd><a href="${url(k.other)}" data-go="${esc(k.other)}">${esc(k.other_name)}</a>
        <span class="ty-conf ${esc(k.confidence)}">${esc(k.confidence)}</span>${k.region ? ` <span class="meta">${esc(k.region)}</span>` : ""}
        <details><summary>${esc(k.claim)}</summary>${k.views ? `<ul>${k.views.map((v) => `<li>${esc(v)}</li>`).join("")}</ul>` : ""}${sourceList(k.sources)}</details></dd>`).join("")}`).join("")}</dl>`;
  }

  const entity = (e) => `<a href="${e.source === "place" ? "#" : buildingUrl(e.id)}" ${e.source === "place" ? "data-place" : "data-open"}="${esc(e.id)}">${esc(e.name)}</a>`;
  const earliest = (e, what) => e ? `<div class="ty-earliest">${e.thumb ? `<img src="${esc(e.thumb)}" alt="" loading="lazy">` : ""}
    <div><b>Earliest surviving example in the catalogue</b><br>${entity(e)} <span class="meta">${esc([e.date_text, e.county, e.nation].filter(Boolean).join(" · "))}</span>
    <br><span class="hint">${esc(what)}</span></div></div>` : "";

  function examples(rows, extra) {
    if (!rows.length) return "";
    return `<details class="tr-list"><summary>Dated examples, oldest first (${rows.length.toLocaleString()}${rows.length >= 200 ? " shown" : ""})</summary>
      <ul class="nearby">${rows.map((r) => `<li>${entity(r)} <span class="meta">${esc([r.date_text || yt(r.year), r.county, r.nation].filter(Boolean).join(" · "))}</span>
        ${r.too_early ? ' <span class="ty-flag" title="Begun long before the first known date: a later phase, or a mapping or dating error">too early</span>' : ""}${extra ? extra(r) : ""}</li>`).join("")}</ul></details>`;
  }

  // counts per century begun, as bars; and per nation
  function charts(box, d) {
    const cent = box.querySelector(".ty-century"), nat = box.querySelector(".ty-nation");
    const rows = Object.entries(d.by_century || {}).map(([c, n]) => [+c, n]).sort((a, b) => a[0] - b[0]);
    if (cent && rows.length) hBars(cent, rows.map(([c, n]) => [c < 0 ? `${-c} BC` : `${c}s`, n]), { max: 60 });
    if (nat) hBars(nat, Object.entries(d.by_nation || {}), { max: 10 });
  }

  function drawMap(box, points) {
    const el = box.querySelector(".ty-map");
    if (!el || !points.length) { el && el.remove(); return; }
    const map = L.map(el, { maxZoom: 17 }).setView([54.3, -4.5], 5);
    addBaseLayer(map);
    const pts = [];
    points.forEach(([lat, lon, id, source, year, primary]) => {
      pts.push([lat, lon]);
      L.circleMarker([lat, lon], { radius: 4, weight: 1, color: cssVar(source === "place" ? "--g2" : "--g1"),
                                    fillOpacity: primary === 0 ? 0.25 : 0.8 })
        .bindPopup(`${year != null ? yt(year) + " · " : ""}<a href="${source === "place" ? "#" : buildingUrl(id)}" ${
          source === "place" ? "data-place" : "data-open"}="${esc(id)}">Open</a>`).addTo(map);
    });
    if (pts.length > 1) map.fitBounds(pts, { padding: [20, 20], maxZoom: 9 }); else map.setView(pts[0], 9);
  }

  const counts = (d) => `${d.buildings.toLocaleString()} catalogue records and ${d.places.toLocaleString()} places`;

  function type(box, d) {
    const t = d.type, p = d.period;
    const mats = d.materials.length ? `<p><b>Materials and techniques:</b> ${d.materials.map((m) =>
      `<a href="${matUrl(m.id)}" data-gom="${esc(m.id)}">${esc(m.name)}</a>`).join(", ")}</p>` : "";
    const recMats = d.record_materials.length ? `<p><b>Found in its records:</b> ${d.record_materials.map((m) =>
      `<a href="${matUrl(m.id)}" data-gom="${esc(m.id)}">${esc(m.name)}</a> <span class="meta">${m.count.toLocaleString()}</span>`).join(", ")}</p>` : "";
    box.innerHTML = `<p class="meta">${esc(t.domain)} › ${esc(t.family)}${t.abroad ? " · a type abroad, reached by the family links" : ""}</p>
      <h2>${esc(t.name)}</h2>${definition(d, t.note)}${d.definition && t.note ? `<p class="prose">${esc(t.note)}</p>` : ""}
      <p><b>In use:</b> ${esc(TypeTree.periodText(p))}. ${esc(cap(p.text))}</p>
      ${t.structure ? `<p><b>Structure:</b> ${esc(t.structure)}</p>` : ""}${t.plan ? `<p><b>Plan:</b> ${esc(t.plan)}</p>` : ""}
      ${mats}${recMats}${links(d.links, typeUrl)}${TypeTime.chains(d.chains, t.name)}
      ${d.abroad ? "" : `<h3>In the catalogue</h3><p>${counts(d)}${d.dated ? `, ${d.dated.toLocaleString()} dated` : ""}${
        d.too_early ? `; ${d.too_early.toLocaleString()} begun more than a century before the first known date (later use of an older building, or an error)` : ""}.
        <a href="${IS_STATIC ? "index.html" : "/"}?q=${encodeURIComponent(t.name)}">Search the catalogue</a></p>
      ${earliest(d.earliest, "Standing or a ruin, of which this is the main type, not dated from the type itself and not too early.")}
      <div class="ty-grid"><div><h4>Begun per century</h4><div class="ty-century"></div><h4>By nation</h4><div class="ty-nation"></div></div>
        <div><div class="ty-map stories-map"></div><p class="hint">Blue: catalogue records, orange: places; faint where it is not the main type.</p></div></div>
      <div class="ty-spread"></div>
      ${examples(d.examples || [])}`}
      <h3>Sources</h3>${sourceList(t.sources) || '<p class="hint">The period and links cite their sources above.</p>'}`;
    if (!d.abroad) { charts(box, d); drawMap(box, d.points); TypeTime.spread(box.querySelector(".ty-spread"), d.spread); }
  }

  function material(box, d) {
    const m = d.material, p = d.period;
    const types = d.types.length ? `<p><b>Used for:</b> ${d.types.map((t) => `<a href="${typeUrl(t.id)}" data-go="${esc(t.id)}">${esc(t.name)}</a>`).join(", ")}</p>` : "";
    const recTypes = d.record_types.length ? `<p><b>Main types of its records:</b> ${d.record_types.map((t) =>
      `<a href="${typeUrl(t.id)}" data-go="${esc(t.id)}">${esc(t.name)}</a> <span class="meta">${t.count.toLocaleString()}</span>`).join(", ")}</p>` : "";
    const ex = (m.examples || []).length ? `<p><b>Named examples:</b> ${m.examples.map((e) => `${esc(e.name)}${e.year != null ? ` (${yt(e.year)})` : ""}`).join("; ")}</p>` : "";
    const via = Object.entries(d.via || {}).map(([k, n]) => `${n.toLocaleString()} from ${k === "wikipedia" ? "Wikipedia" : k === "wikidata" ? "Wikidata" : "the register"}`).join(", ");
    box.innerHTML = `<p class="meta">${esc(m.group)} · ${esc(m.kind)}</p><h2>${esc(m.name)}</h2>${definition(d)}
      <p><b>In use:</b> ${esc(TypeTree.periodText(p))}${p.earlier ? " (the first date is only the earliest a source names)" : ""}. ${esc(cap(p.text))}</p>
      ${m.regions ? `<p><b>Where:</b> ${esc(m.regions.text)}</p>` : ""}${m.technology ? `<p><b>How:</b> ${esc(m.technology)}</p>` : ""}
      ${m.geology ? `<p><b>Bedrock:</b> ${esc(m.geology.join(", "))} <span class="meta">(periods of the geology layer on <a href="${IS_STATIC ? "change.html" : "/change"}">Change over time</a>)</span></p>` : ""}${ex}${types}${recTypes}${links(d.links, matUrl).replace(/data-go=/g, "data-gom=")}
      <h3>In the catalogue</h3><p>${d.count.toLocaleString()} records and places name it${via ? ` (${via})` : ""}. A record names the
        materials of all its phases and is dated by when it was begun, so early examples may owe the material to a later phase.</p>
      ${earliest(d.earliest, "Standing or a ruin, begun when the material was in use, not dated from its type.")}
      <div class="ty-grid"><div><h4>Begun per century</h4><div class="ty-century"></div><h4>By nation</h4><div class="ty-nation"></div></div>
        <div><div class="ty-map stories-map"></div></div></div>
      ${examples(d.examples || [], (r) => r.evidence ? `<br><span class="hint">“${esc(r.evidence.length > 240 ? r.evidence.slice(0, 239) + "…" : r.evidence)}”</span>` : "")}
      <h3>Sources</h3>${sourceList(m.sources)}`;
    charts(box, d);
    drawMap(box, d.points.map((q) => q.concat([1])));
  }

  return { type, material };
})();
