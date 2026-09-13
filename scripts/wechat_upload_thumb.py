#!/usr/bin/env python3
"""Upload a cover image as a permanent WeChat material and print its media_id.

Usage (must go through the Beijing proxy, same as wechat_draft_sync.py):

    scripts/wechat_proxy_run.sh <python> scripts/wechat_upload_thumb.py path/to/cover.jpg

Credentials are read the same way as wechat_draft_sync.py (WECHAT_APP_ID /
WECHAT_APP_SECRET, with WEIXIN_AppID / WEIXIN_AppSecret aliases, loaded from
./.env, repo-root .env, or ~/.env).

The returned media_id goes into the post front matter as `thumb_media_id`.
"""

from __future__ import annotations

import argparse
import json
import mimetypes
import os
import pathlib
import sys
import urllib.parse
import uuid

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

from wechat_draft_sync import API_BASE, WeChatAPIError, WeChatClient, apply_dotenv


def add_material_image(client: WeChatClient, image_path: pathlib.Path) -> dict:
    if not image_path.exists():
        raise FileNotFoundError(f"Image not found: {image_path}")

    mime_type, _ = mimetypes.guess_type(image_path.name)
    mime_type = mime_type or "application/octet-stream"
    boundary = uuid.uuid4().hex
    file_bytes = image_path.read_bytes()

    body = (
        f"--{boundary}\r\n"
        f"Content-Disposition: form-data; name=\"media\"; filename=\"{image_path.name}\"\r\n"
        f"Content-Type: {mime_type}\r\n\r\n"
    ).encode("utf-8") + file_bytes + f"\r\n--{boundary}--\r\n".encode("utf-8")

    headers = {"Content-Type": f"multipart/form-data; boundary={boundary}"}
    result = client._http_request(
        "POST",
        f"{API_BASE}/cgi-bin/material/add_material"
        f"?access_token={urllib.parse.quote(client.access_token)}&type=image",
        data=body,
        headers=headers,
    )
    if not isinstance(result, dict) or "media_id" not in result:
        raise WeChatAPIError(json.dumps(result, ensure_ascii=False))
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("image", type=pathlib.Path, help="Cover image file (jpg/png)")
    args = parser.parse_args(argv)

    apply_dotenv()
    client = WeChatClient(
        app_id=os.getenv("WECHAT_APP_ID"),
        app_secret=os.getenv("WECHAT_APP_SECRET"),
        access_token=os.getenv("WECHAT_ACCESS_TOKEN"),
    )
    result = add_material_image(client, args.image)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    print(f"\nthumb_media_id: {result['media_id']}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
