"""Serve the PWA service worker and manifest from the site root so the
service worker gets root scope ('/') and can control the whole app."""
from django.http import HttpResponse, JsonResponse

SW_JS = """
const CACHE = 'nexus-v1';
self.addEventListener('install', (e) => { self.skipWaiting(); });
self.addEventListener('activate', (e) => { e.waitUntil(self.clients.claim()); });
self.addEventListener('fetch', (event) => {
  const req = event.request;
  if (req.method !== 'GET') return;
  const url = new URL(req.url);
  if (url.pathname.startsWith('/api/')) return;
  if (url.pathname.startsWith('/static/')) {
    event.respondWith(
      caches.open(CACHE).then((cache) =>
        cache.match(req).then((hit) =>
          hit || fetch(req).then((res) => { cache.put(req, res.clone()); return res; }).catch(() => hit)
        )
      )
    );
  }
});
""".strip()

MANIFEST = {
    "name": "Nexus Framework ERP",
    "short_name": "Nexus",
    "description": "نظام تخطيط موارد المؤسسات — Enterprise Command Center",
    "start_url": "/",
    "scope": "/",
    "display": "standalone",
    "orientation": "portrait",
    "background_color": "#faf9f8",
    "theme_color": "#0078d4",
    "lang": "ar",
    "dir": "rtl",
    "icons": [
        {"src": "/static/nexus-icon.svg", "sizes": "any", "type": "image/svg+xml", "purpose": "any maskable"}
    ],
}


def service_worker(request):
    resp = HttpResponse(SW_JS, content_type="application/javascript")
    resp["Service-Worker-Allowed"] = "/"
    resp["Cache-Control"] = "no-cache"
    return resp


def manifest(request):
    return JsonResponse(MANIFEST, content_type="application/manifest+json")
