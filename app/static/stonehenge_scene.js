// The world of the Stonehenge model: ground from the Environment Agency's 1 m LiDAR (written at 2 m by
// bidb.stonehenge), the land beyond drawn so its edge stands where the real skyline does (bidb.sky_horizon profile),
// the sky (three.js Sky: Rayleigh and Mie scattering), the sun and moon (phase lit from the sun) as lights with
// shadows, and the bright stars (BSC5) placed by SkyPos for the date. Model metres: x east, y up, z south.
import * as THREE from "./vendor/three/three.module.min.js";
import { Sky } from "./vendor/three/Sky.js";
import { noise3 } from "./stonehenge_stones.js";

const R = Math.PI / 180, DOME = 7000, EYE = 1.6;
export const dir = (alt, az) => new THREE.Vector3(Math.cos(alt * R) * Math.sin(az * R), Math.sin(alt * R), -Math.cos(alt * R) * Math.cos(az * R));

// Ground heights: bilinear in the LiDAR grid, metres above the ground at the centre; null outside it.
export function heightField(dtm, raw) {
  const n = dtm.n, v = new Uint16Array(raw);
  const at = (i, j) => dtm.min + v[i * n + j] * dtm.scale - dtm.ground;
  return (x, y) => {
    const fj = (x - dtm.x0) / dtm.step, fi = (dtm.y0 - y) / dtm.step;
    if (fi < 0 || fj < 0 || fi >= n - 1 || fj >= n - 1) return null;
    const i = Math.floor(fi), j = Math.floor(fj), a = fi - i, b = fj - j;
    return at(i, j) * (1 - a) * (1 - b) + at(i, j + 1) * (1 - a) * b + at(i + 1, j) * a * (1 - b) + at(i + 1, j + 1) * a * b;
  };
}

export function grassTexture() {
  const s = 512, c = document.createElement("canvas");
  c.width = c.height = s;
  const g = c.getContext("2d"), img = g.createImageData(s, s);
  for (let y = 0; y < s; y++) for (let x = 0; x < s; x++) {
    const u = x / s * 16, v = y / s * 16;
    const n = 0.5 * noise3(u, v, 0.3, 41) + 0.3 * noise3(u * 3, v * 3, 1.1, 42) + 0.2 * noise3(u * 11, v * 11, 2.3, 43);
    const o = (y * s + x) * 4;
    img.data[o] = 104 + 34 * n; img.data[o + 1] = 128 + 30 * n; img.data[o + 2] = 64 + 14 * n; img.data[o + 3] = 255;
  }
  g.putImageData(img, 0, 0);
  const t = new THREE.CanvasTexture(c);
  t.wrapS = t.wrapT = THREE.RepeatWrapping;
  t.colorSpace = THREE.SRGBColorSpace;
  t.anisotropy = 8;
  return t;
}

// The LiDAR ground, cut to a disc of radius `rad` (the land beyond takes over there).
function ground(dtm, height, rad) {
  const n = dtm.n, pos = [], uv = [], idx = [];
  for (let i = 0; i < n; i++) for (let j = 0; j < n; j++) {
    const x = dtm.x0 + j * dtm.step, y = dtm.y0 - i * dtm.step;
    pos.push(x, height(Math.min(x, dtm.x0 + (n - 1.01) * dtm.step), Math.max(y, dtm.y0 - (n - 1.01) * dtm.step)) ?? 0, -y);
    uv.push(x / 9, y / 9);
  }
  for (let i = 0; i < n - 1; i++) for (let j = 0; j < n - 1; j++) {
    const x = dtm.x0 + (j + 0.5) * dtm.step, y = dtm.y0 - (i + 0.5) * dtm.step;
    if (x * x + y * y > rad * rad) continue;
    const a = i * n + j, b = a + 1, c = a + n, d = c + 1;
    idx.push(a, c, b, b, c, d);
  }
  const geo = new THREE.BufferGeometry();
  geo.setAttribute("position", new THREE.Float32BufferAttribute(pos, 3));
  geo.setAttribute("uv", new THREE.Float32BufferAttribute(uv, 2));
  geo.setIndex(idx);
  geo.computeVertexNormals();
  const mesh = new THREE.Mesh(geo, new THREE.MeshStandardMaterial({ map: grassTexture(), roughness: 1, color: 0xffffff }));
  mesh.receiveShadow = true;
  return mesh;
}

// Land from the edge of the LiDAR out to `far` m, rising so that its far edge stands at the skyline's altitude as
// seen from eye height at the centre (the profile already allows for the earth's curve and refraction).
function land(hz, height, inner, far = 5200) {
  const step = hz.step, m = hz.alt.length;
  far = Math.max(far, inner * 2);                                     // rings outward from wherever the ground grid ends
  const radii = [inner, ...[600, 900, 1400, 2200, 3400].filter((r) => r > inner + 100).map((r) => r * far / 5200), far];
  const pos = [], col = [], idx = [];
  const near = new THREE.Color(0x5d7040), farC = new THREE.Color(0x6f7a68);
  for (let k = 0; k < radii.length; k++) for (let a = 0; a < m; a++) {
    const az = a * step, r = radii[k], alt = hz.alt[a] / 100;
    const edge = height(r * Math.sin(az * R) * 0.999, r * Math.cos(az * R) * 0.999) ?? 0;
    const sky = EYE + r * Math.tan(alt * R);
    const t = Math.min(1, Math.max(0, (r - inner) / 1600));
    const y = k === 0 ? edge : edge * (1 - t * t * (3 - 2 * t)) + sky * (t * t * (3 - 2 * t));
    pos.push(r * Math.sin(az * R), y - (k === 0 ? 0.05 : 0), -r * Math.cos(az * R));
    const c = near.clone().lerp(farC, Math.min(1, k / (radii.length - 1)));
    const shade = 0.85 + 0.15 * noise3(az / 9, k, 0.5, 77);
    col.push(c.r * shade, c.g * shade, c.b * shade);
  }
  for (let k = 0; k < radii.length - 1; k++) for (let a = 0; a < m; a++) {
    const p = k * m + a, q = k * m + (a + 1) % m, s = p + m, t = q + m;
    idx.push(p, s, q, q, s, t);
  }
  const geo = new THREE.BufferGeometry();
  geo.setAttribute("position", new THREE.Float32BufferAttribute(pos, 3));
  geo.setAttribute("color", new THREE.Float32BufferAttribute(col, 3));
  geo.setIndex(idx);
  geo.computeVertexNormals();
  const mesh = new THREE.Mesh(geo, new THREE.MeshStandardMaterial({ vertexColors: true, roughness: 1 }));
  mesh.receiveShadow = true;
  return mesh;
}

// B-V colour index → star colour.
function starColour(bv) {
  const t = Math.max(-0.4, Math.min(2, bv));
  const c = new THREE.Color();
  if (t < 0) c.setRGB(0.7, 0.8, 1); else if (t < 0.4) c.setRGB(0.85 + 0.15 * t / 0.4, 0.9, 1 - 0.1 * t / 0.4);
  else if (t < 1) c.setRGB(1, 0.92 - 0.12 * (t - 0.4) / 0.6, 0.85 - 0.25 * (t - 0.4) / 0.6); else c.setRGB(1, 0.75, 0.55);
  return c;
}

function stars(rows) {
  const geo = new THREE.BufferGeometry(), n = rows.length;
  const col = [], size = [];
  rows.forEach((s) => { const c = starColour(s[5]); col.push(c.r, c.g, c.b); size.push(Math.max(1.5, 7.4 - 1.15 * s[4])); });
  geo.setAttribute("position", new THREE.Float32BufferAttribute(new Float32Array(n * 3), 3));
  geo.setAttribute("color", new THREE.Float32BufferAttribute(col, 3));
  geo.setAttribute("size", new THREE.Float32BufferAttribute(size, 1));
  const mat = new THREE.ShaderMaterial({
    uniforms: { opacity: { value: 1 }, scale: { value: 1 } }, transparent: true, depthWrite: false,
    blending: THREE.AdditiveBlending, vertexColors: true,
    vertexShader: `attribute float size; varying vec3 vCol; varying float vAlt; uniform float scale;
      void main() { vCol = color; vAlt = normalize(position).y; vec4 mv = modelViewMatrix * vec4(position, 1.0);
        gl_PointSize = size * scale; gl_Position = projectionMatrix * mv; }`,
    fragmentShader: `varying vec3 vCol; varying float vAlt; uniform float opacity;
      void main() { float d = length(gl_PointCoord - 0.5); float a = smoothstep(0.5, 0.0, d);
        float ext = smoothstep(-0.01, 0.12, vAlt); gl_FragColor = vec4(vCol, a * opacity * ext); }`,
  });
  const pts = new THREE.Points(geo, mat);
  pts.frustumCulled = false;
  pts.renderOrder = 1;
  return pts;
}

function moonMesh() {
  const r = DOME * Math.tan(0.259 * R) * 1.6;               // a little larger than life, as the eye sees it
  const mat = new THREE.ShaderMaterial({
    uniforms: { sunDir: { value: new THREE.Vector3(0, 1, 0) }, glow: { value: 1 } }, transparent: true,
    vertexShader: `varying vec3 vN; varying vec3 vP; void main() { vN = normalize(mat3(modelMatrix) * normal);
      vP = position; gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0); }`,
    fragmentShader: `uniform vec3 sunDir; uniform float glow; varying vec3 vN; varying vec3 vP;
      float h(vec2 p) { return fract(sin(dot(p, vec2(12.9898, 78.233))) * 43758.5453); }
      void main() { float lit = smoothstep(-0.03, 0.08, dot(normalize(vN), normalize(sunDir)));
        vec2 q = normalize(vP).xy * 3.0; float maria = 0.82 + 0.18 * smoothstep(0.2, 0.8, h(floor(q * 2.0)));
        vec3 c = vec3(0.96, 0.95, 0.9) * maria * lit;
        float a = max(lit, 0.06 * (glow - 0.6));      // the dark side shows only at night (earthshine)
        gl_FragColor = vec4(c * glow + vec3(0.05, 0.06, 0.09) * (1.0 - lit) * (glow - 0.6), a); }`,
  });
  const m = new THREE.Mesh(new THREE.SphereGeometry(r, 48, 24), mat);
  m.renderOrder = 2;
  return m;
}

// A soft glow round the sun's disc (the sky shader's own disc is half a degree, a few pixels).
function sunGlow() {
  const c = document.createElement("canvas");
  c.width = c.height = 128;
  const g = c.getContext("2d"), grad = g.createRadialGradient(64, 64, 0, 64, 64, 64);
  grad.addColorStop(0, "rgba(255,250,235,1)"); grad.addColorStop(0.08, "rgba(255,240,200,0.95)");
  grad.addColorStop(0.25, "rgba(255,210,150,0.35)"); grad.addColorStop(1, "rgba(255,180,120,0)");
  g.fillStyle = grad; g.fillRect(0, 0, 128, 128);
  const sp = new THREE.Sprite(new THREE.SpriteMaterial({ map: new THREE.CanvasTexture(c), blending: THREE.AdditiveBlending,
    depthWrite: false, transparent: true, fog: false }));
  const size = 2 * DOME * Math.tan(3 * R);
  sp.scale.set(size, size, 1);
  sp.renderOrder = 3;
  return sp;
}

export function createScene(canvas, data, dtmRaw) {
  const renderer = new THREE.WebGLRenderer({ canvas, antialias: true });
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
  renderer.shadowMap.enabled = true;
  renderer.shadowMap.type = THREE.PCFSoftShadowMap;
  renderer.toneMapping = THREE.ACESFilmicToneMapping;
  renderer.outputColorSpace = THREE.SRGBColorSpace;
  const scene = new THREE.Scene();
  const camera = new THREE.PerspectiveCamera(50, 1, 0.2, 30000);
  const height = heightField(data.dtm, dtmRaw);
  const rad = (data.dtm.n - 2) * data.dtm.step / 2;
  scene.add(ground(data.dtm, height, rad), land(data.horizon, height, rad - 1));

  const sky = new Sky();
  sky.scale.setScalar(20000);
  const su = sky.material.uniforms;
  su.turbidity.value = 2.2; su.rayleigh.value = 1.6; su.mieCoefficient.value = 0.004; su.mieDirectionalG.value = 0.8;
  scene.add(sky);
  // Night: a dark dome inside the sky faded in as the sun goes down (the scattering sky alone stays grey-violet).
  const night = new THREE.Mesh(new THREE.SphereGeometry(9000, 32, 16), new THREE.MeshBasicMaterial({
    color: 0x05070f, side: THREE.BackSide, transparent: true, depthWrite: false, fog: false }));
  night.renderOrder = 0.5;
  scene.add(night);
  const starPts = stars(data.stars);
  scene.add(starPts);
  const moon = moonMesh();
  scene.add(moon);
  const glow = sunGlow();
  scene.add(glow);

  // Shadows are sharp within `half` metres of the model's focus (data.shadow: {half, centre: [x, y]}): small for a
  // passage tomb, so a narrow sunbeam down its passage is drawn crisply.
  const half = data.shadow?.half ?? 95, fc = data.shadow?.centre ?? [0, 0];
  const focus = new THREE.Vector3(fc[0], height(fc[0], fc[1]) ?? 0, -fc[1]);
  const sunLight = new THREE.DirectionalLight(0xffffff, 3);
  const moonLight = new THREE.DirectionalLight(0xb8c8ff, 0.3);
  for (const l of [sunLight, moonLight]) {
    l.castShadow = true;
    l.shadow.mapSize.set(l === sunLight ? 4096 : 2048, l === sunLight ? 4096 : 2048);
    Object.assign(l.shadow.camera, { left: -half, right: half, top: half, bottom: -half, near: 1, far: 800 });
    l.shadow.bias = -0.0004; l.shadow.normalBias = half < 60 ? 0.02 : 0.04;
    l.target.position.copy(focus);
    scene.add(l, l.target);
  }
  const hemi = new THREE.HemisphereLight(0xbfd4ff, 0x4a5a32, 0.5);
  scene.add(hemi);
  scene.fog = new THREE.Fog(0xb9c6d2, 900, 9000);

  // Place sun, moon and stars for SkyPos.at(...) output `p` and the star list.
  function setSky(p, starRows) {
    const s = p.sun, m = p.moon;
    const sd = dir(s.seen, s.az), md = dir(m.seen, m.az);            // where they are seen: refraction lifts them near the horizon
    su.sunPosition.value.copy(sd);
    const day = THREE.MathUtils.smoothstep(s.seen, -4, 6);
    const low = 1 - THREE.MathUtils.smoothstep(s.seen, 2, 25);
    sunLight.position.copy(sd).multiplyScalar(400).add(focus);
    sunLight.intensity = 3.2 * THREE.MathUtils.smoothstep(s.seen, -0.8, 1.5);   // near full strength a degree up
    sunLight.color.setRGB(1, 0.92 - 0.25 * low, 0.85 - 0.45 * low);
    sunLight.castShadow = s.seen > -1;
    const moonUp = THREE.MathUtils.smoothstep(m.seen, -1, 3);
    moonLight.position.copy(md).multiplyScalar(400).add(focus);
    moonLight.intensity = 0.55 * m.phase * moonUp * (1 - day);
    moonLight.castShadow = moonLight.intensity > 0.03;
    hemi.intensity = 0.14 + 0.5 * day + 0.08 * m.phase * moonUp;   // starlight and sky glow on moonless nights
    hemi.color.setRGB(0.55 + 0.2 * day, 0.62 + 0.2 * day, 0.85);
    renderer.toneMappingExposure = 0.35 + 0.25 * day + 0.6 * (1 - day);
    const fogC = new THREE.Color().setRGB(0.02 + 0.68 * day + 0.2 * low * day, 0.03 + 0.7 * day + 0.05 * low * day, 0.06 + 0.72 * day - 0.15 * low * day);
    scene.fog.color.copy(fogC);
    moon.position.copy(md).multiplyScalar(DOME);
    moon.lookAt(0, 0, 0);
    moon.material.uniforms.sunDir.value.copy(sd);
    moon.material.uniforms.glow.value = 0.6 + 0.9 * (1 - day);
    moon.visible = m.seen > -2;
    glow.position.copy(sd).multiplyScalar(DOME * 0.98);
    glow.visible = s.seen > -1.5;
    glow.material.opacity = 0.35 + 0.65 * low;
    night.material.opacity = 1 - THREE.MathUtils.smoothstep(s.seen, -14, -3);
    night.visible = night.material.opacity > 0.01;
    starPts.material.uniforms.opacity.value = 1 - THREE.MathUtils.smoothstep(s.seen, -16, -5);
    starPts.visible = s.seen < -4;
    if (starPts.visible) {
      const a = starPts.geometry.attributes.position;
      starRows.forEach((row, i) => { const h = SkyPos.star(row, p.jde, data.origin.lat, p.lst); const v = dir(h.alt + SkyPos.refraction(h.alt), h.az).multiplyScalar(DOME); a.setXYZ(i, v.x, v.y, v.z); });
      a.needsUpdate = true;
    }
  }

  function resize() {
    const w = canvas.clientWidth, h = canvas.clientHeight;
    renderer.setSize(w, h, false);
    camera.aspect = w / h;
    camera.updateProjectionMatrix();
    starPts.material.uniforms.scale.value = renderer.getPixelRatio() * Math.max(0.8, h / 900);
  }
  return { renderer, scene, camera, height, setSky, resize, starPts, hemi };
}
