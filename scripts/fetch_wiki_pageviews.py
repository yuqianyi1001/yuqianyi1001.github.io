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
DEFAULT_BATCH_SIZE = 100
DEFAULT_MAX_TOTAL = None  # None means process all
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
    # Skip if already processed (done) or already fetched once (Not Found).
    # {    "title": "一三昧",
#     "href": "%25E4%25B8%2580%25E4%25B8%2589%25E6%2598%25A7.html",
    
#     "last_error": "NotFound"},
#   {
#     "title": "一中",
#     "href": "%25E4%25B8%2580%25E4%25B8%25AD.html",
#     "views_2025_jan_nov": 588}, 

    if entry.get("last_error") in {"NotFound"} or (entry.get("views_2025_jan_nov") is not None and int(entry.get("views_2025_jan_nov")) >= 0):
        return True

    return False


def fetch_views(title: str) -> tuple[int, str]:
    url = API_TEMPLATE.format(article=urllib.parse.quote(title), start=START, end=END)
    print(f"Fetching URL: {url}")
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
    # CLI: batch_size [max_total]
    batch_size = DEFAULT_BATCH_SIZE
    max_total = DEFAULT_MAX_TOTAL
    if len(sys.argv) > 1:
        try:
            batch_size = max(1, int(sys.argv[1]))
        except ValueError:
            pass
    if len(sys.argv) > 2:
        try:
            max_total = max(1, int(sys.argv[2]))
        except ValueError:
            pass

    terms = load_terms()
    processed_total = 0
    updated = 0
    batch_count = 0
    dirty_since_save = False
    for entry in terms:
        if max_total is not None and processed_total >= max_total:
            break
        if should_skip(entry):
            continue
        title = entry.get("title")
        if not title:
            continue

        print(f"Processing No.{processed_total+1} Title:{title} ")
        status_code, body = fetch_views(title)
        now = datetime.utcnow().isoformat() + "Z"
        if status_code == 200:
            try:
                payload = json.loads(body)
                print(payload)

                total_views = sum_views(payload)
                entry["views_2025_jan_nov"] = total_views
                entry["status"] = "done"
                entry.pop("last_error", None)

                print(f"Title:{title} views_2025_jan_nov：{total_views}")
            except json.JSONDecodeError:
                entry["status"] = "error"
                entry["last_error"] = "Invalid JSON"
        elif status_code == 404:
            entry["status"] = "not_found"
            entry["last_error"] = "Not Found"
        else:
            entry["status"] = "error"
            entry["last_error"] = f"HTTP {status_code}: {body[:200]}"
            print(f"Error fetching title:{title}, status_code: {status_code}, body: {body[:200]}")
            break  # stop on error for investigation

        entry["last_fetched"] = now
        processed_total += 1
        updated += 1
        dirty_since_save = True
        time.sleep(SLEEP_BETWEEN)
        batch_count += 1
        if batch_count >= batch_size:
            import random
            pause = random.uniform(2, 5)
            if dirty_since_save:
                save_terms(terms)
                dirty_since_save = False
            print(f"Batch completed ({processed_total}); sleeping {pause:.2f}s")
            time.sleep(pause)
            batch_count = 0

    if dirty_since_save:
        save_terms(terms)

    print(f"Processed {processed_total} entries (updated {updated})")


if __name__ == "__main__":
    main()
