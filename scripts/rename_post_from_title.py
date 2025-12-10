#!/usr/bin/env python3
"""
Rename a Jekyll post using a translated, slugified title.

Requirements:
  pip install openai

Environment:
   DASHSCOPE_API_KEY
  BAILIAN_BASE_URL (optional, defaults to Bailian compatible URL)
  BAILIAN_MODEL (optional, defaults to qwen-flash)

Usage:
  python3 scripts/rename_post_from_title.py path/to/post.md [--dry-run]
"""
import argparse
import datetime as _dt
import os
import re
import sys
import unicodedata
from typing import Optional
from pathlib import Path

from openai import OpenAI


def _read_file(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        sys.exit(f"File not found: {path}")


def _front_matter_title(lines: list[str]) -> Optional[str]:
    if not lines or lines[0].strip() != "---":
        return None
    try:
        end = lines.index("---", 1)
    except ValueError:
        return None
    for line in lines[1:end]:
        m = re.match(r"^title:\s*(.+)$", line.strip(), flags=re.IGNORECASE)
        if m:
            raw = m.group(1).strip()
            if raw.startswith(("'", '"')) and raw.endswith("'", '"') and len(raw) >= 2:
                return raw[1:-1]
            return raw
    return None


def _first_heading(lines: list[str]) -> Optional[str]:
    for line in lines:
        m = re.match(r"^#\s+(.*)$", line.strip())
        if m:
            return m.group(1).strip()
    return None


def extract_title(text: str) -> str:
    lines = text.splitlines()
    title = _front_matter_title(lines)
    if title:
        return title
    heading = _first_heading(lines)
    if heading:
        return heading
    sys.exit("No title found in front matter or first H1 heading.")


def slugify(text: str, max_length: int = 80) -> str:
    normalized = unicodedata.normalize("NFKD", text)
    ascii_text = normalized.encode("ascii", "ignore").decode("ascii")
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", ascii_text).strip("-").lower()
    slug = slug or "post"
    return slug[:max_length].rstrip("-")


def load_env_from_file(env_path: Path) -> None:
    """Populate os.environ with values from .env if they are not already set."""
    if not env_path.exists():
        return
    for line in env_path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, val = stripped.split("=", 1)
        key = key.strip()
        val = val.strip().strip("\"'")
        if key and key not in os.environ:
            os.environ[key] = val


def get_client() -> OpenAI:
    api_key = (
        os.getenv("BAILIAN_API_KEY")
        or os.getenv("DASHSCOPE_API_KEY")
        or os.getenv("OPENAI_API_KEY")
    )
    if not api_key:
        sys.exit("Missing API key. Set BAILIAN_API_KEY, DASHSCOPE_API_KEY, or OPENAI_API_KEY.")
    base_url = os.getenv(
        "BAILIAN_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1"
    )
    return OpenAI(api_key=api_key, base_url=base_url)


def translate_title(title: str, client: OpenAI, model: str) -> str:
    system_prompt = (
        "Translate the Chinese post title into concise English (8 words max) "
        "appropriate for a blog URL. Return only the translated title."
    )
    resp = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": title},
        ],
        temperature=0.2,
        max_tokens=64,
    )
    translated = resp.choices[0].message.content.strip()
    return translated


def derive_date(path: Path) -> str:
    m = re.match(r"(\d{4}-\d{2}-\d{2})", path.name)
    if m:
        return m.group(1)
    return _dt.date.today().isoformat()


def main() -> None:
    parser = argparse.ArgumentParser(description="Rename post using translated title.")
    parser.add_argument("file", help="Path to the markdown post")
    parser.add_argument("--model", default=os.getenv("BAILIAN_MODEL", "qwen2.5-7b-instruct"))
    parser.add_argument("--dry-run", action="store_true", help="Show the planned rename without applying it")
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parent.parent
    load_env_from_file(repo_root / ".env")

    src_path = Path(args.file).resolve()
    content = _read_file(src_path)
    original_title = extract_title(content)

    client = get_client()
    translated = translate_title(original_title, client, args.model)
    slug = slugify(translated)
    date_prefix = derive_date(src_path)
    new_name = f"{date_prefix}-{slug}.md"
    new_path = src_path.with_name(new_name)

    if new_path == src_path:
        print(f"Name already matches target: {new_name}")
        return
    if new_path.exists():
        sys.exit(f"Target file already exists: {new_path}")

    print(f"Original title: {original_title}")
    print(f"Translated:     {translated}")
    print(f"Slug:           {slug}")
    print(f"Renaming:       {src_path.name} -> {new_name}")

    if args.dry_run:
        return

    src_path.rename(new_path)
    print(f"Renamed to {new_name}")


if __name__ == "__main__":
    main()
