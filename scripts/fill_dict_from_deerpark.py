#!/usr/bin/env python3
"""
Fill `_dict/*.md` entries with content fetched from deerpark.app API.

Default: process first 10 files (sorted) to avoid hammering the API.
Modify SAMPLE_SIZE or pass an integer CLI arg to change the batch size.

For each term, the script:
  1) reads front-matter `title` from the markdown file
  2) GETs https://deerpark.app/api/v1/dict/lookup/:title
  3) renders each returned entry as markdown under a heading with its source
  4) overwrites the file body (front-matter preserved)
"""

from __future__ import annotations

import json
import sys
import time
import urllib.parse
import urllib.request
from html import unescape
from html.parser import HTMLParser
from pathlib import Path
from typing import Iterable, List, Tuple

BASE_URL = "https://deerpark.app/api/v1/dict/lookup/"
DICT_DIR = Path("_dict")
DEFAULT_BATCH = 10
REQUEST_TIMEOUT = 10  # seconds
SLEEP_BETWEEN = 0.3  # be polite


class ParagraphExtractor(HTMLParser):
    """Convert simple HTML fragments into plain text paragraphs."""

    def __init__(self) -> None:
        super().__init__()
        self.parts: List[str] = []
        self._in_p = False

    def handle_starttag(self, tag: str, attrs) -> None:  # type: ignore[override]
        if tag.lower() == "p":
            if self.parts and self.parts[-1] != "\n\n":
                self.parts.append("\n\n")
            self._in_p = True
        elif tag.lower() == "br":
            self.parts.append("\n")

    def handle_endtag(self, tag: str) -> None:  # type: ignore[override]
        if tag.lower() == "p":
            if not self.parts or self.parts[-1] != "\n\n":
                self.parts.append("\n\n")
            self._in_p = False

    def handle_data(self, data: str) -> None:  # type: ignore[override]
        txt = unescape(data)
        self.parts.append(txt)

    def get_text(self) -> str:
        text = "".join(self.parts)
        # normalize blank lines
        lines = text.splitlines()
        cleaned = []
        for line in lines:
            cleaned.append(line.rstrip())
        out = "\n".join(cleaned)
        # squeeze multiple blank lines to max 2
        while "\n\n\n" in out:
            out = out.replace("\n\n\n", "\n\n")
        return out.strip()


def html_to_text(html: str) -> str:
    parser = ParagraphExtractor()
    parser.feed(html)
    return parser.get_text()


def iter_titles(paths: Iterable[Path]) -> Iterable[Tuple[Path, str, List[str]]]:
    """Yield (path, title, front_matter_lines)."""
    for path in paths:
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except Exception:
            continue
        if not lines or not lines[0].strip().startswith("---"):
            continue
        fm: List[str] = [lines[0]]
        title = ""
        for line in lines[1:]:
            fm.append(line)
            if line.strip().startswith("---"):
                break
            if line.startswith("title:"):
                title = line.split(":", 1)[1].strip().strip('"').strip()
        if title:
            yield path, title, fm


def fetch_term(term: str) -> Tuple[int, str]:
    url = BASE_URL + urllib.parse.quote(term)
    req = urllib.request.Request(url, headers={"User-Agent": "dict-fill-script"})
    try:
        with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT) as resp:
            body = resp.read().decode("utf-8", errors="replace")
            return resp.getcode(), body
    except Exception as exc:  # pragma: no cover
        return 0, f"ERROR: {exc}"


def render_entry(entry: dict) -> str:
    source = entry.get("dict", "未知來源")
    expl = entry.get("expl", "")
    text = html_to_text(expl) if expl else ""
    return f"**來源：{source}**\n\n{text}\n"


def main() -> None:
    batch = DEFAULT_BATCH
    if len(sys.argv) > 1:
        try:
            batch = int(sys.argv[1])
        except ValueError:
            pass

    files = sorted(DICT_DIR.glob("*.md"))[:batch]
    for path, title, fm in iter_titles(files):
        status, body = fetch_term(title)
        print(f"[{status}] {title} ({path.name})")
        if status != 200:
            print(body[:300])
            print("-" * 40)
            time.sleep(SLEEP_BETWEEN)
            continue
        try:
            payload = json.loads(body)
            data = payload.get("data", [])
        except json.JSONDecodeError:
            print("Invalid JSON")
            print(body[:300])
            print("-" * 40)
            time.sleep(SLEEP_BETWEEN)
            continue

        sections = [render_entry(entry) for entry in data]
        content = "\n".join(sections).strip() or "（未取得內容）"

        # rebuild file: front matter + blank line + content
        new_text = "\n".join(fm)
        if not new_text.endswith("\n"):
            new_text += "\n"
        new_text += "\n" + content + "\n"
        path.write_text(new_text, encoding="utf-8")
        print(f"updated {path}")
        print("-" * 40)
        time.sleep(SLEEP_BETWEEN)


if __name__ == "__main__":
    main()
