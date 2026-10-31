// The clock and sky controls shared by every 3D model (/stonehenge, /model/<id>): the moment shown (local solar time
// at the site, years before AD 1582 in the Gregorian calendar extended back), sunrises, sunsets and moonrises over the
// real skyline, the panel's date, time, play and event controls, the readout bar, star names and the URL state
// (?view=&y=&m=&d=&t=<minutes>&cam=). Positions from SkyPos (stonehenge_astro.js) and Sky (sky.js).
import * as THREE from "./vendor/three/three.module.min.js";
import { dir } from "./stonehenge_scene.js";

export const $ = (s) => document.querySelector(s);
export const esc = (s) => String(s ?? "").replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
export const MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"];
export const yearText = (y) => (y <= 0 ? `${1 - y} BC` : `AD ${y}`);
export const deg = (x) => `${x.toFixed(1)}°`;
export const toward = (az, r) => [r * Math.sin(az * Math.PI / 180), r * Math.cos(az * Math.PI / 180)];
export const BASE = (typeof IS_STATIC !== "undefined" && IS_STATIC ? "static" : "/static") + "/data/";

// Event keys a model may list (data.events) → [label, finder(clock) → Julian day or null, which way to face].
export const EVENT_KINDS = {
  summer_rise: ["Midsummer sunrise", (c) => c.sunEvent(90, 6, true), "summer_rise"],
  summer_set: ["Midsummer sunset", (c) => c.sunEvent(90, 6, false), "summer_set"],
  winter_rise: ["Midwinter sunrise", (c) => c.sunEvent(270, 12, true), "winter_rise"],
  winter_set: ["Midwinter sunset", (c) => c.sunEvent(270, 12, false), "winter_set"],
  equinox_rise: ["Equinox sunrise", (c) => c.sunEvent(0, 3, true), "equinox_rise"],
  equinox_set: ["Equinox sunset", (c) => c.sunEvent(0, 3, false), "equinox_set"],
  winter_moon: ["Full moon nearest midwinter, rising", (c) => c.crossing(c.fullMoonNear(c.sunAtLongitude(c.st.y, 270, 12)) - 0.75, 30, "moon", true), "winter_moon"],
  summer_moon: ["Full moon nearest midsummer, rising", (c) => c.crossing(c.fullMoonNear(c.sunAtLongitude(c.st.y, 90, 6)) - 0.75, 30, "moon", true), "summer_moon"],
};

// The clock for a site at lat/lon with its skyline ({alt: [centidegrees], step}); `update` redraws the scene.
export function createClock(lat, lon, horizon) {
  const today = new Date();
  const solarNow = (d) => Math.round(((d.getUTCHours() + d.getUTCMinutes() / 60 + lon / 15 + 24) % 24) * 60);
  const st = { view: "now", y: today.getUTCFullYear(), m: today.getUTCMonth() + 1, d: today.getUTCDate(), t: solarNow(today),
    play: 0, labels: false, names: true, axis: true, ghosts: false, lantern: false };
  const q = new URLSearchParams(location.search);
  for (const k of ["y", "m", "d", "t"]) if (q.get(k) != null && !Number.isNaN(+q.get(k))) st[k] = +q.get(k);
  if (["built", "stages"].includes(q.get("view"))) st.view = q.get("view");
  const hz = { alt: horizon.alt.map((a) => a / 100), step: horizon.step };

  const at = () => SkyPos.at(st.y, st.m, st.d, st.t / 60, lat, lon);
  // Moment from a Julian day (UT) → local solar date and minutes.
  function setJD(jd) {
    const c = SkyPos.calendarDate(jd + lon / 360);
    Object.assign(st, { y: c.year, m: c.month, d: c.day, t: Math.round(c.hours * 60) % 1440 });
  }
  const jdNow = () => SkyPos.julianDay(st.y, st.m, st.d, st.t / 60 - lon / 15);
  const posAt = (jd) => { const c = SkyPos.calendarDate(jd + lon / 360); return SkyPos.at(c.year, c.month, c.day, c.hours, lat, lon); };
  // Upper limb above the skyline (degrees; > 0 once the first gleam shows).
  const clear = (p, body) => p[body].seen + (body === "sun" ? 0.266 : 0.259) - Sky.altitudeAt(hz.alt, hz.step, p[body].az);
  function crossing(jd0, hours, body, rising) {
    let prev = clear(posAt(jd0), body);
    for (let k = 1; k <= hours * 6; k++) {
      const jd = jd0 + k / 144, c = clear(posAt(jd), body);
      if (rising ? prev <= 0 && c > 0 : prev > 0 && c <= 0) {
        let lo = jd - 1 / 144, hi = jd;
        for (let i = 0; i < 20; i++) { const mid = (lo + hi) / 2, v = clear(posAt(mid), body); if (rising ? v > 0 : v <= 0) hi = mid; else lo = mid; }
        return hi;
      }
      prev = c;
    }
    return null;
  }
  function sunAtLongitude(year, target, month) {
    let jd = SkyPos.julianDay(year, month, 21, 12);
    for (let i = 0; i < 6; i++) jd += ((((target - Sky.sunLongitude(jd)) % 360) + 540) % 360 - 180) / 360 * 365.2422;
    return jd;
  }
  function fullMoonNear(jd) {
    let best = jd, bp = -1;
    for (let k = -16; k <= 16; k += 0.25) { const ph = posAt(jd + k).moon.phase; if (ph > bp) { bp = ph; best = jd + k; } }
    return best;
  }
  const midnight = (jd) => Math.floor(jd + lon / 360 - 0.5) + 0.5 - lon / 360;   // local midnight (UT Julian day)
  const sunEvent = (slon, month, rising) => crossing(midnight(sunAtLongitude(st.y, slon, month)), 24, "sun", rising);
  return { st, q, hz, lat, lon, at, setJD, jdNow, posAt, crossing, sunAtLongitude, fullMoonNear, sunEvent, solarNow, today };
}

// Wire the panel (#sh_* controls) to a clock: `update()` redraws; `face(key)` turns the camera for an event;
// `events` are keys of EVENT_KINDS (or [key, [label, finder, face]] pairs for a model's own).
export function wirePanel(clock, { update, events, face, views }) {
  const { st } = clock;
  const list = events.map((e) => (Array.isArray(e) ? e : [e, EVENT_KINDS[e]]));
  $("#sh_events").innerHTML = list.map(([k, [t]]) => `<button type="button" class="btn" data-ev="${k}">${esc(t)}</button>`).join("");
  $("#sh_events").addEventListener("click", (e) => {
    const b = e.target.closest("[data-ev]");
    if (!b) return;
    const [, [label, fn, side]] = list.find(([k]) => k === b.dataset.ev), jd = fn(clock);
    if (jd == null) { $("#sh_note").textContent = "Not found in that year."; return; }
    clock.setJD(jd + 2 / 1440);
    st.play = 0; $("#sh_play").textContent = "▶ Play";
    const p = clock.posAt(jd);
    $("#sh_note").textContent = `${label}: ${deg(p.sun.az)} (sun) · ${deg(p.moon.az)} (moon), over the real skyline.`;
    face(side);
    update();
  });
  $("#sh_cams").innerHTML = Object.entries(views).map(([k, [t]]) => `<option value="${k}">${esc(t)}</option>`).join("");
  $("#sh_cams").addEventListener("change", (e) => views[e.target.value][1]());
  document.querySelectorAll("[name=sh_view]").forEach((r) => r.addEventListener("change", () => { st.view = r.value; update(); }));
  $("#sh_time").addEventListener("input", (e) => { st.t = +e.target.value; update(); });
  const readDate = () => {
    const y = Math.max(1, +$("#sh_y").value || 1);
    st.y = $("#sh_era").value === "BC" ? 1 - y : y;
    st.m = Math.min(12, Math.max(1, +$("#sh_m").value || 1));
    st.d = Math.min(31, Math.max(1, +$("#sh_d").value || 1));
    update();
  };
  ["#sh_y", "#sh_m", "#sh_d", "#sh_era"].forEach((s) => $(s).addEventListener("change", readDate));
  $("#sh_m").innerHTML = MONTHS.map((n, i) => `<option value="${i + 1}">${n}</option>`).join("");
  $("#sh_play").addEventListener("click", (e) => { st.play = st.play ? 0 : +$("#sh_speed").value; e.target.textContent = st.play ? "❚❚ Pause" : "▶ Play"; });
  $("#sh_speed").addEventListener("change", (e) => { if (st.play) st.play = +e.target.value; });
  $("#sh_now").addEventListener("click", () => {
    const n = new Date();
    Object.assign(st, { y: n.getUTCFullYear(), m: n.getUTCMonth() + 1, d: n.getUTCDate(), t: clock.solarNow(n) });
    update();
  });
  [["#sh_labels", "labels"], ["#sh_starnames", "names"], ["#sh_axis", "axis"], ["#sh_ghosts", "ghosts"], ["#sh_lantern", "lantern"]].forEach(([s, k]) => {
    if (!$(s)) return;
    $(s).checked = st[k];
    $(s).addEventListener("change", (e) => { st[k] = e.target.checked; update(); });
  });
  for (const [k, v] of Object.entries(clock.extra || {})) u.set(k, v);          // a page's own state (stage)
  const cam = clock.q.get("cam");
  views[cam && views[cam] ? cam : Object.keys(views)[0]][1]();
  if (cam && views[cam]) $("#sh_cams").value = cam;
}

// Open on a chosen moment when the link names none (data.start: {event, after: minutes}, {sun: "rise"|"set", m, d,
// after} or {m, d, t}; year optional).
export function startMoment(clock, start, note) {
  if (!start || ["y", "m", "d", "t"].some((k) => clock.q.has(k))) return;
  if (start.year != null) clock.st.y = start.year;
  if (start.view && !clock.q.has("view")) clock.st.view = start.view;
  if (start.sun && start.m) {                                       // sunrise or sunset on a given day
    const jd0 = SkyPos.julianDay(clock.st.y, start.m, start.d, 0) - clock.lon / 360;
    const jd = clock.crossing(jd0, 24, "sun", start.sun === "rise");
    if (jd == null) return;
    clock.setJD(jd + (start.after ?? 2) / 1440);
  } else if (start.event) {
    const jd = EVENT_KINDS[start.event]?.[1](clock);
    if (jd == null) return;
    clock.setJD(jd + (start.after ?? 2) / 1440);
    if (start.t != null) clock.st.t = start.t;
  } else Object.assign(clock.st, { m: start.m, d: start.d, t: start.t });
  if (note) $("#sh_note").textContent = note;
}

// The readout bar, panel fields and URL for the clock's moment `P` (SkyPos.at output).
export function readout(clock, P) {
  const { st } = clock;
  const c = SkyPos.calendarDate(SkyPos.julianDay(st.y, st.m, st.d, 12));
  const hh = String(Math.floor(st.t / 60)).padStart(2, "0"), mm = String(Math.floor(st.t % 60)).padStart(2, "0");
  $("#sh_when").textContent = `${c.day} ${MONTHS[c.month - 1]} ${yearText(c.year)}, ${hh}:${mm} local solar time`;
  const s = P.sun, mo = P.moon;
  $("#sh_read").innerHTML = `<b>Sun</b> ${deg(s.az)} ${Sky.compass(s.az)}, ${s.seen >= 0 ? "" : "below the horizon, "}altitude ${deg(s.seen)}
    · <b>Moon</b> ${deg(mo.az)} ${Sky.compass(mo.az)}, altitude ${deg(mo.seen)}, ${Math.round(mo.phase * 100)}% lit, ${mo.waxing ? "waxing" : "waning"}
    <span class="meta">· ΔT ${(P.deltaT / 3600).toFixed(P.deltaT > 3600 ? 1 : 3)} h · Gregorian calendar extended back</span>`;
  $("#sh_time").value = st.t;
  const yv = st.y <= 0 ? 1 - st.y : st.y;
  for (const k of ["y", "m", "d"]) { const el = $("#sh_" + k), v = k === "y" ? yv : st[k]; if (el && +el.value !== v) el.value = v; }
  $("#sh_era").value = st.y <= 0 ? "BC" : "AD";
  document.querySelectorAll("[name=sh_view]").forEach((r) => { r.checked = r.value === st.view; });
  const u = new URLSearchParams({ view: st.view, y: st.y, m: st.m, d: st.d, t: Math.round(st.t) });
  for (const [k, v] of Object.entries(clock.extra || {})) u.set(k, v);          // a page's own state (stage)
  const cam = clock.q.get("cam");
  if (cam) u.set("cam", cam);
  history.replaceState(null, "", `${location.pathname}?${u}`);
}

// Advance the clock while playing (dt seconds); true when the moment changed.
export function tick(clock, dt) {
  const { st } = clock;
  if (!st.play) return false;
  st.t += st.play * dt;
  if (st.t >= 1440 || st.t < 0) { clock.setJD(clock.jdNow() + Math.floor(st.t / 1440)); st.t = ((st.t % 1440) + 1440) % 1440; }
  st.t = Math.round(st.t * 100) / 100;
  return true;
}

// Names of the bright stars and the moon, kept beside them on screen.
export function starNames(W, stars, camera, canvas) {
  const names = stars.map((s, i) => [s[6], i]).filter(([n]) => n);
  const box = $("#sh_names");
  box.innerHTML = names.map(([n]) => `<span>${esc(n)}</span>`).join("") + '<span class="sh-body">Moon</span>';
  const v3 = new THREE.Vector3();
  return function place(P, show) {
    const spans = box.children, on = show && W.starPts.visible;
    const look = camera.getWorldDirection(new THREE.Vector3());
    names.forEach(([, i], k) => {
      const el = spans[k];
      if (!on) { el.style.display = "none"; return; }
      v3.fromBufferAttribute(W.starPts.geometry.attributes.position, i);
      if (!(v3.y > 60 && look.dot(v3) > 0)) { el.style.display = "none"; return; }
      v3.project(camera);
      el.style.display = ""; el.style.left = `${(v3.x + 1) / 2 * canvas.clientWidth}px`; el.style.top = `${(1 - v3.y) / 2 * canvas.clientHeight}px`;
    });
    const mEl = spans[spans.length - 1], md = dir(P.moon.seen, P.moon.az).multiplyScalar(7000);
    const front = look.dot(md) > 0 && P.moon.seen > -1;
    mEl.style.display = show && front ? "" : "none";
    if (front) { md.project(camera); mEl.style.left = `${(md.x + 1) / 2 * canvas.clientWidth}px`; mEl.style.top = `${(1 - md.y) / 2 * canvas.clientHeight + 26}px`; }
  };
}
