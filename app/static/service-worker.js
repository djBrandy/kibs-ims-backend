const CACHE_NAME = 'kibs-ims-cache-v1';
const urlsToCache = [
  '/', // Should match manifest.json start_url
  '/static/offline.html',
  // Add paths to your crucial static assets:
  // '/static/css/main.css',
  // '/static/js/app.js',
  '/static/icons/icon-192x192.png',
  '/static/icons/icon-512x512.png'
  // Add other important pages or assets you want to cache
];

self.addEventListener('install', event => {
  console.log('Service Worker: Installing...');
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => {
        console.log('Service Worker: Caching app shell');
        return cache.addAll(urlsToCache);
      })
      .catch(error => {
        console.error('Service Worker: Failed to cache app shell', error);
      })
  );
});

self.addEventListener('activate', event => {
  console.log('Service Worker: Activating...');
  const cacheWhitelist = [CACHE_NAME];
  event.waitUntil(
    caches.keys().then(cacheNames => {
      return Promise.all(
        cacheNames.map(cacheName => {
          if (cacheWhitelist.indexOf(cacheName) === -1) {
            console.log('Service Worker: Clearing old cache', cacheName);
            return caches.delete(cacheName);
          }
        })
      );
    })
  );
  return self.clients.claim();
});

self.addEventListener('fetch', event => {
  console.log('Service Worker: Fetching', event.request.url);
  event.respondWith(
    caches.match(event.request)
      .then(response => {
        if (response) {
          console.log('Service Worker: Found in cache', event.request.url);
          return response;
        }
        console.log('Service Worker: Not found in cache, fetching from network', event.request.url);
        return fetch(event.request).catch(() => {
          // If fetch fails (e.g., network error), and it's a navigation request, show offline page
          if (event.request.mode === 'navigate') {
            return caches.match('/static/offline.html');
          }
        });
      })
  );
});