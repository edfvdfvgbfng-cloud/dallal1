const CACHE_NAME = 'dalal-pwa-v1';
const OFFLINE_URL = '/offline/';
const PRECACHE_URLS = [
  '/',
  '/offline/',
  '/static/css/style.css',
  '/static/css/dalal-theme.css',
  '/static/css/premium-ui.css',
  '/static/css/responsive.css',
  '/static/js/app.js',
  '/static/js/push-notifications.js',
  '/static/images/favicon.svg',
  '/static/manifest.json'
];

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => cache.addAll(PRECACHE_URLS)).then(() => self.skipWaiting())
  );
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(keys.filter((k) => k !== CACHE_NAME).map((k) => caches.delete(k)))
    ).then(() => self.clients.claim())
  );
});

// Push Notification Handler
self.addEventListener('push', (event) => {
  if (!event.data) {
    return;
  }

  const data = event.data.json();
  const options = {
    body: data.message || '',
    icon: '/static/images/favicon.svg',
    badge: '/static/images/favicon.svg',
    vibrate: [200, 100, 200],
    data: {
      link: data.link || '/',
      notificationId: data.notificationId
    },
    actions: [
      {
        action: 'view',
        title: 'عرض',
        icon: '/static/images/favicon.svg'
      },
      {
        action: 'close',
        title: 'إغلاق',
        icon: '/static/images/favicon.svg'
      }
    ],
    requireInteraction: true,
    tag: data.notificationId || 'default'
  };

  event.waitUntil(
    self.registration.showNotification(data.title || 'إشعار جديد', options)
  );
});

// Notification Click Handler
self.addEventListener('notificationclick', (event) => {
  event.notification.close();

  if (event.action === 'view') {
    const link = event.notification.data.link || '/';
    event.waitUntil(
      clients.openWindow(link)
    );
  } else if (event.action === 'close') {
    // Just close the notification
  } else {
    // Default click behavior
    const link = event.notification.data.link || '/';
    event.waitUntil(
      clients.openWindow(link)
    );
  }
});

self.addEventListener('fetch', (event) => {
  const request = event.request;
  if (request.method !== 'GET') return;

  const url = new URL(request.url);
  if (url.origin !== self.location.origin) return;

  // Network-first for API / dashboard (always fresh)
  if (url.pathname.startsWith('/api/') || url.pathname.startsWith('/dashboard/') || url.pathname.startsWith('/admin/')) {
    event.respondWith(fetch(request).catch(() => caches.match(OFFLINE_URL)));
    return;
  }

  // Cache-first for static assets
  if (url.pathname.startsWith('/static/') || url.pathname.startsWith('/media/')) {
    event.respondWith(
      caches.match(request).then((cached) => {
        const fetchPromise = fetch(request).then((response) => {
          if (response && response.status === 200) {
            const clone = response.clone();
            caches.open(CACHE_NAME).then((cache) => cache.put(request, clone));
          }
          return response;
        }).catch(() => cached);
        return cached || fetchPromise;
      })
    );
    return;
  }

  // Network-first for pages, fallback to cache / offline
  event.respondWith(
    fetch(request)
      .then((response) => {
        if (response && response.status === 200 && response.type === 'basic') {
          const clone = response.clone();
          caches.open(CACHE_NAME).then((cache) => cache.put(request, clone));
        }
        return response;
      })
      .catch(() =>
        caches.match(request).then((cached) => cached || caches.match(OFFLINE_URL))
      )
  );
});
