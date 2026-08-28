#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
靜態網站建置腳本
把 ordered/ 資料夾裡的 111 篇 markdown 章節,轉成統一風格的靜態閱讀站台。
輸出到專案根目錄的 docs/(給 GitHub Pages 用)
"""

import os
import re
import shutil
import markdown as md_lib

# ---- 路徑設定：全部相對於這支腳本檔案所在的位置去推算 ----
# 預期的資料夾結構(跟 build.py 同一層的上一層):
#   專案根目錄/
#   ├── ordered/         ← 章節原始檔
#   ├── Images/           ← 你放插圖的地方(注意大寫I,配合實際使用習慣)
#   ├── songs/            ← 你放配樂的地方
#   ├── Polaroids/        ← 你放拍立得照片的地方,一章可以有好幾張
#   ├── docs/            ← 建置輸出(images/ songs/ polaroids/ 會在建置時自動從上面複製過來;GitHub Pages 從這裡發佈)
#   └── site_build/       ← 這支腳本所在的資料夾
#       ├── build.py
#       ├── templates.py
#       └── style.css
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)

SRC_DIR = os.path.join(PROJECT_ROOT, "ordered")
OUT_DIR = os.path.join(PROJECT_ROOT, "docs")
CHAPTERS_DIR = os.path.join(OUT_DIR, "chapters")
IMAGES_DIR = os.path.join(OUT_DIR, "images")
SONGS_DIR = os.path.join(OUT_DIR, "songs")
POLAROIDS_DIR = os.path.join(OUT_DIR, "polaroids")
JOURNAL_DIR = os.path.join(OUT_DIR, "journal")

# 素材來源資料夾(專案根目錄下,不在 docs/ 裡面)
# 依序嘗試這些資料夾名稱,兼容大小寫習慣不一致的情況
IMAGES_SOURCE_CANDIDATES = ["Images", "images"]
SONGS_SOURCE_CANDIDATES = ["songs", "Songs"]
POLAROIDS_SOURCE_CANDIDATES = ["Polaroids", "polaroids"]
JOURNAL_SOURCE_CANDIDATES = ["Journal", "journal"]


def find_source_dir(candidates):
    for name in candidates:
        path = os.path.join(PROJECT_ROOT, name)
        if os.path.isdir(path):
            return path
    return None

# 支援的圖片/音樂副檔名,依序嘗試比對
IMAGE_EXTS = [".jpeg", ".jpg", ".png", ".webp"]
AUDIO_EXTS = [".mp3", ".m4a", ".ogg", ".wav"]


def find_media(slug, media_dir, exts):
    """在 media_dir 底下尋找 slug + 任一副檔名的檔案,回傳找到的檔名(不含路徑),找不到回傳 None"""
    if not os.path.isdir(media_dir):
        return None
    for ext in exts:
        candidate = slug + ext
        if os.path.isfile(os.path.join(media_dir, candidate)):
            return candidate
    return None


def polaroid_index(stem, slug):
    """判斷檔名(去副檔名)是否屬於某章節的拍立得照片:
    slug.ext 是第 1 張,slug_2.ext slug_3.ext... 是額外的張數。
    是的話回傳序號,不是回傳 None。"""
    if stem == slug:
        return 1
    m = re.match(r"^" + re.escape(slug) + r"_(\d+)$", stem)
    return int(m.group(1)) if m else None


def find_polaroids(slug, media_dir, exts):
    """回傳某章節所有拍立得照片檔名,依序號排序;一張都沒有回傳空列表。"""
    if not os.path.isdir(media_dir):
        return []
    found = []
    for fname in os.listdir(media_dir):
        stem, ext = os.path.splitext(fname)
        if ext.lower() not in exts:
            continue
        idx = polaroid_index(stem, slug)
        if idx is not None:
            found.append((idx, fname))
    found.sort(key=lambda t: t[0])
    return [fname for _, fname in found]


def polaroid_matches_any_slug(stem, slugs):
    """建置時過濾用:檔名是否屬於任何一個章節的拍立得照片(含 _2 _3... 額外張數)。
    手帳頁的多頁比對也共用這個函式(slug / slug_2 / slug_3 ...)。"""
    if stem in slugs:
        return True
    m = re.match(r"^(.+)_(\d+)$", stem)
    return bool(m and m.group(1) in slugs)


def find_journal_pages(slug, media_dir, exts):
    """某章節的手帳頁,支援多頁(slug.ext 是第 1 頁,slug_2.ext ... 是後續頁);
    多頁比對邏輯跟拍立得完全一樣,直接沿用。"""
    return find_polaroids(slug, media_dir, exts)

# 六大篇章分區,對應之前排定的順序區間 (檔名數字範圍, 含頭含尾)
SECTIONS = [
    ("背景與序曲",     1,   25,  "案發後的世界觀補完、漩渦崩解與Victoria的贖罪、David的解職、學校重生、波特蘭假期、墓地告別、隔音期間的日常"),
    ("旅館連環案",     26,  42,  "Devil in Me crossover ── 五人小隊的驚魂旅館夜,及其後續"),
    ("校園與衰退",     43,  64,  "AI元年式的校園諷刺日常,與 Max 超能力逐漸消退的伏筆線"),
    ("宿舍與公路(一)", 65,  76,  "打通宿舍的鬧劇日常,以及奧林匹亞/阿斯托利亞公路旅行"),
    ("校園與公路(二)", 77,  94,  "校園日常延續,西雅圖公路旅行系列"),
    ("Victoria與Kate", 95, 115,  "四人組主線 ── 從死對頭到真心朋友的完整弧線"),
]


def get_section(num):
    for name, lo, hi, desc in SECTIONS:
        if lo <= num <= hi:
            return name
    return "未分類"


def parse_chapter_num(filename):
    m = re.match(r"^(\d+)_", filename)
    return int(m.group(1)) if m else 0


def extract_title(md_text):
    for line in md_text.splitlines():
        line = line.strip()
        if line.startswith("# "):
            return line[2:].strip()
    return "未命名章節"


def slugify(filename):
    # 去掉數字前綴與副檔名,作為輸出檔名 slug
    base = re.sub(r"^\d+_", "", filename)
    base = re.sub(r"\.md$", "", base)
    return base


def render_badges(ch):
    """首頁卡片用:章節有實際插圖/配樂/拍立得(不是佔位)才顯示對應徽章"""
    parts = []
    if ch.get("image_file"):
        parts.append('<span class="badge badge-image" title="有插圖">📷</span>')
    if ch.get("audio_file"):
        parts.append('<span class="badge badge-audio" title="有配樂">♪</span>')
    if ch.get("polaroid_files"):
        parts.append('<span class="badge badge-polaroid" title="有拍立得照片">🖼</span>')
    if ch.get("journal_files"):
        parts.append('<span class="badge badge-journal" title="有 Max 的手帳">📓</span>')
    if not parts:
        return ""
    return f'<div class="ch-badges">{"".join(parts)}</div>'


if __name__ == "__main__":
    files = sorted([f for f in os.listdir(SRC_DIR) if f.endswith(".md")])
    print(f"共找到 {len(files)} 個章節檔案")

    # 章節 slug 集合,用來過濾素材:只有檔名(去副檔名)對得上某章節的
    # 圖片/音樂才會被複製進 docs/,資料夾裡其餘不相干的檔案一律跳過
    slugs = {slugify(f) for f in files}

    from templates import BUTTERFLY_SVG, HEADER, FOOTER, HTML_SHELL, LIGHTBOX, render_player

    os.makedirs(CHAPTERS_DIR, exist_ok=True)

    # GitHub Pages 用:放一個空的 .nojekyll,避免 Jekyll 處理掉某些檔案/資料夾
    open(os.path.join(OUT_DIR, ".nojekyll"), "w").close()

    # 複製 CSS
    shutil.copy(os.path.join(os.path.dirname(__file__), "style.css"), os.path.join(OUT_DIR, "style.css"))

    # ---- 複製素材:從專案根目錄的 Images/ songs/ Polaroids/ 複製進
    # docs/images docs/songs docs/polaroids ----
    images_src = find_source_dir(IMAGES_SOURCE_CANDIDATES)
    songs_src = find_source_dir(SONGS_SOURCE_CANDIDATES)
    polaroids_src = find_source_dir(POLAROIDS_SOURCE_CANDIDATES)

    journal_src = find_source_dir(JOURNAL_SOURCE_CANDIDATES)

    os.makedirs(IMAGES_DIR, exist_ok=True)
    os.makedirs(SONGS_DIR, exist_ok=True)
    os.makedirs(POLAROIDS_DIR, exist_ok=True)
    os.makedirs(JOURNAL_DIR, exist_ok=True)

    if images_src:
        copied = skipped = 0
        for fname in os.listdir(images_src):
            stem, ext = os.path.splitext(fname)
            if ext.lower() in IMAGE_EXTS and stem in slugs:
                shutil.copy(os.path.join(images_src, fname), os.path.join(IMAGES_DIR, fname))
                copied += 1
            elif ext.lower() in IMAGE_EXTS:
                skipped += 1
        print(f"已從 {images_src} 複製 {copied} 張圖片到 docs/images/(跳過 {skipped} 張跟章節對不上的)")
    else:
        print(f"警告:找不到圖片來源資料夾(嘗試過 {IMAGES_SOURCE_CANDIDATES}),跳過圖片複製")

    if songs_src:
        copied = skipped = 0
        for fname in os.listdir(songs_src):
            stem, ext = os.path.splitext(fname)
            if ext.lower() in AUDIO_EXTS and stem in slugs:
                shutil.copy(os.path.join(songs_src, fname), os.path.join(SONGS_DIR, fname))
                copied += 1
            elif ext.lower() in AUDIO_EXTS:
                skipped += 1
        print(f"已從 {songs_src} 複製 {copied} 首歌曲到 docs/songs/(跳過 {skipped} 首跟章節對不上的)")
    else:
        print(f"警告:找不到音樂來源資料夾(嘗試過 {SONGS_SOURCE_CANDIDATES}),跳過音樂複製")

    if polaroids_src:
        copied = skipped = 0
        for fname in os.listdir(polaroids_src):
            stem, ext = os.path.splitext(fname)
            if ext.lower() in IMAGE_EXTS and polaroid_matches_any_slug(stem, slugs):
                shutil.copy(os.path.join(polaroids_src, fname), os.path.join(POLAROIDS_DIR, fname))
                copied += 1
            elif ext.lower() in IMAGE_EXTS:
                skipped += 1
        print(f"已從 {polaroids_src} 複製 {copied} 張拍立得照片到 docs/polaroids/(跳過 {skipped} 張跟章節對不上的)")
    else:
        print(f"警告:找不到拍立得來源資料夾(嘗試過 {POLAROIDS_SOURCE_CANDIDATES}),跳過拍立得複製")

    if journal_src:
        copied = skipped = 0
        for fname in os.listdir(journal_src):
            stem, ext = os.path.splitext(fname)
            if ext.lower() in IMAGE_EXTS and polaroid_matches_any_slug(stem, slugs):
                shutil.copy(os.path.join(journal_src, fname), os.path.join(JOURNAL_DIR, fname))
                copied += 1
            elif ext.lower() in IMAGE_EXTS:
                skipped += 1
        print(f"已從 {journal_src} 複製 {copied} 頁手帳到 docs/journal/(跳過 {skipped} 頁跟章節對不上的)")
    else:
        print(f"警告:找不到手帳來源資料夾(嘗試過 {JOURNAL_SOURCE_CANDIDATES}),跳過手帳複製")

    chapters = []  # 收集每章 metadata,供首頁與導覽使用
    for f in files:
        num = parse_chapter_num(f)
        with open(os.path.join(SRC_DIR, f), "r", encoding="utf-8") as fh:
            text = fh.read()
        title = extract_title(text)
        slug = slugify(f)
        chapters.append({
            "num": num,
            "title": title,
            "slug": slug,
            "section": get_section(num),
            "raw": text,
            "image_file": find_media(slug, IMAGES_DIR, IMAGE_EXTS),
            "audio_file": find_media(slug, SONGS_DIR, AUDIO_EXTS),
            "polaroid_files": find_polaroids(slug, POLAROIDS_DIR, IMAGE_EXTS),
            "journal_files": find_journal_pages(slug, JOURNAL_DIR, IMAGE_EXTS),
        })

    chapters.sort(key=lambda c: c["num"])

    # 全站播放清單:按章節順序,只收錄真的有配樂的章節(不是佔位)
    playlist = [
        {"title": c["title"], "file": c["audio_file"], "section": c["section"]}
        for c in chapters if c["audio_file"]
    ]
    print(f"播放清單共 {len(playlist)} 首歌")

    # 全站拍立得相簿:按章節順序,收錄每章的每一張拍立得照片
    all_polaroids = [
        {"title": c["title"], "slug": c["slug"], "file": f}
        for c in chapters for f in c["polaroid_files"]
    ]
    print(f"拍立得相簿共 {len(all_polaroids)} 張照片")

    # 全站手帳:按章節順序,收錄每章的每一頁手帳
    all_journal = [
        {"title": c["title"], "slug": c["slug"], "file": f}
        for c in chapters for f in c["journal_files"]
    ]
    print(f"手帳共 {len(all_journal)} 頁")

    # ---------- 產生每一章的頁面 ----------
    for i, ch in enumerate(chapters):
        body_html = md_lib.markdown(ch["raw"], extensions=["extra"])
        # 移除 markdown 轉換出的第一個 <h1>,因為我們會自己渲染標題
        body_html = re.sub(r"^<h1>.*?</h1>\s*", "", body_html, count=1)

        prev_ch = chapters[i - 1] if i > 0 else None
        next_ch = chapters[i + 1] if i < len(chapters) - 1 else None

        prev_link = f'<a href="{prev_ch["slug"]}.html">← 上一章</a>' if prev_ch else '<a class="disabled">← 上一章</a>'
        next_link = f'<a href="{next_ch["slug"]}.html">下一章 →</a>' if next_ch else '<a class="disabled">下一章 →</a>'

        image_file = ch["image_file"]
        audio_file = ch["audio_file"]

        media_parts = []
        if audio_file:
            media_parts.append(
                f'<div class="media-item media-audio">'
                f'<span class="slot-label">♪ 配樂</span>'
                f'<audio controls preload="none" src="../songs/{audio_file}"></audio>'
                f'</div>'
            )
        else:
            media_parts.append(
                '<div class="media-item media-placeholder">'
                '<span class="slot-label">♪ 配樂</span>尚未配樂'
                '</div>'
            )

        if image_file:
            media_parts.append(
                f'<div class="media-item media-image">'
                f'<span class="slot-label">📷 插圖</span>'
                f'<img src="../images/{image_file}" alt="{ch["title"]}" loading="lazy">'
                f'</div>'
            )
        else:
            media_parts.append(
                '<div class="media-item media-placeholder">'
                '<span class="slot-label">📷 插圖</span>尚未配圖'
                '</div>'
            )

        polaroid_files = ch["polaroid_files"]
        if polaroid_files:
            polaroid_cards = "".join(
                f'<div class="polaroid-card" style="--rot: {(-4 + (i % 5) * 2)}deg">'
                f'<img src="../polaroids/{f}" alt="{ch["title"]} 拍立得照片" loading="lazy">'
                f'</div>'
                for i, f in enumerate(polaroid_files)
            )
            media_parts.append(
                f'<div class="media-item media-polaroids">'
                f'<span class="slot-label">🖼 拍立得</span>'
                f'<div class="polaroid-strip">{polaroid_cards}</div>'
                f'</div>'
            )

        journal_files = ch["journal_files"]
        if journal_files:
            journal_cards = "".join(
                f'<div class="journal-page-card" style="--rot: {(-2 + (i % 3) * 2)}deg">'
                f'<img src="../journal/{f}" alt="{ch["title"]} Max 的手帳" loading="lazy">'
                f'</div>'
                for i, f in enumerate(journal_files)
            )
            media_parts.append(
                f'<div class="media-item media-journal">'
                f'<span class="slot-label">📓 Max 的手帳</span>'
                f'<div class="journal-strip">{journal_cards}</div>'
                f'</div>'
            )

        media_html = f'<div class="media-slot">{"".join(media_parts)}</div>'

        content = f"""
<main class="chapter-page">
  <div class="chapter-meta">第 {ch['num']:03d} 章 · {ch['section']}</div>
  <h1>{ch['title']}</h1>

  {media_html}

  <div class="chapter-body">
    {body_html}
  </div>

  <nav class="chapter-nav">
    {prev_link}
    <a href="../index.html" class="to-index">目錄</a>
    {next_link}
  </nav>
</main>
"""
        html = HTML_SHELL.format(
            title=f"{ch['title']} · 雙保結局同人合集",
            root="../",
            butterfly=BUTTERFLY_SVG,
            header=HEADER.format(root="../"),
            player=render_player("../", playlist),
            content=content,
            footer=FOOTER,
            lightbox=LIGHTBOX,
        )
        with open(os.path.join(CHAPTERS_DIR, f"{ch['slug']}.html"), "w", encoding="utf-8") as out:
            out.write(html)

    print(f"已產生 {len(chapters)} 個章節頁面")

    # ---------- 產生首頁 ----------
    section_blocks = []
    for idx, (name, lo, hi, desc) in enumerate(SECTIONS, start=1):
        section_chapters = [c for c in chapters if lo <= c["num"] <= hi]
        cards = "\n".join(
            f'''<a class="chapter-card" href="chapters/{c['slug']}.html">
                  {render_badges(c)}
                  <div class="ch-num">{c['num']:03d}</div>
                  <div class="ch-title">{c['title']}</div>
                </a>'''
            for c in section_chapters
        )
        section_blocks.append(f"""
<div class="section-block">
  <div class="section-head">
    <span class="section-num">{idx:02d}</span>
    <h2>{name}</h2>
  </div>
  <p class="section-desc">{desc}</p>
  <div class="chapter-grid">
    {cards}
  </div>
</div>
""")

    hero = f"""
<div class="hero">
  <div class="eyebrow">LIFE IS STRANGE · FAN FICTION ARCHIVE</div>
  <h1>雙保結局</h1>
  <p class="subtitle">如果那年風暴之後，小鎮與 Chloe 都活了下來</p>
  <p class="premise">
    官方原作把玩家推向一道殘酷的電車難題——<strong>犧牲小鎮，或是犧牲 Chloe</strong>，
    二選一，沒有第三條路。這部合集是對那道難題的另一種回答：<br><br>
    <strong>如果 somehow，兩者都保住了呢？</strong><br><br>
    這裡收錄了{len(chapters)}章，從風暴退去的第一個清晨，到公路盡頭的星空，
    記錄著 Chloe 與 Max，還有這座小鎮上每一個劫後餘生的人，
    如何在一個「不該存在」的結局裡，笨拙卻真實地活下去。
  </p>
</div>
<div class="hero-divider">❦</div>
"""

    index_content = hero + '<div class="sections">' + "\n".join(section_blocks) + "</div>"
    index_html = HTML_SHELL.format(
        title="雙保結局 · 拍立得檔案",
        root="",
        butterfly=BUTTERFLY_SVG,
        header=HEADER.format(root=""),
        player=render_player("", playlist),
        content=index_content,
        footer=FOOTER,
        lightbox=LIGHTBOX,
    )
    with open(os.path.join(OUT_DIR, "index.html"), "w", encoding="utf-8") as out:
        out.write(index_html)

    print("首頁已產生:index.html")

    # ---------- 產生拍立得相簿頁 ----------
    if all_polaroids:
        gallery_cards = "\n".join(
            f'''<a class="gallery-card" href="chapters/{p['slug']}.html">
                  <div class="polaroid-card polaroid-card-lg" style="--rot: {(-4 + (i % 5) * 2)}deg">
                    <img src="polaroids/{p['file']}" alt="{p['title']} 拍立得照片" loading="lazy">
                    <div class="polaroid-caption">{p['title']}</div>
                  </div>
                </a>'''
            for i, p in enumerate(all_polaroids)
        )
        gallery_body = f'<div class="gallery-grid">{gallery_cards}</div>'
    else:
        gallery_body = '<p class="gallery-empty">目前還沒有拍立得照片。</p>'

    gallery_content = f"""
<main class="gallery-page">
  <div class="gallery-hero">
    <div class="eyebrow">POLAROID ARCHIVE</div>
    <h1>拍立得相簿</h1>
    <p class="subtitle">散落在故事裡的{len(all_polaroids)}張快照,點一張放大看,再點「回到章節」就能翻到它出現的地方</p>
  </div>
  {gallery_body}
</main>
"""
    gallery_html = HTML_SHELL.format(
        title="拍立得相簿 · 雙保結局同人合集",
        root="",
        butterfly=BUTTERFLY_SVG,
        header=HEADER.format(root=""),
        player=render_player("", playlist),
        content=gallery_content,
        footer=FOOTER,
        lightbox=LIGHTBOX,
    )
    with open(os.path.join(OUT_DIR, "polaroids.html"), "w", encoding="utf-8") as out:
        out.write(gallery_html)

    print("拍立得相簿已產生:polaroids.html")

    # ---------- 產生 Max 的手帳頁 ----------
    if all_journal:
        journal_cards = "\n".join(
            f'''<a class="journal-card" href="chapters/{p['slug']}.html" style="--rot: {(-2 + (i % 3) * 2)}deg">
                  <figure class="journal-page">
                    <img src="journal/{p['file']}" alt="{p['title']} Max 的手帳" loading="lazy">
                    <figcaption class="journal-caption">{p['title']}</figcaption>
                  </figure>
                </a>'''
            for i, p in enumerate(all_journal)
        )
        journal_body = f'<div class="gallery-grid journal-grid">{journal_cards}</div>'
    else:
        journal_body = '<p class="gallery-empty">目前還沒有手帳。</p>'

    journal_content = f"""
<main class="gallery-page journal-gallery">
  <div class="gallery-hero">
    <div class="eyebrow">MAX'S JOURNAL</div>
    <h1>Max 的手帳</h1>
    <p class="subtitle">Max 隨手記下的手繪日記,目前收錄 {len(all_journal)} 頁,點一頁翻開來看,再點「回到章節」就能讀那一章</p>
  </div>
  {journal_body}
</main>
"""
    journal_html = HTML_SHELL.format(
        title="Max 的手帳 · 雙保結局同人合集",
        root="",
        butterfly=BUTTERFLY_SVG,
        header=HEADER.format(root=""),
        player=render_player("", playlist),
        content=journal_content,
        footer=FOOTER,
        lightbox=LIGHTBOX,
    )
    with open(os.path.join(OUT_DIR, "journal.html"), "w", encoding="utf-8") as out:
        out.write(journal_html)

    print("Max 的手帳已產生:journal.html")
    print(f"\n完成！網站輸出於: {OUT_DIR}")

