#!/usr/bin/env python3
"""用百炼 Qwen3 TTS（克隆音色「愚千一」）把 notes/NN.txt 合成为 audio/NN.wav。

- 模型和音色从 ~/.env 读取：BAILIAN_TTS_MODEL、BAILIAN_QWEN_TTS_VOICE_YUQIANYI、DASHSCOPE_API_KEY
- 每段按行切块（单次请求不超过 MAX_CHARS 字），逐块合成后拼接，块间留 GAP 秒静音
- 幂等：audio/NN.wav 已存在就跳过；要重合成某一段，删掉对应 wav 再跑
用法：python3 scripts/synth.py [01 03 ...]
"""
import io
import sys
import time
import wave
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent.parent
NOTES = ROOT / "notes"
AUDIO = ROOT / "audio"
ENDPOINT = "https://dashscope.aliyuncs.com/api/v1/services/aigc/multimodal-generation/generation"
MAX_CHARS = 280
GAP = 0.35
MAX_PARALLEL = 4
MAX_RETRIES = 3

# 只改送给 TTS 的文本；notes 与字幕保持原字
PRONUNCIATION_FIXES = [
    ("我是愚千一", "我是 愚千一"),
    ("般若", "波惹"),
    ("般涅槃", "波涅槃"),
    ("智顗", "智以"),
    ("吐蕃", "吐波"),
    ("僧旻", "僧民"),
]


def load_env():
    env = {}
    for line in (Path.home() / ".env").read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            env[k.strip()] = v.strip().strip('"').strip("'")
    return env


ENV = load_env()
API_KEY = ENV["DASHSCOPE_API_KEY"]
MODEL = ENV["BAILIAN_TTS_MODEL"]
VOICE = ENV["BAILIAN_QWEN_TTS_VOICE_YUQIANYI"]


def fix_pronunciation(text):
    for a, b in PRONUNCIATION_FIXES:
        text = text.replace(a, b)
    return text


def chunks(text):
    out, cur = [], ""
    for line in [l.strip() for l in text.splitlines() if l.strip()]:
        if cur and len(cur) + len(line) > MAX_CHARS:
            out.append(cur)
            cur = ""
        cur += line + "\n"
    if cur:
        out.append(cur)
    return out


def tts(text):
    headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
    body = {"model": MODEL, "input": {"text": fix_pronunciation(text), "voice": VOICE}}
    last = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            r = requests.post(ENDPOINT, headers=headers, json=body, timeout=180)
            p = r.json()
            url = p.get("output", {}).get("audio", {}).get("url")
            if r.status_code == 200 and url:
                return requests.get(url, timeout=180).content
            last = f"HTTP {r.status_code} {p.get('code')} {p.get('message')}"
        except Exception as e:  # 网络抖动时重试
            last = repr(e)
        time.sleep(2 * attempt)
    raise RuntimeError(last)


def synth_one(note):
    out = AUDIO / (note.stem + ".wav")
    if out.exists():
        return f"{note.stem}: skip"
    params, frames = None, []
    for i, c in enumerate(chunks(note.read_text())):
        with wave.open(io.BytesIO(tts(c))) as w:
            if params is None:
                params = w.getparams()
            elif frames:
                frames.append(b"\x00" * int(params.framerate * GAP) * params.sampwidth * params.nchannels)
            frames.append(w.readframes(w.getnframes()))
    with wave.open(str(out), "wb") as w:
        w.setparams(params)
        for f in frames:
            w.writeframes(f)
    dur = sum(len(f) for f in frames) / (params.framerate * params.sampwidth * params.nchannels)
    return f"{note.stem}: {dur:.1f}s"


def main():
    AUDIO.mkdir(exist_ok=True)
    want = set(sys.argv[1:])
    notes = [n for n in sorted(NOTES.glob("*.txt")) if not want or n.stem in want]
    with ThreadPoolExecutor(MAX_PARALLEL) as ex:
        for msg in ex.map(synth_one, notes):
            print(msg, flush=True)


if __name__ == "__main__":
    main()
