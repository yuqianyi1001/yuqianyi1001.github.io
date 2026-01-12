#!/usr/bin/env python3
import argparse
import re
from pathlib import Path

IMAGE_PATTERN = re.compile(r"!\[([^\]]*)\]\(\.\./images/([^)]+)\)")


def replace_images(file_path: Path, base_url: str) -> int:
    content = file_path.read_text(encoding="utf-8")

    def replacement(match: re.Match[str]) -> str:
        alt_text = match.group(1)
        image_name = match.group(2)
        return f"![{alt_text}]({base_url}/{image_name})"

    updated_content, count = IMAGE_PATTERN.subn(replacement, content)
    if updated_content != content:
        file_path.write_text(updated_content, encoding="utf-8")
    return count


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Replace ../images/... markdown image URLs with a base URL."
    )
    parser.add_argument("file", help="Target markdown file.")
    parser.add_argument(
        "--base",
        default="https://raw.githubusercontent.com/yuqianyi1001/yuqianyi1001.github.io/master/images",
        help="Base URL used to replace ../images/ paths.",
    )
    args = parser.parse_args()

    file_path = Path(args.file)
    count = replace_images(file_path, args.base.rstrip("/"))
    print(f"Replaced {count} image(s) in {file_path}")


if __name__ == "__main__":
    main()
