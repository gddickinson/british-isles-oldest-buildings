// Service worker (installed app / offline): pages and data are fetched from the network first and
// kept in a cache, so places you have opened, saved tours and the offline map work without a
// connection. Map tiles from the internet are not cached (the bundled offline map is).
const CACHE = "bi-v1";
const SHELL = ["/", "/map", "/tours", "/stories", "/static/style.css", "/static/state.js", "/static/basemap.js",
               "/static/tour_lib.js", "/static/tours.js", "/static/tour_builder.js"];

// API answers worth keeping offline: records and tours you opened (searches are not kept)
const KEEP_API = /^\/api\/(building|buildings|place|person|tour|tours|stories|timeline|visiting|domesday|excavations|depictions|pron|related|nearby)\b/;

self.addEventListener("install", (e) => e.waitUntil(caches.open(CACHE).then((c) => c.addAll(SHELL)).then(() => self.skipWaiting())));
self.addEventListener("activate", (e) => e.waitUntil(caches.keys()
  .then((keys) => Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k)))).then(() => self.clients.claim())));

self.addEventListener("fetch", (e) => {
  const url = new URL(e.request.url);
  if (e.request.method !== "GET" || url.origin !== location.origin) return;      // tiles, CDNs: browser as usual
  if (url.pathname.startsWith("/api/rebuild") || url.pathname.startsWith("/api/settings")) return;
  const keep = !url.pathname.startsWith("/api/") || KEEP_API.test(url.pathname);   // not every search
  e.respondWith(fetch(e.request).then((resp) => {
    if (resp.ok && keep) { const copy = resp.clone(); caches.open(CACHE).then((c) => c.put(e.request, copy)); }
    return resp;
  }).catch(() => caches.match(e.request).then((hit) => hit || caches.match("/"))));
});
