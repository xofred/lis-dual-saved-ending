# 雙保結局 · 拍立得檔案 — 技術說明

這是一個把 Markdown 章節自動轉換成靜態閱讀網站的建置系統。純 HTML/CSS/JS，沒有任何後端依賴，本地雙擊 `index.html` 就能開，丟到 GitHub Pages / Netlify / Vercel 等任何靜態託管平台也能直接部署。

---

## 一、專案結構

```
site_build/                    ← 建置腳本所在目錄（原始碼，不是網站本身）
├── build.py                   ← 主建置腳本，跑這個檔案會產生整個網站
├── templates.py                ← HTML 共用片段（導覽列、蝴蝶動畫、播放器、頁尾）
├── style.css                  ← 全站樣式表
└── titles.txt                 ← 建置過程中暫存用的檔案，可忽略

ordered/                       ← 章節原始檔資料夾（輸入）
├── 001_xxx.md
├── 002_xxx.md
└── ...                        ← 每個檔案開頭必須是 "# 章節標題" 這一行

Images/                        ← 章節插圖素材(來源,不在 docs/ 裡),檔名對應章節 slug
songs/                         ← 章節配樂素材(來源),檔名對應章節 slug
Polaroids/                     ← 拍立得照片素材(來源),檔名對應章節 slug,可多張
Journal/                       ← Max 的手帳頁素材(來源),檔名對應章節 slug,可多頁

docs/                          ← 建置後的成品（輸出，這就是要部署的東西，整個由 build.py 產生；GitHub Pages 從此資料夾發佈）
├── index.html                 ← 首頁，自動產生的分區目錄
├── polaroids.html              ← 拍立得相簿頁,列出全站所有拍立得照片
├── journal.html                ← Max 的手帳頁,列出全站所有章節插圖,可一頁頁翻閱
├── style.css
├── images/                    ← 從 Images/ 複製過來(只複製有對應章節的檔案)
├── songs/                     ← 從 songs/ 複製過來(只複製有對應章節的檔案)
├── polaroids/                 ← 從 Polaroids/ 複製過來(只複製有對應章節的檔案)
├── journal/                   ← 從 Journal/ 複製過來(只複製有對應章節的檔案)
├── .nojekyll                  ← 空檔案,叫 GitHub Pages 不要跑 Jekyll
├── sw.js                      ← Service Worker,離線快取用(每次建置帶新版本字串,見第七之二節)
└── chapters/
    ├── xxx.html                ← 每章一個獨立頁面
    └── ...
```

**重要**：`docs/` 整個資料夾都是**每次跑 `build.py` 就會重新產生**的產物（為了讓 GitHub Pages 直接發佈，它有進版控，但不要手動編輯），包括 `docs/images` `docs/songs` `docs/polaroids` `docs/journal` 這幾個媒體子資料夾也是——它們是建置時從專案根目錄的 `Images/` `songs/` `Polaroids/` `Journal/` 複製過來的，不是素材真正的家。**要新增/修改素材，永遠是去改根目錄的 `Images/` `songs/` `Polaroids/` `Journal/`，或改 `ordered/` 裡的 `.md` 原始檔，或改 `build.py` / `templates.py` / `style.css` 這幾個原始碼檔案**，改完重新跑一次建置、把 `docs/` 的變更一起 commit 就好，不要手動改 `docs/` 底下的任何東西。

---

## 二、怎麼跑建置

```bash
cd site_build
python3 build.py
```

需要 Python 3 + `markdown` 套件（`pip install markdown`）。跑完會在專案根目錄的 `docs/`（或你設定的 `OUT_DIR`）產生完整網站。

---

## 三、章節檔案規則（`ordered/` 資料夾）

1. **檔名格式**：`{三位數編號}_{英文slug}.md`，例如 `001_dual_saved_ending_family_reunion.md`
   - 編號決定排序與"上一章/下一章"導覽
   - slug 會變成該章節網頁的網址（`/chapters/{slug}.html`），**只能用英文字母、數字、底線**，中文檔名在部分平台會有編碼問題
2. **檔案第一行必須是 `# 標題`**，這行會被抓出來當作章節標題，並且在轉換 HTML 時自動移除（因為模板會自己重新渲染一次標題，避免重複）
3. 其餘內文用標準 Markdown 語法：`##` 是小節標題、`---` 是分隔線（會被樣式渲染成一個蝴蝶符號 ❦）、一般段落照常寫

---

## 四、首頁的六大分區怎麼設定

`build.py` 最上面這段就是分區設定，**新增章節後要手動更新這裡的數字範圍**：

```python
SECTIONS = [
    ("背景與序曲",     1,   25,  "分區描述文字"),
    ("旅館連環案",     26,  42,  "..."),
    ...
]
```

每一項是 `(分區名稱, 起始編號, 結束編號, 分區描述)`。系統會根據每篇章節的編號，自動歸類進對應區塊。**這是目前系統裡唯一需要手動維護的地方**——之後如果要改成自動分區（比如讀取每篇檔案裡的 metadata 標籤），是一個可以優化的方向。

---

## 五、目前已知的待辦事項

- [x] ~~首頁 hero 文案裡寫死「一百一十一章」~~ → 已改成動態計算 `len(chapters)`，會自動反映實際章節數
- [x] ~~媒體嵌入是寫死的預留位~~ → 已改成自動偵測，見下方第六節

---

## 六、音樂、插圖、拍立得照片都是自動偵測機制

不需要改 `.md` 原始檔，也不需要寫 front matter。系統會在建置時，自動去專案根目錄的 `Images/`、`songs/`、`Polaroids/`、`Journal/` 這四個資料夾裡，找有沒有跟章節 slug 同名的檔案，找到就複製進 `docs/` 並自動嵌入，找不到就顯示「尚未配圖 / 尚未配樂」的提示（拍立得、手帳沒有就直接不顯示該欄位）。

### 命名規則（唯一需要注意的地方）

檔名必須跟章節的 slug **完全一致**，只是換副檔名：

```
ordered/023_bedroom_lua.md      ← 章節原始檔，slug 是 bedroom_lua
Images/bedroom_lua.jpeg         ← 插圖，自動配對成功
songs/bedroom_lua.mp3           ← 配樂，自動配對成功
Polaroids/bedroom_lua.jpeg      ← 拍立得照片(第 1 張),自動配對成功
Polaroids/bedroom_lua_2.jpeg    ← 同一章的第 2 張拍立得,加 _2 _3... 後綴
Journal/bedroom_lua.jpeg        ← Max 的手帳(第 1 頁),自動配對成功
Journal/bedroom_lua_2.jpeg      ← 同一章的第 2 頁手帳,加 _2 _3... 後綴
```

支援的副檔名：
- 圖片、拍立得照片：`.jpeg` `.jpg` `.png` `.webp`
- 音樂：`.mp3` `.m4a` `.ogg` `.wav`

如果檔名對不上（比如歌曲取了一個跟章節無關的名字），系統就抓不到，該章節會顯示「尚未配樂」。**目前唯一的解法是把檔案改名成對應章節的 slug**，沒有額外的對應表機制。

### 資料夾位置

素材放在專案根目錄的 `Images/`、`songs/`、`Polaroids/`、`Journal/` 底下就行（不是 `docs/` 裡面，`docs/` 是建置產物）。`build.py` 只會把「檔名對得上某章節 slug」的檔案複製進 `docs/images` `docs/songs` `docs/polaroids` `docs/journal`，跟任何章節都對不上的檔案會被跳過、不進 `docs/`，可以放心把素材原始檔（包含改名前的舊版本）都留在這幾個來源資料夾裡管理。

### 拍立得相簿

除了會顯示在對應章節頁面之外，全站所有拍立得照片還會彙整成一個獨立的「拍立得相簿」頁面（`docs/polaroids.html`，導覽列上有連結），依章節順序排列。

### Max 的手帳（跟插圖是兩種不同素材）

**插圖**（`Images/`，📷）是給讀者順順讀的配圖，一章一張，正文旁邊直接顯示，不放大也不進相簿。

**手帳**（`Journal/`，📓）是另外一種多媒體：模擬 Max 隨手畫的手繪日記頁（帶標題框、分格、手寫註記那種）。放在專案根目錄的 `Journal/` 底下，命名規則跟拍立得一樣——`Journal/{slug}.jpeg` 是第 1 頁，`Journal/{slug}_2.jpeg`、`_3`… 是後續頁，一章可以有好幾頁。建置時複製進 `docs/journal/`，在對應章節頁顯示成一疊可點擊的頁面卡。

全站所有手帳頁還會彙整成一個獨立的「Max 的手帳」頁面（`docs/journal.html`，導覽列上有連結），依章節順序排列，可以一頁頁翻閱。`Journal/` 已列入 `.gitignore`（跟其他素材來源資料夾一樣），只有 `docs/journal/` 進版控。

### 放大檢視（燈箱）

點任何一張拍立得、或任何一頁手帳,會全螢幕放大看原圖（`templates.py` 裡的 `LIGHTBOX` 片段，CSS/JS 純內建、無外部依賴，每頁都會注入）。同一組有多張時可用左右箭頭、鍵盤方向鍵、或手機左右滑動切換；`Esc`、點背景、或下滑關閉。在相簿／手帳頁,燈箱底部會多一個「回到章節 →」連結（章節頁本身不顯示,因為已經在該章節）。章節插圖（📷）不進燈箱。

同一套燈箱靠來源元素分成兩組獨立導覽：拍立得（`.polaroid-card`）與手帳（`.journal-page-card` / `.journal-card`），彼此不會互相翻到。兩組的開場動畫也不同——拍立得是模擬顯影（`developing`），手帳是模擬繞書脊翻頁（`flipping`，往回翻時鉸鏈換到右側）；打開時做完整動畫，左右切換時做快速版，`prefers-reduced-motion` 一律跳過。手機與桌面共用同一套燈箱,靠 `style.css` 裡 `max-width: 640px` 的 media query 調整尺寸。

### 之後如果想做「檔名對不上也能手動指定」

如果之後有音樂/圖片的檔名沒辦法直接跟 slug 對應（比如同一首歌想用在好幾章、或者取了很有意義的原創標題想保留），可以考慮加一個對應表機制，例如在 `build.py` 裡加一個 dict：

```python
MEDIA_OVERRIDE = {
    "dual_saved_ending_family_reunion": {
        "music": "The-Storm-Has-Cantonese-slow-2.mp3",
    },
    # 沒列在這裡的章節,還是照原本的 slug 同名比對邏輯
}
```

然後在 `find_media` 呼叫之前，先檢查該章節的 slug 有沒有出現在 `MEDIA_OVERRIDE` 裡，有的話優先採用覆寫的檔名。這是一個之後可以做的小擴充，目前的版本還沒有這個機制。

---

## 七、其他可能的擴充方向（供參考）

- **搜尋功能**：目前115章只能用目錄瀏覽，之後量再大可能需要一個簡單的全文搜尋（純前端 JS 做關鍵字比對即可，不需要後端）
- **深色模式**：`style.css` 裡的顏色都用 CSS 變數定義（`:root` 區塊），要加深色模式只需要多寫一組變數 + 一個切換按鈕
- **RSS / 訂閱**：如果之後持續更新，可以額外產生一個 `feed.xml`，方便讀者訂閱新章節通知
- **首頁章節卡片加縮圖**：目前卡片只有編號和標題，如果每章都配了插圖，可以把插圖縮圖也放進卡片裡

---

## 七之二、離線快取（Service Worker）

`build.py` 每次建置會產生一個帶版本字串的 `docs/sw.js`（版本 = 建置時間戳，例如 `v20260828-220656`），每個頁面底部都會註冊它。目的:手機讀到一半網路抽風，開過的頁面、看過的圖、聽過的歌都還在。

快取策略（手寫,沒引 Workbox,保持零依賴）:

| 資源 | 策略 | 效果 |
|---|---|---|
| 頁面導覽（HTML） | NetworkFirst | 線上永遠拿最新章節;離線時回退到曾開過的快取,沒開過的顯示簡短離線提示 |
| 圖片 / 拍立得 / 手帳 / 音檔 / 字型檔 | CacheFirst | 開過看過聽過的,離線照樣可用。音檔額外做手動 `Range` 切片,拖進度條不會壞 |
| `style.css` / Google Fonts CSS | StaleWhileRevalidate | 先用快取秒開,背景更新 |

版本一換（下次建置),舊的 `shell-*` / `media-*` 快取會在新 SW 的 `activate` 事件整包刪除。因為 HTML 走 NetworkFirst、JS 又全部內聯在 HTML 裡沒有獨立 bundle,不會有「頁面新、資源舊」的版本錯位,所以 SW 直接 `skipWaiting()` 立即接管,不需要更新提示。

媒體快取有上限（圖片類 ~90 條、頁面 ~130 條），超過就從最舊的開始淘汰。`CacheStorage` 在裝置儲存吃緊時可能被整個清掉——這是效能優化,不是「保證永久離線」。

要停用:把 `templates.py` 的 `SW_REGISTER` 換成空字串重新建置,並在 `sw.js` 加一段 `self.registration.unregister()` 讓已安裝的使用者退出。

## 八、部署方式

`docs/` 資料夾本身就是完整的靜態網站，任何方式都行：

- **本地**：直接雙擊 `docs/index.html`
- **GitHub Pages**：本 repo 就是這樣部署的——Settings → Pages 選 `main` 分支的 `/docs` 資料夾，每次 commit 完 `docs/` 就會自動更新
- **Netlify / Vercel**：把 `docs/` 資料夾拖進去，或連接 git repo 自動部署
- **自己的伺服器**：整個 `docs/` 資料夾丟進網頁根目錄就能跑，不需要任何伺服器端設定（Nginx / Apache 純靜態檔案服務即可）

---

## 九、常見問題

### macOS：頁面打不開，或樣式完全跑掉（例如蝴蝶動畫圖示異常放大佔滿全螢幕）

**症狀**：點連結出現 `ERR_ACCESS_DENIED`；或者首頁能打開，但完全沒有套用任何樣式（純黑白文字、超大異常的 SVG 元素）。

**原因**：macOS 對 `~/Downloads/` 資料夾有較嚴格的安全限制，瀏覽器（尤其 Chrome）對這個資料夾底下較深層路徑的檔案存取，有時會被系統擋下——不只是 HTML 頁面本身，連 `<link>` 引用的 CSS、`<img>` 引用的圖片，這類「連帶載入」的資源也會一起被卡住。

**解法**：把整個專案資料夾**移出 Downloads**，搬到 `~/Documents/`、桌面，或任何其他位置，再重新打開 `index.html`。不需要改任何程式碼，純粹是資料夾位置的問題。這個問題已經實際驗證過——一旦搬離 Downloads，建置與瀏覽都能正常運作。
