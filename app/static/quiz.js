// "Guess the period": ten photographed buildings with well-supported dates; four period choices
// each (the right one and its neighbours, so it is not too easy). Best score kept in this browser.
(() => {
  const PERIODS = ["Neolithic", "Bronze Age", "Iron Age", "Roman Britain", "Early Medieval", "Norman", "High Medieval",
                   "Late Medieval", "Tudor", "Stuart", "Georgian", "Victorian", "Modern"];
  const SPAN = { Neolithic: "c. 4000–2500 BC", "Bronze Age": "2500–800 BC", "Iron Age": "800 BC–AD 43",
    "Roman Britain": "43–410", "Early Medieval": "410–1066", Norman: "1066–1154", "High Medieval": "1154–1307",
    "Late Medieval": "1307–1485", Tudor: "1485–1603", Stuart: "1603–1714", Georgian: "1714–1837",
    Victorian: "1837–1901", Modern: "1901–" };
  const BEST = "bi_quiz_best";
  const $ = (s) => document.querySelector(s);
  let qs = [], i = 0, score = 0;

  function choices(period) {          // four neighbouring periods, the answer at a random place among them
    const k = Math.max(0, PERIODS.indexOf(period));
    const lo = Math.max(0, Math.min(PERIODS.length - 4, k - Math.floor(Math.random() * 4)));
    return PERIODS.slice(lo, lo + 4);
  }

  function best() { try { return +localStorage.getItem(BEST) || 0; } catch (e) { return 0; } }
  function scoreLine() {
    $("#qz_score").textContent = `Question ${Math.min(i + 1, qs.length)} of ${qs.length} · score ${score}` + (best() ? ` · best ${best()}/10` : "");
  }

  function ask() {
    scoreLine();
    if (i >= qs.length) return finish();
    const q = qs[i];
    $("#qz_card").innerHTML = `<img src="${esc(q.image_thumb)}" alt="Photo of the building in question ${i + 1}">
      <p class="hint">${esc(q.category)} · ${esc(q.locality || q.nation || "")}</p>
      <div class="quiz-choices">${choices(q.period).map((p) => `<button class="btn ghost" data-p="${esc(p)}">${esc(p)}
        <span class="hint">${esc(SPAN[p] || "")}</span></button>`).join("")}</div>`;
  }

  function answer(p) {
    const q = qs[i], right = p === q.period;
    score += right;
    document.querySelectorAll(".quiz-choices button").forEach((b) => {
      b.disabled = true;
      b.classList.toggle("right", b.dataset.p === q.period);
      b.classList.toggle("wrong", b.dataset.p === p && !right);
    });
    $("#qz_card").insertAdjacentHTML("beforeend", `<div class="quiz-answer"><b>${right ? "Right!" : "Not quite."}</b>
      It is <a href="${buildingUrl(q.id)}" target="_blank" rel="noopener">${esc(q.name)}</a>, ${esc(q.date_text || "")} (${esc(q.period)}).
      <div class="stories-box" data-stories="${esc(q.id)}"></div>
      <button class="btn small" id="qz_next">${i + 1 < qs.length ? "Next" : "See your score"}</button></div>`);
    $("#qz_next").focus();
    i++;
    scoreLine();
  }

  function finish() {
    if (score > best()) { try { localStorage.setItem(BEST, score); } catch (e) { /* blocked */ } }
    $("#qz_card").innerHTML = `<h2>${score} out of ${qs.length}</h2><p>${score >= 8 ? "Excellent: you know your buildings."
      : score >= 5 ? "Good going." : "The periods blur together; the History page sets them out."}</p>`;
    scoreLine();
  }

  async function round() {
    qs = await api("/api/quiz?n=10").catch(() => []);
    i = 0; score = 0;
    if (!qs.length) { $("#qz_card").innerHTML = "<p class='empty'>No questions available.</p>"; return; }
    ask();
  }

  document.addEventListener("click", (e) => {
    const b = e.target.closest(".quiz-choices button[data-p]");
    if (b && !b.disabled) answer(b.dataset.p);
    if (e.target.id === "qz_next") ask();
  });
  document.addEventListener("DOMContentLoaded", () => { $("#qz_new").onclick = round; round(); });
})();
