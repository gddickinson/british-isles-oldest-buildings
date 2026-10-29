// Where the sun, moon and stars stand in the sky of any date (the Stonehenge model, /stonehenge): altitude and
// azimuth seen from a place, for years back to the Neolithic. Needs sky.js (obliquity, sun's longitude).
//   - time: local mean solar time at the place (no clocks then); universal time = local - longitude / 15 h, and the
//     moon and sun move in terrestrial time = universal time + ΔT (Espenak and Meeus 2006 polynomials: ~16 h by
//     2500 BC, uncertain by about an hour then, which moves the moon by up to half a degree);
//   - dates in the proleptic Gregorian calendar, astronomical years (0 = 1 BC, -2499 = 2500 BC);
//   - moon: Meeus, Astronomical Algorithms ch. 47, the main terms (within ~0.01° of the full series today), with
//     parallax for the place; sun: sky.js (Meeus ch. 25, low precision);
//   - stars: J2000 positions moved by their proper motions, then precessed to the date (Lieske 1977 angles, Meeus
//     ch. 21; a few arcminutes out by 2500 BC). Nutation and aberration left out.
const SkyPos = (() => {
  const R = Math.PI / 180;
  const wrap = (x) => ((x % 360) + 360) % 360;

  // Julian day of a proleptic Gregorian date (astronomical year) at `hours` UT (Meeus ch. 7).
  function julianDay(year, month, day, hours = 0) {
    let y = year, m = month;
    if (m <= 2) { y -= 1; m += 12; }
    const a = Math.floor(y / 100), b = 2 - a + Math.floor(a / 4);
    return Math.floor(365.25 * (y + 4716)) + Math.floor(30.6001 * (m + 1)) + day + b - 1524.5 + hours / 24;
  }
  // Proleptic Gregorian date of a Julian day (Meeus ch. 7) → {year, month, day, hours}.
  function calendarDate(jd) {
    const z = Math.floor(jd + 0.5), f = jd + 0.5 - z;
    const al = Math.floor((z - 1867216.25) / 36524.25), a = z + 1 + al - Math.floor(al / 4);
    const b = a + 1524, c = Math.floor((b - 122.1) / 365.25), d = Math.floor(365.25 * c), e = Math.floor((b - d) / 30.6001);
    const day = b - d - Math.floor(30.6001 * e), month = e < 14 ? e - 1 : e - 13;
    return { year: month > 2 ? c - 4716 : c - 4715, month, day, hours: f * 24 };
  }

  // ΔT = TT - UT in seconds (Espenak and Meeus 2006, NASA eclipse pages).
  function deltaT(y) {
    const poly = (t, cs) => cs.reduce((s, c, i) => s + c * t ** i, 0);
    if (y < -500 || y >= 2150) return -20 + 32 * ((y - 1820) / 100) ** 2;
    if (y < 500) return poly(y / 100, [10583.6, -1014.41, 33.78311, -5.952053, -0.1798452, 0.022174192, 0.0090316521]);
    if (y < 1600) return poly((y - 1000) / 100, [1574.2, -556.01, 71.23472, 0.319781, -0.8503463, -0.005050998, 0.0083572073]);
    if (y < 1700) return poly(y - 1600, [120, -0.9808, -0.01532, 1 / 7129]);
    if (y < 1800) return poly(y - 1700, [8.83, 0.1603, -0.0059285, 0.00013336, -1 / 1174000]);
    if (y < 1860) return poly(y - 1800, [13.72, -0.332447, 0.0068612, 0.0041116, -0.00037436, 0.0000121272, -0.0000001699, 0.000000000875]);
    if (y < 1900) return poly(y - 1860, [7.62, 0.5737, -0.251754, 0.01680668, -0.0004473624, 1 / 233174]);
    if (y < 1920) return poly(y - 1900, [-2.79, 1.494119, -0.0598939, 0.0061966, -0.000197]);
    if (y < 1941) return poly(y - 1920, [21.2, 0.84493, -0.0761, 0.0020936]);
    if (y < 1961) return poly(y - 1950, [29.07, 0.407, -1 / 233, 1 / 2547]);
    if (y < 1986) return poly(y - 1975, [45.45, 1.067, -1 / 260, -1 / 718]);
    if (y < 2005) return poly(y - 2000, [63.86, 0.3345, -0.060374, 0.0017275, 0.000651814, 0.00002373599]);
    if (y < 2050) return poly(y - 2000, [62.92, 0.32217, 0.005589]);
    return -20 + 32 * ((y - 1820) / 100) ** 2 - 0.5628 * (2150 - y);
  }

  // Moon (Meeus ch. 47): [D, M, M', F, Σl (1e-6°), Σr (m)]; E applied for |M| = 1, E² for |M| = 2.
  const LR = [[0, 0, 1, 0, 6288774, -20905355], [2, 0, -1, 0, 1274027, -3699111], [2, 0, 0, 0, 658314, -2955968],
    [0, 0, 2, 0, 213618, -569925], [0, 1, 0, 0, -185116, 48888], [0, 0, 0, 2, -114332, -3149], [2, 0, -2, 0, 58793, 246158],
    [2, -1, -1, 0, 57066, -152138], [2, 0, 1, 0, 53322, -170733], [2, -1, 0, 0, 45758, -204586], [0, 1, -1, 0, -40923, -129620],
    [1, 0, 0, 0, -34720, 108743], [0, 1, 1, 0, -30383, 104755], [2, 0, 0, -2, 15327, 10321], [0, 0, 1, 2, -12528, 0],
    [0, 0, 1, -2, 10980, 79661], [4, 0, -1, 0, 10675, -34782], [0, 0, 3, 0, 10034, -23210], [4, 0, -2, 0, 8548, -21636],
    [2, 1, -1, 0, -7888, 24208], [2, 1, 0, 0, -6766, 30824], [1, 0, -1, 0, -5163, -8379], [1, 1, 0, 0, 4987, -16675],
    [2, -1, 1, 0, 4036, -12831], [2, 0, 2, 0, 3994, -10445], [4, 0, 0, 0, 3861, -11650], [2, 0, -3, 0, 3665, 14403],
    [0, 1, -2, 0, -2689, -7003], [2, 0, -1, 2, -2602, 0], [2, -1, -2, 0, 2390, 10056], [1, 0, 1, 0, -2348, 6322],
    [2, -2, 0, 0, 2236, -9884], [0, 1, 2, 0, -2120, 5751], [0, 2, 0, 0, -2069, 0]];
  const B = [[0, 0, 0, 1, 5128122], [0, 0, 1, 1, 280602], [0, 0, 1, -1, 277693], [2, 0, 0, -1, 173237],
    [2, 0, -1, 1, 55413], [2, 0, -1, -1, 46271], [2, 0, 0, 1, 32573], [0, 0, 2, 1, 17198], [2, 0, 1, -1, 9266],
    [0, 0, 2, -1, 8822], [2, -1, 0, -1, 8216], [2, 0, -2, -1, 4324], [2, 0, 1, 1, 4200], [2, 1, 0, -1, -3359],
    [2, -1, -1, 1, 2463], [2, -1, 0, 1, 2211], [2, -1, -1, -1, 2065], [0, 1, -1, -1, -1870], [4, 0, -1, -1, 1828],
    [0, 1, 0, 1, -1794]];
  // Geocentric ecliptic longitude and latitude (degrees, mean equinox of date) and distance (km); jde in TT.
  function moon(jde) {
    const t = (jde - 2451545) / 36525;
    const lp = 218.3164477 + 481267.88123421 * t - 0.0015786 * t * t + t ** 3 / 538841 - t ** 4 / 65194000;
    const d = 297.8501921 + 445267.1114034 * t - 0.0018819 * t * t + t ** 3 / 545868 - t ** 4 / 113065000;
    const m = 357.5291092 + 35999.0502909 * t - 0.0001536 * t * t + t ** 3 / 24490000;
    const mp = 134.9633964 + 477198.8675055 * t + 0.0087414 * t * t + t ** 3 / 69699 - t ** 4 / 14712000;
    const f = 93.272095 + 483202.0175233 * t - 0.0036539 * t * t - t ** 3 / 3526000 + t ** 4 / 863310000;
    const a1 = 119.75 + 131.849 * t, a2 = 53.09 + 479264.29 * t, a3 = 313.45 + 481266.484 * t;
    const e = 1 - 0.002516 * t - 0.0000074 * t * t;
    const ef = (k) => (Math.abs(k) === 1 ? e : Math.abs(k) === 2 ? e * e : 1);
    let sl = 0, sr = 0, sb = 0;
    for (const [cd, cm, cmp, cf, l, r] of LR) {
      const arg = (cd * d + cm * m + cmp * mp + cf * f) * R;
      sl += l * ef(cm) * Math.sin(arg);
      sr += r * ef(cm) * Math.cos(arg);
    }
    for (const [cd, cm, cmp, cf, b] of B) sb += b * ef(cm) * Math.sin((cd * d + cm * m + cmp * mp + cf * f) * R);
    sl += 3958 * Math.sin(a1 * R) + 1962 * Math.sin((lp - f) * R) + 318 * Math.sin(a2 * R);
    sb += -2235 * Math.sin(lp * R) + 382 * Math.sin(a3 * R) + 175 * Math.sin((a1 - f) * R) + 175 * Math.sin((a1 + f) * R)
      + 127 * Math.sin((lp - mp) * R) - 115 * Math.sin((lp + mp) * R);
    return { lon: wrap(lp + sl / 1e6), lat: sb / 1e6, km: 385000.56 + sr / 1000 };
  }

  // Ecliptic → equatorial (degrees) for the obliquity eps.
  function equatorial(lon, lat, eps) {
    const l = lon * R, b = lat * R, e = eps * R;
    const ra = Math.atan2(Math.sin(l) * Math.cos(e) - Math.tan(b) * Math.sin(e), Math.cos(l));
    const dec = Math.asin(Math.sin(b) * Math.cos(e) + Math.cos(b) * Math.sin(e) * Math.sin(l));
    return { ra: wrap(ra / R), dec: dec / R };
  }
  // Mean sidereal time at Greenwich (degrees), jd in UT (Meeus 12.4).
  function siderealTime(jd) {
    const t = (jd - 2451545) / 36525;
    return wrap(280.46061837 + 360.98564736629 * (jd - 2451545) + 0.000387933 * t * t - t ** 3 / 38710000);
  }
  // Altitude and azimuth (degrees, azimuth from north through east) of ra/dec at local sidereal time lst.
  function horizontal(ra, dec, lat, lst) {
    const h = (lst - ra) * R, d = dec * R, p = lat * R;
    const alt = Math.asin(Math.sin(p) * Math.sin(d) + Math.cos(p) * Math.cos(d) * Math.cos(h));
    const az = Math.atan2(Math.sin(h), Math.cos(h) * Math.sin(p) - Math.tan(d) * Math.cos(p));
    return { alt: alt / R, az: wrap(az / R + 180) };
  }
  // Standard refraction (degrees) for a true altitude (Sæmundsson), as seen.
  const refraction = (alt) => (alt < -2 ? 0 : 1.02 / Math.tan((alt + 10.3 / (alt + 5.11)) * R) / 60);

  // Precession of J2000 equatorial coordinates (degrees) to the equinox of jde (Meeus 21.2-21.4).
  function precess(ra, dec, jde) {
    const t = (jde - 2451545) / 36525;
    const zeta = (2306.2181 * t + 0.30188 * t * t + 0.017998 * t ** 3) / 3600 * R;
    const z = (2306.2181 * t + 1.09468 * t * t + 0.018203 * t ** 3) / 3600 * R;
    const th = (2004.3109 * t - 0.42665 * t * t - 0.041833 * t ** 3) / 3600 * R;
    const a = ra * R, d = dec * R;
    const A = Math.cos(d) * Math.sin(a + zeta);
    const Bq = Math.cos(th) * Math.cos(d) * Math.cos(a + zeta) - Math.sin(th) * Math.sin(d);
    const C = Math.sin(th) * Math.cos(d) * Math.cos(a + zeta) + Math.cos(th) * Math.sin(d);
    return { ra: wrap((Math.atan2(A, Bq) + z) / R), dec: Math.asin(Math.max(-1, Math.min(1, C))) / R };
  }

  // Everything for one moment: local mean solar time `hours` on a proleptic Gregorian date at lat/lon (east +).
  function at(year, month, day, hours, lat, lon) {
    const jd = julianDay(year, month, day, hours - lon / 15);           // UT
    const jde = jd + deltaT(year + (month - 0.5) / 12) / 86400;          // TT
    const t = (jde - 2451545) / 36525;
    const eps = Sky.obliquity(2000 + t * 100);
    const lst = wrap(siderealTime(jd) + lon);
    const sunLon = Sky.sunLongitude(jde);
    const s = equatorial(sunLon, 0, eps);
    const sun = horizontal(s.ra, s.dec, lat, lst);
    const mo = moon(jde), mq = equatorial(mo.lon, mo.lat, eps);
    const mg = horizontal(mq.ra, mq.dec, lat, lst);
    const parallax = Math.asin(6378.14 / mo.km) / R;                    // seen from the ground, not the earth's centre
    const moonAlt = mg.alt - parallax * Math.cos(mg.alt * R);
    const elong = Math.acos(Math.cos((mo.lon - sunLon) * R) * Math.cos(mo.lat * R)) / R;
    return {
      jd, jde, lst, eps, deltaT: (jde - jd) * 86400,
      sun: { alt: sun.alt, az: sun.az, seen: sun.alt + refraction(sun.alt), ra: s.ra, dec: s.dec, lon: sunLon },
      moon: { alt: moonAlt, az: mg.az, seen: moonAlt + refraction(moonAlt), ra: mq.ra, dec: mq.dec, km: mo.km,
        lon: mo.lon, lat: mo.lat, phase: (1 - Math.cos(elong * R)) / 2, waxing: wrap(mo.lon - sunLon) < 180 },
    };
  }

  // Stars: rows [ra, dec (J2000, degrees), pmRa*cos(dec), pmDec (arcsec a year), magnitude, B-V, name?] → alt/az now.
  function star(row, jde, lat, lst) {
    const years = (jde - 2451545) / 365.25;
    const dec0 = row[1] + row[3] * years / 3600;
    const ra0 = row[0] + row[2] * years / 3600 / Math.max(Math.cos(row[1] * R), 1e-6);
    const p = precess(ra0, Math.max(-90, Math.min(90, dec0)), jde);
    return horizontal(p.ra, p.dec, lat, lst);
  }

  return { julianDay, calendarDate, deltaT, moon, equatorial, siderealTime, horizontal, refraction, precess, at, star };
})();
if (typeof module !== "undefined") module.exports = SkyPos;
