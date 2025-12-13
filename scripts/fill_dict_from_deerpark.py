#!/usr/bin/env python3
"""
Fetch dict content from deerpark.app for terms listed in data/dict_terms.json.

Behavior:
  - Reads/writes data/dict_terms.json (resumable state).
  - Processes in batches of 10 terms (default), sleeps 0.3s between requests.
  - Skips entries with status in {"done", "not_found"}.
  - On HTTP 429 or any non-200/404 error, saves state and stops.
  - On success, stores rendered markdown into _dict/<safe filename>.md and updates JSON:
        status: done
        last_error: cleared
        last_fetched: timestamp
  - On 404: status: not_found, records last_fetched and last_error.

CLI: python3 scripts/fill_dict_from_deerpark.py [batch_size]
"""

from __future__ import annotations

import json
import re
import sys
import time
import urllib.parse
import urllib.request
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple

DATA_FILE = Path("data/dict_terms.json")
DICT_DIR = Path("_dict")
BASE_URL = "https://deerpark.app/api/v1/dict/lookup/"
DEFAULT_BATCH = 10
REQUEST_TIMEOUT = 10
SLEEP_BETWEEN = 0.3


def load_terms() -> List[Dict[str, Any]]:
    data = json.loads(DATA_FILE.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError("dict_terms.json is not a list")
    return data


def save_terms(data: List[Dict[str, Any]]) -> None:
    DATA_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def iter_titles(entries: Iterable[Dict[str, Any]]) -> Iterable[Dict[str, Any]]:
    for entry in entries:
        if entry.get("status") in {"done", "not_found"}:
            continue
        yield entry


def safe_filename(title: str, max_len: int = 120) -> str:
    cleaned = re.sub(r'[\\\\/<>:\"|?*]', "_", title).strip()
    if not cleaned:
        cleaned = "untitled"
    if len(cleaned) > max_len:
        cleaned = cleaned[:max_len]
    return cleaned + ".md"


def fetch_term(term: str) -> Tuple[int, str]:
    url = BASE_URL + urllib.parse.quote(term)
    req = urllib.request.Request(url, headers={"User-Agent": "dict-fill-script/0.2"})
    try:
        with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT) as resp:
            body = resp.read().decode("utf-8", errors="replace")
            return resp.getcode(), body
    except Exception as exc:  # pragma: no cover
        return 0, f"ERROR: {exc}"


def render_entry(entry: dict) -> str:
    source = entry.get("dict", "未知來源")
    expl = entry.get("expl", "")
    return f"**來源：{source}**\n\n{expl}\n"


def process_entry(entry: Dict[str, Any]) -> Tuple[bool, str]:
    title = entry.get("title") or entry.get("word") or ""
    if not title:
        return True, "skip-empty-title"
    
    if entry.get("status_fill") in ("error", "done", "not_found"):
        print(f"Skipping already processed entry: {title} with status_fill: {entry.get('status_fill')}")
        return True, "skip-processed"

    time.sleep(SLEEP_BETWEEN)
    status_code, body = fetch_term(title)
    
    if status_code == 200:
        try:
            payload = json.loads(body)
            data = payload.get("data", [])
        except json.JSONDecodeError:
            entry["status_fill"] = "error"
            entry["last_error_fill"] = "Invalid JSON"
            return False, "invalid-json"
        sections = [render_entry(e) for e in data]
        content = "\n".join(sections).strip() or "（未取得內容）"
        fname = safe_filename(title)
        DICT_DIR.mkdir(exist_ok=True)
        md = f"---\ntitle: {title}\nsource: deerpark.app\n---\n\n{content}\n"
        (DICT_DIR / fname).write_text(md, encoding="utf-8")
        entry["status_fill"] = "done"
        entry.pop("last_error_fill", None)
        return True, "ok"
    elif status_code == 404:
        entry["status_fill"] = "not_found"
        entry["last_error_fill"] = "Not Found"
        return True, "not_found"
    elif status_code == 0 and "Not Found" in body:
        entry["status_fill"] = "not_found"
        entry["last_error_fill"] = "Not Found"
        return True, "not_found"
    elif status_code == 429:
        entry["status_fill"] = "error"
        entry["last_error_fill"] = f"HTTP 429: {body[:200]}"
        return False, "rate_limited"
    else:
        entry["status_fill"] = "error"
        entry["last_error_fill"] = f"HTTP {status_code}: {body[:200]}"
        return False, "http_error"


def main() -> None:
    batch_size = DEFAULT_BATCH
    if len(sys.argv) > 1:
        try:
            batch_size = max(1, int(sys.argv[1]))
        except ValueError:
            pass

    terms = load_terms()
    processed = 0
    dirty = False

    for entry in iter_titles(terms):
        print(f"Processing Title:{entry.get('title','')} ")
        ok, reason = process_entry(entry)
        processed += 1
        dirty = True
        

        if processed % batch_size == 0:
            save_terms(terms)
            dirty = False
            print(f"Batch saved after {processed} entries")

        if not ok and reason in {"rate_limited", "http_error"}:
            print(f"Stopping due to error: {reason}")
            break

    if dirty:
        save_terms(terms)
        print("Saved final progress")

    print(f"Processed {processed} entries (batch size {batch_size})")


if __name__ == "__main__":
    main()
