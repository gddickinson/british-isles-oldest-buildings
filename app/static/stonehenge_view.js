// Page /stonehenge (loaded by stonehenge_page.js when WebGL works): the 3D model of Stonehenge now and as thought complete, under the sky of any date and time
// (stonehenge_scene.js, stonehenge_stones.js; clock, panel and sky events from model_clock.js). Click a stone for
// its record and sources. By stage (SH2a, stonehenge_stages.js): the five stages of Darvill et al. 2012 on a slider.
// URL state: ?view=now|built|stages&stage=1-5&aubrey=stones|posts|empty&y=&m=&d=&t=<minutes>&cam=<preset>.
import * as THREE from "./vendor/three/three.module.min.js";
import { OrbitControls } from "./vendor/three/OrbitControls.js";
import { createScene } from "./stonehenge_scene.js";
import { stoneMesh, label, material } from "./stonehenge_stones.js";
import { pieces, stageWorld, AUBREY } from "./stonehenge_stages.js";
import { $, esc, toward, BASE, createClock, wirePanel, startMoment, readout, tick, starNames } from "./model_clock.js";

const [data, raw] = await Promise.all([fetch(BASE + "stonehenge.json").then((r) => r.json()),
  fetch(BASE + "stonehenge_dtm.bin").then((r) => r.arrayBuffer())]);
const LAT = data.origin.lat, LON = data.origin.lon;
const canvas = $("#sh_canvas");
const W = createScene(canvas, data, raw);
const { scene, camera, renderer, height, height0 } = W;
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

// ---- clock ----
const clock = createClock(LAT, LON, data.horizon);
const { st, today } = clock;

// ---- stages (built when first shown, on the stage's own ground) ----
const STAGES = data.stages.stages;
st.stage = Math.min(STAGES.length, Math.max(1, +(clock.q.get("stage") || 1)));
st.aubrey = AUBREY[clock.q.get("aubrey")] ? clock.q.get("aubrey") : "stones";
const built = {};
let shaped = null;
function stageModel() {
  const s = STAGES[st.stage - 1], key = `${s.id}-${s.extra.some((e) => e.kind === "aubrey") ? st.aubrey : ""}`;
  if (shaped !== key) {
    const w = built[key]?.world ?? stageWorld(s, data.stages, height0, st.aubrey);
    W.reshape(w.ground, w.surface);
    shaped = key;
    if (!built[key]) {
      const m = model(pieces(s, data.built, st.aubrey), true);
      m.g.add(w.group);
      scene.add(m.g);
      built[key] = { ...m, world: w };
    }
  }
  return built[key];
}
function showStageText() {
  const s = STAGES[st.stage - 1];
  $("#sh_stage_text").innerHTML = `<b>${esc(s.name)}</b>, ${esc(s.dates)}. ${esc(s.what)}
    ${s.cites.length ? `<details><summary>Sources</summary><ul class="sh-cites">${s.cites.map((c) => `<li>“${esc(c.quote)}” <a href="${esc(c.url)}" target="_blank" rel="noopener">${esc(c.title)}</a></li>`).join("")}</ul></details>` : ""}`;
  $("#sh_aubrey").hidden = !s.extra.some((e) => e.kind === "aubrey");
}

const EVENTS = ["summer_rise", "winter_set", "winter_rise", "equinox_rise", "winter_moon", "summer_moon"];

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
const FOR = { summer_rise: "centre_ne", winter_moon: "centre_ne", winter_set: "centre_sw" };   // event → view

// ---- drawing ----
const placeNames = starNames(W, data.stars, camera, canvas);
let P = null;
function update() {
  P = clock.at();
  W.setSky(P, data.stars);
  const stage = st.view === "stages" ? stageModel() : null;
  if (!stage && shaped) { W.reshape(null); shaped = null; }
  Object.values(built).forEach((b) => { b.g.visible = b === stage; b.labels.visible = st.labels; });
  NOW.g.visible = st.view === "now"; BUILT.g.visible = st.view === "built";
  NOW.labels.visible = BUILT.labels.visible = st.labels;
  for (const g of [BUILT.g, ...Object.values(built).map((b) => b.g)])
    g.children.forEach((m) => { if (m.userData.pale) m.material = st.ghosts ? m.userData.pale : m.userData.plain; });
  $("#sh_stagebox").hidden = st.view !== "stages";
  clock.extra = st.view === "stages" ? { stage: st.stage, aubrey: st.aubrey } : {};
  axis.visible = st.axis;
  readout(clock, P);
}

let last = performance.now();
function frame(now) {
  const dt = Math.min(0.1, (now - last) / 1000);
  last = now;
  if (tick(clock, dt)) update();
  controls.update();
  const g = (height(camera.position.x, -camera.position.z) ?? 0) + 0.4;
  if (camera.position.y < g) camera.position.y = g;
  renderer.render(scene, camera);
  placeNames(P, st.names);
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
  const group = st.view === "now" ? NOW.g : st.view === "built" ? BUILT.g : stageModel().g;
  const hit = ray.intersectObject(group, true).find((h) => h.object.isMesh && h.object.visible && h.object.userData.group);
  showStone(hit ? hit.object.userData : null);
});
const STATUS = { surviving: "Survives, in place", placed: "Survives, shown where it stood", restored: "Lost: drawn where it is thought to have stood" };
function showStone(u) {
  const box = $("#sh_stone");
  if (!u) { box.hidden = true; return; }
  const rec = data.stones[u.id] || {};
  const HOLES = { aubrey_hole: "Aubrey Hole", aubrey_post: "Aubrey Hole (with a post)", aubrey_bluestone: "Aubrey Hole (with a bluestone)", yz_hole: "Pit" };
  const name = HOLES[u.group] ? `${HOLES[u.group]} ${esc((u.id || "").replace(/^AH/, ""))}` : u.id ? `Stone ${esc(u.id)}` : "Bluestone";
  box.hidden = false;
  box.innerHTML = `<button type="button" class="sh-close" aria-label="Close">×</button><h3>${name}</h3>
    <p class="meta">${esc((u.group || rec.group || "").replace(/_/g, " "))}${st.view !== "now" && u.status ? ` · ${esc(STATUS[u.status])}` : rec.state ? ` · today: ${esc(rec.state)}` : ""}</p>
    ${rec.notes ? `<p>${esc(rec.notes)}</p>` : ""}
    ${(rec.cites || []).length ? `<ul class="sh-cites">${rec.cites.map((c) => `<li>“${esc(c.quote)}” <a href="${esc(c.url)}" target="_blank" rel="noopener">${esc(c.title)}</a></li>`).join("")}</ul>` : ""}`;
  box.querySelector(".sh-close").onclick = () => { box.hidden = true; };
}

// ---- controls ----
wirePanel(clock, { update, events: EVENTS, views: VIEWS,
  face: (k) => { if (FOR[k]) { $("#sh_cams").value = FOR[k]; VIEWS[FOR[k]][1](); } } });
$("#sh_aubrey").innerHTML = Object.entries(AUBREY).map(([k, v]) => `<option value="${k}">Aubrey Holes: ${v}</option>`).join("");
$("#sh_aubrey").value = st.aubrey;
$("#sh_stage").value = st.stage;
$("#sh_stage").addEventListener("input", (e) => { st.stage = +e.target.value; st.y = STAGES[st.stage - 1].year; showStageText(); update(); });
$("#sh_aubrey").addEventListener("change", (e) => { st.aubrey = e.target.value; update(); });
showStageText();
document.querySelectorAll("[name=sh_view]").forEach((r) => r.addEventListener("change", () => {
  if (st.view === "stages") st.y = STAGES[st.stage - 1].year;
  if (st.view === "built" && st.y > 0) st.y = -2499;
  if (st.view === "now" && st.y <= 0) st.y = today.getUTCFullYear();
  update();
}));
$("#sh_credits").innerHTML = data.credits.map((c) => `<li>${esc(c)}</li>`).join("")
  + `<li>Plan placed on the ground by fitting it to ${data.origin.fit.pairs} stones mapped on OpenStreetMap (shift only, keeping the plan's north; ${data.origin.fit.rms_m} m root mean square).</li>`;
$("#sh_debate").innerHTML = (data.debate || []).map((d) => `<li>${esc(d.claim)} ${(d.cites || []).map((c) => `<span class="meta">“${esc(c.quote)}”</span>`).join(" ")}</li>`).join("");

window.addEventListener("resize", W.resize);
W.resize();
// With no moment in the link, open on a midsummer morning this year (the stones in sunlight) rather than
// whatever the present hour is, perhaps the dark.
startMoment(clock, { event: "summer_rise", t: 600 },
  "Midsummer morning this year. Press “Midsummer sunrise” for the sun over the Heel Stone, or “Now” for the sky at this moment.");
update();
document.body.classList.add("sh-ready");
requestAnimationFrame(frame);
window.SH = { st, update, scene, camera, controls, data };   // for checks
