"""判斷 PPTX／PDF 是圖片型還是文字型，並列出每頁的文字量與圖片數。"""
import re
import sys
import zipfile
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")


def slide_order(z):
    """依 presentation.xml 的 sldIdLst 回傳投影片路徑，順序不一定等於檔名編號。"""
    pres = z.read("ppt/presentation.xml").decode("utf-8")
    rels = z.read("ppt/_rels/presentation.xml.rels").decode("utf-8")
    targets = {}
    for tag in re.findall(r"<Relationship\b[^>]*>", rels):
        rid = re.search(r'\bId="([^"]+)"', tag).group(1)
        targets[rid] = re.search(r'\bTarget="([^"]+)"', tag).group(1)
    block = re.search(r"<p:sldIdLst>(.*?)</p:sldIdLst>", pres, re.S).group(1)
    return ["ppt/" + targets[r].lstrip("/").replace("ppt/", "") for r in re.findall(r'r:id="([^"]+)"', block)]


def inspect_pptx(path):
    with zipfile.ZipFile(path) as z:
        size = re.search(r'<p:sldSz cx="(\d+)" cy="(\d+)"', z.read("ppt/presentation.xml").decode("utf-8"))
        slide_w, slide_h = int(size.group(1)), int(size.group(2))
        names = set(z.namelist())
        rows = []
        for path_in_zip in slide_order(z):
            xml = z.read(path_in_zip).decode("utf-8")
            chars = sum(len(t) for t in re.findall(r"<a:t>([^<]*)</a:t>", xml))
            pics = re.findall(r"<p:pic>.*?</p:pic>", xml, re.S)
            cover = 0.0
            for pic in pics:
                m = re.search(r'<a:ext cx="(\d+)" cy="(\d+)"', pic)
                if m:
                    cover = max(cover, int(m.group(1)) * int(m.group(2)) / (slide_w * slide_h))
            rows.append((chars, len(pics), cover))
        note = any(n.startswith("ppt/notesSlides/") for n in names)
        return rows, f"投影片比例 {slide_w / slide_h:.3f}，備忘稿：{'有' if note else '無'}"


def inspect_pdf(path):
    import pymupdf
    d = pymupdf.open(path)
    if d.is_encrypted:
        sys.exit("這份 PDF 有密碼保護，請使用者先解除保護。")
    rows = []
    for p in d:
        area = p.rect.width * p.rect.height
        cover = 0.0
        for info in p.get_image_info():
            x0, y0, x1, y1 = info["bbox"]
            cover = max(cover, (x1 - x0) * (y1 - y0) / area)
        rows.append((len(p.get_text().strip()), len(p.get_images()), cover))
    return rows, f"頁面 {d[0].rect.width:.0f}×{d[0].rect.height:.0f}，內建大綱 {len(d.get_toc())} 項"


def main():
    src = Path(sys.argv[1])
    ext = src.suffix.lower()
    if ext == ".pptx":
        rows, info = inspect_pptx(src)
    elif ext == ".pdf":
        rows, info = inspect_pdf(src)
    else:
        sys.exit(f"不支援 {ext}；舊版 .ppt 請先另存為 .pptx。")

    image_pages = [i for i, (chars, _, cover) in enumerate(rows, 1) if cover >= 0.8 and chars <= 30]
    text_pages = [i for i, (chars, _, _) in enumerate(rows, 1) if chars > 30]
    ratio = len(image_pages) / len(rows)
    kind = "圖片型" if ratio >= 0.8 else "文字型" if len(text_pages) / len(rows) >= 0.8 else "混合型"

    print(f"來源：{src.name}（{src.stat().st_size / 1048576:.1f} MB）")
    print(f"共 {len(rows)} 頁；{info}")
    print(f"判定：{kind}（滿版圖片頁 {len(image_pages)}，文字頁 {len(text_pages)}）")
    print("頁\t字數\t圖片\t最大圖覆蓋率")
    for i, (chars, pics, cover) in enumerate(rows, 1):
        print(f"{i}\t{chars}\t{pics}\t{cover:.0%}")


if __name__ == "__main__":
    main()
