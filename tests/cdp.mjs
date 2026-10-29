// Minimal Chrome DevTools Protocol driver for the GUI review (tests/ui_review.mjs): no dependencies,
// Node 22+ (built-in WebSocket and fetch). Headless Chrome with real time (no virtual-time budget), so
// online tiles load as they would for a user.
import { spawn } from "node:child_process";
import { mkdtempSync, writeFileSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

// webgl: WebGL on the GPU (ANGLE over Metal; SwiftShader gives no context here) for pages that draw in 3D (/stonehenge) instead of --disable-gpu.
export async function launch(chromePath, { port = 9333, width = 1280, height = 900, webgl = false } = {}) {
  const profile = mkdtempSync(join(tmpdir(), "uireview-"));
  const gpu = webgl ? ["--enable-gpu", "--use-angle=metal", "--ignore-gpu-blocklist"] : ["--disable-gpu"];
  const proc = spawn(chromePath, ["--headless=new", ...gpu, `--remote-debugging-port=${port}`,
    `--user-data-dir=${profile}`, `--window-size=${width},${height}`, "--no-first-run", "--hide-scrollbars",
    "about:blank"], { stdio: "ignore" });
  for (let i = 0; i < 50; i++) {
    try { await fetch(`http://127.0.0.1:${port}/json/version`); break; } catch (e) { await sleep(200); }
  }
  return {
    port,
    async page() { return openPage(port, width, height); },
    close() { proc.kill(); try { rmSync(profile, { recursive: true, force: true }); } catch (e) { /* busy */ } },
  };
}

async function openPage(port, width, height) {
  const t = await fetch(`http://127.0.0.1:${port}/json/new?about:blank`, { method: "PUT" }).then((r) => r.json());
  const ws = new WebSocket(t.webSocketDebuggerUrl);
  await new Promise((res, rej) => { ws.onopen = res; ws.onerror = rej; });
  let id = 0;
  const pending = new Map(), listeners = [];
  ws.onmessage = (m) => {
    const msg = JSON.parse(m.data);
    if (msg.id && pending.has(msg.id)) {
      const { res, rej } = pending.get(msg.id);
      pending.delete(msg.id);
      msg.error ? rej(new Error(msg.error.message)) : res(msg.result);
    } else if (msg.method) listeners.forEach((f) => f(msg));
  };
  const send = (method, params = {}) => new Promise((res, rej) => {
    const n = ++id;
    pending.set(n, { res, rej });
    ws.send(JSON.stringify({ id: n, method, params }));
  });
  const page = {
    errors: [], requests: new Map(),
    send,
    reset() { page.errors = []; page.requests = new Map(); },
    async goto(url, waitMs = 4000) {
      page.reset();
      await send("Page.navigate", { url });
      await page.waitLoad();
      await sleep(waitMs);
    },
    async waitLoad(timeout = 30000) {
      const t0 = Date.now();
      while (Date.now() - t0 < timeout) {
        try {
          const r = await send("Runtime.evaluate", { expression: "document.readyState", returnByValue: true });
          if (r.result.value === "complete") return;
        } catch (e) { /* navigating */ }
        await sleep(150);
      }
    },
    async eval(expression) {
      const r = await send("Runtime.evaluate", { expression, awaitPromise: true, returnByValue: true });
      if (r.exceptionDetails) throw new Error(r.exceptionDetails.exception?.description || r.exceptionDetails.text);
      return r.result.value;
    },
    async shot(file, clip) {
      const r = await send("Page.captureScreenshot", { format: "jpeg", quality: 70, ...(clip ? { clip: { ...clip, scale: 1 } } : {}) });
      writeFileSync(file, Buffer.from(r.data, "base64"));
    },
    // requests whose URL contains `part`: [{url, status, failed}]
    reqs(part) { return [...page.requests.values()].filter((q) => q.url.includes(part)); },
    close() { ws.close(); fetch(`http://127.0.0.1:${port}/json/close/${t.id}`).catch(() => {}); },
  };
  listeners.push((m) => {
    const p = m.params || {};
    if (m.method === "Runtime.exceptionThrown") page.errors.push("exception: " + (p.exceptionDetails.exception?.description || p.exceptionDetails.text).split("\n")[0]);
    if (m.method === "Runtime.consoleAPICalled" && p.type === "error") page.errors.push("console.error: " + p.args.map((a) => a.value ?? a.description ?? "").join(" ").slice(0, 200));
    if (m.method === "Network.requestWillBeSent") page.requests.set(p.requestId, { url: p.request.url, status: null, failed: null, type: p.type });
    if (m.method === "Network.responseReceived") { const q = page.requests.get(p.requestId); if (q) q.status = p.response.status; }
    if (m.method === "Network.loadingFailed") { const q = page.requests.get(p.requestId); if (q) q.failed = p.errorText; }
  });
  await send("Page.enable");
  await send("Runtime.enable");
  await send("Network.enable");
  await send("Emulation.setDeviceMetricsOverride", { width, height, deviceScaleFactor: 1, mobile: false });
  return page;
}

export { sleep };
