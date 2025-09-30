#!/usr/bin/env python3
"""Extract base64-encoded images from a Markdown file and save them to disk."""

from __future__ import annotations

import argparse
import base64
import datetime as dt
import os
import pathlib
import re
from typing import Dict, List, Tuple

# Regex grabs reference label, mime type, and base64 payload.
IMAGE_REF_PATTERN = re.compile(
    r"^\[([^\]]+)\]: <data:(image/[^;]+);base64,([A-Za-z0-9+/=\s]+)>$",
    re.MULTILINE,
)


def extract_images(markdown_path: pathlib.Path, output_dir: pathlib.Path) -> List[Tuple[str, pathlib.Path]]:
    """Parse `markdown_path` for base64 image references and write them under `output_dir`.

    Returns a list of (reference_label, saved_path) tuples for reporting purposes.
    """

    if not markdown_path.exists():
        raise FileNotFoundError(f"Markdown file not found: {markdown_path}")

    content = markdown_path.read_text(encoding="utf-8")
    matches = list(IMAGE_REF_PATTERN.finditer(content))

    if not matches:
        return []

    output_dir.mkdir(parents=True, exist_ok=True)

    saved: List[Tuple[str, pathlib.Path]] = []
    replacements: Dict[str, str] = {}
    sequence = 0

    for match in matches:
        label, mime_type, b64_payload = match.groups()
        extension = mime_type.split("/")[-1]

        # Remove whitespace introduced by line wrapping.
        payload = re.sub(r"\s+", "", b64_payload)

        try:
            image_bytes = base64.b64decode(payload, validate=True)
        except base64.binascii.Error as exc:  # type: ignore[attr-defined]
            raise ValueError(f"Invalid base64 data for reference [{label}]") from exc

        timestamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%d%H%M%S%fZ")
        filename = f"{timestamp}_{sequence}.{extension}"
        destination = output_dir / filename

        # Ensure uniqueness even if timestamps collide within the same second.
        while destination.exists():
            sequence += 1
            destination = output_dir / f"{timestamp}_{sequence}.{extension}"

        destination.write_bytes(image_bytes)
        saved.append((label, destination))

        relative_path = os.path.relpath(destination, start=markdown_path.parent)
        replacements[label] = relative_path.replace(os.sep, "/")
        sequence += 1

    def replace_reference(match: re.Match[str]) -> str:
        label = match.group(1)
        path = replacements.get(label)
        if not path:
            return match.group(0)
        return f"[{label}]: {path}"

    updated_content = IMAGE_REF_PATTERN.sub(replace_reference, content)
    markdown_path.write_text(updated_content, encoding="utf-8")

    return saved


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "markdown_file",
        type=pathlib.Path,
        help="Path to the Markdown file that contains base64-encoded images.",
    )
    parser.add_argument(
        "--output-dir",
        type=pathlib.Path,
        default=pathlib.Path("images"),
        help="Directory to store the extracted images (default: ./images).",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    saved = extract_images(args.markdown_file, args.output_dir)

    if not saved:
        print("No embedded base64 image references found.")
        return

    print("Saved images:")
    for label, destination in saved:
        print(f"  [{label}] -> {destination}")


if __name__ == "__main__":
    main()
