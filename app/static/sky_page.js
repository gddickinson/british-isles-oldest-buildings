// Sky calendar (/sky, roadmap SK6): the next solstices, equinoxes and cross-quarter days in date order, each with the
// researched alignments facing that sunrise or sunset (static/data/sky.json via SkyHere.load), the time the sun rises
// or sets at each site, and how to see it; the moon's standstills and the sites said to face them; a map of all.
(async () => {
  const $ = (s) => document.querySelector(s);
  const { all } = await SkyHere.load();
  // Ecliptic longitudes of the year's events; both equinoxes are the alignments' "equinox"
  const EVENTS = [
    [0, "equinox", "Spring equinox", "Day and night about equal; the sun rises almost due east and sets almost due west."],
    [45, "beltane", "Beltane (astronomical)", "Half way between the spring equinox and midsummer; the festival itself is on 1 May."],
    [90, "summer_solstice", "Midsummer (summer solstice)", "The longest day: the sun rises and sets furthest north, and stays there for several days."],
    [135, "lughnasa", "Lughnasa (astronomical)", "Half way between midsummer and the autumn equinox; the festival itself is on 1 August."],
    [180, "equinox", "Autumn equinox", "Day and night about equal; the sun rises almost due east and sets almost due west."],
    [225, "samhain", "Samhain (astronomical)", "Half way between the autumn equinox and midwinter; the festival itself is on 1 November."],
    [270, "winter_solstice", "Midwinter (winter solstice)", "The shortest day: the sun rises and sets furthest south, and stays there for several days."],
    [315, "imbolc", "Imbolc (astronomical)", "Half way between midwinter and the spring equinox; the festival itself is on 1 February."],
  ];
  const VERDICT = { established: "Established", probable: "Probable", disputed: "Disputed" };
  const TZ = { timeZone: "Europe/London" };
  const day = (d) => d.toLocaleDateString(undefined, { ...TZ, weekday: "long", day: "numeric", month: "long", year: "numeric" });
  const time = (jd) => (jd == null ? "–" : Sky.dateOf(jd).toLocaleTimeString(undefined, { ...TZ, hour: "2-digit", minute: "2-digit" }));
  const link = (a) => (!a.record ? esc(a.name) : a.record.startsWith("Q")
    ? `<a href="${esc(buildingUrl(a.record))}" data-open="${esc(a.record)}">${esc(a.name)}</a>`
    : `<a href="#" data-place="${esc(a.record)}">${esc(a.name)}</a>`);
  const badge = (a) => `<span class="sky-verdict ${esc(a.verdict)}">${esc(VERDICT[a.verdict] || a.verdict)}</span>`;

  function site(a, jd) {
    let when = "";
    if (jd != null) {
      const d0 = Math.floor(jd - 0.5) + 0.5, [rise, set] = Sky.riseSetTimes(a.lat, a.lon, d0);
      when = ` · sun${a.rise_set} ${time(a.rise_set === "rise" ? rise : set)}`;
    }
    const az = a.azimuth_built ?? a.azimuth_now;
    return `<li>${link(a)} ${badge(a)}<span class="meta"> ${esc(a.body)}${esc(a.rise_set || "")}${
      az != null ? ` towards ${az.toFixed(0)}° ${Sky.compass(az)}` : ""}${when}</span>
      <br>${esc(a.claim)}${a.viewing ? `<br><span class="meta">Seeing it: ${esc(a.viewing)}</span>` : ""}</li>`;
  }

  function render() {
    const rows = all.filter((a) => $("#sk_disputed").checked || a.verdict !== "disputed");
    $("#sk_count").textContent = `${rows.length} alignments`;
    const now = Sky.jdOf(new Date());
    const coming = EVENTS.map(([lon, key, title, text]) => ({ jd: Sky.nextLongitude(lon, now), key, title, text }))
      .sort((a, b) => a.jd - b.jd);
    $("#sk_events").innerHTML = coming.map((e) => {
      const here = rows.filter((a) => a.body === "sun" && a.event === e.key);
      return `<article class="sky-event"><h2>${esc(e.title)} <span class="sky-when">${esc(day(Sky.dateOf(e.jd)))}</span></h2>
        <p class="meta">${esc(e.text)}</p>
        ${here.length ? `<ul class="sky-sites">${here.map((a) => site(a, e.jd)).join("")}</ul>`
          : '<p class="meta">No researched alignment faces this one.</p>'}</article>`;
    }).join("");
    const moon = rows.filter((a) => a.body === "moon");
    const major = Sky.next("moon", "major_south"), minor = Sky.next("moon", "minor_south");
    $("#sk_moon").innerHTML = `<h2>The moon's standstills</h2>
      <p class="prose">Every 18.6 years the moon's rising and setting points swing out beyond the sun's: at a major
        standstill it rises and sets furthest north and south, at a minor standstill least far. Its season lasts about a
        year either side of the peak. Major standstill: ${major.season ? `now (peak ${major.date.getFullYear()})`
          : `next peak ${major.date.getFullYear()}`}; minor: ${minor.season ? `now (peak ${minor.date.getFullYear()})` : `next peak ${minor.date.getFullYear()}`}.</p>
      ${moon.length ? `<ul class="sky-sites">${moon.map((a) => site(a, null)).join("")}</ul>` : ""}`;
    drawMap(rows);
  }

  let map, layer;
  const COLOR = { established: "#2e7d32", probable: "#d08a12", disputed: "#b5651d" };
  function drawMap(rows) {
    if (!map) { map = L.map("sk_map", { maxZoom: 17 }).setView([54.5, -4.5], 5); addBaseLayer(map); }
    if (layer) layer.remove();
    layer = L.layerGroup().addTo(map);
    rows.forEach((a) => L.circleMarker([a.lat, a.lon], { radius: 7, color: "#fff", weight: 1.5, fillColor: COLOR[a.verdict], fillOpacity: 0.9 })
      .bindPopup(`<b>${link(a)}</b> ${badge(a)}<br>${esc(a.event ? `${Sky.NAMES[a.event]} ${a.body}${a.rise_set}` : `${a.body} (no event named)`)}`)
      .addTo(layer));
    if (rows.length && !drawMap.fitted) { map.fitBounds(rows.map((a) => [a.lat, a.lon]), { padding: [20, 20] }); drawMap.fitted = true; }
  }
  $("#sk_disputed").addEventListener("change", render);
  render();
})();
