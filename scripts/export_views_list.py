#!/usr/bin/env python3
"""
Export terms with views_2025_jan_nov into a sorted TSV file for analysis.

Output: data/views_2025_jan_nov.tsv
Columns: views_2025_jan_nov, title
"""

from __future__ import annotations

import json
from pathlib import Path

INPUT = Path("data/dict_terms.json")
OUTPUT = Path("data/views_2025_jan_nov.tsv")


def main() -> None:
    data = json.loads(INPUT.read_text(encoding="utf-8"))
    entries = []
    for e in data:
        if "views_2025_jan_nov" in e:
            entries.append((int(e.get("views_2025_jan_nov", 0)), e.get("title", "")))
    entries.sort(key=lambda x: x[0], reverse=True)

    lines = ["views_2025_jan_nov\ttitle"]
    for views, title in entries:
        lines.append(f"{views}\t{title}")
    OUTPUT.write_text("\n".join(lines), encoding="utf-8")
    print(f"Exported {len(entries)} entries to {OUTPUT}")


if __name__ == "__main__":
    main()
