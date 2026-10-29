// Ordnance Survey and Irish grid references (roadmap LD2): the browser mirror of bidb/osgrid.py (same formulas;
// tests/test_osgrid.py compares the two). Seven-parameter Helmert shifts, so within a few metres of OSTN15.
const OSGrid = (() => {
  const GB = { a: 6377563.396, b: 6356256.909, F0: 0.9996012717, lat0: 49, lon0: -2, E0: 400000, N0: -100000,
    helmert: [-446.448, 125.157, -542.060, 20.4894, -0.1502, -0.2470, -0.8421] };
  const IE = { a: 6377340.189, b: 6356034.447, F0: 1.000035, lat0: 53.5, lon0: -8, E0: 200000, N0: 250000,
    helmert: [-482.530, 130.596, -564.557, -8.150, 1.042, 0.214, 0.631] };
  const WGS = [6378137.0, 6356752.314245];
  const R = Math.PI / 180;
  // The island of Ireland, coarsely (lon, lat): Rathlin and Inishtrahull inside, Kintyre, Islay, Man and the Smalls out
  const IRELAND = [[-11.0, 51.2], [-6.1, 51.2], [-6.05, 52.5], [-5.85, 53.3], [-5.3, 54.2], [-5.3, 54.85],
    [-6.0, 55.2], [-6.05, 55.36], [-7.0, 55.5], [-11.0, 55.5]];

  function arc(lat, p) {
    const { a, b, F0 } = p, lat0 = p.lat0 * R, n = (a - b) / (a + b);
    return b * F0 * ((1 + n + 5 / 4 * n ** 2 + 5 / 4 * n ** 3) * (lat - lat0)
      - (3 * n + 3 * n ** 2 + 21 / 8 * n ** 3) * Math.sin(lat - lat0) * Math.cos(lat + lat0)
      + (15 / 8 * n ** 2 + 15 / 8 * n ** 3) * Math.sin(2 * (lat - lat0)) * Math.cos(2 * (lat + lat0))
      - 35 / 24 * n ** 3 * Math.sin(3 * (lat - lat0)) * Math.cos(3 * (lat + lat0)));
  }

  function radii(lat, p) {
    const { a, b, F0 } = p, e2 = 1 - b * b / (a * a), s = Math.sin(lat);
    const nu = a * F0 / Math.sqrt(1 - e2 * s * s), rho = a * F0 * (1 - e2) / (1 - e2 * s * s) ** 1.5;
    return [nu, rho, nu / rho - 1];
  }

  function tmInverse(E, N, p) {
    let lat = p.lat0 * R, M = 0;
    do { lat = (N - p.N0 - M) / (p.a * p.F0) + lat; M = arc(lat, p); } while (Math.abs(N - p.N0 - M) >= 0.00001);
    const c = Math.cos(lat), t = Math.tan(lat), [nu, rho, eta2] = radii(lat, p), dE = E - p.E0;
    const VII = t / (2 * rho * nu);
    const VIII = t / (24 * rho * nu ** 3) * (5 + 3 * t * t + eta2 - 9 * t * t * eta2);
    const IX = t / (720 * rho * nu ** 5) * (61 + 90 * t * t + 45 * t ** 4);
    const X = 1 / (c * nu), XI = 1 / (c * 6 * nu ** 3) * (nu / rho + 2 * t * t);
    const XII = 1 / (c * 120 * nu ** 5) * (5 + 28 * t * t + 24 * t ** 4);
    const XIIA = 1 / (c * 5040 * nu ** 7) * (61 + 662 * t * t + 1320 * t ** 4 + 720 * t ** 6);
    return [lat - VII * dE ** 2 + VIII * dE ** 4 - IX * dE ** 6,
      p.lon0 * R + X * dE - XI * dE ** 3 + XII * dE ** 5 - XIIA * dE ** 7];
  }

  function tmForward(lat, lon, p) {
    const s = Math.sin(lat), c = Math.cos(lat), t = Math.tan(lat), [nu, rho, eta2] = radii(lat, p);
    const dl = lon - p.lon0 * R;
    const I = arc(lat, p) + p.N0, II = nu / 2 * s * c, III = nu / 24 * s * c ** 3 * (5 - t * t + 9 * eta2);
    const IIIA = nu / 720 * s * c ** 5 * (61 - 58 * t * t + t ** 4), IV = nu * c, V = nu / 6 * c ** 3 * (nu / rho - t * t);
    const VI = nu / 120 * c ** 5 * (5 - 18 * t * t + t ** 4 + 14 * eta2 - 58 * t * t * eta2);
    return [p.E0 + IV * dl + V * dl ** 3 + VI * dl ** 5, I + II * dl ** 2 + III * dl ** 4 + IIIA * dl ** 6];
  }

  function toCart(lat, lon, a, b) {
    const e2 = 1 - b * b / (a * a), nu = a / Math.sqrt(1 - e2 * Math.sin(lat) ** 2);
    return [nu * Math.cos(lat) * Math.cos(lon), nu * Math.cos(lat) * Math.sin(lon), (1 - e2) * nu * Math.sin(lat)];
  }

  // WGS84 -> local datum (the parameters' direction); sign -1: the reverse
  function shift([x, y, z], helmert, sign = 1) {
    const [tx, ty, tz, s0, rx0, ry0, rz0] = helmert.map((v) => sign * v);
    const s = s0 * 1e-6, [rx, ry, rz] = [rx0, ry0, rz0].map((r) => r / 3600 * R);
    return [tx + (1 + s) * x - rz * y + ry * z, ty + rz * x + (1 + s) * y - rx * z, tz - ry * x + rx * y + (1 + s) * z];
  }

  function fromCart([x, y, z], a, b) {
    const e2 = 1 - b * b / (a * a), pp = Math.hypot(x, y);
    let lat = Math.atan2(z, pp * (1 - e2));
    for (let i = 0; i < 10; i++) {
      const nu = a / Math.sqrt(1 - e2 * Math.sin(lat) ** 2);
      lat = Math.atan2(z + e2 * nu * Math.sin(lat), pp);
    }
    return [lat, Math.atan2(y, x)];
  }

  function letterIndex(c) { return c.charCodeAt(0) - 65 - (c > "I" ? 1 : 0); }
  function letter(i) { return String.fromCharCode(65 + i + (i > 7 ? 1 : 0)); }

  // Grid reference -> [easting, northing] (centre of the square it names), or null
  function parse(ref, irish = false) {
    ref = String(ref || "").replace(/ /g, " ").replace(/\s+/g, " ").trim().toUpperCase()
      .replace(/^([A-Z])0(?=\s|\d)/, "$1O");
    const m = ref.match(/^([A-HJ-Z]{1,2})\s*(\d+)\s*(\d*)$/);
    if (!m) return null;
    const digits = m[2] + m[3];
    if (digits.length % 2 || !digits || m[1].length !== (irish ? 1 : 2)) return null;
    const half = digits.length / 2, unit = 10 ** (5 - half);
    let e0, n0;
    if (irish) {
      const i = letterIndex(m[1]);
      e0 = (i % 5) * 100000; n0 = (4 - Math.floor(i / 5)) * 100000;
    } else {
      const [a, b] = [...m[1]].map(letterIndex);
      e0 = (((a - 2) % 5 + 5) % 5 * 5 + b % 5) * 100000;
      n0 = (19 - Math.floor(a / 5) * 5 - Math.floor(b / 5)) * 100000;
    }
    return [e0 + Number(digits.slice(0, half)) * unit + unit / 2, n0 + Number(digits.slice(half)) * unit + unit / 2];
  }

  function toLatLon(ref, irish = false) {
    const en = parse(ref, irish);
    if (!en) return null;
    const p = irish ? IE : GB;
    const [lat, lon] = fromCart(shift(toCart(...tmInverse(...en, p), p.a, p.b), p.helmert, -1), ...WGS);
    return [lat / R, lon / R];
  }

  function toEN(lat, lon, irish = false) {
    const p = irish ? IE : GB;
    return tmForward(...fromCart(shift(toCart(lat * R, lon * R, ...WGS), p.helmert), p.a, p.b), p);
  }

  // [easting, northing] -> "SU 12245 42199" (digits 2-10, truncated as the OS does), or null off the grid
  function format(E, N, irish = false, digits = 10) {
    const e100 = Math.floor(E / 100000), n100 = Math.floor(N / 100000);
    let letters;
    if (irish) {
      if (!(e100 >= 0 && e100 < 5 && n100 >= 0 && n100 < 5)) return null;
      letters = letter((4 - n100) * 5 + e100);
    } else {
      if (!(e100 >= 0 && e100 < 7 && n100 >= 0 && n100 < 13)) return null;
      letters = letter((19 - n100) - (19 - n100) % 5 + Math.floor((e100 + 10) / 5)) + letter((19 - n100) * 5 % 25 + e100 % 5);
    }
    const half = digits / 2, unit = 10 ** (5 - half);
    const pad = (v) => String(Math.floor((v % 100000) / unit)).padStart(half, "0");
    return `${letters} ${pad(E)} ${pad(N)}`;
  }

  function fromLatLon(lat, lon, irish = false, digits = 10) { return format(...toEN(lat, lon, irish), irish, digits); }

  function inIreland(lat, lon) {
    let inside = false;
    for (let i = 0, j = IRELAND.length - 1; i < IRELAND.length; j = i++) {
      const [x, y] = IRELAND[i], [xj, yj] = IRELAND[j];
      if ((y > lat) !== (yj > lat) && lon < (xj - x) * (lat - y) / (yj - y) + x) inside = !inside;
    }
    return inside;
  }

  // {ref, grid: "OS" | "Irish"} of the grid in use at a point (at sea off the other grid's squares, that one);
  // null off both (the Channel Islands, abroad)
  function forPoint(lat, lon, digits = 10) {
    const irish = inIreland(lat, lon);
    for (const grid of [irish, !irish]) {
      const ref = fromLatLon(lat, lon, grid, digits);
      if (ref) return { ref, grid: grid ? "Irish" : "OS" };
    }
    return null;
  }

  return { parse, toLatLon, toEN, format, fromLatLon, inIreland, forPoint };
})();
if (typeof module !== "undefined") module.exports = OSGrid;
