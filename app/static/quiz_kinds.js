// The quizzes: each makes a round of questions from photographed buildings (/api/quiz) and the quiz pool
// (/api/quiz_pool: names to say, stories, history events, the researched oldest lists). Used by quiz.js.
// A question: { prompt (HTML), image?, choices: [{ value, label, sub?, image? }], answer (value, or a list of
// values in order for "order" questions), explain (HTML), link? }.
const QuizKinds = (() => {
  const PERIODS = ["Neolithic", "Bronze Age", "Iron Age", "Roman Britain", "Early Medieval", "Norman", "High Medieval",
                   "Late Medieval", "Tudor", "Stuart", "Georgian", "Victorian", "Modern"];
  const SPAN = { Neolithic: "c. 4000–2500 BC", "Bronze Age": "2500–800 BC", "Iron Age": "800 BC–AD 43",
    "Roman Britain": "43–410", "Early Medieval": "410–1066", Norman: "1066–1154", "High Medieval": "1154–1307",
    "Late Medieval": "1307–1485", Tudor: "1485–1603", Stuart: "1603–1714", Georgian: "1714–1837",
    Victorian: "1837–1901", Modern: "1901–" };
  const STORY = { supernatural: "ghost story", legend: "legend", folklore: "custom or piece of folklore",
                  curiosity: "curious tale" };

  const shuffle = (a) => { a = a.slice(); for (let i = a.length - 1; i > 0; i--) { const j = Math.floor(Math.random() * (i + 1)); [a[i], a[j]] = [a[j], a[i]]; } return a; };
  const take = (a, n) => shuffle(a).slice(0, n);
  const yr = (y) => (y < 0 ? `${-y} BC` : `AD ${y}`);
  const link = (b) => `<a href="${buildingUrl(b.id)}" target="_blank" rel="noopener">${esc(b.name)}</a>`;
  const when = (b) => `${esc(b.date_text || yr(b.year_start))} (${esc(b.period)})`;
  const where = (b) => esc([b.locality, b.county !== b.locality && b.county, b.nation].filter(Boolean).join(", "));
  const photo = (b) => ({ value: b.id, label: b.name, image: b.image_thumb, sub: b.category });

  // `n` items from `pool` that pass `ok` against each other (e.g. different enough dates), or null
  function spread(pool, n, ok, tries = 60) {
    for (let t = 0; t < tries; t++) {
      const got = [];
      for (const x of shuffle(pool)) {
        if (got.every((g) => ok(g, x))) got.push(x);
        if (got.length === n) return got;
      }
    }
    return null;
  }
  // three wrong answers from `pool` (values unlike the answer and each other), the right one among them
  function options(answer, pool, key, near) {
    const seen = new Set([key(answer)]), wrong = [];
    for (const x of near ? pool : shuffle(pool)) {
      if (!seen.has(key(x))) { seen.add(key(x)); wrong.push(x); }
      if (wrong.length === 3) break;
    }
    return shuffle([answer, ...wrong]);
  }

  const K = {};
  K.period = { title: "Guess the period", icon: "⏳", blurb: "A photo of a building: when was it begun?",
    make(d, hard) {
      return take(d.buildings, 10).map((b) => {
        const k = Math.max(0, PERIODS.indexOf(b.period));
        let ps;
        if (hard) {                                 // the answer and its neighbours
          const lo = Math.max(0, Math.min(PERIODS.length - 4, k - Math.floor(Math.random() * 4)));
          ps = PERIODS.slice(lo, lo + 4);
        } else {                                    // periods at least two apart
          ps = [b.period, ...take(PERIODS.filter((p, i) => Math.abs(i - k) >= 2), 3)].sort((x, y) => PERIODS.indexOf(x) - PERIODS.indexOf(y));
        }
        return { prompt: `<p class="hint">${esc(b.category)} · ${esc(b.nation || "")}</p>`, image: b.image_thumb,
          choices: ps.map((p) => ({ value: p, label: p, sub: SPAN[p] })), answer: b.period,
          explain: `It is ${link(b)}, ${when(b)}.`, story: b.id };
      });
    } };

  K.older = { title: "Which is older?", icon: "⚖", blurb: "Two buildings side by side: which was begun first?",
    make(d, hard) {
      const gap = hard ? 40 : 250, out = [];
      for (let i = 0; i < 40 && out.length < 10; i++) {
        const pair = spread(d.buildings, 2, (a, b) => Math.abs(a.year_start - b.year_start) >= gap && a.id !== b.id, 5);
        if (!pair || out.some((q) => q.ids.includes(pair[0].id) || q.ids.includes(pair[1].id))) continue;
        const old = pair[0].year_start < pair[1].year_start ? pair[0] : pair[1];
        out.push({ ids: pair.map((b) => b.id), prompt: "<p>Which was begun first?</p>", choices: pair.map(photo), answer: old.id,
          explain: pair.map((b) => `${link(b)}: ${when(b)}`).join("<br>") });
      }
      return out;
    } };

  K.oldest = { title: "Oldest of four", icon: "🏆", blurb: "Four buildings: pick the oldest.",
    make(d, hard) {
      const out = [], used = new Set();
      for (let i = 0; i < 40 && out.length < 10; i++) {
        const free = d.buildings.filter((b) => !used.has(b.id));
        const four = spread(free, 4, hard ? (a, b) => Math.abs(a.year_start - b.year_start) >= 30
          : (a, b) => a.period !== b.period, 5);
        if (!four) break;
        four.forEach((b) => used.add(b.id));
        const old = four.reduce((a, b) => (b.year_start < a.year_start ? b : a));
        out.push({ prompt: "<p>Which of these is the oldest?</p>", choices: four.map(photo), answer: old.id,
          explain: four.slice().sort((a, b) => a.year_start - b.year_start).map((b) => `${link(b)}: ${when(b)}`).join("<br>") });
      }
      return out;
    } };

  K.order = { title: "Put them in order", icon: "↕", blurb: "Four buildings: tap them from oldest to newest.",
    order: true,
    make(d, hard) {
      const out = [], used = new Set();
      for (let i = 0; i < 40 && out.length < 8; i++) {
        const free = d.buildings.filter((b) => !used.has(b.id));
        const four = spread(free, 4, (a, b) => Math.abs(a.year_start - b.year_start) >= (hard ? 40 : 150), 5);
        if (!four) break;
        four.forEach((b) => used.add(b.id));
        const sorted = four.slice().sort((a, b) => a.year_start - b.year_start);
        out.push({ prompt: "<p>Tap them from the <b>oldest</b> to the <b>newest</b>.</p>", choices: four.map(photo),
          answer: sorted.map((b) => b.id), explain: sorted.map((b, k) => `${k + 1}. ${link(b)}: ${when(b)}`).join("<br>") });
      }
      return out;
    } };

  K.where = { title: "Where in the isles?", icon: "📍", blurb: "A photo and a name: which county is it in?",
    make(d, hard) {
      const withCounty = d.buildings.filter((b) => b.county);
      return take(withCounty, 10).map((b) => {
        const others = withCounty.filter((x) => x.county !== b.county && (hard ? x.nation === b.nation : x.nation !== b.nation));
        const ch = options(b, others.length >= 3 ? others : withCounty.filter((x) => x.county !== b.county), (x) => x.county);
        return { prompt: `<p><b>${esc(b.name)}</b> <span class="hint">${esc(b.category)}</span></p>`, image: b.image_thumb,
          choices: ch.map((x) => ({ value: x.county, label: x.county, sub: hard ? "" : x.nation })), answer: b.county,
          explain: `${link(b)} is in ${where(b)}.` };
      });
    } };

  K.say = { title: "Say the name", icon: "🗣", blurb: "Places that are not said the way they are spelt.",
    make(d, hard) {
      const pool = d.pool.pron;
      return take(pool, 10).map((p) => {
        const len = p.respell.length;
        const near = hard ? pool.slice().sort((a, b) => Math.abs(a.respell.length - len) - Math.abs(b.respell.length - len)) : pool;
        const ch = options(p, near.filter((x) => x.name !== p.name), (x) => x.respell, hard);
        const audio = p.audio ? ` <a href="https://commons.wikimedia.org/wiki/File:${encodeURIComponent(p.audio)}" target="_blank" rel="noopener">▶ hear it</a>` : "";
        return { prompt: `<p class="quiz-big">${esc(p.name)}</p><p class="hint">How is it said? (capitals: the stressed syllable)</p>`,
          choices: ch.map((x) => ({ value: x.respell, label: x.respell })), answer: p.respell,
          explain: `<b>${esc(p.name)}</b> is said “${esc(p.respell)}” <span class="hint">/${esc(p.ipa)}/</span>${audio}` };
      });
    } };

  K.story = { title: "Whose story?", icon: "👻", blurb: "A ghost story, legend or custom: where is it told?",
    make(d, hard) {
      const pool = d.pool.stories;
      return take(pool, 10).map((s) => {
        const same = pool.filter((x) => x.name !== s.name && (hard ? x.nation === s.nation && x.kind === s.kind : true));
        const ch = options(s, same.length >= 3 ? same : pool.filter((x) => x.name !== s.name), (x) => x.short);
        const re = new RegExp(s.short.replace(/[.*+?^${}()|[\]\\]/g, "\\$&"), "i");       // hide the name, then escape
        const text = (s.text.length > 520 ? s.text.slice(0, 500) + "…" : s.text).split(re).map(esc).join("<b>▇▇▇</b>");
        return { prompt: `<p class="hint">A ${STORY[s.kind] || "story"}:</p><blockquote class="quiz-quote">${text}</blockquote>`,
          choices: ch.map((x) => ({ value: x.short, label: x.short })), answer: s.short,
          explain: `It is told of <a href="${buildingUrl(s.id)}" target="_blank" rel="noopener">${esc(s.name)}</a>.` };
      });
    } };

  K.history = { title: "When did it happen?", icon: "📜", blurb: "Events in the history of the isles: pick the date.",
    make(d, hard) {
      const pool = d.pool.history;
      return take(pool, 10).map((e) => {
        const near = pool.filter((x) => x.date_text !== e.date_text)
          .sort((a, b) => Math.abs(a.year - e.year) - Math.abs(b.year - e.year));
        const ch = options(e, hard ? near.slice(0, 8) : near.slice(6), (x) => x.date_text);
        return { prompt: `<p class="quiz-big">${esc(e.title)}</p><p class="hint">${esc(e.region || "")}</p>`,
          choices: ch.sort((a, b) => a.year - b.year).map((x) => ({ value: x.date_text, label: x.date_text })), answer: e.date_text,
          explain: `${esc(e.date_text)}: ${esc(e.description || "")}${e.source ? ` <a href="${esc(e.source)}" target="_blank" rel="noopener">source</a>` : ""}` };
      });
    } };

  K.ages = { title: "How old is it?", icon: "🌳", blurb: "Ancient trees, graves, markets, roads and sport: the oldest things that are not buildings.",
    make(d, hard) {
      const pool = d.pool.lists.filter((e) => e.age);
      return take(pool, 10).map((e) => {
        const near = pool.filter((x) => x.year !== e.year && (!hard || x.list === e.list))
          .sort((a, b) => Math.abs(a.year - e.year) - Math.abs(b.year - e.year));
        const ch = options(e, hard ? near.slice(0, 6) : near.slice(5), (x) => x.age);
        return { prompt: `<p class="quiz-big">${esc(e.name)}</p><p class="hint">${esc(e.category)} · ${esc(e.location || "")}</p>`,
          choices: ch.sort((a, b) => a.year - b.year).map((x) => ({ value: x.age, label: x.age })), answer: e.age,
          explain: `<b>${esc(e.name)}</b>: ${esc(e.age)}${e.claim ? `, ${esc(e.claim)}` : ""}. <span class="hint">From the researched lists on the Oldest page.</span>` };
      });
    } };

  K.first = { title: "Which came first?", icon: "💡", blurb: "Inventions, laws and firsts of trade and industry: which came first?",
    make(d, hard) {
      const gap = hard ? 5 : 30, pool = d.pool.firsts || [], out = [];
      for (let i = 0; i < 60 && out.length < 10; i++) {
        const pair = spread(pool, 2, (a, b) => Math.abs(a.year - b.year) >= gap, 5);
        if (!pair || out.some((q) => q.ids.includes(pair[0].title) || q.ids.includes(pair[1].title))) continue;
        const first = pair[0].year < pair[1].year ? pair[0] : pair[1];
        out.push({ ids: pair.map((x) => x.title), prompt: "<p>Which came first?</p>",
          choices: pair.map((x) => ({ value: x.title, label: x.title, sub: x.what })), answer: first.title,
          explain: pair.map((x) => `<b>${esc(x.title)}</b>: ${x.year}${x.text ? ` — ${esc(x.text)}` : ""}`).join("<br>") +
            ` <span class="hint">From the <a href="${IS_STATIC ? "trades.html" : "/trades"}">trade stories</a>.</span>` });
      }
      return out;
    } };

  K.mixed = { title: "Mixed bag", icon: "🎲", blurb: "A bit of everything, one question from each quiz and more.",
    make(d, hard) {
      const kinds = Object.keys(K).filter((k) => k !== "mixed" && !K[k].order);
      return shuffle(kinds.flatMap((k) => K[k].make(d, hard).slice(0, 2))).slice(0, 12);
    } };

  return { KINDS: K, PERIODS, needsPool: (k) => ["say", "story", "history", "ages", "first", "mixed"].includes(k) };
})();
