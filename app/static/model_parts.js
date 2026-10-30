// Parts of the 3D models (/model/<id>), built from the model's data file (bidb.models3d): stones and slabs, mounds
// with a kerb drum and openings, passages (orthostats, capstones, floor, and a liner behind them), chambers
// (orthostats, a capstone or a corbelled roof), timber posts and banks. Model metres: x east, y north; heights of a
// part are above the ground under it (`height(x, y)`, metres above the ground at the origin). Surfaces inside a
// passage or chamber take no light from the sky (an ambient-occlusion map of 30%), only direct sun or moon light
// coming in through the openings, and the lantern.
import * as THREE from "./vendor/three/three.module.min.js";
import { grassTexture } from "./stonehenge_scene.js";
import { stoneMesh, material, label } from "./stonehenge_stones.js";

const R = Math.PI / 180;
const AO = (() => { const t = new THREE.DataTexture(new Uint8Array([76, 76, 76, 255]), 1, 1); t.needsUpdate = true; return t; })();
const CACHE = {};
// The interior form of a material: no sky light, only direct light.
export function interior(kind) {
  const key = "in-" + kind;
  if (!CACHE[key]) {
    const m = (kind === "floor" ? new THREE.MeshStandardMaterial({ color: 0xa8957c, roughness: 1 }) : material(kind)).clone();
    Object.assign(m, { aoMap: AO, aoMapIntensity: 1, side: THREE.DoubleSide, shadowSide: THREE.DoubleSide });
    CACHE[key] = m;
  }
  return CACHE[key];
}
function grass() {
  if (!CACHE.grass) {
    const t = grassTexture();
    CACHE.grass = new THREE.MeshStandardMaterial({ map: t, roughness: 1, side: THREE.DoubleSide, shadowSide: THREE.DoubleSide });
  }
  return CACHE.grass;
}
const surface = (kind) => (kind === "grass" ? grass() : (CACHE["s-" + kind] ??= Object.assign(material(kind).clone(), { side: THREE.DoubleSide, shadowSide: THREE.DoubleSide })));

// A rectangle of length `len` along azimuth `az` and width `wid` round centre c.
export function rect(c, len, wid, az) {
  const u = [Math.sin(az * R), Math.cos(az * R)], v = [u[1], -u[0]], a = len / 2, b = wid / 2;
  return [[a, b], [a, -b], [-a, -b], [-a, b]].map(([s, t]) => [c[0] + u[0] * s + v[0] * t, c[1] + u[1] * s + v[1] * t]);
}
const mid = (pts) => [pts.reduce((s, p) => s + p[0], 0) / pts.length, pts.reduce((s, p) => s + p[1], 0) / pts.length];

function mesh(pos, idx, mat, uvs) {
  const geo = new THREE.BufferGeometry();
  geo.setAttribute("position", new THREE.Float32BufferAttribute(pos, 3));
  geo.setAttribute("uv", new THREE.Float32BufferAttribute(uvs ?? pos.filter((_, i) => i % 3 !== 1).map((v) => v / 3), 2));
  geo.setIndex(idx);
  geo.computeVertexNormals();
  const m = new THREE.Mesh(geo, mat);
  m.castShadow = m.receiveShadow = true;
  return m;
}
// A vertical wall along a polyline of [x, y, bottom, top] (absolute heights).
function wall(pts, mat) {
  const pos = [], idx = [], uv = [];
  let run = 0;
  pts.forEach(([x, y, lo, hi], i) => {
    if (i) run += Math.hypot(x - pts[i - 1][0], y - pts[i - 1][1]);
    pos.push(x, lo, -y, x, hi, -y);
    uv.push(run / 3, lo / 3, run / 3, hi / 3);
    if (i) { const a = 2 * i - 2; idx.push(a, a + 2, a + 1, a + 1, a + 2, a + 3); }
  });
  return mesh(pos, idx, mat, uv);
}

// One stone or slab: {outline} or {c, len, wid, az}; h, rock, base (lintels, capstones), state, interior.
export function stone(p, height, seed) {
  const outline = p.outline ?? rect(p.c, p.len, p.wid, p.az ?? 0);
  const c = mid(outline), g = p.ground ?? height(c[0], c[1]) ?? 0;
  const m = stoneMesh({ ...p, outline, kind: p.rock ?? "sandstone" }, g + (p.z ?? 0), { seed });
  if (!m) return null;
  if (p.interior) m.material = interior(p.rock ?? "sandstone");
  return m;
}

// Mound: {c, r (or radii: one every 360/n degrees from north), h, kerb_h, p (profile), surface, kerb_rock,
// facade: {from, to, rock, h} (an arc of the drum faced in another stone, and as high as h there, blending back to
// kerb_h over 10°), gap: {az, width, open: [[lo, hi], ...]}} on
// ground flattened by the builder. The top is a dome down to the kerb drum; the drum is open where the passage enters.
function mound(p, height) {
  const [cx, cy] = p.c, NR = 28, NS = 180, kerb = p.kerb_h ?? 0, g0 = height(cx, cy) ?? 0;
  const rAt = (az) => {
    if (!p.radii) return p.r;
    const n = p.radii.length, f = (((az % 360) + 360) % 360) / 360 * n, i = Math.floor(f) % n, t = f - Math.floor(f);
    return p.radii[i] * (1 - t) + p.radii[(i + 1) % n] * t;
  };
  const within = (az, a, b) => ((az - a + 360) % 360) <= ((b - a + 360) % 360);
  const kAt = (az) => {
    const f = p.facade;
    if (!f || f.h == null) return kerb;
    if (within(az, f.from, f.to)) return f.h;
    const off = Math.min((f.from - az + 360) % 360, (az - f.to + 360) % 360);
    return off >= 10 ? kerb : f.h + (kerb - f.h) * off / 10;
  };
  // The dome's profile follows a smoothed outline (a notch at an entrance does not crease it); the true outline only
  // at the edge, where the dome meets the drum.
  const smooth = (a) => { let t = 0; for (let k = -30; k <= 30; k += 5) t += rAt(a + k); return t / 13; };
  const pos = [], idx = [];
  for (let i = 0; i <= NR; i++) for (let j = 0; j < NS; j++) {
    const a = j / NS * 360, Rr = rAt(a), Rs = smooth(a), k = kAt(a);
    const r = i === NR ? Rr : Math.min(Rr, Rs) * i / (NR - 1) * (NR - 1) / NR;
    const z = i === NR ? g0 + k : g0 + k + (p.h - k) * Math.pow(Math.max(0, 1 - (r / Rs) ** 2), p.p ?? 0.8);
    pos.push(cx + r * Math.sin(a * R), z, -(cy + r * Math.cos(a * R)));
  }
  for (let i = 0; i < NR; i++) for (let j = 0; j < NS; j++) {
    const a = i * NS + j, b = i * NS + (j + 1) % NS;
    idx.push(a, b, a + NS, b, b + NS, a + NS);           // faces up
  }
  const g = new THREE.Group();
  g.add(mesh(pos, idx, surface(p.surface ?? "grass")));
  // Drum: one wall per segment, open where the passage comes in.
  const gapHalf = p.gap ? (p.gap.width / 2) / rAt(p.gap.az) / R : 0;
  const inGap = (az) => p.gap && Math.abs(((az - p.gap.az + 540) % 360) - 180) < gapHalf;
  const bands = (az) => {
    const top = kAt(az);
    if (!inGap(az)) return [[0, top]];
    const out = []; let lo = 0;
    for (const [a, b] of p.gap.open) { if (a > lo) out.push([lo, a]); lo = b; }
    if (lo < top) out.push([lo, top]);
    return out;
  };
  for (let j = 0; j < NS; j++) {
    const a0 = j / NS * 360, a1 = (j + 1) / NS * 360, am = (a0 + a1) / 2;
    const dm = surface(p.facade && within(am, p.facade.from, p.facade.to) ? p.facade.rock : p.kerb_rock ?? "cairn");
    for (const [lo, hi] of bands(am)) {
      const pt = (a) => [cx + rAt(a) * Math.sin(a * R), cy + rAt(a) * Math.cos(a * R), g0 + lo, g0 + Math.min(hi, kAt(a))];
      if (hi > lo + 0.02) g.add(wall([pt(a0), pt(a1)], dm));
    }
  }
  return g;
}

// Passage: {path: [[x, y], ...] entrance first, floor: [z, ...] above the ground at the entrance, width, roof (height
// above the floor; numbers or lists), rock, roof_rock, step (stone length), roof_gap: [from, to] metres from the
// entrance left open (a roof-box)}. Orthostats both sides, capstones over, a floor and a liner.
function passage(p, height, seed) {
  const g = new THREE.Group(), path = p.path, n = path.length;
  const g0 = height(path[0][0], path[0][1]) ?? 0;
  const at = (v, i) => (Array.isArray(v) ? v[i] : v);
  let total = 0;
  const cum = [0];
  for (let i = 1; i < n; i++) { total += Math.hypot(path[i][0] - path[i - 1][0], path[i][1] - path[i - 1][1]); cum.push(total); }
  // Position, direction and the interpolated values `d` metres from the entrance.
  const sample = (d) => {
    let i = 1;
    while (i < n - 1 && cum[i] < d) i++;
    const t = Math.min(1, Math.max(0, (d - cum[i - 1]) / ((cum[i] - cum[i - 1]) || 1)));
    const lerp = (v) => at(v, i - 1) + (at(v, i) - at(v, i - 1)) * t;
    const x = path[i - 1][0] + (path[i][0] - path[i - 1][0]) * t, y = path[i - 1][1] + (path[i][1] - path[i - 1][1]) * t;
    const az = Math.atan2(path[i][0] - path[i - 1][0], path[i][1] - path[i - 1][1]) / R;
    return { x, y, az, floor: g0 + lerp(p.floor ?? 0), w: lerp(p.width), h: lerp(p.roof) };
  };
  const step = p.step ?? 1, rock = p.rock ?? "sandstone", roofRock = p.roof_rock ?? rock;
  const side = (s, k) => [s.x + Math.cos(s.az * R) * k, s.y - Math.sin(s.az * R) * k];
  for (let d = step / 2, k = 0; d < total; d += step, k++) {
    const s = sample(d);
    for (const sgn of [-1, 1]) {
      const c = side(s, sgn * (s.w / 2 + 0.17));
      const m = stone({ c, len: step * 0.92, wid: 0.32, az: s.az, h: s.h + 0.15, rock, interior: true, ground: s.floor }, height, seed + k * 2 + (sgn > 0));
      if (m) g.add(m);
    }
  }
  // Roof slabs, one per `step`, cut where the roof is left open (roof_gap: a roof-box slit, an unroofed stretch).
  for (let a = 0, k = 0; a < total - 1e-6; a += step, k++) {
    let pieces = [[a, Math.min(total, a + step)]];
    if (p.roof_gap) {
      const [g0_, g1_] = p.roof_gap;
      pieces = pieces.flatMap(([lo, hi]) => [[lo, Math.min(hi, g0_)], [Math.max(lo, g1_), hi]]).filter(([lo, hi]) => hi - lo > 0.05);
    }
    pieces.forEach(([lo, hi], j) => {
      const s = sample((lo + hi) / 2);
      const cap = stone({ c: [s.x, s.y], len: (hi - lo) * 0.98, wid: s.w + 1, az: s.az, h: 0.35, base: s.h, rock: roofRock, interior: true, ground: s.floor, rough: p.roof_rough ?? 1 }, height, seed + 500 + k * 3 + j);
      if (cap) g.add(cap);
    });
  }
  // Floor and liner, sampled every 0.5 m.
  const fl = [], li = { "-1": [], 1: [] };
  for (let d = 0; d <= total + 1e-6; d += Math.min(0.5, total)) {
    const s = sample(d);
    fl.push(s);
    for (const sgn of [-1, 1]) { const [x, y] = side(s, sgn * (s.w / 2 + 0.36)); li[sgn].push([x, y, s.floor - 0.05, s.floor + s.h + 0.4]); }
  }
  const pos = [], idx = [];
  fl.forEach((s, i) => {
    for (const sgn of [-1, 1]) { const [x, y] = side(s, sgn * (s.w / 2 + 0.2)); pos.push(x, s.floor + 0.02, -y); }
    if (i) { const a = 2 * i - 2; idx.push(a, a + 2, a + 1, a + 1, a + 2, a + 3); }
  });
  g.add(mesh(pos, idx, interior("floor")));
  for (const sgn of [-1, 1]) g.add(wall(li[sgn], interior(rock)));
  return g;
}

// Chamber: {outline: [[x, y], ...], floor (above the ground at its centre), h (walls), roof: {kind: "capstone",
// thickness} or {kind: "corbel", top, rings}, rock, roof_rock, open: [{at: [x, y], width}] where the passage comes in}.
function chamber(p, height, seed) {
  const g = new THREE.Group(), c = mid(p.outline), g0 = (height(c[0], c[1]) ?? 0) + (p.floor ?? 0);
  const rock = p.rock ?? "sandstone", roofRock = p.roof_rock ?? rock, n = p.outline.length;
  const opens = (x, y) => (p.open ?? []).some((o) => Math.hypot(x - o.at[0], y - o.at[1]) < o.width / 2 + 0.3);
  const out = (pt, k) => { const dx = pt[0] - c[0], dy = pt[1] - c[1], l = Math.hypot(dx, dy) || 1; return [pt[0] + dx / l * k, pt[1] + dy / l * k]; };
  let k = 0;
  for (let i = 0; i < n; i++) {
    const a = p.outline[i], b = p.outline[(i + 1) % n], len = Math.hypot(b[0] - a[0], b[1] - a[1]);
    const az = Math.atan2(b[0] - a[0], b[1] - a[1]) / R, m = Math.max(1, Math.round(len / (p.step ?? 1.2)));
    for (let j = 0; j < m; j++) {
      const t = (j + 0.5) / m, x = a[0] + (b[0] - a[0]) * t, y = a[1] + (b[1] - a[1]) * t;
      if (opens(x, y)) continue;
      const s = stone({ c: out([x, y], 0.2), len: len / m * 0.95, wid: 0.4, az, h: p.h + 0.1, rock, interior: true, ground: g0 }, height, seed + k++);
      if (s) g.add(s);
    }
  }
  const ring = (k2, z) => p.outline.map((pt) => { const [x, y] = out(pt, k2); return [x, y, z]; });
  const fpos = [], fidx = [];
  fpos.push(c[0], g0 + 0.02, -c[1]);
  p.outline.forEach((pt) => fpos.push(pt[0], g0 + 0.02, -pt[1]));
  for (let i = 0; i < n; i++) fidx.push(0, 1 + i, 1 + (i + 1) % n);
  g.add(mesh(fpos, fidx, interior("floor")));
  // Liner behind the uprights, edge by edge, open where the passage comes in.
  const lin = ring(0.42, 0);
  for (let i = 0; i < n; i++) {
    const a = lin[i], b = lin[(i + 1) % n], len = Math.hypot(b[0] - a[0], b[1] - a[1]);
    const cut = (p.open ?? []).map((o) => {
      const ex = (b[0] - a[0]) / len, ey = (b[1] - a[1]) / len, t = (o.at[0] - a[0]) * ex + (o.at[1] - a[1]) * ey;
      const d = Math.abs((o.at[0] - a[0]) * ey - (o.at[1] - a[1]) * ex);
      return d < 0.8 && t > -o.width && t < len + o.width ? [t - o.width / 2 - 0.2, t + o.width / 2 + 0.2] : null;
    }).filter(Boolean);
    const spans = [[0, len]];
    for (const [lo, hi] of cut) {
      const s0 = spans.pop();
      if (lo > s0[0]) spans.push([s0[0], Math.min(lo, s0[1])]);
      if (hi < s0[1]) spans.push([Math.max(hi, s0[0]), s0[1]]);
    }
    for (const [t0, t1] of spans) {
      if (t1 - t0 < 0.05) continue;
      const pt = (t) => [a[0] + (b[0] - a[0]) * t / len, a[1] + (b[1] - a[1]) * t / len, g0 - 0.05, g0 + p.h + 0.3];
      g.add(wall([pt(t0), pt(t1)], interior(rock)));
    }
  }
  const roof = p.roof ?? { kind: "capstone", thickness: 0.6 };
  if (roof.kind === "corbel") {
    const rings = roof.rings ?? 8, top = roof.top ?? p.h + 2;
    for (let r = 0; r < rings; r++) {
      const f = 1 - (r + 1) / (rings + 1), z0 = g0 + p.h + (top - p.h) * r / rings, z1 = g0 + p.h + (top - p.h) * (r + 1) / rings;
      const pts = p.outline.map((pt) => [c[0] + (pt[0] - c[0]) * f, c[1] + (pt[1] - c[1]) * f]);
      for (let i = 0; i < n; i++) {
        const a = pts[i], b = pts[(i + 1) % n], len = Math.hypot(b[0] - a[0], b[1] - a[1]);
        const s = stone({ c: out([(a[0] + b[0]) / 2, (a[1] + b[1]) / 2], 0.25), len: len + 0.3, wid: 0.6, az: Math.atan2(b[0] - a[0], b[1] - a[1]) / R,
          h: z1 - z0 + 0.05, base: z0 - g0, rock: roofRock, interior: true, ground: g0 }, height, seed + 900 + r * n + i);
        if (s) g.add(s);
      }
    }
    const capPts = p.outline.map((pt) => out([c[0] + (pt[0] - c[0]) / (rings + 1), c[1] + (pt[1] - c[1]) / (rings + 1)], 0.5));
    const cap = stone({ outline: capPts, h: 0.4, base: top, rock: roofRock, interior: true, ground: g0 }, height, seed + 990);
    if (cap) g.add(cap);
  } else {
    const cap = stone({ outline: p.outline.map((pt) => out(pt, 0.5)), h: roof.thickness ?? 0.6, base: p.h, rock: roofRock, interior: true, ground: g0 }, height, seed + 990);
    if (cap) g.add(cap);
  }
  return g;
}

// Post: {c, d, h, rock (timber unless given)}; a little taper.
function post(p, height) {
  const g0 = height(p.c[0], p.c[1]) ?? 0;
  const m = new THREE.Mesh(new THREE.CylinderGeometry(p.d * 0.45, p.d / 2, p.h + 0.3, 10, 2), material(p.rock ?? "timber"));
  m.position.set(p.c[0], g0 + (p.h - 0.3) / 2, -p.c[1]);
  m.castShadow = m.receiveShadow = true;
  return m;
}

// Bank (h > 0) or the hollow of a silted ditch (h < 0) drawn on the ground: {c, r, w, h, gaps: [[az, width m]]}.
function bank(p, height) {
  const [cx, cy] = p.c, NS = Math.max(90, Math.round(p.r * 2)), NW = 6, pos = [], idx = [];
  const gap = (az) => (p.gaps ?? []).some(([a, w]) => Math.abs(((az - a + 540) % 360) - 180) < (w / 2) / p.r / R);
  for (let j = 0; j <= NS; j++) for (let i = 0; i <= NW; i++) {
    const az = j / NS * 360, rr = p.r - p.w / 2 + p.w * i / NW, x = cx + rr * Math.sin(az * R), y = cy + rr * Math.cos(az * R);
    const prof = Math.sin(Math.PI * i / NW) ** 1.5 * (gap(az) ? 0 : 1);
    pos.push(x, (height(x, y) ?? 0) + 0.03 + p.h * prof, -y);
  }
  for (let j = 0; j < NS; j++) for (let i = 0; i < NW; i++) { const a = j * (NW + 1) + i, b = a + NW + 1; idx.push(a, b, a + 1, a + 1, b, b + 1); }
  return mesh(pos, idx, grass());
}

const BUILDERS = { stone, mound, passage, chamber, post, bank };
// Every part of a view → { group, labels }; each mesh carries its part's `info` for clicks.
export function buildParts(parts, height) {
  const group = new THREE.Group(), labels = new THREE.Group();
  parts.forEach((p, i) => {
    const o = BUILDERS[p.kind]?.(p, height, i * 37 + 11);
    if (!o) return;
    const info = { id: p.id, title: p.title, note: p.note, status: p.status, cites: p.cites };
    o.traverse((m) => {
      if (!m.isMesh) return;
      m.userData = { ...m.userData, info };
      if (p.status === "restored") { m.userData.plain = m.material; m.userData.pale = material(p.rock ?? "sandstone", true); }
    });
    group.add(o);
    if (p.label) {
      const c = p.c ?? mid(p.outline ?? p.path), sp = label(p.label);
      sp.position.set(c[0], (height(c[0], c[1]) ?? 0) + (p.h ?? 2) + 0.8, -c[1]);
      labels.add(sp);
    }
  });
  group.add(labels);
  return { group, labels };
}
