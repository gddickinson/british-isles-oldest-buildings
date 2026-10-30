// The round-tower part of the 3D models (roadmap SH4c: Glendalough, Kildare, Ardmore, Clondalkin, Brechin,
// Abernethy): a tapering shaft on a plinth, a conical cap (or spire, crenellation or flat top), the raised doorway
// and the windows as dark openings. Registered as part kind "tower".
// {c, h (to the top of the shaft), d_base, d_top, plinth, cap: {kind: "cone"|"spire"|"crenel"|"flat", h},
//  door: {sill, h, w, az}, windows: [{z, az, h, w}], rock}
import { BUILDERS, mesh, surface } from "./model_parts.js";
import * as THREE from "./vendor/three/three.module.min.js";

const R = Math.PI / 180;
const DARK = new THREE.MeshStandardMaterial({ color: 0x15130f, roughness: 1 });

function tower(p, height) {
  const g = new THREE.Group(), [cx, cy] = p.c, g0 = height(cx, cy) ?? 0, mat = surface(p.rock ?? "granite");
  const rb = p.d_base / 2, rt = p.d_top / 2, NS = 40, NZ = Math.max(4, Math.round(p.h / 1.5));
  const rAt = (z) => rb + (rt - rb) * z / p.h;
  const pos = [], idx = [], uv = [];
  for (let k = 0; k <= NZ; k++) for (let j = 0; j <= NS; j++) {
    const z = p.h * k / NZ, a = j / NS * 360, r = rAt(z);
    pos.push(cx + r * Math.sin(a * R), g0 + z, -(cy + r * Math.cos(a * R)));
    uv.push(r * a * R / 2, z / 2);
  }
  for (let k = 0; k < NZ; k++) for (let j = 0; j < NS; j++) {
    const a = k * (NS + 1) + j, b = a + NS + 1;
    idx.push(a, a + 1, b, a + 1, b + 1, b);
  }
  g.add(mesh(pos, idx, mat, uv));
  if (p.plinth) {
    const pl = new THREE.Mesh(new THREE.CylinderGeometry(rb + 0.2, rb + 0.25, p.plinth, NS), mat);
    pl.position.set(cx, g0 + p.plinth / 2, -cy);
    pl.castShadow = pl.receiveShadow = true;
    g.add(pl);
  }
  const top = g0 + p.h, cap = p.cap ?? { kind: "cone", h: 4 };
  let capMesh;
  if (cap.kind === "cone" || cap.kind === "spire") {
    capMesh = new THREE.Mesh(new THREE.ConeGeometry(cap.kind === "spire" ? rt * 0.85 : rt + 0.05, cap.h, cap.kind === "spire" ? 8 : NS), mat);
    capMesh.position.set(cx, top + cap.h / 2, -cy);
  } else if (cap.kind === "crenel") {
    capMesh = new THREE.Group();
    for (let j = 0; j < 12; j += 2) {
      const a = j / 12 * 360, m = new THREE.Mesh(new THREE.BoxGeometry(0.7, 0.8, 0.5), mat);
      m.position.set(cx + rt * Math.sin(a * R), top + 0.4, -(cy + rt * Math.cos(a * R)));
      m.rotation.y = -a * R;
      capMesh.add(m);
    }
  }
  if (capMesh) { capMesh.traverse((m) => { if (m.isMesh) m.castShadow = m.receiveShadow = true; }); g.add(capMesh); }
  // Openings: thin dark panels set just proud of the wall.
  const opening = (z, az, h, w) => {
    const r = rAt(z + h / 2) + 0.02, m = new THREE.Mesh(new THREE.PlaneGeometry(w, h), DARK);
    m.position.set(cx + r * Math.sin(az * R), g0 + z + h / 2, -(cy + r * Math.cos(az * R)));
    m.rotation.y = -az * R + Math.PI;
    m.lookAt(cx + (r + 5) * Math.sin(az * R), g0 + z + h / 2, -(cy + (r + 5) * Math.cos(az * R)));
    g.add(m);
  };
  if (p.door) opening(p.door.sill, p.door.az, p.door.h, p.door.w ?? 0.6);
  for (const w of p.windows ?? []) opening(w.z, w.az, w.h ?? 0.8, w.w ?? 0.35);
  return g;
}

BUILDERS.tower = tower;
