// Quiz page: a menu of quizzes (quiz_kinds.js), easy or hard, rounds of about ten questions, the best score of
// each quiz kept in this browser, and a review of the round at the end. ?q=<quiz> opens one directly.
(() => {
  const $ = (s) => document.querySelector(s);
  const KINDS = QuizKinds.KINDS;
  const store = { get(k, d) { try { return JSON.parse(localStorage.getItem(k)) ?? d; } catch (e) { return d; } },
                  set(k, v) { try { localStorage.setItem(k, JSON.stringify(v)); } catch (e) { /* blocked */ } } };
  let data = { buildings: [], pool: null }, kind = null, qs = [], i = 0, score = 0, log = [], picked = [];
  const hard = () => store.get("bi_quiz_hard", false);
  const bests = () => store.get("bi_quiz_bests", {});
  const bestKey = () => `${kind}${hard() ? ":hard" : ""}`;

  async function load(k) {
    if (data.buildings.length < 60) data.buildings = await api("/api/quiz?n=120").catch(() => []);
    if (QuizKinds.needsPool(k) && !data.pool) data.pool = await api("/api/quiz_pool").catch(() => ({ pron: [], stories: [], history: [], lists: [], firsts: [] }));
  }

  function menu() {
    kind = null;
    history.replaceState(null, "", location.pathname);
    $("#qz_play").hidden = true;
    $("#qz_menu").hidden = false;
    const b = bests();
    $("#qz_menu").innerHTML = Object.entries(KINDS).map(([k, q]) => {
      const e = b[k], h = b[k + ":hard"];
      return `<button class="quiz-pick" data-k="${k}"><span class="quiz-icon">${q.icon}</span><b>${esc(q.title)}</b>
        <span class="hint">${esc(q.blurb)}</span>
        <span class="quiz-best">${e || h ? `Best: ${e ? `${e[0]}/${e[1]}` : "–"} easy · ${h ? `${h[0]}/${h[1]}` : "–"} hard` : "Not played yet"}</span></button>`;
    }).join("");
  }

  async function start(k) {
    kind = k;
    history.replaceState(null, "", `?q=${k}`);
    $("#qz_menu").hidden = true;
    $("#qz_play").hidden = false;
    $("#qz_title").textContent = `${KINDS[k].icon} ${KINDS[k].title}`;
    $("#qz_card").innerHTML = "<p class='hint'>Loading…</p>";
    await load(k);
    qs = KINDS[k].make(data, hard());
    i = 0; score = 0; log = [];
    if (!qs.length) { $("#qz_card").innerHTML = "<p class='empty'>No questions available.</p>"; return; }
    ask();
  }

  function scoreLine() {
    const b = bests()[bestKey()];
    $("#qz_score").textContent = `${hard() ? "Hard" : "Easy"} · question ${Math.min(i + 1, qs.length)} of ${qs.length} · score ${score}` +
      (b ? ` · best ${b[0]}/${b[1]}` : "");
  }

  function choiceHTML(c, k) {
    return `<button class="btn ghost ${c.image ? "pic" : ""}" data-v="${esc(c.value)}" data-k="${k}">
      ${c.image ? `<img src="${esc(c.image)}" alt="${esc(c.label)}" loading="lazy">` : ""}
      <span>${esc(c.label)}</span>${c.sub ? `<span class="hint">${esc(c.sub)}</span>` : ""}
      ${KINDS[kind].order ? `<span class="quiz-rank"></span>` : ""}</button>`;
  }

  function ask() {
    scoreLine();
    if (i >= qs.length) return finish();
    const q = qs[i];
    picked = [];
    $("#qz_card").innerHTML = `${q.image ? `<img class="quiz-photo" src="${esc(q.image)}" alt="Photo for question ${i + 1}">` : ""}
      ${q.prompt}<div class="quiz-choices ${q.choices.some((c) => c.image) ? "pics" : ""}">${q.choices.map(choiceHTML).join("")}</div>`;
  }

  function pick(btn) {
    const q = qs[i];
    if (!KINDS[kind].order) return answer(btn.dataset.v);
    if (picked.includes(btn.dataset.v)) return;
    picked.push(btn.dataset.v);
    btn.querySelector(".quiz-rank").textContent = picked.length;
    btn.classList.add("chosen");
    if (picked.length === q.answer.length) answer(picked);
  }

  function answer(v) {
    const q = qs[i], order = Array.isArray(q.answer);
    const right = order ? q.answer.every((a, k) => a === v[k]) : v === q.answer;
    score += right;
    log.push({ q, right });
    document.querySelectorAll(".quiz-choices button").forEach((b) => {
      b.disabled = true;
      if (order) {
        const k = q.answer.indexOf(b.dataset.v);
        b.classList.add(v[k] === b.dataset.v ? "right" : "wrong");
        b.querySelector(".quiz-rank").textContent = k + 1;
      } else {
        b.classList.toggle("right", b.dataset.v === q.answer);
        b.classList.toggle("wrong", b.dataset.v === v && !right);
      }
    });
    $("#qz_card").insertAdjacentHTML("beforeend", `<div class="quiz-answer"><b>${right ? "Right!" : "Not quite."}</b>
      <div>${q.explain}</div>${q.story ? `<div class="stories-box" data-stories="${esc(q.story)}"></div>` : ""}
      <button class="btn small" id="qz_next">${i + 1 < qs.length ? "Next" : "See your score"}</button></div>`);
    $("#qz_next").focus();
    i++;
    scoreLine();
  }

  function finish() {
    const b = bests(), k = bestKey();
    const better = !b[k] || score / qs.length > b[k][0] / b[k][1];
    if (better) { b[k] = [score, qs.length]; store.set("bi_quiz_bests", b); }
    const pct = score / qs.length;
    $("#qz_card").innerHTML = `<h2>${score} out of ${qs.length}${better && score ? " · a new best!" : ""}</h2>
      <p>${pct >= 0.8 ? "Excellent: you know your isles." : pct >= 0.5 ? "Good going." : "These are hard; the History and Oldest pages help."}</p>
      <div class="filter-row"><button class="btn" id="qz_again">Play again</button>
        ${hard() ? "" : `<button class="btn ghost" id="qz_harder">Try it hard</button>`}
        <button class="btn ghost" id="qz_back2">Other quizzes</button></div>
      <h3>Your answers</h3><ol class="quiz-review">${log.map((l) => `<li class="${l.right ? "ok" : "no"}">${l.right ? "✓" : "✗"} ${l.q.explain}</li>`).join("")}</ol>`;
    scoreLine();
  }

  document.addEventListener("click", (e) => {
    const card = e.target.closest(".quiz-pick");
    if (card) return start(card.dataset.k);
    const b = e.target.closest(".quiz-choices button[data-v]");
    if (b && !b.disabled) return pick(b);
    const id = e.target.id;
    if (id === "qz_next") ask();
    else if (id === "qz_again") start(kind);
    else if (id === "qz_harder") { store.set("bi_quiz_hard", true); $("#qz_hard").checked = true; start(kind); }
    else if (id === "qz_back" || id === "qz_back2") menu();
  });
  document.addEventListener("DOMContentLoaded", () => {
    $("#qz_hard").checked = hard();
    $("#qz_hard").onchange = (e) => { store.set("bi_quiz_hard", e.target.checked); kind ? start(kind) : menu(); };
    $("#qz_new").onclick = () => start(kind);
    const k = new URLSearchParams(location.search).get("q");
    KINDS[k] ? start(k) : menu();
  });
})();
