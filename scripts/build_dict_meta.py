#!/usr/bin/env python3
"""
Build a lightweight dictionary index (term names only) from `_dict/*.md`.

Output: assets/dict/meta.json
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import List

ROOT = Path(__file__).resolve().parent.parent
DICT_DIR = ROOT / "_dict"
OUT_JSON = ROOT / "assets" / "dict" / "meta.json"


def extract_title(path: Path) -> str:
    title = path.stem
    lines = path.read_text(encoding="utf-8").splitlines()
    if lines and lines[0].startswith("---"):
        for line in lines[1:]:
            if line.strip().startswith("---"):
                break
            if line.startswith("title:"):
                title = line.split(":", 1)[1].strip().strip('"').strip()
                break
    return title or path.stem


def main() -> None:
    entries: List[str] = []
    for path in sorted(DICT_DIR.glob("*.md")):
        entries.append(extract_title(path))

    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(
        json.dumps(entries, ensure_ascii=False, separators=(",", ":")), encoding="utf-8"
    )
    print(f"Wrote {len(entries)} term names to {OUT_JSON}")


if __name__ == "__main__":
    main()
