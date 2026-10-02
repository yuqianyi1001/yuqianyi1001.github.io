#!/usr/bin/env python3
"""Check posts for things that would stop them from becoming a WeChat draft.

Run before committing a post, and by .github/workflows/check-posts.yml on every
pull request and push:

    python3 scripts/check_posts.py                  # every post from CHECK_SINCE on
    python3 scripts/check_posts.py _posts/2026-10-01-xxx.md

Errors (exit 1):
- `description` longer than 120 characters: WeChat rejects the draft (errcode 45004);
- no `title`;
- file name not `YYYY-MM-DD-english-short-name.md`.
Warning only:
- no `thumb_media_id` and no image in the post: the sync waits until there is a cover.

Only posts dated CHECK_SINCE or later are checked by default; older ones are
never synced (see SYNC_SINCE in wechat_auto_sync.py).
"""

from __future__ import annotations

import pathlib
import re
import sys

import yaml

DESCRIPTION_MAX_CHARS = 120  # keep in step with DIGEST_MAX_CHARS in wechat_draft_sync.py
CHECK_SINCE = "2026-09-25"
NAME_RE = re.compile(r"^(\d{4}-\d{2}-\d{2})-[a-z0-9]+(-[a-z0-9]+)*\.md$")
IMAGE_RE = re.compile(r"!\[[^\]]*\]\([^)\s]+")
ROOT = pathlib.Path(__file__).resolve().parent.parent


def check(path: pathlib.Path) -> tuple[list[str], list[str]]:
    errors, warnings = [], []
    if not NAME_RE.match(path.name):
        errors.append("file name must be YYYY-MM-DD-english-short-name.md (lowercase, kebab-case)")
    text = path.read_text(encoding="utf-8")
    parts = text.split("---", 2)
    if not text.startswith("---") or len(parts) < 3:
        return errors + ["no front matter"], warnings
    try:
        meta = yaml.safe_load(parts[1]) or {}
    except yaml.YAMLError as exc:
        return errors + [f"front matter is not valid YAML: {exc}"], warnings
    if not str(meta.get("title") or "").strip():
        errors.append("no title")
    description = str(meta.get("description") or "").strip()
    if len(description) > DESCRIPTION_MAX_CHARS:
        errors.append(
            f"description is {len(description)} characters, the limit is {DESCRIPTION_MAX_CHARS} "
            f"(cut {len(description) - DESCRIPTION_MAX_CHARS}); WeChat rejects the draft otherwise"
        )
    if not str(meta.get("thumb_media_id") or "").strip() and not IMAGE_RE.search(parts[2]):
        warnings.append("no thumb_media_id and no image: the WeChat sync will wait for a cover")
    return errors, warnings


def main(argv: list[str]) -> int:
    if argv:
        paths = [pathlib.Path(a) for a in argv]
    else:
        paths = [p for p in sorted((ROOT / "_posts").glob("*.md")) if p.name[:10] >= CHECK_SINCE]
    failed = 0
    for path in paths:
        errors, warnings = check(path)
        for message in errors:
            print(f"ERROR {path.name}: {message}")
        for message in warnings:
            print(f"warn  {path.name}: {message}")
        failed += bool(errors)
    print(f"checked {len(paths)} posts, {failed} with errors")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
