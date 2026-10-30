// Festivals (page /festivals): icons, the next date of each festival (fixed day, days from Easter, a solstice or
// equinox from Sky.next), and the wheel of the year drawn as SVG. Used by festivals.js.
const Festivals = (() => {
  const ICON = { christmas: "🎄", "new-year": "🎆", "burns-night": "📜", imbolc: "🕯️", valentine: "💌", "st-david": "🌼",
    "st-patrick": "☘️", easter: "🥚", "st-george": "🐉", "may-day": "🌸", midsummer: "☀️", lammas: "🌾",
    michaelmas: "🍂", halloween: "🎃", "bonfire-night": "🔥", "st-andrew": "✖️" };
  const SEASON = { winter: ["❄️", "#3a6ea5"], spring: ["🌱", "#4c9a2a"], summer: ["☀️", "#d4a017"], autumn: ["🍁", "#c0612b"] };
  const KIND = { history: "📜 History", custom: "🎭 Custom", legend: "🐉 Legend", food: "🍽 Food and drink",
    oldest: "🏆 Oldest", sky: "🌅 Sky", curiosity: "🔎 Curiosity" };
  const DAY = 86400000;

  // Easter Sunday in the Gregorian calendar (the anonymous algorithm, Meeus ch. 8)
  function easter(y) {
    const a = y % 19, b = Math.floor(y / 100), c = y % 100, d = Math.floor(b / 4), e = b % 4, f = Math.floor((b + 8) / 25);
    const g = Math.floor((b - f + 1) / 3), h = (19 * a + b - d - g + 15) % 30, i = Math.floor(c / 4), k = c % 4;
    const l = (32 + 2 * e + 2 * i - h - k) % 7, m = Math.floor((a + 11 * h + 22 * l) / 451);
    const month = Math.floor((h + l - 7 * m + 114) / 31), day = ((h + l - 7 * m + 114) % 31) + 1;
    return new Date(y, month - 1, day);
  }

  // The festival's date in year y (local midnight), or null when its rule is not one of the kinds below.
  function inYear(w, y) {
    if (w.date) { const [m, d] = w.date.split("-").map(Number); return new Date(y, m - 1, d); }
    if (Number.isInteger(w.easter)) { const e = easter(y); return new Date(y, e.getMonth(), e.getDate() + w.easter); }
    if (w.sun && typeof Sky !== "undefined") {
      const t = Sky.next("sun", w.sun, new Date(y, 0, 1)).date;
      return t && t.getFullYear() === y ? new Date(y, t.getMonth(), t.getDate()) : null;
    }
    return null;
  }

  // The next date on or after today (an equinox gives the next of the two)
  function next(w, from = new Date()) {
    const today = new Date(from.getFullYear(), from.getMonth(), from.getDate());
    if (w.sun && typeof Sky !== "undefined") {
      const t = Sky.next("sun", w.sun, new Date(today.getTime() - DAY / 2)).date;
      return t ? new Date(t.getFullYear(), t.getMonth(), t.getDate()) : null;
    }
    for (const y of [today.getFullYear(), today.getFullYear() + 1]) {
      const d = inYear(w, y);
      if (d && d >= today) return d;
    }
    return null;
  }

  const daysUntil = (d, from = new Date()) => Math.round((d - new Date(from.getFullYear(), from.getMonth(), from.getDate())) / DAY);
  function untilText(d) {
    if (!d) return "";
    const n = daysUntil(d);
    return n === 0 ? "today!" : n === 1 ? "tomorrow" : `in ${n} days`;
  }
  const fmt = (d) => d ? d.toLocaleDateString(undefined, { weekday: "short", day: "numeric", month: "long", year: "numeric" }) : "";

  // Wheel of the year: months round a circle (January at the top, clockwise), each festival a dot at its next date,
  // today as a hand. href(f) gives each dot's link.
  function wheel(svg, festivals, href) {
    const now = new Date(), y = now.getFullYear(), start = new Date(y, 0, 1), len = (new Date(y + 1, 0, 1) - start) / DAY;
    const ang = (d) => {
      const doy = ((d - new Date(d.getFullYear(), 0, 1)) / DAY) / len;
      return doy * 2 * Math.PI - Math.PI / 2;
    };
    const pt = (a, r) => [(Math.cos(a) * r).toFixed(1), (Math.sin(a) * r).toFixed(1)];
    let out = "";
    const seasons = [["winter", 11, 2], ["spring", 2, 5], ["summer", 5, 8], ["autumn", 8, 11]];
    seasons.forEach(([s, m0, m1]) => {
      const a0 = ang(new Date(y, m0, 1)), a1 = ang(new Date(m1 < m0 ? y + 1 : y, m1, 1)) + (m1 < m0 ? 2 * Math.PI : 0);
      const [x0, y0] = pt(a0, 150), [x1, y1] = pt(a1, 150), [x2, y2] = pt(a1, 104), [x3, y3] = pt(a0, 104);
      out += `<path class="fe-season" d="M${x0} ${y0} A150 150 0 0 1 ${x1} ${y1} L${x2} ${y2} A104 104 0 0 0 ${x3} ${y3}Z" fill="${SEASON[s][1]}"><title>${s}</title></path>`;
    });
    for (let m = 0; m < 12; m++) {
      const a = ang(new Date(y, m, 1)), [x0, y0] = pt(a, 104), [x1, y1] = pt(a, 150);
      const [lx, ly] = pt(ang(new Date(y, m, 15)), 90);
      out += `<line x1="${x0}" y1="${y0}" x2="${x1}" y2="${y1}" class="fe-tick"/>`
        + `<text x="${lx}" y="${ly}" class="fe-month" text-anchor="middle" dominant-baseline="middle">${new Date(y, m, 15).toLocaleDateString(undefined, { month: "short" })}</text>`;
    }
    const [hx, hy] = pt(ang(now), 150);
    out += `<line x1="0" y1="0" x2="${hx}" y2="${hy}" class="fe-hand"/><circle r="4" class="fe-hub"/>`
      + `<text y="22" text-anchor="middle" class="fe-today">today</text>`;
    festivals.forEach((f) => {
      const d = next(f.when);
      if (!d) return;
      const [x, yy] = pt(ang(d), 127);
      out += `<a href="${href(f)}" class="fe-dot"><title>${esc(f.title)}: ${fmt(d)}</title>`
        + `<circle cx="${x}" cy="${yy}" r="13"/><text x="${x}" y="${yy}" text-anchor="middle" dominant-baseline="central">${ICON[f.id] || "✦"}</text></a>`;
    });
    svg.innerHTML = out;
  }

  return { ICON, SEASON, KIND, easter, inYear, next, daysUntil, untilText, fmt, wheel };
})();
