// Service Worker for QR Code Generator

const CACHE_NAME = 'qr-code-generator-v1';
const urlsToCache = [
  '/api/qr-codes/list',
  '/static/manifest.json',
  '/static/qr-icon-192.png',
  '/static/qr-icon-512.png'
];

// Install event - cache resources
self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => {
        console.log('Opened cache');
        return cache.addAll(urlsToCache);
      })
  );
});

// Fetch event - serve from cache if available
self.addEventListener('fetch', event => {
  event.respondWith(
    caches.match(event.request)
      .then(response => {
        // Cache hit - return response
        if (response) {
          return response;
        }
        return fetch(event.request);
      }
    )
  );
});