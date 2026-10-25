#!/usr/bin/env python3
"""用百炼 Qwen-Audio-TTS（克隆音色「愚千一」）把 notes/NN.txt 合成为 audio/NN.wav。

- 模型和音色读环境变量 BAILIAN_TTS_MODEL、BAILIAN_TTS_VOICE；没有时再读 ~/.env（BAILIAN_QWEN_TTS_VOICE_YUQIANYI）
- API key 读 DASHSCOPE_API_KEY；云端环境由代理注入时可不设
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
ENDPOINT = "https://dashscope.aliyuncs.com/api/v1/services/audio/tts/SpeechSynthesizer"
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
    ("宁如", "泞如"),
    ("宁起", "泞起"),
    ("阿僧祇", "阿僧其"),
    ("俱舍", "俱社"),
    # 「空」读 kōng（平声）；崆 只有 kōng 一个读音。千一要求全部 kōng。
    ("空", "崆"),
    # 「传」读 chuán，不读 zhuàn；《高僧传》的传保持原字（读 zhuàn）
    ("大师传", "大师船"),
    ("汉传", "汉船"),
    ("大本传到", "大本船到"),
    # 四圣谛这一期新加
    ("胜鬘", "胜蛮"),
    ("拘絺罗", "拘痴罗"),
    ("毗舍佉", "毗舍区"),
    ("猗觉", "依觉"),
    ("如来藏", "如来葬"),
    ("烦恼藏", "烦恼葬"),
    # 经号里的「〇」TTS 会吞掉（第三〇五经读成「第三五经」），改送「零」
    ("第八一〇经", "第八百一十经"),  # 「八一〇」会读成「八幺零」
    ("〇", "零"),
    # 「集著」「染著」的著读 zhuó，不读 zhù
    ("集著", "集灼"),
    ("染著", "染灼"),
    # 阿含系列 1 新加
    ("长阿含", "常阿含"),          # cháng
    ("长处生死", "常处生死"),
    ("梵行", "梵形"),              # xíng
    ("如来、应、", "如来、硬、"),  # 应供，yìng
    ("兴起五阴", "星起五阴"),      # xīng
]


def load_env():
    env = {}
    f = Path.home() / ".env"
    for line in (f.read_text().splitlines() if f.exists() else []):
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            env[k.strip()] = v.strip().strip('"').strip("'")
    return env


import os
ENV = {**load_env(), **os.environ}
API_KEY = ENV.get("DASHSCOPE_API_KEY", "injected-by-proxy")
MODEL = ENV["BAILIAN_TTS_MODEL"]
VOICE = ENV.get("BAILIAN_TTS_VOICE") or ENV["BAILIAN_QWEN_TTS_VOICE_YUQIANYI"]


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
    body = {"model": MODEL, "input": {"text": fix_pronunciation(text), "voice": VOICE, "format": "wav", "sample_rate": 24000}}
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
