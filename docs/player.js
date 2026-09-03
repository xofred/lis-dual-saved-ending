/* 由 build.py 產生:全站播放清單資料 + 播放器邏輯。只有配樂變動時才會變。 */
(function() {
  var widget = document.getElementById('playerWidget');
  if (!widget) return;
  var root = widget.getAttribute('data-root') || '';
  var playlist = ([{"title": "雙保結局", "file": "dual_saved_ending_family_reunion.mp3", "section": "背景與序曲", "slug": "dual_saved_ending_family_reunion"}, {"title": "臥室,唱片轉動的聲音", "file": "bedroom_lua.mp3", "section": "背景與序曲", "slug": "bedroom_lua"}, {"title": "AI 作曲速成班", "file": "ai_music_class.mp3", "section": "校園與衰退", "slug": "ai_music_class"}, {"title": "遲來的舞台", "file": "rachel_song.mp3", "section": "校園與衰退", "slug": "rachel_song"}, {"title": "海岸線露營", "file": "coastal_camping.mp3", "section": "校園與衰退", "slug": "coastal_camping"}, {"title": "滔天暗示", "file": "song_from_afar.mp3", "section": "校園與衰退", "slug": "song_from_afar"}, {"title": "微距魔法與天台午後", "file": "macro_magic_rooftop.mp3", "section": "Victoria與Kate", "slug": "macro_magic_rooftop"}, {"title": "星空夜話", "file": "starlit_talk.mp3", "section": "Victoria與Kate", "slug": "starlit_talk"}, {"title": "意外投屏事件", "file": "mv_incident.mp3", "section": "Victoria與Kate", "slug": "mv_incident"}, {"title": "下海追逐戰", "file": "ocean_chase.mp3", "section": "畢業季終章", "slug": "ocean_chase"}, {"title": "相框與日記", "file": "frame_and_diary.mp3", "section": "畢業季終章", "slug": "frame_and_diary"}, {"title": "不分開的約定", "file": "staying_together.mp3", "section": "波特蘭", "slug": "staying_together"}, {"title": "一級通水測試", "file": "irrigation_test.mp3", "section": "波特蘭", "slug": "irrigation_test"}, {"title": "末頁的心裡話", "file": "final_page_confessions.mp3", "section": "波特蘭", "slug": "final_page_confessions"}, {"title": "001號委託", "file": "order_001.mp3", "section": "波特蘭", "slug": "order_001"}, {"title": "收工儀式", "file": "closing_ritual.mp3", "section": "波特蘭", "slug": "closing_ritual"}, {"title": "種子與微光", "file": "seeds_and_light.mp3", "section": "波特蘭", "slug": "seeds_and_light"}, {"title": "重返阿卡迪亞灣", "file": "return_to_arcadia.mp3", "section": "波特蘭", "slug": "return_to_arcadia"}, {"title": "晚餐哲學交流", "file": "supper_philosophy_discussion.mp3", "section": "波特蘭", "slug": "supper_philosophy_discussion"}]).map(function(p) {
    return {
      title: p.title,
      section: p.section || '',
      src: root + 'songs/' + p.file,
      href: p.slug ? (root + 'chapters/' + p.slug + '.html') : ''
    };
  });

  var toggle = document.getElementById('playerToggle');
  var panel = document.getElementById('playerPanel');
  var audio = document.getElementById('playerAudio');
  var playBtn = document.getElementById('playerPlay');
  var prevBtn = document.getElementById('playerPrev');
  var nextBtn = document.getElementById('playerNext');
  var nowTitle = document.getElementById('nowPlayingTitle');
  var listEl = document.getElementById('playlistItems');
  var currentIndex = -1;

  if (!toggle) return;

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

  // ---- 依篇章分區,把清單建進 DOM ----
  if (!playlist.length) {
    var empty = document.createElement('li');
    empty.className = 'playlist-empty';
    empty.textContent = '目前還沒有配樂';
    listEl.appendChild(empty);
    return;
  }

  var order = [], bySection = {};
  playlist.forEach(function(t, i) {
    var sec = t.section || '未分類';
    if (!bySection[sec]) { bySection[sec] = []; order.push(sec); }
    bySection[sec].push(i);
  });
  order.forEach(function(sec) {
    var groupLi = document.createElement('li');
    groupLi.className = 'playlist-group';
    var head = document.createElement('button');
    head.className = 'playlist-group-head';
    head.type = 'button';
    head.setAttribute('aria-expanded', 'false');
    var nm = document.createElement('span');
    nm.className = 'playlist-group-name';
    nm.textContent = sec;
    var ct = document.createElement('span');
    ct.className = 'playlist-group-count';
    ct.textContent = String(bySection[sec].length);
    head.appendChild(nm);
    head.appendChild(ct);
    var sub = document.createElement('ul');
    sub.className = 'playlist-group-items';
    bySection[sec].forEach(function(idx) {
      var t = playlist[idx];
      var li = document.createElement('li');
      li.className = 'playlist-item';
      li.setAttribute('data-index', String(idx));
      var ts = document.createElement('span');
      ts.className = 'playlist-item-title';
      ts.textContent = t.title;
      li.appendChild(ts);
      if (t.href) {
        var a = document.createElement('a');
        a.className = 'playlist-item-link';
        a.href = t.href;
        a.setAttribute('aria-label', '翻到「' + t.title + '」這一章');
        a.textContent = '\u2197';
        li.appendChild(a);
      }
      sub.appendChild(li);
    });
    groupLi.appendChild(head);
    groupLi.appendChild(sub);
    listEl.appendChild(groupLi);
  });

  var items = listEl.querySelectorAll('.playlist-item');
  var groupEls = listEl.querySelectorAll('.playlist-group');

  // 歌單按篇章分區摺疊:點標題展開/收合,預設只展開第一個分區
  function setGroupOpen(g, open) {
    g.classList.toggle('open', open);
    var h = g.querySelector('.playlist-group-head');
    if (h) h.setAttribute('aria-expanded', open ? 'true' : 'false');
  }
  [].forEach.call(groupEls, function(g, i) {
    var h = g.querySelector('.playlist-group-head');
    if (h) h.addEventListener('click', function() {
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
      a.textContent = track.title + ' \u2197';
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
    if (autoplay) audio.play().catch(function() {});
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
    if (audio.paused) audio.play().catch(function() {});
    else audio.pause();
  });
  prevBtn.addEventListener('click', function() {
    loadTrack(currentIndex === -1 ? playlist.length - 1 : currentIndex - 1, true);
  });
  nextBtn.addEventListener('click', function() {
    loadTrack(currentIndex === -1 ? 0 : currentIndex + 1, true);
  });
  audio.addEventListener('play', function() {
    playBtn.textContent = '\u23f8';
    toggle.classList.add('is-playing');
  });
  audio.addEventListener('pause', function() {
    playBtn.textContent = '\u25b6';
    toggle.classList.remove('is-playing');
  });
  audio.addEventListener('ended', function() {
    loadTrack(currentIndex + 1, true);
  });
})();
