# 府城新食代 — PWA 版

原本的單頁網站已改寫成可安裝、可離線瀏覽的 PWA。

## 檔案結構

```
├── index.html        原網頁 + PWA 標籤 + 安裝按鈕 + SW 註冊
├── manifest.json     App 名稱、圖示、主題色、捷徑
├── sw.js             Service Worker（離線快取）
├── gen_icons.py      重新產生所有 icon 的腳本
├── icons/            已產好的圖示（PNG / SVG / ICO）
└── picture/          你的美食照片 01~06
```

## 美食照片

網頁的六張圖都讀 `picture/` 資料夾：

| 檔名 | 位置 |
|---|---|
| 01 | 網紅打卡 — 土石流草莓千層 |
| 02 | 網紅打卡 — 極致海陸雙拼滷肉飯 |
| 03 | 網紅打卡 — 抹茶熔岩恐龍蛋 |
| 04 | 暗黑獵奇主圖 — 皮蛋焦糖布丁冰（建議橫式大圖） |
| 05 | 暗黑獵奇小卡 — 麻辣鴨血馬卡龍 |
| 06 | 暗黑獵奇小卡 — 香菜滿漢全席披薩 |

副檔名 `.jpg / .jpeg / .png / .webp` 都可以，頁面會自動依序試到讀得到為止；
六張全都找不到時才會顯示線上示意圖。
不過 `sw.js` 的離線預載清單預設寫 `.jpg`，如果你的檔案是別的格式，記得把那六行一起改掉。

## 本機測試

Service Worker **只能在 https 或 localhost 下運作**，直接雙擊 `index.html`（file://）不會生效。

```bash
cd 這個資料夾
python3 -m http.server 8000
```

打開 http://localhost:8000 → 按 F12 →
- **Application ▸ Manifest**：確認名稱、圖示都讀得到
- **Application ▸ Service Workers**：狀態是 activated
- **Network ▸ 勾 Offline** 後重新整理：頁面仍能開啟
- **Lighthouse ▸ PWA**：跑一次檢查

## 上線

丟到任何支援 https 的靜態空間即可（GitHub Pages、Netlify、Vercel、Cloudflare Pages、自家主機）。
四個檔案與 `icons/` 要放在**同一層**。

若不是放在網域根目錄（例如 `example.com/food/`），因為路徑都用相對路徑，直接放進子資料夾就能運作。

## 換圖示

```bash
pip install pillow
python3 gen_icons.py --text 食 --bg1 "#f97316" --bg2 "#facc15"
```

參數：`--text` 中央的字、`--bg1/--bg2` 漸層色、`--fg` 文字色、`--out` 輸出資料夾。
找不到中文字型時會自動改畫刀叉圖案。若要用自己的 Logo，直接把 `icons/` 內同名檔案覆蓋掉即可。

## 改版後要記得

網頁內容更新後，請把 `sw.js` 最上面的 `CACHE_VERSION` 改成新的版本號（例如 `v1.0.1`），
使用者下次開啟時舊快取才會被清掉、拿到新內容。

## 快取策略

| 對象 | 策略 |
|---|---|
| 頁面（index.html） | 網路優先，離線時吃快取 |
| 圖片（Unsplash / placehold） | 先給快取、背景更新；全失敗顯示離線替代圖 |
| CDN（Tailwind、Font Awesome、Google Fonts） | 先給快取、背景更新 |
| 同網域靜態檔 | 快取優先 |
| Google Analytics | 不快取，直接走網路 |

## 已知注意事項

- iOS 沒有 `beforeinstallprompt`，安裝按鈕會改為顯示「分享 ▸ 加入主畫面」的教學。
- Tailwind 用的是 CDN 版本，正式上線建議改成編譯後的 CSS 檔，載入更快、離線更穩。
