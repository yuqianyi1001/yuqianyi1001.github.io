#!/usr/bin/env python3
"""
Generate pre-rendered HTML pages for dictionary entries to speed up site builds.

Reads `_dict/*.md` (front matter + body), converts body to simple HTML, and writes
grouped pages into `dict-pages/`:
  - page-N.html (default 200 entries per page)
  - index.html listing all pages

Jekyll is configured to skip `_dict` during build; the generated HTML files are
static and copied as-is.
"""

from __future__ import annotations

import html
import math
import re
import sys
from pathlib import Path
from typing import List, Tuple

ROOT = Path(__file__).resolve().parent.parent
DICT_DIR = ROOT / "_dict"
OUT_DIR = ROOT / "dict-pages"
PAGE_SIZE = 200  # entries per page


def parse_md(path: Path) -> Tuple[str, str]:
    """Return (title, body_text) from a markdown file with front matter."""
    lines = path.read_text(encoding="utf-8").splitlines()
    if not lines or not lines[0].startswith("---"):
        return path.stem, ""
    title = path.stem
    body_lines: List[str] = []
    in_fm = True
    for line in lines[1:]:
        if in_fm:
            if line.startswith("title:"):
                title = line.split(":", 1)[1].strip().strip('"').strip()
            if line.strip().startswith("---"):
                in_fm = False
            continue
        body_lines.append(line)
    return title or path.stem, "\n".join(body_lines).strip()


def md_to_html(md: str) -> str:
    """Very light markdown to HTML: paragraphs and <br>, escaping HTML."""
    if not md:
        return "<p>（待补充）</p>"
    paragraphs = re.split(r"\n\s*\n", md.strip())
    html_parts: List[str] = []
    for para in paragraphs:
        lines = para.splitlines()
        safe = "<br>".join(html.escape(line) for line in lines)
        html_parts.append(f"<p>{safe}</p>")
    return "\n".join(html_parts)


def build_page(title: str, entries: List[Tuple[str, str]]) -> str:
    items = []
    for t, body_html in entries:
        items.append(f"<section class=\"entry\"><h2>{html.escape(t)}</h2>\n{body_html}</section>")
    content = "\n".join(items)
    return f"""<!doctype html>
<html lang="zh">
<head>
  <meta charset="utf-8">
  <title>{html.escape(title)}</title>
  <style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; margin: 2rem auto; max-width: 960px; padding: 0 1rem; line-height: 1.6; }}
    h1 {{ font-size: 1.6rem; margin-bottom: 1rem; }}
    h2 {{ font-size: 1.2rem; margin: 1.2rem 0 0.3rem; }}
    .entry {{ border-bottom: 1px solid #eee; padding-bottom: 0.8rem; }}
  </style>
</head>
<body>
  <h1>{html.escape(title)}</h1>
  {content}
</body>
</html>
"""


def main() -> None:
    page_size = PAGE_SIZE
    if len(sys.argv) > 1:
        try:
            page_size = max(1, int(sys.argv[1]))
        except ValueError:
            pass

    md_files = sorted(DICT_DIR.glob("*.md"))
    entries: List[Tuple[str, str]] = []
    for path in md_files:
        title, body = parse_md(path)
        entries.append((title, md_to_html(body)))

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    total = len(entries)
    pages = math.ceil(total / page_size) if total else 0
    links: List[str] = []

    for i in range(pages):
        chunk = entries[i * page_size : (i + 1) * page_size]
        page_title = f"佛学概念词典（第 {i + 1} 页，共 {pages} 页）"
        html_text = build_page(page_title, chunk)
        outfile = OUT_DIR / f"page-{i + 1}.html"
        outfile.write_text(html_text, encoding="utf-8")
        links.append(f"<li><a href=\"page-{i + 1}.html\">第 {i + 1} 页</a></li>")

    index_html = f"""<!doctype html>
<html lang="zh">
<head>
  <meta charset="utf-8">
  <title>佛学概念词典索引</title>
  <style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; margin: 2rem auto; max-width: 720px; padding: 0 1rem; line-height: 1.6; }}
    h1 {{ font-size: 1.6rem; margin-bottom: 1rem; }}
  </style>
</head>
<body>
  <h1>佛学概念词典索引</h1>
  <p>共 {total} 条目，{pages} 页。页面为静态预生成，加快加载。</p>
  <ul>
    {"".join(links)}
  </ul>
</body>
</html>
"""
    (OUT_DIR / "index.html").write_text(index_html, encoding="utf-8")
    print(f"Generated {pages} pages ({total} entries) into {OUT_DIR}")


if __name__ == "__main__":
    main()
