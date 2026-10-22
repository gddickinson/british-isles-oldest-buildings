// Settings › Share on my home network (app/lan.py): the switch, the address to open on other devices, a QR code.
(function () {
  const box = document.getElementById("sh_status"), on = document.getElementById("sh_on"), qr = document.getElementById("sh_qr");
  const codeOn = document.getElementById("sh_code"), trustedOn = document.getElementById("sh_trusted"),
        codes = document.getElementById("sh_codes");
  if (!box || !THIS_MACHINE) return;
  const QR_LIB = "https://cdnjs.cloudflare.com/ajax/libs/qrcodejs/1.0.0/qrcode.min.js";
  let qrLoading = null;
  const loadQr = () => (qrLoading = qrLoading || new Promise((ok, fail) => {
    const s = document.createElement("script");
    s.src = QR_LIB; s.onload = ok; s.onerror = fail; document.head.appendChild(s);
  }));

  function drawCodes(st) {          // share codes (app/lan.py): the address with ?code= opens without typing it
    codeOn.checked = !!st.code; trustedOn.checked = !!st.trusted;
    const url = st.urls[0] || "";
    codes.innerHTML = [st.code && `Share code <b><code>${esc(st.code)}</code></b>${url ? ` · <code>${esc(url)}/?code=${esc(st.code)}</code>` : ""}`,
      st.trusted && `Trusted code <b><code>${esc(st.trusted)}</code></b> (give it only to devices you would let change things)`,
      !st.code && !st.trusted && "Anyone on the network can open the app (read-only)."].filter(Boolean).join("<br>");
  }
  async function setCode(kind, want) {
    const st = await fetch("/api/share", { method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ [kind]: want ? "new" : "off" }) }).then((r) => r.json()).catch(() => null);
    if (st) { drawCodes(st); draw(st); }
  }
  codeOn.addEventListener("change", () => setCode("code", codeOn.checked));
  trustedOn.addEventListener("change", () => setCode("trusted", trustedOn.checked));

  async function draw(st) {
    on.checked = st.enabled;
    drawCodes(st);
    const waiting = st.enabled !== st.listening;
    box.innerHTML = !st.enabled ? (st.listening ? "Shared for this run only (started with --lan)." : "Only this computer can open the app.")
      : waiting ? "Restarting on the home network…"
      : `Open on another device on this network: ${st.urls.map((u) => `<a href="${esc(u)}" target="_blank" rel="noopener"><code>${esc(u)}</code></a>`).join(" or ")}`;
    qr.innerHTML = "";
    if ((st.enabled || st.listening) && !waiting && st.urls.length) {
      try { await loadQr(); new QRCode(qr, { text: st.urls[0] + (st.code ? "/?code=" + st.code : ""), width: 140, height: 140 }); }
      catch (e) { /* offline: the address is shown above */ }
    }
  }

  async function poll(want, tries = 20) {          // the server restarts: wait until it answers on its new address
    for (let i = 0; i < tries; i++) {
      await new Promise((r) => setTimeout(r, 700));
      const st = await fetch("/api/share").then((r) => r.json()).catch(() => null);
      if (st && st.listening === want) return draw(st);
    }
    box.textContent = "The app did not come back by itself: start it again with ./run.sh";
  }

  on.addEventListener("change", async () => {
    box.textContent = on.checked ? "Restarting on the home network…" : "Restarting for this computer only…";
    qr.innerHTML = "";
    await fetch("/api/share", { method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ enabled: on.checked }) }).catch(() => null);
    poll(on.checked);
  });
  fetch("/api/share").then((r) => r.json()).then(draw).catch(() => { box.textContent = "Not available."; });
})();
