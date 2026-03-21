#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import sys
import urllib.parse
import urllib.request
from pathlib import Path


TOKEN_URL = "https://api.weixin.qq.com/cgi-bin/token"


def load_env_file(env_path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not env_path.exists():
        return values

    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key:
            values[key] = value
    return values


def mask(value: str, visible: int = 4) -> str:
    if len(value) <= visible * 2:
        return "*" * len(value)
    return f"{value[:visible]}...{value[-visible:]}"


def resolve_config() -> tuple[str, str, str]:
    cwd_env = Path.cwd() / ".baoyu-skills" / ".env"
    home_env = Path.home() / ".baoyu-skills" / ".env"

    cwd_values = load_env_file(cwd_env)
    home_values = load_env_file(home_env)

    if os.environ.get("WECHAT_APP_ID") and os.environ.get("WECHAT_APP_SECRET"):
        return os.environ["WECHAT_APP_ID"], os.environ["WECHAT_APP_SECRET"], "environment"

    if cwd_values.get("WECHAT_APP_ID") and cwd_values.get("WECHAT_APP_SECRET"):
        return cwd_values["WECHAT_APP_ID"], cwd_values["WECHAT_APP_SECRET"], str(cwd_env)

    if home_values.get("WECHAT_APP_ID") and home_values.get("WECHAT_APP_SECRET"):
        return home_values["WECHAT_APP_ID"], home_values["WECHAT_APP_SECRET"], str(home_env)

    raise RuntimeError("Missing WECHAT_APP_ID or WECHAT_APP_SECRET in env, .baoyu-skills/.env, or ~/.baoyu-skills/.env")


def fetch_access_token(app_id: str, app_secret: str) -> dict[str, object]:
    query = urllib.parse.urlencode(
        {
            "grant_type": "client_credential",
            "appid": app_id,
            "secret": app_secret,
        }
    )
    url = f"{TOKEN_URL}?{query}"
    with urllib.request.urlopen(url, timeout=20) as response:
        charset = response.headers.get_content_charset() or "utf-8"
        payload = response.read().decode(charset)
    return json.loads(payload)


def main() -> int:
    try:
        app_id, app_secret, source = resolve_config()
    except Exception as exc:
        print(f"Config error: {exc}", file=sys.stderr)
        return 2

    print(f"Config source: {source}")
    print(f"WECHAT_APP_ID: {mask(app_id)}")
    print(f"WECHAT_APP_SECRET: {mask(app_secret)}")

    try:
        payload = fetch_access_token(app_id, app_secret)
    except Exception as exc:
        print(f"Request error: {exc}", file=sys.stderr)
        return 3

    print(json.dumps(payload, ensure_ascii=False, indent=2))

    if "access_token" in payload:
        print("Verification result: OK")
        return 0

    print("Verification result: FAILED", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
