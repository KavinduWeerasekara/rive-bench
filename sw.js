/* Rive Bench service worker.

   Caches the whole app on first visit so it runs with no network at all.
   To ship an update: change VERSION below. The browser re-fetches this file
   when the app is opened online, sees the new version, downloads the new
   assets, and swaps them in on the next launch. */

const VERSION = 'rive-bench-v1';

const CORE = [
  './',
  './index.html',
  './manifest.webmanifest',
  './icon-180.png',
  './icon-192.png',
  './icon-512.png'
];

const EXTRA = [
  './can-it-run.html'
];

self.addEventListener('install', event => {
  event.waitUntil((async () => {
    const cache = await caches.open(VERSION);
    await cache.addAll(CORE);
    // optional files must never fail the install
    await Promise.all(EXTRA.map(u => cache.add(u).catch(() => {})));
    await self.skipWaiting();
  })());
});

self.addEventListener('activate', event => {
  event.waitUntil((async () => {
    const names = await caches.keys();
    await Promise.all(names.filter(n => n !== VERSION).map(n => caches.delete(n)));
    await self.clients.claim();
  })());
});

self.addEventListener('fetch', event => {
  const req = event.request;

  // Only ever handle our own files. The runtime updater talks to npm and
  // jsDelivr; those requests must pass straight through untouched.
  if (req.method !== 'GET') return;
  if (new URL(req.url).origin !== self.location.origin) return;

  event.respondWith((async () => {
    const cached = await caches.match(req, {ignoreSearch: true});
    if (cached) return cached;

    try {
      const res = await fetch(req);
      if (res && res.ok){
        const cache = await caches.open(VERSION);
        cache.put(req, res.clone());
      }
      return res;
    } catch (e) {
      // offline and not cached: fall back to the app shell for navigations
      if (req.mode === 'navigate'){
        const shell = await caches.match('./index.html');
        if (shell) return shell;
      }
      throw e;
    }
  })());
});
