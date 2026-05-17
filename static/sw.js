const CACHE = 'tbc-v5';
const PRECACHE = [
  '/static/img/gas-station.png',
];

self.addEventListener('install', e => {
  e.waitUntil(caches.open(CACHE).then(c => c.addAll(PRECACHE)));
  self.skipWaiting();
});

self.addEventListener('activate', e => {
  e.waitUntil(
    caches.keys().then(keys =>
      Promise.all(keys.filter(k => k !== CACHE).map(k => caches.delete(k)))
    )
  );
  self.clients.claim();
});

self.addEventListener('fetch', e => {
  if (e.request.method !== 'GET') return;

  // Never intercept HTML navigation — let the browser fetch fresh pages directly.
  // This prevents stale CSRF tokens from being served from any cache layer.
  if (e.request.mode === 'navigate') return;

  const url = new URL(e.request.url);

  // CSS and JS: network-first — always fresh, cache as fallback only
  if (url.pathname.startsWith('/static/css/') || url.pathname.startsWith('/static/js/')) {
    e.respondWith(
      fetch(e.request).then(res => {
        const clone = res.clone();
        caches.open(CACHE).then(c => c.put(e.request, clone));
        return res;
      }).catch(() => caches.match(e.request))
    );
    return;
  }

  // Images and fonts: cache-first (truly static, safe to cache long-term)
  if (url.pathname.startsWith('/static/img/') || url.pathname.startsWith('/static/fonts/')) {
    e.respondWith(
      caches.match(e.request).then(cached => cached || fetch(e.request).then(res => {
        const clone = res.clone();
        caches.open(CACHE).then(c => c.put(e.request, clone));
        return res;
      }))
    );
    return;
  }

  // Everything else (non-navigation XHR/fetch): network only, no cache
  // Navigation is already excluded above so this path is for API/XHR calls.
  e.respondWith(fetch(e.request));
});
