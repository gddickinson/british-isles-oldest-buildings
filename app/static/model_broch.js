// The broch part of the 3D models (Mousa, roadmap SH3g): a dry-stone tower with a batter, solid at the base and
// hollow above (an inner and an outer wall tied by the slab floors of its galleries), the court, the entrance
// passage through the solid base, the stair climbing through the galleries, the ledges (scarcements) inside, and a
// cutaway: a sector of the wall left out so the galleries and stair show. Registered as part kind "broch".
// {c, h, r_base, r_top, court_r, solid_h, galleries: [[z0, z1], ...], gallery_w, entrance: {az, width, h},
//  stair: {az0, z0, z1, turn, width}, ledges: [z, ...], cut: [az0, az1] | null, rock}
import { BUILDERS, mesh, surface, stone } from "./model_parts.js";
import * as THREE from "./vendor/three/three.module.min.js";

const R = Math.PI / 180;

function broch(p, height, seed) {
  const g = new THREE.Group(), [cx, cy] = p.c, g0 = height(cx, cy) ?? 0, mat = surface(p.rock ?? "flagstone");
  const ro = (z) => p.r_base + (p.r_top - p.r_base) * z / p.h;                 // outer face
  const rc = p.court_r;
  const gw = p.gallery_w ?? 0.9;
  const mid = (z) => (rc + ro(z)) / 2;
  const gIn = (z) => mid(z) - gw / 2, gOut = (z) => mid(z) + gw / 2;            // the gallery's two faces
  const NS = 120, cut = p.cut;
  const inCut = (az) => cut && ((az - cut[0] + 360) % 360) < ((cut[1] - cut[0] + 360) % 360);
  const e = p.entrance;
  const inDoor = (az, r) => e && Math.abs(((az - e.az + 540) % 360) - 180) < (e.width / 2) / r / R;
  const xy = (r, az) => [cx + r * Math.sin(az * R), cy + r * Math.cos(az * R)];
  // A surface of revolution r(z) between z0 and z1, segment by segment, skipping the cut and (below the lintel) the door.
  const ring = (rFn, z0, z1, door = false) => {
    const pos = [], idx = [], uv = [];
    const zs = [];
    for (let z = z0; z < z1 - 1e-6; z += 0.5) zs.push(z);
    zs.push(z1);
    for (let j = 0; j < NS; j++) {
      const a0 = j / NS * 360, a1 = (j + 1) / NS * 360, am = (a0 + a1) / 2;
      if (inCut(am)) continue;
      for (let k = 0; k < zs.length - 1; k++) {
        if (door && zs[k] < e.h && inDoor(am, rFn(zs[k]))) continue;
        const base = pos.length / 3;
        for (const [a, z] of [[a0, zs[k]], [a1, zs[k]], [a0, zs[k + 1]], [a1, zs[k + 1]]]) {
          const [x, y] = xy(rFn(z), a);
          pos.push(x, g0 + z, -y);
          uv.push(rFn(z) * a * R / 2, z / 2);                                  // round the wall and up it
        }
        idx.push(base, base + 1, base + 2, base + 1, base + 3, base + 2);
      }
    }
    if (pos.length) g.add(mesh(pos, idx, mat, uv));
  };
  // A flat annulus at height z between two radii.
  const annulus = (r0, r1, z) => {
    const pos = [], idx = [], uv = [];
    for (let j = 0; j < NS; j++) {
      const a0 = j / NS * 360, a1 = (j + 1) / NS * 360;
      if (inCut((a0 + a1) / 2)) continue;
      const base = pos.length / 3;
      for (const [r, a] of [[r0, a0], [r1, a0], [r0, a1], [r1, a1]]) { const [x, y] = xy(r, a); pos.push(x, g0 + z, -y); uv.push(x / 2, y / 2); }
      idx.push(base, base + 1, base + 2, base + 1, base + 3, base + 2);
    }
    if (pos.length) g.add(mesh(pos, idx, mat, uv));
  };
  ring(ro, 0, p.h, true);
  ring(() => rc, 0, p.h, true);
  annulus(rc, ro(p.h), p.h);
  for (const [z0, z1] of p.galleries) {
    ring(gIn, z0, z1);
    ring(gOut, z0, z1);
    annulus(gIn(z0), gOut(z0), z0);
    annulus(gIn(z1), gOut(z1), z1);
  }
  for (const z of p.ledges ?? []) annulus(rc - 0.2, rc, z);
  // The cut faces: the wall in section, with the galleries open.
  if (cut) for (const az of cut) {
    const pos = [], idx = [], uv = [];
    const quad = (r0, r1, z0, z1) => {
      const base = pos.length / 3;
      for (const [r, z] of [[r0, z0], [r1, z0], [r0, z1], [r1, z1]]) { const [x, y] = xy(r, az); pos.push(x, g0 + z, -y); uv.push(r / 2, z / 2); }
      idx.push(base, base + 1, base + 2, base + 1, base + 3, base + 2);
    };
    let z = 0;
    for (const [z0, z1] of p.galleries) {
      if (z0 > z) quad(rc, ro(z0), z, z0);                                     // solid between galleries
      quad(rc, gIn(z0), z0, z1);
      quad(gOut(z0), ro(z1), z0, z1);
      z = z1;
    }
    if (z < p.h) quad(rc, ro(p.h), z, p.h);
    g.add(mesh(pos, idx, mat, uv));
  }
  // The entrance passage: side walls and roof through the solid base.
  if (e) {
    const side = (k) => {
      const pts = [rc, ro(0)].map((r) => {
        const [x, y] = xy(r, e.az);
        return [x + Math.cos(e.az * R) * k, y - Math.sin(e.az * R) * k];
      });
      const pos = [], idx = [0, 1, 2, 1, 3, 2];
      for (const [x, y] of pts) pos.push(x, g0, -y);
      for (const [x, y] of pts) pos.push(x, g0 + e.h, -y);
      g.add(mesh(pos, [0, 1, 2, 1, 3, 2], mat));
    };
    side(e.width / 2);
    side(-e.width / 2);
    const [mx, my] = xy((rc + ro(0)) / 2, e.az);
    g.add(stone({ c: [mx, my], len: ro(0) - rc + 0.2, wid: e.width + 0.4, az: e.az, h: 0.3, base: e.h, rock: p.rock ?? "flagstone", rough: 0.3 }, height, seed + 1));
  }
  // The stair: treads climbing clockwise through the wall.
  const s = p.stair;
  if (s) {
    const n = Math.round((s.z1 - s.z0) / 0.22);
    for (let i = 0; i <= n; i++) {
      const az = s.az0 + s.turn * i / n, z = s.z0 + (s.z1 - s.z0) * i / n;
      if (inCut(az)) continue;
      const [x, y] = xy(mid(z), az);
      const st = stone({ c: [x, y], len: 0.32, wid: s.width, az: az + 90, h: 0.12, base: z, rock: p.rock ?? "flagstone", rough: 0.2 }, height, seed + 10 + i);
      if (st) g.add(st);
    }
  }
  return g;
}

BUILDERS.broch = broch;
