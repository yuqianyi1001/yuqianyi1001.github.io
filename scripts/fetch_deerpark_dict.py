#!/usr/bin/env python3
"""
Fetch sample dictionary entries from deerpark.app for terms listed in _dict/*.md.

By default it reads the first 10 markdown files, extracts the front-matter title,
and performs GET https://deerpark.app/api/v1/dict/lookup/:term for each.
It only prints the HTTP status and payload; no files are modified.
"""

from __future__ import annotations

import json
import time
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Iterable, Tuple

BASE_URL = "https://deerpark.app/api/v1/dict/lookup/"
DICT_DIR = Path("_dict")
SAMPLE_SIZE = 10
REQUEST_TIMEOUT = 10  # seconds
SLEEP_BETWEEN = 1  # polite spacing


def iter_titles(paths: Iterable[Path]) -> Iterable[Tuple[Path, str]]:
    """Yield (path, title) from the front matter of markdown files."""
    for path in paths:
        try:
            with path.open("r", encoding="utf-8") as f:
                lines = f.readlines()
        except Exception:
            continue
        if not lines or not lines[0].strip().startswith("---"):
            continue
        for line in lines[1:]:
            if line.strip().startswith("---"):
                break
            if line.startswith("title:"):
                title = line.split(":", 1)[1].strip().strip('"').strip()
                if title:
                    yield path, title
                break


def fetch_term(term: str) -> Tuple[int, str]:
    """Fetch a term from the API, returning (status, body_text)."""
    url = BASE_URL + urllib.parse.quote(term)
    req = urllib.request.Request(url, headers={"User-Agent": "dict-fetch-script"})
    try:
        with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT) as resp:
            body = resp.read().decode("utf-8", errors="replace")
            return resp.getcode(), body
    except Exception as exc:  # pragma: no cover - network/path issues
        return 0, f"ERROR: {exc}"


def main() -> None:
    files = sorted(DICT_DIR.glob("*.md"))[:SAMPLE_SIZE]
    for path, title in iter_titles(files):
        status, body = fetch_term(title)
        print(f"[{status}] {title} ({path.name})")
        if status == 200:
            try:
                data = json.loads(body)
                print(json.dumps(data, ensure_ascii=False, indent=2))
            except json.JSONDecodeError:
                print(body[:500])
        else:
            print(body[:500])
        print("-" * 40)
        time.sleep(SLEEP_BETWEEN)


if __name__ == "__main__":
    main()
