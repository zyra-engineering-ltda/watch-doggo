// static/service-worker.js

const CACHE_NAME = "watchdoggo-v1";
// keep your list small; we will cache them but NOT fail install if one 404s
const URLS_TO_CACHE = [
  "/",
  "/static/js/dashboard.js",          // this one likely exists
  // "/static/css/bootstrap.min.css",  // add back when you're sure of the path
];

// INSTALL – safe version
self.addEventListener("install", (event) => {
  event.waitUntil((async () => {
    const cache = await caches.open(CACHE_NAME);

    // addAll can fail the whole install if 1 file 404s, so use allSettled
    await Promise.allSettled(
      URLS_TO_CACHE.map((url) => cache.add(url))
    );

    // activate immediately
    self.skipWaiting();
  })());
});

// ACTIVATE – take control of open clients
self.addEventListener("activate", (event) => {
  event.waitUntil(self.clients.claim());
});

// FETCH – cache-first, fall back to network
self.addEventListener("fetch", (event) => {
  event.respondWith((async () => {
    const cached = await caches.match(event.request);
    if (cached) {
      return cached;
    }
    try {
      const resp = await fetch(event.request);
      return resp;
    } catch (e) {
      // optional: return a fallback Response here
      return new Response("Offline", { status: 503, statusText: "Offline" });
    }
  })());
});

// PUSH – show notification
self.addEventListener("push", (event) => {
  let data = {};
  if (event.data) {
    try {
      data = event.data.json();
    } catch (e) {
      data = { body: event.data.text() };
    }
  }

  const title = data.title || "WatchDoggo alert";
  const options = {
    body: data.body || "A service changed status.",
    icon: "/static/icons/icon-192.png",
    badge: "/static/icons/icon-192.png",
    data: data.data || {},
  };

  event.waitUntil(self.registration.showNotification(title, options));
});

// CLICK – open URL if provided
self.addEventListener("notificationclick", (event) => {
  event.notification.close();
  const url = event.notification.data?.url || "/";
  event.waitUntil(clients.openWindow(url));
});
