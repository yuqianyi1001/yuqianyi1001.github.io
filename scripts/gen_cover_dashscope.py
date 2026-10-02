#!/usr/bin/env python3
"""用通义千问（DashScope qwen-image）生成文章封面图，输出 1280x720 PNG。

用法：
    DASHSCOPE_API_KEY=... python3 scripts/gen_cover_dashscope.py <post 文件名（不含 .md）> "<提示词>"
输出：images/<post 文件名>-cover.png
"""
import json
import os
import pathlib
import subprocess
import sys
import time
import urllib.request

API = "https://dashscope.aliyuncs.com/api/v1"


def call(url, payload=None, headers=None):
    key = os.environ["DASHSCOPE_API_KEY"]
    h = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
    h.update(headers or {})
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(url, data=data, headers=h, method="POST" if data else "GET")
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.load(r)


def main():
    slug, prompt = sys.argv[1], sys.argv[2]
    root = pathlib.Path(__file__).resolve().parent.parent
    out = root / "images" / f"{slug}-cover.png"

    task = call(
        f"{API}/services/aigc/text2image/image-synthesis",
        {
            "model": "qwen-image",
            "input": {"prompt": prompt},
            "parameters": {"size": "1664*928", "n": 1, "prompt_extend": True, "watermark": False},
        },
        {"X-DashScope-Async": "enable"},
    )
    task_id = task["output"]["task_id"]
    print("task:", task_id)

    while True:
        time.sleep(5)
        res = call(f"{API}/tasks/{task_id}")
        status = res["output"]["task_status"]
        print("status:", status)
        if status == "SUCCEEDED":
            break
        if status in ("FAILED", "CANCELED", "UNKNOWN"):
            sys.exit(json.dumps(res, ensure_ascii=False))

    img_url = res["output"]["results"][0]["url"]
    urllib.request.urlretrieve(img_url, out)
    subprocess.run(["sips", "-z", "720", "1280", "-s", "format", "png", str(out), "--out", str(out)],
                   check=True, capture_output=True)
    print("saved:", out)


if __name__ == "__main__":
    main()
