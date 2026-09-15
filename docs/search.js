/* 由 build.py 產生:全站全文搜尋邏輯,索引資料另外放在 search-index.json */
(function() {
  var overlay = document.getElementById('searchOverlay');
  var toggle = document.getElementById('searchToggle');
  if (!overlay || !toggle) return;
  var root = overlay.getAttribute('data-root') || '';
  var input = document.getElementById('searchInput');
  var closeBtn = document.getElementById('searchClose');
  var statusEl = document.getElementById('searchStatus');
  var resultsEl = document.getElementById('searchResults');
  var panel = overlay.querySelector('.search-panel');

  var index = null;       // 載入後的索引陣列
  var loading = null;     // 載入中的 promise,避免重複抓取
  var defaultStatus = statusEl.textContent;
  var debounceTimer = null;

  function loadIndex() {
    if (index) return Promise.resolve(index);
    if (loading) return loading;
    statusEl.textContent = '索引載入中……';
    loading = fetch(root + 'search-index.json').then(function(res) {
      if (!res.ok) throw new Error('index fetch failed');
      return res.json();
    }).then(function(data) {
      index = data;
      statusEl.textContent = defaultStatus;
      return index;
    }).catch(function() {
      statusEl.textContent = '索引載入失敗,檢查一下網路連線。';
      loading = null;
      throw new Error('index load error');
    });
    return loading;
  }

  function open() {
    overlay.removeAttribute('hidden');
    loadIndex();
    requestAnimationFrame(function() { input.focus(); });
  }
  function close() {
    overlay.setAttribute('hidden', '');
    toggle.focus();
  }

  toggle.addEventListener('click', open);
  closeBtn.addEventListener('click', close);
  overlay.addEventListener('click', function(e) { if (e.target === overlay) close(); });
  document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape' && !overlay.hasAttribute('hidden')) close();
    if ((e.metaKey || e.ctrlKey) && e.key === 'k') { e.preventDefault(); open(); }
  });

  // 在一段文字裡找出關鍵字前後各約 18 字的片段,做成 {pre, match, post}
  function snippetAt(text, i, qlen) {
    var start = Math.max(0, i - 18);
    var end = Math.min(text.length, i + qlen + 18);
    return {
      pre: (start > 0 ? '…' : '') + text.slice(start, i),
      match: text.slice(i, i + qlen),
      post: text.slice(i + qlen, end) + (end < text.length ? '…' : '')
    };
  }

  function countMatches(text, q) {
    var n = 0, i = 0;
    while ((i = text.indexOf(q, i)) !== -1) { n++; i += q.length; }
    return n;
  }

  // 索引檔只存原始大小寫的內文,不預存一份小寫副本(內文本身就有兩三千字,
  // 存兩份等於檔案體積直接翻倍)。小寫化留到第一次被搜到時才算一次,
  // 算完直接記在該筆資料上,之後重複搜尋不用再算。標題併進同一段文字裡
  // 一起搜,這樣搜尋詞出現在標題裡也搜得到。
  function fullOf(entry) {
    if (entry._full === undefined) {
      entry._full = entry.title + '\n' + entry.text;
      entry._search = entry._full.toLowerCase();
    }
    return entry;
  }

  function render(query) {
    resultsEl.innerHTML = '';
    if (!query) {
      statusEl.textContent = defaultStatus;
      statusEl.hidden = false;
      return;
    }
    var q = query.toLowerCase();
    var hits = [];
    for (var k = 0; k < index.length; k++) {
      var entry = fullOf(index[k]);
      var i = entry._search.indexOf(q);
      if (i === -1) continue;
      hits.push({ entry: entry, snippet: snippetAt(entry._full, i, q.length), count: countMatches(entry._search, q) });
    }
    if (!hits.length) {
      statusEl.hidden = false;
      statusEl.textContent = '沒有找到包含「' + query + '」的故事。';
      return;
    }
    statusEl.hidden = true;
    hits.forEach(function(hit) {
      var li = document.createElement('li');
      li.className = 'search-result-item';

      var a = document.createElement('a');
      a.className = 'search-result-title';
      a.href = root + 'chapters/' + hit.entry.slug + '.html';
      a.textContent = hit.entry.title;
      li.appendChild(a);

      var meta = document.createElement('div');
      meta.className = 'search-result-meta';
      meta.textContent = hit.entry.meta + (hit.count > 1 ? '　· 共 ' + hit.count + ' 處符合' : '');
      li.appendChild(meta);

      var snip = document.createElement('div');
      snip.className = 'search-result-snippet';
      snip.appendChild(document.createTextNode(hit.snippet.pre));
      var mark = document.createElement('mark');
      mark.textContent = hit.snippet.match;
      snip.appendChild(mark);
      snip.appendChild(document.createTextNode(hit.snippet.post));
      li.appendChild(snip);

      resultsEl.appendChild(li);
    });
  }

  input.addEventListener('input', function() {
    var query = input.value.trim();
    clearTimeout(debounceTimer);
    debounceTimer = setTimeout(function() {
      loadIndex().then(function() { render(query); }).catch(function() {});
    }, 120);
  });
})();
