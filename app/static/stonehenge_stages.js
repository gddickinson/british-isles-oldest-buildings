// Stonehenge by stages (roadmap SH2a; data from bidb.stonehenge_stages): the henge bank and ditch as they were at
// each stage, drawn as fine meshes over today's LiDAR ground (which is pushed down beneath them), the Avenue's banks
// and ditches, open pits (Aubrey, Y and Z holes), timber posts, and the pieces of the completed monument standing then.
import * as THREE from "./vendor/three/three.module.min.js";
import { noise3 } from "./stonehenge_stones.js";

const R = Math.PI / 180;
const smooth = (a, b, x) => { const t = Math.min(1, Math.max(0, (x - a) / (b - a))); return t * t * (3 - 2 * t); };
const bump = (x, c, half) => (Math.abs(x - c) >= half ? 0 : Math.cos((x - c) / half * Math.PI / 2) ** 2);
const GRASS = new THREE.Color().setStyle("rgb(104,128,64)"), CHALK = new THREE.Color().setStyle("rgb(226,224,212)");
export const AUBREY = { stones: "Bluestones", posts: "Timber posts", empty: "Empty holes" };

// Box outline [x, y] of width w along azimuth `along` and depth d across it, centred on x, y.
export function box(x, y, along, w, d) {
  const a = along * R, b = (along + 90) * R;
  return [[-1, -1], [1, -1], [1, 1], [-1, 1]].map(([s, t]) =>
    [x + s * w / 2 * Math.sin(a) + t * d / 2 * Math.sin(b), y + s * w / 2 * Math.cos(a) + t * d / 2 * Math.cos(b)]);
}

// The stage's pieces as stone records for the model builder: the completed monument's pieces of its groups (all
// when groups is null) and its own bluestones; Aubrey Holes hold stones when `aubrey` is "stones".
export function pieces(stage, built, aubrey) {
  const list = built.filter((s) => !stage.groups || stage.groups.includes(s.group));
  for (const e of stage.extra) {
    if (e.kind === "bluestone" || (e.kind === "aubrey" && aubrey === "stones")) {
      const turn = e.turn ?? Math.atan2(e.x, e.y) / R;
      list.push({ id: e.kind === "aubrey" ? e.id : "", group: e.kind === "aubrey" ? "aubrey_bluestone" : "bluestone", kind: "bluestone",
        status: "restored", outline: box(e.x, e.y, turn + 90, 0.8, 0.5), h: e.h ?? 1.9 });
    }
  }
  return list;
}

// Profile of the henge across its ring at radius r and azimuth az (metres above the old ground).
function henge(e, r, az) {
  const gap = e.entrances.some((g) => Math.abs(((az - g.az + 540) % 360) - 180) * R * r < g.w / 2);
  const bankC = e.ditch_r - e.ditch_w / 2 - e.bank_gap - e.bank_w / 2;
  const ditch = gap ? 0 : -e.depth * (1 - ((r - e.ditch_r) / (e.ditch_w / 2)) ** 2);
  return {
    z: (Math.abs(r - e.ditch_r) < e.ditch_w / 2 ? ditch : 0) + e.bank_h * bump(r, bankC, e.bank_w / 2)
      + (gap ? 0 : e.counter_h * bump(r, e.ditch_r + e.ditch_w / 2 + 0.5 + e.counter_w / 2, e.counter_w / 2)),
    chalk: !gap && Math.abs(r - e.ditch_r) < e.ditch_w / 2 ? 1 : bump(r, bankC, e.bank_w / 2 + 0.6) > 0.05 ? 0.85 : 0,
  };
}
// The Avenue across its width at offset v (metres) from the axis: low banks inside, ditches outside.
function avenue(a, v) {
  const half = a.ditch_gap / 2, bankC = a.corridor / 2 + 1.5, av = Math.abs(v);
  return { z: 0.5 * bump(av, bankC, 1.5) - 0.8 * bump(av, half, 1.0), chalk: bump(av, half, 1.2) > 0.1 ? 0.7 : bump(av, bankC, 1.6) > 0.1 ? 0.5 : 0 };
}

// A fine strip over the ground: u along, v across; xy(u, v) → [x, y]; prof(u, v) → {z, chalk}; heights from the old
// ground taken straight across the strip (so today's worn earthwork is replaced, not added to).
function strip(height0, nu, nv, xy, prof, chalk) {
  const pos = [], col = [], idx = [];
  for (let i = 0; i <= nu; i++) {
    const u = i / nu;
    const [x0, y0] = xy(u, 0), [x1, y1] = xy(u, 1);
    const h0 = height0(x0, y0) ?? 0, h1 = height0(x1, y1) ?? 0;
    for (let j = 0; j <= nv; j++) {
      const v = j / nv, [x, y] = xy(u, v), p = prof(u, v), n = 0.9 + 0.1 * noise3(x / 3, y / 3, 0.2, 9);
      pos.push(x, h0 + (h1 - h0) * v + p.z, -y);
      const c = GRASS.clone().lerp(CHALK, p.chalk * chalk);
      col.push(c.r * n, c.g * n, c.b * n);
    }
  }
  for (let i = 0; i < nu; i++) for (let j = 0; j < nv; j++) {
    const a = i * (nv + 1) + j, b = a + 1, c = a + nv + 1, d = c + 1;
    idx.push(a, c, b, b, c, d);
  }
  const geo = new THREE.BufferGeometry();
  geo.setAttribute("position", new THREE.Float32BufferAttribute(pos, 3));
  geo.setAttribute("color", new THREE.Float32BufferAttribute(col, 3));
  geo.setIndex(idx);
  geo.computeVertexNormals();
  const m = new THREE.Mesh(geo, new THREE.MeshStandardMaterial({ vertexColors: true, roughness: 1 }));
  m.receiveShadow = m.castShadow = true;
  return m;
}

// Everything a stage adds to the scene, and how it changes the ground: {group, ground(x, y), surface(x, y)} where
// ground pushes today's mesh beneath the strips and surface is the stage's own ground for placing things.
export function stageWorld(stage, info, height0, aubrey) {
  const e = stage.earth, [cx, cy] = e.centre, group = new THREE.Group();
  const rIn = e.ditch_r - e.ditch_w / 2 - e.bank_gap - e.bank_w - 1.5, rOut = e.ditch_r + e.ditch_w / 2 + 1 + e.counter_w + 1.5;
  const ring = (u, v) => { const az = u * 360, r = rIn + (rOut - rIn) * v; return [cx + r * Math.sin(az * R), cy + r * Math.cos(az * R)]; };
  group.add(strip(height0, 1440, Math.round((rOut - rIn) / 0.4), ring, (u, v) => henge(e, rIn + (rOut - rIn) * v, u * 360), e.chalk));
  const av = stage.avenue ? info.avenue : null;
  const aFrom = rOut - 0.5, aTo = 390, aw = av ? av.ditch_gap / 2 + 3 : 0, ax = info.avenue.axis * R;
  const along = (u, v) => { const s = aFrom + (aTo - aFrom) * u, o = (0.5 - v) * 2 * aw;   // v runs right to left, so the strip faces up
    return [s * Math.sin(ax) + o * Math.cos(ax), s * Math.cos(ax) - o * Math.sin(ax)]; };
  if (av) group.add(strip(height0, Math.round((aTo - aFrom) / 0.5), Math.round(2 * aw / 0.4), along, (u, v) => avenue(av, (v - 0.5) * 2 * aw), Math.max(e.chalk, 0.3)));

  const inRing = (x, y) => { const r = Math.hypot(x - cx, y - cy); return [r, Math.atan2(x - cx, y - cy) / R]; };
  const inAvenue = (x, y) => [x * Math.sin(ax) + y * Math.cos(ax), x * Math.cos(ax) - y * Math.sin(ax)];
  const ground = (x, y) => {
    const [r] = inRing(x, y);
    let d = -3 * Math.min(smooth(rIn, rIn + 3, r), 1 - smooth(rOut - 3, rOut, r));
    if (av) { const [s, o] = inAvenue(x, y); d = Math.min(d, -3 * Math.min(smooth(aFrom, aFrom + 3, s), 1 - smooth(aw - 3, aw, Math.abs(o)), 1 - smooth(aTo - 3, aTo, s))); }
    return d;
  };
  const surface = (x, y) => {
    const [r, az] = inRing(x, y);
    if (r > rIn && r < rOut) {
      const [x0, y0] = ring(az / 360, 0), [x1, y1] = ring(az / 360, 1), v = (r - rIn) / (rOut - rIn);
      return ((height0(x0, y0) ?? 0) * (1 - v) + (height0(x1, y1) ?? 0) * v + henge(e, r, az).z) - (height0(x, y) ?? 0);
    }
    return 0;
  };

  const pit = new THREE.MeshStandardMaterial({ color: 0x2b2620, roughness: 1 });
  const wood = new THREE.MeshStandardMaterial({ color: 0x6b5236, roughness: 0.9 });
  for (const p of stage.extra) {
    if (p.kind === "bluestone" || (p.kind === "aubrey" && aubrey === "stones")) continue;
    const h = (height0(p.x, p.y) ?? 0) + surface(p.x, p.y);
    if (p.kind === "aubrey" && aubrey === "posts") {
      const post = new THREE.Mesh(new THREE.CylinderGeometry(0.28, 0.32, 3.2, 10), wood);
      post.position.set(p.x, h + 1.5, -p.y);
      post.castShadow = post.receiveShadow = true;
      post.userData = { id: p.id, group: "aubrey_post", status: "restored" };
      group.add(post);
      continue;
    }
    const disc = new THREE.Mesh(new THREE.CircleGeometry(p.d / 2, 20), pit);
    disc.rotation.x = -Math.PI / 2;
    disc.position.set(p.x, h + 0.04, -p.y);
    disc.userData = { id: p.id, group: p.kind === "aubrey" ? "aubrey_hole" : "yz_hole" };
    group.add(disc);
  }
  return { group, ground, surface };
}
