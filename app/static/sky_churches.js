// "Churches and their saints' days" on the Sky calendar page (roadmap SK5): the axes of the catalogue's churches from
// their OpenStreetMap outlines against the range of sunrise, and the test of the idea that medieval churches face
// sunrise on their patron saint's day (static/data/church_orientation.json, written by bidb.church_orientation),
// with the published studies on both sides and their quoted sources.
(async () => {
  const box = document.getElementById("churches");
  const data = await fetch((IS_STATIC ? "static" : "/static") + "/data/church_orientation.json").then((r) => r.json()).catch(() => null);
  if (!box || !data) return;
  const s = data.summary, rows = Object.values(data.churches).filter((c) => c[1] >= 1.4);

  // Histogram of east-end azimuths in 2° bins, with the year's sunrise range at 53° N shaded
  const W = 640, H = 170, P = 28, x = (a) => P + (a - 30) / 120 * (W - 2 * P);
  const bins = new Array(60).fill(0);
  rows.forEach((c) => { if (c[0] >= 30 && c[0] < 150) bins[Math.floor((c[0] - 30) / 2)]++; });
  const top = Math.max(...bins), y = (n) => H - 22 - n / top * (H - 34);
  const lo = Sky.eventAzimuth(53, "sun", "summer_solstice", "rise"), hi = Sky.eventAzimuth(53, "sun", "winter_solstice", "rise");
  const eq = Sky.eventAzimuth(53, "sun", "equinox", "rise");
  const ticks = [30, 45, 60, 75, 90, 105, 120, 135, 150];
  const svg = `<svg class="sky-hist" viewBox="0 0 ${W} ${H}" role="img" aria-label="Number of churches by the direction of their east end">
    <rect class="sky-range" x="${x(lo)}" y="8" width="${x(hi) - x(lo)}" height="${H - 30}"/>
    <line class="sky-eq" x1="${x(eq)}" x2="${x(eq)}" y1="8" y2="${H - 22}"/>
    ${bins.map((n, i) => `<rect class="sky-bar" x="${x(30 + 2 * i) + 0.5}" y="${y(n)}" width="${x(32) - x(30) - 1}" height="${H - 22 - y(n)}"><title>${30 + 2 * i}–${32 + 2 * i}°: ${n}</title></rect>`).join("")}
    ${ticks.map((t) => `<text x="${x(t)}" y="${H - 6}">${t}°</text>`).join("")}
    <text style="text-anchor:start" x="${x(lo) + 4}" y="20">midsummer sunrise</text><text style="text-anchor:end" x="${x(hi) - 4}" y="20">midwinter sunrise</text>
  </svg>`;

  const pct = (k, n) => (n ? `${(100 * k / n).toFixed(1)}%` : "–");
  const result = s.tested ? `<p>Of <b>${s.tested.toLocaleString()}</b> churches begun before 1540 whose saint has a fixed feast,
      <b>${s.observed.toLocaleString()}</b> (${pct(s.observed, s.tested)}) face within ${s.tolerance}° of the sunrise on that feast in the
      Julian calendar of the year they were begun. With the same churches' dedications shuffled at random ${s.shuffles} times,
      ${s.chance_mean} (${pct(s.chance_mean, s.tested)}) do on average, and 95% of shuffles give ${s.chance_95[0]}–${s.chance_95[1]}.
      ${s.observed > s.chance_95[1] ? "More churches face their own saint's sunrise than chance would give."
        : s.observed < s.chance_95[0] ? "Fewer churches face their own saint's sunrise than chance would give."
        : "That is no more than chance: these churches as a whole do not face their own saint's sunrise more often than another saint's."}</p>`
    : '<p class="meta">The feast days are still being researched; the test will appear here.</p>';
  // SK5b: the same test over each church's own skyline, and counting the other saint an ambiguous label may mean
  const verdict = (t) => (t.observed > t.chance_95[1] ? "more than chance" : t.observed < t.chance_95[0] ? "fewer than chance" : "no more than chance");
  const testRow = (name, t) => `<tr><td>${name}</td><td>${t.tested.toLocaleString()}</td><td>${t.observed.toLocaleString()} (${pct(t.observed, t.tested)})</td>
      <td>${t.chance_mean} (${t.chance_95[0]}–${t.chance_95[1]})</td><td>${t.p == null ? "–" : t.p < 0.001 ? "< 0.001" : t.p.toFixed(2)}</td><td>${verdict(t)}</td></tr>`;
  const tests = s.skyline ? `<table class="sky-table"><thead><tr><th>Test</th><th>Churches</th><th>Within ${s.tolerance}° of their feast</th>
      <th>Shuffled: mean (95%)</th><th title="Share of shuffles with as many churches or more">p</th><th>Result</th></tr></thead><tbody>
      ${testRow("Flat horizon", s)}${testRow("Over each church's skyline", s.skyline)}
      ${testRow(`Over the skyline, either saint where the label is ambiguous (${s.other_saints.labels.map(esc).join(", ")})`, s.other_saints)}</tbody></table>
    <p class="meta">The skyline is the bare ground of the terrain model (trees and buildings are not in it), at the axis of
      each church; the sun rises later and further south over higher ground, so the dates the axis points to move.</p>` : "";
  const ded = (s.by_dedication || []).filter((d) => d[1] >= 10);
  const STUDY = { yes: "found support", partly: "found partial support", no: "found no support" };
  box.innerHTML = `<h2>Churches and their saints' days</h2>
    <p class="prose">An old idea holds that a medieval church was set out to face sunrise on its patron saint's day. The
      axes of ${s.with_axis.toLocaleString()} churches in the catalogue, from their OpenStreetMap outlines, are below:
      ${s.east_facing.toLocaleString()} face between north-north-east and south-south-east, most within the year's range of sunrise (shaded) and near
      the equinox line. Each axis is the direction of the outline's walls (weighted by length), so a tower, porch or aisle
      set askew moves it little${s.from_parts ? `; for ${s.from_parts} churches whose nave, chancel or body is mapped as a part of its own, that part's` : ""}.
      Outlines that take in a whole abbey or friary can still mislead, the spike at due east may partly be outlines drawn square to the map, and the horizon is the bare ground of the terrain model.</p>
    ${svg}
    ${result}
    ${tests}
    ${ded.length ? `<details><summary>By dedication (10 or more churches)</summary><table class="sky-table"><thead><tr><th>Dedication</th><th>Churches</th><th>Within ${s.tolerance}°</th></tr></thead>
      <tbody>${ded.map(([d, n, k]) => `<tr><td>${esc(d)}</td><td>${n}</td><td>${k} (${pct(k, n)})</td></tr>`).join("")}</tbody></table></details>` : ""}
    ${(data.studies || []).length ? `<h3>What studies have found</h3><ul class="sky-sites">${data.studies.map((st) => `<li>${esc(st.citation)}
      <span class="sky-verdict ${st.supports === "yes" ? "established" : st.supports === "no" ? "disputed" : ""}">${esc(STUDY[st.supports] || st.supports)}</span>
      <br>${esc(st.finding)}${st.sample ? ` <span class="meta">(${esc(st.sample)})</span>` : ""}
      <ul class="sky-sources">${st.sources.map((q) => `<li><a href="${esc(q.url)}" target="_blank" rel="noopener">${esc(q.title)}</a>${q.locator ? ` <span class="meta">${esc(q.locator)}</span>` : ""}<br>“${esc(q.quote)}”</li>`).join("")}</ul></li>`).join("")}</ul>` : ""}`;
})();
