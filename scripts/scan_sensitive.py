"""從 OCR 結果篩出疑似敏感資料，列出頁碼、類型與頁面座標（已換算回輸出尺寸）。

結果只是候選：OCR 會讀錯小字，也可能把範例值或一般文字列入。
"""
import json
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")

PATTERNS = {
    "電子郵件": r"[\w.\-]+@[\w\-]+\.[\w.\-]+|[\w.\-]+@(gmail|mail|icloud|yahoo|outlook|hotmail)|\.edu\.tw",
    "IP": r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b",
    "序號": r"\b(?=[A-Z0-9]*\d)(?=[A-Z0-9]*[A-Z])[A-Z0-9]{9,14}\b",
    "金鑰": r"[0-9A-Fa-f]{5,}-[0-9A-Fa-f]{4,}|License|API[_ ]?Key|[Tt]oken|[Ss]ecret",
    "識別碼": r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}|\b[0-9a-f]{24,}\b",
    "電話": r"\b09\d{8}\b|\b0\d-?\d{7,8}\b",
    "身分證": r"\b[A-Z][12]\d{8}\b",
    "帳密欄位": r"密碼[:：]|[Pp]assword[:：]|Apple ?ID|身分證|住址",
    "地圖": r"距離|衛星檢視|Lat ?Lng|GPS",
}


def main():
    rows = json.load(open(sys.argv[1], encoding="utf-8-sig"))
    if isinstance(rows, dict):
        rows = [rows]
    found = {}
    for r in rows:
        text = r["text"].replace(" ", "")
        kinds = [k for k, p in PATTERNS.items() if re.search(p, text)]
        words = r.get("words") or []
        if kinds and words:
            box = [
                min(w["x"] for w in words) // 2,
                min(w["y"] for w in words) // 2,
                max(w["x"] + w["w"] for w in words) // 2,
                max(w["y"] + w["h"] for w in words) // 2,
            ]
            found.setdefault(r["p"], []).append((kinds, box, text[:60]))
    if not found:
        print("OCR 沒有找到候選項目；仍要用肉眼檢查帳號、裝置與地圖畫面。")
    for page in sorted(found):
        print(f"--- 第 {page} 頁")
        for kinds, box, text in found[page]:
            print(f"  {'/'.join(kinds)} {box} {text}")
    print(f"\n共 {len(found)} 頁有候選項目。OCR 會漏讀小字，帳號、裝置、地圖畫面仍要讀大圖確認。")


if __name__ == "__main__":
    main()
