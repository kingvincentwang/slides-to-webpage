"""依 masks.json 把遮蔽畫進頁面影像，覆蓋 pNNN.webp，並在 check/ 輸出複查用的圖。

用法：apply_masks.py 工作目錄 masks.json

每次都從未遮蔽的 hi/ 重畫，所以修改座標後重跑即可，不會疊加舊遮罩。
"""
import json
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

sys.stdout.reconfigure(encoding="utf-8")

GRAY = "#cfd5dc"
LABEL = "#5d6b7a"
FONT = "C:/Windows/Fonts/msjhbd.ttc"


def font(size):
    try:
        return ImageFont.truetype(FONT, size)
    except OSError:
        return ImageFont.load_default(size)


def main():
    work = Path(sys.argv[1])
    masks = json.loads(Path(sys.argv[2]).read_text(encoding="utf-8"))
    info = json.loads((work / "manifest.json").read_text(encoding="utf-8"))
    size = (info["width"], info["height"])
    check = work / "check"
    check.mkdir(exist_ok=True)

    for key, spec in masks.items():
        p = int(key)
        im = Image.open(work / "hi" / f"p{p:03d}.png").convert("RGB").resize(size, Image.LANCZOS)
        d = ImageDraw.Draw(im)
        for box in spec.get("boxes", []):
            d.rectangle(box, fill=GRAY)
        for block in spec.get("blocks", []):
            d.rectangle(block["box"], fill=GRAY)
            if block.get("label"):
                x0, y0, x1, y1 = block["box"]
                d.text(((x0 + x1) / 2, (y0 + y1) / 2), block["label"], fill=LABEL,
                       font=font(block.get("size", 30)), anchor="mm")
        for rep in spec.get("replace", []):
            x0, y0, x1, y1 = rep["box"]
            d.rectangle(rep["box"], fill=rep.get("fill", GRAY))
            d.text((x0 + 2, (y0 + y1) / 2), rep["text"], fill=rep.get("color", LABEL),
                   font=font(rep.get("size", 24)), anchor="lm")
        im.save(work / f"p{p:03d}.webp", "WEBP", quality=info.get("quality", 72), method=6)
        im.resize((size[0] * 2, size[1] * 2), Image.LANCZOS).save(check / f"p{p:03d}.png")
        im.save(check / f"p{p:03d}.jpg", quality=88)
    print(f"已遮蔽 {len(masks)} 頁。請對 {check} 再跑 OCR，並用 Read 看 check/pNNN.jpg，然後重新建置。")


if __name__ == "__main__":
    main()
