#!/usr/bin/env python3
"""
Fetch 2025-01-01 to 2025-11-30 zh.wikipedia pageviews for terms in data/dict_terms.json.

- Processes terms in batches; default limit: first 100 terms.
- Saves progress back into data/dict_terms.json by adding:
    "status": "done"|"not_found"|"error"
    "views_2025_jan_nov": <int>   # sum of views
    "last_error": <str>           # if error
    "last_fetched": <timestamp>
- Resumable: re-run will skip entries with status in {"done","not_found"} unless forced.
"""

from __future__ import annotations

import json
import sys
import time
import urllib.parse
import urllib.request
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

INPUT = Path("data/dict_terms.json")
DEFAULT_LIMIT = 100
START = "20250101"
END = "20251130"
API_TEMPLATE = (
    "https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/"
    "zh.wikipedia/all-access/user/{article}/daily/{start}/{end}"
)
SLEEP_BETWEEN = 0.3  # seconds
TIMEOUT = 10


def load_terms() -> List[Dict[str, Any]]:
    data = json.loads(INPUT.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError("dict_terms.json is not a list")
    return data


def save_terms(data: List[Dict[str, Any]]) -> None:
    INPUT.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def should_skip(entry: Dict[str, Any]) -> bool:
    # Skip if already processed (done/not_found) or already fetched once.
    if entry.get("status") in {"done", "not_found"}:
        return True
    if entry.get("last_fetched"):
        return True
    return False


def fetch_views(title: str) -> tuple[int, str]:
    url = API_TEMPLATE.format(article=urllib.parse.quote(title), start=START, end=END)
    req = urllib.request.Request(url, headers={"User-Agent": "dict-wiki-fetch/0.1"})
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            body = resp.read().decode("utf-8", errors="replace")
            return resp.getcode(), body
    except Exception as exc:  # pragma: no cover
        return 0, f"ERROR: {exc}"


def sum_views(payload: Dict[str, Any]) -> int:
    items = payload.get("items", [])
    total = 0
    for item in items:
        try:
            total += int(item.get("views", 0))
        except Exception:
            continue
    return total


def main() -> None:
    limit = DEFAULT_LIMIT
    if len(sys.argv) > 1:
        try:
            limit = int(sys.argv[1])
        except ValueError:
            pass

    terms = load_terms()
    processed = 0
    updated = 0
    for idx, entry in enumerate(terms):
        if processed >= limit:
            break
        if should_skip(entry):
            continue
        title = entry.get("title")
        if not title:
            continue

        print(f"Processing No.{processed+1} Title:{title} ")
        status_code, body = fetch_views(title)
        now = datetime.utcnow().isoformat() + "Z"
        if status_code == 200:
            try:
                payload = json.loads(body)
                total_views = sum_views(payload)
                entry["views_2025_jan_nov"] = total_views
                entry["status"] = "done"
                entry.pop("last_error", None)
            except json.JSONDecodeError:
                entry["status"] = "error"
                entry["last_error"] = "Invalid JSON"
        elif status_code == 404:
            entry["status"] = "not_found"
            entry["last_error"] = "Not Found"
        else:
            entry["status"] = "error"
            entry["last_error"] = f"HTTP {status_code}: {body[:200]}"
        entry["last_fetched"] = now
        processed += 1
        updated += 1
        time.sleep(SLEEP_BETWEEN)

    if updated:
        save_terms(terms)
    print(f"Processed {processed} entries (updated {updated}) out of limit {limit}")


if __name__ == "__main__":
    main()
