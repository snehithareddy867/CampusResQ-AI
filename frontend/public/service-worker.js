/* CampusResQ AI - Service Worker for Web Push + offline shell */
self.addEventListener("install", (e) => {
  self.skipWaiting();
});
self.addEventListener("activate", (e) => {
  e.waitUntil(self.clients.claim());
});

self.addEventListener("push", (event) => {
  let data = {};
  try { data = event.data ? event.data.json() : {}; } catch { data = { title: "CampusResQ", body: event.data ? event.data.text() : "" }; }
  const title = data.title || "CampusResQ Alert";
  const isCritical = (data.priority === "critical");
  const options = {
    body: data.body || "",
    icon: "/favicon.ico",
    badge: "/favicon.ico",
    tag: data.incident_id || "campusresq",
    renotify: isCritical,
    requireInteraction: isCritical,
    vibrate: isCritical ? [300, 100, 300, 100, 500] : [200, 100, 200],
    data: { url: data.url || "/notifications", incident_id: data.incident_id },
  };
  event.waitUntil(self.registration.showNotification(title, options));
});

self.addEventListener("notificationclick", (event) => {
  event.notification.close();
  const url = event.notification.data?.url || "/notifications";
  event.waitUntil(
    self.clients.matchAll({ type: "window", includeUncontrolled: true }).then((windows) => {
      for (const c of windows) {
        if ("focus" in c) { c.navigate(url); return c.focus(); }
      }
      if (self.clients.openWindow) return self.clients.openWindow(url);
    })
  );
});
