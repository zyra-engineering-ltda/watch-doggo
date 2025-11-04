// super-minimal SW just to get push/notifications working

self.addEventListener("install", (event) => {
  // activate immediately
  self.skipWaiting();
});

self.addEventListener("activate", (event) => {
  // take control of existing clients
  event.waitUntil(self.clients.claim());
});

// handle push payloads (from server) – keep from earlier plan
self.addEventListener("push", (event) => {
  let data = {};
  if (event.data) {
    data = event.data.json();
  }

  const title = data.title || "WatchDoggo alert";
  const options = {
    body: data.body || "A service changed status.",
    icon: "/static/icons/icon-192.png",
    badge: "/static/icons/icon-192.png",
    data: data.data || {}
  };

  event.waitUntil(self.registration.showNotification(title, options));
});

self.addEventListener("notificationclick", (event) => {
  event.notification.close();
  const url = event.notification.data?.url || "/";
  event.waitUntil(clients.openWindow(url));
});
