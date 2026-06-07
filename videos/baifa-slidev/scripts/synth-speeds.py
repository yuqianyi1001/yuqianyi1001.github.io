"""
Generate the same text at 3 different speech_rate values (1.0, 1.1, 1.2)
using the already-enrolled cloned voice on Aliyun 百炼.

Reuses voice_id from .bailian_voice_id (saved by clone-and-synth.py).
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

env_file = Path.home() / ".env"
if env_file.exists():
    for line in env_file.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))

import dashscope  # noqa: E402
from dashscope.audio.tts_v2 import SpeechSynthesizer, AudioFormat  # noqa: E402

API_KEY = os.environ.get("DASHSCOPE_API_KEY")
if not API_KEY:
    sys.exit("ERROR: DASHSCOPE_API_KEY not found")
dashscope.api_key = API_KEY

ROOT = Path(__file__).resolve().parent.parent
VOICE_ID = (ROOT / ".bailian_voice_id").read_text().strip()
TARGET_MODEL = "cosyvoice-v2"
OUT_DIR = ROOT / "audio-test"
OUT_DIR.mkdir(exist_ok=True)

TEXT_FILE = ROOT / "audio-test/p1.txt"
SPEEDS = [1.0, 1.1, 1.2]

text = TEXT_FILE.read_text(encoding="utf-8").strip()
print(f"[setup] voice_id={VOICE_ID}")
print(f"[setup] text={len(text)} chars from {TEXT_FILE.name}")

for rate in SPEEDS:
    label = f"p1-speed-{rate:.1f}"
    out = OUT_DIR / f"{label}.mp3"
    print(f"[tts] rate={rate} -> {out.name}")
    synth = SpeechSynthesizer(
        model=TARGET_MODEL,
        voice=VOICE_ID,
        format=AudioFormat.MP3_22050HZ_MONO_256KBPS,
        speech_rate=rate,
    )
    audio = synth.call(text)
    if not audio:
        print(f"[tts] FAILED for rate={rate}: empty response")
        continue
    out.write_bytes(audio)
    print(f"[tts] wrote {out.name} ({len(audio)/1024:.1f} KB)")

print("[done]")
