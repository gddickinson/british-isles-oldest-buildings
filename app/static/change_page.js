// "Change over time" page: every series of static/data/change/series.json as a graph with its source, licence and
// notes, a table of values on request, dated events per theme, the cited analysis notes (E5) and the full list of sources.
(async () => {
  const $ = (s) => document.querySelector(s);
  const d = await ChangePanel.load();
  const sources = d.sources || {}, series = d.series || [], events = d.events || [], notes = d.notes || [];
  const shown = series.filter((s) => !s.hidden);
  const modelsOf = (s) => (s.models || []).map((id) => series.find((x) => x.id === id)).filter(Boolean);
  const themes = [...new Set(shown.map((s) => s.theme).concat(events.map((e) => e.theme)))];
  const RANGES = [["Each graph's own years", "fit"], ["All time", -4000], ["Since AD 1000", 1000], ["Since 1500", 1500], ["Since 1700", 1700], ["Since 1900", 1900]];
  $("#ch_range").innerHTML = RANGES.map(([t, y]) => `<option value="${y}">${t}</option>`).join("");
  $("#ch_theme").innerHTML += themes.map((t) => `<option>${esc(t)}</option>`).join("");
  const yt = ChangeCharts.yearText;
  const cite = (ids) => (ids || []).map((id) => sources[id] ? `<a href="#src-${esc(id)}">${esc(sources[id].short || sources[id].publisher)}</a>` : "").join("; ");

  function table(s) {
    return `<table class="ch-table"><caption>${esc(s.label || s.title)}</caption><thead><tr><th>Year</th><th>${esc(s.unit_long || s.unit || "Value")}</th>
      ${s.points.some((p) => p[2] != null) ? "<th>Range</th>" : ""}${s.points.some((p) => p[4]) ? "<th>Estimate by</th>" : ""}</tr></thead><tbody>${s.points.map((p) =>
      `<tr><td>${yt(p[0])}</td><td>${ChangeCharts.fmt(p[1])}</td>${s.points.some((q) => q[2] != null) ? `<td>${p[2] != null ? `${ChangeCharts.fmt(p[2])}–${ChangeCharts.fmt(p[3])}` : ""}</td>` : ""}${p[4] ? `<td style="text-align:left">${esc(p[4])}</td>` : ""}</tr>`).join("")}
      </tbody></table>`;
  }

  function draw() {
    const only = $("#ch_theme").value;
    $("#ch_body").innerHTML = themes.filter((t) => !only || t === only).map((t) => `<section class="ch-theme"><h2>${esc(t)}</h2>
      <div class="ch-grid">${shown.filter((s) => s.theme === t).map((s) => `<figure class="cc-item ch-fig" id="fig-${esc(s.id)}" data-id="${esc(s.id)}">
        <figcaption class="cc-title">${esc(s.title)}${s.region ? ` <span class="cc-region">${esc(s.region)}</span>` : ""}
          <span class="cc-now">${esc(s.unit_long || s.unit || "")}</span></figcaption>
        <div class="cc-plot"></div>
        <div class="cc-src">Source: ${cite(s.sources)}${s.modelled ? " · modelled" : ""}${modelsOf(s).map((m) =>
          `<br>Compared with ${esc(m.label || m.title)}: ${cite(m.sources)}`).join("")}</div>
        ${s.note ? `<p class="cc-note">${esc(s.note)}</p>` : ""}
        ${modelsOf(s).map((m) => m.note ? `<p class="cc-note"><b>${esc(m.label || m.title)}:</b> ${esc(m.note)}</p>` : "").join("")}
        <details><summary>Table of values</summary>${[s, ...modelsOf(s)].map(table).join("")}</details></figure>`).join("")}</div>
      ${eventList(events.filter((e) => e.theme === t))}</section>`).join("");
    document.querySelectorAll(".ch-fig").forEach((f) => {
      const s = series.find((x) => x.id === f.dataset.id);
      const models = modelsOf(s);
      ChangeCharts.draw(f.querySelector(".cc-plot"), s, { ...ChangeCharts.span(s, $("#ch_range").value, models), year: null, models });
    });
  }
  function eventList(list) {
    if (!list.length) return "";
    return `<h3>Events</h3><ul class="ch-events">${list.sort((a, b) => a.year - b.year).map((e) =>
      `<li><b>${yt(e.year)}${e.end && e.end !== e.year ? `–${yt(e.end)}` : ""}</b> ${esc(e.title)}${e.text ? ` — ${esc(e.text)}` : ""}
        <span class="cc-src">(${e.sources ? cite(e.sources) : esc(e.citation)})</span></li>`).join("")}</ul>`;
  }
  $("#ch_sources").innerHTML = Object.entries(sources).sort((a, b) => (a[1].short || "").localeCompare(b[1].short || ""))
    .map(([id, s]) => `<p id="src-${esc(id)}" class="ch-source"><b>${esc(s.short || s.publisher)}</b> — ${esc(s.citation)}
      <a href="${esc(s.url)}" target="_blank" rel="noopener">${esc(s.url)}</a>.
      Licence: ${s.licence_url ? `<a href="${esc(s.licence_url)}" target="_blank" rel="noopener">${esc(s.licence)}</a>` : esc(s.licence || "—")}${s.used ? `. Used for: ${esc(s.used)}` : ""}.</p>`).join("");
  // E5 notes: text, the graphs to compare (links to the figures), and the quoted sources
  const span = (n) => `${yt(n.years[0])}${n.years[1] !== n.years[0] ? `–${yt(n.years[1])}` : ""}`;
  const chip = (id) => {
    if (id === "catalogue") return `<span class="ch-chip">this catalogue's buildings per century (Map page)</span>`;
    const s = series.find((x) => x.id === id);
    return s ? `<a class="ch-chip" href="#fig-${esc(id)}">${esc(s.title)}${s.region ? `, ${esc(s.region)}` : ""}</a>` : "";
  };
  $("#ch_notes").innerHTML = notes.map((n) => `<article class="ch-note" id="note-${esc(n.id)}">
      <h3>${esc(n.title)} <span class="cc-region">${span(n)}</span></h3>
      <p>${esc(n.text)}</p>
      <div class="ch-chips">Compare: ${n.series.map(chip).join(" ")}</div>
      ${n.sources.map((q) => `<blockquote class="ch-quote">“${esc(q.quote)}”
        <cite>— <a href="${esc(q.url)}" target="_blank" rel="noopener" title="${esc(q.citation)}">${esc(q.short)}</a>,
          ${esc(q.locator || "")}${q.licence ? ` (${esc(q.licence)})` : ""}</cite></blockquote>`).join("")}
    </article>`).join("");
  $("#ch_notes").addEventListener("click", (e) => {     // a graph hidden by the theme filter: show all themes first
    const a = e.target.closest("a.ch-chip");
    if (a && !document.querySelector(a.getAttribute("href"))) { $("#ch_theme").value = ""; draw(); }
  });
  $("#ch_range").addEventListener("change", draw);
  $("#ch_theme").addEventListener("change", draw);
  draw();
  if (location.hash) document.querySelector(location.hash)?.scrollIntoView();
})();
