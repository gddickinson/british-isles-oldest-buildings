// Page /stonehenge (loaded by stonehenge_page.js when WebGL works): the 3D model of Stonehenge now and as thought complete, under the sky of any date and time
// (stonehenge_scene.js, stonehenge_stones.js; positions from SkyPos in stonehenge_astro.js, sky.js). Click a stone for
// its record and sources. URL state: ?view=now|built&y=&m=&d=&t=<minutes>&cam=<preset>.
import * as THREE from "./vendor/three/three.module.min.js";
import { OrbitControls } from "./vendor/three/OrbitControls.js";
import { createScene, dir } from "./stonehenge_scene.js";
import { stoneMesh, label, material } from "./stonehenge_stones.js";

const BASE = (typeof IS_STATIC !== "undefined" && IS_STATIC ? "static" : "/static") + "/data/";
const $ = (s) => document.querySelector(s);
const esc = (s) => String(s ?? "").replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
const MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"];
const yearText = (y) => (y <= 0 ? `${1 - y} BC` : `AD ${y}`);
const deg = (x) => `${x.toFixed(1)}°`;

const [data, raw] = await Promise.all([fetch(BASE + "stonehenge.json").then((r) => r.json()),
  fetch(BASE + "stonehenge_dtm.bin").then((r) => r.arrayBuffer())]);
const LAT = data.origin.lat, LON = data.origin.lon;
const canvas = $("#sh_canvas");
const W = createScene(canvas, data, raw);
const { scene, camera, renderer, height } = W;
const controls = new OrbitControls(camera, canvas);
controls.enableDamping = true;
controls.maxPolarAngle = Math.PI * 0.97;        // free to look up from eye level; the ground clamp keeps it above the turf
controls.minDistance = 0.02;
controls.maxDistance = 1800;

// ---- the stones ----
const centre = (pts) => [pts.reduce((s, p) => s + p[0], 0) / pts.length, pts.reduce((s, p) => s + p[1], 0) / pts.length];
const groundAt = (pts) => { const c = centre(pts); return height(c[0], c[1]) ?? 0; };
const heel = data.now.find((s) => s.id === "96");
function model(list, built) {
  const g = new THREE.Group(), labels = new THREE.Group();
  list.forEach((s, i) => {
    const pts = s.arc ? null : s.outline;
    const c = s.arc ? [s.arc.cx + s.arc.r * Math.sin(s.arc.az * Math.PI / 180), s.arc.cy + s.arc.r * Math.cos(s.arc.az * Math.PI / 180)] : centre(pts);
    const gnd = height(c[0], c[1]) ?? 0;
    const st = { ...s };
    if (!built && s.id === "96") st.lean = [27, (Math.atan2(-c[0], -c[1]) * 180 / Math.PI + 360) % 360];   // leans towards the circle
    const m = stoneMesh(st, gnd, { seed: i * 7 + 3 });
    if (!m) return;
    if (built && s.status === "restored") { m.userData.plain = m.material; m.userData.pale = material(s.kind, true); }
    g.add(m);
    if (s.id) {
      const sp = label(s.id);
      sp.position.set(c[0], gnd + (s.base ?? 0) + s.h + 0.7, -c[1]);
      labels.add(sp);
    }
  });
  g.add(labels);
  return { g, labels };
}
const NOW = model(data.now, false), BUILT = model(data.built, true);
scene.add(NOW.g, BUILT.g);
const axis = new THREE.Group();
[49.57, 229.57].forEach((az) => {
  const pts = [];
  for (let r = 0; r <= 140; r += 2) { const x = r * Math.sin(az * Math.PI / 180), y = r * Math.cos(az * Math.PI / 180); pts.push(new THREE.Vector3(x, (height(x, y) ?? 0) + 0.08, -y)); }
  axis.add(new THREE.Line(new THREE.BufferGeometry().setFromPoints(pts), new THREE.LineBasicMaterial({ color: 0xffcc33 })));
});
scene.add(axis);

// ---- state ----
const today = new Date();
const st = { view: "now", y: today.getUTCFullYear(), m: today.getUTCMonth() + 1, d: today.getUTCDate(),
  t: Math.round(((today.getUTCHours() + today.getUTCMinutes() / 60 + LON / 15 + 24) % 24) * 60), play: 0,
  labels: false, names: true, axis: true, ghosts: false };
const q = new URLSearchParams(location.search);
for (const k of ["y", "m", "d", "t"]) if (q.get(k) != null && !Number.isNaN(+q.get(k))) st[k] = +q.get(k);
if (q.get("view") === "built") st.view = "built";

const at = () => SkyPos.at(st.y, st.m, st.d, st.t / 60, LAT, LON);
// Moment from a Julian day (UT) → local solar date and minutes.
function setJD(jd) {
  const c = SkyPos.calendarDate(jd + LON / 360);
  Object.assign(st, { y: c.year, m: c.month, d: c.day, t: Math.round(c.hours * 60) % 1440 });
}
const jdNow = () => SkyPos.julianDay(st.y, st.m, st.d, st.t / 60 - LON / 15);
const posAt = (jd) => { const c = SkyPos.calendarDate(jd + LON / 360); return SkyPos.at(c.year, c.month, c.day, c.hours, LAT, LON); };
const hz = { alt: data.horizon.alt.map((a) => a / 100), step: data.horizon.step };
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
const midnight = (jd) => Math.floor(jd + LON / 360 - 0.5) + 0.5 - LON / 360;   // local midnight (UT Julian day)
const sunEvent = (lon, month, rising) => crossing(midnight(sunAtLongitude(st.y, lon, month)), 24, "sun", rising);
const EVENTS = {
  summer_rise: ["Midsummer sunrise", () => sunEvent(90, 6, true), "ne"],
  winter_set: ["Midwinter sunset", () => sunEvent(270, 12, false), "sw"],
  winter_rise: ["Midwinter sunrise", () => sunEvent(270, 12, true), "se"],
  equinox_rise: ["Equinox sunrise", () => sunEvent(0, 3, true), "e"],
  winter_moon: ["Full moon nearest midwinter, rising", () => crossing(fullMoonNear(sunAtLongitude(st.y, 270, 12)) - 0.75, 30, "moon", true), "ne"],
  summer_moon: ["Full moon nearest midsummer, rising", () => crossing(fullMoonNear(sunAtLongitude(st.y, 90, 6)) - 0.75, 30, "moon", true), "se"],
};

// ---- camera presets ----
const eye = (x, y) => (height(x, y) ?? 0) + 1.6;
// Camera at `from` looking at `to` ([x, y(north), height?]); standing (eye level): it turns on the spot, so
// dragging looks round and up at the sky (the orbit centre a few centimetres ahead).
function look(from, to, fov = 50, standing = false) {
  camera.position.set(from[0], from[2] ?? eye(from[0], from[1]), -from[1]);
  const t = new THREE.Vector3(to[0], to[2] ?? eye(to[0], to[1]), -to[1]);
  if (standing) t.sub(camera.position).normalize().multiplyScalar(0.05).add(camera.position);
  controls.target.copy(t);
  controls.enableZoom = !standing;
  camera.fov = fov; camera.updateProjectionMatrix(); controls.update();
}
const toward = (az, r) => [r * Math.sin(az * Math.PI / 180), r * Math.cos(az * Math.PI / 180)];
const heelC = heel ? centre(heel.outline) : toward(51, 77);
const VIEWS = {
  overview: ["Overview", () => look([-48, -62, 38], [0, 0, 2])],
  above: ["From above", () => look([0, -0.01, 120], [0, 0, 0], 40)],
  centre_ne: ["Centre, facing the sunrise (NE)", () => look([0, 0], toward(49.57, 6), 60, true)],
  centre_sw: ["Centre, facing the sunset (SW)", () => look([0, 0], toward(229.57, 6), 60, true)],
  heel: ["From the Heel Stone, facing the circle", () => look(toward(49.57, 110), [0, 0], 40, true)],
  avenue: ["Along the Avenue", () => look(toward(49.57, 140), [0, 0], 40, true)],
  ne: ["Outside, facing the sunrise", () => look(toward(229.57, 35), toward(49.57, 60), 55, true)],
  sw: ["Outside, facing the sunset", () => look(toward(49.57, 35), toward(229.57, 60), 55, true)],
  sky: ["Centre, looking up at the sky", () => look([0, 0], [0, 8, 40], 75, true)],
};
const FOR = { ne: "centre_ne", sw: "centre_sw", se: "overview", e: "overview" };

// ---- drawing ----
const names = (data.stars.map((s, i) => [s[6], i]).filter(([n]) => n));
const nameBox = $("#sh_names");
nameBox.innerHTML = names.map(([n]) => `<span>${esc(n)}</span>`).join("") + '<span class="sh-body">Moon</span>';
let P = null;
function update() {
  P = at();
  W.setSky(P, data.stars);
  NOW.g.visible = st.view === "now"; BUILT.g.visible = st.view === "built";
  NOW.labels.visible = BUILT.labels.visible = st.labels;
  BUILT.g.children.forEach((m) => { if (m.userData.pale) m.material = st.ghosts ? m.userData.pale : m.userData.plain; });
  axis.visible = st.axis;
  const c = SkyPos.calendarDate(SkyPos.julianDay(st.y, st.m, st.d, 12));
  const hh = String(Math.floor(st.t / 60)).padStart(2, "0"), mm = String(st.t % 60).padStart(2, "0");
  $("#sh_when").textContent = `${c.day} ${MONTHS[c.month - 1]} ${yearText(c.year)}, ${hh}:${mm} local solar time`;
  const s = P.sun, mo = P.moon;
  $("#sh_read").innerHTML = `<b>Sun</b> ${deg(s.az)} ${Sky.compass(s.az)}, ${s.seen >= 0 ? "" : "below the horizon, "}altitude ${deg(s.seen)}
    · <b>Moon</b> ${deg(mo.az)} ${Sky.compass(mo.az)}, altitude ${deg(mo.seen)}, ${Math.round(mo.phase * 100)}% lit, ${mo.waxing ? "waxing" : "waning"}
    <span class="meta">· ΔT ${(P.deltaT / 3600).toFixed(P.deltaT > 3600 ? 1 : 3)} h · Gregorian calendar extended back</span>`;
  $("#sh_time").value = st.t;
  for (const k of ["y", "m", "d"]) { const el = $("#sh_" + k); if (el && +el.value !== (k === "y" ? Math.abs(st.y <= 0 ? 1 - st.y : st.y) : st[k])) el.value = k === "y" ? (st.y <= 0 ? 1 - st.y : st.y) : st[k]; }
  $("#sh_era").value = st.y <= 0 ? "BC" : "AD";
  document.querySelectorAll("[name=sh_view]").forEach((r) => { r.checked = r.value === st.view; });
  const u = new URLSearchParams({ view: st.view, y: st.y, m: st.m, d: st.d, t: st.t });
  history.replaceState(null, "", `${location.pathname}?${u}`);
}
const v3 = new THREE.Vector3();
function placeNames() {
  const show = st.names && W.starPts.visible;
  const spans = nameBox.children;
  names.forEach(([, i], k) => {
    const el = spans[k];
    if (!show) { el.style.display = "none"; return; }
    v3.fromBufferAttribute(W.starPts.geometry.attributes.position, i);
    const ok = v3.y > 60 && v3.clone().project(camera).z < 1 && camera.getWorldDirection(new THREE.Vector3()).dot(v3) > 0;
    if (!ok) { el.style.display = "none"; return; }
    v3.project(camera);
    el.style.display = ""; el.style.left = `${(v3.x + 1) / 2 * canvas.clientWidth}px`; el.style.top = `${(1 - v3.y) / 2 * canvas.clientHeight}px`;
  });
  const mEl = spans[spans.length - 1], md = dir(P.moon.seen, P.moon.az).multiplyScalar(7000);
  const front = camera.getWorldDirection(new THREE.Vector3()).dot(md) > 0 && P.moon.seen > -1;
  mEl.style.display = st.names && front ? "" : "none";
  if (front) { md.project(camera); mEl.style.left = `${(md.x + 1) / 2 * canvas.clientWidth}px`; mEl.style.top = `${(1 - md.y) / 2 * canvas.clientHeight + 26}px`; }
}

let last = performance.now();
function frame(now) {
  const dt = Math.min(0.1, (now - last) / 1000);
  last = now;
  if (st.play) {
    st.t += st.play * dt;
    if (st.t >= 1440 || st.t < 0) { setJD(jdNow() + Math.floor(st.t / 1440)); st.t = ((st.t % 1440) + 1440) % 1440; }
    st.t = Math.round(st.t * 100) / 100;
    update();
  }
  controls.update();
  const g = (height(camera.position.x, -camera.position.z) ?? 0) + 0.4;
  if (camera.position.y < g) camera.position.y = g;
  renderer.render(scene, camera);
  placeNames();
  requestAnimationFrame(frame);
}

// ---- stone records ----
const ray = new THREE.Raycaster(), ptr = new THREE.Vector2();
let down = null;
canvas.addEventListener("pointerdown", (e) => { down = [e.clientX, e.clientY]; });
canvas.addEventListener("pointerup", (e) => {
  if (!down || Math.hypot(e.clientX - down[0], e.clientY - down[1]) > 4) return;
  const r = canvas.getBoundingClientRect();
  ptr.set((e.clientX - r.left) / r.width * 2 - 1, -(e.clientY - r.top) / r.height * 2 + 1);
  ray.setFromCamera(ptr, camera);
  const hit = ray.intersectObject(st.view === "now" ? NOW.g : BUILT.g, true).find((h) => h.object.isMesh && h.object.visible);
  showStone(hit ? hit.object.userData : null);
});
const STATUS = { surviving: "Survives, in place", placed: "Survives, shown where it stood", restored: "Lost: drawn where it is thought to have stood" };
function showStone(u) {
  const box = $("#sh_stone");
  if (!u) { box.hidden = true; return; }
  const rec = data.stones[u.id] || {};
  const name = u.id ? `Stone ${esc(u.id)}` : "Bluestone";
  box.hidden = false;
  box.innerHTML = `<button type="button" class="sh-close" aria-label="Close">×</button><h3>${name}</h3>
    <p class="meta">${esc((u.group || rec.group || "").replace(/_/g, " "))}${st.view === "built" && u.status ? ` · ${esc(STATUS[u.status])}` : rec.state ? ` · today: ${esc(rec.state)}` : ""}</p>
    ${rec.notes ? `<p>${esc(rec.notes)}</p>` : ""}
    ${(rec.cites || []).length ? `<ul class="sh-cites">${rec.cites.map((c) => `<li>“${esc(c.quote)}” <a href="${esc(c.url)}" target="_blank" rel="noopener">${esc(c.title)}</a></li>`).join("")}</ul>` : ""}`;
  box.querySelector(".sh-close").onclick = () => { box.hidden = true; };
}

// ---- controls ----
$("#sh_events").innerHTML = Object.entries(EVENTS).map(([k, [t]]) => `<button type="button" class="btn" data-ev="${k}">${t}</button>`).join("");
$("#sh_cams").innerHTML = Object.entries(VIEWS).map(([k, [t]]) => `<option value="${k}">${t}</option>`).join("");
$("#sh_events").addEventListener("click", (e) => {
  const b = e.target.closest("[data-ev]");
  if (!b) return;
  const [, fn, face] = EVENTS[b.dataset.ev], jd = fn();
  if (jd == null) { $("#sh_note").textContent = "Not found in that year."; return; }
  setJD(jd + 2 / 1440);
  st.play = 0; $("#sh_play").textContent = "▶ Play";
  $("#sh_note").textContent = `${b.textContent}: ${deg(posAt(jd).sun.az)} (sun) · ${deg(posAt(jd).moon.az)} (moon), over the real skyline.`;
  if (FOR[face]) { $("#sh_cams").value = FOR[face]; VIEWS[FOR[face]][1](); }
  update();
});
$("#sh_cams").addEventListener("change", (e) => VIEWS[e.target.value][1]());
document.querySelectorAll("[name=sh_view]").forEach((r) => r.addEventListener("change", () => {
  st.view = r.value;
  if (st.view === "built" && st.y > 0) { st.y = -2499; }
  if (st.view === "now" && st.y <= 0) { st.y = today.getUTCFullYear(); }
  update();
}));
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
  Object.assign(st, { view: "now", y: n.getUTCFullYear(), m: n.getUTCMonth() + 1, d: n.getUTCDate(), t: Math.round(((n.getUTCHours() + n.getUTCMinutes() / 60 + LON / 15 + 24) % 24) * 60) });
  update();
});
[["#sh_labels", "labels"], ["#sh_starnames", "names"], ["#sh_axis", "axis"], ["#sh_ghosts", "ghosts"]].forEach(([s, k]) => {
  $(s).checked = st[k];
  $(s).addEventListener("change", (e) => { st[k] = e.target.checked; update(); });
});
$("#sh_credits").innerHTML = data.credits.map((c) => `<li>${esc(c)}</li>`).join("")
  + `<li>Plan placed on the ground by fitting it to ${data.origin.fit.pairs} stones mapped on OpenStreetMap (shift only, keeping the plan's north; ${data.origin.fit.rms_m} m root mean square).</li>`;
$("#sh_debate").innerHTML = (data.debate || []).map((d) => `<li>${esc(d.claim)} ${(d.cites || []).map((c) => `<span class="meta">“${esc(c.quote)}”</span>`).join(" ")}</li>`).join("");

window.addEventListener("resize", W.resize);
W.resize();
VIEWS[q.get("cam") && VIEWS[q.get("cam")] ? q.get("cam") : "overview"][1]();
if (q.get("cam")) $("#sh_cams").value = q.get("cam");
// With no moment in the link, open on a midsummer morning this year (the stones in sunlight) rather than
// whatever the present hour is, perhaps the dark.
if (!["y", "m", "d", "t"].some((k) => q.has(k))) {
  const jd = EVENTS.summer_rise[1]();
  if (jd != null) {
    setJD(jd);
    st.t = 10 * 60;
    $("#sh_note").textContent = "Midsummer morning this year. Press “Midsummer sunrise” for the sun over the Heel Stone, or “Now” for the sky at this moment.";
  }
}
update();
document.body.classList.add("sh-ready");
requestAnimationFrame(frame);
window.SH = { st, update, scene, camera, controls, data };   // for checks
