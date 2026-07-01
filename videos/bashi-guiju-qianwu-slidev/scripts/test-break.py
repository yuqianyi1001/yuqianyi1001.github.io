"""Test SSML <break> support — fix run-on sentences across 。"""
import os
from pathlib import Path

env_file = Path.home() / ".env"
if env_file.exists():
    for line in env_file.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))

import dashscope
from dashscope.audio.tts_v2 import SpeechSynthesizer, AudioFormat

dashscope.api_key = os.environ.get("DASHSCOPE_API_KEY")
ROOT = Path(__file__).resolve().parent.parent
VOICE_ID = (ROOT / ".bailian_voice_id").read_text().strip()

OUT = ROOT / "break-test"
OUT.mkdir(exist_ok=True)

# 同样的语句 — 测断句不同方式
CASES = [
    ("v1-plain", '<speak>身识能<phoneme alphabet="py" ph="liao3">了</phoneme>触。所缘 = 色声香味触 五尘。</speak>'),
    ("v2-break300", '<speak>身识能<phoneme alphabet="py" ph="liao3">了</phoneme>触。<break time="300ms"/>所缘 = 色声香味触 五尘。</speak>'),
    ("v3-break500", '<speak>身识能<phoneme alphabet="py" ph="liao3">了</phoneme>触。<break time="500ms"/>所缘 = 色声香味触 五尘。</speak>'),
    ("v4-break800", '<speak>身识能<phoneme alphabet="py" ph="liao3">了</phoneme>触。<break time="800ms"/>所缘 = 色声香味触 五尘。</speak>'),
    ("v5-newline", '<speak>身识能<phoneme alphabet="py" ph="liao3">了</phoneme>触。\n所缘 = 色声香味触 五尘。</speak>'),
    ("v6-doubled", '<speak>身识能<phoneme alphabet="py" ph="liao3">了</phoneme>触。。所缘 = 色声香味触 五尘。</speak>'),
]

for label, text in CASES:
    out = OUT / f"{label}.mp3"
    print(f"\n[{label}]\n  {text}")
    try:
        synth = SpeechSynthesizer(model="cosyvoice-v2", voice=VOICE_ID,
                                   format=AudioFormat.MP3_22050HZ_MONO_256KBPS, speech_rate=1.0)
        audio = synth.call(text)
        if audio:
            out.write_bytes(audio)
            print(f"  ✓ {len(audio)/1024:.0f} KB")
        else:
            print(f"  ✗ empty")
    except Exception as e:
        print(f"  ✗ {e}")

print(f"\n听 {OUT}/ — 哪个版本两句之间有明显停顿？")
