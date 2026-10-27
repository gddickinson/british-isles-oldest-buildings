// Building types BT3c2: a material's bedrock drawn on its page's map, from the layers of "Change over time"
// (bidb.change_geology). A material with rock kinds (m.rock, e.g. ["limestone"]) is drawn where BGS 625k (the UK) or
// GSI/GSNI 1:500k (all Ireland) maps a unit containing that rock (any of the unit's periods), within its periods
// (m.geology) unless the kinds are igneous (dated by when they cooled). A material with periods only is drawn by
// period everywhere; m.rock = [] means quarried abroad (nothing drawn). The examples are counted by whether they stand on it,
// out of those on the land the layers cover. TypeGeology.draw(map, m, points) → Promise of a summary, or null.
const TypeGeology = (() => {
  const ROOT = (typeof IS_STATIC !== "undefined" && IS_STATIC ? "static" : "/static") + "/data/change/";
  const IGNEOUS = new Set(["felsic", "mafic"]);
  const COLOR = { limestone: "#2E9FBF", chalk: "#7FC64E", sandstone: "#D98C3A", mudstone: "#7A6FA8", felsic: "#E0457B", mafic: "#555555" };
  const get = (f) => fetch(ROOT + f).then((r) => r.json());
  let geo, rocks;
  const loadGeo = () => (geo = geo || Promise.all([get("layers.json"), get("geology.json")])
    .then(([m, g]) => ({ meta: m.layers.find((l) => l.id === "geology"), g })).catch(() => null));
  const loadRocks = () => (rocks = rocks || get("rocks.json").catch(() => null));

  // rings of a Polygon or MultiPolygon with their bounding boxes, [lon, lat] order
  const parts = (feats) => feats.flatMap((f) => (f.geometry.type === "Polygon" ? [f.geometry.coordinates] : f.geometry.coordinates)
    .map((poly) => {
      let w = 180, e = -180, s = 90, n = -90;
      poly[0].forEach(([x, y]) => { w = Math.min(w, x); e = Math.max(e, x); s = Math.min(s, y); n = Math.max(n, y); });
      return { poly, box: [w, s, e, n] };
    }));

  // even-odd test over the outer ring and its holes
  function inPoly(x, y, poly) {
    let inside = false;
    poly.forEach((ring) => {
      for (let i = 0, j = ring.length - 1; i < ring.length; j = i++) {
        const [xi, yi] = ring[i], [xj, yj] = ring[j];
        if ((yi > y) !== (yj > y) && x < ((xj - xi) * (y - yi)) / (yj - yi) + xi) inside = !inside;
      }
    });
    return inside;
  }

  const on = (ps, lat, lon) => ps.some(({ poly, box }) =>
    lon >= box[0] && lon <= box[2] && lat >= box[1] && lat <= box[3] && inPoly(lon, lat, poly));

  async function draw(map, m, points) {
    if (m.rock && !m.rock.length) return { abroad: true };
    const kinds = m.rock || [], periods = m.geology || [];
    const [gd, rd] = await Promise.all([loadGeo(), kinds.length ? loadRocks() : null]);
    if (!gd || !gd.meta || (kinds.length && !rd)) return null;
    const { meta, g } = gd, names = meta.legend.map((l) => l.label);
    const pset = new Set(periods.map((p) => names.indexOf(p)).filter((i) => i >= 0));
    const spans = (f) => [...pset].some((i) => i >= f.properties.p && i <= f.properties.q);   // the unit's oldest to youngest period
    const igneous = kinds.length && kinds.every((k) => IGNEOUS.has(k));
    if (!map.getPane("bedrock")) map.createPane("bedrock").style.zIndex = 350;   // under the dots (overlay pane 400)
    const fill = (feats, color) => L.geoJSON({ type: "FeatureCollection", features: feats }, { pane: "bedrock", interactive: false,
      style: (f) => { const c = color(f); return { fillColor: c, color: c, fillOpacity: 0.5, weight: 0.8, opacity: 0.9 }; } }).addTo(map);
    const legend = [];
    const target = [];
    if (kinds.length) {
      const bit = (k) => 1 << rd.kinds.findIndex((x) => x.id === k);
      kinds.forEach((k) => {
        const feats = rd.features.filter((f) => (f.properties.k & bit(k)) && (igneous || !pset.size || spans(f)));
        fill(feats, () => COLOR[k]);
        legend.push({ color: COLOR[k], label: rd.kinds.find((x) => x.id === k).label + (igneous || !pset.size ? "" : ` (${periods.join(", ")})`) });
        target.push(...feats);
      });
    }
    const periodFeats = kinds.length ? [] : g.features.filter((f) => pset.has(f.properties.p));
    if (periodFeats.length) {
      fill(periodFeats, (f) => meta.legend[f.properties.p].color);
      [...pset].sort((a, b) => a - b).forEach((i) => legend.push({ color: meta.legend[i].color, label: `${names[i]} bedrock` }));
    }
    // examples on land the layers cover (the UK and Ireland; not the Isle of Man or the Channel Islands)
    const cover = parts(g.features);
    const tparts = parts(target.concat(periodFeats));
    const covered = points.filter(([lat, lon]) => on(cover, lat, lon));
    const n = covered.filter(([lat, lon]) => on(tparts, lat, lon)).length;
    return { on: n, total: covered.length, all: points.length, legend, sources: meta.sources };
  }

  return { draw, inPoly };
})();
