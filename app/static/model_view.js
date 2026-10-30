// Page /model/<id> (loaded by stonehenge_page.js when WebGL works): a 3D model built from its data file
// `static/data/model_<id>.json` (bidb.models3d) and ground grid, under the sky of any date and time (clock, panel and
// events from model_clock.js, world from stonehenge_scene.js, parts from model_parts.js). Click a part for its
// record and sources. URL state as /stonehenge: ?view=now|built&y=&m=&d=&t=<minutes>&cam=<preset>.
import * as THREE from "./vendor/three/three.module.min.js";
import { OrbitControls } from "./vendor/three/OrbitControls.js";
import { createScene } from "./stonehenge_scene.js";
import { buildParts } from "./model_parts.js";
import "./model_broch.js";
import { $, esc, toward, BASE, createClock, wirePanel, startMoment, readout, tick, starNames } from "./model_clock.js";

const ID = $("#sh_canvas").dataset.model;
const [data, raw] = await Promise.all([fetch(`${BASE}model_${ID}.json`).then((r) => r.json()),
  fetch(`${BASE}model_${ID}_dtm.bin`).then((r) => r.arrayBuffer())]);
const LAT = data.origin.lat, LON = data.origin.lon;
const canvas = $("#sh_canvas");
const W = createScene(canvas, data, raw);
const { scene, camera, renderer, height } = W;
const controls = new OrbitControls(camera, canvas);
controls.enableDamping = true;
controls.maxPolarAngle = Math.PI * 0.97;
controls.minDistance = 0.02;
controls.maxDistance = 1800;

const NOW = buildParts(data.views.now, height);
const BUILT = data.views.built ? buildParts(data.views.built, height) : null;
scene.add(NOW.group);
if (BUILT) scene.add(BUILT.group);
const axis = new THREE.Group();
(data.axis ?? []).forEach((az) => {
  const pts = [];
  for (let r = 0; r <= (data.axis_length ?? 120); r += 1) { const [x, y] = toward(az, r); pts.push(new THREE.Vector3(x, (height(x, y) ?? 0) + 0.08, -y)); }
  axis.add(new THREE.Line(new THREE.BufferGeometry().setFromPoints(pts), new THREE.LineBasicMaterial({ color: 0xffcc33 })));
});
scene.add(axis);
// The lantern: a warm light carried with the camera, for looking round a dark chamber.
const lantern = new THREE.PointLight(0xffc98a, 0, 14, 1.6);
camera.add(lantern);
scene.add(camera);

const clock = createClock(LAT, LON, data.horizon);
const { st } = clock;

// Camera at `from` looking at `to` ([x, y(north), height above the ground?]); standing: turns on the spot.
const eye = (x, y) => (height(x, y) ?? 0) + 1.6;
function look(from, to, fov = 50, standing = false) {
  camera.position.set(from[0], from[2] != null ? (height(from[0], from[1]) ?? 0) + from[2] : eye(from[0], from[1]), -from[1]);
  const t = new THREE.Vector3(to[0], to[2] != null ? (height(to[0], to[1]) ?? 0) + to[2] : eye(to[0], to[1]), -to[1]);
  if (standing) t.sub(camera.position).normalize().multiplyScalar(0.05).add(camera.position);
  controls.target.copy(t);
  controls.enableZoom = !standing;
  camera.fov = fov; camera.updateProjectionMatrix(); controls.update();
}
const VIEWS = Object.fromEntries(Object.entries(data.cams).map(([k, c]) => [k, [c.label, () => look(c.from, c.to, c.fov, c.standing)]]));

const placeNames = starNames(W, data.stars, camera, canvas);
let P = null;
function update() {
  P = clock.at();
  W.setSky(P, data.stars);
  NOW.group.visible = st.view === "now" || !BUILT;
  if (BUILT) BUILT.group.visible = st.view === "built";
  NOW.labels.visible = st.labels;
  if (BUILT) {
    BUILT.labels.visible = st.labels;
    BUILT.group.traverse((m) => { if (m.userData?.pale) m.material = st.ghosts ? m.userData.pale : m.userData.plain; });
  }
  axis.visible = st.axis;
  lantern.intensity = st.lantern ? 6 : 0;
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

// ---- part records ----
const ray = new THREE.Raycaster(), ptr = new THREE.Vector2();
let down = null;
canvas.addEventListener("pointerdown", (e) => { down = [e.clientX, e.clientY]; });
canvas.addEventListener("pointerup", (e) => {
  if (!down || Math.hypot(e.clientX - down[0], e.clientY - down[1]) > 4) return;
  const r = canvas.getBoundingClientRect();
  ptr.set((e.clientX - r.left) / r.width * 2 - 1, -(e.clientY - r.top) / r.height * 2 + 1);
  ray.setFromCamera(ptr, camera);
  const grp = st.view === "built" && BUILT ? BUILT.group : NOW.group;
  const hit = ray.intersectObject(grp, true).find((h) => h.object.isMesh && h.object.visible && h.object.userData.info?.title);
  showPart(hit ? hit.object.userData.info : null);
});
const STATUS = { surviving: "Survives", restored: "Lost: drawn where it is thought to have been", reconstructed: "Modern reconstruction" };
function showPart(u) {
  const box = $("#sh_stone");
  if (!u) { box.hidden = true; return; }
  box.hidden = false;
  box.innerHTML = `<button type="button" class="sh-close" aria-label="Close">×</button><h3>${esc(u.title)}</h3>
    ${u.status ? `<p class="meta">${esc(STATUS[u.status] ?? u.status)}</p>` : ""}${u.note ? `<p>${esc(u.note)}</p>` : ""}
    ${(u.cites || []).length ? `<ul class="sh-cites">${u.cites.map((c) => `<li>“${esc(c.quote)}” <a href="${esc(c.url)}" target="_blank" rel="noopener">${esc(c.title)}</a></li>`).join("")}</ul>` : ""}`;
  box.querySelector(".sh-close").onclick = () => { box.hidden = true; };
}

// ---- controls ----
wirePanel(clock, { update, events: data.events, views: VIEWS,
  face: (k) => { const v = data.face?.[k]; if (v && VIEWS[v]) { $("#sh_cams").value = v; VIEWS[v][1](); } } });
if (BUILT && data.built_year != null) document.querySelectorAll("[name=sh_view]").forEach((r) => r.addEventListener("change", () => {
  if (st.view === "built" && st.y > 0) st.y = data.built_year;
  if (st.view === "now" && st.y <= 0) st.y = clock.today.getUTCFullYear();
  update();
}));
$("#sh_credits").innerHTML = data.credits.map((c) => `<li>${esc(c)}</li>`).join("");
$("#sh_facts").innerHTML = (data.facts ?? []).map((f) => `<li>${esc(f.text)} ${(f.cites || []).map((c) =>
  `<span class="meta">“${esc(c.quote)}” (<a href="${esc(c.url)}" target="_blank" rel="noopener">${esc(c.title)}</a>)</span>`).join(" ")}</li>`).join("");

window.addEventListener("resize", W.resize);
W.resize();
startMoment(clock, data.start, data.start?.note);
update();
document.body.classList.add("sh-ready");
requestAnimationFrame(frame);
window.SH = { st, update, scene, camera, controls, data, THREE };   // for checks
