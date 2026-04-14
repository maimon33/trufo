const CACHE = 'trufo-pwa-v1'
const SHELL = ['/app/', '/app/index.html']

self.addEventListener('install', e => {
  e.waitUntil(caches.open(CACHE).then(c => c.addAll(SHELL)))
  self.skipWaiting()
})

self.addEventListener('activate', e => {
  e.waitUntil(
    caches.keys().then(keys =>
      Promise.all(keys.filter(k => k !== CACHE).map(k => caches.delete(k)))
    )
  )
  self.clients.claim()
})

self.addEventListener('fetch', e => {
  // Never cache API calls
  if (new URL(e.request.url).pathname.startsWith('/api/')) return
  e.respondWith(
    caches.match(e.request).then(r => r || fetch(e.request))
  )
})
