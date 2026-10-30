// Stones of the Stonehenge model (/stonehenge): a mesh per stone from its plan outline (model metres, x east, y north;
// static/data/stonehenge.json from bidb.stonehenge), raised to its height, edges rounded, the faces roughened with
// noise and slightly tapered; curved lintels of the complete circle from their arc; procedural textures for sarsen
// (grey-buff with lichen), bluestone (spotted blue-grey dolerite) and the Altar Stone's green-grey sandstone.
import * as THREE from "./vendor/three/three.module.min.js";

// Value noise, seeded, smooth (3-D, for displacing the stone surfaces and painting textures).
function hash(x, y, z, s) {
  let h = (x * 374761393 + y * 668265263 + z * 2147483647 + s * 1274126177) | 0;
  h = Math.imul(h ^ (h >>> 13), 1274126177);
  return ((h ^ (h >>> 16)) >>> 0) / 4294967295;
}
export function noise3(x, y, z, s = 0) {
  const xi = Math.floor(x), yi = Math.floor(y), zi = Math.floor(z);
  const f = (t) => t * t * (3 - 2 * t);
  const u = f(x - xi), v = f(y - yi), w = f(z - zi);
  let out = 0;
  for (let dx = 0; dx < 2; dx++) for (let dy = 0; dy < 2; dy++) for (let dz = 0; dz < 2; dz++) {
    out += hash(xi + dx, yi + dy, zi + dz, s) * (dx ? u : 1 - u) * (dy ? v : 1 - v) * (dz ? w : 1 - w);
  }
  return out * 2 - 1;
}
const fbm = (x, y, z, s, oct = 4) => { let a = 0, amp = 0.5, f = 1; for (let i = 0; i < oct; i++) { a += amp * noise3(x * f, y * f, z * f, s + i); amp /= 2; f *= 2.1; } return a; };

const PALETTES = {
  sarsen: { base: [150, 143, 128], dark: [96, 92, 84], patches: [[176, 172, 120], [190, 192, 176], [170, 120, 70]] },
  bluestone: { base: [92, 98, 108], dark: [60, 64, 72], patches: [[150, 156, 160], [120, 126, 118], [168, 168, 150]] },
  sandstone: { base: [128, 130, 112], dark: [92, 96, 84], patches: [[160, 160, 140], [140, 150, 120], [150, 140, 110]] },
  // Rocks of the other models (model_parts.js): Lewisian gneiss, greywacke, granite, quartz, Orkney flagstone,
  // schist, oak timber, the rubble of a cairn, and modern concrete markers.
  gneiss: { base: [150, 148, 142], dark: [88, 86, 84], patches: [[200, 198, 190], [120, 118, 126], [176, 168, 120]] },
  greywacke: { base: [104, 108, 100], dark: [66, 70, 64], patches: [[140, 146, 132], [120, 126, 110], [160, 150, 110]] },
  granite: { base: [150, 146, 140], dark: [100, 96, 92], patches: [[190, 186, 180], [130, 120, 116], [170, 160, 140]] },
  quartz: { base: [226, 226, 220], dark: [176, 176, 170], patches: [[240, 240, 236], [200, 200, 196], [214, 210, 196]] },
  flagstone: { base: [112, 106, 98], dark: [70, 66, 62], patches: [[140, 134, 124], [120, 116, 104], [168, 150, 110]] },
  schist: { base: [122, 124, 118], dark: [80, 82, 78], patches: [[160, 162, 150], [140, 136, 112], [176, 160, 120]] },
  timber: { base: [128, 100, 72], dark: [84, 62, 44], patches: [[150, 120, 88], [110, 86, 60], [140, 116, 84]] },
  cairn: { base: [130, 128, 120], dark: [76, 74, 70], patches: [[170, 168, 160], [110, 108, 100], [150, 146, 120]] },
  concrete: { base: [190, 188, 182], dark: [150, 148, 142], patches: [[205, 203, 198], [175, 172, 166], [185, 180, 170]] },
};
function rockCanvas(kind, size = 512) {
  const p = PALETTES[kind], c = document.createElement("canvas");
  c.width = c.height = size;
  const g = c.getContext("2d"), img = g.createImageData(size, size), bump = g.createImageData(size, size);
  for (let y = 0; y < size; y++) for (let x = 0; x < size; x++) {
    const u = x / size * 8, v = y / size * 8;                       // tiles: noise periodic over 8 units
    const n = fbm(u, v, 0.5, 3, 5), grain = noise3(u * 9, v * 9, 1.7, 9);
    let col = p.base.map((b, i) => b + (p.dark[i] - b) * Math.max(0, n) * 1.2 + grain * 10);
    p.patches.forEach((pc, k) => {
      const m = fbm(u * 1.6 + k * 13, v * 1.6, 2 + k, 20 + k, 3);
      const t = Math.max(0, Math.min(1, (m - (k === 2 ? 0.32 : 0.12)) * 6));   // lichen patches (orange rarer)
      col = col.map((cv, i) => cv + (pc[i] - cv) * t * 0.55);
    });
    if (kind === "bluestone") { const spot = noise3(u * 22, v * 22, 3, 31); if (spot > 0.55) col = col.map((cv) => cv + 45); }
    const o = (y * size + x) * 4;
    for (let i = 0; i < 3; i++) img.data[o + i] = Math.max(0, Math.min(255, col[i]));
    img.data[o + 3] = 255;
    const b = 128 + 90 * n + 30 * grain;
    bump.data[o] = bump.data[o + 1] = bump.data[o + 2] = b; bump.data[o + 3] = 255;
  }
  g.putImageData(img, 0, 0);
  const b = document.createElement("canvas");
  b.width = b.height = size;
  b.getContext("2d").putImageData(bump, 0, 0);
  return [c, b];
}

const MATERIALS = {};
export function material(kind, restored = false) {
  const key = kind + (restored ? "-r" : "");
  if (MATERIALS[key]) return MATERIALS[key];
  if (!MATERIALS[kind + "-tex"]) {
    const [c, b] = rockCanvas(kind);
    const tex = (cv, srgb) => {
      const t = new THREE.CanvasTexture(cv);
      t.wrapS = t.wrapT = THREE.RepeatWrapping;
      t.repeat.set(0.35, 0.35);
      t.anisotropy = 8;
      if (srgb) t.colorSpace = THREE.SRGBColorSpace;
      return t;
    };
    MATERIALS[kind + "-tex"] = [tex(c, true), tex(b, false)];
  }
  const [map, bumpMap] = MATERIALS[kind + "-tex"];
  MATERIALS[key] = new THREE.MeshStandardMaterial({ map, bumpMap, bumpScale: 2.5, roughness: 0.93, metalness: 0,
    color: restored ? 0xd8dde6 : 0xffffff, transparent: restored, opacity: restored ? 0.55 : 1 });
  return MATERIALS[key];
}

// Outline helpers: rounded corners (Chaikin) and points every ~0.15 m so the sides take the roughening.
function chaikin(pts, n = 2) {
  for (let k = 0; k < n; k++) {
    const out = [];
    pts.forEach((p, i) => { const q = pts[(i + 1) % pts.length]; out.push([0.75 * p[0] + 0.25 * q[0], 0.75 * p[1] + 0.25 * q[1]], [0.25 * p[0] + 0.75 * q[0], 0.25 * p[1] + 0.75 * q[1]]); });
    pts = out;
  }
  return pts;
}
function resample(pts, step = 0.15) {
  const out = [];
  pts.forEach((p, i) => {
    const q = pts[(i + 1) % pts.length], d = Math.hypot(q[0] - p[0], q[1] - p[1]), n = Math.max(1, Math.ceil(d / step));
    for (let k = 0; k < n; k++) out.push([p[0] + (q[0] - p[0]) * k / n, p[1] + (q[1] - p[1]) * k / n]);
  });
  return out;
}
const centroid = (pts) => [pts.reduce((s, p) => s + p[0], 0) / pts.length, pts.reduce((s, p) => s + p[1], 0) / pts.length];

// Arc outline of a curved lintel: {cx, cy, r, az, span (degrees), depth}.
export function arcOutline(a, n = 14) {
  const pts = [], R = Math.PI / 180;
  for (let i = 0; i <= n; i++) { const t = (a.az - a.span / 2 + a.span * i / n) * R; pts.push([a.cx + (a.r + a.depth / 2) * Math.sin(t), a.cy + (a.r + a.depth / 2) * Math.cos(t)]); }
  for (let i = n; i >= 0; i--) { const t = (a.az - a.span / 2 + a.span * i / n) * R; pts.push([a.cx + (a.r - a.depth / 2) * Math.sin(t), a.cy + (a.r - a.depth / 2) * Math.cos(t)]); }
  return pts;
}

// One stone: outline (model metres), from `base` to `base + h` above the ground at `ground`; standing stones taper,
// fallen ones are sunk a little; `lean` = [degrees, azimuth] tilts it (the Heel Stone); `rough` scales the surface
// noise (0 for the edges of a narrow opening that light must pass, e.g. a roof-box). Returns a Mesh.
export function stoneMesh(s, ground, { restored = false, seed = 1 } = {}) {
  let pts = s.arc ? arcOutline(s.arc) : s.outline;
  if (pts.length < 3) return null;
  const c = centroid(pts);
  pts = resample(chaikin(pts.map((p) => [p[0] - c[0], p[1] - c[1]]), s.arc ? 1 : 2));
  const lying = !["standing", "leaning", "in place"].includes(s.state ?? "standing") && !s.status;
  const lintel = s.base != null;
  const h = s.h, bevel = Math.min(0.18, h * 0.2, 0.25);
  const shape = new THREE.Shape(pts.map((p) => new THREE.Vector2(p[0], p[1])));
  const geo = new THREE.ExtrudeGeometry(shape, { depth: Math.max(0.02, h - 2 * bevel), steps: Math.max(2, Math.ceil(h / 0.3)),
    bevelEnabled: true, bevelThickness: bevel, bevelSize: Math.min(bevel, 0.12), bevelSegments: 3, curveSegments: 4 });
  geo.translate(0, 0, bevel);
  geo.rotateX(-Math.PI / 2);                               // shape y (north) → -z, extrusion → up
  const pos = geo.attributes.position, v = new THREE.Vector3();
  geo.computeVertexNormals();
  const nrm = geo.attributes.normal;
  const sink = lying ? 0.2 : lintel ? 0 : 0.3;            // standing stones run on into the ground
  for (let i = 0; i < pos.count; i++) {
    v.fromBufferAttribute(pos, i);
    const t = Math.max(0, Math.min(1, v.y / h));
    if (!lying && !lintel) { const k = 1 - 0.1 * t; v.x *= k; v.z *= k; }
    const d = (s.rough ?? 1) * (0.07 * fbm(v.x * 0.9, v.y * 0.9, v.z * 0.9, seed, 3) + 0.025 * noise3(v.x * 4, v.y * 4, v.z * 4, seed + 7));
    v.x += nrm.getX(i) * d; v.y += nrm.getY(i) * d * (v.y > 0.05 ? 1 : 0); v.z += nrm.getZ(i) * d;
    if (s.lean) { const [deg, az] = s.lean, k = Math.tan(deg * Math.PI / 180) * v.y; v.x += k * Math.sin(az * Math.PI / 180); v.z -= k * Math.cos(az * Math.PI / 180); }
    pos.setXYZ(i, v.x, v.y, v.z);
  }
  geo.computeVertexNormals();
  const mesh = new THREE.Mesh(geo, material(s.kind, restored));
  mesh.position.set(c[0], ground + (lintel ? s.base : -sink), -c[1]);
  if (!lying && !lintel) mesh.scale.y = (h + sink) / h;
  mesh.castShadow = mesh.receiveShadow = true;
  mesh.userData = { id: s.id, group: s.group, status: s.status, state: s.state };
  return mesh;
}

// A label sprite (stone numbers).
export function label(text) {
  const c = document.createElement("canvas"), g = c.getContext("2d");
  c.width = 128; c.height = 64;
  g.font = "bold 40px system-ui, sans-serif"; g.textAlign = "center"; g.textBaseline = "middle";
  g.lineWidth = 6; g.strokeStyle = "rgba(0,0,0,0.75)"; g.strokeText(text, 64, 32); g.fillStyle = "#fff"; g.fillText(text, 64, 32);
  const t = new THREE.CanvasTexture(c);
  t.colorSpace = THREE.SRGBColorSpace;
  const sp = new THREE.Sprite(new THREE.SpriteMaterial({ map: t, depthTest: false, transparent: true }));
  sp.scale.set(1.6, 0.8, 1);
  sp.renderOrder = 10;
  return sp;
}
