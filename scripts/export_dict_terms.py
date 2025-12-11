#!/usr/bin/env python3
"""
Export terms from 丁福保佛學大辭典.html into a JSON list for analysis/state tracking.

Output: data/dict_terms.json
Structure:
[
  {
    "title": "一一",
    "href": "%E4%B8%80%E4%B8%80.html"
  },
  ...
]
"""

from __future__ import annotations

import json
from html.parser import HTMLParser
from pathlib import Path
from typing import List

SOURCE = Path("_references/丁福保佛學大辭典.html")
OUT = Path("data/dict_terms.json")


class LinkParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.in_a = False
        self.current_href: str | None = None
        self.entries: List[dict] = []

    def handle_starttag(self, tag: str, attrs) -> None:  # type: ignore[override]
        if tag.lower() == "a":
            href = dict(attrs).get("href")
            if href:
                self.in_a = True
                self.current_href = href

    def handle_data(self, data: str) -> None:  # type: ignore[override]
        if self.in_a and self.current_href:
            text = data.strip()
            if text:
                self.entries.append({"title": text, "href": self.current_href})

    def handle_endtag(self, tag: str) -> None:  # type: ignore[override]
        if tag.lower() == "a":
            self.in_a = False
            self.current_href = None


def main() -> None:
    html_text = SOURCE.read_text(encoding="utf-8")
    parser = LinkParser()
    parser.feed(html_text)

    # remove duplicates preserving order
    seen = set()
    unique_entries = []
    for entry in parser.entries:
        key = (entry["title"], entry["href"])
        if key in seen:
            continue
        seen.add(key)
        unique_entries.append(entry)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(unique_entries, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Exported {len(unique_entries)} entries to {OUT}")


if __name__ == "__main__":
    main()
