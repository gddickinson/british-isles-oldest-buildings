// "On this day" (History page): battles, openings and foundations, births and deaths of the people
// in the catalogue on a day of the year; ‹ › step through the days. Hosted: data/on_this_day.json.
(() => {
  const MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August", "September",
                  "October", "November", "December"];
  const ICON = { born: "👶", died: "✝", "battle or event": "⚔", began: "▶", "founded or built": "🏛", opened: "🔑" };
  let date = new Date(), STATIC = null;

  async function forDay(m, d) {
    if (!IS_STATIC) return api(`/api/on_this_day?month=${m}&day=${d}`);
    STATIC = STATIC || fetch("data/on_this_day.json").then((r) => r.json()).catch(() => ({}));
    return ((await STATIC)[`${m}-${d}`] || []).map(([year, what, entity_kind, entity_id, name]) =>
      ({ year, what, entity_kind, entity_id, name }));
  }

  const yearText = (y) => (y < 0 ? `${-y} BC` : String(y));
  const link = (r) => r.entity_kind === "building"
    ? `<a href="${buildingUrl(r.entity_id)}">${esc(r.name)}</a>`
    : `<a href="#" data-otd="${esc(r.entity_kind)}" data-id="${esc(r.entity_id)}">${esc(r.name)}</a>`;

  async function show() {
    const m = date.getMonth() + 1, d = date.getDate();
    document.getElementById("otd_title").textContent = `On this day: ${d} ${MONTHS[m - 1]}`;
    const rows = await forDay(m, d).catch(() => []);
    const events = rows.filter((r) => r.entity_kind !== "person"), people = rows.filter((r) => r.entity_kind === "person");
    const li = (r) => `<li><span class="otd-year">${yearText(r.year)}</span> ${ICON[r.what] || "•"}
      ${r.what === "battle or event" ? "" : `<span class="hint">${esc(r.what)}</span>`} ${link(r)}</li>`;
    document.getElementById("otd_list").innerHTML = events.map(li).join("")
      + people.slice(0, Math.max(6, 14 - events.length)).map(li).join("")
      || "<li class='empty'>Nothing recorded for this day.</li>";
  }

  document.addEventListener("click", (e) => {
    const a = e.target.closest("[data-otd]");
    if (!a) return;
    e.preventDefault();
    if (a.dataset.otd === "place") openPlace(a.dataset.id); else openPerson(a.dataset.id);
  });
  const step = (n) => { date = new Date(date.getFullYear(), date.getMonth(), date.getDate() + n); show(); };
  document.addEventListener("DOMContentLoaded", () => {
    document.getElementById("otd_prev").onclick = () => step(-1);
    document.getElementById("otd_next").onclick = () => step(1);
    document.getElementById("otd_today").onclick = () => { date = new Date(); show(); };
    show();
  });
})();
