# -*- coding: utf-8 -*-
"""共用 HTML 片段"""

import json

BUTTERFLY_SVG = """
<div class="butterfly" id="butterfly" aria-hidden="true">
  <svg viewBox="0 0 100 100">
    <g transform="translate(50,50)">
      <path class="wing left" d="M0,-4 C-18,-30 -45,-25 -42,-2 C-45,18 -20,22 0,4 Z" />
      <path class="wing right" d="M0,-4 C18,-30 45,-25 42,-2 C45,18 20,22 0,4 Z" />
      <ellipse cx="0" cy="0" rx="2.2" ry="10" fill="#26313F"/>
    </g>
  </svg>
</div>
<script>
  // 蝴蝶跟隨捲動的位置,緩慢地在頁面右側遊走
  (function() {
    const b = document.getElementById('butterfly');
    if (!b) return;
    let ticking = false;
    function place() {
      const scrollFrac = window.scrollY / Math.max(1, document.body.scrollHeight - window.innerHeight);
      const top = 80 + scrollFrac * (window.innerHeight - 160);
      b.style.top = top + 'px';
      b.style.right = (18 + Math.sin(scrollFrac * 8) * 10) + 'px';
      ticking = false;
    }
    window.addEventListener('scroll', function() {
      if (!ticking) { requestAnimationFrame(place); ticking = true; }
    });
    place();
  })();
</script>
"""

HEADER = """
<header class="site-header">
  <a href="{root}index.html" class="brand">雙保結局 · 拍立得檔案</a>
  <nav>
    <a href="{root}index.html">目錄</a>
    <a href="{root}polaroids.html">拍立得相簿</a>
    <a href="{root}journal.html">Max 的手帳</a>
  </nav>
</header>
"""

PLAYER_TEMPLATE = """
<div class="player-widget" id="playerWidget">
  <button class="player-toggle" id="playerToggle" type="button" aria-expanded="false">♪ 歌單</button>
  <div class="player-panel" id="playerPanel" hidden>
    <div class="player-now" id="nowPlayingTitle">尚未播放</div>
    <audio id="playerAudio" preload="none"></audio>
    <div class="player-controls">
      <button id="playerPrev" type="button" title="上一首">⏮</button>
      <button id="playerPlay" type="button" title="播放/暫停">▶</button>
      <button id="playerNext" type="button" title="下一首">⏭</button>
    </div>
    <ul class="playlist" id="playlistItems">
__LIST_HTML__
    </ul>
  </div>
</div>
<script>
(function() {
  var playlist = __PLAYLIST_JSON__;
  var toggle = document.getElementById('playerToggle');
  var panel = document.getElementById('playerPanel');
  var audio = document.getElementById('playerAudio');
  var playBtn = document.getElementById('playerPlay');
  var prevBtn = document.getElementById('playerPrev');
  var nextBtn = document.getElementById('playerNext');
  var nowTitle = document.getElementById('nowPlayingTitle');
  var items = document.querySelectorAll('#playlistItems .playlist-item');
  var groupEls = document.querySelectorAll('#playlistItems .playlist-group');
  var currentIndex = -1;

  if (!toggle) { return; }

  toggle.addEventListener('click', function() {
    var isHidden = panel.hasAttribute('hidden');
    if (isHidden) {
      panel.removeAttribute('hidden');
      toggle.setAttribute('aria-expanded', 'true');
      if (currentIndex !== -1) revealCurrent();
    } else {
      panel.setAttribute('hidden', '');
      toggle.setAttribute('aria-expanded', 'false');
    }
  });

  if (!playlist.length) { return; }

  // 歌單按篇章分區摺疊:點標題展開/收合,預設只展開第一個分區
  function setGroupOpen(g, open) {
    g.classList.toggle('open', open);
    var head = g.querySelector('.playlist-group-head');
    if (head) head.setAttribute('aria-expanded', open ? 'true' : 'false');
  }
  [].forEach.call(groupEls, function(g, i) {
    var head = g.querySelector('.playlist-group-head');
    if (head) head.addEventListener('click', function() {
      setGroupOpen(g, !g.classList.contains('open'));
    });
    setGroupOpen(g, i === 0);
  });

  // 展開當前曲目所屬分區,並把它捲進可視範圍
  function revealCurrent() {
    var el = items[currentIndex];
    if (!el) return;
    var g = el.closest ? el.closest('.playlist-group') : null;
    if (g) setGroupOpen(g, true);
    requestAnimationFrame(function() { el.scrollIntoView({ block: 'nearest' }); });
  }

  function highlight() {
    [].forEach.call(items, function(el) {
      var i = parseInt(el.getAttribute('data-index'), 10);
      el.classList.toggle('playing', i === currentIndex);
    });
  }

  // 「正在播放」標題:有對應章節就渲染成連結,點了翻到那一章
  function setNowPlaying(track) {
    nowTitle.innerHTML = '';
    if (track.href) {
      var a = document.createElement('a');
      a.className = 'player-now-link';
      a.href = track.href;
      a.textContent = track.title + ' ↗';
      nowTitle.appendChild(a);
    } else {
      nowTitle.textContent = track.title;
    }
  }

  function loadTrack(i, autoplay) {
    currentIndex = (i + playlist.length) % playlist.length;
    var track = playlist[currentIndex];
    audio.src = track.src;
    setNowPlaying(track);
    highlight();
    revealCurrent();
    if (autoplay) {
      audio.play().catch(function() {});
    }
  }

  [].forEach.call(items, function(el) {
    var i = parseInt(el.getAttribute('data-index'), 10);
    el.addEventListener('click', function() { loadTrack(i, true); });
    // 列右側的章節鈕:直接導覽,別觸發播放
    var link = el.querySelector('.playlist-item-link');
    if (link) link.addEventListener('click', function(e) { e.stopPropagation(); });
  });

  playBtn.addEventListener('click', function() {
    if (currentIndex === -1) { loadTrack(0, true); return; }
    if (audio.paused) { audio.play().catch(function() {}); }
    else { audio.pause(); }
  });

  prevBtn.addEventListener('click', function() {
    loadTrack(currentIndex === -1 ? playlist.length - 1 : currentIndex - 1, true);
  });

  nextBtn.addEventListener('click', function() {
    loadTrack(currentIndex === -1 ? 0 : currentIndex + 1, true);
  });

  audio.addEventListener('play', function() {
    playBtn.textContent = '⏸';
    toggle.classList.add('is-playing');
  });
  audio.addEventListener('pause', function() {
    playBtn.textContent = '▶';
    toggle.classList.remove('is-playing');
  });
  audio.addEventListener('ended', function() {
    loadTrack(currentIndex + 1, true);
  });
})();
</script>
"""


def render_player(root, playlist):
    """全站播放清單選單。root 是目前頁面到站台根目錄的相對路徑前綴,
    playlist 是 [{"title": 章節標題, "file": 配樂檔名, "section": 篇章分區}, ...],
    只收錄真的有配樂的章節(不是佔位)。清單依 playlist 順序(即章節順序)
    按篇章分區分組,前端可逐區摺疊,避免歌一多就變成小框裡的長捲軸。"""
    items = [
        {
            "title": p["title"],
            "src": root + "songs/" + p["file"],
            "section": p.get("section", ""),
            "href": (root + "chapters/" + p["slug"] + ".html") if p.get("slug") else "",
        }
        for p in playlist
    ]

    if not items:
        list_html = '      <li class="playlist-empty">目前還沒有配樂</li>'
    else:
        section_order = []
        by_section = {}
        for i, it in enumerate(items):
            sec = it["section"] or "未分類"
            if sec not in by_section:
                by_section[sec] = []
                section_order.append(sec)
            by_section[sec].append((i, it))

        blocks = []
        for sec in section_order:
            lis = "\n".join(
                '          <li class="playlist-item" data-index="{0}">'
                '<span class="playlist-item-title">{1}</span>'
                '<a class="playlist-item-link" href="{2}" aria-label="翻到「{1}」這一章">↗</a>'
                '</li>'.format(i, it["title"], it["href"])
                for i, it in by_section[sec]
            )
            blocks.append(
                '      <li class="playlist-group">\n'
                '        <button class="playlist-group-head" type="button" aria-expanded="false">\n'
                '          <span class="playlist-group-name">{sec}</span>\n'
                '          <span class="playlist-group-count">{n}</span>\n'
                '        </button>\n'
                '        <ul class="playlist-group-items">\n'
                '{lis}\n'
                '        </ul>\n'
                '      </li>'.format(sec=sec, n=len(by_section[sec]), lis=lis)
            )
        list_html = "\n".join(blocks)

    return (
        PLAYER_TEMPLATE
        .replace("__LIST_HTML__", list_html)
        .replace("__PLAYLIST_JSON__", json.dumps(items, ensure_ascii=False))
    )


FOOTER = """
<footer class="site-footer">
  <div class="disclaimer">
    這是一部基於《奇異人生》（Life is Strange）的非營利同人創作合集，<br>
    設定前提為「雙保結局」——小鎮與 Chloe 皆倖存的另一條時間線。<br>
    原作版權歸 Dontnod Entertainment / Square Enix 所有，本作不涉及任何商業用途。
  </div>
</footer>
"""

LIGHTBOX = """
<div class="lightbox" id="lightbox" hidden aria-hidden="true" role="dialog" aria-modal="true" aria-label="放大檢視">
  <button class="lightbox-close" id="lightboxClose" type="button" aria-label="關閉">&times;</button>
  <button class="lightbox-nav lightbox-prev" id="lightboxPrev" type="button" aria-label="上一張">&lsaquo;</button>
  <button class="lightbox-nav lightbox-next" id="lightboxNext" type="button" aria-label="下一張">&rsaquo;</button>
  <figure class="lightbox-figure" id="lightboxFigure">
    <img class="lightbox-img" id="lightboxImg" alt="">
    <figcaption class="lightbox-caption" id="lightboxCaption"></figcaption>
  </figure>
</div>
<script>
(function() {
  var box = document.getElementById('lightbox');
  if (!box) return;
  var figure = document.getElementById('lightboxFigure');
  var imgEl = document.getElementById('lightboxImg');
  var capEl = document.getElementById('lightboxCaption');
  var closeBtn = document.getElementById('lightboxClose');
  var prevBtn = document.getElementById('lightboxPrev');
  var nextBtn = document.getElementById('lightboxNext');

  var idx = 0;
  var lastFocus = null;
  var groups = { polaroid: [], journal: [] };
  var slides = [];          // 目前作用中的那一組
  var kind = 'polaroid';    // polaroid = 顯影;journal = 翻頁
  var animTimer = null;
  var reduceMotion = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  var ANIM_CLASSES = ['developing', 'developing-quick', 'flipping', 'flipping-quick', 'flip-back'];
  var ANIM = {
    polaroid: { open: 'developing', step: 'developing-quick', clearAfter: 1200 },
    journal:  { open: 'flipping',   step: 'flipping-quick',   clearAfter: 900 }
  };

  // 拍立得:打開時完整顯影,左右切換只做快速淡入。
  // 手帳:打開時整頁翻入,左右切換做快速翻頁(往回翻時鉸鏈換到右側)。
  function playAnim(mode, back) {
    ANIM_CLASSES.forEach(function(c) { imgEl.classList.remove(c); });
    if (reduceMotion || !mode) return;
    void imgEl.offsetWidth;  // 強制 reflow,讓同一元素能重新觸發動畫
    var cfg = ANIM[kind];
    imgEl.classList.add(mode === 'open' ? cfg.open : cfg.step);
    if (kind === 'journal' && mode === 'step' && back) imgEl.classList.add('flip-back');
    clearTimeout(animTimer);
    animTimer = setTimeout(function() {
      ANIM_CLASSES.forEach(function(c) { imgEl.classList.remove(c); });
    }, cfg.clearAfter);
  }

  // 收集頁面上兩種可放大的素材(各自獨立導覽,不會互相翻到):
  //   .polaroid-card               章節頁的拍立得小卡 + 相簿頁包在 <a> 裡的大卡
  //   .journal-page-card / .journal-card  章節頁的手帳頁 + 手帳頁包在 <a> 裡的整頁
  // (章節插圖 .media-image 不放大,那是給讀者順順讀的配圖)
  function collect(selector, k, capSel) {
    [].forEach.call(document.querySelectorAll(selector), function(card) {
      var img = card.querySelector('img');
      if (!img) return;
      var capNode = capSel ? card.querySelector(capSel) : null;
      var link = card.closest ? card.closest('a') : null;
      var group = groups[k];
      var slideIndex = group.length;
      group.push({
        src: img.getAttribute('src'),
        caption: capNode ? capNode.textContent.trim() : '',
        href: link ? link.getAttribute('href') : ''
      });
      var openThis = function(e) { if (e) e.preventDefault(); open(k, slideIndex); };
      img.addEventListener('click', openThis);
      // 相簿/手帳頁:整張卡是連往章節的連結,改成先開燈箱,燈箱裡再提供「回到章節」
      if (link) link.addEventListener('click', openThis);
    });
  }

  collect('.polaroid-card', 'polaroid', '.polaroid-caption');
  collect('.journal-page-card, .journal-card', 'journal', '.journal-caption');

  if (!groups.polaroid.length && !groups.journal.length) return;

  function render(mode, back) {
    var s = slides[idx];
    if (imgEl.getAttribute('src') !== s.src) imgEl.src = s.src;
    figure.classList.toggle('is-journal', kind === 'journal');
    if (imgEl.complete && imgEl.naturalWidth) {
      playAnim(mode, back);
    } else {
      imgEl.onload = function() { playAnim(mode, back); };
    }
    var parts = [];
    if (s.caption) parts.push('<span class="lightbox-title"></span>');
    if (slides.length > 1) parts.push('<span class="lightbox-count">' + (idx + 1) + ' / ' + slides.length + '</span>');
    capEl.innerHTML = parts.join('');
    var titleSpan = capEl.querySelector('.lightbox-title');
    if (titleSpan) titleSpan.textContent = s.caption;
    if (s.href) {
      var a = document.createElement('a');
      a.className = 'lightbox-link';
      a.href = s.href;
      a.textContent = '回到章節 →';
      capEl.appendChild(a);
    }
    var multi = slides.length > 1;
    prevBtn.hidden = !multi;
    nextBtn.hidden = !multi;
  }

  function open(k, i) {
    kind = k;
    slides = groups[k];
    idx = i;
    lastFocus = document.activeElement;
    box.setAttribute('aria-label', k === 'journal' ? '手帳放大檢視' : '拍立得放大檢視');
    render('open', false);
    box.removeAttribute('hidden');
    box.setAttribute('aria-hidden', 'false');
    document.body.style.overflow = 'hidden';
    closeBtn.focus();
    document.addEventListener('keydown', onKey);
  }

  function close() {
    box.setAttribute('hidden', '');
    box.setAttribute('aria-hidden', 'true');
    document.body.style.overflow = '';
    clearTimeout(animTimer);
    ANIM_CLASSES.forEach(function(c) { imgEl.classList.remove(c); });
    imgEl.onload = null;
    imgEl.removeAttribute('src');
    document.removeEventListener('keydown', onKey);
    if (lastFocus && lastFocus.focus) lastFocus.focus();
  }

  function step(d) {
    idx = (idx + d + slides.length) % slides.length;
    render('step', d < 0);
  }

  function onKey(e) {
    if (e.key === 'Escape') close();
    else if (e.key === 'ArrowLeft') step(-1);
    else if (e.key === 'ArrowRight') step(1);
  }

  closeBtn.addEventListener('click', close);
  prevBtn.addEventListener('click', function() { step(-1); });
  nextBtn.addEventListener('click', function() { step(1); });
  box.addEventListener('click', function(e) {
    if (e.target === box || e.target === figure) close();
  });

  // 手機:左右滑動切換,下滑關閉
  var sx = 0, sy = 0;
  box.addEventListener('touchstart', function(e) {
    sx = e.touches[0].clientX; sy = e.touches[0].clientY;
  }, { passive: true });
  box.addEventListener('touchend', function(e) {
    var dx = e.changedTouches[0].clientX - sx;
    var dy = e.changedTouches[0].clientY - sy;
    if (Math.abs(dx) > 50 && Math.abs(dx) > Math.abs(dy)) step(dx < 0 ? 1 : -1);
    else if (dy > 90 && Math.abs(dy) > Math.abs(dx)) close();
  }, { passive: true });
})();
</script>
"""

HTML_SHELL = """<!DOCTYPE html>
<html lang="zh-Hant">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}</title>
<link rel="stylesheet" href="{root}style.css">
</head>
<body>
{butterfly}
{header}
{player}
{content}
{footer}
{lightbox}
{sw_register}
</body>
</html>
"""

# 頁面裡註冊 Service Worker 的小片段。__ROOT__ 會在建置時換成該頁到站台根的相對前綴,
# 讓 sw.js 一律從站台根註冊(scope 才涵蓋整站)。
SW_REGISTER = """
<script>
if ('serviceWorker' in navigator) {
  window.addEventListener('load', function() {
    navigator.serviceWorker.register('__ROOT__sw.js', { updateViaCache: 'none' }).catch(function() {});
  });
}
</script>
"""

# Service Worker 本體。build.py 會把 __CACHE_VERSION__ 換成建置時間戳再寫出 docs/sw.js。
# 策略:
#   - 頁面導覽 → NetworkFirst(線上永遠拿最新章節,離線回退曾開過的快取)
#   - 圖片/拍立得/手帳/音檔/字型檔 → CacheFirst(開過看過聽過的,網路抽風照樣可用)
#     音檔額外做手動 Range 切片,拖動進度條才不會壞
#   - CSS / 字型 CSS → StaleWhileRevalidate
# HTML 走 NetworkFirst、又沒有獨立的 JS bundle,所以直接 skipWaiting 不會有版本錯位。
SERVICE_WORKER = """/* 由 build.py 產生,請勿手動編輯 */
const VERSION = '__CACHE_VERSION__';
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
         /\\/(images|polaroids|journal|songs)\\//.test(url.pathname);
}
function isFontFile(url) { return url.hostname === 'fonts.gstatic.com'; }
function isStyle(url) {
  return (url.origin === self.location.origin && url.pathname.endsWith('.css')) ||
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
  const m = /bytes=(\\d+)-(\\d*)/.exec(range) || [];
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
"""
