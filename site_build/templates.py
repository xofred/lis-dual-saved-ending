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
  var currentIndex = -1;

  if (!toggle) { return; }

  toggle.addEventListener('click', function() {
    var isHidden = panel.hasAttribute('hidden');
    if (isHidden) {
      panel.removeAttribute('hidden');
      toggle.setAttribute('aria-expanded', 'true');
    } else {
      panel.setAttribute('hidden', '');
      toggle.setAttribute('aria-expanded', 'false');
    }
  });

  if (!playlist.length) { return; }

  function highlight() {
    items.forEach(function(el, i) {
      el.classList.toggle('playing', i === currentIndex);
    });
  }

  function loadTrack(i, autoplay) {
    currentIndex = (i + playlist.length) % playlist.length;
    var track = playlist[currentIndex];
    audio.src = track.src;
    nowTitle.textContent = track.title;
    highlight();
    if (autoplay) {
      audio.play().catch(function() {});
    }
  }

  items.forEach(function(el, i) {
    el.addEventListener('click', function() { loadTrack(i, true); });
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
    playlist 是 [{"title": 章節標題, "file": 配樂檔名}, ...],
    只收錄真的有配樂的章節(不是佔位)。"""
    items = [{"title": p["title"], "src": root + "songs/" + p["file"]} for p in playlist]

    if items:
        list_html = "\n".join(
            '      <li class="playlist-item" data-index="{0}">{1}</li>'.format(i, it["title"])
            for i, it in enumerate(items)
        )
    else:
        list_html = '      <li class="playlist-empty">目前還沒有配樂</li>'

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
</body>
</html>
"""
