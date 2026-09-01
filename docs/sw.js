/* 由 build.py 產生,請勿手動編輯 */
const VERSION = 'vbdb2f55f6142';
const SHELL = 'shell-' + VERSION;
const MEDIA = 'media-' + VERSION;
const SHELL_MAX = 130;
const MEDIA_MAX = 90;

self.addEventListener('install', function() { self.skipWaiting(); });

self.addEventListener('activate', function(event) {
  event.waitUntil((async function() {
    const keys = await caches.keys();
    await Promise.all(keys.filter(function(k) { return !k.endsWith(VERSION); })
                          .map(function(k) { return caches.delete(k); }));
    await self.clients.claim();
  })());
});

function isMedia(url) {
  return url.origin === self.location.origin &&
         /\/(images|polaroids|journal|songs)\//.test(url.pathname);
}
function isFontFile(url) { return url.hostname === 'fonts.gstatic.com'; }
function isStyle(url) {
  return (url.origin === self.location.origin &&
          (url.pathname.endsWith('.css') || url.pathname.endsWith('/player.js'))) ||
         url.hostname === 'fonts.googleapis.com';
}

async function trim(name, max) {
  const cache = await caches.open(name);
  const keys = await cache.keys();
  const extra = keys.length - max;
  for (var i = 0; i < extra; i++) await cache.delete(keys[i]);
}

// CacheFirst + 音檔的手動 Range 切片
async function media(request, url) {
  const key = new Request(url.href);
  const cache = await caches.open(MEDIA);
  var res = await cache.match(key);
  if (!res) {
    try {
      res = await fetch(key);
    } catch (e) {
      return (await caches.match(request)) || Response.error();
    }
    if (res && (res.ok || res.type === 'opaque')) {
      await cache.put(key, res.clone());
      trim(MEDIA, MEDIA_MAX);
    }
  }
  const range = request.headers.get('range');
  if (!range || res.type === 'opaque' || !res.ok) return res;
  const buf = await res.arrayBuffer();
  const m = /bytes=(\d+)-(\d*)/.exec(range) || [];
  const start = m[1] ? parseInt(m[1], 10) : 0;
  const end = m[2] ? parseInt(m[2], 10) : buf.byteLength - 1;
  return new Response(buf.slice(start, end + 1), {
    status: 206,
    headers: {
      'Content-Type': res.headers.get('Content-Type') || 'application/octet-stream',
      'Content-Range': 'bytes ' + start + '-' + end + '/' + buf.byteLength,
      'Content-Length': String(end - start + 1),
      'Accept-Ranges': 'bytes'
    }
  });
}

self.addEventListener('fetch', function(event) {
  const request = event.request;
  if (request.method !== 'GET') return;
  const url = new URL(request.url);

  if (request.mode === 'navigate') {
    event.respondWith((async function() {
      try {
        const fresh = await fetch(request);
        const cache = await caches.open(SHELL);
        cache.put(request, fresh.clone());
        trim(SHELL, SHELL_MAX);
        return fresh;
      } catch (e) {
        return (await caches.match(request)) ||
               (await caches.match(self.registration.scope + 'index.html')) ||
               (await caches.match(self.registration.scope)) ||
               new Response('離線中,而且這一頁還沒被開過、沒存進快取。', {
                 status: 503, headers: { 'Content-Type': 'text/plain; charset=utf-8' }
               });
      }
    })());
    return;
  }

  if (isMedia(url) || isFontFile(url)) {
    event.respondWith(media(request, url));
    return;
  }

  if (isStyle(url)) {
    event.respondWith((async function() {
      const cache = await caches.open(SHELL);
      const cached = await cache.match(request);
      const network = fetch(request).then(function(fresh) {
        if (fresh.ok || fresh.type === 'opaque') cache.put(request, fresh.clone());
        return fresh;
      }).catch(function() { return null; });
      return cached || (await network) || Response.error();
    })());
  }
});
