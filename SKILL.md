---
name: slides-to-webpage
description: 把 PPT／PPTX 或 PDF 轉成單一 HTML 檔的 Reveal.js 投影片網頁（可放 GitHub Pages），附轉場、翻頁音效、進度條、頁碼、章節目錄，並在公開前掃描與遮蔽敏感資料。只要使用者給了 .pptx 或投影片、手冊類 PDF，並說「轉成網頁」「做成這種網頁」「轉 HTML」「放到 GitHub Pages」「線上投影片」「reveal」，或貼出類似的投影片網址要照做，就使用此 skill；即使只丟檔案、延續先前的轉換工作也一樣。要產生 .pptx、編輯 PPT 本身、或把考卷做成逐題解說網頁時不適用。
---

# 投影片轉網頁

把 PPTX／PDF 轉成一個 HTML 檔：Reveal.js 從 CDN 載入，圖片以 Base64 內嵌，所以只管理一個檔案，也能直接放上 GitHub Pages。

腳本在 `scripts/`，範本在 `assets/`，以下 `$S` 代表此 skill 的目錄。把工作檔放在暫存目錄（例如 scratchpad），成品放在使用者的工作資料夾。

需要 Python 的 `pymupdf`、`Pillow`。缺少時先告知使用者再安裝。Python 指令一律加 `-I`，並在暫存目錄之外執行腳本，避免載入下載檔案旁的模組。

## 1. 判斷來源類型

```bash
python -I "$S/scripts/inspect_source.py" "來源檔"
```

依結果選擇轉換方式。類型決定了使用者之後能否修改內容，所以要告訴使用者選了哪一種、原因是什麼。

| 來源 | 判斷依據 | 做法 |
|---|---|---|
| 圖片型（NotebookLM 匯出、掃描檔、截圖手冊） | 每頁幾乎沒有文字，一張圖滿版 | 走「A. 圖片投影片」 |
| 文字型（真正的文字、表格、程式碼） | 每頁有大量文字 | 走「B. 重建網頁」 |
| 混合型 | 兩者都有 | 依多數頁面選擇，少數頁面用圖片嵌入 B，或文字重打 |

重建能換來可搜尋、可修改、檔案小；圖片型則保留原本的視覺設計。原作已是精心設計的整頁圖片時，不要重新排版。

## A. 圖片投影片

### 算圖並看過每一頁

```bash
python -I "$S/scripts/render_pages.py" "來源檔" 工作目錄
```

產生 `pNNN.webp`、OCR 用的 `hi/pNNN.png`、`manifest.json`，以及每張 16 頁的 `sheets/sNN.jpg`。

用 Read 看完所有縮圖，並記下章節起始頁和敏感資料。縮圖上的紅色頁碼是為了檢視而加，不會進入成品。

頁數不多（約 30 頁內）時，直接讀每頁大圖，打出文字放進 `text.json`，供螢幕報讀軟體使用：

```json
{"1": {"title": "標題", "lines": ["第一段", "第二段"]}}
```

頁數很多時，改為只提供章節名稱作為替代文字，並告知使用者畫面文字無法搜尋。

### 章節目錄

超過約 25 頁就製作 `chapters.json`。長手冊沒有目錄會很難使用，頁數少則不需要。

```json
[{"name": "一、系統簡介", "start": 7, "subs": [["核心架構", 7], ["系統概述", 8]]}]
```

頁碼一律以實際頁面為準，因為來源的目錄通常沒有標頁碼，也可能和內容不完全相符。

### 建置

```bash
python -I "$S/scripts/build_deck.py" 工作目錄 成品.html --title "兩到四個詞的標題" --chapters chapters.json --text text.json --accent "#2b3990" --bg "#ffffff"
```

`--chapters`、`--text` 可省略。`--accent` 取自來源的主色，`--bg` 取自頁面邊緣的顏色，這樣長寬比不同時，留白才不突兀。

## B. 重建網頁

1. 從 PPTX 的 `ppt/slides/slideN.xml` 抽出文字（注意 `sldIdLst` 的順序），備忘稿在 `ppt/notesSlides/`。顏色與字型從 XML 的 `srgbClr`、`typeface` 統計出來。PDF 用 `pymupdf` 的 `page.get_text()`，並對照頁面畫面，修正表格與多欄的閱讀順序。
2. 複製 `assets/text-deck.html`，修改 `:root` 的色彩、字型和內容。範本已含轉場、音效和備忘稿外掛。
3. 用網頁元素重建，不要轉成圖片：真正的 `<table>`、`<pre>`、內嵌 SVG 圖示。小圖示重畫成 SVG 會比原本的 PNG 清晰。
4. 備忘稿逐頁放進 `<aside class="notes">`。背景用 `data-background-color`，才會滿版。
5. 內容照原文，不自行改寫。發現疑似錯字或過時資訊時，保留原文並告知使用者。

## 2. 檢查

只有實際在瀏覽器看過才算完成。瀏覽器窗格無法開啟 `file://`，所以暫時建立 `.claude/launch.json`，用 `python -m http.server` 綁定 `127.0.0.1` 來預覽，檢查完停止伺服器並刪除該檔案。

- 用 JavaScript 先把所有 section 的 `data-transition` 改成 `none`，再 `Reveal.slide(i)` 逐頁檢查。否則截圖或量測可能落在轉場中途，被誤判為版面問題。
- 圖片型：確認每張 `img` 的 `naturalWidth` 正確。小字至少抽看一頁大圖，確認壓縮後還讀得清楚。
- 重建型：在切換到該頁後量每個元素的底部與右側，確認都在畫布內，並逐頁截圖。
- 目錄：點小節能跳頁，關閉後方向鍵仍能換頁。
- 檢查按鈕和控制箭頭沒有蓋住標題或內容。
- 手機寬度看一次。圖片型直拿時會很小，若是如此就直接告知。
- 翻頁聲無法由 Claude 聽到，所以要請使用者自行確認，不要說已測試。

## 3. 敏感資料

轉換前後都先想一件事：GitHub Pages 的頁面任何人都看得到。手冊和後台截圖常有授權金鑰、帳號、IP、序號，教學簡報常有學生照片。

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File "$S\scripts\ocr.ps1" -Dir 工作目錄\hi -Out 工作目錄\ocr.json
```

```bash
python -I "$S/scripts/scan_sensitive.py" 工作目錄/ocr.json
```

輸出候選頁、類型和頁面座標。OCR 需要 Windows 已安裝語言的辨識元件。

OCR 不夠可靠，IP 這類小字可能讀錯，所以要加上肉眼檢查。帳號設定、裝置詳細資料、儀表板「最近活動」、地圖這幾種畫面要讀大圖。

把結果以「頁面／內容／風險」的表格告知使用者，並列出刻意保留的項目。**使用者要求後才遮蔽**，因為遮蔽會改變內容，例如金鑰被遮後學員就看不到。

### 遮蔽

把座標寫進 `masks.json`（頁面像素，與 `manifest.json` 的寬高相同）：

```json
{
  "14": {"boxes": [[270, 648, 372, 678]],
         "blocks": [{"box": [716, 385, 1348, 722], "label": "地圖位置已遮蔽"}]},
  "92": {"replace": [{"box": [596, 356, 1392, 392], "fill": "#ffff00", "color": "#e0201b", "size": 28, "text": "（請填入貴校的授權金鑰）"}]}
}
```

```bash
python -I "$S/scripts/apply_masks.py" 工作目錄 masks.json
```

遮蔽是畫在高解析度來源上再重新壓縮，所以原始資料不會留在 HTML 裡。不要只用 CSS 蓋住，那樣原圖仍可下載。

遮蔽後：

1. 對 `工作目錄/check` 再跑一次 OCR 與掃描，確認資料已消失。
2. 用 Read 看 `check/pNNN.jpg`，確認沒有蓋到旁邊的說明文字，地圖也要看清楚有沒有漏出邊緣。
3. 重新建置，覆蓋舊的 HTML，避免誤傳未遮蔽版。
4. 提醒使用者：原始 PPT／PDF 仍未遮蔽；已外流的金鑰需要更換，光遮蔽網頁無法收回。

## 4. 交付

成品交給使用者，不主動上傳或發布。結尾說明：

- 使用了哪種轉換方式，容量由多少變成多少。
- 實際檢查過什麼，沒檢查的也要說（翻頁聲、只看縮圖的頁面）。
- 需要網路才能載入 Reveal.js 與字型。
- 公開前要確認的事：學生或人物照片是否取得同意、他人文件是否有權公開、批評性內容、備忘稿也會公開在原始碼中、AI 產生的內容要查證。

被問到如何發布時，說明：上傳 HTML 到公開 repository，在 Settings → Pages 選擇分支，網址是 `https://帳號.github.io/repo/檔名.html`。
