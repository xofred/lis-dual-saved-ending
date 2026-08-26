# -*- coding: utf-8 -*-
"""共用 HTML 片段"""

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
  </nav>
</header>
"""

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
{content}
{footer}
</body>
</html>
"""
