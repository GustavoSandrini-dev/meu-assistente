const C = "ma-v48";
const SHELL = ["./","./index.html","./painel-financeiro-web.html","./biblioteca-jogos-web.html","./filmes-web.html","./livros-web.html","./tarefas-web.html","./vida-saudavel-web.html","./alimentos-taco.json","./preparacoes.json","./precos-alimentos.json","./common.js","./manifest.webmanifest","./icon-192.png","./icon-512.png"];
self.addEventListener("install", e => { e.waitUntil(caches.open(C).then(c => c.addAll(SHELL)).then(() => self.skipWaiting())); });
self.addEventListener("activate", e => { e.waitUntil(caches.keys().then(k => Promise.all(k.filter(x => x !== C).map(x => caches.delete(x)))).then(() => self.clients.claim())); });
self.addEventListener("fetch", e => {
  const u = new URL(e.request.url);
  if (u.origin === location.origin && e.request.method === "GET") {
    e.respondWith(fetch(e.request).then(res => { const cp = res.clone(); caches.open(C).then(c => c.put(e.request, cp)); return res; }).catch(() => caches.match(e.request)));
  }
});

// ---------- Web Push (lembrete de água do módulo Vida Saudável) ----------
// Notificação SILENCIOSA: aparece na tela, não toca som nem vibra.
self.addEventListener("push", e => {
  let d = {};
  try { d = e.data ? e.data.json() : {}; } catch (_) { d = { body: e.data ? e.data.text() : "" }; }
  const titulo = d.title || "💧 Hora de beber água";
  // o servidor manda como o usuário quer ser avisado: silencioso, com som
  // ou com som e vibração. Som personalizado não existe na web.
  const opts = {
    body: d.body || "Bora tomar um copo d'água.",
    icon: "./icon-192.png",
    badge: "./icon-192.png",
    silent: d.silent !== false,
    tag: d.tag || "agua",
    renotify: d.silent === false,
    data: { url: d.url || "./vida-saudavel-web.html" },
    actions: [{ action: "beber", title: "Bebi um copo" }]
  };
  if (d.silent === false && Array.isArray(d.vibrate)) opts.vibrate = d.vibrate;
  e.waitUntil(self.registration.showNotification(titulo, opts));
});

self.addEventListener("notificationclick", e => {
  e.notification.close();
  const base = (e.notification.data && e.notification.data.url) || "./vida-saudavel-web.html";
  const alvo = e.action === "beber" ? "./vida-saudavel-web.html?agua=250" : base;
  e.waitUntil(clients.matchAll({ type: "window", includeUncontrolled: true }).then(list => {
    for (const c of list) { if (c.url.includes("vida-saudavel-web.html") && "focus" in c) { c.navigate(alvo); return c.focus(); } }
    return clients.openWindow(alvo);
  }));
});
