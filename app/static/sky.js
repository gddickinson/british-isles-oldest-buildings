// Sun and moon on the horizon (roadmap SK1): the browser mirror of bidb/sky.py (same formulas; tests/test_sky.py
// compares the two). Rising and setting are the first and last gleam of the upper limb with standard refraction.
const Sky = (() => {
  const R = Math.PI / 180;
  const SUN_RADIUS = 0.266, MOON_RADIUS = 0.259, MOON_PARALLAX = 0.951, MOON_INCLINATION = 5.145;
  const SUN_EVENTS = { equinox: 0, summer_solstice: 90, winter_solstice: 270, imbolc: 315, beltane: 45, lughnasa: 135, samhain: 225 };
  const NAMES = {
    summer_solstice: "Midsummer (summer solstice)", winter_solstice: "Midwinter (winter solstice)", equinox: "Equinoxes",
    imbolc: "Imbolc (early February)", beltane: "Beltane (early May)", lughnasa: "Lughnasa (early August)",
    samhain: "Samhain (early November)", major_north: "Major lunar standstill, north", major_south: "Major lunar standstill, south",
    minor_north: "Minor lunar standstill, north", minor_south: "Minor lunar standstill, south",
  };

  const SHORT = { summer_solstice: "Midsummer", winter_solstice: "Midwinter", equinox: "Equinoxes", imbolc: "Imbolc",
    beltane: "Beltane", lughnasa: "Lughnasa", samhain: "Samhain", major_north: "Moon, major standstill N",
    major_south: "Moon, major standstill S", minor_north: "Moon, minor standstill N", minor_south: "Moon, minor standstill S" };
  function obliquity(year) {
    const t = (year - 2000) / 10000;
    const c = [-4680.93, -1.55, 1999.25, -51.38, -249.67, -39.05, 7.12, 27.87, 5.79, 2.45];
    return (84381.448 + c.reduce((s, k, i) => s + k * t ** (i + 1), 0)) / 3600;
  }
  function declination(body, event, year = 2000) {
    const eps = obliquity(year);
    if (body === "sun") return Math.asin(Math.sin(eps * R) * Math.sin(SUN_EVENTS[event] * R)) / R;
    const [size, side] = event.split("_");
    const d = size === "major" ? eps + MOON_INCLINATION : eps - MOON_INCLINATION;
    return side === "north" ? d : -d;
  }
  const refraction = (h) => 1 / Math.tan((h + 7.31 / (h + 4.4)) * R) / 60;
  const centreAltitude = (body, horizon = 0) => (body === "sun"
    ? horizon - refraction(horizon) - SUN_RADIUS
    : horizon - refraction(horizon) - MOON_RADIUS + MOON_PARALLAX * Math.cos(horizon * R));
  function azimuth(lat, dec, riseSet = "rise", body = "sun", horizon = 0) {
    const h = centreAltitude(body, horizon) * R;
    const c = (Math.sin(dec * R) - Math.sin(lat * R) * Math.sin(h)) / (Math.cos(lat * R) * Math.cos(h));
    if (Math.abs(c) > 1) return null;
    const a = Math.acos(c) / R;
    return riseSet === "rise" ? a : 360 - a;
  }
  function declinationOf(lat, az, body = "sun", horizon = 0) {
    const h = centreAltitude(body, horizon) * R;
    return Math.asin(Math.sin(lat * R) * Math.sin(h) + Math.cos(lat * R) * Math.cos(h) * Math.cos(az * R)) / R;
  }
  const eventAzimuth = (lat, body, event, riseSet, year = 2000, horizon = 0) =>
    azimuth(lat, declination(body, event, year), riseSet, body, horizon);

  // Dates: Julian days from JavaScript dates (UT).
  const jdOf = (date) => date.getTime() / 86400000 + 2440587.5;
  const dateOf = (jd) => new Date((jd - 2440587.5) * 86400000);
  function sunLongitude(jd) {
    const t = (jd - 2451545) / 36525;
    const l0 = 280.46646 + 36000.76983 * t, m = (357.52911 + 35999.05029 * t) * R;
    const c = (1.914602 - 0.004817 * t) * Math.sin(m) + 0.019993 * Math.sin(2 * m) + 0.000289 * Math.sin(3 * m);
    return (((l0 + c - 0.00569 - 0.00478 * Math.sin((125.04 - 1934.136 * t) * R)) % 360) + 360) % 360;
  }
  function sunDeclination(jd) {
    const t = (jd - 2451545) / 36525;
    const eps = obliquity(2000 + t * 100) + 0.00256 * Math.cos((125.04 - 1934.136 * t) * R);
    return Math.asin(Math.sin(eps * R) * Math.sin(sunLongitude(jd) * R)) / R;
  }
  const wrap = (x) => ((x % 360) + 360) % 360;
  const nextSunEvent = (event, jd) => nextLongitude(SUN_EVENTS[event], jd);
  function nextLongitude(target, jd) {
    let g = jd + wrap(target - sunLongitude(jd)) / 360 * 365.2422;
    for (let i = 0; i < 6; i++) g += (wrap(target - sunLongitude(g) + 180) - 180) / 360 * 365.2422;
    return g > jd ? g : nextLongitude(target, jd + 1);
  }
  function equationOfTime(jd) {
    const t = (jd - 2451545) / 36525, eps = obliquity(2000 + t * 100) * R;
    const l0 = wrap(280.46646 + 36000.76983 * t) * R, m = (357.52911 + 35999.05029 * t) * R;
    const e = 0.016708634 - 0.000042037 * t, y = Math.tan(eps / 2) ** 2;
    return 4 * (y * Math.sin(2 * l0) - 2 * e * Math.sin(m) + 4 * e * y * Math.sin(m) * Math.cos(2 * l0)
      - 0.5 * y * y * Math.sin(4 * l0) - 1.25 * e * e * Math.sin(2 * m)) / R;
  }
  // Julian days of sunrise and sunset on the day starting at jd0 (0h UT); lon east positive; null if none.
  function riseSetTimes(lat, lon, jd0, horizon = 0) {
    return [-1, 1].map((sign) => {
      let t = jd0 + 0.5 - lon / 360;
      for (let i = 0; i < 2; i++) {
        const dec = sunDeclination(t) * R, h = centreAltitude("sun", horizon) * R;
        const c = (Math.sin(h) - Math.sin(lat * R) * Math.sin(dec)) / (Math.cos(lat * R) * Math.cos(dec));
        if (Math.abs(c) > 1) return null;
        t = jd0 + (720 - 4 * lon - equationOfTime(t)) / 1440 + sign * Math.acos(c) / R * 4 / 1440;
      }
      return t;
    });
  }
  const nodeLongitude = (jd) => wrap(125.04452 - 1934.136261 * (jd - 2451545) / 36525);
  function nextStandstill(kind, jd) {
    const days = wrap(nodeLongitude(jd) - (kind === "major" ? 0 : 180)) / 1934.136261 * 36525;
    return jd + (days || 6798.38);
  }
  // The next date of an event: a solar event's day, or the year of the moon's next standstill (a season of about a
  // year either side, when the moon reaches its extreme rising points each month).
  function next(body, event, from = new Date()) {
    const jd = jdOf(from);
    if (body === "sun") return { date: dateOf(nextSunEvent(event, jd)) };
    const kind = event.split("_")[0];
    const last = nextStandstill(kind, jd - 6798.38);
    if (jd - last < 365) return { date: dateOf(last), season: true };
    return { date: dateOf(nextStandstill(kind, jd)) };
  }
  // Dates in a year when the sun rises (or sets) at an azimuth: none, or one or two.
  function sunDatesAt(lat, az, year = new Date().getUTCFullYear()) {
    const dec = declinationOf(lat, az), out = [];
    const start = jdOf(new Date(Date.UTC(year, 0, 1)));
    let prev = sunDeclination(start) - dec;
    for (let d = 1; d <= 366; d++) {
      const cur = sunDeclination(start + d) - dec;
      if (prev * cur <= 0 && prev !== cur) out.push(dateOf(start + d - 1 + prev / (prev - cur)));
      prev = cur;
    }
    return out;
  }
  const compass = (az) => ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE", "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"][Math.round(wrap(az) / 22.5) % 16];

  return { SUN_EVENTS, NAMES, SHORT, obliquity, declination, refraction, centreAltitude, azimuth, declinationOf, eventAzimuth,
    jdOf, dateOf, sunLongitude, sunDeclination, nextSunEvent, nextLongitude, equationOfTime, riseSetTimes, nodeLongitude, nextStandstill, next, sunDatesAt, compass };
})();
if (typeof module !== "undefined") module.exports = Sky;
