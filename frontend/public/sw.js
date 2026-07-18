// Minimal service worker — cache-first for static assets, network for the rest.
//
// NOTE ON CONTROL TAKEOVER:
// This worker deliberately does NOT call skipWaiting() or clients.claim().
// Together those make a newly-installed worker seize the page that is already
// open — which re-initialises the live document mid-session and swallows the
// first interaction after load (a first click on any <select> registered but
// did not open it). Letting the worker activate only for future navigations
// leaves the page the user is on untouched. A new worker takes over on the
// next full load, which is the correct, non-disruptive moment.
const CACHE = 'nexus-v2';

self.addEventListener('install', () => {
  // No skipWaiting(): the new worker waits for the old one to be gone (all tabs
  // closed / next load) rather than barging into a live page.
});

self.addEventListener('activate', (event) => {
  // Drop old caches, but do NOT clients.claim() — claiming an already-loaded
  // page is what caused the first-click-lost behaviour.
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k)))
    )
  );
});

self.addEventListener('fetch', (event) => {
  const req = event.request;
  if (req.method !== 'GET') return;
  const url = new URL(req.url);
  if (url.pathname.startsWith('/api/')) return;
  if (url.pathname.startsWith('/static/')) {
    event.respondWith(
      caches.open(CACHE).then((cache) =>
        cache.match(req).then((hit) =>
          hit ||
          fetch(req)
            .then((res) => {
              cache.put(req, res.clone());
              return res;
            })
            .catch(() => hit)
        )
      )
    );
  }
});
