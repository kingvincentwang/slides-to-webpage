# slides-to-webpage

A [Claude Code](https://claude.com/claude-code) skill：把 PPTX 或 PDF 轉成單一 HTML 檔的 [Reveal.js](https://revealjs.com/) 投影片網頁，可直接放上 GitHub Pages。

## 功能

- 自動判斷來源是圖片型、文字型或混合型
- **圖片型**（NotebookLM 匯出、掃描檔、截圖手冊）：壓縮後內嵌成滿版投影片，畫面與原檔相同
- **文字型**：用網頁元素重建文字、表格和程式碼，並保留演講備忘稿
- 隨機轉場、合成翻頁音效、進度條、頁碼、可分享單頁的網址
- 長文件可加章節目錄
- 公開前掃描敏感資料，並可把遮蔽直接畫進圖片（OCR 僅支援 Windows）

## 安裝

需要 Claude Code（或 Claude 桌面版）與 Python 3。

```bash
git clone https://github.com/kingvincentwang/slides-to-webpage.git ~/.claude/skills/slides-to-webpage
python -m pip install pymupdf pillow
```

Windows PowerShell 請把路徑換成 `"$env:USERPROFILE\.claude\skills\slides-to-webpage"`。

更新時在該資料夾執行 `git pull`。

## 使用

開一個新的工作階段，然後：

```text
/slides-to-webpage 路徑/檔名.pptx
```

也可以附上檔案，直接說「幫我轉成網頁」。

## 限制

- 成品要連上網路才能載入 Reveal.js（文字型還有字型）
- 圖片型的畫面文字無法直接修改
- OCR 可能漏讀小字，敏感資料仍要由人確認
- macOS／Linux 沒有 OCR 掃描，也尚未實際測試

## 公開成品前

GitHub Pages 的頁面任何人都看得到。請確認已遮蔽金鑰、帳號等資料，人物照片已取得同意，並有權公開該文件。

## 授權

[MIT](LICENSE)
