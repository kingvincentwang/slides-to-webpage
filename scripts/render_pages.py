"""把圖片型 PPTX／PDF 算成壓縮圖、OCR 用高解析圖與檢視縮圖。

用法：render_pages.py 來源檔 工作目錄 [--width 1400] [--quality 72]
"""
import argparse
import io
import json
import math
import posixpath
import re
import sys
import zipfile
from pathlib import Path

from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).parent))
from inspect_source import slide_order


def pptx_pages(path):
    """每頁取覆蓋面積最大的圖片；不適用於文字型投影片。"""
    with zipfile.ZipFile(path) as z:
        for slide in slide_order(z):
            xml = z.read(slide).decode("utf-8")
            rels_path = posixpath.join(posixpath.dirname(slide), "_rels", posixpath.basename(slide) + ".rels")
            rels = z.read(rels_path).decode("utf-8")
            targets = {}
            for tag in re.findall(r"<Relationship\b[^>]*>", rels):
                targets[re.search(r'\bId="([^"]+)"', tag).group(1)] = re.search(r'\bTarget="([^"]+)"', tag).group(1)
            best, best_area = None, -1
            for pic in re.findall(r"<p:pic>.*?</p:pic>", xml, re.S):
                rid = re.search(r'r:embed="([^"]+)"', pic)
                ext = re.search(r'<a:ext cx="(\d+)" cy="(\d+)"', pic)
                area = int(ext.group(1)) * int(ext.group(2)) if ext else 0
                if rid and area > best_area:
                    best, best_area = rid.group(1), area
            if best is None:
                sys.exit(f"{slide} 沒有圖片：這份不是圖片型，請改用重建方式。")
            target = posixpath.normpath(posixpath.join(posixpath.dirname(slide), targets[best]))
            yield Image.open(io.BytesIO(z.read(target))).convert("RGB")


def pdf_pages(path, width):
    import pymupdf
    d = pymupdf.open(path)
    for p in d:
        # 以 2 倍輸出寬度算圖，給 OCR 與遮蔽使用
        z = width * 2 / p.rect.width
        px = p.get_pixmap(matrix=pymupdf.Matrix(z, z), alpha=False)
        yield Image.frombytes("RGB", (px.width, px.height), px.samples)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("source")
    ap.add_argument("workdir")
    ap.add_argument("--width", type=int, default=1400)
    ap.add_argument("--quality", type=int, default=72)
    a = ap.parse_args()

    src, out = Path(a.source), Path(a.workdir)
    (out / "hi").mkdir(parents=True, exist_ok=True)
    (out / "sheets").mkdir(exist_ok=True)
    pages = pptx_pages(src) if src.suffix.lower() == ".pptx" else pdf_pages(src, a.width)

    thumbs, total, size = [], 0, None
    for i, im in enumerate(pages, 1):
        if size is None:
            # PPTX 的圖不放大超過原尺寸，壓縮只會更糊
            w = min(a.width, im.width) if src.suffix.lower() == ".pptx" else a.width
            size = (w, round(im.height * w / im.width))
        # 所有頁統一尺寸，遮蔽座標與版面才會一致
        page = im.resize(size, Image.LANCZOS)
        page.save(out / f"p{i:03d}.webp", "WEBP", quality=a.quality, method=6)
        total += (out / f"p{i:03d}.webp").stat().st_size
        hi = im if im.width >= size[0] * 2 else page.resize((size[0] * 2, size[1] * 2), Image.LANCZOS)
        hi.resize((size[0] * 2, size[1] * 2), Image.LANCZOS).save(out / "hi" / f"p{i:03d}.png")
        thumbs.append(page.resize((476, round(476 * size[1] / size[0])), Image.LANCZOS))

    (out / "manifest.json").write_text(
        json.dumps({"width": size[0], "height": size[1], "pages": len(thumbs), "quality": a.quality}),
        encoding="utf-8",
    )

    cols, rows = 4, 4
    cw, ch = 480, thumbs[0].height + 4
    for s in range(math.ceil(len(thumbs) / (cols * rows))):
        sheet = Image.new("RGB", (cols * cw, rows * ch), "white")
        draw = ImageDraw.Draw(sheet)
        for k, t in enumerate(thumbs[s * cols * rows:(s + 1) * cols * rows]):
            x, y = (k % cols) * cw, (k // cols) * ch
            sheet.paste(t, (x, y))
            draw.rectangle([x, y, x + 44, y + 20], fill="red")
            draw.text((x + 6, y + 4), str(s * cols * rows + k + 1), fill="white")
        sheet.save(out / "sheets" / f"s{s + 1:02d}.jpg", quality=80)

    mb = total / 1048576
    print(f"{len(thumbs)} 頁，{size[0]}×{size[1]}，WebP {mb:.2f} MB，內嵌後約 {mb * 4 / 3:.2f} MB")
    print(f"檢視縮圖：{out / 'sheets'}（紅色數字是頁碼，不會進入成品）")


if __name__ == "__main__":
    main()
