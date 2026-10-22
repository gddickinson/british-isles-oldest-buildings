// Shared tour tools (Tours page, builder): modes, stop ordering (nearest neighbour + 2-opt, as
// bidb/tour_plan.py), routes (/api/route locally; straight lines when hosted), GPX/KML, Google Maps
// directions links, picking stops for a suggested tour, and drawing a tour on a Leaflet map.
const TourLib = (() => {
  const MODES = {
    walk: { label: "Walk", icon: "🚶", kmh: 4.5, stopMin: 15, detour: 1.3, loop: false, gmaps: "walking", radius: 1.3, spacing: 0.12 },
    cycle: { label: "Cycle", icon: "🚲", kmh: 15, stopMin: 15, detour: 1.35, loop: true, gmaps: "bicycling", radius: 7, spacing: 1.5 },
    drive: { label: "Drive", icon: "🚗", kmh: 50, stopMin: 35, detour: 1.4, loop: true, gmaps: "driving", radius: 25, spacing: 5 },
  };
  const THEMES = { highlights: "Highlights", ghosts: "Ghosts & legends", prehistoric: "Prehistoric", castles: "Castles",
                   churches: "Early churches", roman: "Roman", trail: "Long-distance & pilgrim ways",
                   literary: "Literary places", maritime: "Maritime heritage", industrial: "Industrial Revolution",
                   victorian: "Victorian", underground: "Underground",
                   coastal: "Coastal defences", military: "Military heritage",
                   museums: "Museums & galleries", bridges: "Bridges",
                   digs: "Archaeology & digs" };
  const rad = Math.PI / 180;
  const km = (a, b) => {
    const h = Math.sin((b.lat - a.lat) * rad / 2) ** 2 + Math.cos(a.lat * rad) * Math.cos(b.lat * rad) * Math.sin((b.lon - a.lon) * rad / 2) ** 2;
    return 12742 * Math.asin(Math.sqrt(Math.min(1, h)));
  };
  const length = (p, loop) => p.slice(1).reduce((d, s, i) => d + km(p[i], s), 0) + (loop && p.length > 2 ? km(p[p.length - 1], p[0]) : 0);

  function order(stops, loop, keepFirst = true) {
    if (stops.length < 3) return stops.slice();
    const rest = stops.slice();
    const path = [rest.splice(keepFirst ? 0 : rest.reduce((m, s, i) => (s.lon < rest[m].lon ? i : m), 0), 1)[0]];
    while (rest.length) {
      const last = path[path.length - 1];
      let best = 0;
      rest.forEach((s, i) => { if (km(last, s) < km(last, rest[best])) best = i; });
      path.push(rest.splice(best, 1)[0]);
    }
    for (let improved = true; improved;) {
      improved = false;
      for (let i = 1; i < path.length - 1; i++) {
        for (let j = i + 1; j < path.length; j++) {
          const cand = path.slice(0, i).concat(path.slice(i, j + 1).reverse(), path.slice(j + 1));
          if (length(cand, loop) < length(path, loop) - 1e-9) { path.splice(0, path.length, ...cand); improved = true; }
        }
      }
    }
    return path;
  }

  function decode(str, precision = 6) {             // Google polyline (OSRM polyline6) -> [[lat, lon]]
    const f = 10 ** precision, out = [];
    let i = 0, lat = 0, lon = 0;
    while (i < str.length) {
      for (const k of [0, 1]) {
        let shift = 0, result = 0, b;
        do { b = str.charCodeAt(i++) - 63; result |= (b & 0x1f) << shift; shift += 5; } while (b >= 0x20);
        const d = result & 1 ? ~(result >> 1) : result >> 1;
        if (k === 0) lat += d; else lon += d;
      }
      out.push([lat / f, lon / f]);
    }
    return out;
  }

  const points = (stops, loop) => stops.concat(loop && stops.length > 2 ? [stops[0]] : []);

  // {distance_km, duration_min (travel + stops), line: [[lat, lon]], routed}
  async function route(mode, stops, loop) {
    const m = MODES[mode], pts = points(stops, loop);
    let res = null;
    if (!IS_STATIC && pts.length >= 2 && pts.length <= 25) {
      res = await api(`/api/route?mode=${mode}&points=${pts.map((s) => `${s.lat.toFixed(5)},${s.lon.toFixed(5)}`).join(";")}`).catch(() => null);
      if (res && res.error) res = null;
    }
    if (res) {
      const travel = mode === "walk" ? res.distance_km / m.kmh * 60 : res.duration_min;
      return { distance_km: res.distance_km, duration_min: travel + m.stopMin * stops.length, line: decode(res.geometry), routed: true,
               elevation: res.elevation || null };
    }
    const d = length(pts, false) * m.detour;
    return { distance_km: d, duration_min: d / m.kmh * 60 + m.stopMin * stops.length,
             line: pts.map((s) => [s.lat, s.lon]), routed: false };
  }

  const hours = (min) => (min >= 90 ? `${(min / 60).toFixed(1)} h` : `${Math.round(min)} min`);
  const x = (s) => esc(s || "");

  function gpx(t) {
    return `<?xml version="1.0" encoding="UTF-8"?>
<gpx version="1.1" creator="British Isles Oldest Buildings" xmlns="http://www.topografix.com/GPX/1/1">
<metadata><name>${x(t.title)}</name></metadata>
${t.stops.map((s, i) => `<wpt lat="${s.lat}" lon="${s.lon}"><name>${i + 1}. ${x(s.name)}</name><desc>${x([s.date_text, s.category].filter(Boolean).join(" · "))}</desc></wpt>`).join("\n")}
<trk><name>${x(t.title)}</name><trkseg>${(t.line || []).map(([la, lo]) => `<trkpt lat="${la.toFixed(6)}" lon="${lo.toFixed(6)}"/>`).join("")}</trkseg></trk>
</gpx>`;
  }

  function kml(t) {
    return `<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2"><Document><name>${x(t.title)}</name>
${t.stops.map((s, i) => `<Placemark><name>${i + 1}. ${x(s.name)}</name><description>${x(s.date_text)}</description><Point><coordinates>${s.lon},${s.lat}</coordinates></Point></Placemark>`).join("\n")}
<Placemark><name>Route</name><LineString><coordinates>${(t.line || []).map(([la, lo]) => `${lo.toFixed(6)},${la.toFixed(6)}`).join(" ")}</coordinates></LineString></Placemark>
</Document></kml>`;
  }

  // Google Maps directions (up to 9 waypoints): opens on a phone for turn-by-turn navigation
  function googleMaps(mode, stops, loop) {
    const pts = points(stops, loop), ll = (s) => `${s.lat.toFixed(5)},${s.lon.toFixed(5)}`;
    const via = pts.slice(1, -1).slice(0, 9);
    return `https://www.google.com/maps/dir/?api=1&travelmode=${MODES[mode].gmaps}&origin=${ll(pts[0])}`
      + `&destination=${ll(pts[pts.length - 1])}${via.length ? "&waypoints=" + encodeURIComponent(via.map(ll).join("|")) : ""}`;
  }

  function save(name, mime, text, button) {
    if (IS_STATIC) return copyText(text, button, "Copied: paste into a file");
    const a = Object.assign(document.createElement("a"), { href: URL.createObjectURL(new Blob([text], { type: mime })), download: name });
    a.click();
    setTimeout(() => URL.revokeObjectURL(a.href), 1000);
  }
  const fileName = (t, ext) => (t.title || "tour").toLowerCase().replace(/[^a-z0-9]+/g, "_").replace(/^_|_$/g, "") + "." + ext;

  // best candidates within the radius, spread apart (as tour_plan.pick_stops); hours scales the count
  function pick(cands, centre, mode, want) {
    const m = MODES[mode], chosen = [];
    for (const c of cands.slice().sort((a, b) => b.score - a.score)) {
      if (km(centre, c) > m.radius * Math.max(1, want / 8)) continue;
      if (chosen.every((o) => km(o, c) >= m.spacing)) chosen.push(c);
      if (chosen.length >= want) break;
    }
    return chosen;
  }
  const stopsFor = (mode, hrs) => Math.max(3, Math.min(14, Math.round(hrs * 60 / (MODES[mode].stopMin + { walk: 15, cycle: 30, drive: 45 }[mode]))));

  function draw(map, layer, t, opts = {}) {
    layer.clearLayers();
    if (t.line && t.line.length > 1) L.polyline(t.line, { color: cssVar("--accent"), weight: 4, opacity: 0.8,
      dashArray: t.routed === false ? "6 6" : null }).addTo(layer);
    t.stops.forEach((s, i) => L.marker([s.lat, s.lon], { icon: L.divIcon({ className: "num-marker", html: String(i + 1), iconSize: [26, 26] }) })
      .bindPopup(`<b>${i + 1}. ${esc(s.name)}</b><br>${esc(s.date_text || "")}${opts.popup ? opts.popup(s, i) : ""}`).addTo(layer));
    if (t.stops.length) map.fitBounds(L.latLngBounds(t.stops.map((s) => [s.lat, s.lon]).concat(t.line || [])).pad(0.1));
  }

  // Follow a tour on a phone: your position, the next unvisited stop, its distance and direction;
  // a stop counts as visited within `near` km. Returns a function that stops following.
  const COMPASS = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"];
  function bearing(a, b) {
    const y = Math.sin((b.lon - a.lon) * rad) * Math.cos(b.lat * rad);
    const x = Math.cos(a.lat * rad) * Math.sin(b.lat * rad) - Math.sin(a.lat * rad) * Math.cos(b.lat * rad) * Math.cos((b.lon - a.lon) * rad);
    return COMPASS[Math.round(((Math.atan2(y, x) / rad + 360) % 360) / 45) % 8];
  }
  function follow(map, stops, mode, status) {
    if (!navigator.geolocation) { status.textContent = "Location is not available in this browser."; return () => null; }
    const near = { walk: 0.06, cycle: 0.15, drive: 0.4 }[mode] || 0.1, done = new Set();
    let me = null;
    status.textContent = "Finding your location…";
    const id = navigator.geolocation.watchPosition((p) => {
      const here = { lat: p.coords.latitude, lon: p.coords.longitude };
      if (!me) me = L.circleMarker([here.lat, here.lon], { radius: 8, color: "#fff", weight: 3, fillColor: "#1a73e8", fillOpacity: 1 }).addTo(map);
      me.setLatLng([here.lat, here.lon]);
      stops.forEach((s, i) => { if (km(here, s) <= near) done.add(i); });
      const next = stops.findIndex((s, i) => !done.has(i));
      if (next < 0) { status.textContent = "🎉 All stops visited."; return; }
      const s = stops[next], d = km(here, s);
      status.innerHTML = `Next: <b>${next + 1}. ${esc(s.name)}</b> · ${Prefs.dist(d, d < 1 ? 2 : 1)} ${bearing(here, s)} · ${done.size}/${stops.length} visited`;
      if (!map.getBounds().contains([here.lat, here.lon])) map.panTo([here.lat, here.lon]);
    }, (err) => { status.textContent = "Location unavailable: " + err.message; }, { enableHighAccuracy: true, maximumAge: 5000 });
    return () => { navigator.geolocation.clearWatch(id); if (me) me.remove(); status.textContent = ""; };
  }

  // Elevation profile (bidb/tour_elevation.py): small area chart with climb and height range
  function profileHTML(e) {
    if (!e || !e.profile || !e.profile.length) return "";
    const w = 320, h = 60, lo = Math.min(...e.profile), hi = Math.max(...e.profile), span = Math.max(hi - lo, 20);
    const pts = e.profile.map((v, i) => `${(i / (e.profile.length - 1) * w).toFixed(1)},${(h - (v - lo) / span * (h - 6) - 3).toFixed(1)}`);
    return `<div class="elev"><svg viewBox="0 0 ${w} ${h}" width="${w}" height="${h}" role="img" aria-label="Elevation profile">
      <polygon points="0,${h} ${pts.join(" ")} ${w},${h}" class="elev-fill"/><polyline points="${pts.join(" ")}" class="elev-line"/></svg>
      <span title="From a 25 m terrain model (EU-DEM via OpenTopoData): short climbs are smoothed out">↗ about ${e.climb_m} m climb · ${e.min_m}–${e.max_m} m · <b>${esc(e.hilly)}</b></span></div>`;
  }

  return { MODES, THEMES, km, follow, profileHTML, order, decode, route, hours, gpx, kml, googleMaps, save, fileName, pick, stopsFor, draw };
})();
