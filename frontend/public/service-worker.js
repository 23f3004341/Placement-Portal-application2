const APP_SHELL = ["/", "/offline.html", "/icons/app-icon.svg"];

self.addEventListener("install", (event) => {
  event.waitUntil(caches.open("placement-portal-shell-v2").then((cache) => cache.addAll(APP_SHELL)));
  self.skipWaiting();
});

self.addEventListener("activate", (event) => {
  event.waitUntil(self.clients.claim());
});

self.addEventListener("fetch", (event) => {
  if (event.request.mode === "navigate") {
    event.respondWith(fetch(event.request).catch(() => caches.match("/offline.html")));
  }
});
