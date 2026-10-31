"""把工作目錄的 pNNN.webp 組成單檔 Reveal.js 網頁。

用法：build_deck.py 工作目錄 成品.html --title 標題
        [--chapters chapters.json] [--text text.json] [--accent #2b3990] [--bg #ffffff]
"""
import argparse
import base64
import html
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

ASSETS = Path(__file__).parent.parent / "assets"


def load(path):
    return json.loads(Path(path).read_text(encoding="utf-8")) if path else None


def page_label(page, chapters):
    chap = sub = ""
    for c in chapters or []:
        for title, start in c["subs"]:
            if start <= page:
                chap, sub = c["name"], title
    return f"第 {page} 頁：{chap}－{sub}" if chap else f"第 {page} 頁"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("workdir")
    ap.add_argument("output")
    ap.add_argument("--title", required=True)
    ap.add_argument("--chapters")
    ap.add_argument("--text")
    ap.add_argument("--accent", default="#2b3990")
    ap.add_argument("--bg", default="#ffffff")
    a = ap.parse_args()

    work = Path(a.workdir)
    info = json.loads((work / "manifest.json").read_text(encoding="utf-8"))
    w, h, total = info["width"], info["height"], info["pages"]
    chapters = load(a.chapters)
    text = load(a.text) or {}

    sections = []
    for p in range(1, total + 1):
        data = base64.b64encode((work / f"p{p:03d}.webp").read_bytes()).decode()
        hidden = ""
        entry = text.get(str(p))
        if entry:
            lines = "".join(f"<p>{html.escape(x)}</p>" for x in entry.get("lines", []))
            hidden = f'<div class="sr-only"><h2>{html.escape(entry.get("title", ""))}</h2>{lines}</div>'
        alt = entry.get("title") if entry else page_label(p, chapters)
        sections.append(
            f'    <section><img data-src="data:image/webp;base64,{data}" alt="{html.escape(alt or "")}" '
            f'width="{w}" height="{h}" />{hidden}</section>'
        )

    nav = ""
    if chapters:
        blocks = []
        for c in chapters:
            items = "".join(
                f'<li><button type="button" data-page="{s}"><span>{html.escape(t)}</span><small>{s}</small></button></li>'
                for t, s in c["subs"]
            )
            blocks.append(f'<details data-start="{c["start"]}"><summary>{html.escape(c["name"])}</summary><ul>{items}</ul></details>')
        nav = (ASSETS / "toc.html").read_text(encoding="utf-8").replace("__TITLE__", html.escape(a.title)).replace(
            "__NAV__", "\n  ".join(blocks)
        )

    page = (ASSETS / "image-deck.html").read_text(encoding="utf-8")
    for key, value in {
        "__TITLE__": html.escape(a.title),
        "__ACCENT__": a.accent,
        "__BG__": a.bg,
        "__W__": str(w),
        "__H__": str(h),
        "__TOC__": nav,
        "__SECTIONS__": "\n".join(sections),
    }.items():
        page = page.replace(key, value)
    out = Path(a.output)
    out.write_text(page, encoding="utf-8")
    print(f"{total} 頁，{out.stat().st_size / 1048576:.2f} MB，目錄：{'有' if chapters else '無'}，隱藏文字：{len(text)} 頁")


if __name__ == "__main__":
    main()
