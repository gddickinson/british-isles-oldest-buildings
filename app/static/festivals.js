// Festivals and seasons page (/festivals): the wheel of the year and a card per festival in order of its next date
// (/api/festivals), and each festival's own page (?f=<id>, /api/festival/<id>, bidb.festival_finds): facts and
// customs with their quoted sources, places to visit, a map, the churches of its saints, stories, sky alignments,
// what happened on the day and the oldest customs of /things.
(async () => {
  const $ = (s) => document.querySelector(s);
  const F = Festivals;
  const all = await api("/api/festivals").catch(() => []);
  const url = new URLSearchParams(location.search);
  const S = { season: url.get("season") || "", f: url.get("f") || "" };
  const pageUrl = (id) => `${location.pathname}?f=${encodeURIComponent(id)}`;
  const thingsUrl = (id) => `${typeof IS_STATIC !== "undefined" && IS_STATIC ? "things.html" : "/things"}#thing-${encodeURIComponent(id)}`;
  const skyUrl = () => (typeof IS_STATIC !== "undefined" && IS_STATIC ? "sky.html" : "/sky");
  const CHECK = { "quote-found": "✓ quote found in the source", "quote-missing": "quote not found at the last check",
    unreachable: "source could not be read at the last check", "no-link": "print source" };
  const dated = all.map((f) => ({ ...f, nextDate: F.next(f.when) }))
    .sort((a, b) => (a.nextDate || Infinity) - (b.nextDate || Infinity));

  // Index -------------------------------------------------------------------------------------------------------
  function renderIndex() {
    $("#fe_index").classList.remove("hidden");
    $("#fe_page").classList.add("hidden");
    F.wheel($("#fe_wheel"), all, (f) => pageUrl(f.id));
    const seasons = ["", ...Object.keys(F.SEASON)];
    $("#fe_seasons").innerHTML = seasons.map((s) => `<button type="button" data-s="${s}" class="${s === S.season ? "on" : ""}">${
      s ? `${F.SEASON[s][0]} ${s[0].toUpperCase() + s.slice(1)}` : "All the year"}</button>`).join("");
    const soon = dated[0];
    $("#fe_next").innerHTML = soon ? `Next: <a href="${pageUrl(soon.id)}">${F.ICON[soon.id] || ""} ${esc(soon.title)}</a>, ${F.untilText(soon.nextDate)} (${F.fmt(soon.nextDate)})` : "";
    const rows = dated.filter((f) => !S.season || f.season === S.season);
    $("#fe_cards").innerHTML = rows.map((f) => `<a class="fe-card" href="${pageUrl(f.id)}" style="--fe:${F.SEASON[f.season]?.[1] || "var(--accent)"}">
      <span class="fe-icon">${F.ICON[f.id] || "✦"}</span>
      <h2>${esc(f.title)}</h2>
      <p class="fe-when">${esc(f.when_text)}${f.nextDate ? ` · <b>${F.untilText(f.nextDate)}</b>` : ""}</p>
      <p>${esc(f.intro)}</p>
      <p class="meta">${f.facts} facts · ${f.places} places${f.churches ? ` · ${f.churches.toLocaleString()} churches` : ""}</p>
    </a>`).join("") || `<p class="meta">No festivals yet.</p>`;
    document.title = "Festivals and seasons · British Isles Oldest Buildings";
  }

  // One festival ------------------------------------------------------------------------------------------------
  const linkTo = (link, name) => link
    ? `<a href="#" data-story-open="${esc(link[0])}" data-id="${esc(link[1])}">${esc(name)}</a>` : esc(name);
  const sources = (list) => `<details class="fe-src"><summary>${list.length} source${list.length === 1 ? "" : "s"}</summary><ul>${list.map((s) =>
    `<li>“${esc(s.quote)}” — <a href="${esc(s.url)}" target="_blank" rel="noopener">${esc(s.title)}</a>${s.locator ? ` (${esc(s.locator)})` : ""}${
      s.check ? ` <span class="th-check ${s.check === "quote-found" ? "ok" : ""}">${esc(CHECK[s.check] || s.check)}</span>` : ""}</li>`).join("")}</ul></details>`;
  const yearText = (y) => (y < 0 ? `${-y} BC` : `${y}`);

  const factCard = (x, i) => `<article class="fe-fact" id="fact-${i}">
    <div class="fe-kind">${esc(F.KIND[x.kind] || x.kind)}${x.year != null ? ` · ${yearText(x.year)}` : ""}</div>
    <h3>${esc(x.title)}</h3>
    <p>${esc(x.text)}</p>
    ${x.where ? `<p class="meta">📍 ${linkTo(x.link, x.where.name)} <a href="#" data-pan="f${i}" title="Show on the map">map</a></p>` : ""}
    ${sources(x.sources)}
  </article>`;

  const placeCard = (p, i) => `<article class="fe-place">
    <h3>${linkTo(p.link, p.name)} <a href="#" data-pan="p${i}" class="hint" title="Show on the map">map</a></h3>
    <p>${esc(p.why)}</p>${sources(p.sources)}</article>`;

  const recordRow = (r, kind) => `<li>${r.image_thumb ? `<img src="${esc(r.image_thumb)}" alt="" loading="lazy">` : `<span class="fe-noimg"></span>`}
    <span><a href="#" data-story-open="${kind}" data-id="${esc(r.id)}">${esc(r.name)}</a>
    <span class="hint">${esc([r.date_text, r.kind_label, r.locality || r.nation].filter(Boolean).join(" · "))}</span></span></li>`;

  let map = null, layers = {}, markers = {};
  function drawMap(p) {
    if (map) { map.remove(); map = null; }
    map = L.map("fe_map", { maxZoom: 17 }).setView([54.3, -4.5], 5);
    addBaseLayer(map);
    markers = {};
    const dot = (lat, lon, color, r = 6) => L.circleMarker([lat, lon], { radius: r, color: "#fff", weight: 1.2, fillColor: color, fillOpacity: 0.9 });
    const open = (link, name) => (link ? `<a href="#" data-story-open="${esc(link[0])}" data-id="${esc(link[1])}">${esc(name)}</a>` : esc(name));
    const groups = {
      places: ["Places to visit", "#c0392b", L.layerGroup()], facts: ["Facts", "#8e44ad", L.layerGroup()],
      churches: [`Churches (${p.finds.dedications.join(", ")})`, "#2e6fbf", L.layerGroup()],
      found: ["Places in the catalogue", "#2e7d32", L.layerGroup()], stories: ["Stories", "#b5651d", L.layerGroup()],
      sky: ["Sky alignments", "#d4a017", L.layerGroup()] };
    p.places.forEach((x, i) => { markers[`p${i}`] = dot(x.lat, x.lon, groups.places[1], 8).bindPopup(`<b>${open(x.link, x.name)}</b><br>${esc(x.why)}`).addTo(groups.places[2]); });
    p.facts.forEach((x, i) => { if (x.where) markers[`f${i}`] = dot(x.where.lat, x.where.lon, groups.facts[1], 7).bindPopup(`<b>${esc(x.title)}</b><br>${open(x.link, x.where.name)}`).addTo(groups.facts[2]); });
    p.finds.church_points.forEach(([id, lat, lon]) => dot(lat, lon, groups.churches[1], 4).bindPopup(`<a href="#" data-story-open="building" data-id="${esc(id)}">Open the church</a>`).addTo(groups.churches[2]));
    p.finds.places.forEach((x) => { if (x.lat != null) dot(x.lat, x.lon, groups.found[1], 5).bindPopup(`<b>${open(["place", x.id], x.name)}</b><br>${esc(x.kind_label || "")}`).addTo(groups.found[2]); });
    p.finds.people.forEach((x) => { if (x.lat != null) dot(x.lat, x.lon, groups.found[1], 5).bindPopup(`<b>${open([x.kind, x.id], x.name)}</b><br>${esc(x.person)}: ${esc(x.role)}`).addTo(groups.found[2]); });
    p.finds.stories.forEach((x) => { if (x.lat != null) dot(+x.lat, +x.lon, groups.stories[1], 5).bindPopup(`<b>${open([x.entity_kind, x.entity_id], x.name)}</b><br>${esc(x.kind_label)}`).addTo(groups.stories[2]); });
    p.finds.sky.forEach((x) => { if (x.lat != null) dot(x.lat, x.lon, groups.sky[1], 6).bindPopup(`<b>${esc(x.name)}</b><br>${esc(x.claim)}`).addTo(groups.sky[2]); });
    const overlays = {};
    Object.values(groups).forEach(([label, color, g]) => {
      if (!g.getLayers().length) return;
      g.addTo(map);
      overlays[`<span class="fe-key" style="background:${color}"></span>${esc(label)}`] = g;
    });
    L.control.layers(null, overlays, { collapsed: false }).addTo(map);
    const pts = [...groups.places[2].getLayers(), ...groups.facts[2].getLayers()];
    if (pts.length) map.fitBounds(L.featureGroup(pts).getBounds().pad(0.15), { maxZoom: 9 });
    layers = groups;
  }

  const section = (id, title, body, note = "") => body ? `<section class="fe-sec" id="${id}"><h2>${title}</h2>${note}${body}</section>` : "";

  async function renderPage(id) {
    $("#fe_index").classList.add("hidden");
    const box = $("#fe_page");
    box.classList.remove("hidden");
    box.innerHTML = `<p class="meta">Loading…</p>`;
    const p = await api(`/api/festival/${encodeURIComponent(id)}`).catch(() => null);
    if (!p) { box.innerHTML = `<p>No such festival. <a href="${location.pathname}">All festivals</a></p>`; return; }
    const d = F.next(p.when), fd = p.finds, i = dated.findIndex((f) => f.id === id);
    const prev = dated[(i - 1 + dated.length) % dated.length], nxt = dated[(i + 1) % dated.length];
    const kinds = [...new Set(p.facts.map((x) => x.kind))];
    const toc = [["facts", "Facts and customs"], ["places", "Places to visit"], ["where", "Map"],
      [fd.church_count && "churches", "Churches"], [fd.stories.length && "stories", "Stories"], [fd.sky.length && "sky", "Sky"],
      [fd.on_the_day.length && "day", "On the day"], [fd.things.length && "things", "Oldest customs"]].filter(([k]) => k);
    box.innerHTML = `<p class="fe-crumb"><a href="${location.pathname}">← All festivals</a></p>
      <header class="fe-head" style="--fe:${F.SEASON[p.season]?.[1] || "var(--accent)"}">
        <span class="fe-icon big">${F.ICON[p.id] || "✦"}</span>
        <div><h1>${esc(p.title)}</h1>
          ${p.also?.length ? `<p class="meta">Also: ${p.also.map(esc).join(" · ")}</p>` : ""}
          <p class="fe-when">${esc(p.when_text)}${d ? ` · next ${F.fmt(d)}, <b>${F.untilText(d)}</b>` : ""}</p></div>
      </header>
      <p class="prose">${esc(p.intro)}</p>
      <nav class="fe-toc">${toc.map(([k, t]) => `<a href="#${k}">${t}</a>`).join("")}</nav>
      ${section("facts", "Facts and customs", `<div class="pron-chips" id="fe_kinds">${["", ...kinds].map((k) =>
        `<button type="button" data-k="${k}" class="${k ? "" : "on"}">${k ? esc(F.KIND[k] || k) : "All"}</button>`).join("")}</div>
        <div class="fe-facts">${p.facts.map(factCard).join("")}</div>`)}
      ${section("places", "Places to visit", `<div class="fe-places">${p.places.map(placeCard).join("")}</div>`)}
      <section class="fe-sec" id="where"><h2>Map</h2><div id="fe_map" class="fe-map"></div></section>
      ${section("churches", `Churches of ${fd.dedications.map(esc).join(", ")}`, fd.church_count ? `<ul class="fe-records">${fd.churches.map((r) => recordRow(r, "building")).join("")}</ul>` : "",
        `<p class="meta">${fd.church_count.toLocaleString()} catalogue records are dedicated to ${fd.dedications.length > 1 ? "them" : "this saint"} (by Wikidata); the oldest ${Math.min(fd.church_count, fd.churches.length)} are below, all on the map.</p>`)}
      ${section("found", "More places in the catalogue", (fd.places.length || fd.people.length) ? `<ul class="fe-records">${fd.places.map((r) => recordRow(r, "place")).join("")}${
        fd.people.map((r) => recordRow({ ...r, kind_label: `${r.person}: ${r.role}` }, r.kind)).join("")}</ul>` : "",
        fd.place_count > fd.places.length ? `<p class="meta">${fd.places.length} of ${fd.place_count.toLocaleString()}, oldest first.</p>` : "")}
      ${section("stories", "Stories", fd.stories.map((s) => Stories.storyHTML(s, true)).join(""),
        `<p class="meta">${fd.story_count.toLocaleString()} stories in the catalogue mention it${fd.story_count > fd.stories.length ? `; the ${fd.stories.length} that mention it most` : ""}.</p>`)}
      ${section("sky", "Sky", fd.sky.length ? `<ul class="fe-sky">${fd.sky.map((a) => `<li><b>${a.record ? linkTo(["building", a.record], a.name) : esc(a.name)}</b>
        <span class="sky-verdict ${esc(a.verdict)}">${esc(a.verdict)}</span><br>${esc(a.claim)}${a.viewing ? `<br><span class="meta">${esc(a.viewing)}</span>` : ""}</li>`).join("")}</ul>` : "",
        `<p class="meta">Monuments said to face this sunrise or sunset (researched alignments; see the <a href="${skyUrl()}">Sky calendar</a> for times and directions).</p>`)}
      ${section("day", "On the day in history", fd.on_the_day.length ? `<ul class="fe-day">${fd.on_the_day.map((r) =>
        `<li><b>${r.year}</b> ${esc(r.what)}: ${r.entity_kind === "person" ? esc(r.name) : linkTo([r.entity_kind, r.entity_id], r.name)}</li>`).join("")}</ul>` : "")}
      ${section("things", "Oldest customs and things", fd.things.length ? `<ul class="fe-day">${fd.things.map((t) =>
        `<li><a href="${thingsUrl(t.id)}">${esc(t.name)}</a> <span class="hint">${esc(t.age_text)}</span><br>${esc(t.claim)}</li>`).join("")}</ul>` : "")}
      <nav class="fe-prevnext">${prev ? `<a href="${pageUrl(prev.id)}">← ${F.ICON[prev.id] || ""} ${esc(prev.title)}</a>` : ""}
        ${nxt ? `<a href="${pageUrl(nxt.id)}">${F.ICON[nxt.id] || ""} ${esc(nxt.title)} →</a>` : ""}</nav>`;
    document.title = `${p.title} · Festivals · British Isles Oldest Buildings`;
    drawMap(p);
    $("#fe_kinds")?.addEventListener("click", (e) => {
      const b = e.target.closest("button[data-k]");
      if (!b) return;
      $("#fe_kinds").querySelectorAll("button").forEach((x) => x.classList.toggle("on", x === b));
      box.querySelectorAll(".fe-fact").forEach((el, n) => el.classList.toggle("hidden", !!b.dataset.k && p.facts[n].kind !== b.dataset.k));
    });
    if (location.hash) document.getElementById(location.hash.slice(1))?.scrollIntoView();
    else window.scrollTo(0, 0);
  }

  function render() {
    if (S.f) renderPage(S.f); else renderIndex();
  }

  $("#fe_seasons").addEventListener("click", (e) => {
    const b = e.target.closest("button[data-s]");
    if (!b) return;
    S.season = b.dataset.s;
    history.replaceState(null, "", location.pathname + (S.season ? `?season=${S.season}` : ""));
    renderIndex();
  });
  $("#fe_page").addEventListener("click", (e) => {
    const a = e.target.closest("a[data-pan]");
    if (!a) return;
    e.preventDefault();
    const m = markers[a.dataset.pan];
    if (m) { $("#fe_map").scrollIntoView({ block: "center" }); map.setView(m.getLatLng(), Math.max(map.getZoom(), 12)); m.openPopup(); }
  });
  // festival links within the page switch without a reload
  document.addEventListener("click", (e) => {
    const a = e.target.closest("a[href]"), href = a?.getAttribute("href");     // SVG links: href is not a string
    if (!a || e.metaKey || e.ctrlKey || !a.closest(".festivals-page") || href.startsWith("#")) return;
    const u = new URL(href, location.href);
    if (u.pathname !== location.pathname) return;
    e.preventDefault();
    history.pushState(null, "", u.pathname + u.search);
    S.f = u.searchParams.get("f") || "";
    render();
  });
  window.addEventListener("popstate", () => { S.f = new URLSearchParams(location.search).get("f") || ""; render(); });
  render();
})();
