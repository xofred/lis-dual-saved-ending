/* 由 build.py 產生:全站播放清單資料 + 播放器邏輯。只有配樂變動時才會變。 */
(function() {
  var widget = document.getElementById('playerWidget');
  if (!widget) return;
  var root = widget.getAttribute('data-root') || '';
  var playlist = ([{"title": "雙保結局", "file": "dual_saved_ending_family_reunion.mp3", "section": "背景與序曲", "slug": "dual_saved_ending_family_reunion", "cover": "images/dual_saved_ending_family_reunion.jpeg"}, {"title": "故人", "file": "old_friends.mp3", "section": "背景與序曲", "slug": "old_friends", "cover": "images/old_friends.jpeg"}, {"title": "父親的墓", "file": "father_grave.mp3", "section": "背景與序曲", "slug": "father_grave", "cover": "images/father_grave.jpeg"}, {"title": "臥室,唱片轉動的聲音", "file": "bedroom_lua.mp3", "section": "背景與序曲", "slug": "bedroom_lua", "cover": "images/bedroom_lua.jpeg"}, {"title": "AI 作曲速成班", "file": "ai_music_class.mp3", "section": "校園與衰退", "slug": "ai_music_class", "cover": "images/ai_music_class.jpeg"}, {"title": "遲來的舞台", "file": "rachel_song.mp3", "section": "校園與衰退", "slug": "rachel_song", "cover": "images/rachel_song.jpeg"}, {"title": "海岸線露營", "file": "coastal_camping.mp3", "section": "校園與衰退", "slug": "coastal_camping", "cover": "polaroids/coastal_camping.jpeg"}, {"title": "滔天暗示", "file": "song_from_afar.mp3", "section": "校園與衰退", "slug": "song_from_afar", "cover": "images/song_from_afar.jpeg"}, {"title": "微距魔法與天台午後", "file": "macro_magic_rooftop.mp3", "section": "Victoria與Kate", "slug": "macro_magic_rooftop", "cover": "polaroids/macro_magic_rooftop.jpeg"}, {"title": "星空夜話", "file": "starlit_talk.mp3", "section": "Victoria與Kate", "slug": "starlit_talk", "cover": "images/starlit_talk.jpeg"}, {"title": "意外投屏事件", "file": "mv_incident.mp3", "section": "Victoria與Kate", "slug": "mv_incident", "cover": "images/mv_incident.jpeg"}, {"title": "下海追逐戰", "file": "ocean_chase.mp3", "section": "畢業季終章", "slug": "ocean_chase", "cover": "polaroids/ocean_chase.jpeg"}, {"title": "相框與日記", "file": "frame_and_diary.mp3", "section": "畢業季終章", "slug": "frame_and_diary", "cover": "polaroids/frame_and_diary.jpeg"}, {"title": "不分開的約定", "file": "staying_together.mp3", "section": "珍珠區的天台", "slug": "staying_together", "cover": "images/staying_together.jpeg"}, {"title": "一級通水測試", "file": "irrigation_test.mp3", "section": "珍珠區的天台", "slug": "irrigation_test", "cover": "polaroids/irrigation_test.jpeg"}, {"title": "末頁的心裡話", "file": "final_page_confessions.mp3", "section": "匠魂與鋼鐵車廂", "slug": "final_page_confessions", "cover": "images/final_page_confessions.jpeg"}, {"title": "001號委託", "file": "order_001.mp3", "section": "匠魂與鋼鐵車廂", "slug": "order_001", "cover": "polaroids/order_001.jpeg"}, {"title": "收工儀式", "file": "closing_ritual.mp3", "section": "匠魂與鋼鐵車廂", "slug": "closing_ritual", "cover": "images/closing_ritual.jpeg"}, {"title": "種子與微光", "file": "seeds_and_light.mp3", "section": "暑假與長輩認證", "slug": "seeds_and_light", "cover": "polaroids/seeds_and_light.jpeg"}, {"title": "重返阿卡迪亞灣", "file": "return_to_arcadia.mp3", "section": "暑假與長輩認證", "slug": "return_to_arcadia", "cover": "polaroids/return_to_arcadia.jpeg"}, {"title": "晚餐哲學交流", "file": "supper_philosophy_discussion.mp3", "section": "青年機械教室", "slug": "supper_philosophy_discussion", "cover": "images/supper_philosophy_discussion.jpeg"}, {"title": "壁畫日和長者探班", "file": "mural_day_and_visit.mp3", "section": "青年機械教室", "slug": "mural_day_and_visit", "cover": "images/mural_day_and_visit.jpeg"}, {"title": "風雨方舟", "file": "storm_system_test.mp3", "section": "青年機械教室", "slug": "storm_system_test", "cover": "polaroids/storm_system_test.jpeg"}, {"title": "開學日", "file": "first_day_send_off.mp3", "section": "開學季", "slug": "first_day_send_off", "cover": "polaroids/first_day_send_off.jpeg"}, {"title": "黃銅鎮紙", "file": "miles_farewell_letter.mp3", "section": "開學季", "slug": "miles_farewell_letter", "cover": "images/miles_farewell_letter.jpeg"}, {"title": "重力加倍術", "file": "gravity_doubling_spell.mp3", "section": "開學季", "slug": "gravity_doubling_spell", "cover": "images/gravity_doubling_spell.jpeg"}, {"title": "命案現場的誤會", "file": "crime_scene_misunderstanding.mp3", "section": "開學季", "slug": "crime_scene_misunderstanding", "cover": "images/crime_scene_misunderstanding.jpeg"}, {"title": "法定放空日", "file": "mandatory_relaxation_day.mp3", "section": "開學季", "slug": "mandatory_relaxation_day", "cover": "polaroids/mandatory_relaxation_day.jpeg"}, {"title": "弟弟的週末報到", "file": "miles_weekend_visit.mp3", "section": "開學季", "slug": "miles_weekend_visit", "cover": "polaroids/miles_weekend_visit.jpeg"}, {"title": "雙重曝光的一天", "file": "double_exposure_day.mp3", "section": "開學季", "slug": "double_exposure_day", "cover": "polaroids/double_exposure_day.jpeg"}, {"title": "感恩節的西雅圖", "file": "thanksgiving_in_seattle.mp3", "section": "家人拜訪", "slug": "thanksgiving_in_seattle", "cover": "images/thanksgiving_in_seattle.jpeg"}, {"title": "重工業前衛搖滾樂隊", "file": "wild_band_formation.mp3", "section": "家人拜訪", "slug": "wild_band_formation", "cover": "polaroids/wild_band_formation.jpeg"}, {"title": "迷途小藍鳥的迴響", "file": "samuel_response.mp3", "section": "家人拜訪", "slug": "samuel_response", "cover": "images/samuel_response.jpeg"}, {"title": "帶過來的完整", "file": "what_we_carried_whole.mp3", "section": "北上", "slug": "what_we_carried_whole", "cover": "polaroids/what_we_carried_whole.jpeg"}, {"title": "長輩收割機與土撥鼠", "file": "harvester_and_groundhog.mp3", "section": "海灣新居", "slug": "harvester_and_groundhog", "cover": "polaroids/harvester_and_groundhog.jpeg"}, {"title": "工業垃圾的朋克讚歌", "file": "industrial_junk_anthem.mp3", "section": "海灣新居", "slug": "industrial_junk_anthem", "cover": "images/industrial_junk_anthem.jpeg"}, {"title": "遲來的童年", "file": "belated_childhood.mp3", "section": "海灣新居", "slug": "belated_childhood", "cover": "images/belated_childhood.jpeg"}, {"title": "創傷覆寫", "file": "trauma_rewrite.mp3", "section": "海灣新居", "slug": "trauma_rewrite", "cover": "images/trauma_rewrite.jpeg"}, {"title": "暴風雨夜", "file": "the_storm_night.mp3", "section": "海灣新居", "slug": "the_storm_night", "cover": "images/the_storm_night.jpeg"}, {"title": "三明治擁抱", "file": "sandwich_hug.mp3", "section": "海灣新居", "slug": "sandwich_hug", "cover": "images/sandwich_hug.jpeg"}, {"title": "醫者不能自醫", "file": "healer_cannot_heal_self.mp3", "section": "海灣新居", "slug": "healer_cannot_heal_self", "cover": "images/healer_cannot_heal_self.jpeg"}]).map(function(p) {
    return {
      title: p.title,
      section: p.section || '',
      src: root + 'songs/' + p.file,
      href: p.slug ? (root + 'chapters/' + p.slug + '.html') : '',
      cover: p.cover ? (root + p.cover) : ''
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
  var mediaSession = navigator.mediaSession;

  // 副檔名 → MIME,給 Media Session 的封面圖用
  function coverMime(path) {
    var ext = (path.split('.').pop() || '').toLowerCase();
    if (ext === 'png') return 'image/png';
    if (ext === 'webp') return 'image/webp';
    return 'image/jpeg';
  }

  // 把當前曲目資訊餵給系統(鎖屏 / 控制中心 / 藍牙車機 / Apple Watch 都吃這個)
  function updateMediaSession(track) {
    if (!mediaSession || !window.MediaMetadata) return;
    var art = [];
    if (track.cover) {
      var url = new URL(track.cover, location.href).href;
      var type = coverMime(track.cover);
      art = ['96x96', '192x192', '512x512'].map(function(sizes) {
        return { src: url, sizes: sizes, type: type };
      });
    }
    try {
      mediaSession.metadata = new window.MediaMetadata({
        title: track.title,
        artist: track.section || 'Life is Strange:雙保結局',
        album: '雙保結局 · 全站配樂',
        artwork: art
      });
    } catch (e) {}
  }

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
    updateMediaSession(track);
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

  // ---- Media Session:鎖屏 / 控制中心 / AirPods 雙擊(下一首)三擊(上一首)----
  if (mediaSession && typeof mediaSession.setActionHandler === 'function') {
    var bind = function(action, fn) {
      try { mediaSession.setActionHandler(action, fn); } catch (e) {}
    };
    bind('play', function() { audio.play().catch(function() {}); });
    bind('pause', function() { audio.pause(); });
    bind('previoustrack', function() {
      loadTrack(currentIndex === -1 ? playlist.length - 1 : currentIndex - 1, true);
    });
    bind('nexttrack', function() {
      loadTrack(currentIndex === -1 ? 0 : currentIndex + 1, true);
    });
    bind('seekto', function(d) {
      if (d && d.seekTime != null && isFinite(d.seekTime)) audio.currentTime = d.seekTime;
    });
  }

  audio.addEventListener('play', function() {
    playBtn.textContent = '\u23f8';
    toggle.classList.add('is-playing');
    if (mediaSession) mediaSession.playbackState = 'playing';
  });
  audio.addEventListener('pause', function() {
    playBtn.textContent = '\u25b6';
    toggle.classList.remove('is-playing');
    if (mediaSession) mediaSession.playbackState = 'paused';
  });
  // 鎖屏進度條:把播放位置同步給系統
  audio.addEventListener('timeupdate', function() {
    if (!mediaSession || typeof mediaSession.setPositionState !== 'function') return;
    if (!audio.duration || !isFinite(audio.duration)) return;
    try {
      mediaSession.setPositionState({
        duration: audio.duration,
        position: Math.min(audio.currentTime, audio.duration),
        playbackRate: audio.playbackRate || 1
      });
    } catch (e) {}
  });
  audio.addEventListener('ended', function() {
    loadTrack(currentIndex + 1, true);
  });
})();
