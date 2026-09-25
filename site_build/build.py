#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
靜態網站建置腳本
把各季資料夾(ordered/、ordered_s2/、ordered_s3/ …,見下方 SEASONS)裡的
markdown 章節,轉成統一風格的靜態閱讀站台。輸出到專案根目錄的 docs/(給 GitHub Pages 用)
"""

import os
import re
import sys
import shutil
import hashlib
import json
import markdown as md_lib
from PIL import Image, ImageOps

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

OUT_DIR = os.path.join(PROJECT_ROOT, "docs")
CHAPTERS_DIR = os.path.join(OUT_DIR, "chapters")
IMAGES_DIR = os.path.join(OUT_DIR, "images")
SONGS_DIR = os.path.join(OUT_DIR, "songs")
POLAROIDS_DIR = os.path.join(OUT_DIR, "polaroids")
JOURNAL_DIR = os.path.join(OUT_DIR, "journal")
# 拍立得/手帳的小縮圖(給故事頁的小卡、兩個相簿頁用),原始全解析度檔案還是
# 完整留在 POLAROIDS_DIR / JOURNAL_DIR,只有點開燈箱放大看那一刻才會載入
THUMBS_DIR = os.path.join(OUT_DIR, "thumbs")
POLAROID_THUMBS_DIR = os.path.join(THUMBS_DIR, "polaroids")
JOURNAL_THUMBS_DIR = os.path.join(THUMBS_DIR, "journal")

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

# 圖片壓縮參數:插圖是讀者順順讀文章時直接看到的(最寬也就是文章欄寬 700px 出頭),
# 縮到 1400px 長邊在 retina 螢幕上一樣銳利,不需要原圖那種 3~10MB 的解析度。
# 拍立得/手帳的小卡最大也就 300px 寬,縮圖給到 720px 長邊在 3x 螢幕上都還綽綽有餘。
IMAGE_MAX_DIM = 1400
THUMB_MAX_DIM = 720
JPEG_QUALITY = 82
# 改了 resize_image() 的壓縮邏輯本身(不是上面那三個數字)就手動 +1,讓所有
# 快取紀錄一次性失效、全部重新壓縮一次;只是調整 IMAGE_MAX_DIM 這幾個數字
# 不用管這個,resize_image_cached() 自己會比對到參數變了。
RESIZE_ALGO_VERSION = 1

# 圖片壓縮很吃 CPU(478 張全部重跑要近一分鐘),建置期做增量快取:記住每個
# 輸出檔案上次是拿哪個來源檔案內容(sha1)、用什麼參數壓的,這次來源檔案內容
# 沒變、參數也沒變,就直接跳過、留著上次壓好的檔案不動。快取存在 build.py
# 旁邊的 .image_cache.json,不進版本控制(純本機加速用,見 .gitignore)。
IMAGE_CACHE_PATH = os.path.join(SCRIPT_DIR, ".image_cache.json")


def load_image_cache():
    try:
        with open(IMAGE_CACHE_PATH, "r", encoding="utf-8") as fh:
            return json.load(fh)
    except (FileNotFoundError, ValueError):
        return {}


def save_image_cache(cache):
    with open(IMAGE_CACHE_PATH, "w", encoding="utf-8") as fh:
        json.dump(cache, fh)


def file_sha1(path):
    h = hashlib.sha1()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def resize_image_cached(src_path, dst_path, max_dim, old_cache, new_cache, quality=JPEG_QUALITY):
    """跟 resize_image() 一樣,但先比對來源檔案內容 hash + 壓縮參數;沒變、
    輸出檔案也還在,就跳過重新壓縮。回傳這次是否真的重新壓了(給統計用)。
    new_cache 只會收進這次實際處理過的項目,改名/刪掉的來源檔案自然不會被
    寫回去,快取檔案本身也就跟著自動瘦身,不用另外清孤兒紀錄。"""
    key = os.path.relpath(dst_path, OUT_DIR)
    src_hash = file_sha1(src_path)
    record = {"src_hash": src_hash, "max_dim": max_dim, "quality": quality, "algo": RESIZE_ALGO_VERSION}
    prev = old_cache.get(key)
    if prev == record and os.path.isfile(dst_path):
        new_cache[key] = record
        return False
    resize_image(src_path, dst_path, max_dim, quality)
    new_cache[key] = record
    return True


def prune_orphans(dir_path, keep_names):
    """把 dir_path 底下不在 keep_names 裡的檔案刪掉(改名/刪掉來源時留下的孤兒)。
    取代原本整批 rmtree 的做法——這三個資料夾現在跨次建置保留,才有東西可以
    比對快取,所以孤兒清理要單獨做。"""
    if not os.path.isdir(dir_path):
        return
    for fname in os.listdir(dir_path):
        if fname not in keep_names:
            os.remove(os.path.join(dir_path, fname))


def resize_image(src_path, dst_path, max_dim, quality=JPEG_QUALITY):
    """把一張圖縮到長邊不超過 max_dim(小於就不放大),存到 dst_path。
    保留原始格式;JPEG 額外做品質壓縮,其餘格式用該格式的無損最佳化。
    用 exif_transpose 先把手機拍照常見的旋轉 EXIF 套用實際轉正,避免縮圖歪掉。"""
    with Image.open(src_path) as img:
        fmt = (img.format or "JPEG").upper()  # exif_transpose/resize 之後 .format 會變 None,先記下來
        img = ImageOps.exif_transpose(img)
        w, h = img.size
        scale = max_dim / max(w, h)
        if scale < 1:
            img = img.resize((max(1, round(w * scale)), max(1, round(h * scale))), Image.LANCZOS)
        save_kwargs = {"optimize": True}
        if fmt in ("JPEG", "JPG"):
            if img.mode not in ("RGB", "L"):
                img = img.convert("RGB")
            save_kwargs["quality"] = quality
        img.save(dst_path, **save_kwargs)


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

# 第一季的篇章分區,對應排定的順序區間 (檔名數字範圍, 含頭含尾)
SECTIONS = [
    ("背景與序曲",     1,   25,  "案發後的世界觀補完、漩渦崩解與Victoria的贖罪、David的解職、學校重生、波特蘭假期、墓地告別、隔音期間的日常"),
    ("旅館連環案",     26,  42,  "Devil in Me crossover ── 五人小隊的驚魂旅館夜,及其後續"),
    ("校園與衰退",     43,  64,  "AI元年式的校園諷刺日常,與 Max 超能力逐漸消退的伏筆線"),
    ("宿舍與公路(一)", 65,  76,  "打通宿舍的鬧劇日常,以及奧林匹亞/阿斯托利亞公路旅行"),
    ("校園與公路(二)", 77,  94,  "校園日常延續,西雅圖公路旅行系列"),
    ("Victoria與Kate", 95, 115,  "四人組主線 ── 從死對頭到真心朋友的完整弧線"),
    ("畢業季終章",     116, 129,  "從凌晨兩點的苦讀夜到畢業典禮 ── Chloe 補完高中學分的最後一個學期,提勒穆克海岸小旅行、放榜與畢業"),
]

# 第二季的篇章分區,對應檔名數字範圍 (含頭含尾)
SECTIONS_S2 = [
    ("珍珠區的天台",   1,  17, "落腳波特蘭珍珠區的頂層 Loft、Max 的西雅圖聯展首秀、天台花園的第一個夏天,以及藝術學院宿舍的深夜攻防戰"),
    ("匠魂與鋼鐵車廂", 18, 35, "Chloe 的工匠魂徹底點燃 ── 從防彈眼鏡盒、Kate 的園藝工具箱、草本煉金工坊,到 PNCA 期中展的最高榮譽與手工典藏冊,再到買下廢棄火車車廂、除鏽、立起 PRICE FORGE & ATELIER 的招牌、點燈、接下第一號委託"),
    ("暑假與長輩認證", 36, 45, "材料力學補考衝刺、鮑威爾書店的書名暗殺、全員 cosplay 鬧劇、Kate 的兒童草本園藝班開課、重返阿卡迪亞灣,以及 David 在車庫深夜給出的那句核准"),
    ("青年機械教室",   46, 56, "Miles 與「頂級義警」Robert McCall 登場、二號車廂改成青年機械教室、正式開課、Victoria 強行發起的健身房體脂淨化行動,以及 Warren 與 Brooke 帶著無人機從西雅圖回歸"),
    ("開學季",         57, 68, "硬核親友團護送 Miles 上大學、一首 Lo-Fi 讓全員癱在地毯上、Victoria 頒布《法定放空日》、堪比國稅局審計的合規培訓,以及配電子榨菜吃飯的日常"),
    ("家人拜訪",       69, 80, "感恩節北上見 Max 的父母、Kate 與 Victoria 的家人先後上門、重工業前衛搖滾樂隊成軍、Kate 解封的及腰長髮,以及週末市集的「令千金」風波三部曲與西雅圖慈善晚宴"),
    ("北上",           81, 85, "波特蘭市中心的治安在半年裡崩壞、Victoria 攤開西海岸地圖、David 領銜的軍規級拆遷、兩節鋼鐵車廂的公路北上,以及在普吉特海灣臨海高地上的重新落位"),
]

# 第三季的篇章分區(還在連載中,最後一段先給開放範圍收新章節;完結後再比照第二季收尾定案)
SECTIONS_S3 = [
    ("海灣新居",           1,  10, "Max 的父母正式見過 Kate 與 Victoria、新基地的懸崖追逐與湯森港補給日、工坊接下搬遷後第一筆銀鹽委託、Victoria 的稅務核聚變、Kate 的特洛伊木馬健康料理,以及四個95後遲來的童年補完"),
    ("公款出差東京行",     11, 18, "Victoria 把去日本看展包裝成跨國避稅核銷、秋葉原的卡牌估值談判與東京街頭反撞人事件、成田機場的龍貓超重風波,一路吵鬧回到海灣,順便把星鏈密碼也扯進了戰場"),
    ("海盜瞭望塔",         19, 25, "重啟阿卡迪亞灣那座未完成的海盜樹屋、暴風雨夜裡的 PTSD 覆寫、Kate 罕見的情緒崩潰與解構主義茶道,以及暗房裡一場被竹竿搞砸的浪漫告白"),
    ("懸崖邊的柴米油鹽",   26, 28, "菸稅、化糞池維修費與商業攝影恰飯,以及一通被直球拒絕的邀約電話 ── 就算搬上了懸崖新基地,現實開銷與老朋友的日常還是不會缺席"),
    ("Lily 的起源（倒敘）", 29, 41, "從超能力救場、加入工坊實習,到雨夜識破真相、拜師學藝、畫廊救場逆襲 Victoria,再到愛與和平感化失敗、動物收容所治療、確立食物鏈頂點,最後留守辦妥搬遷手續 ── 實習生 Lily 從社恐白兔進化成複合型黑魔法總監的完整回溯"),
    ("黑魔法全面上線",     42, 50, "歪掉的技能樹全面暴露、國防部與跨國企業聞風來挖角、孫子兵法被寫滿行政註解、Chloe 的加密貨幣爆倉半山腰、樂園與公路旅行兩次「找回純真」計畫接連失敗,直到一封匿名爆料信把四人的舊傷疤翻出來,全員選擇並肩迎戰"),
    ("審判與垃圾食物大越獄", 51, 57, "Lily 對獄中的 Jefferson 發動跨州行政絞殺、國防部聞訊來勸退挖角、東方食療讓資本主義苦瓜苦到崩潰,直到 Kate 和 Lily 出差兩天,家裡三頭猛獸原形畢露展開類比時代垃圾食物大越獄,最後全員反式脂肪中毒躺平"),
    ("賭城與空中合規",     58, 63, "拉斯維加斯年度放風 ── 賭桌上的食物鏈現形、荒漠廢墟與地景藝術、私人飛機被塔台放鴿子,以及電影之夜被開成聯邦合規糾錯研討會"),
    ("行政黑魔法全開",     64, 69, "多年懸案被一紙行政調查工具秒破、Kate 罕見的「舊約聖經級審判」教會風波、跨國企業重金求上防禦性合規大師課,以及連雨季都能被告到破產的終極行政黑魔法"),
    ("唐人街味覺降維",     70, 72, "Lily 帶隊殺進中國城飲茶酒樓與茶餐廳 ── 筷子的物理學與內臟恐懼、粥水配油炸鬼的碳水終極奧義,以及「搭檯」文化對名媛社交距離的徹底粉碎"),
    ("數位圍城",           73, 80, "多元公平指標差點斷了文化津貼、敵意建築物理教訓滑板黨、AirPods 降噪結界與 Apple Watch 健康規訓、拔網路線的失敗數位越獄,直到一場暴風雨停電讓核微反應爐與小鎮末日眾生相一起登場"),
    ("資本博弈與矽谷反壟斷", 81, 88, "監管資訊差套利玩轉華爾街、Chase 家族借調風波逼出獅子開口的籌碼談判、Victoria 專屬 AI 秘書從蜜月期到失控、任天堂 DMCA 與復古相機的類比信仰保衛戰,一路打到微軟反壟斷與訂閱制計畫性報廢"),
    ("核能鄰居與日常降維",   89, 101, "FaceTime 掩護戰騙過 Max 父母、基金經理合規對轟討回管理費、迪士尼樂園式的獎勵之旅、電話騷擾變現指南、靶場合規與教會聖約洗禮,直到 DARPA 頂級科學家為了核聚變反應爐把二號車廂變成月度戰術下午茶現場,Warren 與 Brooke 順勢完成技術碾壓"),
    ("信用卡驚魂與風控朝聖", 102, 109, "瞭望塔頂的初吻復刻與靶場教學、MOBA 暴走引發的防禦性聲明、殭屍信用卡引爆的恐慌性凍結、與神秘風控架構師 Mr. V 的加密聊天室,一路朝聖到那座賽博監獄般的風控指揮中心,再逃進舊金山街頭跟自動駕駛車大眼瞪小眼"),
    ("舊金山七日壯遊",       110, 115, "沒有 Wi-Fi 的正宗塔可店與街頭陰影裡的被遺忘者、FAA 全線停飛逼出的私人候機室佔領、宿醉早餐引爆的階級飲食內戰,以及不知為何如期舉行的反劫機 4D 真人秀"),
    ("聖誕節與洗衣機大戰",   116, 127, "紅藍警燈與過節話題各自埋下一根刺、聖誕送禮三部曲(血汗小熊、貴族縫紉機事故、回禮恐慌症)、洗衣機災難升級成微觀駭客報復戰,直到深夜潛入物流基地的機器狗生死追逐"),
    ("保單與信託風暴的開場", 128, 133, "Max 未雨綢繆拍下的全家福保險存檔、Chase 家族祖父的越洋來電正式引爆百萬信託風暴,緊接著是跨區支付卡關的舉手之勞、暗網購物許可的大天使微笑審訊,最後演變成尖叫雞軍團大戰與資產錯位配置的物理報復"),
    ("羊駝毛耍廢科學與酸黃瓜審判", 134, 138, "Kate 網購的羊駝毛保暖裝備正式登場、耍廢打電動被包裝成預防性醫療的科學宣言、大天使深夜對屠殺畫面的慈悲審判嚇壞眾人、底線試探後的心照不宣,直到一場酸黃瓜引爆的臉部肌肉抗爭復仇秀"),
    ("底片危機、公路里程與海盜塔黑歷史", 139, 146, "蘋果硬體簽章讓寶麗來底片的物理證據地位岌岌可危、汽車餐廳裡各自滑手機的賽博沉默約會、牙籤難題與州警攔檢意外曝光車頂黑歷史照,一路演變成 Lily 的高精度掃描、Victoria 非軍規海盜塔升級令,以及深夜曝光心跳與倒灌記憶的驚魂"),
    ("國防部突襲與AI包工頭", 147, 150, "雨季裡三輛聯邦車牌休旅車突襲車廂逼收反應爐、良性腫瘤原則掩護太陽能板改裝大業曝光,直到眾人發現 Lily 沉默的第二大腦早已是私有部署的AI包工頭"),
    ("吊床、雪茄與畢業典禮的閒散日子", 151, 160, "松樹間的吊床 physics 教學、太平洋西北藝術學院的合規交作業意外、薄荷菸與古巴雪茄的男子氣概實驗、畢業典禮品味制裁的倒敘回憶、MBTI 人格武器庫與加州超級富豪稅風暴,直到 PAX West 展場意外進化成破次元 Coser 神話,以及 AI 生成中文譯名的荒唐測試,為疫情前最後的悠閒日子畫下句點"),
    ("疫苗通行證、綠色通行碼與封鎖下的哀傷", 161, 165, "疫苗優先接種的VIP特權引爆世代價值觀衝突、沒有通行碼就被地下龐克酒吧拒於門外、Zoom禮拜裡教區長輩的孤獨眼淚、卡車司機抗議引爆的凍結帳戶怒火,以及 Max 鏡頭下那座封城十一個月的鬼城"),
    ("供應鏈斷裂的末日廚房大戰", 166, 170, "馬斯洛需求層次在雞毛蒜皮日常裡倒塌成戰術級鬆餅災難、美軍單兵口糧的抽樣質檢、八千美元烤箱主板燒毀撞上全球供應鏈斷裂,直到直升機空投模組化野戰廚房進駐又撤離,眾人戒斷式懷念起那段瘋狂的日子"),
    ("居家隔離的心理保衛戰", 171, 177, "Chloe 自製末日LARP裝備被冷眼吐槽、喪屍片頭腦風暴出的末日生存法則、瘟疫危機桌遊玩成行政車禍、Lily 化身宮廷弄臣的解壓矩陣心理代償、共享衛浴前的手機成癮攻防戰,以及 Victoria 商舖與米其林餐廳先後撞上的疫情限制與內捲耳光"),
    ("Lily 的招募回憶(倒敘二)", 178, 9999, "時間倒回2017年的波特蘭新生宿舍 ── 深夜求救的巫毒甜甜圈交易、強迫症收納展覽館裡的意外收留、龐克唱片行的感官升級、宵禁夜歸的溫暖收留,直到珍珠區天台合照裡剩餘價值的合法轉移與工具牆前的行政洗禮,一路回到懸崖新基地那場遲來的第一頓晚餐 ── 第三季還沒完結,這段留給後續新章節自動歸入"),
]

# ---- 所有季的設定表 ----
# 第一季是預設季(不畫分隔線、三位數編號);第二季起在首頁用 season-divider + 暖色
# 區塊明顯區隔。要加新的一季:建一個 ordered_sN/ 資料夾,寫一份 SECTIONS_SN,
# 再往這個 list 尾巴加一筆就好。
SEASONS = [
    {
        "num": 1,
        "src": os.path.join(PROJECT_ROOT, "ordered"),
        "sections": SECTIONS,
        "divider": None,
    },
    {
        "num": 2,
        "src": os.path.join(PROJECT_ROOT, "ordered_s2"),
        "sections": SECTIONS_S2,
        "divider": {
            "eyebrow": "SEASON TWO",
            "name": "波特蘭",
            "desc": "風暴之後,四個人都留在了波特蘭 ── Max 讀 PNCA、Chloe 修應用機械、Kate 唸兒童心理、Victoria 遠端上課兼接手畫廊。從珍珠區的天台到普吉特海灣,新生活的一整段日常。",
        },
    },
    {
        "num": 3,
        "src": os.path.join(PROJECT_ROOT, "ordered_s3"),
        "sections": SECTIONS_S3,
        "divider": {
            "eyebrow": "SEASON THREE",
            "name": "普吉特海灣",
            "desc": "兩節鋼鐵車廂在華盛頓州奧林匹亞半島的臨海高地上重新扎根 ── 遠離波特蘭的煙硝,四個人在普吉特海灣邊的新生活。",
        },
    },
]

CN_NUM = "零一二三四五六七八九十"

# 終端機警告色:只在真的接著終端機、且沒被 NO_COLOR 這個業界慣例環境變數
# 關掉時才上色,避免輸出被重導向到檔案/log 時混進一堆看不懂的跳脫碼
_USE_COLOR = sys.stdout.isatty() and not os.environ.get("NO_COLOR")
WARN = "\033[1;93m" if _USE_COLOR else ""    # 粗體亮黃,警告用
RESET = "\033[0m" if _USE_COLOR else ""


def get_section(num, sections=SECTIONS):
    """依檔名編號找出章節所屬的篇章分區名。傳入該季的 sections list。"""
    for name, lo, hi, desc in sections:
        if lo <= num <= hi:
            return name
    return "未分類"


def parse_chapter_num(filename):
    """回傳 (編號, 插入字母後綴) 的 tuple。檔名可以在數字後面加一個小寫字母,
    用來在不影響後面所有編號的情況下,在某個編號的位置插入一篇故事——比如
    002a_xxx.md、002b_xxx.md,兩篇都算「第 2 章」這個位置,靠字母決定先後。
    沒有字母後綴就回傳空字串,行為跟以前完全一樣。"""
    m = re.match(r"^(\d+)([a-z]?)_", filename)
    return (int(m.group(1)), m.group(2)) if m else (0, "")


def find_duplicate_numbers(files):
    """同一季資料夾裡,檔名數字前綴(含插入字母後綴)重複的那些檔案(比如
    手誤取了兩個一模一樣的 110_,或忘記給插入章節加字母後綴)。回傳
    {(編號, 後綴): [檔名, ...]},只收真的重複(同一組合 ≥ 2 個檔案)的項目;
    002a 和 002b 是刻意的不同組合,不會被當成重複。不同季各自從頭編號、
    互不相干,所以呼叫方要逐季分開檢查,不能整批混著查。這不影響任何排序
    或連結是否正確(檔名 slug 才是配對依據),純粹是編號本身有歧義、容易
    讓人誤會兩篇故事的先後順序,所以只警告、不擋 build。"""
    by_num = {}
    for f in files:
        by_num.setdefault(parse_chapter_num(f), []).append(f)
    return {n: fs for n, fs in by_num.items() if len(fs) > 1}


def extract_title(md_text):
    for line in md_text.splitlines():
        line = line.strip()
        if line.startswith("# "):
            return line[2:].strip()
    return "未命名章節"


def slugify(filename):
    # 去掉數字前綴(可能帶一個插入用的字母後綴,比如 002a_)與副檔名,作為輸出檔名 slug
    base = re.sub(r"^\d+[a-z]?_", "", filename)
    base = re.sub(r"\.md$", "", base)
    return base


# python-markdown 的星號解析是逐字元的傳統 regex 引擎,遇到「*斜體包著**粗體**,
# 兩邊收尾疊在一起變成三顆星連在一起」這種寫法會誤判:粗體整個消失,句尾還會
# 露出兩顆孤立的裸星號。Typora 等照 CommonMark 規則走的編輯器不會有這個問題,
# 只有這裡的 build 會炸。修法:轉 HTML 前,先把這兩種「三星疊在一起」的樣式直接
# 換成對應的 <em>/<strong> 原生 HTML,繞開這段有歧義的星號解析,其餘星號完全不動。
def fix_nested_emphasis(text):
    # 收尾疊在一起:*文字**粗體***  →  <em>文字<strong>粗體</strong></em>
    text = re.sub(
        r"\*([^*\n]+?)\*\*([^*\n]+?)\*\*\*",
        r"<em>\1<strong>\2</strong></em>",
        text,
    )
    # 開頭疊在一起:***粗體**文字*  →  <em><strong>粗體</strong>文字</em>
    text = re.sub(
        r"\*\*\*([^*\n]+?)\*\*([^*\n]*?)\*",
        r"<em><strong>\1</strong>\2</em>",
        text,
    )
    return text


# Markdown 原生規則:引用區塊(> ...)裡連續兩行之間如果沒有空白 > 行分隔,
# 會被當成同一段落,單一換行被壓縮成空白 ── 逐行寫的名言註解、逐條列出的
# 稱號解釋,擠成一坨看不出原本的分行。Typora 等編輯器預設把段落內單一換行
# 當真正的換行處理,這裡沒有,所以看起來比原始檔案差。
# 修法:引用區塊裡每一行非空白內容,結尾補上 Markdown 的強制換行語法(兩個
# 空白),讓它换行時真的斷行;本來就用空白 > 行分開的段落不受影響(段落
# 最後一行補的換行標記沒有任何效果),清單項目(> - ...)也不受影響。
def fix_blockquote_linebreaks(text):
    lines = text.split("\n")
    for i, line in enumerate(lines):
        if line.startswith(">") and line[1:].strip():
            lines[i] = line.rstrip() + "  "
    return "\n".join(lines)


# python-markdown 預設會讓 .md 原始檔裡寫的原始 HTML 原封不動穿透進最終頁面,
# 不會自動跳脫(這是 Markdown 的標準行為,不是這裡的 bug)。故事草稿常常是從
# 外部檔案貼進來的,萬一裡面夾帶了 <script> 之類的標籤,build 完就會變成一段
# 在公開網站上真的會執行的程式碼。用一組寬鬆但涵蓋主要向量的 regex 在讀進
# 每個章節時掃一遍,抓到就直接讓整個建置失敗,而不是默默把它發布出去。
DANGEROUS_HTML_PATTERNS = [
    (re.compile(r"<\s*(script|iframe|object|embed|svg|style|link|meta|base|form)\b", re.I), "危險標籤"),
    (re.compile(r"\bon[a-z]+\s*=", re.I), "行內事件處理屬性(on*=)"),
    (re.compile(r"javascript\s*:", re.I), "javascript: 協定"),
]


def scan_dangerous_html(text):
    """掃一份章節原始 markdown 文字,找出可能被瀏覽器當成可執行內容的原始 HTML。
    回傳 [(行號, 命中的原文片段, 分類), ...],依行號排序;沒有就回傳空列表。"""
    hits = []
    for pattern, label in DANGEROUS_HTML_PATTERNS:
        for m in pattern.finditer(text):
            line_no = text.count("\n", 0, m.start()) + 1
            hits.append((line_no, m.group(0), label))
    hits.sort(key=lambda h: h[0])
    return hits


_HTML_TAG_RE = re.compile(r"<[^>]+>")
_HTML_UNESCAPE = (
    ("&amp;", "&"), ("&lt;", "<"), ("&gt;", ">"), ("&quot;", '"'), ("&#39;", "'"),
)


def html_to_search_text(html):
    """把章節內文的 HTML 轉回一段純文字,給全文搜尋索引用(不用完美,只求能被搜到)。"""
    text = _HTML_TAG_RE.sub(" ", html)
    for esc, ch in _HTML_UNESCAPE:
        text = text.replace(esc, ch)
    return re.sub(r"\s+", " ", text).strip()


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


def list_md(src_dir):
    if not os.path.isdir(src_dir):
        return []
    return sorted(f for f in os.listdir(src_dir) if f.endswith(".md"))


if __name__ == "__main__":
    # 每一季讀出自己資料夾裡的 .md 檔清單
    for s in SEASONS:
        s["files"] = list_md(s["src"])
    print("、".join(f'第{CN_NUM[s["num"]]}季 {len(s["files"])} 篇' for s in SEASONS)
          + f',共 {sum(len(s["files"]) for s in SEASONS)} 個章節檔案')

    # 重複編號警告:同一季裡兩個檔案共用同一個數字前綴(通常是手誤,比如
    # 複製舊檔案改標題時忘記改編號)。這不影響排序或素材配對是否正確
    # (slug 才是真正的配對依據),也不會讓 build 失敗,只是編號本身有歧義、
    # 容易搞錯故事的先後順序,所以印出來提醒,但繼續往下建置。
    for s in SEASONS:
        dupes = find_duplicate_numbers(s["files"])
        if dupes:
            print(f'{WARN}⚠ 警告:第{CN_NUM[s["num"]]}季有重複的章節編號,'
                  f'不影響建置,但可能弄錯故事順序:{RESET}')
            for (n, suffix), fs in sorted(dupes.items()):
                print(f'{WARN}    編號 {n}{suffix}:{"、".join(fs)}{RESET}')

    # 章節 slug 集合,用來過濾素材:只有檔名(去副檔名)對得上某章節的
    # 圖片/音樂才會被複製進 docs/,資料夾裡其餘不相干的檔案一律跳過
    slugs = {slugify(f) for s in SEASONS for f in s["files"]}

    # 把所有章節的原始檔內容先整批讀進來、掃一輪危險 HTML。刻意放在任何
    # docs/ 清空/複製動作之前:一旦中伏就直接中止,docs/ 連碰都不會被碰到,
    # 不會留下一個清到一半的目錄。掃過的內容留著給下面的 chapters 迴圈直接
    # 重用,不用再讀一次檔案。
    raw_texts = {}  # (season_num, filename) -> 檔案內容
    html_violations = []  # [(檔案路徑, 行號, 命中片段, 分類), ...]
    for s in SEASONS:
        for f in s["files"]:
            path = os.path.join(s["src"], f)
            with open(path, "r", encoding="utf-8") as fh:
                text = fh.read()
            raw_texts[(s["num"], f)] = text
            for line_no, matched, label in scan_dangerous_html(text):
                html_violations.append((os.path.relpath(path, PROJECT_ROOT), line_no, matched, label))

    if html_violations:
        print("\n建置中止:偵測到原始 .md 檔案裡有可能被瀏覽器直接執行的 HTML 內容", file=sys.stderr)
        print("(python-markdown 會讓這類內容原封不動穿透進最終頁面,不會自動跳脫)\n", file=sys.stderr)
        for filepath, line_no, matched, label in html_violations:
            print(f"  {filepath}:{line_no}  [{label}]  {matched!r}", file=sys.stderr)
        print(f"\n共 {len(html_violations)} 處。確認是誤判、或真的要保留這段內容的話,"
              f"改寫掉(或跟我說要不要調整 DANGEROUS_HTML_PATTERNS)後再重新建置。", file=sys.stderr)
        sys.exit(1)

    from templates import (
        BUTTERFLY_SVG, HEADER, FOOTER, HTML_SHELL, LIGHTBOX,
        SW_REGISTER, SERVICE_WORKER, render_player, render_player_js,
        render_search, render_search_js, render_search_index,
    )

    sw_register_chapter = SW_REGISTER.replace("__ROOT__", "../")
    sw_register_root = SW_REGISTER.replace("__ROOT__", "")

    # docs/ 底下這幾個子資料夾整個是建置產物,先清空再重建。
    # 不清的話,改名或刪掉的章節/素材會在 docs/ 裡留下孤兒檔案;而 find_media
    # 這些函式是去 docs/ 裡比對的,孤兒檔案會被錯配到另一個還存在的章節上
    # (例:Journal/wrong_words.jpeg 改名成 case_file_sketch.jpeg 後,舊的
    #  docs/journal/wrong_words.jpeg 沒被清掉,同一張手帳就同時出現在兩篇故事)。
    os.makedirs(OUT_DIR, exist_ok=True)
    for d in (CHAPTERS_DIR, SONGS_DIR, POLAROIDS_DIR, JOURNAL_DIR):
        if os.path.isdir(d):
            shutil.rmtree(d)
        os.makedirs(d)
    # 插圖跟縮圖這三個資料夾不整個清掉:裡面的檔案要拿來跟這次的來源檔案比對
    # hash,沒變就跳過重新壓縮(見下面 resize_image_cached)。孤兒檔案改用
    # prune_orphans() 個別清,而不是整批 rmtree。
    for d in (IMAGES_DIR, POLAROID_THUMBS_DIR, JOURNAL_THUMBS_DIR):
        os.makedirs(d, exist_ok=True)

    # GitHub Pages 用:放一個空的 .nojekyll,避免 Jekyll 處理掉某些檔案/資料夾
    open(os.path.join(OUT_DIR, ".nojekyll"), "w").close()

    # 複製 CSS
    shutil.copy(os.path.join(os.path.dirname(__file__), "style.css"), os.path.join(OUT_DIR, "style.css"))

    # 複製字型檔(自行代管,不再向 Google Fonts 發外部請求,見 style.css 開頭的說明)
    fonts_src = os.path.join(os.path.dirname(__file__), "fonts")
    fonts_out = os.path.join(OUT_DIR, "fonts")
    if os.path.isdir(fonts_out):
        shutil.rmtree(fonts_out)
    shutil.copytree(fonts_src, fonts_out)

    # ---- 複製素材:從專案根目錄的 Images/ songs/ Polaroids/ 複製進
    # docs/images docs/songs docs/polaroids ----
    images_src = find_source_dir(IMAGES_SOURCE_CANDIDATES)
    songs_src = find_source_dir(SONGS_SOURCE_CANDIDATES)
    polaroids_src = find_source_dir(POLAROIDS_SOURCE_CANDIDATES)

    journal_src = find_source_dir(JOURNAL_SOURCE_CANDIDATES)

    image_cache_old = load_image_cache()
    image_cache_new = {}

    if images_src:
        copied = reused = skipped = 0
        keep = set()
        for fname in os.listdir(images_src):
            stem, ext = os.path.splitext(fname)
            if ext.lower() in IMAGE_EXTS and stem in slugs:
                # 插圖是讀者順順讀文章時直接看到的(沒有燈箱放大),縮到 IMAGE_MAX_DIM
                # 直接取代原圖,不用另外維護一份縮圖 + 原圖
                keep.add(fname)
                changed = resize_image_cached(
                    os.path.join(images_src, fname), os.path.join(IMAGES_DIR, fname),
                    IMAGE_MAX_DIM, image_cache_old, image_cache_new,
                )
                copied += changed
                reused += not changed
            elif ext.lower() in IMAGE_EXTS:
                skipped += 1
        prune_orphans(IMAGES_DIR, keep)
        print(f"已從 {images_src} 壓縮 {copied} 張圖片到 docs/images/(沿用快取 {reused} 張,跳過 {skipped} 張跟章節對不上的)")
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
        copied = reused = skipped = 0
        keep = set()
        for fname in os.listdir(polaroids_src):
            stem, ext = os.path.splitext(fname)
            if ext.lower() in IMAGE_EXTS and polaroid_matches_any_slug(stem, slugs):
                # 原圖原封不動留給燈箱放大用(POLAROIDS_DIR 還是整批 rmtree,複製很
                # 便宜不需要快取);縮圖比較貴,另外存一份給小卡跟兩個相簿頁用
                keep.add(fname)
                shutil.copy(os.path.join(polaroids_src, fname), os.path.join(POLAROIDS_DIR, fname))
                changed = resize_image_cached(
                    os.path.join(polaroids_src, fname), os.path.join(POLAROID_THUMBS_DIR, fname),
                    THUMB_MAX_DIM, image_cache_old, image_cache_new,
                )
                copied += changed
                reused += not changed
            elif ext.lower() in IMAGE_EXTS:
                skipped += 1
        prune_orphans(POLAROID_THUMBS_DIR, keep)
        print(f"已從 {polaroids_src} 複製 {copied + reused} 張拍立得照片到 docs/polaroids/,產生縮圖 {copied} 張(沿用快取 {reused} 張,跳過 {skipped} 張跟章節對不上的)")
    else:
        print(f"警告:找不到拍立得來源資料夾(嘗試過 {POLAROIDS_SOURCE_CANDIDATES}),跳過拍立得複製")

    if journal_src:
        copied = reused = skipped = 0
        keep = set()
        for fname in os.listdir(journal_src):
            stem, ext = os.path.splitext(fname)
            if ext.lower() in IMAGE_EXTS and polaroid_matches_any_slug(stem, slugs):
                keep.add(fname)
                shutil.copy(os.path.join(journal_src, fname), os.path.join(JOURNAL_DIR, fname))
                changed = resize_image_cached(
                    os.path.join(journal_src, fname), os.path.join(JOURNAL_THUMBS_DIR, fname),
                    THUMB_MAX_DIM, image_cache_old, image_cache_new,
                )
                copied += changed
                reused += not changed
            elif ext.lower() in IMAGE_EXTS:
                skipped += 1
        prune_orphans(JOURNAL_THUMBS_DIR, keep)
        print(f"已從 {journal_src} 複製 {copied + reused} 頁手帳到 docs/journal/,產生縮圖 {copied} 頁(沿用快取 {reused} 頁,跳過 {skipped} 頁跟章節對不上的)")
    else:
        print(f"警告:找不到手帳來源資料夾(嘗試過 {JOURNAL_SOURCE_CANDIDATES}),跳過手帳複製")

    save_image_cache(image_cache_new)

    chapters = []  # 收集每章 metadata,供首頁與導覽使用
    for s in SEASONS:
        for f in s["files"]:
            num, num_suffix = parse_chapter_num(f)
            text = raw_texts[(s["num"], f)]  # 前面掃危險 HTML 時已經讀過,直接重用
            slug = slugify(f)
            chapters.append({
                "num": num,
                "num_suffix": num_suffix,
                "season": s["num"],
                "title": extract_title(text),
                "slug": slug,
                "section": get_section(num, s["sections"]),
                "raw": text,
                "image_file": find_media(slug, IMAGES_DIR, IMAGE_EXTS),
                "audio_file": find_media(slug, SONGS_DIR, AUDIO_EXTS),
                "polaroid_files": find_polaroids(slug, POLAROIDS_DIR, IMAGE_EXTS),
                "journal_files": find_journal_pages(slug, JOURNAL_DIR, IMAGE_EXTS),
            })

    # 閱讀順序:一季一季來,每季內依檔名編號,同編號再依插入字母後綴排
    # (沒有後綴排最前面,002 在 002a 前面;002a 在 002b 前面)
    chapters.sort(key=lambda c: (c["season"], c["num"], c["num_suffix"]))

    # 播放器封面圖(給系統鎖屏 / 控制中心 / AirPods 的 Media Session 用):
    # 優先該章第一張拍立得,其次插圖,兩者都沒有就用第一季第一章的插圖
    default_cover = (
        "images/" + chapters[0]["image_file"]
        if chapters and chapters[0].get("image_file") else ""
    )

    def chapter_cover(c):
        if c["polaroid_files"]:
            return "thumbs/polaroids/" + c["polaroid_files"][0]  # 鎖屏封面圖用縮圖就夠了
        if c["image_file"]:
            return "images/" + c["image_file"]
        return default_cover

    # 全站播放清單:按章節順序,只收錄真的有配樂的章節(不是佔位)
    playlist = [
        {
            "title": c["title"], "file": c["audio_file"], "section": c["section"],
            "slug": c["slug"], "cover": chapter_cover(c),
        }
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
    search_entries = []  # 全文搜尋索引,跟章節頁一起邊產生邊收集
    for i, ch in enumerate(chapters):
        fixed_raw = fix_blockquote_linebreaks(fix_nested_emphasis(ch["raw"]))
        body_html = md_lib.markdown(fixed_raw, extensions=["extra"])
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
                f'<img src="../thumbs/polaroids/{f}" data-full="../polaroids/{f}" '
                f'alt="{ch["title"]} 拍立得照片" loading="lazy">'
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
                f'<img src="../thumbs/journal/{f}" data-full="../journal/{f}" '
                f'alt="{ch["title"]} Max 的手帳" loading="lazy">'
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

        season_prefix = "" if ch["season"] == 1 else f'第{CN_NUM[ch["season"]]}季 · '
        if ch["num"] == 0:  # 000_ 檔名當序章處理
            chapter_meta = f'{season_prefix}序章 · {ch["section"]}'
        elif ch["season"] == 1:
            chapter_meta = f'第 {ch["num"]:03d}{ch["num_suffix"]} 章 · {ch["section"]}'
        else:
            chapter_meta = f'{season_prefix}第 {ch["num"]:02d}{ch["num_suffix"]} 章 · {ch["section"]}'

        search_entries.append({
            "title": ch["title"], "slug": ch["slug"], "meta": chapter_meta,
            "text": html_to_search_text(body_html),
        })

        content = f"""
<main class="chapter-page">
  <div class="chapter-meta">{chapter_meta}</div>
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
            player=render_player("../"),
            search=render_search("../", len(chapters)),
            content=content,
            footer=FOOTER,
            lightbox=LIGHTBOX,
            sw_register=sw_register_chapter,
        )
        with open(os.path.join(CHAPTERS_DIR, f"{ch['slug']}.html"), "w", encoding="utf-8") as out:
            out.write(html)

    print(f"已產生 {len(chapters)} 個章節頁面")

    # ---------- 產生首頁 ----------
    def chapter_card(c):
        if c["num"] == 0:
            num = "序章"
        elif c["season"] == 1:
            num = f'{c["num"]:03d}{c["num_suffix"]}'
        else:
            num = f'{c["num"]:02d}{c["num_suffix"]}'
        num_label = num if c["season"] == 1 else f'S{c["season"]} · {num}'
        return (
            f'<a class="chapter-card" href="chapters/{c["slug"]}.html">'
            f'{render_badges(c)}'
            f'<div class="ch-num">{num_label}</div>'
            f'<div class="ch-title">{c["title"]}</div>'
            f'</a>'
        )

    def render_section(label, name, desc, section_chapters, is_open=False, extra_class=""):
        """一個可折疊的篇章分區:<details> 原生折疊,標題+篇數+簡介放 <summary>,
        展開才顯示章節卡片。is_open 控制預設是否展開。"""
        cards = "\n      ".join(chapter_card(c) for c in section_chapters)
        cls = ("section-block " + extra_class).strip()
        open_attr = " open" if is_open else ""
        return f"""
<details class="{cls}"{open_attr}>
  <summary class="section-summary">
    <span class="section-num">{label}</span>
    <h2 class="section-name">{name}</h2>
    <span class="section-count">{len(section_chapters)} 章</span>
    <span class="section-desc">{desc}</span>
  </summary>
  <div class="chapter-grid">
      {cards}
  </div>
</details>
"""

    def render_season(season):
        """一整季的首頁區塊:非預設季在最前面加一條 season-divider,底下是這一季
        所有非空的篇章分區(每個都是預設收合的 <details>)。"""
        season_chapters = [c for c in chapters if c["season"] == season["num"]]
        if not season_chapters:
            return ""
        div = season["divider"]
        extra = "" if div is None else "season-block"
        blocks = []
        for idx, (name, lo, hi, desc) in enumerate(season["sections"], start=1):
            sec_chapters = [c for c in season_chapters if lo <= c["num"] <= hi]
            if not sec_chapters:
                continue
            blocks.append(render_section(f"{idx:02d}", name, desc, sec_chapters, extra_class=extra))
        header = ""
        if div is not None:
            header = f"""
<div class="season-divider">
  <div class="eyebrow">{div["eyebrow"]}</div>
  <h2>第{CN_NUM[season["num"]]}季 · {div["name"]}</h2>
  <p class="season-desc">{div["desc"]}</p>
</div>
"""
        return header + "\n".join(blocks)

    seasons_html = "\n".join(render_season(s) for s in SEASONS)

    hero = f"""
<div class="hero">
  <div class="eyebrow">LIFE IS STRANGE · FAN FICTION ARCHIVE</div>
  <h1>雙保結局</h1>
  <p class="subtitle">如果那年風暴之後，小鎮與 Chloe 都活了下來</p>
  <p class="premise">
    官方原作把玩家推向一道殘酷的電車難題——<strong>犧牲小鎮，或是犧牲 Chloe</strong>，
    二選一，沒有第三條路。這部合集是對那道難題的另一種回答：<br><br>
    <strong>如果 somehow，兩者都保住了呢？</strong><br><br>
    這裡收錄了{len(chapters)}章，從風暴退去的第一個清晨，一路到畢業典禮的夏天，
    再到四個人在波特蘭重新開始的新生活，
    記錄著 Chloe 與 Max，還有這座小鎮上每一個劫後餘生的人，
    如何在一個「不該存在」的結局裡，笨拙卻真實地活下去。
  </p>
</div>
<div class="hero-divider">❦</div>
"""

    index_content = hero + '<div class="sections">' + seasons_html + "</div>"
    index_html = HTML_SHELL.format(
        title="雙保結局 · 拍立得檔案",
        root="",
        butterfly=BUTTERFLY_SVG,
        header=HEADER.format(root=""),
        player=render_player(""),
        search=render_search("", len(chapters)),
        content=index_content,
        footer=FOOTER,
        lightbox=LIGHTBOX,
        sw_register=sw_register_root,
    )
    with open(os.path.join(OUT_DIR, "index.html"), "w", encoding="utf-8") as out:
        out.write(index_html)

    print("首頁已產生:index.html")

    # ---------- 產生拍立得相簿頁 ----------
    if all_polaroids:
        gallery_cards = "\n".join(
            f'''<a class="gallery-card" href="chapters/{p['slug']}.html">
                  <div class="polaroid-card polaroid-card-lg" style="--rot: {(-4 + (i % 5) * 2)}deg">
                    <img src="thumbs/polaroids/{p['file']}" data-full="polaroids/{p['file']}" alt="{p['title']} 拍立得照片" loading="lazy">
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
        player=render_player(""),
        search=render_search("", len(chapters)),
        content=gallery_content,
        footer=FOOTER,
        lightbox=LIGHTBOX,
        sw_register=sw_register_root,
    )
    with open(os.path.join(OUT_DIR, "polaroids.html"), "w", encoding="utf-8") as out:
        out.write(gallery_html)

    print("拍立得相簿已產生:polaroids.html")

    # ---------- 產生 Max 的手帳頁 ----------
    if all_journal:
        journal_cards = "\n".join(
            f'''<a class="journal-card" href="chapters/{p['slug']}.html" style="--rot: {(-2 + (i % 3) * 2)}deg">
                  <figure class="journal-page">
                    <img src="thumbs/journal/{p['file']}" data-full="journal/{p['file']}" alt="{p['title']} Max 的手帳" loading="lazy">
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
        player=render_player(""),
        search=render_search("", len(chapters)),
        content=journal_content,
        footer=FOOTER,
        lightbox=LIGHTBOX,
        sw_register=sw_register_root,
    )
    with open(os.path.join(OUT_DIR, "journal.html"), "w", encoding="utf-8") as out:
        out.write(journal_html)

    print("Max 的手帳已產生:journal.html")

    # ---------- 產生 player.js(全站播放清單資料 + 播放器邏輯) ----------
    # 抽成獨立檔,加一首歌只會動到這個檔,不會讓每個章節頁都產生 diff
    with open(os.path.join(OUT_DIR, "player.js"), "w", encoding="utf-8") as out:
        out.write(render_player_js(playlist))
    print(f"播放器已產生:player.js({len(playlist)} 首)")

    # ---------- 產生全文搜尋(search.js + search-index.json) ----------
    # 邏輯跟索引資料分開:加一篇故事只會動到 search-index.json,search.js 不變
    with open(os.path.join(OUT_DIR, "search.js"), "w", encoding="utf-8") as out:
        out.write(render_search_js())
    with open(os.path.join(OUT_DIR, "search-index.json"), "w", encoding="utf-8") as out:
        out.write(render_search_index(search_entries))
    print(f"全文搜尋已產生:search.js + search-index.json({len(search_entries)} 篇)")

    # ---------- 產生 Service Worker(版本 = docs/ 內容 hash) ----------
    # 版本號用內容 hash 而非時間戳:只有 docs/ 真的有東西變了,sw.js 才變,
    # 回訪讀者也才會被要求重新快取(不然每次建置都白洗一次快取)。
    # macOS Finder(或其他系統/編輯器)隨手逛過 docs/ 底下任何一層資料夾,都可能
    # 自己產生這些雜訊檔案,內容跟真正的網站產出完全無關,卻會被 os.walk 掃到。
    # 之前就是漏了排除這個,才會出現「明明沒改東西,兩次建置的內容 hash 卻不一樣」
    # (.DS_Store 的內容會隨 Finder 開過幾次資料夾自己變動)。
    JUNK_BASENAMES = {".DS_Store", "Thumbs.db", "desktop.ini"}

    def docs_content_hash(path, exclude):
        rels = []
        for base_dir, _dirs, names in os.walk(path):
            for name in names:
                if name in JUNK_BASENAMES:
                    continue
                rel = os.path.relpath(os.path.join(base_dir, name), path)
                if rel not in exclude:
                    rels.append(rel)
        rels.sort()  # 全域排序,不受檔案系統遍歷順序影響
        h = hashlib.sha1()
        for rel in rels:
            h.update(rel.encode("utf-8") + b"\0")
            with open(os.path.join(path, rel), "rb") as fh:
                h.update(fh.read())
        return h.hexdigest()[:12]

    sw_version = "v" + docs_content_hash(OUT_DIR, exclude={"sw.js"})
    with open(os.path.join(OUT_DIR, "sw.js"), "w", encoding="utf-8") as out:
        out.write(SERVICE_WORKER.replace("__CACHE_VERSION__", sw_version))
    print(f"Service Worker 已產生:sw.js({sw_version})")

    print(f"\n完成！網站輸出於: {OUT_DIR}")

