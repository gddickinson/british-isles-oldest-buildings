// Building types BT6c: labelled diagrams of a type (plan, section, elevation) drawn as SVG from the shapes of
// bidb.type_diagrams, every label from a quoted source; the quotes it is drawn from listed under it.
// TypeDiagram.html(list) → the "Diagrams" section of a type page.
const TypeDiagram = (() => {
  const pts = (v) => v.reduce((s, n, i) => s + (i % 2 ? "," : i ? " " : "") + n, "");

  function shape(s) {
    const [kind] = s;
    const c = (i) => `class="td-${esc(s[i])}"`;
    if (kind === "rect") return `<rect x="${s[1]}" y="${s[2]}" width="${s[3]}" height="${s[4]}"${s[6] ? ` rx="${s[6]}"` : ""} ${c(5)}/>`;
    if (kind === "circle") return `<circle cx="${s[1]}" cy="${s[2]}" r="${s[3]}" ${c(4)}/>`;
    if (kind === "ellipse") return `<ellipse cx="${s[1]}" cy="${s[2]}" rx="${s[3]}" ry="${s[4]}" ${c(5)}/>`;
    if (kind === "poly") return `<polygon points="${pts(s[1])}" ${c(2)}/>`;
    if (kind === "line") return `<polyline points="${pts(s[1])}" ${c(2)}/>`;
    if (kind === "path") return `<path d="${esc(s[1])}" ${c(2)}/>`;
    return "";
  }

  function label(l) {
    const tos = !l.to ? [] : Array.isArray(l.to[0]) ? l.to : [l.to];
    const leaders = tos.map(([x, y]) => `<line x1="${l.at[0]}" y1="${l.at[1] + (y < l.at[1] ? -10 : 3)}" x2="${x}" y2="${y}" class="td-leader"/>
      <circle cx="${x}" cy="${y}" r="2" class="td-tip"/>`).join("");
    return `${leaders}<text x="${l.at[0]}" y="${l.at[1]}" text-anchor="${l.a || "middle"}" class="td-label">${esc(l.t)}</text>`;
  }

  function svg(d) {
    const [w, h] = d.size;
    return `<svg viewBox="0 0 ${w} ${h}" class="td-svg" role="img" aria-label="${esc(d.title)}">
      ${d.shapes.map(shape).join("")}${d.labels.map(label).join("")}</svg>`;
  }

  const source = (s) => `<li>“${esc(s.quote)}” — <a href="${esc(s.url)}" target="_blank" rel="noopener">${esc(s.title)}</a>${
    s.author ? `, ${esc(s.author)}` : ""}${s.locator ? ` (${esc(s.locator)})` : ""}</li>`;

  function html(list) {
    if (!list || !list.length) return "";
    return `<h3>Diagrams</h3><p class="hint">Diagrams, not to scale unless a size is marked: every label is taken from the
      quoted sources below each one, and nothing is drawn that they do not describe except what the note says.</p>
      <div class="td-list">${list.map((d) => `<figure class="td-fig">${svg(d)}<figcaption><b>${esc(d.title)}</b>
        ${d.note ? `<br><span class="hint">${esc(d.note)}</span>` : ""}
        <details><summary>Drawn from</summary><ul class="cc-src ty-sources">${(d.sources || []).map(source).join("")}</ul></details>
        </figcaption></figure>`).join("")}</div>`;
  }

  return { html, svg };
})();
